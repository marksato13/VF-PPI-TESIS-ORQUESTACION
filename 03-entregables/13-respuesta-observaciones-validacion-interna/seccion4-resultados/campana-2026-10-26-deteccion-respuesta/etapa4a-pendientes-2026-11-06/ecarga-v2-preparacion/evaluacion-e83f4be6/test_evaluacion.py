"""Pruebas offline de derivar_bastion.py, derivar_pcap.py y construir_entrada.py.

Usan los ficheros de la observación de integración del 06-nov SOLO PARA PROBAR LAS HERRAMIENTAS: reproducen O1–O10 ya
publicados. NO son datos de E-carga y ninguna entrada que se construya aquí es un resultado de E-carga.
  OBS06=…/evidencia/06-observacion  EVALUADOR=…/evaluar_ecarga.py  python3 -m pytest -q test_evaluacion.py
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).parent
OBS = Path(os.environ["OBS06"])
EVAL = os.environ["EVALUADOR"]
D06, H06 = 1793940600.0, 1793944200.0      # ventana de la observación del 06-nov (04:50–05:50Z)


def _m(n):
    s = importlib.util.spec_from_file_location(n, AQUI / f"{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


db, dp, ce = _m("derivar_bastion"), _m("derivar_pcap"), _m("construir_entrada")
MUESTRAS = (OBS / "bastion" / "muestras.txt").read_text(encoding="utf-8", errors="replace")
CLASIF = OBS / "sensor1" / "final" / "clasificacion" / "clasificacion.json"


# ---------------------------------------------------------------- derivar_bastion: reproduce O1, O6, O8, O9, O10
def test_bastion_reproduce_lo_publicado_del_06nov():
    r = db.derivar(MUESTRAS, D06, H06)
    assert r["cobertura"]["ok"] and r["cobertura"]["muestras_ventana"] == 121
    for s in ("S1", "S6", "S8", "S9", "S10"):
        assert r[s]["valor"] is True, (s, r[s])
    assert r["S1"]["pid_nr"]["ppi-motor"] == ["1384", "0"] and r["S1"]["pid_nr"]["agente"] == ["15020", "0"]
    assert r["S8"]["firma_invalida_ini_fin"] == [14, 14]
    assert r["S10"]["rulesets_sensor1"] == ["24c320e3e9538573"] and r["S10"]["rulesets_srvdmz"] == ["e3b0c44298fc1c14"]


def _desde(texto, n, patron, nuevo):
    p = texto.split("### ")
    for i in range(1 + n, len(p)):
        p[i] = re.sub(patron, nuevo, p[i], flags=re.M)
    return "### ".join(p)


def test_bastion_reinicio_da_s1_false_y_dato_ausente_da_null():
    assert db.derivar(_desde(MUESTRAS, 60, r"^S suricata pid=\d+", "S suricata pid=9"), D06, H06)["S1"]["valor"] is False
    r = db.derivar(_desde(MUESTRAS, 60, r"^S suricata pid=.*$", "S suricata ERROR"), D06, H06)
    assert r["S1"]["valor"] is None


def test_bastion_sin_cobertura_todo_null():
    r = db.derivar(MUESTRAS, D06 - 7200, H06 - 7200)       # ventana sin muestras
    assert not r["cobertura"]["ok"] and all(r[s]["valor"] is None for s in ("S1", "S6", "S8", "S9", "S10"))
    p = MUESTRAS.split("### ")
    hueco = "### ".join(p[:50] + p[56:])                    # quita ~3 min de muestras
    assert db.derivar(hueco, D06, H06)["S1"]["valor"] is None


def test_bastion_firma_y_ruleset():
    assert db.derivar(_desde(MUESTRAS, 70, r"firma_invalida=14", "firma_invalida=15"), D06, H06)["S8"]["valor"] is False
    assert db.derivar(_desde(MUESTRAS, 70, r"^S ruleset=\w+", "S ruleset=0000000000000000"), D06, H06)["S10"]["valor"] is False
    assert db.derivar(_desde(MUESTRAS, 70, r"panel_https=401", "panel_https=000"), D06, H06)["S9"]["valor"] is False


# ---------------------------------------------------------------- derivar_pcap: reproduce O2, O3
def test_pcap_reproduce_lo_publicado_del_06nov():
    with open(OBS / "sensor1" / "pcap.jsonl", encoding="utf-8") as fh:
        r = dp.derivar(fh, D06, H06)
    assert r["ficheros"] == 717 and r["S2"]["valor"] is True and r["S2"]["primero"] == "live-20261106045002.pcap"
    assert r["S2"]["errores"] == [] and r["S2"]["registros"] == 585151
    assert r["S3"]["valor"] is True and r["S3"]["salto_max_nombres_s"] == 6.0


def test_pcap_error_de_formato_o_primero_tardio():
    lineas = (OBS / "sensor1" / "pcap.jsonl").read_text(encoding="utf-8").splitlines()
    objetivo = "live-20261106050004.pcap"                 # existe en la ventana (nombre real del anillo)
    assert sum(objetivo in l for l in lineas) == 1
    mal = [l.replace('"registros"', '"error": "registro incompleto", "registros"') if objetivo in l else l
           for l in lineas]
    r = dp.derivar(mal, D06, H06)
    assert r["S2"]["valor"] is False and r["S2"]["errores"] == [objetivo]
    sin_primeros = [l for l in lineas if not any(f in l for f in ("live-20261106045002", "live-20261106045007",
                                                                   "live-20261106045012"))]
    r = dp.derivar(sin_primeros, D06, H06)                     # el primero legible empieza ~17 s tarde
    assert r["S2"]["valor"] is False and r["S2"]["primero_tras_desde_s"] > 7
    assert dp.derivar(lineas, D06 - 9000, D06 - 8000)["S2"]["valor"] is None


# ---------------------------------------------------------------- construir_entrada
def _args(tmp, **kw):
    base = ["--desde", str(kw.pop("desde", D06)), "--hasta", str(kw.pop("hasta", H06)),
            "--clasificacion", str(kw.pop("clasificacion", CLASIF)),
            "--salida-entrada", str(tmp / "entrada.json"), "--salida-traza", str(tmp / "traza.json")]
    for k, v in kw.items():
        if isinstance(v, list):
            for x in v:
                base += [f"--{k.replace('_', '-')}", str(x)]
        else:
            base += [f"--{k.replace('_', '-')}", str(v)]
    return base


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _veredicto(entrada):
    r = subprocess.run([sys.executable, "-I", EVAL, "veredicto", "--entrada", str(entrada)], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_solo_clasificacion_no_rellena_nada_mas(tmp_path):
    assert ce.main(_args(tmp_path)) == 0
    e, t = _json(tmp_path / "entrada.json"), _json(tmp_path / "traza.json")
    assert e["clasificacion"]["clase_periodo"] == "C0" and e["clasificacion"]["motivos"] == []
    assert e["suricata"]["estado"] == "cero_explicito" and e["suricata"]["descartes"] == 0
    assert e["descartes_por_millon"] == 0.0
    assert e["K"] == {"K1": None, "K2": None, "K3": None, "K4a": None, "K5": True}
    assert {k for k, v in e["S"].items() if v is not None} == {"S4", "S5", "S12", "S13"}
    assert t["fuentes"]["clasificacion"]["sha256"] and t["entrada_sha256"]
    assert t["campos"]["S.S13"]["fuente"] == "clasificacion"
    rc, r = _veredicto(tmp_path / "entrada.json")      # la entrada cumple el contrato: nunca rc 2
    assert rc == 1 and r["estabilidad_tecnica"] == "no demostrable" and r["habilita_condicion_3"] is False


def test_todas_las_fuentes_y_manuales(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps(db.derivar(MUESTRAS, D06, H06)))
    with open(OBS / "sensor1" / "pcap.jsonl", encoding="utf-8") as fh:
        (tmp_path / "p.json").write_text(json.dumps(dp.derivar(fh, D06, H06)))
    (tmp_path / "c.json").write_text(json.dumps({"desde": D06, "hasta": H06, "fuente_contadores": "eve stats",
                                                 "paquetes": 600_000, "rafagas_ge_umbral": 9, "umbral_rafaga_paquetes_8s": 5000,
                                                 "flujos_eve": 900, "flujos_grandes": 49, "umbral_flujo_grande": 1000}))
    (tmp_path / "pf.json").write_text(json.dumps({"version": "2026-11-06.4", "desde": D06, "hasta": H06,
                                                  "K4a": {"cumple": True}, "K4b": {"estado": "sin_trafico"}}))
    ev = tmp_path / "ev.txt"
    ev.write_text("evidencia de prueba")
    assert ce.main(_args(tmp_path, comparar=tmp_path / "c.json", perfiles=tmp_path / "pf.json", perfiles_rc=0,
                         bastion=tmp_path / "b.json", pcap=tmp_path / "p.json",
                         manual=[f"S7=true:{ev}", f"S11=true:{ev}", f"S14=null:{ev}", f"S15=true:{ev}"])) == 0
    e, t = _json(tmp_path / "entrada.json"), _json(tmp_path / "traza.json")
    assert e["K"] == {"K1": True, "K2": True, "K3": False, "K4a": True, "K5": True}     # K3: 49 < 50
    assert e["S"]["S14"] is None and all(e["S"][s] is True for s in ("S1", "S2", "S3", "S6", "S7", "S8", "S9", "S10", "S11", "S15"))
    assert t["K4b_informativo"] == {"estado": "sin_trafico"} and t["sin_medida"] == ["S.S14"]
    assert t["fuentes"]["manual_S7"]["sha256"]
    rc, r = _veredicto(tmp_path / "entrada.json")
    assert rc == 1 and r["estabilidad_tecnica"] == "carga insuficiente"


def test_periodo_distinto_deja_null(tmp_path):
    (tmp_path / "c.json").write_text(json.dumps({"desde": D06 + 60, "hasta": H06, "fuente_contadores": "eve stats",
                                                 "paquetes": 9_999_999, "rafagas_ge_umbral": 99, "umbral_rafaga_paquetes_8s": 5000,
                                                 "flujos_eve": 9, "flujos_grandes": 99, "umbral_flujo_grande": 1000}))
    (tmp_path / "pf.json").write_text(json.dumps({"version": "2026-11-06.4", "desde": D06, "hasta": H06, "K4a": {"cumple": True}}))
    assert ce.main(_args(tmp_path, comparar=tmp_path / "c.json", perfiles=tmp_path / "pf.json", perfiles_rc=2)) == 0
    e = _json(tmp_path / "entrada.json")
    assert e["K"]["K1"] is None and e["K"]["K2"] is None and e["K"]["K3"] is None
    assert e["K"]["K4a"] is None                                                    # perfiles con rc 2


def test_k3_sin_flujos_leidos_es_null(tmp_path):
    (tmp_path / "c.json").write_text(json.dumps({"desde": D06, "hasta": H06, "fuente_contadores": "eve stats",
                                                 "paquetes": 700_000, "rafagas_ge_umbral": 10, "umbral_rafaga_paquetes_8s": 5000,
                                                 "flujos_eve": 0, "flujos_grandes": 0, "umbral_flujo_grande": 1000}))
    assert ce.main(_args(tmp_path, comparar=tmp_path / "c.json")) == 0
    assert _json(tmp_path / "entrada.json")["K"]["K3"] is None


@pytest.mark.parametrize("manual", ["S1=true:{ev}", "S7=sí:{ev}", "S7=true:/no/existe", "S7=true"])
def test_manual_mal_formado_o_sin_evidencia_rc2(tmp_path, manual):
    ev = tmp_path / "ev.txt"
    ev.write_text("x")
    assert ce.main(_args(tmp_path, manual=[manual.format(ev=ev)])) == 2
    assert not (tmp_path / "entrada.json").exists() and "error" in _json(tmp_path / "traza.json")


def test_clasificacion_sin_medida_eve_o_de_otro_periodo_rc2(tmp_path):
    c = _json(CLASIF)
    c["suricata"] = {"fuente": "stats.log"}
    (tmp_path / "cl.json").write_text(json.dumps(c))
    assert ce.main(_args(tmp_path, clasificacion=tmp_path / "cl.json")) == 2
    (tmp_path / "traza.json").unlink()
    assert ce.main(_args(tmp_path, desde=D06 + 600)) == 2


def test_no_sobrescribe(tmp_path):
    (tmp_path / "entrada.json").write_text("{}")
    assert ce.main(_args(tmp_path)) == 2 and _json(tmp_path / "entrada.json") == {}


def test_c1_sintetico_dpm_y_s13_exactos(tmp_path):
    c = _json(CLASIF)
    c["clase_periodo"] = "C1"
    c["capturas"]["captura"]["motivos"] = ["Suricata (EVE): 1495 descartes de 100000000 paquetes"]
    c["suricata"]["medida"].update(estado="descartes", descartes=1495, paquetes=100_000_000)
    (tmp_path / "cl.json").write_text(json.dumps(c))
    assert ce.main(_args(tmp_path, clasificacion=tmp_path / "cl.json")) == 0
    e = _json(tmp_path / "entrada.json")
    assert e["descartes_por_millon"] == 14.95 and e["S"]["S13"] is False         # 14,95 exacto no cumple
    assert e["clasificacion"]["motivos"] == ["captura: Suricata (EVE): 1495 descartes de 100000000 paquetes"]
