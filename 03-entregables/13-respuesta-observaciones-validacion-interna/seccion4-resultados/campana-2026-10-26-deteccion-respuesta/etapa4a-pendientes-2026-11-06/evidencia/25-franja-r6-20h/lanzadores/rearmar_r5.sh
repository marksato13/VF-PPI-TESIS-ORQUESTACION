#!/usr/bin/env bash
# [LAPTOP Git Bash] Aparta el intento r6 y deja libre la fase A de la r5. No borra nada. VERSION 2026-11-07.1
#   rearmar_r5.sh "MOTIVO"
# Mueve los ficheros A* del intento r6 a evidencia/14-ecarga-ejecucion/intento-r6-20h/, comprueba sus hashes después de mover y
# renombra la copia publicada. Se niega si la r6 pasó de la fase A o si ya llegó la hora de la r5.
# rc: 0 rearmado · 1 no procede · 2 uso
set -u -o pipefail
export LC_ALL=C
M=${1:-}; [ -n "$M" ] || { echo "uso: rearmar_r5.sh MOTIVO"; exit 2; }
R="${CF_R:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06}"
EJ="$R/evidencia/14-ecarga-ejecucion"; W="${CF_W:-/c/Users/markp/cf-ecarga-v2-1}"; D="$EJ/intento-r6-20h"
no() { echo "NO_REARMADO: $1"; exit 1; }
[ "$(date +%s)" -lt 1794103500 ] || no "ya es la hora de la fase A de la r5"
[ -d "$EJ" ] || no "no existe la evidencia"
[ ! -e "$D" ] || no "ya existe $D"
[ ! -e "$W-intento-r6" ] || no "ya existe la copia apartada"
cd "$EJ" || exit 2
for f in B* C* D* E*; do [ ! -e "$f" ] || no "existe $f: la r6 pasó de la fase A"; done
S='[ ! -e ~/cf-e4/ecarga-v2-ejecucion-20261108T0100Z ] && echo LIBRE || echo OCUPADA'
O="-n -o BatchMode=yes -o ConnectTimeout=10 -i"
a=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$S") || no "bastión sin respuesta"
b=$(ssh $O ~/.ssh/id_ed25519 gadmin@10.10.10.30 "ssh $O ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '$S'") || no "Sensor1 sin respuesta"
[ "$a" = LIBRE ] && [ "$b" = LIBRE ] || no "carpeta de la r6 en los hosts: bastión $a, Sensor1 $b"
L=$(find . -maxdepth 1 -name 'A[0-9]*' | sed 's|^\./||' | sort)
[ -n "$L" ] || no "no hay ficheros del intento r6"
mkdir "$D" || no "mkdir"
{ echo "motivo: $M"; date -u +%FT%TZ; printf 'copia publicada apartada: %s\n' "$W-intento-r6"; } > "$D/MOTIVO.txt"
printf '%s\n' "$L" | while IFS= read -r f; do find "$f" -type f; done | sort | while IFS= read -r f; do sha256sum "$f"; done | sed -E 's/^([0-9a-f]{64}) \*/\1  /' > "$D/SHA256SUMS"
printf '%s\n' "$L" | while IFS= read -r f; do mv -n -- "$f" "$D/$f" || exit 1; done || no "mv"
(cd "$D" && sha256sum -c --strict --quiet SHA256SUMS) || no "hashes distintos tras mover; revisar $D"
[ ! -e "$W" ] || mv -n -- "$W" "$W-intento-r6" || no "no se pudo apartar la copia"
for f in $L; do [ ! -e "$EJ/$f" ] || no "$f sigue en la carpeta"; done
echo "REARMADO r5: $(wc -l < "$D/SHA256SUMS") ficheros en $D"
