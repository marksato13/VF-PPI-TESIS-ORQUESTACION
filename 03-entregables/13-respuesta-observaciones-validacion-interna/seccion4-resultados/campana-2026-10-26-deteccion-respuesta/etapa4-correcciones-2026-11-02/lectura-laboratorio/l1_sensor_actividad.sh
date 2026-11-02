#!/usr/bin/env bash
# [SENSOR1 m4rk] Lectura (sin sudo, sin cambios): ¿piloto-con-dns es actividad actual o solo una etiqueta histórica?
# Procesos y argumentos, unidades y timers, cron, escrituras recientes del dataset y de artifacts, y la etiqueta de
# campaña que escribe HOY el acumulador. Además, el histórico de descartes del kernel de Suricata (stats.log).
set -u
C=$HOME/cyberflow
echo "## l1 $(hostname) $(whoami) $(date -u +%FT%T.%3NZ)"
echo "== procesos con argumentos (cyberflow, acumulador, campaña, piloto, generador, captura)"
ps -eo pid,ppid,user,lstart,args --sort=start_time | grep -E 'cyberflow|acumul|campaign|campana|piloto|generar|perfil|tcpdump|suricata|motor|via_rapida|publicar|archivar|salud' | grep -v -E 'grep -E|l1_sensor' | cut -c1-400
echo "== unidades ppi-*/cyberflow*/cf-* (todas las cargadas) y timers"
systemctl list-units --all --no-pager --plain 'ppi-*' 'cyberflow*' 'cf-*' 2>&1 | head -40
systemctl list-timers --all --no-pager 2>&1 | grep -E 'ppi|cyberflow|cf-|logrotate|NEXT' | head -20
echo "== ExecStart de las unidades del acumulador / dataset (lectura de systemctl cat, sin sudo)"
for u in $(systemctl list-units --all --no-pager --plain --no-legend 'ppi-*' 'cyberflow*' 2>/dev/null | awk '{print $1}'); do
  systemctl cat "$u" 2>/dev/null | grep -E '^ExecStart|campaign|campana|piloto' | sed "s|^|  $u: |" | cut -c1-400
done
echo "== cron del usuario y de sistema (lectura)"
crontab -l 2>&1 | grep -v '^#' | sed 's/^/  user: /'
ls -la /etc/cron.d 2>&1 | sed 's/^/  /'
grep -l -E 'cyberflow|piloto|campaign' /etc/cron.d/* /etc/crontab 2>/dev/null | sed 's/^/  menciona: /'
echo "== dataset multilayer-v3.csv: tamaño, mtime, última fila y etiquetas de las últimas 5000 filas"
D=$C/artifacts/linea-base/multilayer-v3.csv
stat -c '  %s B mtime=%y' "$D" 2>&1
tail -1 "$D" | cut -c1-120 | sed 's/^/  última: /'
tail -n 5000 "$D" | cut -d, -f1 | sort | uniq -c | sed 's/^/  /'
echo "  última fila piloto-con-dns: $(tac "$D" | grep -m1 '^piloto-con-dns,' | cut -c1-80)"
echo "== ficheros escritos en las últimas 24 h bajo artifacts/ y logs/ (los 30 más recientes)"
find $C/artifacts $C/logs -type f -mmin -1440 -printf '%TY-%Tm-%TdT%TH:%TM %s %p\n' 2>/dev/null | sort -r | head -30 | sed 's/^/  /'
echo "== ¿algún fichero o proceso menciona piloto-con-dns fuera del dataset? (configs, unidades de usuario)"
grep -rIl --exclude='*.csv' --exclude-dir=.git --exclude-dir=artifacts -e 'piloto-con-dns' $C/config* $C/*.toml $HOME/.config/systemd 2>/dev/null | head | sed 's/^/  /'
echo "== Suricata: stats.log (actual y rotados legibles), serie de kernel_drops con su hora"
for f in /var/log/suricata/stats.log.1 /var/log/suricata/stats.log; do
  [ -r "$f" ] || { echo "  $f no legible"; continue; }
  echo "  -- $f ($(stat -c '%s B, mtime %y' "$f"))"
  awk '/^Date:/{d=$2" "$4} /capture.kernel_drops/{print d, $NF} /capture.kernel_packets/{p=$NF}' "$f" \
    | awk 'NR==1{prev=$3; print "  primera", $0; next} {if ($3>prev) print "  incremento", $1, $2, "+" $3-prev, "(acum", $3")"; prev=$3; last=$0} END{print "  última", last}' | tail -60
done
ls -la /var/log/suricata/ 2>&1 | head -20 | sed 's/^/  /'
echo "== Suricata: configuración relevante legible (af-packet, hilos, rotación de eve)"
grep -nE '^\s*(- interface|threads|cluster-type|ring-size|block-size|use-mmap|tpacket-v3|buffer-size)' /etc/suricata/suricata.yaml 2>&1 | head -20 | sed 's/^/  /'
cat /etc/logrotate.d/suricata 2>&1 | sed 's/^/  logrotate: /'
systemctl show -p ActiveEnterTimestamp -p NRestarts suricata 2>&1 | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
