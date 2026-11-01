# Paso 1 / R0: perfil del motor DESPLEGADO (sin modificar) en el tramo de inundacion, con el arnes de replay.
# Solo lectura sobre ~/cyberflow y ~/cf-campana-A-20261029; escribe en ~/cf-p1.
set -e
scp -q ~/cf-stage/p1/replay_motor.py sensor1:cf-p1-replay_motor.py
ssh -o BatchMode=yes sensor1 'bash -s' <<'EOR'
set -e
mkdir -p ~/cf-p1/herramientas ~/cf-p1/r0-perfil-ref
mv ~/cf-p1-replay_motor.py ~/cf-p1/herramientas/replay_motor.py
sha256sum ~/cf-p1/herramientas/replay_motor.py ~/cyberflow/scripts/engine/motor_decision.py ~/cyberflow/scripts/features/extract_multilayer_v2.py ~/cyberflow/scripts/features/extract_multilayer_v3.py | cut -c1-16,64-
C=~/cf-campana-A-20261029; D=~/cyberflow
ARGS="--model-path $D/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib --manifest-path $D/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json --detector-name if_limpio_2026_10 --schema $D/configs/features/multilayer-v2.json --entity-network 10.10.0.0/16 --excluir 10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32 --excluir-protocolos 112,240 --step-seconds 10 --history-seconds 230"
echo "$ARGS" > ~/cf-p1/args-motor.txt
O=~/cf-p1/r0-perfil-ref
tmux new-session -d -s cfR0 "cd $O && nice -n 15 $D/.venv/bin/python ~/cf-p1/herramientas/replay_motor.py --motor $D/scripts/engine/motor_decision.py --pcap-dir $C/archivo-pcap --eve $C/fuentes/eve.json --desde 2026-10-29T09:00:00Z --hasta 2026-10-29T09:10:00Z --perfilar --salida $O -- $ARGS > stdout.txt 2> stderr.txt; echo rc=\$? > rc.txt"
sleep 2; tmux ls
EOR
