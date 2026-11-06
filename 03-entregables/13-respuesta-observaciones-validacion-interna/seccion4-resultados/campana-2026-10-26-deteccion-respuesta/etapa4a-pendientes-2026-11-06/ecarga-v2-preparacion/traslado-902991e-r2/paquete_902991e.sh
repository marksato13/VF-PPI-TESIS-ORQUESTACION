#!/usr/bin/env bash
# paquete_902991e.sh — revisión r2 (traslado 2026-11-07.1). Sustituye a evidencia/13-correccion-s14/paquete_902991e.sh.
# [LAPTOP Git Bash] Traslada el paquete del commit PUBLICADO 902991e a ~/cf-e4/paquete-902991e en el bastión, Sensor1 y
# srv-dmz. SOLO copia y verifica: no instala, no reinicia, no cambia permisos, no toca servicios, no arranca generadores
# y no ejecuta ninguna herramienta del ensayo. No sobrescribe ni elimina paquetes anteriores.
#
# Uso:
#   bash paquete_902991e.sh                         construye, verifica en local, copia y verifica en los tres hosts
#   bash paquete_902991e.sh --solo-construir DIR    construye y verifica en local en DIR (nuevo); NO copia nada
#
# Códigos de salida (última línea: "... portatil RESULTADO_GLOBAL rc=<n> <mensaje>"):
#   0  TRASLADO COMPLETO: bastion, sensor1 y srvdmz verificados (3/3). Única salida que permite seguir a P0.
#   2  PRECONDICION: uso, repositorio, git fetch, 902991e ausente o no publicado en la rama remota.
#   3  CONSTRUCCION: git archive, extracción, SHA256SUMS, evaluador, manifiesto de E-carga, versiones o tgz.
#   4  TRANSFERENCIA_AL_BASTION: scp del paquete o de op_host falla. Ningún host preparado.
#   5  SSH_BASTION / SIN_RESULTADO: no se pudo ejecutar el reparto o su salida no se puede interpretar.
#   6  TRASLADO INCOMPLETO: algún host no quedó verificado. NO continuar como si estuviera preparado.
# Un error de limpieza se registra y NUNCA sustituye al código original.
# CF_REPO (opcional) apunta a otro clon del producto; solo lo usa el banco de pruebas.
set -u -o pipefail
VERSION_GUION="paquete_902991e r2 2026-11-07.1"
C=902991e
CFULL=902991ec077c9495a99e1075cb26af35ae980507
RAMA=origin/recuperacion/etapa4a-pendientes-20261106
ESPERADO=53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f
ECARGA=e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80
VS14='VERSION = "evaluar_s14 2026-11-06.2"'
VCE='VERSION = "construir_entrada 2026-11-06.3"'
R="${CF_REPO:-/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion}"
B=gadmin@10.10.10.30
K="$HOME/.ssh/id_ed25519"
O=(-o BatchMode=yes -o ConnectTimeout=10)
RUN="$(date -u +%Y%m%dT%H%M%SZ)-$$"
W=""; CONSERVAR_W=0; REMOTO_PENDIENTE=0; TGZ=""; SUMAS=""; NF=""

nota() { printf '%s portatil %s rc=%s %s\n' "$(date -u +%FT%TZ)" "$1" "$2" "$3"; return 0; }
limpiar() {
  local r
  if [ $REMOTO_PENDIENTE -eq 1 ]; then   # el reparto no llegó a limpiar: retirar SOLO los ficheros de este RUN
    ssh "${O[@]}" -i "$K" "$B" "rm -f -- /tmp/cf-e4-stage-$C.$RUN.tgz /tmp/cf-e4-op_host-$C.$RUN.sh" < /dev/null; r=$?
    nota limpieza-bastion $r "$([ $r -eq 0 ] && echo 'tmp de este RUN retirados' || echo 'NO retirados (revisar /tmp del bastión)')"
  fi
  if [ -n "$W" ] && [ $CONSERVAR_W -eq 0 ] && [ -e "$W" ]; then
    rm -rf -- "$W"; r=$?
    [ $r -eq 0 ] || nota limpieza-local $r "NO-ELIMINADO $W"
  fi
  return 0
}
fin() { local rc=$1; limpiar; nota RESULTADO_GLOBAL "$rc" "$2"; exit "$rc"; }
h() { sha256sum -- "$1" 2>/dev/null | cut -c1-64; }

