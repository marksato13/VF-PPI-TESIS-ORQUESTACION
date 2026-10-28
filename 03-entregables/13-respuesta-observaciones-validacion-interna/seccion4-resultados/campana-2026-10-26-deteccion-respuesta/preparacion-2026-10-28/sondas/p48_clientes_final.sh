#!/usr/bin/env bash
# PREP 36 — clientes: estado de los seis perfiles (activo, NRestarts, PID, inicio, argumentos) y errores en el journal
# desde su arranque. Solo lectura.
set -u
echo "## p36 clientes $(date -u +%FT%T.%3NZ) | TZ $(timedatectl show -p Timezone --value) | hora local $(date +%H:%M)"
echo "   target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for u in $(systemctl list-dependencies --plain --no-pager cyberflow-lab.target | grep -o 'cyberflow-[a-z0-9@-]*\.service' | sort -u); do
  P=$(systemctl show -p MainPID --value $u)
  echo "   $u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u) PID=$P desde=$(systemctl show -p ActiveEnterTimestamp --value $u | cut -c5-23)"
  [ "$P" != 0 ] && echo "      $(tr '\0' ' ' < /proc/$P/cmdline | cut -c1-200)"
  echo "      errores journal desde inicio: $(journalctl -u $u --since '2026-10-28 07:36:00' --no-pager 2>/dev/null | grep -ciE 'error|traceback|exception')"
done
echo "   alias: $(ip -br addr | grep -o '10\.10\.20\.2[0-9]' | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
