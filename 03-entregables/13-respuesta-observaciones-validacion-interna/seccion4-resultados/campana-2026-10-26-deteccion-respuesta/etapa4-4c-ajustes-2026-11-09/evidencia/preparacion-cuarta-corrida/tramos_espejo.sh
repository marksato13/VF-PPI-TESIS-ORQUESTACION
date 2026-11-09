ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os, statistics, datetime as dt
L = [l.split() for l in open(os.path.expanduser("~/espejo-1s-20261109.log")) if len(l.split()) == 3]
t = [dt.datetime.strptime(a[0], "%H:%M:%S") for a in L]; rx = [int(a[1]) for a in L]
r = [(L[i][0], (rx[i]-rx[i-1]) / max(1, (t[i]-t[i-1]).total_seconds())) for i in range(1, len(L))]
print("muestras", len(L), L[0][0], "->", L[-1][0])
g = []
for h, v in r:
    if v < 20:
        if g and (dt.datetime.strptime(h, "%H:%M:%S") - dt.datetime.strptime(g[-1][1], "%H:%M:%S")).total_seconds() <= 3: g[-1][1] = h; g[-1][2] += 1
        else: g.append([h, h, 1])
print(len(g), "tramos con <20 pkt/s (tolerando 3 s de separación):")
for a, b, n in g: print(f"   {a}Z -> {b}Z  ({n} s con <20 pkt/s)")
# tasa media por minuto
por = {}
for h, v in r: por.setdefault(h[:5], []).append(v)
print("tasa media por minuto:", " ".join(f"{k}={statistics.mean(v):.0f}" for k, v in sorted(por.items())))
PY'
