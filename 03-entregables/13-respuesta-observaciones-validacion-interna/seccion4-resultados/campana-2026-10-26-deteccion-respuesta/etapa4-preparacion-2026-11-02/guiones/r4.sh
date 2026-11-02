#!/usr/bin/env bash
# [LAPTOP Git Bash] r4.sh <guion> <bastion|sensor|srv|kali|clientes> [argumentos...]
# Igual que r.sh del 3B (ejecuta un guion local en un host a través del bastión, salida en out_<guion>.txt), pero
# además pasa ARGUMENTOS al guion. Por seguridad solo admite argumentos con letras, cifras y los signos . : , - _ +
# (fases, fechas ISO, epochs): si no, se detiene sin conectar.
set -u
d=$(cd "$(dirname "$0")" && pwd); s="${1:?guion}"; h="${2:?host}"; shift 2
for x in "$@"; do
  [[ "$x" =~ ^[A-Za-z0-9.:,_+-]+$ ]] || { echo "PARADA argumento no admitido: $x"; exit 2; }
done
a="$*"
case "$h" in
 bastion) r="tr -d '\r' | bash -s -- $a";;
 sensor) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'bash -s -- $a'";;
 srv) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'bash -s -- $a'";;
 kali) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'bash -s -- $a'";;
 clientes) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'bash -s -- $a'";;
 *) echo "PARADA host desconocido: $h"; exit 2;;
esac
n=$(basename "$s" .sh)
sed '1s/^\xEF\xBB\xBF//' "$d/$s" | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$r" 2>&1 | tee "$d/out_${n}${a:+_${a//[:, ]/_}}.txt"
