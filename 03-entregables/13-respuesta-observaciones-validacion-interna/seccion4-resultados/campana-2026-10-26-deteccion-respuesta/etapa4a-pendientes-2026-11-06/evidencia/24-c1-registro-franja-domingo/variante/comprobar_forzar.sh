#!/usr/bin/env bash
# [LAPTOP Git Bash] Lanza comprobar_forzar_host.sh en clientes a través del bastión. SOLO LECTURA. VERSION 2026-11-07.1
#   comprobar_forzar.sh con|sin|vivo SALIDA_NUEVA
# Mismo transporte que comprobar_p12.sh: el host imprime primero el sha256 de lo recibido, que debe ser el local.
# rc: 0 CUMPLE · 1 NO_CUMPLE · 3 ERROR o transporte incoherente · 2 uso
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
M=${1:-}; S=${2:-}
[ "$M" = con ] || [ "$M" = sin ] || [ "$M" = vivo ] || { echo "uso: comprobar_forzar.sh con|sin|vivo SALIDA_NUEVA"; exit 2; }
[ -n "$S" ] && [ ! -e "$S" ] || { echo "SALIDA vacía o ya existe"; exit 2; }
G="$AQUI/comprobar_forzar_host.sh"; [ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || { echo "CR en $G"; exit 2; }
O="-o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
L=$(sha256sum < "$G" | cut -c1-64); B64=$(base64 -w0 < "$G")
mkdir "$S" || exit 2
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 \"set -o pipefail; printf %s $B64 | base64 -d | sha256sum && printf %s $B64 | base64 -d | bash -s -- $M\"" \
  < /dev/null > "$S/clientes.stdout" 2> "$S/clientes.stderr"; rc=$?
echo "$rc" > "$S/clientes.rc"
rec=$(head -1 "$S/clientes.stdout" | cut -c1-64); ult=$(tail -1 "$S/clientes.stdout"); req=$(grep "^REQ FORZAR\.$M " "$S/clientes.stdout")
if [ "$rec" != "$L" ]; then g=3; e="TRANSPORTE_DISTINTO recibido=$rec local=$L"
elif [ "$ult" != "FIN_FORZAR rc=$rc" ] || [ "$(printf '%s' "$req" | grep -c .)" != 1 ]; then g=3; e="INCOHERENTE ssh rc=$rc, última línea «$ult»"
else case $rc in 0) g=0;; 1) g=1;; *) g=3;; esac; e="$req"; fi
echo "RESULTADO_FORZAR rc=$g guion_sha=$L $e" | tee "$S/resumen.txt"
exit $g
