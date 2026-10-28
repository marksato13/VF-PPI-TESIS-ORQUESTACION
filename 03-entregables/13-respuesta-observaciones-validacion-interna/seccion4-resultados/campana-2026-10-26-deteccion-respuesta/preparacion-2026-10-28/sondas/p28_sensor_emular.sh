#!/usr/bin/env bash
# PREP 28 — sensor: emulacion ciclo a ciclo del motor ANTERIOR sobre el archivo del preflight (solo lectura).
set -u
H=$HOME/cf-prep-20261028/herramientas; O=$HOME/cf-prep-20261028/diagnostico; mkdir -p "$O"
echo "## p28  inicio=$(date -u +%FT%T.%3NZ)  emular sha=$(sha256sum $H/emular_ciclos.py | cut -c1-16)"
P=$HOME/.venv-no; PY=$HOME/cyberflow/.venv/bin/python
echo "--- (1) ciclos con alguna ventana a cero"
$PY $H/emular_ciclos.py --archivo $HOME/cf-preflight-20261028/archivador-070336 --desde 2026-10-28T06:49:00+00:00 \
   --hasta 2026-10-28T07:03:40+00:00 --solo-ciclos-con-cero --max-ciclos 40 2>&1 | tee $O/emulacion-ciclos-con-cero.txt
echo "--- (2) todos los ciclos de 06:50:00 a 06:56:00"
$PY $H/emular_ciclos.py --archivo $HOME/cf-preflight-20261028/archivador-070336 --desde 2026-10-28T06:50:00+00:00 \
   --hasta 2026-10-28T06:56:00+00:00 --max-ciclos 40 --ejemplos 8 2>&1 | tee $O/emulacion-todos-0650-0656.txt
echo "## fin=$(date -u +%FT%T.%3NZ)"
