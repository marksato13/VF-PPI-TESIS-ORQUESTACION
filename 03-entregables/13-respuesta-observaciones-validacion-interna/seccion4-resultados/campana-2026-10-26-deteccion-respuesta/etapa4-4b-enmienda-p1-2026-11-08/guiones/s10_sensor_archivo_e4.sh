#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s10 — uso: s10_sensor_archivo_e4.sh <4b|4c>. Sin sudo; no toca motor, captura ni Suricata.
# Equivale al s10+s11 del 3B, con tres cambios: directorio ~/cf-e4/<fase>, rotación de 5 s, y el muestreador de
# salud (salud_captura.py) además del de recursos. Arranca, en sesiones persistentes (setsid nohup):
#   1) el archivador full-span ~/bin/archivar_captura.sh (2181af5f…, intervalo 20 s);
#   2) el muestreador de recursos (copia del aprobado en el paso 2, cambia SOLO el directorio; da ens37_rx_drop a
#      calidad_fuentes.py);
#   3) salud_captura.py muestrear cada 10 s (SALUD-CAPTURA.md §5).
# Registra el punto de partida del EVE (inodo y byte), stats.log, motor_decision.log, argv del motor y servicios.
# Resultado esperado: "## fin" con archivador, muestreador y salud con PID vivos y ESTADO.txt "OK".
# Parada: cualquier "PARAR".
#
# ENMIENDA P1 (2026-11-08, etapa4-4b-enmienda-p1-2026-11-08): el muestreador de salud es el de
# ~/cyberflow-e4/herramientas-20261106/salud_captura.py (VERSION 2026-11-06.1, sha pinned), no el de ec78ca5: stats.log de
# Suricata 7 no escribe kernel_drops a cero y la herramienta congelada daba «Suricata sin medida» (C3) en toda ventana.
# Suricata se mide por los eventos `stats` de EVE. Antes de crear nada se exige una medida EVE de Suricata (cero
# descartes o descartes; ausente/desactualizada/error/cobertura insuficiente = PARAR). No cambia ningún criterio.
set -u
FASE=${1:?uso: s10_sensor_archivo_e4.sh 4b|4c}
case "$FASE" in 4b|4c) ;; *) echo "PARAR: fase $FASE"; exit 2;; esac
B=$HOME/cf-e4/$FASE; D=$B/archivo-pcap; E4=$HOME/cyberflow-e4/ec78ca5; PY=$HOME/cyberflow/.venv/bin/python
HP=$HOME/cyberflow-e4/herramientas-20261106; SCP=$HP/salud_captura.py
SCP_SHA=274b4d613357be60e362f13ce007f07b6bb8055e0e0029316f7bafaa845344d2
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
[ "$(sha256sum "$HOME/bin/archivar_captura.sh" | cut -c1-64)" = 2181af5f8406e3aa4f41a26e24d7ec83bfaf72eee06aa3ee564e2dbba5639eb6 ] \
  || { echo "PARAR: hash del archivador"; exit 2; }
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: el código candidato no verifica"; exit 2; }
( cd "$HP" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: las herramientas P1 no verifican"; exit 2; }
[ "$(sha256sum "$SCP" | cut -c1-64)" = "$SCP_SHA" ] || { echo "PARAR: salud_captura de P1 con hash distinto"; exit 2; }
# Suricata debe poder medirse por EVE stats ANTES de empezar (la ausencia nunca vale como cero)
T1=$(( $(date -u +%s) - 30 )); T0=$(( T1 - 600 ))
EST=$("$PY" -I "$SCP" suricata-eve --eve /var/log/suricata/eve.json --desde "$T0" --hasta "$T1" 2>/dev/null \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('estado'))" 2>/dev/null)
case "$EST" in
  cero_explicito|descartes) echo "  Suricata medido por EVE stats (10 min previos): $EST";;
  *) echo "PARAR: Suricata no medible por EVE stats ('$EST'): sin datos no se empieza"; exit 2;;
esac
P=$(systemctl show -p MainPID --value ppi-motor)
tr '\0' ' ' < "/proc/$P/cmdline" | grep -q "cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py .*--disparo eventos" \
  || { echo "PARAR: el motor en ejecución no es el candidato"; exit 2; }
