# op_host_902991e.sh — revisión r2 (traslado 2026-11-07.1). Sustituye a evidencia/13-correccion-s14/op_host_902991e.sh.
# Se ejecuta en CADA host (bastión, Sensor1, srv-dmz) con `bash -s` o `bash <fichero>`, lanzado por
# reparto_bastion_902991e.sh. SOLO copia y verifica: no instala, no reinicia, no cambia permisos, no toca servicios y no
# ejecuta ninguna herramienta del ensayo.
#
# Entorno obligatorio: N (bastion|sensor1|srvdmz), RUN (AAAAMMDDTHHMMSSZ-PID), TGZ (sha256 del tgz enviado) y SUMAS
# (sha256 del SHA256SUMS interno del paquete). Espera el tgz en /tmp/cf-e4-stage-902991e.$RUN.tgz.
#
# Resultado utilizable = ~/cf-e4/paquete-902991e  Y  ~/cf-e4/paquete-902991e.VERIFICADO.txt con SUMAS=<SUMAS>.
# Nada más cuenta como paquete preparado. El directorio de trabajo es ~/cf-e4/.paquete-902991e.parcial.<RUN> (oculto,
# nunca utilizable) y solo se renombra a paquete-902991e cuando TODO verifica.
#
# Códigos de salida (última línea: "<N>: ESTADO_FINAL=<estado> rc=<código>"):
#   0  VERIFICADO (copia nueva) o YA_VERIFICADO (existía con marca y se re-verificó sin modificarlo)
#   2  USO / PRECONDICION (entorno inválido, ~/cf-e4 o el registro no se pueden crear, staging ya existe)
#   3  DESTINO_EXISTE: paquete-902991e o su marca ya existen sin marca coincidente; no se toca nada
#   4  TGZ_AUSENTE / TGZ_DISTINTO / COPIA_LOCAL: transferencia incompleta o alterada
#   5  EXTRACCION: tar falla, o rutas fuera de paquete-902991e/
#   6  INVENTARIO_INVALIDO: SHA256SUMS distinto, hash incorrecto, fichero ausente o fichero inesperado
#   7  EVALUADOR_DISTINTO        8  MANIFIESTO_ECARGA_DISTINTO        9  VERSION_INCORRECTA
#  10  INSTALACION / INSTALADO_SIN_MARCA (mv o marca fallidos: el paquete NO es utilizable)
#  11  AVISO_FALLIDO: paquete verificado, pero el aviso de sustitución de paquete-a12deae no se pudo crear
# Un error de limpieza se registra y NUNCA sustituye al código original.
set -u -o pipefail
VERSION_GUION="op_host_902991e r2 2026-11-07.1"
C=902991e
ESPERADO=53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f
ECARGA=e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80
VS14='VERSION = "evaluar_s14 2026-11-06.2"'
VCE='VERSION = "construir_entrada 2026-11-06.3"'
N=${N:-}; RUN=${RUN:-}; TGZ=${TGZ:-}; SUMAS=${SUMAS:-}
CF="$HOME/cf-e4"
DEST="$CF/paquete-$C"
MARCA="$CF/paquete-$C.VERIFICADO.txt"
ANT="$CF/paquete-a12deae"
AVISO="$CF/paquete-a12deae.NO-USAR.txt"
STG=""; PAR=""; TW=""; LOG=""

