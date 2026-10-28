#!/usr/bin/env bash
# PREP 30 — sensor: arranca una instancia CANDIDATA del motor corregido EN PARALELO al de produccion (que no se
# toca). Mismos argumentos salvo --log-path y --state-dir propios. Lee el anillo y eve.json en solo lectura.
# Arbol propio: scripts/engine/{motor_decision.py (candidato), heuristicos.py -> produccion},
# scripts/features -> produccion. PID guardado para pararla.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
C=$HOME/cf-prep-20261028/candidato; H=$HOME/cf-prep-20261028/herramientas
echo "## p30  inicio=$(ts)"
[ -e "$C/motor.pid" ] && kill -0 "$(cat $C/motor.pid)" 2>/dev/null && { echo "ABORTO: ya hay un candidato vivo"; exit 2; }
mkdir -p "$C/scripts/engine" "$C/logs" "$C/_state"
cp "$H/motor_decision.py" "$C/scripts/engine/motor_decision.py"
ln -sfn $HOME/cyberflow/scripts/engine/heuristicos.py "$C/scripts/engine/heuristicos.py"
ln -sfn $HOME/cyberflow/scripts/features "$C/scripts/features"
echo "  candidato sha=$(sha256sum $C/scripts/engine/motor_decision.py | cut -c1-64)"
echo "  produccion sha=$(sha256sum $HOME/cyberflow/scripts/engine/motor_decision.py | cut -c1-64) (no se toca)"
echo "  carga: $(cat /proc/loadavg) | cpus=$(nproc) | mem libre=$(free -m | awk '/Mem/{print $7}') MB"
P=$(systemctl show -p MainPID --value ppi-motor)
ARGV=$(tr '\0' '\n' < /proc/$P/cmdline | tail -n +3 | sed "s#^$HOME/cyberflow/logs/motor_decision.log\$#$C/logs/motor_decision.log#" | tr '\n' ' ')
echo "  argv candidato: $ARGV --state-dir $C/_state"
cd $HOME/cyberflow
setsid nohup bash -c 'C="$1"; shift; '"$HOME"'/cyberflow/.venv/bin/python "$C/scripts/engine/motor_decision.py" "$@" > "$C/motor.out" 2>&1 & p=$!; echo $p > "$C/motor.pid"; wait $p; echo $? > "$C/motor.rc"' _ "$C" $ARGV --state-dir "$C/_state" >/dev/null 2>&1 < /dev/null &
for i in $(seq 1 10); do [ -s "$C/motor.pid" ] && break; sleep 0.5; done
PC=$(cat $C/motor.pid); echo "  PID candidato=$PC  cmdline=$(tr '\0' ' ' < /proc/$PC/cmdline | cut -c1-200)…"
grep -c -- '--log-path' /proc/$PC/cmdline >/dev/null; tr '\0' '\n' < /proc/$PC/cmdline | grep -A1 -- '--log-path' | tail -1 | sed 's/^/  log del candidato: /'
sleep 40
echo "  [$(ts)] vivo=$(kill -0 $PC 2>/dev/null && echo SI || echo NO) | lineas log candidato=$(wc -l < $C/logs/motor_decision.log 2>/dev/null)"
head -1 $C/logs/motor_decision.log | cut -c1-400 | sed 's/^/  arranque: /'
tail -2 $C/logs/motor_decision.log | cut -c1-500 | sed 's/^/  ultima: /'
echo "  salida (errores): $(grep -ciE 'error|traceback' $C/motor.out)"; tail -3 $C/motor.out | cut -c1-300 | sed 's/^/    /'
echo "  produccion sigue: PID=$(systemctl show -p MainPID --value ppi-motor) NRestarts=$(systemctl show -p NRestarts --value ppi-motor)"
echo "## fin=$(ts)"
