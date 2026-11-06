#!/bin/sh
# [LAPTOP PowerShell -> banco Docker sin red] Pruebas NUEVAS de test_etapa4_ecarga.py contra el evaluador de f6dc685.
# El repo se monta solo lectura; se copia a /tmp/w y solo se sustituye evaluar_ecarga.py por el blob de f6dc685.
set -u
rm -rf /tmp/w && cp -r /src /tmp/w
cp /w/f6dc685/evaluar_ecarga.py /tmp/w/deploy/etapa4/sensor1/evaluar_ecarga.py
cd /tmp/w
echo "== sha256 del evaluador probado"; sha256sum deploy/etapa4/sensor1/evaluar_ecarga.py
grep -m1 '^VERSION' deploy/etapa4/sensor1/evaluar_ecarga.py
echo "== pruebas nuevas contra f6dc685 (se esperan fallos)"
python3 -m pytest -q -p no:cacheprovider -rf tests/test_etapa4_ecarga.py 2>&1 | grep -E '^(FAILED|[0-9]+ (passed|failed))' | sed 's/ - .*//'
echo "== reproduccion de los tres fallos con el evaluador de f6dc685"
python3 /w/reproducir.py deploy/etapa4/sensor1/evaluar_ecarga.py
echo "== reproduccion con el evaluador corregido (repo montado)"
python3 /w/reproducir.py /src/deploy/etapa4/sensor1/evaluar_ecarga.py
