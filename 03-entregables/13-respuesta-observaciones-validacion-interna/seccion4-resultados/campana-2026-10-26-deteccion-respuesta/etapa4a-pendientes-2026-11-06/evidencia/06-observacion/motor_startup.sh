set -u
# [SENSOR1 m4rk] Solo lecturas: ¿por qué verificar_sensor1 no encuentra el motor_startup del candidato?
L=/home/m4rk/cyberflow/logs/motor_decision.log
ls -la --time-style=+%FT%T /home/m4rk/cyberflow/logs/ | grep -E "motor_decision"
echo "motor activo desde: $(systemctl show -p ActiveEnterTimestamp --value ppi-motor)"
echo "motor_startup en el registro actual: $(grep -cF '"event": "motor_startup"' $L)"
grep -F '"event": "motor_startup"' $L | tail -1 | cut -c1-600
for f in $L.1 $L.1.gz $L.2.gz; do [ -f $f ] || continue; echo "== $f"; (zcat -f $f | grep -F '"event": "motor_startup"' | tail -1 | cut -c1-600); done
echo "primera línea del registro actual:"; head -1 $L | cut -c1-200
grep -rl motor_decision /etc/logrotate.d 2>/dev/null; cat /etc/logrotate.d/*cyberflow* 2>/dev/null | head -30
journalctl -u ppi-motor --no-pager -b 2>/dev/null | grep -i -m3 -E "startup|umbral|threshold" | cut -c1-300
