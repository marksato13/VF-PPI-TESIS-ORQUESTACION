"""Analisis del replay 4.3 con la regla FIJADA en PROTOCOLO-REPLAY-4.3.md (hash en FIJADO.txt). Offline. No ajusta nada a los datos."""
import csv, collections, datetime as dt, json, math, os, sys
from pathlib import Path

R = Path(os.environ.get("CF43_DIR", "."))   # carpeta de trabajo (ver README, seccion Reproduccion)
EXT = R / "extractos"
A3B = Path(os.environ.get("CF43_ANALISIS3B", str(R / "analisis-3b.json")))   # analisis-3b.json de s50 v2
KALI = "10.10.20.30"
iso = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00") if s.endswith("Z") else s)
ts = lambda s: iso(s).timestamp()
SERV = {"inundacion_http": {("TCP", 80)}, "fuerza_bruta_http": {("TCP", 18081)}, "dns_inusual": {("UDP", 53), ("TCP", 53)}, "escaneo_sostenido": "TCP*", "escaneo_breve": "TCP*"}


def excl(firma):  # exclusiones del conteo de deteccion (regla §2.2)
    return firma.startswith("SURICATA STREAM ") or firma.startswith("ET INFO ")


def cp(k, n, a=0.05):  # Clopper-Pearson exacto por biseccion
    if n == 0: return (None, None)
    def cdf(x, p):  # P(X<=x)
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, x + 1))
    lo = 0.0 if k == 0 else None; hi = 1.0 if k == n else None
    if lo is None:
        a_, b_ = 0.0, 1.0
        for _ in range(60):
            m = (a_ + b_) / 2
            if 1 - cdf(k - 1, m) > a / 2: b_ = m
            else: a_ = m
        lo = (a_ + b_) / 2
    if hi is None:
        a_, b_ = 0.0, 1.0
        for _ in range(60):
            m = (a_ + b_) / 2
            if cdf(k, m) > a / 2: a_ = m
            else: b_ = m
        hi = (a_ + b_) / 2
    return (lo, hi)


def pct(k, n):
    lo, hi = cp(k, n); return "%d/%d (%.0f %%; IC95 %.0f–%.0f %%)" % (k, n, 100 * k / n, 100 * lo, 100 * hi)


EP = list(csv.DictReader(open(R / "episodios-elegibles.csv", encoding="utf-8")))
A = json.load(open(A3B, encoding="utf8"))["episodios"]
INV = {r["episodio_id"]: r for r in csv.DictReader(open(R / "episodios-campana-A-4c.csv", encoding="utf-8-sig"))}
INCLUIDOS = {e["episodio_id"] for e in EP}
PRIN, SENS = "HIB_0.01", "HIB_0.03"   # CORRECCION-ALFA-2026-11-11: principal HIB_0.01; HIB_0.03 = sensibilidad
CFG = ["HIB_0.01", "IF_0.01", "HEUR", "HIB_0.03", "IF_0.03"]


def alertas(cfg, sl):
    p = EXT / cfg / sl / "alertas.jsonl"
    return [json.loads(l) for l in open(p, encoding="utf-8")] if p.exists() else None


def estado(sl):
    p = EXT / (sl + ".estado")
    return open(p).read().strip() if p.exists() else "ausente"


def cf_episodio(e):
    a = A[e["episodio_id"]]; t0, t1 = ts(e["inicio_utc"]), ts(e["fin_utc"]); out = {}
    for c in CFG:
        sig = [w for w in a["ventanas"] if c in (w.get("senales") or []) and w.get("atribucion") == "atribuible"]
        sig.sort(key=lambda w: w["window_end_utc"])
        dur = [w for w in sig if ts(w["window_end_utc"]) <= t1]
        post = [w for w in sig if ts(w["window_end_utc"]) > t1]
        out[c] = {"durante": len(dur), "posterior": len(post), "primera_s": round(ts((dur or post)[0]["window_end_utc"]) - t0, 2) if (dur or post) else None,
                  "primera_durante_s": round(ts(dur[0]["window_end_utc"]) - t0, 2) if dur else None, "categoria_oficial": a[c]["categoria"]}
    return out


