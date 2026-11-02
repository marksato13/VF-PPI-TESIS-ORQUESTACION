#!/usr/bin/env bash
# Banco (root, --network none): ensayos del cierre técnico de la Etapa 3.
set -u
cp -a /src /w && cd /w
echo "== pruebas nuevas en Linux"
python3 -m pytest -q -p no:cacheprovider tests/test_detector_rapido_flujo.py tests/test_auth_failure_vista.py 2>&1 | tail -3
echo "== ensayo VLAN (captura)"
mkdir -p /out/vlan && python3 deploy/pruebas-aisladas/ensayo_vlan_captura.py /seg /out/vlan > /out/vlan/stdout.txt 2> /out/vlan/stderr.txt
tail -3 /out/vlan/stdout.txt
echo "== C sin VLAN (escaso + carga) x3"
mkdir -p /out/bateria-c && python3 deploy/pruebas-aisladas/ensayo_via_rapida.py /seg /out/bateria-c C 3 quitar \
  > /out/bateria-c/stdout.txt 2> /out/bateria-c/stderr.txt
wc -l /out/bateria-c/ensayo-via-rapida.jsonl
echo "== C con VLAN conservada (escaso + carga) x3"
mkdir -p /out/bateria-c-vlan && python3 deploy/pruebas-aisladas/ensayo_via_rapida.py /seg /out/bateria-c-vlan C 3 conservar \
  > /out/bateria-c-vlan/stdout.txt 2> /out/bateria-c-vlan/stderr.txt
wc -l /out/bateria-c-vlan/ensayo-via-rapida.jsonl
echo FIN
