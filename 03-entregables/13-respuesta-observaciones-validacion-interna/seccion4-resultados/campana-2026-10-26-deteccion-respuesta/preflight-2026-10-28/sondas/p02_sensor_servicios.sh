#!/usr/bin/env bash
# PREFLIGHT 02 — sensor: servicios, argumentos reales, unidades, permisos, interfaz, disco. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p02 sensor  inicio=$(ts)  host=$(hostname)  user=$(id -un)  grupos=$(id -Gn)"
echo "## unidades ppi/cyberflow/suricata (estado)"
systemctl list-units --all --no-pager --plain --no-legend 2>/dev/null | grep -Ei 'ppi|cyberflow|suricata' | awk '{printf "  %-44s %-9s %-9s %s\n",$1,$2,$3,$4}'
echo "## timers"
systemctl list-timers --all --no-pager --no-legend 2>/dev/null | grep -Ei 'ppi|cyberflow|suricata' | sed 's/^/  /'
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard; do
  echo "## $u"
  systemctl show "$u" -p ActiveState -p SubState -p UnitFileState -p MainPID -p NRestarts -p ActiveEnterTimestamp -p User -p Group --no-pager 2>/dev/null | sed 's/^/  /'
  echo "  ExecStart(unidad):"; systemctl cat "$u" 2>/dev/null | grep -E '^(ExecStart|ExecStartPre|User|Group|Restart|WorkingDirectory|Environment)' | sed 's/^/    /'
  pid=$(systemctl show "$u" -p MainPID --value 2>/dev/null)
  if [ -n "$pid" ] && [ "$pid" != 0 ]; then echo "  argv real (PID $pid):"; tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | sed 's/^/    /'; echo; fi
done
echo "## procesos tcpdump / motor (argv)"; ps -eo pid,user,lstart,args --no-headers 2>/dev/null | grep -E 'tcpdump|motor_decision|suricata ' | grep -v grep | sed 's/^/  /'
echo "## ¿--enforce en el motor?"; if ps -eo args --no-headers | grep -E 'motor_decision' | grep -v grep | grep -q -- '--enforce'; then echo "  SI: el motor corre con --enforce"; else echo "  NO: ningun proceso motor_decision lleva --enforce"; fi
systemctl cat ppi-motor 2>/dev/null | grep -c -- '--enforce' | sed 's/^/  ocurrencias de --enforce en la unidad: /'
echo "## sudo -n -l (NOPASSWD disponible)"; sudo -n -l 2>&1 | sed 's/^/  /' | head -40
echo "## interfaz ens37"; ip -s -s link show ens37 2>&1 | sed 's/^/  /'
echo "  promisc: $(cat /sys/class/net/ens37/flags 2>/dev/null) (bit 0x100 = PROMISC)"
echo "## disco"; df -hP / /home /var /var/lib/ppi-motor-capture /var/log/suricata 2>/dev/null | sed 's/^/  /'
echo "## timedatectl"; timedatectl 2>&1 | sed 's/^/  /'; timedatectl show-timesync --all 2>/dev/null | grep -E 'ServerName|ServerAddress|NTPMessage|Frequency|PollInterval' | sed 's/^/  /'
echo "## fin=$(ts)"
