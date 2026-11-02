#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s30 — uso: s30_replay_e4.sh <4b|4c> <desde_iso> <hasta_iso>. Sin sudo.
# Extrae el segmento EVE de la ejecución (desde el byte inicial registrado en s10) y lanza en sesión persistente la
# repetición offline (inventario) con el MISMO motor candidato (ec78ca5, replay_motor.py del mismo commit) sobre el
# PCAP archivado. El archivador SIGUE en marcha (condición 5 del cierre). Argumentos del motor: los del proceso en
# vivo (argv-motor.txt) sin --eve-path/--capture-dir/--log-path/--state-dir y sin --disparo: el inventario enumera
# las ventanas requeridas con la retícula de 10 s, como en el 3B; el disparo solo cambia CUÁNDO se decide.
# Parada: eve.json rotado durante la ejecución (copytruncate: el tamaño actual es menor que el inicial).
set -u
FASE=${1:?fase}; DESDE=${2:?desde}; HASTA=${3:?hasta}
B=$HOME/cf-e4/$FASE; O=$B/replay; PY=$HOME/cyberflow/.venv/bin/python; E4=$HOME/cyberflow-e4/ec78ca5
[ -e "$O" ] && { echo "PARAR: existe $O"; exit 2; }
mkdir -p "$O" "$B/copias"
echo "## s30-e4 $(date -u +%FT%T.%3NZ) desde=$DESDE hasta=$HASTA"
read -r INO TAM < <(python3 -c "import json;d=json.load(open('$B/eve/inicio.json'));print(d['inode'],d['size'])")
[ "$(stat -c %i /var/log/suricata/eve.json)" = "$INO" ] || { echo "PARAR: eve.json cambió de inodo (rotación)"; exit 3; }
[ "$(stat -c %s /var/log/suricata/eve.json)" -ge "$TAM" ] || { echo "PARAR: eve.json es menor que al empezar (copytruncate durante la ejecución)"; exit 3; }
tail -c +$(( TAM + 1 )) /var/log/suricata/eve.json > "$B/copias/eve-segmento.json"
echo "  eve segmento desde byte $TAM: $(stat -c %s "$B/copias/eve-segmento.json") bytes, sha256 $(sha256sum "$B/copias/eve-segmento.json" | cut -c1-64)"
H=$E4/scripts/engine/replay_motor.py; M=$E4/scripts/engine/motor_decision.py
ARGS=$(python3 - "$B/estado-inicial/argv-motor.txt" <<'PY'
import sys, shlex
a = open(sys.argv[1]).read().split()[2:]
out, i = [], 0
while i < len(a):
    if a[i] in ("--eve-path", "--capture-dir", "--log-path", "--state-dir", "--disparo"):
        i += 2; continue
    out.append(a[i]); i += 1
print(" ".join(shlex.quote(x) for x in out))
PY
)
echo "$ARGS" > "$O/args-motor.txt"; sed 's/^/  args: /' "$O/args-motor.txt"
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) || { echo "PARAR: el código candidato no verifica"; exit 2; }
sha256sum "$H" "$M" "$E4/scripts/engine/motor_incremental.py" "$B/copias/eve-segmento.json" > "$O/huellas.txt"
sed 's/^/  /' "$O/huellas.txt"
date -u +%FT%TZ > "$O/inicio.txt"
setsid nohup bash -c "cd '$O' && /usr/bin/time -v nice -n 15 '$PY' '$H' --motor '$M' --pcap-dir '$B/archivo-pcap' --eve '$B/copias/eve-segmento.json' --desde '$DESDE' --hasta '$HASTA' --salida '$O' -- $ARGS > stdout.txt 2> stderr.txt; echo rc=\$? > rc.txt; date -u +%FT%TZ > fin.txt" > /dev/null 2>&1 < /dev/null &
sleep 5; echo "  replay lanzado: $(pgrep -f replay_motor.py | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
