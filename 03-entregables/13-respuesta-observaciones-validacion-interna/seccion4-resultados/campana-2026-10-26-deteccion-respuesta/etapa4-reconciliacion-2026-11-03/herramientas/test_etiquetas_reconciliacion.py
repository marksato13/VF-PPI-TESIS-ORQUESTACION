"""Pruebas SIN tráfico de las etiquetas de detección oportuna (reconciliación 2026-11-03).

Datos sintéticos: comprueban el CÓDIGO, no son resultados.
  python3 -m pytest -q test_etiquetas_reconciliacion.py      (desde esta carpeta)

1. Casos nuevos: señal del IF, regla prevista y otra regla se cuentan aparte; la respuesta aplicada nunca se
   deduce del registro del motor; la medida publicada indica si su regla es la prevista.
2. Regresión: TODAS las pruebas originales de tests/test_analizar_3b.py y tests/test_referencia_trafico_4c.py se
   vuelven a ejecutar contra las versiones nuevas de esta carpeta (se precargan en sys.modules), sin tocar sus
   expectativas.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]                               # campana-2026-10-26-deteccion-respuesta
sys.path.insert(0, str(RAIZ / "scripts"))            # analizar.py y poblacion.py sin cambios


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, AQUI / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod                        # las pruebas originales importarán ESTA versión
    spec.loader.exec_module(mod)
    return mod


a3 = _cargar("analizar_3b")
rt = _cargar("referencia_trafico_4c")
sys.path.insert(0, str(RAIZ / "tests"))
import test_analizar_3b as orig3b  # noqa: E402
import test_referencia_trafico_4c as origrt  # noqa: E402

for _m, _p in ((orig3b, "test_original_3b__"), (origrt, "test_original_rt__")):
    for _n in dir(_m):
        if _n.startswith("test_") and callable(getattr(_m, _n)):
            globals()[_p + _n[5:]] = getattr(_m, _n)

assert orig3b.a3 is a3 and origrt.rt is rt, "las pruebas originales deben usar las versiones nuevas"

KALI, SRV = orig3b.KALI, orig3b.SRV
T0, INI, FIN = orig3b.T0, orig3b.INI, orig3b.FIN
MODELO = "if_limpio_2026_10"


def _ep(escenario):
    return {**orig3b.EP, "escenario": escenario}


def _vivo(w, **campos):
    vivo, _inv, dest = orig3b.escenario()
    r = vivo[(KALI, orig3b.iso(w))]
    r.update(campos)
    return vivo, dest


def test_escaneo_con_brute_force_es_otra_regla_no_la_prevista():
    """C10 de la Etapa 2: una regla brute_force durante un escaneo no es detección oportuna del escaneo."""
    w = T0 + 30
    vivo, dest = _vivo(w, heuristico={"heuristico": "brute_force", "accion": "BLOCK"},
                       heuristicos=[{"heuristico": "brute_force", "accion": "BLOCK"}])
    e = a3.emisiones_episodio(orig3b.EID, _ep("escaneo_breve"), KALI, vivo, dest, orig3b.DESP, MODELO)
    assert e["oportunas"] == 1                       # el recuento antiguo la contaba
    assert e["oportunas_regla_prevista"] == 0 and e["oportunas_regla_no_prevista"] == 1
    assert e["oportunas_senal_if"] == 0
    assert e["detalle"][0]["etiquetas"] == ["regla_no_prevista"]


def test_port_scan_en_escaneo_es_regla_prevista():
    w = T0 + 30
    vivo, dest = _vivo(w, heuristico={"heuristico": "port_scan", "accion": "BLOCK"})
    e = a3.emisiones_episodio(orig3b.EID, _ep("escaneo_sostenido"), KALI, vivo, dest, orig3b.DESP, MODELO)
    assert e["oportunas_regla_prevista"] == 1 and e["oportunas_regla_no_prevista"] == 0
    assert e["latencia_primera_oportuna_regla_prevista_s"] == round(w + 20 - INI, 2)


def test_senal_if_por_decision_if_y_auth_que_autoriza():
    """ec78ca5: decision_if es la clasificación pura del IF; un ALERT por auth_failure no es señal del IF."""
    w1, w2 = T0 + 30, T0 + 40
    vivo, dest = _vivo(w1, decision="ALERT", decision_if="ALERT", detector_name=MODELO)
    vivo[(KALI, orig3b.iso(w2))].update(decision="ALERT", decision_if="PERMIT", detector_name="auth_failure_heuristic")
    e = a3.emisiones_episodio(orig3b.EID, _ep("fuerza_bruta_http"), KALI, vivo, dest, orig3b.DESP, MODELO)
    et = {d["window_end_utc"]: d["etiquetas"] for d in e["detalle"]}
    assert et[orig3b.iso(w1)] == ["senal_if"]
    assert et[orig3b.iso(w2)] == ["regla_prevista"]
    assert e["oportunas_senal_if"] == 1 and e["oportunas_regla_prevista"] == 1


def test_registro_antiguo_sin_decision_if():
    """24f8a80 no escribe decision_if: ALERT con el detector del modelo cuenta como señal del IF."""
    w = T0 + 30
    vivo, dest = _vivo(w, decision="ALERT", detector_name=MODELO)
    e = a3.emisiones_episodio(orig3b.EID, _ep("inundacion_http"), KALI, vivo, dest, orig3b.DESP, MODELO)
    assert e["detalle"][0]["etiquetas"] == ["senal_if"]


def test_hibrida_lleva_las_dos_etiquetas_y_respuesta_no_medida():
    w = T0 + 30
    vivo, dest = _vivo(w, decision="ALERT", decision_if="ALERT", detector_name=MODELO,
                       heuristico={"heuristico": "http_abuse", "accion": "LIMIT"})
    e = a3.emisiones_episodio(orig3b.EID, _ep("inundacion_http"), KALI, vivo, dest, orig3b.DESP, MODELO)
    assert e["detalle"][0]["etiquetas"] == ["senal_if", "regla_prevista"]
    assert e["respuesta_aplicada"] == "no_medida"


def test_referencia_marca_regla_publicada_y_no_inventa_aplicacion(tmp_path):
    eid, ini = "escaneo_breve-r1", T0 + 2
    an = {"episodios": {eid: {
        "en_poblacion_principal": True, "IF_0.05": {"categoria": "oportuna"}, "HEUR": {"categoria": "oportuna"},
        "ventanas": [], "emisiones_reales": {"emisiones": 1, "atribuibles": 1, "oportunas": 1,
                                              "oportunas_senal_if": 0, "oportunas_regla_prevista": 0,
                                              "oportunas_regla_no_prevista": 1}}}}
    (tmp_path / "an.json").write_text(json.dumps(an), encoding="utf-8")
    tr = {"episodios": [{"episodio": eid, "escenario": "escaneo_breve", "destino": SRV,
                         "t_proc_inicio_utc": rt.iso(T0), "t_proc_fin_utc": rt.iso(T0 + 18),
                         "t_trafico_inicio_utc": rt.iso(ini), "t_trafico_fin_utc": rt.iso(T0 + 16),
                         "paquetes_ataque": 40, "captura_cubre_ventana": True}]}
    (tmp_path / "tr.json").write_text(json.dumps(tr), encoding="utf-8")
    pub = {"evento": "publicacion", "publicado_en": T0 + 10, "secuencia": 7,
           "nuevos": [{"ip": KALI, "regla": "brute_force", "accion": "BLOCK", "tipo": "nueva", "destino": "srv-dmz"}]}
    (tmp_path / "pub.jsonl").write_text(json.dumps(pub) + "\n", encoding="utf-8")
    rt.main(["--analisis", str(tmp_path / "an.json"), "--trafico", str(tmp_path / "tr.json"),
             "--traza-publicador", str(tmp_path / "pub.jsonl"), "--salida", str(tmp_path / "o.json")])
    r = json.loads((tmp_path / "o.json").read_text(encoding="utf-8"))["episodios"][eid]
    assert r["respuesta_propuesta"]["regla_es_prevista"] is False
    assert r["etiquetas"]["medida_publicada"] is True and r["etiquetas"]["medida_publicada_es_regla_prevista"] is False
    assert r["etiquetas"]["otra_regla_oportuna"] is True and r["etiquetas"]["regla_prevista_oportuna"] is False
    assert r["etiquetas"]["aplicacion_confirmada"] is None and r["etiquetas"]["efecto_observado"] is None
