set -u
# [SENSOR1 m4rk] Solo lecturas. Observación fija P4: O2, O3, O4, O5, O12 sobre la ventana 04:50:00Z–05:50:00Z.
O=~/cf-e4p/observacion-p4-20261106T0450Z; H=~/cyberflow-e4/herramientas-20261106; PY=/home/m4rk/cyberflow/.venv/bin/python
D=${1:-1793940600}; A=${2:-1793944200}; S=$O/${3:-final}; mkdir -p $S
echo "######## sensor post $(date -u +%FT%TZ) ventana $D-$A"
pgrep -af "obs_pcap|salud_captura.py muestrear" || echo "muestreadores terminados"
echo "--- eve (O3 rotación)"; ls -la --time-style=+%FT%T /var/log/suricata/ | grep -E "eve|stats"
EVES="--suricata-eve /var/log/suricata/eve.json"
for f in /var/log/suricata/eve.json.1 /var/log/suricata/eve.json.1.gz; do
  [ -f "$f" ] && [ "$(stat -c %Y "$f")" -ge "$D" ] && EVES="--suricata-eve $f $EVES" && echo "eve rotó en la ventana: $f"
done
echo "--- O4/O12 suricata-eve"
for e in $EVES; do [ "$e" = --suricata-eve ] && continue; $PY -I $H/salud_captura.py suricata-eve --eve "$e" --desde $D --hasta $A > $S/suricata-eve-$(basename $e).json; echo "rc=$? $e"; cat $S/suricata-eve-$(basename $e).json; echo; done
echo "--- O5 clasificar_periodo"
$PY -I $H/clasificar_periodo.py --salud-captura $H/salud_captura.py --muestras $O/muestras.jsonl --salida $S/clasificacion --desde $D --hasta $A $EVES > $S/clasificar.out 2>&1; echo "rc=$?"
cat $S/clasificar.out | tail -40
echo "--- O2/O3 pcap"
python3 - $O/pcap.jsonl $D $A <<'EOF'
import json, sys, datetime as dt
rs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
D, A = float(sys.argv[2]), float(sys.argv[3])
def t_nombre(r):
    return dt.datetime.strptime(r["fichero"][5:19], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
v = sorted((r for r in rs if D <= t_nombre(r) < A), key=t_nombre)
err = [r for r in v if r.get("error")]
print("ficheros que empiezan en la ventana:", len(v), "errores de formato:", len(err), err[:5])
print("primero:", v[0]["fichero"] if v else None, "último:", v[-1]["fichero"] if v else None)
saltos_n = [t_nombre(b) - t_nombre(a) for a, b in zip(v, v[1:])]
saltos_p = [b["primero"] - a["ultimo"] for a, b in zip(v, v[1:]) if a.get("ultimo") and b.get("primero")]
print("salto entre nombres consecutivos: max %.1f s (esperado 5)" % max(saltos_n))
print("hueco entre último paquete y primero del siguiente: max %.3f s" % max(saltos_p))
print("registros totales:", sum(r.get("registros", 0) for r in v), "ficheros vacíos:", sum(1 for r in v if not r.get("registros")))
print("esperados (3600/5):", 720, "faltan nombres:", 720 - len(v))
EOF
echo "--- ruleset Sensor1 después"; sudo -n nft list ruleset | sed -E "s/counter packets [0-9]+ bytes [0-9]+/counter/" | sha256sum
