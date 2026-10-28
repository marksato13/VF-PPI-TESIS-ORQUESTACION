#!/usr/bin/env bash
# PREFLIGHT 17 — sensor: resumen de cada ejecucion del publicador entre 07:03:30 y 07:10 (¿entro 10.10.20.30 en LIMIT
# tras las ALERT benignas de 07:04?). Solo lectura.
set -u
echo "## p17  $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
o=$(journalctl -u ppi-publicar-feed.service --since '2026-10-28 07:03:30 UTC' --until '2026-10-28 07:10:00 UTC' --no-pager -o short-iso 2>&1)
echo "  lineas: $(echo "$o" | wc -l)"
echo "$o" | grep -F '{"block"' | awk '{$2=$3=""; print}' | sort | uniq -c | sed 's/^/    /'
echo "  ejecuciones con limit>0 o block>0:"; echo "$o" | grep -F '{"block"' | grep -vE '"block": 0, "entradas": 0, "limit": 0' | sed 's/^/    /' | head
