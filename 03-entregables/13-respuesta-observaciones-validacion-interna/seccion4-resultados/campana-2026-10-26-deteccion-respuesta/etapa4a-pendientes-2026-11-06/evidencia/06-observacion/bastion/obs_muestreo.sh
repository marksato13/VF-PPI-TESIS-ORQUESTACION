#!/usr/bin/env bash
# [BASTIÓN gadmin] Observación fija P4 (CRITERIOS-FIJADOS.md §4): ventana 2026-11-06 04:50:00Z–05:50:00Z.
# SOLO LECTURAS cada 30 s (criterio: ≤ 60 s) en bastión, Sensor1 y srv-dmz. Empieza antes y acaba después de la
# ventana para acotar sus extremos. No modifica nada del laboratorio.
set -u
O=$HOME/evidencia-etapa4/observacion-p4-20261106T0450Z
mkdir -p "$O"
FIN=$(date -d '2026-11-06 05:51:30Z' +%s)
S="ssh -n -o BatchMode=yes -o ConnectTimeout=10"
echo "$$ $(date -u +%FT%TZ) inicio muestreo" >> "$O/muestreo.pid"
while [ "$(date +%s)" -le "$FIN" ]; do
  {
  echo "### $(date -u +%FT%TZ) $(date +%s)"
  echo "B relay pid=$(systemctl show -p MainPID --value ppi-relay-eventos) nr=$(systemctl show -p NRestarts --value ppi-relay-eventos) $(systemctl is-active ppi-relay-eventos) v1timer=$(systemctl is-active ppi-relay-feed.timer) v1=$(systemctl is-active ppi-relay-feed)"
  echo "B panel_https=$(curl -sk -m 6 -o /dev/null -w '%{http_code}' https://10.10.60.11:8788/) ultima_traza=$(tail -1 ~/relay-v2/traza.jsonl | tr -d '\000' | cut -c1-220)"
  $S -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 suricata ppi-publicar-feed-v2 ppi-dashboard; do printf "S %s pid=%s nr=%s %s\n" $u "$(systemctl show -p MainPID --value $u)" "$(systemctl show -p NRestarts --value $u)" "$(systemctl is-active $u)"; done
echo "S v1 $(systemctl is-active ppi-publicar-feed.timer)/$(systemctl is-active ppi-publicar-feed) enforce_aplicar=$(ps -eo args | grep -E -- "--(enforce|aplicar)( |$)" | grep -vc grep)"
echo "S feed_seq=$(python3 -c "import json;print(json.load(open(\"/home/m4rk/feed-v2/feed.json\"))[\"secuencia\"])" 2>&1)"
echo "S home_libre_kb=$(df --output=avail -k /home | tail -1 | tr -d " ") carga=$(cut -d" " -f1-3 /proc/loadavg) memdisp_kb=$(awk "/MemAvailable/{print \$2}" /proc/meminfo)"
echo "S ruleset=$(sudo -n nft list ruleset | sed -E "s/counter packets [0-9]+ bytes [0-9]+/counter/" | sha256sum | cut -c1-16)"
echo "S eve_ultimo_stats=$(tail -c 300000 /var/log/suricata/eve.json | grep "\"event_type\":\"stats\"" | tail -1 | python3 -c "import json,sys;e=json.load(sys.stdin);c=e[\"stats\"][\"capture\"];print(e[\"timestamp\"],e[\"stats\"][\"uptime\"],c.get(\"kernel_packets\"),c.get(\"kernel_drops\"))" 2>&1)"
echo "S anillo_ultimo=$(ls -t /var/lib/ppi-motor-capture 2>/dev/null | head -1)"' 2>&1
  $S -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
u=ppi-enforce-agent-v2-dmz; p=$(systemctl show -p MainPID --value $u)
echo "D agente pid=$p nr=$(systemctl show -p NRestarts --value $u) $(systemctl is-active $u) aplicar_cmd=$(tr "\0" " " < /proc/$p/cmdline | grep -c -- --aplicar) v1=$(systemctl is-active ppi-enforce-agent.timer)"
T=/var/lib/cyberflow/agente/traza.jsonl
echo "D aplicacion=$(sudo -n grep -c "\"evento\": \"aplicacion\"" $T) firma_invalida=$(sudo -n grep -c firma_invalida $T) paquete_invalido=$(sudo -n grep -c paquete_invalido $T) ruleset=$(sudo -n nft list ruleset | sha256sum | cut -c1-16)"
echo "D ultima=$(sudo -n tail -1 $T | cut -c1-200)"' 2>&1
  } >> "$O/muestras.txt" 2>&1
  sleep $(( 30 - $(date +%s) % 30 ))
done
echo "$(date -u +%FT%TZ) fin muestreo" >> "$O/muestreo.pid"

