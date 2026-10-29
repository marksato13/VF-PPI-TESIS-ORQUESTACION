"""Duración de trabajo de cada ciclo del motor frente a bytes de PCAP en la historia de 230 s."""
import bisect, collections, datetime, json, re, sys

motor, archlog = sys.argv[1], sys.argv[2]
HIST = 230
C = collections.OrderedDict()
for l in open(motor, encoding="utf-8"):
    d = json.loads(l)
    if d.get("event") != "decision":
        continue
    c = C.setdefault(d["inicio_ciclo"], {"fin": 0, "n": 0})
    c["fin"] = max(c["fin"], d["logged_at"]); c["n"] += 1
# PCAP: live-YYYYmmddHHMMSS.pcap (bytes) -> inicio del fichero
pc = []
for l in open(archlog, encoding="utf-8"):
    m = re.search(r" OK live-(\d{14})\.pcap \((\d+) bytes\)", l)
    if m:
        t = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc).timestamp()
        pc.append((t, int(m.group(2))))
pc.sort(); ts = [t for t, _ in pc]; acc = [0]
for _, b in pc:
    acc.append(acc[-1] + b)
rows = []
for k, c in C.items():
    if k < ts[0] + HIST or k > ts[-1]:
        continue
    i, j = bisect.bisect_left(ts, k - HIST), bisect.bisect_left(ts, k)
    rows.append((k, c["fin"] - k, (acc[j] - acc[i]) / 1e6, c["n"]))
print("ciclos con historia PCAP completa:", len(rows))
# correlación y tramos por volumen
import statistics as st
x = [r[2] for r in rows]; y = [r[1] for r in rows]
mx, my = st.mean(x), st.mean(y)
cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
r = cov / (sum((a - mx) ** 2 for a in x) ** .5 * sum((b - my) ** 2 for b in y) ** .5)
pend = cov / sum((a - mx) ** 2 for a in x)
print(f"Pearson r(trabajo, MB en 230 s) = {r:.3f}; pendiente {pend:.3f} s/MB; ordenada {my - pend * mx:.2f} s")
for lo, hi in [(0, 5), (5, 20), (20, 40), (40, 60), (60, 80), (80, 120), (120, 999)]:
    sel = [b for a, b in zip(x, y) if lo <= a < hi]
    if sel:
        sel.sort()
        print(f"  {lo:>3}-{hi:<3} MB: ciclos={len(sel):4d} trabajo p50={sel[len(sel)//2]:5.1f} s p90={sel[int(.9*(len(sel)-1))]:5.1f} s max={sel[-1]:5.1f} s")
f = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%S")
print("10 ciclos más largos:")
for k, w, mb, n in sorted(rows, key=lambda r: -r[1])[:10]:
    print(f"  {f(k)} trabajo={w:5.1f} s MB_230s={mb:6.1f} decisiones={n}")
