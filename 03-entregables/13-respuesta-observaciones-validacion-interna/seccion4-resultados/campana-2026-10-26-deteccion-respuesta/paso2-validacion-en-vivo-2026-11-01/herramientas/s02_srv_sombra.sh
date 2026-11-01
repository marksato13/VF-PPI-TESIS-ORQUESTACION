#!/usr/bin/env bash
# PASO2 s02 — srv-dmz: sombra (agente y timer parados/deshabilitados), sets vacios con consulta OK, escalada local.
# Solo lectura.
set -u
echo "## s02 srv $(hostname) $(date -u +%FT%T.%3NZ)"
for u in ppi-enforce-agent.timer ppi-enforce-agent.service; do echo "  $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u)"; done
sudo -n nft list sets 2>&1 | grep -E '^\s*set ' | sed 's/^/  /'
for s in cyberflow_bloqueados cyberflow_limitados; do o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?
  if [ $rc -ne 0 ]; then echo "  $s CONSULTA FALLIDA rc=$rc: $o"; else echo "  $s rc=0 $(echo "$o" | grep -q 'elements' && echo "CON ELEMENTOS: $(echo "$o" | grep elements)" || echo 'sin elementos')"; fi; done
echo "  ultima ejecucion del agente: $(journalctl -u ppi-enforce-agent.service --no-pager -q -n 1 -o short-iso 2>/dev/null)"
echo "  sombra: ultimo=$(sudo -n cat /opt/cf-sombra-estado/ultimo 2>&1)"
echo "  escalada local sha=$(sudo -n sha256sum /var/lib/ppi-enforce/estado.json 2>&1 | cut -c1-64)"
echo "  servicios web: $(ss -ltnp 2>/dev/null | awk 'NR>1{print $4}' | tr '\n' ' ')"
for u in $(systemctl list-units --type=service --state=running --no-pager --plain | awk '{print $1}' | grep -iE 'http|nginx|apache|brute|lab|web'); do echo "  servicio $u"; done
echo "  carga: $(uptime)"; free -m | sed -n 2p | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
