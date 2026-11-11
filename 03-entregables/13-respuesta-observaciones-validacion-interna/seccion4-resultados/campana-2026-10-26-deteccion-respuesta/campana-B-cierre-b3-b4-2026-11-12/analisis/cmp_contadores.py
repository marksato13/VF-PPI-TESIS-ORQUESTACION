import json, pickle, datetime, collections, bisect
W = r"C:\Users\markp\cf-b4"; K = "10.10.20.30"
D = pickle.load(open(W + r"\span-kali-srv.pkl", "rb")); k2s = sorted(D["k2s"])
tk = [x[0] for x in k2s]
ep = lambda s: datetime.datetime.fromisoformat(s).timestamp()
mar = [json.loads(l) for l in open(W + r"\kali\corrida\marcas.jsonl", encoding="utf8") if l.strip()]
ini = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
fin = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
ag = [json.loads(l) for l in open(W + r"\agente-B4.jsonl", encoding="utf8", errors="replace") if l.strip()]
ap = sorted([(a["aplicado_en"], n["id"], n["set"]) for a in ag if a.get("evento") == "aplicacion" for n in a.get("nuevos", []) if n.get("ip") == K], key=lambda x: x[0])
L = [json.loads(l) for l in open(W + r"\set-lecturas.jsonl", encoding="utf8") if l.strip()]
byid = collections.defaultdict(list)
for x in L:
    if not x.get("ok"): continue
    e = x["sets"].get("bloqueados", {}).get(K)
    if e: byid[e["id"]].append((x["t"], e["paquetes"], e["bytes"]))
def span(a, b): return bisect.bisect_right(tk, b) - bisect.bisect_left(tk, a)
print("aplicaciones K:", len(ap), "ids con lecturas:", len(byid))
tot = {}
for e in ini:
    if e not in fin: continue
    t0, t1 = ini[e], fin[e]
    segs = [(a, i) for a, i, s in ap if t0 <= a <= t1 and i in byid]
    sc = ss = sb = 0; ratios = []
    for a, i in segs:
        rd = byid[i]; tl = rd[-1][0]; c = max(p for _, p, _ in rd); by = max(b for _, _, b in rd)
        n = span(a, tl); sc += c; ss += n; sb += by; ratios.append((c, n))
    tot[e] = (len(segs), sc, ss, sb)
    print("%-24s segmentos %3d | contador srv-dmz (suma de maximos por elemento) %5d | SPAN Kali->srv-dmz en las mismas ventanas %6d | razon %.3f | bytes contador %d" % (e, len(segs), sc, ss, sc / ss if ss else float("nan"), sb))
# ejemplo de segmentos de un escaneo
e = "escaneo_breve-r4"; t0, t1 = ini[e], fin[e]
print("ejemplo", e)
for a, i, s in ap:
    if t0 <= a <= t1 and i in byid:
        rd = byid[i]; print("  aplic +%.1f s id %s lecturas %d  1a +%.1fs pq=%d  ultima +%.1fs pq=%d | SPAN [aplic, ultima lectura]=%d, SYN=%d" % (a - t0, i[:6], len(rd), rd[0][0] - a, rd[0][1], rd[-1][0] - a, rd[-1][1], span(a, rd[-1][0]), sum(1 for x in k2s[bisect.bisect_left(tk, a):bisect.bisect_right(tk, rd[-1][0])] if x[1] == 6 and x[3] & 2 and not x[3] & 16)))
# puertos distintos (SYN sin ACK a TCP)
print("PUERTOS DISTINTOS probados (SYN) acumulados desde el inicio")
for e in ini:
    if not e.startswith("escaneo") or e not in fin: continue
    t0, t1 = ini[e], fin[e]; seen = set(); cnt = collections.Counter(); marks = {}
    pts = [10, 30, 60, 120, 180, 300, 600, 900]; syn = 0
    for ts, pr, dp, fl in k2s[bisect.bisect_left(tk, t0):bisect.bisect_right(tk, t1)]:
        if pr == 6 and fl & 2 and not fl & 16:
            seen.add(dp); cnt[dp] += 1; syn += 1
            for p in pts:
                if ts - t0 <= p: marks[p] = (len(seen), syn)
    hist = collections.Counter(cnt.values())
    print("%-22s dur %4.0f | SYN %5d | puertos distintos %5d | veces por puerto %s | acumulado(t:puertos/SYN) %s" % (e, t1 - t0, syn, len(seen), dict(sorted(hist.items())), {p: marks[p] for p in pts if p in marks}))