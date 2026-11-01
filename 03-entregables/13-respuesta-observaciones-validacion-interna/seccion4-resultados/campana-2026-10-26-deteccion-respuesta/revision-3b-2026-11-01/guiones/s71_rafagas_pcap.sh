# REVISION 3B q12 — sensor, solo lectura: ráfagas por intervalo de stats de Suricata desde las cabeceras PCAP
set -u
B=$HOME/cf-3b-20261101T0721Z; R=$HOME/cf-3b-revision-20261101
python3 - $B/archivo-pcap $B/analisis/suricata-stats.json $R/rafagas-por-intervalo.json <<'PY'
import sys, struct, json, glob, os, bisect
from collections import Counter
d, sp, out = sys.argv[1:]
c100, c10 = Counter(), Counter()
n = 0
for f in sorted(glob.glob(os.path.join(d, "live-*.pcap"))):
    with open(f, "rb") as fh:
        g = fh.read(24)
        if len(g) < 24: continue
        mag = struct.unpack("<I", g[:4])[0]
        div = 1e9 if mag == 0xa1b23c4d else 1e6
        while True:
            h = fh.read(16)
            if len(h) < 16: break
            s, u, incl, orig = struct.unpack("<IIII", h)
            fh.seek(incl, 1)
            t = s + u / div
            c100[int(t * 10)] += 1; c10[int(t * 100)] += 1; n += 1
st = json.load(open(sp))
res = []
for a, b in zip(st, st[1:]):
    if b["momento"] - a["momento"] > 9: continue
    # stats 'Date' tiene resolución de 1 s: se toma [a-1, b] para no omitir paquetes del borde
    m100 = max((c100.get(k, 0) for k in range(int((a["momento"] - 1) * 10), int(b["momento"] * 10) + 1)), default=0)
    m10 = max((c10.get(k, 0) for k in range(int((a["momento"] - 1) * 100), int(b["momento"] * 100) + 1)), default=0)
    tot = sum(c100.get(k, 0) for k in range(int(a["momento"] * 10), int(b["momento"] * 10)))
    res.append({"t": b["timestamp"], "momento": b["momento"], "kernel_packets": b["kernel_packets"] - a["kernel_packets"],
                "drops": b["kernel_drops"] - a["kernel_drops"], "pcap_paquetes": tot, "max_100ms": m100, "max_10ms": m10})
json.dump({"paquetes_pcap": n, "intervalos": res}, open(out, "w"))
D = [r for r in res if r["drops"] > 0]; N = [r for r in res if r["drops"] == 0 and r["pcap_paquetes"] > 0]
def q(v, p): v = sorted(v); return v[int(p * (len(v) - 1))] if v else None
for nom, g in (("con", D), ("sin", N)):
    print(nom, len(g), "max10ms p50/p90/max", q([r["max_10ms"] for r in g], .5), q([r["max_10ms"] for r in g], .9), max(r["max_10ms"] for r in g),
          "max100ms p50/p90/max", q([r["max_100ms"] for r in g], .5), q([r["max_100ms"] for r in g], .9), max(r["max_100ms"] for r in g))
for r in D: print(r["t"][11:19], r["drops"], r["pcap_paquetes"], r["max_100ms"], r["max_10ms"])
print("sin descartes con max_10ms >= min de los con descartes:", sum(1 for r in N if r["max_10ms"] >= min(x["max_10ms"] for x in D)), "de", len(N))
print("paquetes pcap", n)
PY
