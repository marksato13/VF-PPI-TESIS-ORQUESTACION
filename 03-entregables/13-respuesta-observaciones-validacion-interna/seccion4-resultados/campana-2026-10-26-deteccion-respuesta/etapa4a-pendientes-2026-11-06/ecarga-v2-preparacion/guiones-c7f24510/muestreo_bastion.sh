#!/usr/bin/env bash
# [BASTIÓN gadmin] Muestreo de E-carga v2 cada 30 s (criterio <= 60 s) en bastión, Sensor1, srv-dmz y clientes, con la
# guardia de §3.7 tras cada muestra. Las lecturas de B/S/D son las MISMAS que obs_muestreo.sh del 06-nov
# (evidencia/06-observacion), parametrizadas; se añade la línea C (estado de los generadores, solo lectura).
#
#   muestreo_bastion.sh DIR FIN_EPOCH PARADA_EPOCH real|seco
#
#   real: si la guardia da «parar», o al llegar a PARADA_EPOCH, PARA los generadores (una sola vez) con
#         generadores.sh parar en el host de clientes. Nunca los arranca.
#   seco: hace las mismas lecturas y evalúa la guardia, pero NUNCA para nada: solo escribe «SECO: se pararía».
# Sale al pasar FIN_EPOCH. Deja: muestras.txt, guardia.jsonl, eventos.log y muestreo.pid en DIR (no sobrescribe: si
# DIR/muestras.txt ya existe, aborta).
set -u
O=${1:?DIR}; FIN=${2:?FIN_EPOCH}; PARADA=${3:?PARADA_EPOCH}; MODO=${4:?real|seco}
case "$MODO" in real|seco) ;; *) echo "modo $MODO no válido"; exit 2;; esac
AQUI="$(cd "$(dirname "$0")" && pwd)"
[ -e "$O/muestras.txt" ] && { echo "ABORTA: $O/muestras.txt ya existe (no se sobrescribe)"; exit 2; }
mkdir -p "$O"
S="ssh -n -o BatchMode=yes -o ConnectTimeout=10"
# Sin -n: el guion generadores.sh entra por stdin.
CLI="ssh -o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
log() { echo "$(date -u +%FT%TZ) $(date +%s) $*" | tee -a "$O/eventos.log"; }
parado=0
parar_generadores() {  # $1 = motivo
  if [ "$parado" = 1 ]; then return; fi
  if [ "$MODO" = seco ]; then log "SECO: se pararían los generadores ($1)"; parado=1; return; fi
  log "PARADA de generadores: $1"
  $CLI 'bash -s parar' < "$AQUI/generadores.sh" >> "$O/eventos.log" 2>&1; log "parada rc=$?"; parado=1
}
echo "$$ $(date -u +%FT%TZ) inicio muestreo modo=$MODO fin=$FIN parada=$PARADA" >> "$O/muestreo.pid"
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
  $CLI 'bash -s estado' < "$AQUI/generadores.sh" 2>&1 | sed 's/^/C /'
  } >> "$O/muestras.txt" 2>&1
  g=$(python3 -I "$AQUI/guardia.py" "$O/muestras.txt"); echo "$g" >> "$O/guardia.jsonl"
  case "$g" in *'"parar": true'*) parar_generadores "guardia: $(python3 -c 'import json,sys;print("; ".join(json.loads(sys.argv[1])["motivos"])[:400])' "$g")";; esac
  [ "$(date +%s)" -ge "$PARADA" ] && parar_generadores "fin previsto (PARADA_EPOCH $PARADA)"
  sleep $(( 30 - $(date +%s) % 30 ))
done
echo "$(date -u +%FT%TZ) fin muestreo" >> "$O/muestreo.pid"
