#!/usr/bin/env bash
# [LAPTOP Git Bash] Envía archivar_cache.sh a Sensor1 (vía bastión) en base64 dentro del argumento de ssh, exige que el
# sha256 recibido sea el del fichero local, y guarda stdout/stderr/rc en ESTA carpeta (nunca sobrescribe).
# Después trae (solo lectura) los ficheros de evidencia del destino, salvo el propio .pyc.
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
G="$AQUI/archivar_cache.sh"
TS=$(date -u +%Y%m%dT%H%M%SZ)
O="-o BatchMode=yes -o ConnectTimeout=10"
K="$HOME/.ssh/id_ed25519"
[ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || { echo "CR en $G"; exit 2; }
for x in stdout stderr rc; do [ ! -e "$AQUI/sensor1-$TS.$x" ] || { echo "ya existe sensor1-$TS.$x"; exit 2; }; done
L=$(sha256sum < "$G" | cut -c1-64); B=$(base64 -w0 < "$G")
echo "local sha256 $L TS $TS"
r="set -o pipefail; printf %s $B | base64 -d | sha256sum && printf %s $B | base64 -d | TS=$TS bash -s"
ssh $O -i "$K" gadmin@10.10.10.30 "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"$r\"" < /dev/null \
  > "$AQUI/sensor1-$TS.stdout" 2> "$AQUI/sensor1-$TS.stderr"; rc=$?
echo "$rc" > "$AQUI/sensor1-$TS.rc"
rec=$(head -1 "$AQUI/sensor1-$TS.stdout" | cut -c1-64)
echo "recibido $rec"; [ "$rec" = "$L" ] && echo "TRANSPORTE_IGUAL" || echo "TRANSPORTE_DISTINTO"
cat "$AQUI/sensor1-$TS.stdout"; echo "--- stderr"; cat "$AQUI/sensor1-$TS.stderr"; echo "rc=$rc"
if [ "$rc" = 0 ]; then
  D=/home/m4rk/cf-e4/archivo-cache-pyc-$TS
  mkdir "$AQUI/destino-sensor1-$TS" || exit 2
  ssh $O -i "$K" gadmin@10.10.10.30 "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd $D && tar -cf - --exclude=*.pyc . | base64 -w0'" < /dev/null \
    | base64 -d | tar -xf - -C "$AQUI/destino-sensor1-$TS" && echo "TRAIDO destino-sensor1-$TS"
  (cd "$AQUI/destino-sensor1-$TS" && grep -v '\.pyc$' SHA256SUMS | sha256sum -c) && echo "SELLO_LOCAL_OK (sin el .pyc, verificado en el host)"
fi
exit "$rc"
