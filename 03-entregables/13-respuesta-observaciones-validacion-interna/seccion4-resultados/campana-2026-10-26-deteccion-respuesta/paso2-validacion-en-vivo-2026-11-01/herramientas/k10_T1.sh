#!/usr/bin/env bash
# PASO2 k10 — Kali: lanza el episodio tecnico REP (inundacion aprobada) en segundo plano y espera su fin (<=150 s +
# margen). Aborta si hay curl o generador vivos. Marcas en ~/cf-paso2-20261101T0254Z/episodios/marcas.jsonl
set -u
REP=T1; B=~/cf-paso2-20261101T0254Z; S=$B/episodios
echo "## k10 $REP $(date -u +%FT%T.%3NZ)"
[ "$(pgrep -c curl)" = 0 ] && [ "$(pgrep -fc kali_episodio_tecnico)" = 0 ] || { echo "ABORTO: carga viva"; exit 2; }
mkdir -p $S
setsid nohup python3 $B/kali_episodio_tecnico.py --rep $REP --salida-dir $S --autorizado > $S/lanzador-$REP.out 2>&1 < /dev/null &
for i in $(seq 1 200); do sleep 1; pgrep -fc "kali_episodio_tecnico.py --rep $REP" >/dev/null || break; done
echo "  lanzador: $(cat $S/lanzador-$REP.out)"
grep "\"$REP\"\|-r$REP\"" $S/marcas.jsonl | cut -c1-400
echo "  curl vivos tras el episodio: $(pgrep -c curl)"
echo "## fin $(date -u +%FT%T.%3NZ)"
