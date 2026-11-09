ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os, statistics, datetime as dt
L = [l.split() for l in open(os.path.expanduser("~/espejo-1s-20261109.log")) if len(l.split()) == 3]
t = [dt.datetime.strptime(a[0], "%H:%M:%S") for a in L]
rx = [int(a[1]) for a in L]; dr = [int(a[2]) for a in L]
r = []
for i in range(1, len(L)):
    dt_s = (t[i] - t[i-1]).total_seconds() or 1
    r.append((L[i][0], (rx[i] - rx[i-1]) / dt_s, dr[i] - dr[i-1]))
med = statistics.median(x[1] for x in r)
print(f"muestras: {len(L)} ({L[0][0]}Z -> {L[-1][0]}Z) | mediana {med:.0f} pkt/s | mín {min(x[1] for x in r):.0f} | máx {max(x[1] for x in r):.0f} | rx_dropped +{dr[-1]-dr[0]}")
bajos = [x for x in r if x[1] < 0.2 * med]
print("segundos con <20% de la mediana:", len(bajos), bajos[:12])
# ventanas de 10 s con cero paquetes
z = 0; mz = 0
for x in r:
    z = z + 1 if x[1] < 5 else 0; mz = max(mz, z)
print("racha máxima de segundos con <5 pkt/s:", mz)
PY'
