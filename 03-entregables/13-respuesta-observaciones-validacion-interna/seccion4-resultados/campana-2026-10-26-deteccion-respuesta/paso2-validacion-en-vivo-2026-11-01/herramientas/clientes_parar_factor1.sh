#!/usr/bin/env bash
# PASO2 — clientes: para los seis perfiles con factor 1,0 (grupos de proceso guardados en pids). Solo procesos propios.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID
echo "## parar factor1 $(date -u +%FT%T.%3NZ)"
while read u p; do kill -TERM -- -$p 2>/dev/null; echo "  $u pgid=$p TERM"; done < "$B/pids"
sleep 3
while read u p; do pgrep -g $p >/dev/null && { kill -KILL -- -$p; echo "  $u KILL"; }; done < "$B/pids"
echo "  quedan: $(pgrep -fc clientes_factor1.py)"; mv "$B/pids" "$B/pids.parado-$(date -u +%H%M%S)"
for f in $B/perfiles/*.out; do echo "  $(basename $f): $(tail -1 $f)"; done
echo "## fin $(date -u +%FT%T.%3NZ)"
