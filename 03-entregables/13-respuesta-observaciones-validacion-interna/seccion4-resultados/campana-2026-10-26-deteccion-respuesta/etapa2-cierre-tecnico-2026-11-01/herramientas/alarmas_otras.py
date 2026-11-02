"""Senales (7 configuraciones) sobre entidades distintas del origen de ensayo, en el control y durante cada
episodio (window_end en (inicio, fin+60)). Mismos umbrales alfa que el comparador; HEUR = algun heuristico.
Uso: python alarmas_otras.py marcas.jsonl motor_decision.log umbrales.json salida.json"""
import json, sys, collections, datetime as dt
ts = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
U = json.load(open(sys.argv[3], encoding="utf-8"))
ORIGEN = "10.10.20.30"
ep = {}
for l in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(l)
    if r.get("evento") in ("inicio", "fin") and r.get("episodio_id"):
        ep.setdefault(r["episodio_id"], {})[r["evento"]] = ts(r["reloj"]["pared_utc"])
tramos = {"control": (ts("2026-11-01T07:32:00Z"), ts("2026-11-01T08:05:00Z"))}
tramos.update({e: (m["inicio"], m["fin"] + 60) for e, m in ep.items() if "fin" in m})
res = {t: {"ventanas_otras": 0, **{c: 0 for c in ["IF_" + a for a in U] + ["HEUR"] + ["HIB_" + a for a in U]},
           "entidades_HEUR": collections.Counter(), "entidades_IF_0.05": collections.Counter(), "reglas": collections.Counter()} for t in tramos}
for l in open(sys.argv[2], encoding="utf-8"):
    r = json.loads(l)
    if "decision" not in r or r.get("entity_ip") == ORIGEN:
        continue
    w = ts(r["window_end_utc"]); s = r.get("score"); hs = r.get("heuristicos") or []
    for t, (a, b) in tramos.items():
        if (t == "control" and a <= w <= b) or (t != "control" and a < w < b):
            x = res[t]; x["ventanas_otras"] += 1
            for al, u in U.items():
                fi = s is not None and s < u
                x["IF_" + al] += fi; x["HIB_" + al] += fi or bool(hs)
                if al == "0.05" and fi: x["entidades_IF_0.05"][r["entity_ip"]] += 1
            if hs:
                x["HEUR"] += 1; x["entidades_HEUR"][r["entity_ip"]] += 1
                for h in hs: x["reglas"][h.get("heuristico")] += 1
for x in res.values():
    for k in ("entidades_HEUR", "entidades_IF_0.05", "reglas"): x[k] = dict(x[k].most_common())
json.dump(res, open(sys.argv[4], "w", encoding="utf-8"), indent=1)
print("control", {k: v for k, v in res["control"].items()})
tot = collections.Counter()
for t, x in res.items():
    if t != "control":
        for k in ("ventanas_otras", "IF_0.05", "IF_0.01", "HEUR"): tot[k] += x[k]
print("episodios (suma)", dict(tot))
