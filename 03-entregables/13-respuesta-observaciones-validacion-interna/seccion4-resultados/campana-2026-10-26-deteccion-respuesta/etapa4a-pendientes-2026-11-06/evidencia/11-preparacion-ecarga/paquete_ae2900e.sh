#!/usr/bin/env bash
# [LAPTOP Git Bash] Paquete del commit PUBLICADO ae2900e -> ~/cf-e4/paquete-ae2900e en bastión, Sensor1 y srv-dmz.
# Solo copia y verifica: no instala nada en servicios, no reinicia nada y NO sobrescribe (op_host.sh se niega si la
# carpeta o el tgz ya existen). Deja junto a paquete-f6dc685, sin tocarlo, un aviso de no uso para el veredicto.
set -euo pipefail
C=ae2900e
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
echo "portátil: evaluar_ecarga.py del archivo de $RAMA = $EV"
[ "$EV" = "$ESPERADO" ] || { echo "ABORTA: el evaluador del paquete no es el publicado"; exit 2; }
echo "portátil: $(grep -m1 '^VERSION = ' "$W/paquete-$C/deploy/etapa4/sensor1/evaluar_ecarga.py")"
echo "portátil: ficheros $(wc -l < "$W/paquete-$C/SHA256SUMS"); SHA256SUMS interno $(sha256sum < "$W/paquete-$C/SHA256SUMS" | cut -c1-64)"
tar -C "$W" -czf "$W/paquete-$C.tgz" "paquete-$C"
echo "portátil: tgz $(sha256sum < "$W/paquete-$C.tgz" | cut -c1-64)"
cat > "$W/aviso.txt" <<'EOF'
paquete-f6dc685 contiene evaluar_ecarga.py 2026-11-06.3 (sha256 953506fb44344e954e5f5e440cab18d27b5daed9f376153bdc42cc51697f4fda),
con el defecto de «veredicto» corregido en ae2900e (PROTOCOLO-CARGA-v2 r2, §0.1).
NO debe utilizarse para emitir el veredicto de E-carga. Usar ~/cf-e4/paquete-ae2900e
(evaluar_ecarga.py 2026-11-06.4, sha256 53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f).
EOF
K="$HOME/.ssh/id_ed25519"
B="gadmin@10.10.10.30"
SO="-o BatchMode=yes -o ConnectTimeout=10"
scp -q $SO -i "$K" "$W/paquete-$C.tgz" "$B:/tmp/cf-e4-stage-$C.tgz"
scp -q $SO -i "$K" "$W/aviso.txt" "$B:/tmp/cf-e4-stage-aviso.txt"
scp -q $SO -i "$K" "$AQUI/op_host.sh" "$B:/tmp/cf-e4-op_host.sh"
# Primero los dos hosts remotos (desde el bastión, que guarda la copia de staging), luego el propio bastión.
ssh $SO -i "$K" "$B" "C=$C ESPERADO=$ESPERADO bash -s" <<'REMOTO'
set -u
for d in 'm4rk@10.10.60.11 cyberflow-to-sensor sensor1' 'adminsrvdmz@10.10.30.10 cyberflow-to-srv srvdmz'; do
  set -- $d
  O="-o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/$2"
  scp -q $O /tmp/cf-e4-stage-$C.tgz /tmp/cf-e4-stage-aviso.txt "$1:/tmp/"
  ssh $O "$1" "C=$C ESPERADO=$ESPERADO N=$3 bash -s" < /tmp/cf-e4-op_host.sh; echo "$3: rc $?"
done
C=$C ESPERADO=$ESPERADO N=bastion bash /tmp/cf-e4-op_host.sh; echo "bastion: rc $?"
rm -f /tmp/cf-e4-op_host.sh /tmp/cf-e4-stage-$C.tgz /tmp/cf-e4-stage-aviso.txt
REMOTO
rm -r "$W"