def suri_episodio(e, cfg):
    sl = e["episodio_id"]; al = alertas(cfg, sl)
    if al is None or estado(sl) != "OK %s" % sl and not estado(sl).startswith("OK"): return None
    t0, t1 = ts(e["inicio_utc"]), ts(e["fin_utc"]); dest = e["destino"]; fam = e["familia"]
    c = collections.Counter(); validas = []; excl_n = collections.Counter(); fuera = collections.Counter()
    for a in al:
        f = a["firma"] or ""
        if excl(f):
            excl_n["STREAM" if f.startswith("SURICATA STREAM ") else "ET INFO"] += 1; continue
        t = ts(a["timestamp"])
        if not (t0 <= t <= t1 + 60): fuera["tiempo"] += 1; continue
        par = {a["src_ip"], a["dest_ip"]}
        if par != {KALI, dest}: fuera["origen_destino"] += 1; continue
        srv = a["dest_port"] if a["src_ip"] == KALI else a["src_port"]
        pr = (a["proto"] or "").upper()
        reg = SERV[fam]
        ok = (pr == "TCP") if reg == "TCP*" else ((pr, srv) in reg)
        if not ok: fuera["comportamiento"] += 1; continue
        validas.append((t, a))
    validas.sort(key=lambda x: x[0])
    dur = [(t, a) for t, a in validas if t <= t1]; post = [(t, a) for t, a in validas if t > t1]
    nosurif = [(t, a) for t, a in validas if not a["firma"].startswith("SURICATA ")]
    ndur = [(t, a) for t, a in dur if not a["firma"].startswith("SURICATA ")]
    return {"durante": len(dur), "posterior": len(post), "primera_s": round((dur or post)[0][0] - t0, 2) if validas else None, "primera_durante_s": round(dur[0][0] - t0, 2) if dur else None,
            "sids": sorted({(a["sid"], a["firma"][:70]) for t, a in validas}), "excluidas": dict(excl_n), "no_atribuibles": dict(fuera), "durante_sin_SURICATA_otros": len(ndur), "total_alertas": len(al)}


filas = []
for e in EP:
    cf = cf_episodio(e)
    fila = {"episodio": e["episodio_id"], "familia": e["familia"], "destino": e["destino"], "inicio": e["inicio_utc"], "fin": e["fin_utc"], "cf": cf, "estado_slice": estado(e["episodio_id"])}
    for cfg in ("principal", "s1"): fila[cfg] = suri_episodio(e, cfg)
    filas.append(fila)
