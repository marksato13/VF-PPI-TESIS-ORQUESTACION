#!/usr/bin/env python3
"""Etapa 2: ¿cuanto prorrogan las ventanas SIN trafico propio (score None) las restricciones?

Pasa las decisiones de un replay (motor_decision.log), en orden de logged_at, por
`incorporar` REAL del publicador v2 candidato (politica if_senal), dos veces:
  A) todas las decisiones (comportamiento del candidato tal cual);
  B) solo las decisiones con score (requisito R-E3.1: una ventana sin trafico
     propio no crea entradas nuevas).
Para cada episodio del origen de ensayo informa: eventos creados, nivel maximo de
la escalera y `hasta` final de la restriccion vigente (ip|destino|alcance) medido
desde el fin del episodio. Simulacion: no toca ningun host.

Uso (desde la raiz de la rama candidata):
  python -I simular_renovaciones.py --repo . --replay <dir> --marcas marcas.jsonl --salida x.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def ts(x: str) -> float:
    return dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--replay", type=Path, required=True)
    ap.add_argument("--marcas", type=Path, required=True)
    ap.add_argument("--origen", default="10.10.20.30")
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts" / "engine"))
    import publicar_feed_v2 as P  # noqa: E402

    dec = [json.loads(l) for l in (a.replay / "motor_decision.log").open(encoding="utf-8")]
    dec = sorted((d for d in dec if d.get("event") == "decision"), key=lambda d: d["logged_at"])
    marcas = [json.loads(l) for l in a.marcas.open(encoding="utf-8")]
    ini = {m["episodio_id"]: ts(m["reloj"]["pared_utc"]) for m in marcas if m.get("evento") == "inicio"}
    fin = {m["episodio_id"]: ts(m["reloj"]["pared_utc"]) for m in marcas if m.get("evento") == "fin"}
    t_min, t_max = ts(dec[0]["window_end_utc"]), ts(dec[-1]["window_end_utc"])
    eps = sorted((ini[e], fin[e], e) for e in ini if e in fin and t_min <= ini[e] <= t_max)

    res = {"replay": a.replay.name, "decisiones": len(dec), "variantes": {}}
    for nombre, filtro in (("A_todas", lambda d: True), ("B_solo_con_score", lambda d: d.get("score") is not None)):
        estado: dict = {}
        nuevos = []
        for d in dec:
            if filtro(d):
                for n in P.incorporar([d], estado, P.NUNCA_BLOQUEAR_V2, "if_senal", d["logged_at"]):
                    nuevos.append(n)
        por_ep = []
        for k, (t0, t1, e) in enumerate(eps):
            sig = eps[k + 1][0] if k + 1 < len(eps) else t_max + 600
            ns = [n for n in nuevos if n["ip"] == a.origen and t0 - 10 < ts(n["window_end_utc"]) <= sig]
            if not ns:
                por_ep.append({"episodio": e, "eventos": 0})
                continue
            por_dest = {}
            for n in ns:
                x = por_dest.setdefault(n["destino"], {"eventos": 0, "hasta_max_tras_fin_s": None,
                                                        "ultima_ventana_tras_fin_s": None, "acciones": set()})
                x["eventos"] += 1
                x["acciones"].add(n["accion"])
                h = n["hasta"] - t1
                x["hasta_max_tras_fin_s"] = round(max(h, x["hasta_max_tras_fin_s"] or h))
                w = ts(n["window_end_utc"]) - t1
                x["ultima_ventana_tras_fin_s"] = round(max(w, x["ultima_ventana_tras_fin_s"] or w))
            for x in por_dest.values():
                x["acciones"] = sorted(x["acciones"])
            niveles = [v["nivel"] for k2, v in estado.get("eventos", {}).items()
                       if v["ip"] == a.origen and t0 - 10 < ts(k2.split("|")[1]) <= sig]
            por_ep.append({"episodio": e, "eventos": len(ns), "por_destino": por_dest,
                           "nivel_max": max(niveles) if niveles else None})
        res["variantes"][nombre] = {
            "eventos_totales": len(nuevos),
            "eventos_origen_ensayo": sum(1 for n in nuevos if n["ip"] == a.origen),
            "otras_ips_con_eventos": sorted({n["ip"] for n in nuevos if n["ip"] != a.origen}),
            "episodios": por_ep}
    a.salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for v, r in res["variantes"].items():
        print(v, "eventos", r["eventos_totales"], "otras_ips", r["otras_ips_con_eventos"])
        for e in r["episodios"]:
            print("  ", e["episodio"], e.get("eventos"), e.get("nivel_max"),
                  {k: (x["eventos"], x["hasta_max_tras_fin_s"], x["ultima_ventana_tras_fin_s"])
                   for k, x in e.get("por_destino", {}).items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
