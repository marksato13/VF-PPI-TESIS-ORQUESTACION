#!/usr/bin/env bash
set -u
B=$(cd "$(dirname "$0")" && pwd)
echo "## parar factor1 $(date -u +%FT%T.%3NZ)"
while read u p; do kill -TERM -- -$p 2>/dev/null; echo "  $u pgid=$p TERM"; done < "$B/pids"
sleep 3
while read u p; do pgrep -g $p >/dev/null && { kill -KILL -- -$p; echo "  $u KILL"; }; done < "$B/pids"
echo "  quedan: $(pgrep -fc clientes_factor1.py)"; mv "$B/pids" "$B/pids.parado-$(date -u +%H%M%S)"
for f in $B/perfiles/*.out; do echo "  $(basename $f): $(tail -1 $f)"; done
