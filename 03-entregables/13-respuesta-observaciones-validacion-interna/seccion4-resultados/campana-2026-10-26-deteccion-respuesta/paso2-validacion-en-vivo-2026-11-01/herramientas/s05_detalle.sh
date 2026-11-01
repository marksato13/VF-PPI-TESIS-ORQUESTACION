#!/usr/bin/env bash
# PASO2 s05 — bastion: detalles (solo lectura) de kali, srv-dmz y clientes.
set -u
echo "## kali: procesos que coinciden con el patron de carga"
ssh -n kali "ps -eo pid,etime,args | grep -E '[c]url |[n]map |[d]ig |[g]enerar_campana' | cut -c1-200; cat ~/cf-campana-A-prep-20261029/comando_generador.txt; echo; cat ~/cf-campana-A-prep-20261029/hashes_generador.txt; ls -la ~/cf-campana-A/scripts ~/cf-campana-A/escenarios"
echo "## srv-dmz: nftables (consulta completa)"
ssh -n srvdmz 'sudo -n nft list tables; echo "rc_tables=$?"; sudo -n nft list ruleset > /tmp/.r 2>&1; echo "rc_ruleset=$? lineas=$(wc -l < /tmp/.r)"; grep -nE "table|set |elements" /tmp/.r | head -30; rm -f /tmp/.r; sudo -n -l 2>&1 | tail -12; sudo -n ls -la /opt/cf-sombra-estado/ /opt/cf-sombra-estado/20261028-073340 2>&1 | head -20; ls -la /var/lib/ppi-enforce 2>&1; systemctl cat ppi-enforce-agent.service 2>&1 | grep -E "ExecStart|estado|feed" '
echo "## clientes: generador y factor"
ssh -n clientes 'cd ~/laboratorio; ls -la . *; sha256sum clientes_lab.py; grep -nE "factor|hora|weekday|isoweekday|semana|horario|FACTOR|getenv|environ|add_argument|def " clientes_lab.py | head -80'
