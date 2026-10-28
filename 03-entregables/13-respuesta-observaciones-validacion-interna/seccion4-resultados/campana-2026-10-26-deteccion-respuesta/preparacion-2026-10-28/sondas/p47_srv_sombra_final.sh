#!/usr/bin/env bash
# PREP 39 — srv-dmz: la sombra sigue en pie (agente parado, timer deshabilitado, sets vacios con consulta OK, ninguna
# ejecucion del agente desde la activacion). Solo lectura.
set -u
echo "## p39 srv  $(date -u +%FT%T.%3NZ)"
for u in ppi-enforce-agent.timer ppi-enforce-agent.service; do echo "  $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u)"; done
for s in cyberflow_bloqueados cyberflow_limitados; do o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?
  if [ $rc -ne 0 ]; then echo "  $s CONSULTA FALLIDA rc=$rc: $o"; else echo "  $s rc=0 $(echo "$o" | grep -q 'elements' && echo "CON ELEMENTOS: $(echo "$o" | grep elements)" || echo 'sin elementos')"; fi; done
echo "  ejecuciones del agente desde 07:33:42: $(journalctl -u ppi-enforce-agent.service --since '2026-10-28 07:33:42' --no-pager -q 2>/dev/null | grep -c . )"
journalctl -u ppi-enforce-agent.service --since '2026-10-28 07:33:42' --no-pager -q 2>/dev/null | tail -3 | sed 's/^/    /'
echo "  ultimo=$(sudo -n cat /opt/cf-sombra-estado/ultimo)  mecanismo=$(sudo -n cat /opt/cf-sombra-estado/$(sudo -n cat /opt/cf-sombra-estado/ultimo)/mecanismo)"
echo "  escalada actual sha=$(sudo -n sha256sum /var/lib/ppi-enforce/estado.json 2>/dev/null | cut -c1-16) (respaldo 73310d14)"
sha256sum ~/cf-campana/modo_sombra.sh ~/cf-campana/restaurar_enforcement.sh | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
