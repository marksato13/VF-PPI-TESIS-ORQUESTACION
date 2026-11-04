set -u
# [Sensor1 m4rk] Correspondencia panel 93f076e <-> trazas v2 reales (solo lectura)
cd ~/cyberflow/scripts/engine
~/cyberflow/.venv/bin/python -I - <<'EOF' 2>&1 | grep -v SyntaxWarning | grep -v "const origen"
import sys, json, time, collections, hashlib
sys.path.insert(0, ".")
from pathlib import Path
import dashboard as db, cadena_v2
LOG = Path.home() / "cyberflow/logs/motor_decision.log"
V2 = Path.home() / "feed-v2"
ahora = time.time(); desde = ahora - 3600
print("ahora", time.strftime("%FT%TZ", time.gmtime(ahora)))
print("dashboard", hashlib.sha256(open("dashboard.py","rb").read()).hexdigest()[:12],
      "cadena_v2", hashlib.sha256(open("cadena_v2.py","rb").read()).hexdigest()[:12])
recs = [dict(d) for d in db._decisiones_tramo(LOG, 32 * 1024 * 1024) if float(d.get("logged_at", 0)) >= desde]
db._CADENA_V2 = idx = cadena_v2.IndiceV2(V2, "sombra")
idx.anotar(recs, ahora)
C = collections.Counter
print("decisiones última hora:", len(recs), "| ALERT:", sum(d.get("decision") == "ALERT" for d in recs))
print("acción (panel 93f076e):", dict(C((db.accion_de(d) or ("PERMIT",))[0] for d in recs)))
print("cobertura:", dict(C(d["cadena_v2"]["cobertura"] for d in recs)))
print("IF (señal α):", dict(C(d["cadena_v2"]["if"]["estado"] for d in recs)))
print("IF del motor (decision_if):", dict(C(str(d["cadena_v2"]["if_motor"]["decision_if"]) for d in recs)))
print("medida:", dict(C(d["cadena_v2"]["medida"]["estado"] for d in recs)))
print("aplicación:", dict(C(d["cadena_v2"]["aplicacion"] for d in recs)))
print("aplicación por medida:", dict(C((d["cadena_v2"]["medida"]["estado"], d["cadena_v2"]["aplicacion"]) for d in recs)))
# decisiones posteriores a la última publicación: nunca «sin_senal» ni «no_publicada»
post = [d for d in recs if d["logged_at"] > idx.traza_hasta - cadena_v2.MARGEN_LECTURA_S]
print("posteriores a la última publicación (−2 s):", len(post), "estados IF:", dict(C(d["cadena_v2"]["if"]["estado"] for d in post)),
      "medida:", dict(C(d["cadena_v2"]["medida"]["estado"] for d in post)))
sen = [json.loads(l) for l in open(V2 / "senales-if.jsonl")]
sen_h = {s["decision_id"] for s in sen if float(s.get("logged_at") or 0) >= desde}
dec_ids = {d.get("decision_id") for d in recs}
con_senal = {d["decision_id"] for d in recs if d["cadena_v2"]["if"]["estado"] == "senal"}
print("señales α en la hora:", len(sen_h), "| en el registro:", len(sen_h & dec_ids),
      "| marcadas 'senal':", len(con_senal), "| iguales:", con_senal == (sen_h & dec_ids))
tr = [json.loads(l) for l in open(V2 / "traza.jsonl")]
print("traza: publicaciones", len(tr), "secuencias", tr[0]["secuencia"], "->", tr[-1]["secuencia"],
      "| nuevos:", sum(len(p.get("nuevos", [])) for p in tr), "| huecos >30 s:", len(idx.huecos), idx.huecos[:5])
r = idx.resumen(ahora)
print("resumen:", {k: r[k] for k in ("estado", "incidencias", "politica", "modo", "traza_fresca", "huecos_traza",
                                      "feed_secuencia", "feed_edad_s", "feed_entradas", "aplicacion")})
print("vigentes:", idx.vigentes(ahora))
# simulación de fuente ausente SIN tocar ~/feed-v2: índice sobre un directorio inexistente
fx = cadena_v2.IndiceV2(Path("/nonexistent-feed-v2"), "sombra")
m = [dict(d) for d in recs[-50:]]; fx.anotar(m, ahora)
print("con fuentes ausentes:", dict(C((d["cadena_v2"]["medida"]["estado"], d["cadena_v2"]["aplicacion"]) for d in m)),
      "| acciones:", dict(C((db.accion_de(d) or ("PERMIT",))[0] for d in m)) if (setattr(db, "_CADENA_V2", fx) or True) else "",
      "| incidencias:", fx.resumen(ahora)["incidencias"][:2])
t0 = time.time(); idx._sellos = None; idx.anotar(recs, ahora); print("coste anotar %d decisiones: %.3f s" % (len(recs), time.time() - t0))
EOF
echo "--- unidad del panel (argumentos efectivos)"; tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-dashboard)/cmdline | tr ' ' '\n' | grep -nE 'modo-panel|cadena-v2|sin-cadena|modo-respuesta|demo' || echo "(sin --modo-panel: rige el valor por omisión v2)"
