import json, collections
W = r"C:\Users\markp\cf-b4"
B3 = json.load(open(r"C:\Users\markp\cf-b3\resultado-b3.json", encoding="utf8"))["episodios"]
B4 = json.load(open(W + r"\resultado-b4.json", encoding="utf8"))["episodios"]
E1D = {x["episodio"]: x for x in json.load(open(W + r"\resultado-b4-e1-por-destino.json", encoding="utf8"))}
marcas = [json.loads(l) for l in open(W + r"\kali\corrida\marcas.jsonl", encoding="utf8") if l.strip()]
orden = [m for m in marcas if m["evento"] == "campana_inicio"][0]["tramo"]["orden_completo"]
def clases(p):
    try:
        v = [json.loads(l) for l in open(p, encoding="utf8") if l.strip()]
        c = {}
        for x in v:
            if isinstance(x.get("clases"), dict):
                for k, val in x["clases"].items(): c[k] = val if isinstance(val, str) else val.get("clase")
        return c
    except Exception as e: return {}
c3 = clases(r"C:\Users\markp\cf-b3\bastion\vigia\vigia.jsonl"); c4 = clases(W + r"\bastion\vigia\vigia.jsonl")
fila = {}
for tr, L, cl in (("B3", B3, c3), ("B4", B4, c4)):
    for r in L: fila[r["episodio"]] = (tr, r, cl.get(r["episodio"], "n/d"))
sim = {"cumple": "cumple", "verificado": "verificado", "indeterminado": "indeterminado", "no_aplica": "no aplica", "fallido": "FALLIDO"}
rows = []; tot = collections.defaultdict(collections.Counter); fam = collections.defaultdict(lambda: collections.defaultdict(list))
for i, e in enumerate(orden, 1):
    tr, r, cl = fila[e]
    e1o = r["E1"]["resultado"]; e1n = E1D[e]["resultado_por_destino"] if e in E1D else e1o
    e1 = sim[e1o] if e1o == e1n else "%s → **%s** (por destino)" % (sim[e1o], sim[e1n])
    vals = {k: r[k]["resultado"] for k in ("E2", "E3", "E4", "E5")}
    rows.append("| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (i, tr, e, r["estado_generador"], cl, e1, sim[vals["E2"]], sim[vals["E3"]], sim[vals["E4"]], sim[vals["E5"]]))
    tot["E1 original"][e1o] += 1; tot["E1 lectura por destino"][e1n] += 1
    for k, v in vals.items(): tot[k][v] += 1
    f = r["familia"]; fam[f][tr].append(e)
out = ["# Tabla de cobertura de los 25 episodios (B3 + B4)", "",
 "Dos corridas separadas: **B3** = episodios 1-6 (corrida parcial cancelada por decision de Mark tras el episodio 6, ID `4c-20261111T051928Z-2eb2f728a738`; los seis en clase de salud C0) y **B4** = episodios 7-25 (ID `4c-B4-20261111T135745Z-b0ec7e96836a`, los 19 en C0). El orden es el de `orden_completo` del generador. Fuentes: `resultado-b3.json`, `resultado-b4.json`, `resultado-b4-e1-por-destino.json`. E3 y los estados del generador son los formales; no se reclasifican.", "",
 "| Nº | Tramo | Episodio | Generador | Clase | E1 | E2 | E3 | E4 | E5 |", "|---|---|---|---|---|---|---|---|---|---|"] + rows
out += ["", "## Totales sobre los 25", "", "| Indicador | cumple/verificado | indeterminado | no aplica | fallido |", "|---|---|---|---|---|"]
for k in ("E1 original", "E1 lectura por destino", "E2", "E3", "E4", "E5"):
    c = tot[k]; ok = c["cumple"] + c["verificado"]
    out.append("| %s | %d | %d | %d | %d |" % (k, ok, c["indeterminado"], c["no_aplica"], c["fallido"]))
out += ["", "## Cobertura por familia (5 planificados por familia)", "", "| Familia | B3 (episodios) | B4 (episodios) | Total |", "|---|---|---|---|"]
for f in ("inundacion_http", "fuerza_bruta_http", "dns_inusual", "escaneo_breve", "escaneo_sostenido"):
    a, b = fam[f]["B3"], fam[f]["B4"]
    out.append("| %s | %d (%s) | %d (%s) | %d |" % (f, len(a), ", ".join(x.rsplit("-", 1)[1] for x in a) or "-", len(b), ", ".join(x.rsplit("-", 1)[1] for x in b), len(a) + len(b)))
out += ["", "Estados del generador sobre los 25: " + ", ".join("%s %d" % (k, v) for k, v in collections.Counter(fila[e][1]["estado_generador"] for e in orden).items()) + ". Los 8 `incompleto_timeout` son escaneos de B4 (conservados)."]
open(W + r"\CONSOLIDADO-25-EPISODIOS.md", "w", encoding="utf8").write("\n".join(out) + "\n")
print("\n".join(out))