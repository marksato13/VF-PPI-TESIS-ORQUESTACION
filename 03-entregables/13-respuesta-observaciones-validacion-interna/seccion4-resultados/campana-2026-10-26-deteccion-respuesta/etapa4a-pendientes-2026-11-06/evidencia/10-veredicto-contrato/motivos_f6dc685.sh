#!/bin/sh
# Motivo concreto del fallo de las pruebas de los tres defectos, contra el evaluador de f6dc685 (copia en /tmp/w).
set -u
mkdir -p /tmp/w && cp -r /src/. /tmp/w/
cp /w/f6dc685/evaluar_ecarga.py /tmp/w/deploy/etapa4/sensor1/evaluar_ecarga.py
cd /tmp/w
echo "== motivo del fallo de las pruebas de los tres defectos contra f6dc685"
python3 -m pytest -q -p no:cacheprovider --tb=line \
  -k "fallo1 or fallo2 or fallo3 or limite_s13 or c3_y_no_evaluable" tests/test_etapa4_ecarga.py 2>&1 \
  | grep -E '^(/|E |[0-9]+ (passed|failed))'