construir() {   # construye y verifica en $W; deja TGZ, SUMAS y NF
  local P="$W/paquete-$C" x
  if ! git -c core.autocrlf=false -C "$R" archive --format=tar -o "$W/fuente.tar" "$CFULL"; then nota git-archive 3 fallo; return 3; fi
  if ! mkdir -- "$P" || ! tar -xf "$W/fuente.tar" -C "$P"; then nota extraccion-local 3 fallo; return 3; fi
  rm -f -- "$W/fuente.tar"
  if ! ( cd "$P" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum ) > "$W/sumas.crudo"; then
    nota sha256sums 3 "no se pudo calcular"; return 3
  fi
  # Se escribe FUERA del árbol y luego se mueve: así SHA256SUMS nunca se lista a sí mismo.
  if ! sed -E 's/^([0-9a-f]{64}) \*/\1  /' "$W/sumas.crudo" > "$W/SHA256SUMS" || [ ! -s "$W/SHA256SUMS" ] \
     || ! mv -- "$W/SHA256SUMS" "$P/SHA256SUMS"; then
    nota sha256sums 3 "no se pudo escribir"; return 3
  fi
  if ! ( cd "$P" && sha256sum -c --strict --quiet SHA256SUMS ); then nota sha256sums 3 "no verifica en local"; return 3; fi
  NF=$(wc -l < "$P/SHA256SUMS")
  x=$(h "$P/deploy/etapa4/sensor1/evaluar_ecarga.py")
  if [ "$x" != "$ESPERADO" ]; then nota evaluador 3 "${x:-ausente} != $ESPERADO"; return 3; fi
  if ! grep -qxF -- "$VS14" "$P/deploy/etapa4/ecarga/evaluar_s14.py" || ! grep -qxF -- "$VCE" "$P/deploy/etapa4/ecarga/construir_entrada.py"; then
    nota versiones 3 "evaluar_s14 o construir_entrada no son las esperadas"; return 3
  fi
  x=$(h "$P/deploy/etapa4/ecarga/SHA256SUMS")
  if [ "$x" != "$ECARGA" ] || ! ( cd "$P/deploy/etapa4/ecarga" && sha256sum -c --strict --quiet SHA256SUMS ); then
    nota manifiesto-ecarga 3 "${x:-ausente} != $ECARGA o no verifica"; return 3
  fi
  if ! tar -C "$W" -cf "$W/paquete.tar" "paquete-$C" || ! gzip -n -c "$W/paquete.tar" > "$W/paquete-$C.tgz"; then
    nota tgz 3 "no se pudo empaquetar"; return 3
  fi
  rm -f -- "$W/paquete.tar"
  TGZ=$(h "$W/paquete-$C.tgz"); SUMAS=$(h "$P/SHA256SUMS")
  if ! [[ "$TGZ" =~ ^[0-9a-f]{64}$ ]] || ! [[ "$SUMAS" =~ ^[0-9a-f]{64}$ ]]; then nota tgz 3 "hash ilegible"; return 3; fi
  nota paquete 0 "$NF ficheros; evaluador $ESPERADO; ecarga/SHA256SUMS $ECARGA; SHA256SUMS interno $SUMAS; tgz $TGZ"
  return 0
}

