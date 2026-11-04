set -u
date -u +%FT%TZ; hostname
systemctl show ppi-motor ppi-motor-capture -p Id -p MainPID -p NRestarts -p DropInPaths -p ActiveState -p ExecMainStartTimestamp
echo "cmdline motor: $(tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-motor)/cmdline)"
echo "cmdline captura: $(tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-motor-capture)/cmdline)"
sha256sum ~/cyberflow/scripts/engine/motor_decision.py ~/cyberflow/scripts/engine/motor_incremental.py
ls -ld ~/cyberflow-e4 ~/feed-v2 ~/cf-e4 ~/respaldos-etapa4 2>&1
timedatectl show -p NTPSynchronized
echo "--- unidades ppi/cf"
systemctl list-units --all --no-legend 'ppi-*' 'cf-*' | awk '{print $1,$2,$3,$4}'
echo "--- sudo -n journalctl (prueba real)"
sudo -n journalctl -u ppi-motor-capture -n 2 --no-pager 2>&1 | tail -2; echo "rc=${PIPESTATUS[0]}"
echo "--- sudo -n -l"
sudo -n -l 2>&1 | head -20
echo "--- disco/memoria"
df -h /home | tail -1; free -m | grep Mem; nproc
echo "--- suricata"
systemctl show suricata -p ActiveState -p MainPID -p ExecMainStartTimestamp -p NRestarts 2>&1
ls -la --time-style=full-iso /var/log/suricata/ 2>&1 | head
tail -n 40 /var/log/suricata/stats.log 2>&1 | grep -E 'Date|capture.kernel' | tail -4
echo "--- logrotate"
systemctl list-timers --all --no-legend logrotate.timer
