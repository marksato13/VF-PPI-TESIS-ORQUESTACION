ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os
T = lambda s: int(s[:2])*3600+int(s[3:5])*60+int(s[6:8])
filas = {}
for f in ("f","g","h"):
    p = os.path.expanduser(f"~/espejo-1s-{f}-20261109.log")
    if os.path.exists(p):
        for l in open(p):
            a = l.split()
            if len(a) == 3: filas.setdefault(a[0], []).append((f, int(a[1]), int(a[2])))
ks = sorted(filas)
print("registro:", ks[0], "->", ks[-1], "| segundos con muestra:", len(ks))
# 1) huecos: segundos sin muestra entre el primero y el último
faltan = [s for s in range(T(ks[0]), T(ks[-1])+1) if "%02d:%02d:%02d" % (s//3600, s%3600//60, s%60) not in filas]
print("segundos SIN muestra en todo el registro:", len(faltan), [("%02d:%02d:%02d" % (s//3600, s%3600//60, s%60)) for s in faltan[:8]])
# duplicados entre muestreadores solapados: ¿coinciden?
dif = [(k, v) for k, v in filas.items() if len({(x[1]) for x in v}) > 1]
print("segundos con lecturas distintas entre muestreadores solapados:", len(dif), dif[:3])
# 2) contador monótono (sin reinicio) y tasa por segundo
v = {}; prev = None; rev = 0
for k in ks:
    rx = filas[k][0][1]
    if prev is not None:
        d = rx - prev[1]; dt_ = max(1, T(k) - T(prev[0]))
        if d < 0: rev += 1
        v[k] = d / dt_
    prev = (k, rx)
print("retrocesos del contador rx_packets:", rev)
# 3) la muestra de 20:36:57
k = "20:36:57"; i = ks.index(k)
print("muestra 20:36:57: rx=%d (previa %s=%d, siguiente %s=%d) -> delta previa %d paquetes en %d s" % (filas[k][0][1], ks[i-1], filas[ks[i-1]][0][1], ks[i+1], filas[ks[i+1]][0][1], filas[k][0][1]-filas[ks[i-1]][0][1], T(k)-T(ks[i-1])))
print("  vecinos consecutivos (1 s):", T(k)-T(ks[i-1]) == 1 and T(ks[i+1])-T(k) == 1, "| tasa 20:36:57 =", round(v[k]), "pkt/s; vecinos:", round(v[ks[i-1]]), round(v[ks[i+1]]))
# 4) ventana de 30 min previos al arranque: 20:08:14 -> ahora
fin = ks[-1]
ventana = [(s, round(x)) for s, x in v.items() if "20:08:14" <= s <= fin and x < 20]
print("segundos <20 pkt/s entre 20:08:14 y", fin, ":", ventana)
nuevos = [(s, round(x)) for s, x in v.items() if s > "20:38:44" and x < 20]
print("segundos <20 pkt/s DESPUÉS de las 20:38:44 (hasta", fin + "):", nuevos)
print("minutos cubiertos desde 20:08:14:", round((T(fin)-T("20:08:14"))/60, 1), "| tasa mínima excluyendo ese segundo:", round(min(x for s, x in v.items() if s >= "20:08:14" and s != "20:36:57")), "pkt/s")
PY'
