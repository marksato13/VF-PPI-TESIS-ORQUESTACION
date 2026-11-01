#!/bin/bash
# Paso 1: corridas offline R1-R4 con el arnes de replay sobre la evidencia congelada de la campana A.
# Solo LEE ~/cyberflow (modelo, esquema, venv) y ~/cf-campana-A-20261029; escribe solo en ~/cf-p1.
# Fase A (en paralelo, sus tiempos NO se usan): R2 candidato con verificacion || R4 reinicio (ref, luego cand).
# Fase B (sola, tiempos limpios): R1 referencia con perfil, luego R3 candidato sin verificacion.
set -u
P=~/cf-p1; C=~/cf-campana-A-20261029; D=~/cyberflow; PY=$D/.venv/bin/python
H=$P/herramientas/replay_motor.py
REF=$P/referencia/scripts/engine/motor_decision.py
CAN=$P/candidato/scripts/engine/motor_decision.py
ARGS=$(cat $P/args-motor.txt)
DESDE=2026-10-29T07:15:10Z; HASTA=2026-10-29T10:39:20Z
cp $P/candidato/scripts/engine/replay_motor.py $H
sha256sum $H $REF $CAN $P/candidato/scripts/engine/motor_incremental.py > $P/huellas.txt

corre() {  # nombre motor [opciones del arnes...] -- [opciones extra del motor]
  local n=$1 m=$2; shift 2
  local O=$P/$n; rm -rf $O; mkdir -p $O
  local arnes=() extra=()
  while [ $# -gt 0 ] && [ "$1" != "--" ]; do arnes+=("$1"); shift; done
  [ $# -gt 0 ] && shift; extra=("$@")
  date -u +%FT%TZ > $O/inicio.txt
  ( cd $O && /usr/bin/time -v nice -n 15 $PY $H --motor $m --pcap-dir $C/archivo-pcap --eve $C/fuentes/eve.json \
      "${arnes[@]}" --salida $O -- $ARGS "${extra[@]}" > stdout.txt 2> stderr.txt; echo rc=$? > rc.txt )
  date -u +%FT%TZ > $O/fin.txt
}

# Fase A
corre r2-cand-verif $CAN --desde $DESDE --hasta $HASTA -- --verificar-equivalencia $P/r2-cand-verif/verificacion.jsonl &
(
  corre r4-ref-reinicio $REF --desde 2026-10-29T08:55:00Z --hasta 2026-10-29T09:20:00Z --reiniciar-en 2026-10-29T09:05:00Z
  corre r4-cand-reinicio $CAN --desde 2026-10-29T08:55:00Z --hasta 2026-10-29T09:20:00Z --reiniciar-en 2026-10-29T09:05:00Z -- --verificar-equivalencia $P/r4-cand-reinicio/verificacion.jsonl
) &
wait
echo "fase A fin $(date -u +%FT%TZ)" >> $P/progreso.txt
# Fase B
corre r1-ref-perfil $REF --desde $DESDE --hasta $HASTA --perfilar
corre r3-cand $CAN --desde $DESDE --hasta $HASTA
echo "fase B fin $(date -u +%FT%TZ)" >> $P/progreso.txt
