ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os
T = lambda s: int(s[:2])*3600+int(s[3:5])*60+int(s[6:8])
H = lambda s: "%02d:%02d:%02d" % (s//3600, s%3600//60, s%60)
for f in ("g","h"):
    L = [l.split() for l in open(os.path.expanduser(f"~/espejo-1s-{f}-20261109.log")) if len(l.split()) == 3]
    r = [(L[i][0], T(L[i][0]) - T(L[i-1][0]), int(L[i][1]) - int(L[i-1][1])) for i in range(1, len(L))]
    ven = [(s, dt, d) for s, dt, d in r if "20:08:14" <= s <= "20:38:44"]
    print(f"muestreador {f}: {len(ven)} intervalos en la ventana 20:08:14-20:38:44; intervalos de 2 s o más (muestra perdida por deriva): {sum(1 for _, dt, _ in ven if dt > 1)}; máximo {max(dt for _, dt, _ in ven)} s")
    print("   intervalos con <20 pkt/s:", [(s, dt, d, round(d/dt)) for s, dt, d in ven if d/dt < 20])
    print("   intervalos con <100 pkt/s:", len([1 for s, dt, d in ven if d/dt < 100]))
# lo que ve H alrededor de los instantes de G
L = [l.split() for l in open(os.path.expanduser("~/espejo-1s-h-20261109.log")) if len(l.split()) == 3]
h = {L[i][0]: int(L[i][1]) - int(L[i-1][1]) for i in range(1, len(L))}
for s in ("20:30:29","20:30:30","20:30:31","20:33:23","20:33:24","20:33:25"): print("H", s, h.get(s))
PY'
