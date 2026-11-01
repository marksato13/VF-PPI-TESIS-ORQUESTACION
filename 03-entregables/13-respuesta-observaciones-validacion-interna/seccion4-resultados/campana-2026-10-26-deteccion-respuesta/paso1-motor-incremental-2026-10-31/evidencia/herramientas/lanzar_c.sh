#!/bin/bash
tmux has-session -t cfP1c 2>/dev/null && { echo "cfP1c ya existe"; exit 0; }
tmux new-session -d -s cfP1c "bash ~/cf-p1/herramientas/fase_c.sh > ~/cf-p1/fase_c.out 2>&1"
sleep 2; tmux ls