json.dump(filas, open(R / "resultados-por-episodio.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ tabla por episodio y coincidencias
FAMS = ["dns_inusual", "inundacion_http", "fuerza_bruta_http", "escaneo_sostenido", "escaneo_breve"]
def det_cf(f, c): return f["cf"][c]["durante"] > 0
def det_su(f, cfg): return None if f[cfg] is None else f[cfg]["durante"] > 0
def coincide(a, b):
    if a is None or b is None: return "indeterminado"
    return "ambos" if a and b else "solo_CyberFlow" if a else "solo_Suricata" if b else "ninguno"

md = []
md.append("| Episodio | Fam. | CF HIB_0.01 (oficial) | CF t datos (s) | CF IF_0.01 / HEUR | CF HIB_0.03 (sens.) | Suricata PRINCIPAL durante / posterior | 1.ª válida (s) | SIDs válidos | Suricata S1 durante | Coincidencia (principal) |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|")
for f in filas:
    cf = f["cf"]; p = f["principal"]; s1 = f["s1"]
    md.append("| `%s` | %s | %s | %s | %s / %s | %s | %s | %s | %s | %s | %s |" % (
        f["episodio"], f["familia"].replace("_http", "").replace("_inusual", ""), cf[PRIN]["categoria_oficial"], cf[PRIN]["primera_durante_s"] if cf[PRIN]["durante"] else ("post %s" % cf[PRIN]["primera_s"] if cf[PRIN]["posterior"] else "—"),
        "sí" if det_cf(f, "IF_0.01") else "no", "sí" if det_cf(f, "HEUR") else "no", "sí" if det_cf(f, SENS) else "no",
        "indeterminado" if p is None else "%d / %d" % (p["durante"], p["posterior"]), "—" if not p or p["primera_s"] is None else p["primera_s"],
        "; ".join("%s %s" % (sid, fm[:34]) for sid, fm in (p["sids"] if p else [])[:3]) or "—",
        "indeterminado" if s1 is None else ("%d" % s1["durante"]), coincide(det_cf(f, PRIN), det_su(f, "principal"))))
TABLA_EP = "\n".join(md)

cov = []; coin = collections.defaultdict(collections.Counter); coin_s = collections.defaultdict(collections.Counter)
def fam_rows(sel):
    return [f for f in filas if sel(f)]
cov.append("| Familia | n | CF HIB_0.01 (principal) | CF IF_0.01 | CF HEUR | CF HIB_0.03 (sens.) | Suricata principal | Suricata S1 (HOME_NET original) | Principal sin `SURICATA *` restantes |")
cov.append("|---|---|---|---|---|---|---|---|---|")
for fam in FAMS + ["TOTAL"]:
    fs = filas if fam == "TOTAL" else [f for f in filas if f["familia"] == fam]
    n = len(fs)
    def k(fn): return sum(1 for f in fs if fn(f))
    kp = [f for f in fs if f["principal"] is not None]; ks = [f for f in fs if f["s1"] is not None]
    cov.append("| %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (fam, n, pct(k(lambda f: det_cf(f, PRIN)), n), pct(k(lambda f: det_cf(f, "IF_0.01")), n), pct(k(lambda f: det_cf(f, "HEUR")), n), pct(k(lambda f: det_cf(f, SENS)), n),
        pct(sum(1 for f in kp if det_su(f, "principal")), len(kp)) if kp else "indeterminado", pct(sum(1 for f in ks if det_su(f, "s1")), len(ks)) if ks else "indeterminado",
        pct(sum(1 for f in kp if f["principal"]["durante_sin_SURICATA_otros"] > 0), len(kp)) if kp else "indeterminado"))
    if fam != "TOTAL":
        for f in fs:
            coin[fam][coincide(det_cf(f, PRIN), det_su(f, "principal"))] += 1; coin_s[fam][coincide(det_cf(f, SENS), det_su(f, "principal"))] += 1
    else:
        for fam2 in FAMS:
            for kx, v in coin[fam2].items(): coin["TOTAL"][kx] += v
            for kx, v in coin_s[fam2].items(): coin_s["TOTAL"][kx] += v
COB = "\n".join(cov)
co = ["| Familia | ambos | solo CyberFlow | solo Suricata | ninguno | indeterminado |", "|---|---|---|---|---|---|"]
for fam in FAMS + ["TOTAL"]:
    c = coin[fam]; co.append("| %s | %d | %d | %d | %d | %d |" % (fam, c["ambos"], c["solo_CyberFlow"], c["solo_Suricata"], c["ninguno"], c["indeterminado"]))
COIN = "\n".join(co)
co2 = ["| Familia (sensibilidad HIB_0.03) | ambos | solo CyberFlow | solo Suricata | ninguno | indeterminado |", "|---|---|---|---|---|---|"]
for fam in FAMS + ["TOTAL"]:
    c = coin_s[fam]; co2.append("| %s | %d | %d | %d | %d | %d |" % (fam, c["ambos"], c["solo_CyberFlow"], c["solo_Suricata"], c["ninguno"], c["indeterminado"]))
COIN_S = "\n".join(co2)

# ------------------------------------------------------------------ latencia (solo donde ambos alertan, durante o posterior)
lat = ["| Episodio | CyberFlow HIB_0.01 (s, datos) | Suricata (s, paquete) | Δ = Suricata − CF (s) | Lectura |", "|---|---|---|---|---|"]
nlat = 0
for f in filas:
    p = f["principal"]; cfp = f["cf"][PRIN]["primera_s"]
    if p is None or p["primera_s"] is None or cfp is None: continue
    nlat += 1; d = round(p["primera_s"] - cfp, 2)
    lat.append("| `%s` | %s | %s | %+.2f | %s |" % (f["episodio"], cfp, p["primera_s"], d, "no concluyente (< 10 s, rejilla de CyberFlow)" if abs(d) < 10 else ("Suricata primero" if d < 0 else "CyberFlow primero")))
LAT = "\n".join(lat) if nlat else "(ningún episodio cumple la condición: ambos con detección)"

# ------------------------------------------------------------------ control: misma unidad
rows = [json.loads(l[2:]) for l in open(R / "control-extracto-sensor1.txt", encoding="utf-8-sig") if l.startswith("R ")]
THR01, THR03 = -0.6223889502095352, -0.5898535710336618
pop = {(r[0], r[1]) for r in rows}
ents = {r[0] for r in rows}
cf_pairs = {c: set() for c in CFG}
for r in rows:
    if r[2] is not None and r[2] < THR01: cf_pairs["IF_0.01"].add((r[0], r[1])); cf_pairs["HIB_0.01"].add((r[0], r[1]))
    if r[2] is not None and r[2] < THR03: cf_pairs["IF_0.03"].add((r[0], r[1])); cf_pairs["HIB_0.03"].add((r[0], r[1]))
    if r[4]: cf_pairs["HEUR"].add((r[0], r[1])); cf_pairs["HIB_0.01"].add((r[0], r[1])); cf_pairs["HIB_0.03"].add((r[0], r[1]))
wins = sorted({r[1] for r in rows})
def wend(t):  # primer multiplo de 10 s >= t
    return dt.datetime.fromtimestamp(math.ceil(t / 10) * 10, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
ctl = {}
for cfg in ("principal", "s1"):
    al = alertas(cfg, "control_30min")
    if al is None: ctl[cfg] = None; continue
    pares = set(); sidc = collections.Counter(); ex = collections.Counter(); fuera = collections.Counter(); validas = []
    for a in al:
        f = a["firma"] or ""
        if excl(f): ex["STREAM" if f.startswith("SURICATA STREAM ") else "ET INFO"] += 1; continue
        w = wend(ts(a["timestamp"]))
        ent = (a.get("flujo") or {}).get("src_ip") or a["src_ip"]
        if w not in wins: fuera["fuera_de_intervalo"] += 1; continue
        if ent not in ents: fuera["entidad_fuera_de_poblacion:" + ent] += 1; continue
        pares.add((ent, w)); sidc[(a["sid"], f[:60])] += 1; validas.append(a)
    ctl[cfg] = {"pares": pares, "ventanas": {w for _, w in pares}, "sids": sidc, "excluidas": ex, "fuera": fuera, "validas": len(validas), "total": len(al)}
cf_w = {c: {w for _, w in cf_pairs[c]} for c in CFG}
ct = ["| Detector / configuración | Unidad A: entidad-ventana con señal (de %d) | Unidad B: ventana de 10 s con señal (de %d) | Alertas/eventos válidos |" % (len(pop), len(wins)), "|---|---|---|---|"]
for c in CFG:
    ct.append("| CyberFlow `%s` | %d (%.2f %%) | %d (%.1f %%) | %d señales entidad-ventana |" % (c, len(cf_pairs[c]), 100 * len(cf_pairs[c]) / len(pop), len(cf_w[c]), 100 * len(cf_w[c]) / len(wins), len(cf_pairs[c])))
for cfg, nom in (("principal", "Suricata ET Open — HOME_NET principal"), ("s1", "Suricata ET Open — HOME_NET original (S1)")):
    x = ctl[cfg]
    if x is None: ct.append("| %s | indeterminado | indeterminado | — |" % nom); continue
    ct.append("| %s | %d (%.2f %%) | %d (%.1f %%) | %d alertas válidas (de %d totales) |" % (nom, len(x["pares"]), 100 * len(x["pares"]) / len(pop), len(x["ventanas"]), 100 * len(x["ventanas"]) / len(wins), x["validas"], x["total"]))
CTL = "\n".join(ct)
CTL_DET = []
for cfg in ("principal", "s1"):
    x = ctl[cfg]
    if x:
        CTL_DET.append("**%s** — excluidas del conteo: %s; no contadas (fuera de población/intervalo): %s; firmas contadas: %s" % (cfg, dict(x["excluidas"]), dict(x["fuera"]), [(s, f, n) for (s, f), n in x["sids"].most_common(10)]))
open(R / "RESULTADOS-TABLAS.md", "w", encoding="utf-8").write("\n\n".join(["## Tabla por episodio", TABLA_EP, "## Cobertura por familia", COB, "## Coincidencias (CyberFlow HIB_0.01 vs Suricata principal)", COIN, "## Sensibilidad: coincidencias con HIB_0.03", COIN_S, "## Latencia comparativa", LAT, "## Control legítimo 30 min", CTL, "\n\n".join(CTL_DET)]) + "\n")
print(open(R / "RESULTADOS-TABLAS.md", encoding="utf-8").read())
json.dump({"ctl": {k: (None if v is None else {"pares": len(v["pares"]), "ventanas": len(v["ventanas"]), "validas": v["validas"], "total": v["total"], "excluidas": dict(v["excluidas"]), "fuera": dict(v["fuera"]), "sids": [[s, f, n] for (s, f), n in v["sids"].most_common()]}) for k, v in ctl.items()},
           "cf_control": {c: {"pares": len(cf_pairs[c]), "ventanas": len(cf_w[c])} for c in CFG}, "poblacion_pares": len(pop), "ventanas": len(wins)}, open(R / "resultados-control.json", "w"), indent=1, ensure_ascii=False)