nota() {   # nota <operación> <rc> <detalle>: a la salida y al registro del host
  local l="$N: $1 rc=$2 $3"
  printf '%s\n' "$l"
  if [ -n "$LOG" ]; then printf '%s %s\n' "$(date -u +%FT%TZ)" "$l" >> "$LOG" 2>/dev/null; fi
  return 0
}
limpiar() {   # solo restos de ESTA ejecución; nunca paquetes anteriores ni evidencia
  local r
  if [ -n "$PAR" ] && [ -e "$PAR" ]; then
    rm -rf -- "$PAR"; r=$?
    if [ $r -eq 0 ]; then nota limpieza-staging 0 eliminado; else nota limpieza-staging $r "NO-ELIMINADO $PAR (oculto, no utilizable)"; fi
  fi
  if [ -n "$TW" ] && [ -e "$TW" ]; then
    rm -rf -- "$TW"; r=$?
    [ $r -eq 0 ] || nota limpieza-temporal $r "NO-ELIMINADO $TW"
  fi
  if [ -n "$STG" ] && [ -e "$STG" ]; then
    rm -f -- "$STG"; r=$?
    if [ $r -eq 0 ]; then nota limpieza-tgz-recibido 0 eliminado; else nota limpieza-tgz-recibido $r "NO-ELIMINADO $STG"; fi
  fi
  return 0
}
fin() {   # fin <rc> <estado>: limpia, registra y sale con el código ORIGINAL
  local rc=$1 est=$2
  limpiar
  if [ -n "$LOG" ]; then printf '%s %s: ESTADO_FINAL=%s rc=%s\n' "$(date -u +%FT%TZ)" "$N" "$est" "$rc" >> "$LOG" 2>/dev/null; fi
  printf '%s: ESTADO_FINAL=%s rc=%s\n' "$N" "$est" "$rc"
  exit "$rc"
}
h() { sha256sum -- "$1" 2>/dev/null | cut -c1-64; }
estado_de() { case $1 in 6) echo INVENTARIO_INVALIDO;; 7) echo EVALUADOR_DISTINTO;; 8) echo MANIFIESTO_ECARGA_DISTINTO;;
                         9) echo VERSION_INCORRECTA;; *) echo ERROR_$1;; esac; }

verificar() {   # verificar <dir>: inventario completo, hashes, evaluador, versiones y manifiesto de E-carga
  local D=$1 x r n
  if [ ! -f "$D/SHA256SUMS" ]; then nota inventario 6 "SHA256SUMS ausente"; return 6; fi
  x=$(h "$D/SHA256SUMS")
  if [ "$x" != "$SUMAS" ]; then nota inventario 6 "SHA256SUMS interno ${x:-ilegible} != $SUMAS"; return 6; fi
  ( cd "$D" && sha256sum -c --strict --quiet SHA256SUMS ) > "$TW/c.txt" 2>&1; r=$?
  if [ $r -ne 0 ]; then
    nota hashes 6 "sha256sum -c rc=$r ($(grep -c . "$TW/c.txt") avisos)"
    head -20 "$TW/c.txt" | sed "s|^|$N:   |"
    return 6
  fi
  if ! sed -E 's/^[0-9a-f]{64}  //' "$D/SHA256SUMS" | LC_ALL=C sort > "$TW/listado"; then nota inventario 6 "listado ilegible"; return 6; fi
  if ! ( cd "$D" && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort ) > "$TW/presente"; then
    nota inventario 6 "no se pudo recorrer el paquete"; return 6
  fi
  if ! cmp -s "$TW/listado" "$TW/presente"; then
    nota inventario 6 "faltan $(LC_ALL=C comm -23 "$TW/listado" "$TW/presente" | wc -l), sobran $(LC_ALL=C comm -13 "$TW/listado" "$TW/presente" | wc -l)"
    LC_ALL=C comm -3 "$TW/listado" "$TW/presente" | head -20 | sed "s|^|$N:   difiere |"
    return 6
  fi
  n=$(wc -l < "$TW/listado")
  nota inventario 0 "$n ficheros: hashes correctos, ninguno ausente, ninguno inesperado"
  x=$(h "$D/deploy/etapa4/sensor1/evaluar_ecarga.py")
  if [ "$x" != "$ESPERADO" ]; then nota evaluador 7 "evaluar_ecarga.py ${x:-ausente} != $ESPERADO"; return 7; fi
  nota evaluador 0 "= $ESPERADO"
  if ! grep -qxF -- "$VS14" "$D/deploy/etapa4/ecarga/evaluar_s14.py" 2>/dev/null \
     || ! grep -qxF -- "$VCE" "$D/deploy/etapa4/ecarga/construir_entrada.py" 2>/dev/null; then
    nota versiones 9 "se exige evaluar_s14 2026-11-06.2 y construir_entrada 2026-11-06.3"; return 9
  fi
  nota versiones 0 "evaluar_s14 2026-11-06.2, construir_entrada 2026-11-06.3"
  x=$(h "$D/deploy/etapa4/ecarga/SHA256SUMS")
  if [ "$x" != "$ECARGA" ]; then nota manifiesto-ecarga 8 "ecarga/SHA256SUMS ${x:-ausente} != $ECARGA"; return 8; fi
  ( cd "$D/deploy/etapa4/ecarga" && sha256sum -c --strict --quiet SHA256SUMS ) > "$TW/e.txt" 2>&1; r=$?
  if [ $r -ne 0 ]; then nota manifiesto-ecarga 8 "ecarga/SHA256SUMS no verifica (rc $r)"; return 8; fi
  nota manifiesto-ecarga 0 "= $ECARGA y verifica"
  return 0
}

