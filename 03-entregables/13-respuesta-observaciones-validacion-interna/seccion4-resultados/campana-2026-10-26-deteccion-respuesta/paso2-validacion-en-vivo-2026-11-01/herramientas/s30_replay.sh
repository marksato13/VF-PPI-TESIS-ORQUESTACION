#!/usr/bin/env bash
# PASO2 s30 — sensor: repeticion offline de referencia (inventario de ventanas esperadas) con el MISMO motor
# candidato instalado, sobre el PCAP archivado y el segmento EVE conservado. Solo escribe en ~/cf-paso2-ID/replay.
# Se lanza DESPUES de cerrar las pruebas (no compite con las mediciones). Uso: s30_replay.sh <desde_iso> <hasta_iso>
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; O=$B/replay; PY=$HOME/cyberflow/.venv/bin/python
[ -e "$O" ] && { echo "ABORTO: existe $O"; exit 2; }
mkdir -p "$O"
H=$B/producto-24f8a80/scripts/engine/replay_motor.py; M=$HOME/cyberflow/scripts/engine/motor_decision.py
ARGS=$(python3 - "$B/estado-inicial/argv-motor.txt" <<'PY'
import sys, shlex
a = open(sys.argv[1]).read().split()[2:]
out, i = [], 0
while i < len(a):
    if a[i] in ("--eve-path", "--capture-dir", "--log-path"): i += 2; continue
    out.append(a[i]); i += 1
print(" ".join(shlex.quote(x) for x in out))
PY
)
echo "$ARGS" > $O/args-motor.txt
sha256sum $H $M $HOME/cyberflow/scripts/engine/motor_incremental.py $B/copias/eve-segmento.json > $O/huellas.txt
date -u +%FT%TZ > $O/inicio.txt
( cd $O && eval /usr/bin/time -v nice -n 15 $PY $H --motor $M --pcap-dir $B/archivo-pcap --eve $B/copias/eve-segmento.json \
    --desde "$1" --hasta "$2" --salida $O -- $ARGS > stdout.txt 2> stderr.txt; echo rc=$? > rc.txt )
date -u +%FT%TZ > $O/fin.txt
