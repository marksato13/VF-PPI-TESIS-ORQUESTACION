#!/usr/bin/env bash
# Dentro del banco (Linux): las pruebas nuevas contra 585da7b (deben fallar) y contra la
# corrección (deben pasar); después la suite completa de la corrección.
set -u
cp -a /src /w && cp -a /src /w_viejo
cp /viejo/scripts/engine/*.py /w_viejo/scripts/engine/
NUEVAS="tests/test_detector_rapido_flujo.py tests/test_auth_failure_vista.py"
echo "== 585da7b (ficheros corregidos revertidos) + pruebas nuevas"
cd /w_viejo && timeout 600 python3 -m pytest -q -p no:cacheprovider $NUEVAS -rf 2>&1 | grep -E "^(FAILED|ERROR)|passed|failed"
echo "== correccion + pruebas nuevas"
cd /w && python3 -m pytest -q -p no:cacheprovider $NUEVAS 2>&1 | tail -5
echo "== suite completa (correccion)"
cd /w && python3 -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15
