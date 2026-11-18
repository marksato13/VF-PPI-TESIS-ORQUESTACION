python3 - <<'PY'
import os, statistics, datetime as dt
L = [l.split() for l in open(os.path.expanduser("~/espejo-1s-B-nueva-20261111.log")) if len(l.split()) == 3]
t = [dt.datetime.strptime(a[0], "%H:%M:%S") for a in L]; rx = [int(a[1]) for a in L]; dr = [int(a[2]) for a in L]
r = []
for i in range(1, len(L)):
    dtm = (t[i] - t[i-1]).total_seconds()
    if dtm < 0: dtm += 86400
    r.append((L[i][0], (rx[i] - rx[i-1]) / max(1.0, dtm), dtm))
print("muestras", len(L), L[0][0], "->", L[-1][0], "| mínimo %.0f pkt/s, mediana %.0f, máximo %.0f" % (min(v for _, v, _ in r), statistics.median(v for _, v, _ in r), max(v for _, v, _ in r)))
bajos = [(h, v) for h, v, _ in r if v < 20]
print("segundos < 20 pkt/s:", len(bajos), bajos[:10])
print("intervalo de muestreo máximo: %.0f s" % max(d for _, _, d in r), "| rx_dropped acumulado +%d" % (dr[-1] - dr[0]))
por = {}
for h, v, _ in r: por.setdefault(h[:5], []).append(v)
print("tasa media por minuto:", " ".join("%s=%.0f" % (k, statistics.mean(v)) for k, v in sorted(por.items())))
PY
