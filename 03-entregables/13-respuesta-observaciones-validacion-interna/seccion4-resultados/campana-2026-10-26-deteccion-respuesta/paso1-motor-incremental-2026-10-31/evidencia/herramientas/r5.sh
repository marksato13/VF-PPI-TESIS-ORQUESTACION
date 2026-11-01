#!/bin/bash
# R5: tiempos limpios del reinicio del candidato 9b4cf2b (sin verificacion, solo), tras la fase C.
# R4 midio el reinicio solo con --verificar-equivalencia o en paralelo con R2: sus tiempos no valen.
set -u
P=~/cf-p1; C=~/cf-campana-A-20261029; D=~/cyberflow; PY=$D/.venv/bin/python
until grep -q "fase C fin" $P/progreso.txt 2>/dev/null; do sleep 30; done
O=$P/r5-cand-reinicio-tiempos; mkdir -p $O
sha256sum $P/candidato/scripts/engine/motor_decision.py $P/candidato/scripts/engine/motor_incremental.py > $O/huellas.txt
date -u +%FT%TZ > $O/inicio.txt
( cd $O && /usr/bin/time -v nice -n 15 $PY $P/herramientas/replay_motor.py --motor $P/candidato/scripts/engine/motor_decision.py \
    --pcap-dir $C/archivo-pcap --eve $C/fuentes/eve.json --desde 2026-10-29T08:55:00Z --hasta 2026-10-29T09:20:00Z \
    --reiniciar-en 2026-10-29T09:05:00Z --salida $O -- $(cat $P/args-motor.txt) > stdout.txt 2> stderr.txt; echo rc=$? > rc.txt )
date -u +%FT%TZ > $O/fin.txt
echo "R5 fin $(date -u +%FT%TZ)" >> $P/progreso.txt
