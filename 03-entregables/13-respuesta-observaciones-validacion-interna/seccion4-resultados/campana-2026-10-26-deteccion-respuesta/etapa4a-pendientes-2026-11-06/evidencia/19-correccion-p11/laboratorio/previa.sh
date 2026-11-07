#!/usr/bin/env bash
# [LAPTOP Git Bash] Comprobación previa de SOLO LECTURA en bastión, Sensor1, srv-dmz y clientes: generadores y
# muestreadores del ensayo. Envía previa_host.sh en base64 dentro del argumento de ssh; el host imprime primero el sha
# de lo recibido, que debe ser el del fichero local. Guarda <SALIDA>/<host>.stdout|stderr|rc (SALIDA no debe existir).
# rc: 0 los 4 sin procesos del ensayo · 4 alguno con procesos, error o transporte distinto · 2 uso/precondición.
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
S="${1:?uso: previa.sh SALIDA_NUEVA}"; [ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
G="$AQUI/previa_host.sh"; [ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || { echo "CR en $G"; exit 2; }
O="-o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
L=$(sha256sum < "$G" | cut -c1-64); B64=$(base64 -w0 < "$G")
mkdir "$S" || exit 2
orden() { printf 'set -o pipefail; printf %%s %s | base64 -d | sha256sum && printf %%s %s | base64 -d | N=%s bash -s' "$B64" "$B64" "$1"; }
g=0
for h in bastion sensor1 srvdmz clientes; do
  case $h in
    bastion) ssh $O -i "$K" "$B" "$(orden bastion)" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    sensor1) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"$(orden sensor1)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    srvdmz) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \"$(orden srvdmz)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    clientes) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 \"$(orden clientes)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
  esac
  rec=$(head -1 "$S/$h.stdout" | cut -c1-64)
  ult=$(tail -1 "$S/$h.stdout")
  if [ "$rec" != "$L" ]; then e=TRANSPORTE_DISTINTO; g=4
  elif [ "$ult" != "RESULTADO $h rc=$rc" ]; then e=INCOHERENTE; g=4
  elif [ "$rc" = 0 ]; then e=SIN_PROCESOS_DEL_ENSAYO
  else e=NO_CONFORME; g=4; fi
  echo "$rc" > "$S/$h.rc"
  echo "HOST $h rc=$rc estado=$e" | tee -a "$S/resumen.txt"
done
echo "RESULTADO_PREVIA rc=$g guion_sha=$L" | tee -a "$S/resumen.txt"
exit $g
