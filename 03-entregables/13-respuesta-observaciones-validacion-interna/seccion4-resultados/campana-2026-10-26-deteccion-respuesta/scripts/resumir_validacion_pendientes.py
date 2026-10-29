"""Agrega la salida de validar_build_rows_pendientes.py, la cruza con la duración real de cada ciclo y con los
episodios de la campaña.

Estimaciones (no mediciones en vivo): trabajo real menos el ahorro medido sin conexión en build_rows, para la
partición por entidad (t_global - t_entidad) y para «solo pendientes» (t_global - t_pendientes).
Uso: python resumir_validacion_pendientes.py --motor M --marcas marcas.jsonl --validacion t0.jsonl [t1 ...] --salida-dir D
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
    v = sorted(x for x in v if x is not None)
    return round(v[int(p * (len(v) - 1))], 2) if v else None


def ep(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True)
    ap.add_argument("--marcas", required=True)
    ap.add_argument("--validacion", nargs="+", required=True)
    ap.add_argument("--salida-dir", required=True, type=Path)
    a = ap.parse_args()
    real = collections.defaultdict(float)
    for l in open(a.motor, encoding="utf-8"):
        if '"event": "decision"' in l:
            d = json.loads(l)
            real[d["inicio_ciclo"]] = max(real[d["inicio_ciclo"]], d["logged_at"] - d["inicio_ciclo"])
    iv = {}
    for l in open(a.marcas, encoding="utf-8"):
        m = json.loads(l)
        if m.get("episodio_id") and m["evento"] in ("inicio", "fin"):
            iv.setdefault(m["episodio_id"], [None, None])[0 if m["evento"] == "inicio" else 1] = ep(m["reloj"]["pared_utc"])

    def escenario(k):
        for e, (i, f) in iv.items():
            if i <= k <= f + 60:
                return e.rsplit("-", 1)[0]
        return "pausa"

    # un ciclo puede venir de dos trabajadores (reparto solapado): se conserva una sola vez
    unicos = {}
    for f in a.validacion:
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            unicos.setdefault(r["inicio_ciclo"], r)
    regs = sorted(unicos.values(), key=lambda r: r["inicio_ciclo"])
    filas = []
    for r in regs:
        w = real.get(r["inicio_ciclo"]); tg = r.get("t_global_s")
        filas.append({"hora": r["hora"], "inicio_ciclo": r["inicio_ciclo"], "escenario": escenario(r["inicio_ciclo"]),
                      "paquetes": r.get("paquetes"), "filas_global": r.get("filas_global"),
                      "filas_variante": r.get("filas_variante"), "identicas": r["identicas"], "cubiertas": r["cubiertas"],
                      "t_global_s": tg, "t_entidad_s": r.get("t_entidad_s"), "t_pendientes_s": r.get("t_pendientes_s"),
                      "trabajo_real_s": round(w, 2) if w is not None else None,
                      "estimado_entidad_s": round(w - (tg - r["t_entidad_s"]), 2) if w is not None and tg is not None else None,
                      "estimado_pendientes_s": round(w - (tg - r["t_pendientes_s"]), 2) if w is not None and tg is not None else None,
                      "detalle": json.dumps({k: r[k] for k in ("distintas", "no_cubiertas") if k in r}) if
                      ("distintas" in r or "no_cubiertas" in r) else ""})
    a.salida_dir.mkdir(parents=True, exist_ok=True)
    with open(a.salida_dir / "pendientes-por-ciclo.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(filas[0])); wr.writeheader(); wr.writerows(filas)

    def bloque(nom, sel):
        return {"grupo": nom, "ciclos": len(sel), "identicos": sum(bool(f["identicas"]) for f in sel),
                "cubiertos": sum(bool(f["cubiertas"]) for f in sel),
                "acel_pendientes_vs_global_p50": q([f["t_global_s"] / f["t_pendientes_s"] for f in sel
                                                    if f["t_pendientes_s"]], .5),
                "real_p50_s": q([f["trabajo_real_s"] for f in sel], .5), "real_max_s": q([f["trabajo_real_s"] for f in sel], 1),
                "entidad_p50_s": q([f["estimado_entidad_s"] for f in sel], .5),
                "entidad_max_s": q([f["estimado_entidad_s"] for f in sel], 1),
                "pendientes_p50_s": q([f["estimado_pendientes_s"] for f in sel], .5),
                "pendientes_p90_s": q([f["estimado_pendientes_s"] for f in sel], .9),
                "pendientes_max_s": q([f["estimado_pendientes_s"] for f in sel], 1),
                "real_>9,5s": sum((f["trabajo_real_s"] or 0) > 9.5 for f in sel),
                "entidad_>9,5s": sum((f["estimado_entidad_s"] or 0) > 9.5 for f in sel),
                "pendientes_>9,5s": sum((f["estimado_pendientes_s"] or 0) > 9.5 for f in sel)}

    res = [bloque(n, [f for f in filas if h0 <= f["hora"] < h1]) for n, h0, h1 in TRAMOS]
    res = [r for r in res if r["ciclos"]]
    bat = [f for f in filas if "08:35:10" <= f["hora"] < "10:33:07"]
    res += [bloque("bateria:" + e, [f for f in bat if f["escenario"] == e]) for e in sorted({f["escenario"] for f in bat})]
    res.append(bloque("TOTAL", filas))
    with open(a.salida_dir / "pendientes-resumen.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(res[0])); wr.writeheader(); wr.writerows(res)
    for r in res:
        print(r)
    for f in filas:
        if not (f["identicas"] and f["cubiertas"]):
            print("FALLO", f["hora"], f["detalle"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
