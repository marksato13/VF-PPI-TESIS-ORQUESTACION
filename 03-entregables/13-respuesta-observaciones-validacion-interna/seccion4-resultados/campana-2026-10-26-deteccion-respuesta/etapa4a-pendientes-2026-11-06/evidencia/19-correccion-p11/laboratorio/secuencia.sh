#!/usr/bin/env bash
# [LAPTOP Git Bash] Verificaciones de SOLO LECTURA en el laboratorio, en orden, deteniéndose si falla una precondición:
#   1. previa.sh: sin generadores ni muestreadores del ensayo (bastión, Sensor1, srv-dmz, clientes)
#   2. comprobador post-copia r3 (../../18-cache-archivada-postcopia-p0/comprobador-r3, sin cambios)
#   3. instantánea del paquete antes del P0 (y comparación con la última de la entrega 18)
#   4. P0 r3 en modo ANTICIPADO (../p0-r3/p0_r3.sh), lanzado desde $HOME con rutas absolutas
#   5. instantánea después y comparación antes/después
# Nada arranca, para ni escribe en los hosts. Cada paso guarda stdout, stderr y rc.
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
EV="$(cd "$AQUI/../.." && pwd)"
TS=$(date -u +%Y%m%dT%H%M%SZ)
echo "secuencia $TS"
bash "$AQUI/previa.sh" "$AQUI/previa-$TS"; r=$?; echo "RC_PREVIA=$r"
[ $r = 0 ] || { echo "PARADA: la comprobación previa no es conforme (rc $r)"; exit 10; }
bash "$EV/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh" "$AQUI/postcopia-r3-$TS"; r=$?; echo "RC_POSTCOPIA=$r"
[ $r = 0 ] || { echo "PARADA: post-copia r3 no conforme (rc $r)"; exit 11; }
bash "$AQUI/instantaneas/tomar.sh" "antes-p0-$TS"; r=$?; echo "RC_INST_ANTES=$r"
[ $r = 0 ] || { echo "PARADA: instantánea previa no válida (rc $r)"; exit 12; }
bash "$AQUI/instantaneas/tomar.sh" comparar "../../../18-cache-archivada-postcopia-p0/instantaneas/despues-p0" "antes-p0-$TS" \
  > "$AQUI/instantaneas/comparacion-18despues-vs-antes-p0-$TS.txt"; echo "RC_COMPARA_CON_18=$?"; cat "$AQUI/instantaneas/comparacion-18despues-vs-antes-p0-$TS.txt"
cd "$HOME" || exit 2
bash "$EV/19-correccion-p11/p0-r3/p0_r3.sh" anticipado "$AQUI/p0-r3-anticipado-$TS"; rp=$?
echo "$rp" > "$AQUI/p0-r3-anticipado-$TS.rc-driver"; echo "RC_P0=$rp"
bash "$AQUI/instantaneas/tomar.sh" "despues-p0-$TS"; echo "RC_INST_DESPUES=$?"
bash "$AQUI/instantaneas/tomar.sh" comparar "antes-p0-$TS" "despues-p0-$TS" > "$AQUI/instantaneas/comparacion-antes-despues-p0-$TS.txt"; rcmp=$?
cat "$AQUI/instantaneas/comparacion-antes-despues-p0-$TS.txt"; echo "RC_COMPARA=$rcmp"
exit 0
