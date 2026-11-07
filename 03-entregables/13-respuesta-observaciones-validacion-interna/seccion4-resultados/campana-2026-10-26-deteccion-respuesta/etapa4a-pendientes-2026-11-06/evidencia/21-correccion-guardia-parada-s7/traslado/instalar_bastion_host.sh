# instalar_bastion_host.sh — [BASTIÓN gadmin] Herramientas de E-carga v2 corregidas, en una carpeta APARTE del paquete.
# Se ejecuta con `bash -s -- ORDEN COMMIT SUMAS [TGZ]` desde trasladar_bastion.sh, o con `bash fichero` en el banco.
# NO toca ~/cf-e4/paquete-902991e: P0 r3 y el comprobador post-copia r3 siguen midiendo ese paquete.
#   verificar  SOLO LECTURA. Comprueba carpeta, lista exacta, sha de SHA256SUMS, cada fichero, y que generadores.sh y guardia.py
#              son los bytes del paquete.
#   instalar   Exige /tmp/cf-e4-ecarga-bastion-COMMIT.tgz con sha TGZ y carpeta libre. Extrae en temporal, verifica, y solo
#              entonces renombra. Quita el permiso de escritura. Borra el tgz de /tmp solo si todo verifica.
# rc: 0 VERIFICADO · 2 uso · 3 carpeta ya existente · 4 tgz ausente o distinto · 5 no verifica
set -u -o pipefail
export LC_ALL=C
ORDEN=${1:-}; C=${2:-}; SUMAS=${3:-}; TGZ=${4:-}
CF="$HOME/cf-e4"; D="$CF/ecarga-bastion-$C"; P="$CF/paquete-902991e/deploy/etapa4/ecarga"
F="/tmp/cf-e4-ecarga-bastion-$C.tgz"
LISTA="SHA256SUMS arrancar_c1.sh construir_entrada.py derivar_s7.py generadores.sh guardia.py muestreo_bastion.sh puerta_c1.py s7_post.sh"
fin() { echo "bastion: ESTADO_FINAL=$2 rc=$1"; exit "$1"; }
[[ $C =~ ^[0-9a-f]{7}$ ]] && [[ $SUMAS =~ ^[0-9a-f]{64}$ ]] || fin 2 USO

comprobar() {  # comprobar CARPETA
  local d=$1 f x
  [ -d "$d" ] || { echo "bastion: falta la carpeta"; return 1; }
  x=$(cd "$d" && ls -A | sort | tr '\n' ' ')
  [ "$x" = "$LISTA " ] || { echo "bastion: lista distinta: $x"; return 1; }
  x=$(sha256sum < "$d/SHA256SUMS" | cut -c1-64)
  [ "$x" = "$SUMAS" ] || { echo "bastion: SHA256SUMS $x distinto del esperado $SUMAS"; return 1; }
  (cd "$d" && sha256sum -c --strict --quiet SHA256SUMS) || { echo "bastion: algún fichero no coincide"; return 1; }
  for f in generadores.sh guardia.py; do
    cmp -s "$d/$f" "$P/$f" || { echo "bastion: $f difiere del paquete-902991e"; return 1; }
  done
  command -v flock > /dev/null || { echo "bastion: falta flock"; return 1; }
  echo "bastion: $d conforme: $(wc -l < "$d/SHA256SUMS") ficheros, SHA256SUMS $x"
}

case "$ORDEN" in
  verificar)
    comprobar "$D" && fin 0 VERIFICADO
    fin 5 NO_VERIFICA ;;
  instalar)
    [[ $TGZ =~ ^[0-9a-f]{64}$ ]] || fin 2 USO
    [ ! -e "$D" ] || fin 3 CARPETA_EXISTENTE
    [ -f "$F" ] && [ "$(sha256sum < "$F" | cut -c1-64)" = "$TGZ" ] || fin 4 TGZ_DISTINTO
    W=$(mktemp -d "$CF/.ecarga-bastion-$C.XXXXXX") || fin 5 NO_VERIFICA
    if ! tar -xzf "$F" -C "$W" --no-same-owner || ! comprobar "$W"; then rm -rf -- "$W"; fin 5 NO_VERIFICA; fi
    chmod -R a-w "$W"; chmod 755 "$W"
    mv -- "$W" "$D" || { rm -rf -- "$W"; fin 5 NO_VERIFICA; }
    chmod a-w "$D"
    comprobar "$D" || fin 5 NO_VERIFICA
    rm -f -- "$F"
    fin 0 VERIFICADO ;;
  *) fin 2 USO ;;
esac