# --- 1. Uso, referencia Git ---------------------------------------------------------------------------------------
SOLO=""
if [ $# -eq 2 ] && [ "$1" = --solo-construir ]; then SOLO=$2
elif [ $# -ne 0 ]; then fin 2 "USO: bash paquete_902991e.sh [--solo-construir DIR]"; fi
nota inicio 0 "$VERSION_GUION; RUN=$RUN; destino $C ($CFULL)"
AQUI="$(cd "$(dirname "$0")" && pwd)" || fin 2 "PRECONDICION: no se localiza la carpeta del guion"
OPH="$AQUI/op_host_902991e.sh"; REP="$AQUI/reparto_bastion_902991e.sh"
[ -f "$OPH" ] && [ -f "$REP" ] || fin 2 "PRECONDICION: faltan op_host_902991e.sh o reparto_bastion_902991e.sh junto al guion"
git -C "$R" rev-parse --git-dir > /dev/null 2>&1 || fin 2 "PRECONDICION: $R no es un repositorio git"
git -C "$R" fetch -q origin; r=$?
nota git-fetch $r origin; [ $r -eq 0 ] || fin 2 "PRECONDICION: git fetch falla; no se usa una referencia sin confirmar"
x=$(git -C "$R" rev-parse --verify -q "$CFULL^{commit}"); r=$?
[ $r -eq 0 ] && [ "$x" = "$CFULL" ] || fin 2 "PRECONDICION: $CFULL no existe en el repositorio"
git -C "$R" merge-base --is-ancestor "$CFULL" "$RAMA"; r=$?
nota referencia $r "$CFULL en $RAMA (punta $(git -C "$R" rev-parse --short "$RAMA" 2>/dev/null))"
[ $r -eq 0 ] || fin 2 "PRECONDICION: $CFULL no está publicado en $RAMA"

# --- 2. Construcción y verificación local --------------------------------------------------------------------------
if [ -n "$SOLO" ]; then
  [ -e "$SOLO" ] && fin 2 "PRECONDICION: $SOLO ya existe; no se sobrescribe"
  mkdir -p -- "$SOLO" || fin 2 "PRECONDICION: no se puede crear $SOLO"
  W=$(cd "$SOLO" && pwd); CONSERVAR_W=1
else
  W=$(mktemp -d -t cf-e4-portatil.XXXXXX) || { W=""; fin 2 "PRECONDICION: mktemp falla"; }
fi
construir || fin 3 "CONSTRUCCION: el paquete no supera la verificación local; no se copia nada"
if [ -n "$SOLO" ]; then
  printf 'TGZ=%s\nSUMAS=%s\nFICHEROS=%s\n' "$TGZ" "$SUMAS" "$NF"
  fin 0 "SOLO CONSTRUIDO en $W (no se ha copiado nada)"
fi

# --- 3. Transferencia al bastión -----------------------------------------------------------------------------------
REMOTO_PENDIENTE=1
scp -q "${O[@]}" -i "$K" "$W/paquete-$C.tgz" "$B:/tmp/cf-e4-stage-$C.$RUN.tgz" < /dev/null; r=$?
nota scp-paquete-bastion $r "/tmp/cf-e4-stage-$C.$RUN.tgz"
[ $r -eq 0 ] || fin 4 "TRANSFERENCIA_AL_BASTION: el paquete no llegó; NINGÚN host preparado"
scp -q "${O[@]}" -i "$K" "$OPH" "$B:/tmp/cf-e4-op_host-$C.$RUN.sh" < /dev/null; r=$?
nota scp-op_host-bastion $r "/tmp/cf-e4-op_host-$C.$RUN.sh"
[ $r -eq 0 ] || fin 4 "TRANSFERENCIA_AL_BASTION: op_host no llegó; NINGÚN host preparado"

# --- 4. Reparto y verificación en los tres hosts -------------------------------------------------------------------
ssh "${O[@]}" -i "$K" "$B" "RUN=$RUN TGZ=$TGZ SUMAS=$SUMAS bash -s" < "$REP" > "$W/salida-reparto.txt" 2>&1; rb=$?
[ $rb -eq 255 ] || REMOTO_PENDIENTE=0        # el reparto se ejecutó y limpia sus propios ficheros
cat -- "$W/salida-reparto.txt"
nota ssh-reparto $rb "$([ $rb -eq 255 ] && echo 'SSH al bastión fallido' || echo ejecutado)"

ok=0; faltan=""; sinres=0
for hh in bastion sensor1 srvdmz; do
  n=$(grep -cE "^RESULTADO $hh rc=" "$W/salida-reparto.txt")
  l=$(grep -E "^RESULTADO $hh rc=[0-9]+ estado=[A-Z0-9_]+\$" "$W/salida-reparto.txt")
  if [ "$n" = 1 ] && [ -n "$l" ]; then
    hrc=$(printf '%s' "$l" | sed -E 's/^RESULTADO [a-z0-9]+ rc=([0-9]+) .*$/\1/')
    hest=$(printf '%s' "$l" | sed -E 's/^.* estado=([A-Z0-9_]+)$/\1/')
  else
    hrc=-; hest=SIN_RESULTADO; sinres=$((sinres + 1))
  fi
  case "$hrc:$hest" in
    0:VERIFICADO|0:YA_VERIFICADO) ok=$((ok + 1)); nota "host-$hh" 0 "$hest" ;;
    *) faltan="$faltan $hh"; nota "host-$hh" "$hrc" "$hest: paquete NO preparado en $hh" ;;
  esac
done
if [ $ok -eq 3 ] && [ $rb -eq 0 ]; then
  fin 0 "TRASLADO COMPLETO: bastion, sensor1 y srvdmz verificados (3/3)"
fi
if [ $sinres -eq 3 ]; then
  fin 5 "SSH_BASTION/SIN_RESULTADO (ssh rc $rb): estado de los hosts DESCONOCIDO; no hay ningún host confirmado"
fi
fin 6 "TRASLADO INCOMPLETO: $ok/3 verificados; NO preparado en:$faltan (ssh rc $rb). No continuar con P0; ver el procedimiento de recuperación"
