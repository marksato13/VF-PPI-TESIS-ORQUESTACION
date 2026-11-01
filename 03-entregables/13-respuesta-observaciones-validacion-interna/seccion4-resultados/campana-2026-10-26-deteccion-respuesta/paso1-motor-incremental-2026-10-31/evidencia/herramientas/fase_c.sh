#!/bin/bash
# Fase C: repite las verificaciones afectadas por 9b4cf2b (cambio de logged_at), DESPUES de R3 para no
# distorsionar su medicion. Directorio nuevo; no toca r2/r4 de 4552d83.
#  - suite unittest completa del candidato 9b4cf2b
#  - R4 con reinicio en la inundacion + --verificar-equivalencia (candidato 9b4cf2b)
set -u
P=~/cf-p1; C=~/cf-campana-A-20261029; D=~/cyberflow; PY=$D/.venv/bin/python
until grep -q "fase B fin" $P/progreso.txt 2>/dev/null; do sleep 60; done
CAN=$P/candidato/scripts/engine/motor_decision.py
ARGS=$(cat $P/args-motor.txt)
sha256sum $CAN $P/candidato/scripts/engine/motor_incremental.py $P/candidato/tests/test_motor_incremental.py > $P/huellas-9b4cf2b.txt
(cd $P/candidato && $PY -m unittest discover -s tests > $P/pruebas-9b4cf2b.txt 2>&1; echo rc=$? >> $P/pruebas-9b4cf2b.txt)
O=$P/r4-cand-reinicio-9b4cf2b; mkdir -p $O
date -u +%FT%TZ > $O/inicio.txt
( cd $O && /usr/bin/time -v nice -n 15 $PY $P/herramientas/replay_motor.py --motor $CAN --pcap-dir $C/archivo-pcap \
    --eve $C/fuentes/eve.json --desde 2026-10-29T08:55:00Z --hasta 2026-10-29T09:20:00Z \
    --reiniciar-en 2026-10-29T09:05:00Z --salida $O -- $ARGS --verificar-equivalencia $O/verificacion.jsonl \
    > stdout.txt 2> stderr.txt; echo rc=$? > rc.txt )
date -u +%FT%TZ > $O/fin.txt
echo "fase C fin $(date -u +%FT%TZ)" >> $P/progreso.txt