aviso() {   # aviso de sustitución junto a paquete-a12deae; SOLO se llama con el paquete nuevo ya verificado y marcado
  local r
  if [ ! -e "$ANT" ]; then nota aviso 0 "no hay paquete-a12deae en este host: no hace falta aviso"; return 0; fi
  if [ -e "$AVISO" ]; then
    if [ -f "$AVISO" ] && grep -qF "paquete-$C" "$AVISO"; then nota aviso 0 "ya presente"; return 0; fi
    nota aviso 11 "$AVISO existe y no es el aviso esperado: no se toca"; return 11
  fi
  printf '%s\n' "paquete-a12deae SUSTITUIDO por ~/cf-e4/paquete-$C (verificado; RUN=$RUN; PROTOCOLO-CARGA-v2 r4)." \
    "No usar para S14 ni para construir la entrada: evaluar_s14 2026-11-06.1 no contaba el hueco anterior al tramo saturado." \
    "El contenido de paquete-a12deae no se ha modificado." > "$AVISO.tmp.$RUN" && mv -T -- "$AVISO.tmp.$RUN" "$AVISO"
  r=$?
  if [ $r -ne 0 ]; then rm -f -- "$AVISO.tmp.$RUN" 2>/dev/null; nota aviso 11 "no se pudo crear (rc $r)"; return 11; fi
  nota aviso 0 "creado junto a paquete-a12deae (su contenido no se toca)"
  return 0
}

# --- 1. Entorno ---------------------------------------------------------------------------------------------------
case "$N" in bastion|sensor1|srvdmz) ;; *) N="${N:-?}"; fin 2 USO;; esac
if ! [[ "$RUN" =~ ^[0-9]{8}T[0-9]{6}Z-[0-9]+$ ]] || ! [[ "$TGZ" =~ ^[0-9a-f]{64}$ ]] || ! [[ "$SUMAS" =~ ^[0-9a-f]{64}$ ]]; then
  nota entorno 2 "RUN, TGZ o SUMAS ausentes o mal formados"; fin 2 USO
fi
STG="/tmp/cf-e4-stage-$C.$RUN.tgz"
if ! mkdir -p -- "$CF"; then nota cf-e4 2 "no se puede crear $CF"; fin 2 PRECONDICION; fi
if [ -e "$CF/traslado-$C.$RUN.$N.log" ]; then nota registro 2 "RUN repetido: el registro ya existe y no se sobrescribe"; fin 2 PRECONDICION; fi
LOG="$CF/traslado-$C.$RUN.$N.log"
if ! : > "$LOG"; then LOG=""; nota registro 2 "no se puede crear el registro"; fin 2 PRECONDICION; fi
nota inicio 0 "$VERSION_GUION; RUN=$RUN; TGZ=$TGZ; SUMAS=$SUMAS"
TW=$(mktemp -d -t cf-e4-host.XXXXXX) || { TW=""; nota temporal 2 "mktemp falla"; fin 2 PRECONDICION; }
n=$(find "$CF" -maxdepth 1 -name ".paquete-$C.parcial.*" | wc -l)
[ "$n" -eq 0 ] || nota restos-previos 0 "$n directorio(s) .paquete-$C.parcial.* de intentos anteriores: no se tocan, no son utilizables"

# --- 2. Destino ya existente: re-verificar sin modificar, o no tocar ------------------------------------------------
if [ -e "$DEST" ] || [ -e "$MARCA" ]; then
  if [ -d "$DEST" ] && [ -f "$MARCA" ] && grep -qxF "SUMAS=$SUMAS" "$MARCA"; then
    nota destino 0 "paquete-$C ya existe con marca y el mismo SHA256SUMS: se re-verifica sin modificarlo"
    verificar "$DEST"; r=$?
    [ $r -eq 0 ] || fin $r "$(estado_de $r)_EN_PAQUETE_EXISTENTE"
    aviso || fin 11 AVISO_FALLIDO
    fin 0 YA_VERIFICADO
  fi
  nota destino 3 "paquete-$C o su marca ya existen sin marca coincidente: no se sobrescribe ni se toca"
  fin 3 DESTINO_EXISTE
