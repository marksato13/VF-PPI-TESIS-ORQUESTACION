#!/usr/bin/env bash
# [LAPTOP Git Bash -> BASTIÓN gadmin] Prueba EN SECO de la lectura de S11 (O11, hashes congelados): ejecuta SIN CAMBIOS
# precheck.sh del 06-nov (evidencia/06-observacion) con la etiqueta «seco-preparacion». Solo lecturas en Sensor1,
# bastión y srv-dmz (srv-dmz con sudo -n de lectura). Sin valor de medida: el día del ensayo se ejecuta en P0 («antes»)
# y tras la ventana («despues») y se comparan las líneas de hash.
set -u
DOC="$1"
echo "sha256 precheck.sh (06-nov, sin cambios): $(sha256sum < "$DOC" | cut -c1-64)"
ssh -o BatchMode=yes -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 "bash -s seco-preparacion" < "$DOC" 2>&1
echo "rc=$?"
