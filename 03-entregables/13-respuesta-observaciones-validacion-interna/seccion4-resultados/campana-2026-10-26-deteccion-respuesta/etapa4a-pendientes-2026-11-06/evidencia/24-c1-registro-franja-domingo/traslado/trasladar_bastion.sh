#!/usr/bin/env bash
# [LAPTOP Git Bash] Traslado aditivo de las herramientas corregidas al bastión. VERSION 2026-11-07.3.
#   trasladar_bastion.sh preparar SALIDA   solo local: construye el tgz desde el commit publicado y lo verifica
#   trasladar_bastion.sh copiar SALIDA     ESCRIBE EN EL BASTIÓN. Solo con la orden de traslado de Mark
#   trasladar_bastion.sh verificar         solo lectura en el bastión; es el paso A3b
# 2026-11-07.3: el tgz fija formato y permisos, así no depende de cómo vea el modo de los ficheros cada entorno.
# Los bytes salen de `git show COMMIT:…` de la rama publicada, nunca de la copia de trabajo. No reinicia nada, no toca
# ~/cf-e4/paquete-902991e y no llega a Sensor1, srv-dmz ni clientes: todos estos guiones corren en el bastión.
# rc: 0 bien · 1 referencia o hash distinto · 2 uso · el del bastión si falla allí
set -u -o pipefail
export LC_ALL=C
AQUI="$(cd "$(dirname "$0")" && pwd)"
C=0a794f4; CL=0a794f4d06ecf795c4fb991b858eeab3ed64ca98; SUMAS=fa9b4c7b661677fc2ab7d434017d67cafd85e5e77a08ea56d6b89aa4b571cf89; TGZ=08b8bea3ffb7a6104a1dd0a43af52d827a4e77e2f03f2ece8e8238fd5955dfd6
RAMA=origin/recuperacion/etapa4a-pendientes-20261106
PR="${CF_PRODUCTO:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion}"
FICHEROS="arrancar_c1.sh construir_entrada.py derivar_s7.py generadores.sh guardia.py muestreo_bastion.sh puerta_c1.py s7_post.sh"
BASTION=gadmin@10.10.10.30
LLAVE=${CF_LLAVE:-$HOME/.ssh/id_ed25519}
ORDEN=${1:-}; SALIDA=${2:-}
SSHO="-o BatchMode=yes -o ConnectTimeout=10 -i $LLAVE"

preparar() {
  [ -n "$SALIDA" ] && [ ! -e "$SALIDA" ] || { echo "uso: preparar SALIDA_NUEVA"; exit 2; }
  git -C "$PR" fetch -q origin || { echo "FALLO git fetch"; exit 1; }
  git -C "$PR" merge-base --is-ancestor "$CL" "$RAMA" || { echo "FALLO $CL no está en $RAMA"; exit 1; }
  mkdir -p "$SALIDA/ficheros" || exit 2
  local f h e
  for f in $FICHEROS; do
    git -C "$PR" show "$CL:deploy/etapa4/ecarga/$f" > "$SALIDA/ficheros/$f" || { echo "FALLO git show $f"; exit 1; }
    h=$(sha256sum < "$SALIDA/ficheros/$f" | cut -c1-64)
    e=$(git -C "$PR" show "$CL:deploy/etapa4/ecarga/SHA256SUMS" | sed -n "s/^\([0-9a-f]\{64\}\)  $f\$/\1/p")
    [ "$h" = "$e" ] || { echo "FALLO $f: $h distinto del SHA256SUMS del commit ($e)"; exit 1; }
    printf '%s  %s\n' "$h" "$f"
  done > "$SALIDA/ficheros/SHA256SUMS"
  (cd "$SALIDA/ficheros" && tar --format=ustar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --mode=0644 -cf - -- SHA256SUMS $FICHEROS) | gzip -n > "$SALIDA/ecarga-bastion-$C.tgz"
  h=$(sha256sum < "$SALIDA/ficheros/SHA256SUMS" | cut -c1-64)
  [ "$h" = "$SUMAS" ] || { echo "FALLO SHA256SUMS $h distinto de $SUMAS"; exit 1; }
  h=$(sha256sum < "$SALIDA/ecarga-bastion-$C.tgz" | cut -c1-64)
  [ "$h" = "$TGZ" ] || { echo "FALLO tgz $h distinto de $TGZ"; exit 1; }
  echo "OK    tgz $h, SHA256SUMS $SUMAS, commit $CL"
}

case "$ORDEN" in
  preparar) preparar ;;
  copiar)
    F="$SALIDA/ecarga-bastion-$C.tgz"
    [ -f "$F" ] && [ "$(sha256sum < "$F" | cut -c1-64)" = "$TGZ" ] || { echo "FALLO falta el tgz preparado o es distinto"; exit 1; }
    scp -q $SSHO "$F" "$BASTION:/tmp/cf-e4-ecarga-bastion-$C.tgz" || { echo "FALLO scp"; exit 1; }
    ssh $SSHO "$BASTION" bash -s -- instalar "$C" "$SUMAS" "$TGZ" < "$AQUI/instalar_bastion_host.sh" ;;
  verificar)
    ssh $SSHO "$BASTION" bash -s -- verificar "$C" "$SUMAS" < "$AQUI/instalar_bastion_host.sh" ;;
  *) echo "uso: trasladar_bastion.sh preparar|copiar SALIDA | verificar"; exit 2 ;;
esac
