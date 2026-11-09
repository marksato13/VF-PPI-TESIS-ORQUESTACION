ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
echo "hora $(date -u +%T)Z"
echo "logrotate.timer: $(systemctl is-active logrotate.timer) / enabled=$(systemctl is-enabled logrotate.timer 2>&1)"
for u in cf-4b-tope.timer cf-4b-tope.service cf-4b-vigia.service; do echo "$u: $(systemctl is-active $u 2>&1) | $(systemctl show -p ActiveEnterTimestamp --value $u 2>/dev/null)"; done
echo "-- tope: $(systemctl show cf-4b-tope.timer -p NextElapseUSecRealtime --value 2>&1)"
systemctl list-timers --all --no-pager 2>/dev/null | grep -E "cf-4b|logrotate" | cut -c1-150
echo "-- vigía proceso: $(pgrep -af "cf-4b-rotacion vigilar" | cut -c1-120)"
echo "-- log:"; tail -4 /var/lib/cf-4b-rotacion/log.txt | cut -c1-170
echo "-- comprobar (solo lectura):"; /usr/local/sbin/cf-4b-rotacion comprobar 2>&1 | tail -10 | cut -c1-170
echo "-- medición F: $(wc -l < ~/espejo-1s-f-20261109.log) s; procesos: $(pgrep -fc "[l]t 2400")"'
