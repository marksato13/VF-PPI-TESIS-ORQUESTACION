#!/usr/bin/env bash
# PREP 29 — sensor: emulacion de TODOS los ciclos con ceros del archivo del preflight, cruzada con el valor
# completo (diag_ventanas) para clasificar cada cero-con-trafico. Solo lectura.
set -u
H=$HOME/cf-prep-20261028/herramientas; O=$HOME/cf-prep-20261028/diagnostico
echo "## p29  inicio=$(date -u +%FT%T.%3NZ)  emular sha=$(sha256sum $H/emular_ciclos.py | cut -c1-16)"
$HOME/cyberflow/.venv/bin/python $H/emular_ciclos.py --archivo $HOME/cf-preflight-20261028/archivador-070336 \
  --desde 2026-10-28T06:49:00+00:00 --hasta 2026-10-28T07:04:20+00:00 --solo-ciclos-con-cero --max-ciclos 200 \
  --ejemplos 0 --comparacion $O/comparacion-preflight-0646-0704.jsonl 2>&1 | grep -v '"tipo": "cero"' | tee $O/emulacion-ceros-con-trafico.txt
echo "## fin=$(date -u +%FT%T.%3NZ)"
