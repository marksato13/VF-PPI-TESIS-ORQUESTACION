"""control_4b.py: separa por clase de salud, por α, por regla heurística, vía rápida y propuestas.

La regresión contra el control publicado del 3B (2 644 ventanas; IF 395/254/83, HEUR 92, HIB 466/336/171) se
ejecutó con la evidencia real (ver etapa4-preparacion-2026-11-02/evidencia/control-4b/). Aquí, datos sintéticos.
Ejecutar: python -m pytest tests/test_control_4b.py
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import os
sys.path.insert(0, os.environ["HERR"])
import control_4b as c4  # noqa: E402

T0 = 1793700000.0          # múltiplo de 10
U05, U03, U01 = -0.5694578968203694, -0.5898535710336618, -0.6223889502095352


def _iso(t):
    import datetime as dt
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _config(tmp: Path) -> Path:
    p = tmp / "config.json"
    p.write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "0.01": U01},
                             "poblacion": {"excepciones_respuesta": [], "exclusiones_poblacion": []}}))
    return p


def _dec(ip, w, score, heur=None, decision="PERMIT", detector="if_limpio_2026_10"):
    r = {"event": "decision", "logged_at": w + 5, "entity_ip": ip, "window_end_utc": _iso(w),
         "decision": decision, "packet_count_10s": 10, "score": score, "detector_name": detector,
         "umbral": U05}
    if heur:
        r["heuristico"] = {"heuristico": heur, "accion": "LIMIT", "motivo": "x"}
    return r


def _salud_falsa(limite):
    """clasificar: C0 si hasta < limite, C1 si no. Sustituye a salud_captura sin depender del otro repo."""
    m = types.SimpleNamespace(VERSION="falsa", CRITERIOS={"rotacion_s": 5.0})
    m.clasificar = lambda incs, td, desde, hasta, crit: (
        {"clase": "C0", "motivos": []} if hasta < limite else {"clase": "C1", "motivos": ["Suricata: 3 descartes"]})
    m.leer_tcpdump_log = lambda p: []
    return m


def _motor(tmp: Path) -> Path:
    regs = [
        _dec("10.10.20.20", T0 + 10, -0.70),                       # IF en los 3 α (C0)
        _dec("10.10.20.21", T0 + 20, -0.58),                       # solo IF_0.05 (C0)
        _dec("10.10.20.20", T0 + 30, -0.40, heur="dns_entropy"),   # HEUR (C0)
        _dec("10.10.20.22", T0 + 40, None),                        # IF no aplicable (C0)
        _dec("10.10.20.20", T0 + 100, -0.60, heur="http_flood"),   # C1: IF_0.05/0.03 + HEUR
        _dec("10.10.20.23", T0 + 110, -0.30, decision="ALERT", detector="auth_failure_heuristic"),  # C1
    ]
    p = tmp / "motor.log"
    p.write_text("\n".join(json.dumps(r) for r in regs) + "\n")
    return p


def test_por_clase_regla_y_entidad(tmp_path):
    motor, cfg = _motor(tmp_path), _config(tmp_path)
    U = c4.an.umbrales_de(json.loads(cfg.read_text()))
    pob = c4.poblacion.cargar_poblacion(json.loads(cfg.read_text()))
    regs, _, _ = c4.an.leer_motor(motor)
    clasif = c4.Clasificador(_salud_falsa(T0 + 60), [], [])
    d = c4.analizar(regs, [], T0, T0 + 200, U, pob, clasif)
    assert d["ventanas_por_clase"]["C0"] == 4 and d["ventanas_por_clase"]["C1"] == 2
    c0 = d["por_clase"]["C0"]
    assert c0["if_y_configuraciones"]["IF_0.05"]["falsas_alarmas"] == 2
    assert c0["if_y_configuraciones"]["IF_0.03"]["falsas_alarmas"] == 1
    assert c0["if_y_configuraciones"]["IF_0.01"]["falsas_alarmas"] == 1
    assert c0["heuristicos"]["por_regla"] == {"dns_entropy": 1}
    assert c0["por_entidad"]["10.10.20.20"]["IF_0.05"] == 1
    c1 = d["por_clase"]["C1"]
    assert c1["heuristicos"]["por_regla"] == {"http_flood": 1}
    assert c1["heuristicos"]["auth_failure_heuristic_alert_heredada"] == 1
    assert c1["emisiones_reales"]["alert_por_detector"] == {"auth_failure_heuristic": 1}
    assert d["motivos_por_clase"]["C1"] == {"Suricata": 2}


def test_c3_no_entra_en_tasas(tmp_path):
    motor, cfg = _motor(tmp_path), _config(tmp_path)
    m = _salud_falsa(0)
    m.clasificar = lambda *a: {"clase": "C3", "motivos": ["reinicio o parada: ppi-motor"]}
    out = tmp_path / "o.json"
    regs, _, _ = c4.an.leer_motor(motor)
    U = c4.an.umbrales_de(json.loads(cfg.read_text()))
    pob = c4.poblacion.cargar_poblacion(json.loads(cfg.read_text()))
    d = c4.analizar(regs, [], T0, T0 + 200, U, pob, c4.Clasificador(m, [], []))
    assert d["ventanas_por_clase"]["C3"] == 6
    assert "if_y_configuraciones" not in d["por_clase"]["C3"]
    assert not out.exists()


def test_via_rapida_y_propuestas(tmp_path):
    sr = tmp_path / "senales-rapidas.jsonl"
    sr.write_text("\n".join(json.dumps(x) for x in [
        {"event": "senal_rapida", "regla": "port_scan_temprano", "origen": "10.10.20.20", "destino": "10.10.30.10",
         "t_evidencia": T0 + 50, "emitido_en": T0 + 50.2},
        {"event": "senal_rapida", "regla": "port_scan_temprano", "origen": "10.10.20.20", "destino": "10.10.30.10",
         "t_evidencia": T0 + 5000, "emitido_en": T0 + 5000.1}]) + "\n")
    v = c4.via_rapida(sr, T0, T0 + 200, None)
    assert v["senales"] == 1 and v["retraso_emision_s"] == [0.2]
    tr = tmp_path / "traza.jsonl"
    tr.write_text("\n".join(json.dumps(x) for x in [
        {"evento": "publicacion", "publicado_en": T0 + 30, "nuevos": [
            {"tipo": "nueva", "regla": "if_senal", "accion": "LIMIT", "ip": "10.10.20.21"},
            {"tipo": "rechazada", "regla": "auth_failure", "accion": "BLOCK", "ip": "10.10.20.23",
             "motivo_rechazo": "sin_evidencia_http"}]},
        {"evento": "publicacion", "publicado_en": T0 + 9000, "nuevos": [
            {"tipo": "nueva", "regla": "if_senal", "accion": "LIMIT", "ip": "10.10.20.22"}]}]) + "\n")
    p = c4.propuestas(tr, T0, T0 + 200)
    assert p["propuestas"] == 1 and p["por_entidad"] == {"10.10.20.21": 1}
    assert p["rechazadas"] == 1 and p["rechazadas_por_motivo"] == {"sin_evidencia_http": 1}


def test_cli_sin_salud_es_sin_medida(tmp_path):
    out = tmp_path / "control.json"
    rc = c4.main(["--motor", str(_motor(tmp_path)), "--config", str(_config(tmp_path)),
                  "--desde", _iso(T0), "--hasta", _iso(T0 + 200), "--salida", str(out)])
    d = json.loads(out.read_text(encoding="utf-8"))
    assert rc == 0 and d["detector"]["ventanas_por_clase"]["sin_medida"] == 6
    assert d["fuentes"]["salud_captura"] is None
