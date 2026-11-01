#!/bin/bash
# Lanza corridas.sh en tmux (sesion cfP1) y muestra el arranque.
rm -f ~/cf-p1/progreso.txt
tmux new-session -d -s cfP1 "bash ~/cf-p1/herramientas/corridas.sh > ~/cf-p1/corridas.out 2>&1"
sleep 90
tmux ls
cut -c1-16,64- ~/cf-p1/huellas.txt
for d in ~/cf-p1/r2* ~/cf-p1/r4*; do echo "$d"; tail -c 300 "$d/stderr.txt"; echo; wc -l < "$d/ciclos-arnes.jsonl"; done
