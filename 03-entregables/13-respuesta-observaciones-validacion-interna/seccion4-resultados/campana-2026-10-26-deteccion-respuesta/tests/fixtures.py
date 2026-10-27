#!/usr/bin/env python3
"""Escribe fixtures con resultado CONOCIDO (no son datos de campaña) para verificar analizar.py.
Uso: python3 fixtures.py <dir>   ; luego: python3 ../scripts/analizar.py --marcas <dir>/marcas.jsonl
     --motor <dir>/motor.log --config <dir>/cfg.json --etiquetas <dir>/etiquetas.csv --salida <dir>/analisis
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

U05, U03 = -0.5694578968203694, -0.5898535710336618
K = "10.10.20.30"
iso = lambda ep: datetime.fromtimestamp(ep, timezone.utc).isoformat()


def linea(logged, ip, wend, score, decision, heur=None, pk=5):
    return json.dumps({"event": "decision", "logged_at": logged, "entity_ip": ip, "window_end_utc": iso(wend),
                       "score": score, "threshold": U05, "decision": decision, "packet_count_10s": pk,
                       "history_coverage_s": 60, "detector_name": "if_limpio_2026_10", "heuristico": heur})


def escribir(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    T = 1793000000
    M = [("inicio", "inundacion_http-r1", "inundacion_http", 1, "10.10.30.10", T, None),
         ("fin", "inundacion_http-r1", None, None, None, T + 90, "completo"),
         ("inicio", "dns_inusual-r1", "dns_inusual", 1, "10.10.10.20", T + 1000, None),
         ("fin", "dns_inusual-r1", None, None, None, T + 1090, "completo"),
         ("inicio", "escaneo_breve-r1", "escaneo_breve", 1, "10.10.30.10", T + 2000, None),
         ("fin", "escaneo_breve-r1", None, None, None, T + 2090, "incompleto_timeout"),
         ("inicio", "inundacion_http-r2", "inundacion_http", 2, "10.10.30.10", T + 3000, None),
         ("fin", "inundacion_http-r2", None, None, None, T + 3090, "completo")]
    ms = []
    for ev, eid, esc, rep, dst, t, est in M:
        o = {"evento": ev, "episodio_id": eid, "reloj": {"pared_utc": iso(t)}}
        if ev == "inicio":
            o.update({"escenario": esc, "repeticion": rep, "destino": dst})
        else:
            o["estado"] = est
        ms.append(json.dumps(o))
    (d / "marcas.jsonl").write_text("\n".join(ms), encoding="utf-8")

    L = []
    for w in range(T, T + 150, 10):
        L.append(linea(w + 1, K, w, -0.70 if w == T + 40 else -0.50,
                       "ALERT" if w == T + 40 else "PERMIT",
                       {"heuristico": "http_abuse", "accion": "LIMIT"} if w == T + 40 else None))
    for w in range(T + 1000, T + 1150, 10):
        L.append(linea(w + 1, K, w, -0.50, "PERMIT",
                       {"heuristico": "dns_entropy", "accion": "LIMIT"} if w == T + 1030 else None))
    for w in range(T + 3000, T + 3150, 10):
        L.append(linea(w + 1, K, w, -0.70 if w == T + 3100 else -0.50, "ALERT" if w == T + 3100 else "PERMIT"))
    L.append(linea(T + 41, K, T + 40, -0.70, "ALERT", {"heuristico": "http_abuse", "accion": "LIMIT"}))  # duplicado
    (d / "motor.log").write_text("\n".join(L), encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps(
        {"umbrales": {"0.05": U05, "0.03": U03}, "origen": K,
         "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}), encoding="utf-8")
    (d / "etiquetas.csv").write_text(
        "entity_ip,window_end_utc,etiqueta\n%s,%s,1\n%s,%s,0\n" % (K, iso(T + 40), K, iso(T + 50)), encoding="utf-8")
    print("fixtures en", d)


if __name__ == "__main__":
    escribir(Path(sys.argv[1] if len(sys.argv) > 1 else "fixtures"))
