python3 - <<'PY'
import json, os, statistics, datetime as dt, glob
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%S")
for d in ("4c-cancelada-20261109T1058Z", "4c-x3-cancelada-20261109T1350Z", "4c"):
    p = os.path.expanduser(f"~/cf-e4/{d}/salud/muestras.jsonl")
    if not os.path.exists(p): print(d, "sin muestras"); continue
    ms = []
    for l in open(p):
        try:
            j = json.loads(l); ms.append((j["t"], j["interfaz"]["rx_packets"]))
        except Exception: pass
    r = []
    for (t0, a), (t1, b) in zip(ms, ms[1:]):
        if t1 - t0 > 0 and b >= a: r.append((t0, t1, (b - a) / (t1 - t0)))
    med = statistics.median(x[2] for x in r)
    bajos = [(t0, t1, v) for t0, t1, v in r if v < 0.2 * med]
    # agrupar tramos bajos contiguos
    g = []
    for t0, t1, v in bajos:
        if g and t0 - g[-1][1] < 15: g[-1][1] = t1; g[-1][2] = min(g[-1][2], v)
        else: g.append([t0, t1, v])
    print(f"== {d}: {f(ms[0][0])}Z -> {f(ms[-1][0])}Z | mediana {med:.0f} pkt/s | tramos con <20% de la mediana: {len(g)}")
    for t0, t1, v in g[:40]: print(f"   {f(t0)}-{f(t1)} ({int(t1-t0)} s) mín {v:.0f} pkt/s")
PY
