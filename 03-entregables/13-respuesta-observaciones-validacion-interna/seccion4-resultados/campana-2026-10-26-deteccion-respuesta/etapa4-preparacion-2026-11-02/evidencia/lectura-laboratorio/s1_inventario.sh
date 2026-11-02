#!/usr/bin/env bash
# Inventario de solo lectura de Sensor1 (sin sudo, sin cambios). Enmascara valores de variables sensibles.
set +e
mask() { sed -E 's/(([A-Za-z_]*(KEY|TOKEN|PASS|SECRET|PWD)[A-Za-z_]*)=)[^ "]*/\1***/Ig'; }
echo "== fecha"; date -u +%FT%TZ; hostname; uptime; nproc; free -m; df -h / /home /var/log 2>/dev/null
echo "== unidades (cargadas)"
systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' 'suricata*' '*pcap*' '*captura*' | cat
echo "== ficheros de unidad"
systemctl list-unit-files --no-legend 'ppi-*' 'cyberflow*' 'suricata*' '*pcap*' | cat
echo "== timers"
systemctl list-timers --all --no-legend | grep -Ei 'ppi|cyber|pcap|suri|archiv' | cat
for u in $(systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' 'suricata*' '*pcap*' | awk '{print $1}'); do
  echo "---------------- $u"
  systemctl show "$u" -p FragmentPath -p DropInPaths -p User -p Group -p WorkingDirectory -p MainPID -p ActiveState \
     -p SubState -p UnitFileState -p ExecMainStartTimestamp -p NRestarts -p EnvironmentFiles | mask
  systemctl cat "$u" 2>&1 | mask
done
echo "== crontab m4rk"; crontab -l 2>&1 | mask
echo "== home"; ls -la ~ | head -60
echo "== cyberflow es repo?"; git -C ~/cyberflow rev-parse HEAD 2>&1; git -C ~/cyberflow status --porcelain 2>&1 | head -20
ls -la ~/cyberflow ~/cyberflow/scripts/engine 2>&1 | head -80