fi

# --- 3. Paquete recibido -------------------------------------------------------------------------------------------
if [ ! -f "$STG" ]; then nota tgz-recibido 4 "$STG no existe"; fin 4 TGZ_AUSENTE; fi
x=$(h "$STG")
if [ "$x" != "$TGZ" ]; then nota tgz-recibido 4 "sha256 ${x:-ilegible} != $TGZ (transferencia incompleta o alterada)"; fin 4 TGZ_DISTINTO; fi
nota tgz-recibido 0 "= $TGZ"
PAR="$CF/.paquete-$C.parcial.$RUN"
if ! mkdir -- "$PAR"; then PAR=""; nota staging 2 "no se puede crear el directorio de trabajo"; fin 2 PRECONDICION; fi
if ! cp -- "$STG" "$PAR/p.tgz"; then nota copia-local 4 "cp falla"; fin 4 COPIA_LOCAL; fi
x=$(h "$PAR/p.tgz")
if [ "$x" != "$TGZ" ]; then nota copia-local 4 "copia distinta (${x:-ilegible})"; fin 4 COPIA_LOCAL; fi

# --- 4. Extracción -------------------------------------------------------------------------------------------------
if ! tar -tzf "$PAR/p.tgz" > "$TW/tar.lst" 2> "$TW/tar.err"; then
  nota extraccion 5 "tar -t falla: $(head -1 "$TW/tar.err")"; fin 5 EXTRACCION
fi
if grep -vqE "^paquete-$C(/|\$)" "$TW/tar.lst" || grep -qE '(^|/)\.\.(/|$)' "$TW/tar.lst"; then
  nota extraccion 5 "el tgz contiene rutas fuera de paquete-$C/"; fin 5 EXTRACCION
fi
if ! tar -xzf "$PAR/p.tgz" -C "$PAR" --no-same-owner 2> "$TW/tar.err"; then
  nota extraccion 5 "tar -x falla: $(head -1 "$TW/tar.err")"; fin 5 EXTRACCION
fi
if [ ! -d "$PAR/paquete-$C" ]; then nota extraccion 5 "sin paquete-$C/ tras extraer"; fin 5 EXTRACCION; fi
nota extraccion 0 "$(wc -l < "$TW/tar.lst") entradas en $PAR"

# --- 5. Verificación completa --------------------------------------------------------------------------------------
verificar "$PAR/paquete-$C"; r=$?
[ $r -eq 0 ] || fin $r "$(estado_de $r)"

# --- 6. Instalación por renombrado (sin sobrescribir) y marca ------------------------------------------------------
if [ -e "$DEST" ] || [ -e "$MARCA" ]; then nota instalacion 3 "el destino apareció durante la verificación"; fin 3 DESTINO_EXISTE; fi
if ! mv -T -- "$PAR/paquete-$C" "$DEST"; then nota instalacion 10 "mv falla"; fin 10 INSTALACION; fi
nota instalacion 0 "$DEST"
if ! { printf 'paquete-%s verificado en %s (%s)\nRUN=%s\nTGZ=%s\nSUMAS=%s\nevaluar_ecarga=%s\necarga_SHA256SUMS=%s\n' \
         "$C" "$N" "$(date -u +%FT%TZ)" "$RUN" "$TGZ" "$SUMAS" "$ESPERADO" "$ECARGA" > "$MARCA.tmp.$RUN" \
       && mv -T -- "$MARCA.tmp.$RUN" "$MARCA"; }; then
  rm -f -- "$MARCA.tmp.$RUN" 2>/dev/null
  nota marca 10 "sin marca: $DEST NO es utilizable"; fin 10 INSTALADO_SIN_MARCA
fi
nota marca 0 "$MARCA"

# --- 7. Aviso de sustitución (solo ahora, con el paquete nuevo verificado) -----------------------------------------
aviso || fin 11 AVISO_FALLIDO
fin 0 VERIFICADO
