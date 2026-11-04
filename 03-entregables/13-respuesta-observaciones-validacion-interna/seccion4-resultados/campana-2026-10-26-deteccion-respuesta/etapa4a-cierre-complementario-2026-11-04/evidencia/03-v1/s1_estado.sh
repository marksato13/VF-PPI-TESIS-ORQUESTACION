set -u
echo "### fecha $(date -u +%FT%TZ)"
echo "### PCAP: unidad de captura"
systemctl cat ppi-motor-capture 2>/dev/null | grep -vE '^\s*$'
systemctl show ppi-motor-capture -p User -p Group -p UMask -p MainPID -p ExecMainStartTimestamp -p NRestarts
pc=$(systemctl show -p MainPID --value ppi-motor-capture); echo "captura cmdline: $(tr '\0' ' ' < /proc/$pc/cmdline)"
for p in $pc $(pgrep -P $pc); do echo "PID $p: $(ps -o user=,group=,comm= -p $p) status:"; grep -E '^(Uid|Gid|Groups)' /proc/$p/status; done
pm=$(systemctl show -p MainPID --value ppi-motor); echo "motor: $(ps -o user=,group= -p $pm)"; grep -E '^(Uid|Gid|Groups)' /proc/$pm/status
echo "### directorio del anillo"; ls -ld /var/lib/ppi-motor-capture; ls -l --time-style=+%T /var/lib/ppi-motor-capture | head -4; ls /var/lib/ppi-motor-capture | wc -l
stat -c '%U:%G %a %n' /var/lib/ppi-motor-capture/* | awk '{print $1,$2}' | sort | uniq -c
echo "### errores pcaps ilegibles en el registro del motor"
L=~/cyberflow/logs/motor_decision.log
grep -n -E 'PermissionError|ilegible|Permission denied' $L | tail -8 | cut -c1-400
grep -c 'PermissionError' $L
echo "### journal captura al arranque 02:11"
journalctl -u ppi-motor-capture --since '2026-11-04 02:10:50' --until '2026-11-04 02:11:30' --no-pager 2>&1 | head -20
journalctl -u ppi-motor --since '2026-11-04 02:10:50' --until '2026-11-04 02:11:40' --no-pager 2>&1 | grep -iE 'perm|error|ilegible' | head
echo "### drop-in etapa4 de la captura y del motor"
cat /etc/systemd/system/ppi-motor-capture.service.d/*.conf 2>/dev/null
cat /etc/systemd/system/ppi-motor.service.d/*.conf 2>/dev/null
echo "### cadena v1 en sensor"
systemctl list-units --all --no-pager 'ppi-*' 'cf-*' | cat
systemctl list-unit-files --no-pager 'ppi-*' 'cf-*' | cat
systemctl list-timers --all --no-pager | grep -iE 'ppi|cf-'
systemctl cat ppi-publicar-feed.service ppi-publicar-feed.timer 2>/dev/null
systemctl show ppi-publicar-feed.service -p ExecStart -p TriggeredBy -p WantedBy -p RequiredBy -p After -p User
systemctl list-dependencies --reverse --no-pager ppi-publicar-feed.service | cat
ls -la ~/feed ~/feed-v2 2>/dev/null | head -30
echo "### suricata"
suricata -V 2>&1; systemctl show suricata -p MainPID -p ExecMainStartTimestamp -p NRestarts -p ExecStart
sha256sum /etc/suricata/suricata.yaml; ls -l /etc/suricata/suricata.yaml
grep -n -A30 '^af-packet:' /etc/suricata/suricata.yaml | head -80
grep -nE '^\s*(max-pending-packets|runmode|autofp-scheduler|threading:|set-cpu-affinity|detect-thread-ratio)' /etc/suricata/suricata.yaml
grep -n -A12 '^stats:' /etc/suricata/suricata.yaml | head -20
ethtool -g ens37 2>&1; ethtool -k ens37 2>/dev/null | grep -E 'generic-receive|large-receive'
nproc; free -m | head -2
