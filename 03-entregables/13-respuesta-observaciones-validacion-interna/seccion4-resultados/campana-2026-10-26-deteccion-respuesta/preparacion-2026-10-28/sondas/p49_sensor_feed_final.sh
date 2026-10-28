#!/usr/bin/env bash
# PREP 40 — sensor: propuestas del publicador del feed desde la activacion de la sombra (07:33:42) y feed vigente.
# Las propuestas NO son restricciones aplicadas (el agente de srv-dmz esta parado). Solo lectura.
set -u
echo "## p40  $(date -u +%FT%T.%3NZ)"
o=$(journalctl -u ppi-publicar-feed.service --since '2026-10-28 07:33:42 UTC' --no-pager -o short-iso 2>&1)
echo "  ejecuciones (lineas con resumen): $(echo "$o" | grep -cF '{"block"')"
echo "$o" | grep -F '{"block"' | awk '{$1=$2=$3=""; print}' | sort | uniq -c | sed 's/^/    /'
echo "  ejecuciones con limit>0 o block>0 (primeras/ultimas):"; echo "$o" | grep -F '{"block"' | grep -vE '"block": 0, "entradas": 0, "limit": 0' | sed -n '1,3p;$p' | sed 's/^/    /'
F=$(systemctl cat ppi-publicar-feed.service 2>/dev/null | grep -oE '/[^ ]*feed\.json' | head -1); F=${F:-/var/lib/ppi-feed/feed.json}
echo "  feed vigente $F: $(stat -c '%y' $F 2>/dev/null) sha=$(sha256sum $F 2>/dev/null | cut -c1-16)"
python3 -c "import json,sys; d=json.load(open('$F')); e=d.get('entradas',d.get('entries',[])); print('   entradas:',len(e)); [print('    ',json.dumps(x)[:220]) for x in e[:8]]" 2>&1
echo "## fin $(date -u +%FT%T.%3NZ)"
