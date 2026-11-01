#!/bin/bash
tmux has-session -t cfP1r5 2>/dev/null && { echo "cfP1r5 ya existe"; exit 0; }
tmux new-session -d -s cfP1r5 "bash ~/cf-p1/herramientas/r5.sh > ~/cf-p1/r5.out 2>&1"
sleep 1; tmux ls