tr '\0' ' ' < "/proc/$P/cmdline" | grep -q -- --enforce && { echo "PARAR: el motor lleva --enforce"; exit 2; }
mkdir -p "$B/eve" "$B/recursos" "$B/salud" "$B/herramientas" "$B/estado-inicial" "$B/copias"
echo "## s10-e4 $FASE $(date -u +%FT%T.%3NZ)"
python3 -c "import os,json,time;s=os.stat('/var/log/suricata/eve.json');print(json.dumps({'t':time.time(),'inode':s.st_ino,'size':s.st_size}))" | tee "$B/eve/inicio.json"
cp -p /var/log/suricata/stats.log "$B/eve/stats-inicio.log" && echo "  stats.log inicial ($(stat -c %s "$B/eve/stats-inicio.log") bytes)"
echo "  motor_decision.log inicio: inodo $(stat -c %i "$HOME/cyberflow/logs/motor_decision.log") tam $(stat -c %s "$HOME/cyberflow/logs/motor_decision.log")" | tee "$B/eve/motor-inicio.txt"
tr '\0' ' ' < "/proc/$P/cmdline" > "$B/estado-inicial/argv-motor.txt"
# arranque exacto del motor (btime + starttime/HZ), para recalcular_caracteristicas.py --arranque-motor
python3 -c "import os,sys;b=int([l.split()[1] for l in open('/proc/stat') if l.startswith('btime')][0]);s=int(open('/proc/%s/stat'%sys.argv[1]).read().rsplit(')',1)[1].split()[19]);print('%.2f'%(b+s/os.sysconf('SC_CLK_TCK')))" "$P" > "$B/estado-inicial/arranque-motor.t"
echo "  arranque del motor (epoch): $(cat "$B/estado-inicial/arranque-motor.t")"
systemctl show -p Id -p MainPID -p NRestarts -p ActiveState -p ActiveEnterTimestamp ppi-motor ppi-motor-capture \
  ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata ppi-publicar-feed.timer > "$B/estado-inicial/servicios.txt"
sha256sum "$HOME"/feed-v2/feed.json "$HOME"/feed-v2/feed.sig "$HOME"/feed-v2/estado.json "$HOME"/feed/feed.json \
  "$HOME"/feed/feed.sig "$HOME"/feed/estado.json > "$B/estado-inicial/sha256-feed.txt" 2>&1
cp -p "$HOME"/feed-v2/estado.json "$B/estado-inicial/estado-v2.json"; cp -p "$HOME"/feed/estado.json "$B/estado-inicial/estado-v1.json"
for f in senales-rapidas.jsonl senales-if.jsonl traza.jsonl via-rapida-resumen.jsonl; do
  printf '%s %s\n' "$f" "$(stat -c %s "$HOME/feed-v2/$f" 2>/dev/null || echo 0)"; done > "$B/estado-inicial/feed-v2-bytes.txt"
