set -u
# [Sensor1 m4rk] Correspondencia panel desplegado <-> trazas v2 reales (solo lectura)
cd ~/cyberflow/scripts/engine
~/cyberflow/.venv/bin/python -I - <<'EOF' 2>&1 | grep -v SyntaxWarning | grep -v "const origen"
import sys, json, time, collections
sys.path.insert(0, ".")
from pathlib import Path
import dashboard as db, cadena_v2
LOG = Path.home() / "cyberflow/logs/motor_decision.log"
V2 = Path.home() / "feed-v2"
ahora = time.time(); desde = ahora - 3600
print("dashboard", __import__("hashlib").sha256(open("dashboard.py","rb").read()).hexdigest()[:12],
      "cadena_v2", __import__("hashlib").sha256(open("cadena_v2.py","rb").read()).hexdigest()[:12])
# 1) panel v1 (como estaba ca66db5): sin cadena
db._CADENA_V2 = None
recs = [dict(d) for d in db._decisiones_tramo(LOG, 32 * 1024 * 1024) if float(d.get("logged_at", 0)) >= desde]
db.anotar_politica_modelo(recs)
v1 = collections.Counter((db.accion_de(d) or ("PERMIT",))[0] for d in recs if str(d.get("entity_ip")) not in db.NUNCA_BLOQUEAR)
# 2) panel desplegado: con cadena v2
db._CADENA_V2 = idx = cadena_v2.IndiceV2(V2, "sombra")
for d in recs: d.pop("politica_modelo", None)
idx.anotar(recs)
v2 = collections.Counter((db.accion_de(d) or ("PERMIT",))[0] for d in recs)
print("decisiones última hora:", len(recs), "| ALERT:", sum(d.get("decision") == "ALERT" for d in recs))
print("acción según panel v1 (ca66db5):", dict(v1))
print("acción según panel v2 (e0dc71d):", dict(v2))
print("IF:", dict(collections.Counter(d["cadena_v2"]["if"]["estado"] for d in recs)))
print("medida:", dict(collections.Counter(d["cadena_v2"]["medida"]["estado"] for d in recs)))
print("aplicación:", dict(collections.Counter(d["cadena_v2"]["aplicacion"] for d in recs)))
# 3) correspondencia por id con las fuentes
sen = [json.loads(l) for l in open(V2 / "senales-if.jsonl")]
sen_h = {s["decision_id"] for s in sen if float(s.get("logged_at") or 0) >= desde}
dec_ids = {d.get("decision_id") for d in recs}
con_senal = {d["decision_id"] for d in recs if d["cadena_v2"]["if"]["estado"] == "senal"}
print("señales IF en la hora:", len(sen_h), "| en el registro:", len(sen_h & dec_ids),
      "| marcadas 'senal' por el panel:", len(con_senal), "| iguales:", con_senal == (sen_h & dec_ids))
alert_sin_senal = [d["decision_id"] for d in recs if d.get("decision") == "ALERT" and d["cadena_v2"]["if"]["estado"] != "senal"]
print("ALERT del motor sin señal IF en el panel:", len(alert_sin_senal), alert_sin_senal[:3])
tr = [json.loads(l) for l in open(V2 / "traza.jsonl")]
nuevos = [x for p in tr for x in p.get("nuevos", [])]
print("traza: publicaciones", len(tr), "secuencias", tr[0]["secuencia"], "->", tr[-1]["secuencia"], "| nuevos:", len(nuevos))
print("vigentes del panel (feed v2):", db.acciones_vigentes(recs, ahora), "| entradas feed v2:", len(json.load(open(V2 / "feed.json"))["entradas"]))
r = idx.resumen(ahora)
print("resumen:", {k: r[k] for k in ("politica", "modo", "feed_secuencia", "feed_edad_s", "feed_atrasado", "feed_entradas", "aplicacion", "efecto")})
print("fuentes:", r["fuentes"])
# 4) ejemplo de una decisión ALERT de 10.10.20.24 (cliente legítimo) tal como la ve el panel
ej = next((d for d in reversed(recs) if d.get("decision") == "ALERT" and d.get("entity_ip") == "10.10.20.24"), None)
if ej: print("ejemplo:", ej["decision_id"], json.dumps(ej["cadena_v2"], ensure_ascii=False))
t0 = time.time(); idx._sellos = {}; idx.anotar(recs); print("coste anotar %d decisiones: %.3f s" % (len(recs), time.time() - t0))
EOF
