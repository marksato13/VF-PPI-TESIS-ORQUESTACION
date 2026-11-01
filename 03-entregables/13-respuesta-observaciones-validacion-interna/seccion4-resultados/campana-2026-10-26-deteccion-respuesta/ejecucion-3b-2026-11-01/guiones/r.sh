#!/usr/bin/env bash
# r.sh <script> <bastion|sensor|srv|kali|clientes> : ejecuta un script local en un host via el bastion; salida en out_<nombre>.txt (UTF-8)
d=$(cd "$(dirname "$0")" && pwd); s="$1"; h="${2:-bastion}"
case "$h" in
 bastion) r="tr -d '\r' | bash -s";;
 sensor) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'bash -s'";;
 srv) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'bash -s'";;
 kali) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'bash -s'";;
 clientes) r="tr -d '\r' | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'bash -s'";;
esac
n=$(basename "$s" .sh)
sed '1s/^\xEF\xBB\xBF//' "$d/$s" | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$r" 2>&1 | tee "$d/out_$n.txt"
