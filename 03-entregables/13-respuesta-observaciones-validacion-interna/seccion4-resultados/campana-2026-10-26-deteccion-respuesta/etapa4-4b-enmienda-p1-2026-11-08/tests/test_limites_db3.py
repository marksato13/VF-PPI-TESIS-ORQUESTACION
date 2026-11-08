"""Pruebas de la referencia de DB-3 (propuesta): ventanas faltantes por cotas, no como ALERT."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.environ.get("HERR", str(Path(__file__).resolve().parents[1] / "scripts")))
import limites_db3 as db  # noqa: E402


def grid(a, b, paso=10.0):
    out, t = [], a
    while t <= b:
        out.append(t)
        t += paso
    return out


def test_marcar_faltantes_como_alert_une_avisos():
    """Dos ALERT a 70 s (dos avisos) con la franja intermedia faltante: si se marcara todo ALERT, quedaría UN aviso."""
    O = [1000.0, 1070.0]
    M = grid(1010.0, 1060.0)
    assert db.avisos_observados(O) == 2
    assert db.avisos_observados(O + M) == 1                   # el defecto del tratamiento «faltante = ALERT»
    c = db.cotas_avisos(O, M)
    assert c == {"observado": 2, "minimo": 1, "maximo": 2}


def test_faltantes_lejanas_pueden_crear_avisos_nuevos():
    O = [1000.0]
    M = grid(2000.0, 2200.0)                                  # 21 ventanas faltantes, lejos de toda ALERT
    c = db.cotas_avisos(O, M)
    assert c["observado"] == 1 and c["minimo"] == 1
    assert c["maximo"] == 1 + 4                               # 2000, 2060, 2120, 2180: separadas ≥ 60 s


def test_faltantes_cerca_de_una_alert_no_crean_aviso_nuevo():
    c = db.cotas_avisos([1000.0], [1020.0, 1050.0])
    assert c == {"observado": 1, "minimo": 1, "maximo": 1}


def test_separacion_estricta():
    assert db.avisos_observados([1000.0, 1059.0]) == 1        # 59 s < 60: mismo aviso
    assert db.avisos_observados([1000.0, 1060.0]) == 2        # 60 s: avisos distintos


def test_cotas_de_tiempo():
    c = db.cotas_tiempo(alertas_n=8, decididas_n=100, faltantes_n=20)
    assert c["observado"] == 0.08
    assert round(c["minimo"], 4) == round(8 / 120, 4) and round(c["maximo"], 4) == round(28 / 120, 4)


def test_decision_con_cota():
    assert db.decision(0.05, 0.09, 0.10) == "cumple"
    assert db.decision(0.12, 0.20, 0.10) == "no_cumple"
    assert db.decision(0.08, 0.23, 0.10) == "no_concluyente"      # el límite cae dentro de la cota
    assert db.decision(None, None, 0.10) == "sin_dato"


def test_entidad_concluyente_y_no_concluyente():
    # 8 h requeridas, 2 avisos observados, ninguna faltante: 0,25 avisos/h y 4/2880 en alerta
    O = [1000.0, 5000.0]
    e = db.evaluar_entidad(O, decididas_n=2880, alertas_n=2, faltantes=[], horas_requeridas=8.0)
    assert e["decision"] == "cumple"
    # mismas alertas pero 300 ventanas faltantes lejos: el máximo de avisos pasa de 2 a 2+k y puede cruzar 1/h
    M = grid(10000.0, 12990.0)
    e2 = db.evaluar_entidad(O, decididas_n=2580, alertas_n=2, faltantes=M, horas_requeridas=8.0)
    assert e2["L1_avisos_por_hora"]["maximo"] > 1.0 >= e2["L1_avisos_por_hora"]["observado"]
    assert e2["decision"] == "no_concluyente"


def test_alfa_elegible_solo_si_todas_cumplen_y_empate_al_menor():
    ok = {"decision": "cumple"}
    nc = {"decision": "no_concluyente"}
    nok = {"decision": "no_cumple"}
    v = {"0.05": db.veredicto_alfa({"a": ok, "b": nok}), "0.03": db.veredicto_alfa({"a": ok, "b": nc}),
         "0.01": db.veredicto_alfa({"a": ok, "b": ok})}
    assert [a for a, x in v.items() if x["elegible"]] == ["0.01"]
    assert db.elegir_alfa(v, {"0.05": 9, "0.03": 9, "0.01": 3})["alfa"] == "0.01"
    v2 = {"0.03": db.veredicto_alfa({"a": ok}), "0.01": db.veredicto_alfa({"a": ok})}
    r = db.elegir_alfa(v2, {"0.03": 7, "0.01": 7})
    assert r["resultado"] == "elegido" and r["alfa"] == "0.01" and r["empate_entre"] == ["0.01", "0.03"]


def test_sin_elegibles_distingue_ninguno_de_no_concluyente():
    ok, nc, nok = {"decision": "cumple"}, {"decision": "no_concluyente"}, {"decision": "no_cumple"}
    v = {"0.05": db.veredicto_alfa({"a": nok}), "0.03": db.veredicto_alfa({"a": nok}), "0.01": db.veredicto_alfa({"a": nok})}
    assert db.elegir_alfa(v, {"0.05": 1, "0.03": 1, "0.01": 1})["resultado"] == "ningun_alfa_cumple"
    v["0.01"] = db.veredicto_alfa({"a": nc})
    assert db.elegir_alfa(v, {"0.05": 1, "0.03": 1, "0.01": 1})["resultado"] == "no_concluyente"
