#!/usr/bin/env bash
# [LAPTOP Git Bash] Lanza comprobar_rotacion_host.sh en Sensor1 a través del bastión. SOLO LECTURA. VERSION 2026-11-07.1
#   comprobar_rotacion.sh rotacion|aprendizaje SALIDA_NUEVA [EPOCH_MIN]
# Mínimos de la franja r6: rotación 1794096000 (00:00Z) y reentrenamiento 1794097800 (00:30Z). EPOCH_MIN solo para lecturas en seco.
# rc: 0 CUMPLE · 1 NO_CUMPLE · 3 ERROR o transporte incoherente · 2 uso
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
M=${1:-}; S=${2:-}
case "$M" in rotacion) E=${3:-1794096000};; aprendizaje) E=${3:-1794097800};; *) echo "uso: comprobar_rotacion.sh rotacion|aprendizaje SALIDA_NUEVA [EPOCH_MIN]"; exit 2;; esac
[[ "$E" =~ ^[0-9]+$ ]] || { echo "EPOCH_MIN no numérico"; exit 2; }
[ -n "$S" ] && [ ! -e "$S" ] || { echo "SALIDA vacía o ya existe"; exit 2; }
G="$AQUI/comprobar_rotacion_host.sh"; [ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || { echo "CR en $G"; exit 2; }
O="-o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
L=$(sha256sum < "$G" | cut -c1-64); B64=$(base64 -w0 < "$G")
mkdir "$S" || exit 2
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"set -o pipefail; printf %s $B64 | base64 -d | sha256sum && printf %s $B64 | base64 -d | bash -s -- $M $E\"" \
  < /dev/null > "$S/sensor1.stdout" 2> "$S/sensor1.stderr"; rc=$?
echo "$rc" > "$S/sensor1.rc"
rec=$(head -1 "$S/sensor1.stdout" | cut -c1-64); ult=$(tail -1 "$S/sensor1.stdout"); req=$(grep "^REQ ROTACION\.$M " "$S/sensor1.stdout")
if [ "$rec" != "$L" ]; then g=3; e="TRANSPORTE_DISTINTO recibido=$rec local=$L"
elif [ "$ult" != "FIN_ROTACION rc=$rc" ] || [ "$(printf '%s' "$req" | grep -c .)" != 1 ]; then g=3; e="INCOHERENTE ssh rc=$rc, última línea «$ult»"
else case $rc in 0) g=0;; 1) g=1;; *) g=3;; esac; e="$req"; fi
echo "RESULTADO_ROTACION rc=$g guion_sha=$L $e" | tee "$S/resumen.txt"
exit $g
