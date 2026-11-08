#!/usr/bin/env bash
# [LAPTOP Git Bash] P12 en Sensor1, SOLO LECTURA. Envía comprobar_p12_host.sh en base64 dentro del argumento de ssh
# (mismo transporte que previa.sh y p0_r3.sh); el host imprime primero el sha256 de lo recibido, que debe ser el local.
#   comprobar_p12.sh SALIDA_NUEVA          (SALIDA no debe existir; guarda sensor1.stdout|stderr|rc y resumen.txt)
# rc: 0 P12 CUMPLE · 1 NO_CUMPLE · 3 ERROR o transporte/salida incoherente · 2 uso. VERSION 2026-11-07.1
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
S="${1:?uso: comprobar_p12.sh SALIDA_NUEVA}"; [ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
G="$AQUI/comprobar_p12_host.sh"; [ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || { echo "CR en $G"; exit 2; }
X=/home/m4rk/cf-e4/ecarga-v2-ejecucion-20261108T0930Z
O="-o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
L=$(sha256sum < "$G" | cut -c1-64); B64=$(base64 -w0 < "$G")
mkdir "$S" || exit 2
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"set -o pipefail; printf %s $B64 | base64 -d | sha256sum && printf %s $B64 | base64 -d | bash -s -- $X\"" \
  < /dev/null > "$S/sensor1.stdout" 2> "$S/sensor1.stderr"; rc=$?
echo "$rc" > "$S/sensor1.rc"
rec=$(head -1 "$S/sensor1.stdout" | cut -c1-64); ult=$(tail -1 "$S/sensor1.stdout"); req=$(grep '^REQ P12 ' "$S/sensor1.stdout")
if [ "$rec" != "$L" ]; then g=3; e="TRANSPORTE_DISTINTO recibido=$rec local=$L"
elif [ "$ult" != "FIN_P12 rc=$rc" ] || [ "$(printf '%s' "$req" | grep -c .)" != 1 ]; then g=3; e="INCOHERENTE ssh rc=$rc, última línea «$ult»"
else case $rc in 0) g=0;; 1) g=1;; *) g=3;; esac; e="$req"; fi
echo "RESULTADO_P12 rc=$g guion_sha=$L $e" | tee "$S/resumen.txt"
exit $g
