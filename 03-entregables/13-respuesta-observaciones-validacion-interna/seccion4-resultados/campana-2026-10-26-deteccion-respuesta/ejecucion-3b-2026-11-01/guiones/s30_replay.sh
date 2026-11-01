#!/usr/bin/env bash
# PASO3B s30 — sensor: extrae el segmento EVE de la ejecucion (desde el byte inicial registrado en s10) y lanza en
# sesion persistente la repeticion offline (inventario) con el MISMO motor instalado (replay_motor.py del paso 2,
# c93c80c8...) sobre el PCAP archivado. El archivador SIGUE en marcha: el archivo no se cierra hasta comprobar la
# repeticion (condicion 5 de la seccion 3 bis). Uso: s30_replay.sh <desde_iso> <hasta_iso>
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; O=$B/replay; PY=$HOME/cyberflow/.venv/bin/python
[ -e "$O" ] && { echo "PARAR: existe $O"; exit 2; }
mkdir -p "$O" "$B/copias"
echo "## s30 $(date -u +%FT%T.%3NZ) desde=$1 hasta=$2"
I=$(python3 -c "import json;d=json.load(open('$B/eve/inicio.json'));print(d['inode'],d['size'])"); set -- $I "$1" "$2"
[ "$(stat -c %i /var/log/suricata/eve.json)" = "$1" ] || { echo "PARAR: eve.json cambio de inodo (rotacion)"; exit 3; }
tail -c +$(( $2 + 1 )) /var/log/suricata/eve.json > "$B/copias/eve-segmento.json"
echo "  eve segmento desde byte $2: $(stat -c %s $B/copias/eve-segmento.json) bytes, sha256 $(sha256sum $B/copias/eve-segmento.json | cut -c1-64)"
head -c 300 "$B/copias/eve-segmento.json" | head -1 | cut -c1-120 | sed 's/^/  primera: /'
H=$HOME/cf-paso2-20261101T0254Z/producto-24f8a80/scripts/engine/replay_motor.py; M=$HOME/cyberflow/scripts/engine/motor_decision.py
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
sed 's/^/  /' $O/huellas.txt
date -u +%FT%TZ > $O/inicio.txt
setsid nohup bash -c "cd $O && /usr/bin/time -v nice -n 15 $PY $H --motor $M --pcap-dir $B/archivo-pcap --eve $B/copias/eve-segmento.json --desde $3 --hasta $4 --salida $O -- $ARGS > stdout.txt 2> stderr.txt; echo rc=\$? > rc.txt; date -u +%FT%TZ > fin.txt" > /dev/null 2>&1 < /dev/null &
sleep 5; echo "  replay lanzado: $(pgrep -f replay_motor.py | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
