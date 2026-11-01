#!/usr/bin/env bash
# PASO3B s10 — sensor: arranca el ARCHIVADOR FULL-SPAN revisado (~/bin/archivar_captura.sh, 2181af5f..., intervalo 20 s)
# y el muestreador de recursos (5 s) en sesiones persistentes (setsid nohup), y registra el punto de partida del EVE
# (inodo y byte) y de stats.log. No toca motor, captura ni Suricata. NO es cf-capturar (solo Kali).
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; D=$B/archivo-pcap
[ -d "$B" ] || { echo "PARAR: falta $B"; exit 2; }
[ -e "$D" ] && { echo "PARAR: ya existe $D"; exit 2; }
mkdir -p "$D" "$B/eve" "$B/recursos" "$B/herramientas"
echo "## s10 $(date -u +%FT%T.%3NZ)"
echo "  archivador: $(sha256sum $HOME/bin/archivar_captura.sh | cut -c1-64)"
python3 -c "import os,json,time;s=os.stat('/var/log/suricata/eve.json');print(json.dumps({'t':time.time(),'inode':s.st_ino,'size':s.st_size}))" | tee "$B/eve/inicio.json"
cp -p /var/log/suricata/stats.log "$B/eve/stats-inicio.log" && echo "  stats.log inicial copiado ($(stat -c %s $B/eve/stats-inicio.log) bytes)"
echo "  motor_decision.log inicio: inodo $(stat -c %i $HOME/cyberflow/logs/motor_decision.log) tam $(stat -c %s $HOME/cyberflow/logs/motor_decision.log)" | tee "$B/eve/motor-inicio.txt"
# muestreador (copia del guion aprobado del paso 2 con el directorio de esta ejecucion)
sed "s#^ID=.*#ID=$ID#; s#cf-paso2-\$ID#cf-3b-\$ID#" $HOME/cf-paso2-20261101T0254Z/herramientas/sensor_muestrear.sh > "$B/herramientas/sensor_muestrear.sh"
grep -n 'cf-3b' "$B/herramientas/sensor_muestrear.sh" | sed 's/^/  | /'
setsid nohup bash "$B/herramientas/sensor_muestrear.sh" > "$B/recursos/muestreo.out" 2>&1 < /dev/null &
# archivador full-span; su rc queda en archivo-pcap.rc al terminar
setsid nohup bash -c 'D="$1"; bash $HOME/bin/archivar_captura.sh "$D" 20 > "$D.stdout" 2> "$D.stderr"; echo $? > "$D.rc"' _ "$D" > /dev/null 2>&1 < /dev/null &
sleep 30
AP=$(pgrep -f "archivar_captura.sh $D 20" | head -1); echo "$AP" > "$D.pid"
echo "  archivador PID=$AP cmdline=$(tr '\0' ' ' < /proc/$AP/cmdline 2>/dev/null)"
echo "  muestreador PID=$(cat $B/recursos/muestreo.pid) muestras=$(wc -l < $B/recursos/muestras.jsonl)"
echo "  ESTADO.txt: $(cat $D/ESTADO.txt 2>&1)  ficheros=$(ls $D/live-*.pcap 2>/dev/null | wc -l)"
grep ' OK ' $D/archivar.log | head -1 | sed 's/^/  primero: /'; tail -2 $D/archivar.log | sed 's/^/  | /'
echo "## fin $(date -u +%FT%T.%3NZ)"
