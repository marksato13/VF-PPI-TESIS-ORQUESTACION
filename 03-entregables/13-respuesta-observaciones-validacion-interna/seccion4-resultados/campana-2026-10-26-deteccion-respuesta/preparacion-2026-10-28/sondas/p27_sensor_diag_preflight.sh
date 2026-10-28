#!/usr/bin/env bash
# PREP 27 — sensor: diagnostico (solo lectura) sobre el archivo full-SPAN del preflight (06:44:51-07:04:52),
# ventanas 06:46:10-07:04:20 (historia completa de 60 s y 30 s de margen final). Motor ANTERIOR (sin cambios).
set -u
H=$HOME/cf-prep-20261028/herramientas; O=$HOME/cf-prep-20261028/diagnostico; mkdir -p "$O"
echo "## p27  inicio=$(date -u +%FT%T.%3NZ)  diag sha=$(sha256sum $H/diag_ventanas.py | cut -c1-16)"
$HOME/cyberflow/.venv/bin/python $H/diag_ventanas.py --archivo $HOME/cf-preflight-20261028/archivador-070336 \
  --desde 2026-10-28T06:46:10+00:00 --hasta 2026-10-28T07:04:20+00:00 --json $O/comparacion-preflight-0646-0704.jsonl 2>&1
echo "## fin=$(date -u +%FT%T.%3NZ)"
