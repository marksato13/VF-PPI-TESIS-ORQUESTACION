C=~/cf-e4/4c/copias
echo "senales-rapidas.jsonl: $(wc -l < $C/feed-v2/senales-rapidas.jsonl) líneas, $(stat -c %s $C/feed-v2/senales-rapidas.jsonl) B"
head -c 700 $C/feed-v2/senales-rapidas.jsonl; echo
python3 - <<PY
import json, datetime as dt, collections
C = "$C"
t = lambda s: dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
marc = {}
for l in open(f"{C}/marcas.jsonl"):
    j = json.loads(l)
    if j.get("evento") in ("inicio", "fin"): marc.setdefault(j["episodio_id"], {})[j["evento"]] = t(j["reloj"]["pared_utc"])
sen = []
for l in open(f"{C}/feed-v2/senales-rapidas.jsonl"):
    try: sen.append(json.loads(l))
    except Exception: pass
print("señales totales:", len(sen), "| claves:", sorted(sen[0].keys()) if sen else None)
def ts(s):
    for k in ("emitida_en", "t_emision", "ts", "logged_at", "t", "emitido_en", "registro_escrito_en", "momento"):
        if k in s:
            v = s[k]
            try: return float(v)
            except Exception: return t(v)
    return None
print("ejemplo:", json.dumps(sen[0])[:420] if sen else "")
por = collections.defaultdict(list)
for s in sen:
    x = ts(s)
    if x is None: continue
    for e, m in marc.items():
        if m["inicio"] - 5 <= x <= m["fin"] + 120: por[e].append((round(x - m["inicio"], 2), s.get("regla") or s.get("rule") or s.get("tipo"), s.get("entity_ip") or s.get("origen") or s.get("ip")))
for e in sorted(marc):
    if e.startswith("escaneo"):
        v = por.get(e, [])
        print(f"{e:22} dur={marc[e]['fin']-marc[e]['inicio']:5.1f}s señales rápidas en [inicio-5, fin+120]: {len(v)}", v[:3])
PY
echo "== 4B (8 h): señales rápidas en control"; python3 - <<PY
import json
j = json.load(open("$HOME/cf-e4/4b/analisis/control-4b.json"))
v = j["via_rapida"]; print("senales:", v.get("senales"), "| por_regla:", v.get("por_regla"), "| significado:", str(v.get("significado"))[:120])
PY