#!/usr/bin/env bash
# PREFLIGHT 07 — srv-dmz: servicios objetivo, endpoint 18081 y su log, agente de enforcement, nftables, feed. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p07 srv-dmz  inicio=$(ts)  host=$(hostname)  user=$(id -un)  uptime=$(uptime -p)"
echo "## reloj"; timedatectl 2>&1 | grep -E 'Universal|synchronized|NTP service' | sed 's/^/  /'; timedatectl show-timesync 2>/dev/null | grep -E 'ServerName|ServerAddress' | sed 's/^/  /'
echo "## escuchas TCP (80/443/18081/22)"; ss -ltnp 2>/dev/null | awk 'NR==1||/:(80|443|18081|22) /' | sed 's/^/  /'
sudo -n ss -ltnp 2>/dev/null | grep -E ':(80|443|18081) ' | sed 's/^/  [root] /'
echo "## unidades relevantes"
systemctl list-units --all --no-pager --plain --no-legend 2>/dev/null | grep -Ei 'ppi|cyberflow|nginx|apache|http|brute|lab' | awk '{printf "  %-40s %-9s %-9s %s\n",$1,$2,$3,$4}'
for u in ppi-brute-lab.service ppi-enforce-agent.timer ppi-enforce-agent.service; do
  echo "  -- $u: $(systemctl show "$u" -p ActiveState -p SubState -p UnitFileState -p NRestarts -p ActiveEnterTimestamp -p LastTriggerUSec --value 2>/dev/null | tr '\n' ' ')"
done
echo "  ExecStart agente: $(systemctl show ppi-enforce-agent.service -p ExecStart --value 2>/dev/null | sed -E 's/.*argv\[\]=([^;]*);.*/\1/')"
echo "  ExecStart endpoint: $(systemctl show ppi-brute-lab.service -p ExecStart --value 2>/dev/null | sed -E 's/.*argv\[\]=([^;]*);.*/\1/')"
echo "## log del endpoint (ultimas 6 lineas; incluye las 3 peticiones del preflight)"
sudo -n tail -n 6 /opt/brute-lab/brute.log 2>&1 | sed 's/^/  /'
echo "  lineas totales: $(sudo -n wc -l < /opt/brute-lab/brute.log 2>/dev/null)"
echo "## journal del agente (ultimas 8)"; sudo -n journalctl --no-pager -u ppi-enforce-agent.service -n 8 2>&1 | sed 's/^/  /'
echo "## nftables (consulta real; si falla NO equivale a vacio)"
if out=$(sudo -n nft list table inet cyberflow 2>&1); then
  echo "  consulta OK (rc=0):"; echo "$out" | sed 's/^/    /'
  for s in cyberflow_bloqueados cyberflow_limitados; do
    if o=$(sudo -n nft -j list set inet cyberflow "$s" 2>&1); then
      n=$(echo "$o" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(sum(len(x["set"].get("elem",[])) for x in d["nftables"] if "set" in x))')
      echo "  set $s: consulta OK, elementos=$n"
    else echo "  set $s: CONSULTA FALLIDA ($o) -> estado DESCONOCIDO"; fi
  done
else echo "  CONSULTA FALLIDA (rc!=0): $out -> estado DESCONOCIDO"; fi
echo "## otras tablas nft (nombres)"; sudo -n nft list tables 2>&1 | sed 's/^/  /'
echo "## feed / estado del agente"
for d in /var/lib/ppi-enforce /var/lib/cyberflow /etc/cyberflow /opt/cyberflow ~/feed ~/cyberflow-agent; do [ -e "$d" ] && { echo "  $d:"; sudo -n ls -la "$d" 2>&1 | sed 's/^/    /' | head -12; }; done
echo "## scripts de sombra/restauracion presentes"
find ~ /opt /usr/local -maxdepth 3 \( -name 'modo_sombra.sh' -o -name 'restaurar_enforcement.sh' \) 2>/dev/null | while read -r f; do echo "  $(sha256sum "$f" | cut -c1-64) $f"; done; echo "  (fin)"
echo "## respaldos de sombra previos"; ls -ld ~/cf-sombra* /var/backups/cf-sombra* 2>/dev/null | sed 's/^/  /' || echo "  ninguno"
echo "## sudo -n -l (resumen)"; sudo -n -l 2>&1 | grep -E 'NOPASSWD|ALL' | sed 's/^/  /' | head -6
echo "## disco"; df -hP / | sed 's/^/  /'
echo "## fin=$(ts)"
