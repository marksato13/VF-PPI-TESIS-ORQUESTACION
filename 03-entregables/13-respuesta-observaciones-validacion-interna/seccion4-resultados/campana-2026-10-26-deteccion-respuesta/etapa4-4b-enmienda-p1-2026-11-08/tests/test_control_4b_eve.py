"""Enmienda P1 de la 4B: control_4b.py con Suricata medido por EVE `stats` (cero descartes / descartes / datos faltantes).

Datos sintéticos; usa la salud_captura REAL 2026-11-06.1 (la del Sensor1, sha 274b4d61…). Ejecutar desde la raíz de la
enmienda, con las herramientas ensambladas en HERR (variable de entorno; por omisión ../herramientas-banco):
    HERR=/ruta/herramientas python -m pytest tests/test_control_4b_eve.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HERR = Path(os.environ.get("HERR", AQUI.parent / "herramientas-banco"))
sys.path.insert(0, str(HERR))
import control_4b as c4  # noqa: E402
import datos_sinteticos as ds  # noqa: E402
import salud_captura as sc  # noqa: E402

T0, DUR = ds.T0, 1800.0           # 30 min de ventanas
W0, W1 = T0 + 120, T0 + DUR       # primera y última window_end evaluadas
AHORA = T0 + DUR + 3600           # análisis posterior: 'desactualizada' solo si la fuente se corta


def _preparar(tmp: Path, **eve):
    ev = tmp / "eve-segmento.json"
    ev.write_bytes(ds.eve_stats(T0 - 300, T0 + DUR + 120, **eve))
    inc = tmp / "incrementos.jsonl"
    inc.write_text("\n".join(json.dumps(i) for i in ds.incrementos(T0 - 300, T0 + DUR + 120)) + "\n")
    td = tmp / "tcpdump-anillo.log"
    td.write_text(ds.tcpdump_log(T0 - 300, T0 + DUR + 120))
    mot = tmp / "motor.log"
    mot.write_text(ds.motor_log(W0, W1))
    cfg = ds.config(tmp)
    return ev, inc, td, mot, cfg


def _correr(tmp: Path, **eve):
    ev, inc, td, mot, cfg = _preparar(tmp, **eve)
    out = tmp / "control.json"
    rc = c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                  "--salud-captura", str(HERR / "salud_captura.py"), "--incrementos", str(inc),
                  "--tcpdump-anillo", str(td), "--suricata-eve", str(ev), "--ahora", str(AHORA),
                  "--salida", str(out)])
    assert rc == 0
    return json.loads(out.read_text(encoding="utf-8")), ev, inc, td, mot, cfg


def _clasificador(tmp, ev, inc, td):
    lect = sc.leer_eve_stats([ev], desde=W0 - 120)
    incs = [json.loads(l) for l in inc.read_text().splitlines() if l.strip()]
    return c4.Clasificador(sc, incs, sc.leer_tcpdump_log(td), 5.0, lect, AHORA)


def _grid():
    w, out = W0, []
    while w <= W1:
        out.append(w)
        w += 10.0
    return out


def _solapa(w, a, b):
    """Segundos de [w − 60, w] que caen dentro de [a, b]."""
    return max(0.0, min(w, b) - max(w - 60, a))


# ------------------------------------------------------------------------------------------------ las tres categorías


def test_sin_eventos_todo_cero_descartes(tmp_path):
    d, *_ = _correr(tmp_path)
    s = d["detector"]["suricata_por_ventana"]["ventanas_decididas_por_categoria"]
    n = d["detector"]["ventanas_decididas"]
    assert s == {"cero_descartes": n, "descartes": 0, "datos_faltantes": 0}
    assert d["detector"]["ventanas_por_clase"]["C0"] == n
    assert d["periodo_completo"]["anillo_if_heur"]["clase"] == "C0"
    assert d["periodo_completo"]["anillo_if_heur"]["suricata_categoria"] == "cero_descartes"
    assert d["periodo_completo"]["anillo_if_heur"]["suricata_estado"] == "cero_explicito"
    assert d["fuentes"]["suricata_eve"]["muestras_leidas"] > 200


def test_descartes_hacen_c1_y_datos_faltantes_hacen_c3(tmp_path):
    rafaga_t = T0 + 600           # +37 descartes en la muestra de T0+600
    hueco = (T0 + 1000, T0 + 1100)  # 100 s sin eventos stats
    sin = (T0 + 1400, T0 + 1480)    # eventos sin kernel_drops (ausente)
    d, ev, inc, td, mot, cfg = _correr(tmp_path, rafagas=[(rafaga_t, 37)], huecos=[hueco], sin_drops=[sin])
    cl = _clasificador(tmp_path, ev, inc, td)
    por = {"cero_descartes": [], "descartes": [], "datos_faltantes": []}
    for w in _grid():
        c = cl.clase(w)
        por[c["suricata_categoria"]].append(w)
        # coherencia entre categoría de Suricata y clase de la ventana (no hay otras causas de C3 en estos datos)
        assert {"cero_descartes": "C0", "descartes": "C1", "datos_faltantes": "C3"}[c["suricata_categoria"]] == c["clase"]
    # ventanas SEGURAS (lejos de los bordes de cada evento) -> categoría exacta
    for w in _grid():
        lejos = all(_solapa(w, a - 25, b + 25) == 0 for a, b in [(rafaga_t - 8, rafaga_t), hueco, sin])
        if lejos:
            assert w in por["cero_descartes"], f"{ds.iso(w)} debía ser cero_descartes"
        if _solapa(w, hueco[0], hueco[1]) >= 30 or _solapa(w, sin[0], sin[1]) >= 30:
            assert w in por["datos_faltantes"], f"{ds.iso(w)} debía ser datos_faltantes"
        if 10 < (rafaga_t - (w - 60)) < 50 and all(_solapa(w, a - 25, b + 25) == 0 for a, b in [hueco, sin]):
            assert w in por["descartes"], f"{ds.iso(w)} debía ser descartes"
    assert por["descartes"] and por["datos_faltantes"] and por["cero_descartes"]
    # los números del informe coinciden con la reconstrucción
    s = d["detector"]["suricata_por_ventana"]
    n_vent = len(por["cero_descartes"]) + len(por["descartes"]) + len(por["datos_faltantes"])
    assert d["detector"]["ventanas_decididas"] == n_vent * len(ds.IPS)
    for k in por:
        assert s["ventanas_decididas_por_categoria"][k] == len(por[k]) * len(ds.IPS)
    assert d["detector"]["ventanas_por_clase"]["C1"] == len(por["descartes"]) * len(ds.IPS)
    assert d["detector"]["ventanas_por_clase"]["C3"] == len(por["datos_faltantes"]) * len(ds.IPS)
    assert d["detector"]["ventanas_por_clase"]["C0"] == len(por["cero_descartes"]) * len(ds.IPS)
    # los estados concretos de los datos faltantes se conservan
    est = s["datos_faltantes_decididas_por_estado"]
    assert set(est) <= {"ausente", "cobertura_insuficiente"} and est.get("ausente") and est.get("cobertura_insuficiente")
    assert s["tramos_con_datos_faltantes_total"] == 2 and len(s["tramos_con_datos_faltantes"]) == 2


def test_las_tasas_no_mezclan_clases(tmp_path):
    """C0 solo cuenta ventanas con cero descartes; C1 y C3 no se suman a C0, y C3 no entra en ninguna tasa."""
    rafaga_t, hueco = T0 + 600, (T0 + 1000, T0 + 1100)
    d, ev, inc, td, mot, cfg = _correr(tmp_path, rafagas=[(rafaga_t, 5)], huecos=[hueco])
    cl = _clasificador(tmp_path, ev, inc, td)
    U = c4.an.umbrales_de(json.loads(cfg.read_text()))
    regs, _, _ = c4.an.leer_motor(mot)
    esperado = {"C0": 0, "C1": 0}
    n_clase = {"C0": 0, "C1": 0, "C3": 0}
    for r in regs:
        k = cl.clase(r["_wend"])["clase"]
        n_clase[k] += 1
        if k in esperado and c4.an.senales(r, U)["IF_0.05"]:
            esperado[k] += 1
    por = d["detector"]["por_clase"]
    assert por["C0"]["if_y_configuraciones"]["ventanas"] == n_clase["C0"]
    assert por["C0"]["if_y_configuraciones"]["IF_0.05"]["falsas_alarmas"] == esperado["C0"]
    assert por["C1"]["if_y_configuraciones"]["IF_0.05"]["falsas_alarmas"] == esperado["C1"]
    assert "if_y_configuraciones" not in por["C3"] and por["C3"]["ventanas"] == n_clase["C3"]
    assert n_clase["C0"] + n_clase["C1"] + n_clase["C3"] == d["detector"]["ventanas_decididas"]


# ------------------------------------------------------------------------------------------------ periodo completo


@pytest.mark.parametrize("eve,clase,cat,estado", [
    ({}, "C0", "cero_descartes", "cero_explicito"),
    ({"rafagas": [(T0 + 700, 12)]}, "C1", "descartes", "descartes"),
    ({"huecos": [(T0 + 900, T0 + 960)]}, "C3", "datos_faltantes", "cobertura_insuficiente"),
    ({"sin_drops": [(T0 + 900, T0 + 960)]}, "C3", "datos_faltantes", "ausente"),
    ({"reinicios": [T0 + 900]}, "C3", "datos_faltantes", "cobertura_insuficiente"),
    ({"basura_en": T0 + 796}, "C3", "datos_faltantes", "error_lectura"),
])
def test_periodo_completo_distingue_los_tres_resultados(tmp_path, eve, clase, cat, estado):
    d, *_ = _correr(tmp_path, **eve)
    p = d["periodo_completo"]["anillo_if_heur"]
    assert (p["clase"], p["suricata_categoria"], p["suricata_estado"]) == (clase, cat, estado)
    # por hora: el periodo de 30 min tiene un único tramo y repite la misma clase
    assert len(d["periodo_completo"]["por_hora"]) == 1


def test_descartes_y_hueco_en_el_mismo_periodo_ganan_los_datos_faltantes(tmp_path):
    """Un hueco impide demostrar el cero Y los descartes parciales quedan informados: el periodo es C3 y no se afirma ni cero ni C1."""
    d, *_ = _correr(tmp_path, rafagas=[(T0 + 500, 9)], huecos=[(T0 + 900, T0 + 960)])
    p = d["periodo_completo"]["anillo_if_heur"]
    assert p["clase"] == "C3" and p["suricata_categoria"] == "datos_faltantes"
    assert p["suricata"]["descartes_parciales"] == 9 and p["suricata"]["descartes"] is None


def test_desactualizada_si_la_fuente_se_corta_antes_del_fin(tmp_path):
    ev = tmp_path / "eve.json"
    ev.write_bytes(ds.eve_stats(T0 - 300, T0 + 900))          # el EVE se corta a los 900 s
    lect = sc.leer_eve_stats([ev], desde=T0 - 120)
    cl = c4.Clasificador(sc, [], [], 5.0, lect, T0 + 5000)
    m = sc.medida_suricata_eve(lect, T0 + 1000, T0 + 1060, T0 + 5000)
    assert m["estado"] == "desactualizada" and c4.categoria_suricata(m["estado"]) == "datos_faltantes"
    assert cl.eve is lect


def test_error_de_lectura_no_es_cero(tmp_path):
    d, *_ = _correr(tmp_path, basura_en=T0 + 796)
    s = d["detector"]["suricata_por_ventana"]
    assert s["datos_faltantes_decididas_por_estado"].get("error_lectura")
    assert d["detector"]["ventanas_por_clase"]["C0"] == 0           # una línea corrupta en mitad del EVE invalida todo el tramo
    assert d["fuentes"]["suricata_eve"]["invalidas"] == 1


# ------------------------------------------------------------------------------------------------ guardas y regresión


def test_categoria_suricata():
    assert c4.categoria_suricata("cero_explicito") == "cero_descartes"
    assert c4.categoria_suricata("descartes") == "descartes"
    for e in ("ausente", "desactualizada", "error_lectura", "cobertura_insuficiente", None, "otro"):
        assert c4.categoria_suricata(e) == "datos_faltantes"


def test_eve_con_salud_congelada_se_niega(tmp_path):
    ev, inc, td, mot, cfg = _preparar(tmp_path)
    congelada = tmp_path / "salud_congelada.py"
    congelada.write_text("VERSION='2026-11-02.2'\nCRITERIOS={'rotacion_s':5.0}\ndef leer_tcpdump_log(p): return []\n"
                         "def clasificar(*a, **k): return {'clase':'C0','motivos':[]}\n")
    with pytest.raises(SystemExit, match="medida_suricata_eve"):
        c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                 "--salud-captura", str(congelada), "--incrementos", str(inc), "--tcpdump-anillo", str(td),
                 "--suricata-eve", str(ev), "--salida", str(tmp_path / "o.json")])


def test_eve_inexistente_se_para(tmp_path):
    ev, inc, td, mot, cfg = _preparar(tmp_path)
    with pytest.raises(SystemExit, match="no legible"):
        c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                 "--salud-captura", str(HERR / "salud_captura.py"), "--incrementos", str(inc),
                 "--tcpdump-anillo", str(td), "--suricata-eve", str(tmp_path / "no-existe.json"),
                 "--salida", str(tmp_path / "o.json")])


def test_sin_eve_se_comporta_como_antes(tmp_path):
    """Sin --suricata-eve no aparecen las claves nuevas y la clase la decide stats.log (aquí: sin medida -> C3)."""
    ev, inc, td, mot, cfg = _preparar(tmp_path)
    out = tmp_path / "o.json"
    assert c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                    "--salud-captura", str(HERR / "salud_captura.py"), "--incrementos", str(inc),
                    "--tcpdump-anillo", str(td), "--salida", str(out)]) == 0
    d = json.loads(out.read_text(encoding="utf-8"))
    assert "suricata_por_ventana" not in d["detector"] and "periodo_completo" not in d
    assert d["detector"]["ventanas_por_clase"]["C0"] == 0           # el defecto que corrige la enmienda
    assert d["detector"]["ventanas_por_clase"]["C3"] == d["detector"]["ventanas_decididas"]


def test_sin_salud_es_sin_medida(tmp_path):
    ev, inc, td, mot, cfg = _preparar(tmp_path)
    out = tmp_path / "o.json"
    assert c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                    "--salida", str(out)]) == 0
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["detector"]["ventanas_por_clase"]["sin_medida"] == d["detector"]["ventanas_decididas"]


def test_ventanas_no_evaluadas_tambien_se_categorizan(tmp_path):
    """Las ventanas no evaluadas (sin decisión) se cuentan por categoría de Suricata, separadas de las decididas."""
    ev, inc, td, mot, cfg = _preparar(tmp_path, huecos=[(T0 + 1000, T0 + 1100)])
    extra = [{"event": "ventana_no_evaluada", "entity_ip": "10.10.20.21", "window_end_utc": ds.iso(T0 + 1055),
              "logged_at": T0 + 1065, "motivo": "pcap_incompleto"},
             {"event": "ventana_no_evaluada", "entity_ip": "10.10.20.21", "window_end_utc": ds.iso(T0 + 305),
              "logged_at": T0 + 315, "motivo": "pcap_incompleto"}]
    with open(mot, "a") as fh:
        fh.write("\n".join(json.dumps(x) for x in extra) + "\n")
    out = tmp_path / "o.json"
    assert c4.main(["--motor", str(mot), "--config", str(cfg), "--desde", ds.iso(W0), "--hasta", ds.iso(W1),
                    "--salud-captura", str(HERR / "salud_captura.py"), "--incrementos", str(inc),
                    "--tcpdump-anillo", str(td), "--suricata-eve", str(ev), "--ahora", str(AHORA),
                    "--salida", str(out)]) == 0
    s = json.loads(out.read_text(encoding="utf-8"))["detector"]["suricata_por_ventana"]
    assert s["ventanas_no_evaluadas_por_categoria"] == {"cero_descartes": 1, "descartes": 0, "datos_faltantes": 1}
