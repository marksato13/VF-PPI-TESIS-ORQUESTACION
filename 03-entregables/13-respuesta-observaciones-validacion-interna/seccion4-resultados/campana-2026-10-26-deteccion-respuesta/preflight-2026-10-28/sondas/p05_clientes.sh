#!/usr/bin/env bash
# PREFLIGHT 05 — VM de clientes legitimos: direcciones, unidades de los 6 perfiles, procesos, reloj. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p05 clientes  inicio=$(ts)  host=$(hostname)  user=$(id -un)  grupos=$(id -Gn)  uptime=$(uptime -p)"
echo "## direcciones"; ip -br addr 2>&1 | sed 's/^/  /'
echo "## unidades cyberflow-lab*"
systemctl list-units --all --no-pager --plain --no-legend 2>/dev/null | grep -Ei 'cyberflow|lab' | sed 's/^/  /'
systemctl list-unit-files --no-pager --no-legend 2>/dev/null | grep -Ei 'cyberflow|lab' | sed 's/^/  fichero: /'
systemctl show cyberflow-lab.target -p ActiveState -p UnitFileState -p InactiveEnterTimestamp -p ActiveEnterTimestamp 2>/dev/null | sed 's/^/  target: /'
for u in $(systemctl list-units --all --no-pager --plain --no-legend 'cyberflow-lab*' 2>/dev/null | awk '{print $1}' | grep '\.service$'); do
  echo "  -- $u: $(systemctl show "$u" -p ActiveState -p SubState -p Result -p NRestarts -p InactiveEnterTimestamp -p ExecMainStatus --value 2>/dev/null | tr '\n' ' ')"
  systemctl cat "$u" 2>/dev/null | grep -E '^ExecStart' | sed 's/^/       /'
done
echo "## journal reciente de los perfiles (si es legible)"
journalctl --no-pager -n 25 -u 'cyberflow-lab*' 2>&1 | sed 's/^/  /'
echo "## procesos del generador"; ps -eo pid,user,lstart,args --no-headers | grep -E 'clientes_lab|laboratorio' | grep -v grep | sed 's/^/  /' || true
echo "  (procesos encontrados: $(ps -eo args --no-headers | grep -E 'clientes_lab' | grep -vc grep))"
echo "## ficheros del generador"; ls -la ~/laboratorio 2>&1 | sed 's/^/  /'; sha256sum ~/laboratorio/*.py 2>/dev/null | sed 's/^/  /'
echo "## sudo -n -l"; sudo -n -l 2>&1 | sed 's/^/  /' | head -12
echo "## reloj"; timedatectl 2>&1 | grep -E 'Universal|synchronized|NTP service' | sed 's/^/  /'; timedatectl show-timesync 2>/dev/null | grep -E 'ServerName|ServerAddress' | sed 's/^/  /'
echo "## alcance benigno a srv-dmz:80 desde cada IP de perfil (connect TCP, sin carga)"
for i in 21 22 23 24 25 26; do
  if timeout 3 python3 - "$i" <<'PY' 2>/dev/null; then echo "  10.10.20.$i -> 10.10.30.10:80 conectado"; else echo "  10.10.20.$i -> 10.10.30.10:80 FALLO"; fi
import socket,sys
s=socket.socket(); s.settimeout(2); s.bind(("10.10.20."+sys.argv[1],0)); s.connect(("10.10.30.10",80)); s.close()
PY
done
echo "## fin=$(ts)"