# 2) muestreador de recursos (paso 2, af06bd7b…): solo cambia la línea del directorio
cat > "$B/herramientas/sensor_muestrear.sh" <<EOS
#!/usr/bin/env bash
set -u
R=$B/recursos; mkdir -p "\$R"; O=\$R/muestras.jsonl
echo \$\$ > "\$R/muestreo.pid"
HZ=\$(getconf CLK_TCK)
while :; do
  P=\$(systemctl show -p MainPID --value ppi-motor)
  read -r ut st < <(awk '{print \$14, \$15}' /proc/\$P/stat 2>/dev/null || echo "0 0")
  rss=\$(awk '/VmRSS/{print \$2}' /proc/\$P/status 2>/dev/null); hwm=\$(awk '/VmHWM/{print \$2}' /proc/\$P/status 2>/dev/null)
  ma=\$(awk '/MemAvailable/{print \$2}' /proc/meminfo); sf=\$(awk '/SwapFree/{print \$2}' /proc/meminfo); stt=\$(awk '/SwapTotal/{print \$2}' /proc/meminfo)
  pin=\$(awk '/pswpin/{print \$2}' /proc/vmstat); pout=\$(awk '/pswpout/{print \$2}' /proc/vmstat)
  read -r l1 l5 l15 _ < /proc/loadavg
  cpu=\$(awk '/^cpu /{print \$2+\$3+\$4+\$5+\$6+\$7+\$8, \$5+\$6}' /proc/stat)
  psi=\$(awk '/^some/{print \$2}' /proc/pressure/memory | cut -d= -f2)
  rx=\$(awk '/ens37/{print \$3, \$5}' /proc/net/dev)
  printf '{"t":%s,"pid":%s,"utime":%s,"stime":%s,"hz":%s,"rss_kb":%s,"hwm_kb":%s,"memavail_kb":%s,"swapfree_kb":%s,"swaptotal_kb":%s,"pswpin":%s,"pswpout":%s,"load1":%s,"cpu_total_idle":"%s","psi_mem_some10":%s,"ens37_rx_drop":"%s","anillo":%s}\n' \\
    "\$(date +%s.%N)" "\${P:-0}" "\${ut:-0}" "\${st:-0}" "\$HZ" "\${rss:-0}" "\${hwm:-0}" "\$ma" "\$sf" "\$stt" "\$pin" "\$pout" "\$l1" "\$cpu" "\${psi:-0}" "\$rx" \\
    "\$(ls /var/lib/ppi-motor-capture/ 2>/dev/null | wc -l)" >> "\$O"
  sleep 5
done
EOS
setsid nohup bash "$B/herramientas/sensor_muestrear.sh" > "$B/recursos/muestreo.out" 2>&1 < /dev/null &
# 1) archivador full-span; su rc queda en archivo-pcap.rc al terminar
setsid nohup bash -c 'D="$1"; bash "$HOME/bin/archivar_captura.sh" "$D" 20 > "$D.stdout" 2> "$D.stderr"; echo $? > "$D.rc"' _ "$D" > /dev/null 2>&1 < /dev/null &
# 3) salud de la captura cada 10 s (sin --hasta: se para en s40 con el PID guardado)
setsid nohup "$PY" -I "$SCP" muestrear --salida "$B/salud/muestras.jsonl" \
  --suricata-stats /var/log/suricata/stats.log --interfaz ens37 \
  --unidad ppi-motor --unidad ppi-motor-capture --unidad ppi-via-rapida@ens37 --unidad ppi-publicar-feed-v2 --unidad suricata \
  --anillo /var/lib/ppi-motor-capture --archivador "$D" \
  --resumen-rapida "$HOME/feed-v2/via-rapida-resumen.jsonl" --ciclos "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl" \
  --hijos-de-unidad ppi-via-rapida@ens37 --intervalo 10 > "$B/salud/muestrear.out" 2>&1 < /dev/null &
echo $! > "$B/salud/muestrear.pid"
sleep 45
AP=$(pgrep -f "archivar_captura.sh $D 20" | head -1); echo "$AP" > "$D.pid"
echo "  archivador PID=$AP  ESTADO: $(cat "$D/ESTADO.txt" 2>&1)  ficheros=$(ls "$D"/live-*.pcap 2>/dev/null | wc -l)"
grep ' OK ' "$D/archivar.log" | head -1 | sed 's/^/  primero: /'
echo "  recursos PID=$(cat "$B/recursos/muestreo.pid") muestras=$(wc -l < "$B/recursos/muestras.jsonl")"
echo "  salud PID=$(cat "$B/salud/muestrear.pid") vivo=$(kill -0 "$(cat "$B/salud/muestrear.pid")" 2>/dev/null && echo si || echo NO) muestras=$(wc -l < "$B/salud/muestras.jsonl")"
tail -1 "$B/salud/muestras.jsonl" | python3 -c "import sys,json;m=json.loads(sys.stdin.read());print('  fuentes:', {k:(v.get('ok') if isinstance(v,dict) else '-') for k,v in m.items() if isinstance(v,dict)})"
"$PY" -I "$SCP" suricata-eve --eve /var/log/suricata/eve.json --desde "$T0" --hasta "$T1" > "$B/salud/suricata-eve-inicio.json" 2>&1
echo "  salud: $SCP (sha $SCP_SHA)  Suricata inicial (EVE): $EST"
echo "## fin $(date -u +%FT%T.%3NZ)"
