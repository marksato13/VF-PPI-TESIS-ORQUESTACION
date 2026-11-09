ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os
T = lambda s: int(s[:2])*3600+int(s[3:5])*60+int(s[6:8])
v = {}
for f in ("f","g","h"):
    p = os.path.expanduser(f"~/espejo-1s-{f}-20261109.log")
    if not os.path.exists(p): continue
    L = [l.split() for l in open(p) if len(l.split()) == 3]
    for i in range(1, len(L)): v[L[i][0]] = (int(L[i][1]) - int(L[i-1][1])) / max(1, T(L[i][0]) - T(L[i-1][0]))
ks = sorted(v)
i = ks.index("20:36:57")
print("alrededor de 20:36:57Z:", [(k, int(v[k])) for k in ks[i-6:i+7]])
bajos = [(k, int(x)) for k, x in v.items() if x < 100 and k >= "20:08:14"]
print("segundos <100 pkt/s desde 20:08:14:", sorted(bajos))
print("percentil 1 de la tasa desde 20:08:14:", sorted(x for k, x in v.items() if k >= "20:08:14")[len([1 for k in v if k >= "20:08:14"])//100])
PY'
