B=~/cf-e4/4c; C=$B/copias
echo "== config que leyó s50 v2"; sha256sum ~/cf-e4/herramientas/config-campana-4c.json | cut -c1-64; grep -E "config-campana-4c.json" ~/cf-e4/herramientas/herramientas-e4.sha256 | cut -c1-64
echo "== modelo y manifiesto desplegados"
M=~/cyberflow/artifacts/preliminar/limpio-2026-10
ls $M | head; sha256sum $M/if_limpio_2026_10_desplegable.joblib | cut -c1-64
python3 - <<PY
import json, glob
for p in sorted(glob.glob("$M/manifest*.json"))[:2]:
    j = json.load(open(p)); print(p.split("/")[-1], {k: j[k] for k in j if "umbral" in k.lower() or "threshold" in k.lower() or "sha" in k.lower() or "alpha" in k.lower() or "contam" in k.lower()})
PY
echo "== argumentos del motor (replay y servicio)"; tr ' ' '\n' < $B/replay/args-motor.txt | grep -E "^--(model|manifest|detector|umbral|threshold)" -A1 | head -12
systemctl cat ppi-motor 2>/dev/null | grep -E "ExecStart|model-path|manifest-path|umbral" | cut -c1-240 | head -4
echo "== umbrales REGISTRADOS por el motor en las decisiones (copias/motor_decision.log y replay)"
python3 - <<PY
import json, collections, datetime as dt
UD, U05, U03, U01 = -0.5693969936322356, -0.5694578968203694, -0.5898535710336618, -0.6223889502095352
def leer(p):
    n = collections.Counter(); ths = collections.Counter(); filas = []
    for l in open(p, errors="replace"):
        try: j = json.loads(l)
        except Exception: continue
        if j.get("event") != "decision": continue
        n["decisiones"] += 1
        u = j.get("umbral", j.get("threshold"))
        ths[repr(u)] += 1
        if isinstance(j.get("score"), (int, float)): filas.append((j.get("entity_ip"), j["window_end_utc"], j["score"], j.get("decision")))
    return n, ths, filas
for nombre, p in (("copias/motor_decision.log (en vivo)", "$C/motor_decision.log"), ("replay/motor_decision.log", "$B/replay/motor_decision.log")):
    n, ths, filas = leer(p)
    print(nombre, dict(n), "| umbrales registrados:", dict(ths.most_common(5)))
n, ths, filas = leer("$C/motor_decision.log")
# banda entre el umbral recalibrado 0.05 y el desplegado: el motor alertaría (score < UD) pero IF_0.05 del análisis no (score >= U05)
banda = [f for f in filas if U05 <= f[2] < UD]
print("ventanas con score en [U05, UD) (alerta del motor en vivo, no IF_0.05 del análisis):", len(banda), "de", len(filas), "con score")
print("   por IP:", dict(collections.Counter(f[0] for f in banda).most_common(8)))
t = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
marc = {}
for l in open("$C/marcas.jsonl"):
    j = json.loads(l)
    if j.get("evento") in ("inicio", "fin"): marc.setdefault(j["episodio_id"], {})[j["evento"]] = t(j["reloj"]["pared_utc"])
kali = [f for f in banda if f[0] == "10.10.20.30"]
dentro = [(f, e) for f in kali for e, m in marc.items() if m["inicio"] - 60 <= t(f[1]) <= m["fin"] + 60]
print("   de Kali (10.10.20.30):", len(kali), "| dentro de [inicio-60, fin+60] de algún episodio:", len(dentro))
for f, e in dentro[:12]: print("     ", e, f[1], round(f[2], 8), f[3])
ctrl = [f for f in banda if "2026-11-09T21:23:00" <= f[1][:19] <= "2026-11-09T21:53:00"]
print("   dentro del control 21:23-21:53Z:", len(ctrl), "| ver detalle:", dict(collections.Counter(f[0] for f in ctrl).most_common(5)))
print("ventanas del control con score < U05 (IF_0.05 del análisis):", sum(1 for f in filas if f[2] < U05 and "2026-11-09T21:23:00" <= f[1][:19] <= "2026-11-09T21:53:00"),
      "| con score < UD (motor en vivo):", sum(1 for f in filas if f[2] < UD and "2026-11-09T21:23:00" <= f[1][:19] <= "2026-11-09T21:53:00"))
PY