"""Coste de ciclo, memoria y latencia de decision por episodio (y en el control) a partir de un replay.
Uso: python rendimiento_episodios.py marcas.jsonl dir_replay salida.json"""
import json, sys, statistics as st, datetime as dt
ts = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
ep = {}
for l in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(l)
    if r.get("evento") in ("inicio", "fin") and r.get("episodio_id"):
        ep.setdefault(r["episodio_id"], {})[r["evento"]] = ts(r["reloj"]["pared_utc"])
ep["control"] = {"inicio": ts("2026-11-01T07:32:00Z"), "fin": ts("2026-11-01T08:05:00Z")}
ciclos = [json.loads(l) for l in open(sys.argv[2] + "/ciclos-arnes.jsonl", encoding="utf-8")]
dec = []
for l in open(sys.argv[2] + "/motor_decision.log", encoding="utf-8"):
    r = json.loads(l)
    if "decision" in r and "logged_at" in r:
        dec.append((ts(r["window_end_utc"]), r["logged_at"] - ts(r["window_end_utc"])))
def p(v, q):
    v = sorted(v); return round(v[min(len(v) - 1, int(q * len(v)))], 3) if v else None
out = {}
for e, m in sorted(ep.items()):
    a, b = m["inicio"], m["fin"] + 60
    cs = [c for c in ciclos if a <= c["t"] <= b]
    lat = [x for w, x in dec if a < w <= b]
    out[e] = {"ciclos": len(cs), "ciclo_p50_s": p([c["dur_s"] for c in cs], .5), "ciclo_max_s": max((c["dur_s"] for c in cs), default=None),
              "rss_max_mb": max((c.get("rss_mb", 0) for c in cs), default=None), "pico_mb": max((c.get("pico_mb", 0) for c in cs), default=None),
              "decisiones": len(lat), "latencia_p50_s": p(lat, .5), "latencia_p90_s": p(lat, .9), "latencia_max_s": max(lat, default=None)}
json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
for e, v in out.items():
    if e.startswith("inundacion") or e == "control":
        print(e, v)
