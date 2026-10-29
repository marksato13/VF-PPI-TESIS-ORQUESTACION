"""Agrega la salida de validar_build_rows_por_entidad.py y la cruza con la duración real de cada ciclo.

Estimación (no medición en vivo): trabajo_estimado = trabajo_real - (t_global - t_entidad). Supone que el ahorro
medido sin conexión se traslada tal cual al motor en vivo; no corrige la parte del ciclo que el perfil no reproduce.
Uso: python resumir_validacion_por_entidad.py --motor motor_decision.log --validacion t0.jsonl [t1.jsonl ...] --salida-dir D
"""
import argparse
import collections
import csv
import datetime
import json
from pathlib import Path

TRAMOS = [("previo", "07:00:00", "08:01:00"), ("control", "08:01:00", "08:35:10"),
          ("bateria", "08:35:10", "10:33:07"), ("posterior", "10:33:07", "11:00:00")]


def q(v, p):
    v = sorted(v)
    return round(v[int(p * (len(v) - 1))], 2) if v else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True)
    ap.add_argument("--validacion", nargs="+", required=True)
    ap.add_argument("--salida-dir", required=True, type=Path)
    a = ap.parse_args()
    real = collections.defaultdict(float)
    for l in open(a.motor, encoding="utf-8"):
        if '"event": "decision"' in l:
            d = json.loads(l)
            real[d["inicio_ciclo"]] = max(real[d["inicio_ciclo"]], d["logged_at"] - d["inicio_ciclo"])
    regs = [json.loads(l) for f in a.validacion for l in open(f, encoding="utf-8")]
    regs.sort(key=lambda r: r["inicio_ciclo"])
    a.salida_dir.mkdir(parents=True, exist_ok=True)
    filas = []
    for r in regs:
        w = real.get(r["inicio_ciclo"])
        est = (w - (r["t_global_s"] - r["t_entidad_s"])) if (w is not None and "t_global_s" in r) else None
        filas.append({**{k: r.get(k) for k in ("hora", "inicio_ciclo", "paquetes", "apps", "entidades", "filas",
                                                "identicas", "t_global_s", "t_entidad_s")},
                      "trabajo_real_s": round(w, 2) if w is not None else None,
                      "trabajo_estimado_por_entidad_s": round(est, 2) if est is not None else None,
                      "diferencia": json.dumps(r.get("diferencia")) if r.get("diferencia") else ""})
    with open(a.salida_dir / "validacion-por-ciclo.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(filas[0])); wr.writeheader(); wr.writerows(filas)

    res = []
    for nom, h0, h1 in TRAMOS:
        sel = [f for f in filas if h0 <= f["hora"] < h1]
        if not sel:
            continue
        con = [f for f in sel if f["t_global_s"] is not None]
        res.append({
            "tramo": nom, "ciclos": len(sel), "identicos": sum(bool(f["identicas"]) for f in sel),
            "distintos": sum(not f["identicas"] for f in sel),
            "filas_comparadas": sum(f["filas"] or 0 for f in sel),
            "aceleracion_build_rows_p50": q([f["t_global_s"] / f["t_entidad_s"] for f in con if f["t_entidad_s"]], .5),
            "trabajo_real_p50_s": q([f["trabajo_real_s"] for f in con if f["trabajo_real_s"] is not None], .5),
            "trabajo_real_max_s": q([f["trabajo_real_s"] for f in con if f["trabajo_real_s"] is not None], 1),
            "estimado_p50_s": q([f["trabajo_estimado_por_entidad_s"] for f in con if f["trabajo_estimado_por_entidad_s"] is not None], .5),
            "estimado_p90_s": q([f["trabajo_estimado_por_entidad_s"] for f in con if f["trabajo_estimado_por_entidad_s"] is not None], .9),
            "estimado_max_s": q([f["trabajo_estimado_por_entidad_s"] for f in con if f["trabajo_estimado_por_entidad_s"] is not None], 1),
            "real_mayor_9_5s": sum((f["trabajo_real_s"] or 0) > 9.5 for f in con),
            "estimado_mayor_9_5s": sum((f["trabajo_estimado_por_entidad_s"] or 0) > 9.5 for f in con)})
    with open(a.salida_dir / "validacion-resumen.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(res[0])); wr.writeheader(); wr.writerows(res)
    for r in res:
        print(r)
    print("total ciclos", len(filas), "identicos", sum(bool(f["identicas"]) for f in filas),
          "filas comparadas", sum(f["filas"] or 0 for f in filas))
    for f in filas:
        if not f["identicas"]:
            print("DISTINTO", f["hora"], f["diferencia"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
