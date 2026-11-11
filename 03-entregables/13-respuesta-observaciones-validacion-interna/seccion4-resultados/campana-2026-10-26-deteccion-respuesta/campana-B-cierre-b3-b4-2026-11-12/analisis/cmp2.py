import json, pickle, datetime, collections, bisect
W = r"C:\Users\markp\cf-b4"; K = "10.10.20.30"
D = pickle.load(open(W + r"\span-kali-srv.pkl", "rb")); k2s = sorted(D["k2s"]); tk = [x[0] for x in k2s]
ep = lambda s: datetime.datetime.fromisoformat(s).timestamp()
mar = [json.loads(l) for l in open(W + r"\kali\corrida\marcas.jsonl", encoding="utf8") if l.strip()]
ini = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
fin = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
L = [json.loads(l) for l in open(W + r"\set-lecturas.jsonl", encoding="utf8") if l.strip()]
rd = [(x["t"], x["sets"]["bloqueados"].get(K)) for x in L if x.get("ok")]
def span(a, b): return bisect.bisect_right(tk, b) - bisect.bisect_left(tk, a)
print("episodio | lecturas con Kali | resets (id nuevo o contador baja) | contador observado (cota inferior) | cota superior (+SPAN en huecos de reset) | SPAN misma ventana | observado/SPAN | superior/SPAN | huecos de lectura >3 s")
for e in ini:
    if e not in fin or e.startswith(("dns", "inund")): continue
    a, b = ini[e], fin[e]
    w = [(t, el) for t, el in rd if a <= t <= b + 60 and el]
    if len(w) < 2: continue
    obs = w[0][1]["paquetes"]; resets = 0; gaps = 0; extra = 0; prev = w[0]
    for t, el in w[1:]:
        p0, p1 = prev[1], el
        if t - prev[0] > 3: gaps += 1
        if p1["id"] != p0["id"] or p1["paquetes"] < p0["paquetes"]:
            resets += 1; obs += p1["paquetes"]; extra += span(prev[0], t)
        else:
            obs += p1["paquetes"] - p0["paquetes"]
        prev = (t, el)
    sp = span(w[0][0], w[-1][0])
    print("%-22s | %3d | %3d | %5d | %5d | %6d | %.3f | %.3f | %d" % (e, len(w), resets, obs, obs + extra, sp, obs / sp, (obs + extra) / sp, gaps))
# puerto atipico
pc = collections.Counter(x[2] for x in k2s if x[1] == 6 and x[3] & 2 and not x[3] & 16 and ini["escaneo_sostenido-r5"] <= x[0] <= fin["escaneo_sostenido-r5"])
print("puertos con mas SYN en sostenido-r5:", pc.most_common(3))
pc = collections.Counter(x[2] for x in k2s if x[1] == 6 and x[3] & 2 and not x[3] & 16 and ini["escaneo_breve-r4"] <= x[0] <= fin["escaneo_breve-r4"]); print("breve-r4:", pc.most_common(3))
# paquetes Kali->srv que NO son SYN en escaneo (por tipo)
e = "escaneo_breve-r4"; c = collections.Counter((x[1], x[3]) for x in k2s if ini[e] <= x[0] <= fin[e]); print("breve-r4 tipos (proto, flags):", c.most_common(6))
# tasa SPAN por 10 s antes y despues de la 1a aplicacion en breve-r4