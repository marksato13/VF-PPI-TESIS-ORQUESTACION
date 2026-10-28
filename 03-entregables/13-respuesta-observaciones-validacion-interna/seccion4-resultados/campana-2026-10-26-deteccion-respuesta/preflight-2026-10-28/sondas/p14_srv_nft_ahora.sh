#!/usr/bin/env bash
# PREFLIGHT 14 — srv-dmz: estado actual de los sets nft tras las ALERT del preflight (solo lectura).
set -u
echo "## p14  $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
for s in cyberflow_bloqueados cyberflow_limitados; do
  o=$(sudo -n nft list set inet cyberflow $s 2>&1); rc=$?
  echo "  $s rc=$rc elementos: $(echo "$o" | tr '\n' ' ' | grep -oE 'elements = \{[^}]*\}' || echo '(ninguno)')"
done
echo "  ultimas ejecuciones del agente:"; journalctl -u cyberflow-agente.service --since '-15 min' --no-pager 2>/dev/null | grep -iE '10\.10\.20\.30|aplic|limit|block' | tail -n 8 | sed 's/^/    /'
