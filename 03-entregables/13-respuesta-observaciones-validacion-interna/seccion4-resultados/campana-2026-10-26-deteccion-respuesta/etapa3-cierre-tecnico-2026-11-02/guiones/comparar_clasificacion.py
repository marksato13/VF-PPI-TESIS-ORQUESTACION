"""Compara la clasificacion por episodio y configuracion (sin los instantes del reloj de coste)."""
import json
import sys

a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
CONF = ["IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01"]
CAMPOS = ("categoria", "senales_atribuibles", "oportunas", "senales_no_atribuibles")
dif = []
for e, vb in b["episodios"].items():
    va = a["episodios"][e]
    for c in CONF:
        x = {k: (va.get(c) or {}).get(k) for k in CAMPOS}
        y = {k: (vb.get(c) or {}).get(k) for k in CAMPOS}
        if x != y:
            dif.append((e, c, x, y))
    ta = [(w["window_end_utc"], w["estado"], w.get("atribucion")) for w in va.get("ventanas", [])]
    tb = [(w["window_end_utc"], w["estado"], w.get("atribucion")) for w in vb.get("ventanas", [])]
    if ta != tb:
        dif.append((e, "ventanas", len(ta), len(tb)))
print("diferencias (sin tiempos):", len(dif))
for d in dif:
    print(" ", json.dumps(d, ensure_ascii=False))
res = {"configuraciones": CONF, "campos": CAMPOS, "diferencias": dif}
if len(sys.argv) > 3:
    json.dump(res, open(sys.argv[3], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
