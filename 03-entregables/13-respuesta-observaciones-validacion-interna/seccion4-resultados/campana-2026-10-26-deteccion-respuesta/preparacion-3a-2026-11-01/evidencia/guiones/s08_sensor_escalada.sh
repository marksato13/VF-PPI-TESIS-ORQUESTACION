#!/usr/bin/env bash
# PASO3A s08 — sensor (solo lectura): quien lee/escribe estado.json, que significa 'bloqueos', copia con hashes.
set -u
B=$HOME/cf-paso3a-20261101T0523Z; C=$HOME/cyberflow; mkdir -p $B/escalada
echo "## s08 $(date -u +%FT%T.%3NZ)"
cd $C
echo "## referencias a estado.json / escalada en el codigo desplegado"
grep -rn --include=*.py -E "estado\.json|import escalada|from escalada|escalada\." scripts src 2>/dev/null | grep -v "/tests/" | head -40
echo "## ficheros de la ruta del feed"
ls -la /var/lib/ppi-feed 2>/dev/null || true
F=$(dirname $(readlink -f $(grep -rln --include=*.py "estado.json" scripts src 2>/dev/null | head -1) 2>/dev/null) 2>/dev/null)
echo "## unidades que tocan el feed"
systemctl list-units --all --no-pager 2>/dev/null | grep -iE "feed|publica|enforce" | sed 's/^/  /'
for u in $(systemctl list-unit-files --no-pager 2>/dev/null | awk '/feed|publica/ {print $1}'); do echo "--- $u"; systemctl cat $u 2>/dev/null | grep -E "ExecStart|OnCalendar|OnUnitActiveSec|User" | sed 's/^/  /'; done
echo "## escalada.py: definicion de bloqueos y ventana de reincidencia"
E=$(find $C -name escalada.py -not -path "*/tests/*" | head -1); echo "  $E"; sha256sum $E
grep -n -E "bloqueos|24|86400|reincid|ventana|def " $E | head -40
P=$(find $C -name publicar_feed.py -not -path "*/tests/*" | head -1); echo "  $P"; sha256sum $P
grep -n -E "estado|escalada|sombra|enforce|bloqueos" $P | head -40
echo "## motor: lee estado.json?"
grep -n -E "estado\.json|escalada" $C/scripts/engine/motor_decision.py $C/scripts/engine/motor_incremental.py 2>/dev/null | head; echo "  (vacio = no lo lee)"
echo "## copia del estado actual"
for f in $(find / -xdev -name estado.json -path "*feed*" 2>/dev/null | head -3) ; do echo "  $f"; done
echo "## fin"
