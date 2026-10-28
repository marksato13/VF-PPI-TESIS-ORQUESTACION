#!/usr/bin/env bash
# PREP 37 — sensor: comparacion por clave produccion vs candidato vs completo (comparar_motores.py) sobre el archivo
# de diagnostico. Solo lectura. Uso: bash -s DESDE HASTA ETIQUETA
set -u
H=$HOME/cf-prep-20261028/herramientas; O=$HOME/cf-prep-20261028/diagnostico; C=$HOME/cf-prep-20261028/candidato
DESDE=${1:?}; HASTA=${2:?}; ET=${3:?}
echo "## p37 $ET  inicio=$(date -u +%FT%T.%3NZ)  comparar sha=$(sha256sum $H/comparar_motores.py | cut -c1-16)"
$HOME/cyberflow/.venv/bin/python $H/comparar_motores.py --archivo $HOME/cf-prep-20261028/archivo-diagnostico-073542 \
  --desde "$DESDE" --hasta "$HASTA" --cand $C/logs/motor_decision.log --json $O/comparacion-motores-$ET.jsonl 2>&1 | tee $O/comparacion-motores-$ET.txt
echo "## fin=$(date -u +%FT%T.%3NZ)"
