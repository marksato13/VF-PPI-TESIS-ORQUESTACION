#!/bin/bash
# Solo lectura: estado de las corridas del paso 1.
P=~/cf-p1
date -u
tmux ls 2>&1
echo "== progreso"; cat $P/progreso.txt 2>/dev/null
echo "== procesos"; ps -eo pid,etime,pcpu,rss,args | grep -E "[r]eplay_motor|[f]ase_c|[c]orridas.sh" | cut -c1-200
for d in r1-ref-perfil r3-cand r4-cand-reinicio-9b4cf2b; do
  echo "== $d"
  [ -d $P/$d ] || { echo "no existe"; continue; }
  cat $P/$d/inicio.txt $P/$d/fin.txt $P/$d/rc.txt 2>/dev/null
  echo "ciclos: $(wc -l < $P/$d/ciclos-arnes.jsonl 2>/dev/null)"
  tail -n1 $P/$d/ciclos-arnes.jsonl 2>/dev/null | cut -c1-80
  grep -i -E "Traceback|Error|Killed" $P/$d/stderr.txt | head -5
  grep -E "Maximum resident|Elapsed|Exit status" $P/$d/stderr.txt 2>/dev/null
done
echo "== pruebas"; tail -5 $P/pruebas-9b4cf2b.txt 2>/dev/null
echo "== fase_c.out"; tail -5 $P/fase_c.out 2>/dev/null
echo "== corridas.out"; tail -5 $P/corridas.out 2>/dev/null
free -m | head -2; uptime
