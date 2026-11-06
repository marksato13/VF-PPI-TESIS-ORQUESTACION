#!/usr/bin/env bash
# [LAPTOP Git Bash] Paquete del commit PUBLICADO a12deae -> ~/cf-e4/paquete-a12deae en bastión, Sensor1 y srv-dmz.
# Solo copia y verifica: no instala nada en servicios, no reinicia nada, no ejecuta ningún guion de E-carga y NO
# sobrescribe (op_host_a12deae.sh se niega si la carpeta o el tgz ya existen). Clientes no necesita el paquete:
# generadores.sh le llega por stdin desde el bastión.
set -euo pipefail
C=a12deae
ESPERADO=53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion"
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAMA=origin/recuperacion/etapa4a-pendientes-20261106
git -C "$R" fetch -q origin
[ "$(git -C "$R" rev-parse --short $RAMA)" = "$C" ] || { echo "ABORTA: $RAMA no es $C"; exit 2; }
W=$(mktemp -d); mkdir "$W/paquete-$C"
git -C "$R" archive "$RAMA" | tar -x -C "$W/paquete-$C"
( cd "$W/paquete-$C" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sed -E 's/^([0-9a-f]{64}) \*/\1  /' > SHA256SUMS )
EV=$(sha256sum < "$W/paquete-$C/deploy/etapa4/sensor1/evaluar_ecarga.py" | cut -c1-64)
[ "$EV" = "$ESPERADO" ] || { echo "ABORTA: el evaluador del paquete no es el publicado"; exit 2; }
ECARGA=$(sha256sum < "$W/paquete-$C/deploy/etapa4/ecarga/SHA256SUMS" | cut -c1-64)
echo "portátil: evaluar_ecarga.py $EV; ecarga/SHA256SUMS $ECARGA"
echo "portátil: ficheros $(wc -l < "$W/paquete-$C/SHA256SUMS"); SHA256SUMS interno $(sha256sum < "$W/paquete-$C/SHA256SUMS" | cut -c1-64)"
tar -C "$W" -czf "$W/paquete-$C.tgz" "paquete-$C"
echo "portátil: tgz $(sha256sum < "$W/paquete-$C.tgz" | cut -c1-64)"
K="$HOME/.ssh/id_ed25519"
B="gadmin@10.10.10.30"
SO="-o BatchMode=yes -o ConnectTimeout=10"
scp -q $SO -i "$K" "$W/paquete-$C.tgz" "$B:/tmp/cf-e4-stage-$C.tgz"
scp -q $SO -i "$K" "$AQUI/op_host_a12deae.sh" "$B:/tmp/cf-e4-op_host_a12deae.sh"
ssh $SO -i "$K" "$B" "C=$C ESPERADO=$ESPERADO ECARGA=$ECARGA bash -s" <<'REMOTO'
set -u
for d in 'm4rk@10.10.60.11 cyberflow-to-sensor sensor1' 'adminsrvdmz@10.10.30.10 cyberflow-to-srv srvdmz'; do
  set -- $d
  O="-o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/$2"
  scp -q $O /tmp/cf-e4-stage-$C.tgz "$1:/tmp/"
  ssh $O "$1" "C=$C ESPERADO=$ESPERADO ECARGA=$ECARGA N=$3 bash -s" < /tmp/cf-e4-op_host_a12deae.sh; echo "$3: rc $?"
done
C=$C ESPERADO=$ESPERADO ECARGA=$ECARGA N=bastion bash /tmp/cf-e4-op_host_a12deae.sh; echo "bastion: rc $?"
rm -f /tmp/cf-e4-op_host_a12deae.sh /tmp/cf-e4-stage-$C.tgz
REMOTO
rm -r "$W"
