#!/usr/bin/env bash
# [LAPTOP Git Bash] Toma la instantánea (solo lectura) del paquete en bastión, Sensor1 y srv-dmz.
#   bash tomar.sh ETIQUETA     -> guarda <ETIQUETA>/<host>.stdout|stderr|rc (la carpeta NO debe existir)
#   bash tomar.sh comparar A B -> compara las dos instantáneas host a host (rc 0 idénticas; 1 difieren; 2 error)
set -u -o pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)" || exit 2
O="-o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
if [ "${1:-}" = comparar ]; then
  A="$AQUI/$2"; Z="$AQUI/$3"; rc=0
  for h in bastion sensor1 srvdmz; do
    for x in "$A" "$Z"; do [ "$(cat "$x/$h.rc" 2>/dev/null)" = 0 ] || { echo "COMPARA $h ERROR instantánea no válida en $x"; rc=2; continue 2; }; done
    la=$(grep '^INSTANTANEA ' "$A/$h.stdout" | cut -d' ' -f4-); lz=$(grep '^INSTANTANEA ' "$Z/$h.stdout" | cut -d' ' -f4-)
    d=$(diff <(sed -n '/^== ESTRUCTURA/,$p' "$A/$h.stdout" | grep -v '^INSTANTANEA ') <(sed -n '/^== ESTRUCTURA/,$p' "$Z/$h.stdout" | grep -v '^INSTANTANEA ')); r=$?
    if [ $r = 0 ] && [ "$la" = "$lz" ]; then echo "COMPARA $h IDENTICAS $la"
    elif [ $r = 1 ]; then echo "COMPARA $h DIFIEREN"; printf '%s\n' "$d" | head -20; [ $rc = 2 ] || rc=1
    else echo "COMPARA $h ERROR diff rc $r"; rc=2; fi
  done
  echo "RESULTADO_COMPARACION rc=$rc"; exit $rc
fi
E="${1:?uso: tomar.sh ETIQUETA}"; S="$AQUI/$E"
[ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
G="$AQUI/instantanea_host.sh"; [ "$(tr -cd '\r' < "$G" | wc -c)" -eq 0 ] || exit 2
L=$(sha256sum < "$G" | cut -c1-64); B64=$(base64 -w0 < "$G")
mkdir "$S" || exit 2
orden() { printf 'set -o pipefail; printf %%s %s | base64 -d | sha256sum && printf %%s %s | base64 -d | N=%s bash -s' "$B64" "$B64" "$1"; }
g=0
for h in bastion sensor1 srvdmz; do
  case $h in
    bastion) ssh $O -i "$K" "$B" "$(orden bastion)" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    sensor1) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 \"$(orden sensor1)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
    srvdmz) ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \"$(orden srvdmz)\"" < /dev/null > "$S/$h.stdout" 2> "$S/$h.stderr"; rc=$?;;
  esac
  rec=$(head -1 "$S/$h.stdout" | cut -c1-64)
  [ "$rec" = "$L" ] || { rc=97; echo "TRANSPORTE_DISTINTO $h" >> "$S/$h.stderr"; }
  echo "$rc" > "$S/$h.rc"; [ "$rc" = 0 ] || g=4
  echo "$h rc=$rc $(grep '^INSTANTANEA ' "$S/$h.stdout" | tail -1)"
done
echo "RESULTADO_INSTANTANEA $E rc=$g"; exit $g
