#!/usr/bin/env bash
# PASO3B c02 — srv-dmz (solo lectura): sombra (agente inactivo, timer desactivado, sin tabla nft de CyberFlow) y
# servicios del laboratorio. Cada consulta privilegiada informa su rc: un error de permisos NO prueba ausencia.
set -u
echo "## c02 $(hostname) $(date -u +%FT%T.%3NZ)"
for u in ppi-enforce-agent.timer ppi-enforce-agent.service ppi-brute-lab.service lab-web-http.service lab-web-https.service; do
  echo "  $u active=$(systemctl is-active $u 2>&1) enabled=$(systemctl is-enabled $u 2>&1)"
done
T=$(sudo -n nft list tables 2>&1); rc=$?
echo "  sudo -n nft list tables rc=$rc -> $(echo "$T" | tr '\n' ' ')"
[ $rc -eq 0 ] && { echo "$T" | grep -q 'inet cyberflow' && echo "  ATENCION: existe inet cyberflow" || echo "  consulta correcta (rc=0): NO existe la tabla inet cyberflow"; }
R=$(sudo -n nft list ruleset 2>&1); rc=$?; echo "  nft list ruleset rc=$rc, lineas=$(echo "$R" | wc -l), menciones cyberflow=$(echo "$R" | grep -ci cyberflow)"
echo "  iptables: $(sudo -n iptables -S 2>&1 | grep -ci cyberflow) reglas cyberflow (rc=${PIPESTATUS[0]})"
echo "  agente: $(sha256sum /home/adminsrvdmz/enforce/agente_enforce.py | cut -c1-64) (esperado 2985c123...)"
echo "  brute-lab: PID=$(systemctl show -p MainPID --value ppi-brute-lab) desde $(systemctl show -p ActiveEnterTimestamp --value ppi-brute-lab); app.py $(sha256sum /opt/brute-lab/app.py | cut -c1-16); brute.log $(wc -l < /opt/brute-lab/brute.log) lineas"
echo "  escucha: $(ss -ltnH | awk '{print $4}' | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
