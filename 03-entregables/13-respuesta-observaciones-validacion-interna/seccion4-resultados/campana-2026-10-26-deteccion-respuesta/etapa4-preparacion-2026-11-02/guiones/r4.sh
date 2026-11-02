#!/usr/bin/env bash
# [LAPTOP Git Bash] r4.sh <guion> <bastion|sensor|srv|kali|clientes> [argumentos...]
# Igual que r.sh del 3B (ejecuta un guion local en un host a través del bastión, salida en out_<guion>.txt), pero
# además pasa ARGUMENTOS al guion. Por seguridad solo admite argumentos con letras, cifras y los signos . : , - _ +
# (fases, fechas ISO, epochs): si no, se detiene sin conectar.
# Errores (2026-11-02, defecto 4): pipefail; el rc es el del guion remoto (o el de SSH, sed o tee si fallan ellos):
# antes `… | ssh … | tee` devolvía siempre el rc de tee (0). La última línea del out_*.txt dice qué rc hubo.
set -u -o pipefail
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
o="$d/out_${n}${a:+_${a//[:, ]/_}}.txt"
sed '1s/^\xEF\xBB\xBF//' "$d/$s" | ssh -o BatchMode=yes -o ConnectTimeout=10 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 "$r" 2>&1 | tee "$o"
p=("${PIPESTATUS[@]}")
# el rc del guion remoto llega como rc de ssh (ssh devuelve el del orden remoto; 255 si falla la conexión)
rc=${p[1]}; [ "${p[0]}" != 0 ] && rc=${p[0]}; [ "$rc" = 0 ] && [ "${p[2]}" != 0 ] && rc=${p[2]}
echo "## r4 rc=$rc (sed=${p[0]} ssh=${p[1]} tee=${p[2]}) $(date -u +%FT%T.%3NZ)" | tee -a "$o"
exit "$rc"
