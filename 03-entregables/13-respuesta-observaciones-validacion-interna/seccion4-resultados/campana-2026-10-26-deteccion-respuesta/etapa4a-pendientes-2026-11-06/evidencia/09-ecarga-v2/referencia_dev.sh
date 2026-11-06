set -u
# [SENSOR1 m4rk] SOLO LECTURA. Paquete 38ee91d (reglas K4a/K4b fijadas y publicadas ANTES de esta lectura).
# 1) Flow-timeouts reales de Suricata (cuándo se emite un evento flow tras el último paquete).
# 2) Referencia de DESARROLLO de K4a/K4b (no es E-carga ni la calibra): ventanas del 04-nov con generadores activos
#    (base 4A y ensayo del anillo) y la ventana del 06-nov sin generadores.
# 3) Comprobación en seco del fin de obs_pcap.py para la franja propuesta.
P=~/cf-e4/paquete-38ee91d/deploy/etapa4/sensor1
echo "######## $(date -u +%FT%TZ) paquete $(cd ~/cf-e4/paquete-38ee91d && sha256sum SHA256SUMS | cut -c1-16)"
echo "######## 1. flow-timeouts y flow (suricata.yaml, solo lectura)"
sha256sum /etc/suricata/suricata.yaml | cut -c1-16
awk '/^flow-timeouts:/{p=1} p&&/^[a-z]/&&!/^flow-timeouts:/{p=0} p' /etc/suricata/suricata.yaml | grep -vE '^\s*#' | head -40
grep -nE '^\s*-?\s*flow(:|$)|^\s*flow:' /etc/suricata/suricata.yaml | head -5
B=/var/log/suricata/eve.json.1-2026110600.backup
echo "######## 2. referencia de desarrollo; fichero $B: primera/última marca"
head -c 400 $B | grep -o '"timestamp":"[^"]*"' | head -1; tail -c 2000 $B | grep -o '"timestamp":"[^"]*"' | tail -1
for v in "base4A 1793758785 1793762391" "ensayo-anillo 1793773615 1793777215"; do set -- $v
  echo "== $1 ($2 - $3)"
  python3 -I $P/evaluar_ecarga.py perfiles --eve $B --desde $2 --hasta $3 | python3 -c '
import json,sys; r=json.load(sys.stdin)
if "error" in r: print("ERROR", r["error"]); sys.exit()
print("K4a cumple:", r["K4a"]["cumple"]); [print("  ", n, p["flujos_por_tramo"]) for n,p in r["K4a"]["perfiles"].items()]
b=r["K4b"]; print("K4b:", {k:b[k] for k in ("estado","flujos","intervalos","intervalos_con_actividad","media_por_intervalo","mediana_por_intervalo","lambda_ref","umbral_suma_40s","max_suma_40s")}); print("  episodios:", b["episodios"])'
  echo "rc=${PIPESTATUS[0]}"
done
echo "== obs-06nov (1793940600 - 1793944200), eve.json actual"
python3 -I $P/evaluar_ecarga.py perfiles --eve /var/log/suricata/eve.json --desde 1793940600 --hasta 1793944200 | python3 -c '
import json,sys; r=json.load(sys.stdin); print("K4a cumple:", r["K4a"]["cumple"], {n:p["flujos_por_tramo"] for n,p in r["K4a"]["perfiles"].items()}); print("K4b:", r["K4b"]["estado"])'
echo "######## 3. obs_pcap.py --en-seco (fin = fin de ventana + 60 s)"
python3 -I $P/obs_pcap.py --dir /var/lib/ppi-motor-capture --salida /tmp/no-se-usa --hasta-epoch 1794197760 --hasta-iso 2026-11-09T04:16:00Z --en-seco; echo "rc=$?"
echo "-- con el error del 06-nov (debe dar rc 2):"
python3 -I $P/obs_pcap.py --dir /var/lib/ppi-motor-capture --salida /tmp/no-se-usa --hasta-epoch 1793945490 --hasta-iso 2026-11-06T05:51:30Z --en-seco; echo "rc=$?"
ls -d /tmp/no-se-usa 2>/dev/null || echo "(no se creó /tmp/no-se-usa: en seco no escribe)"
echo "######## 4. calendario: zona del Sensor1 $(timedatectl show -p Timezone --value)"
python3 -I -c '
import datetime as d
for e,n in ((1794191400,"P0"),(1794193200,"T_g arranque generadores"),(1794194100,"inicio ventana"),(1794197700,"fin ventana"),(1794197760,"fin obs_pcap"),(1794197820,"parada generadores"),(1794198600,"analisis desde")):
    u=d.datetime.fromtimestamp(e,d.timezone.utc); p=u.astimezone(d.timezone(d.timedelta(hours=-5)))
    print(e, n, u.strftime("%a %F %T UTC"), "|", p.strftime("%a %F %T Peru (UTC-5)"), "| weekday UTC", u.weekday())'
