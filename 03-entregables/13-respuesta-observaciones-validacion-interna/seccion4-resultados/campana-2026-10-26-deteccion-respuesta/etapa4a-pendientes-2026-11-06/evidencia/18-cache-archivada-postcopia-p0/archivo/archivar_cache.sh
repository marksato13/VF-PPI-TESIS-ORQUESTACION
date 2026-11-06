#!/usr/bin/env bash
# [SENSOR1 m4rk] Archiva FUERA del paquete la única caché autorizada y la retira del paquete 902991e.
# Autorización (Mark, 06-nov): «archivar la caché identificada fuera del paquete». NADA MÁS: no toca otros .pyc,
# cachés históricas (paquete-ae2900e, paquete-a12deae) ni ningún otro fichero del paquete.
# Uso: TS=<AAAAMMDDTHHMMSSZ> bash -s
# Orden: precondiciones -> destino NUEVO -> instantánea antes -> copia + metadatos -> verificación de la copia ->
#        SOLO ENTONCES rm del original -> rmdir de __pycache__ solo si quedó vacío -> instantánea después -> diferencia.
# Códigos: 0 hecho y verificado · 4 precondición o situación inesperada ANTES de retirar nada (nada retirado)
#          3 fallo al copiar/verificar la copia (original NO retirado) · 5 fallo o diferencia inesperada DESPUÉS de retirar.
set -u -o pipefail
export LC_ALL=C
VERSION="archivar_cache 2026-11-06.1"
TS=${TS:-}
ESP=${BANCO_ESP:-754ec72930cb1b187b387f0360ae65c25763ec0cccf4abe7dd5f8aa19be701d1}
U=${BANCO_USUARIO:-m4rk}              # solo el banco aislado cambia usuario y raíz; en Sensor1 no se definen
CF=${BANCO_CF:-/home/m4rk/cf-e4}
P=$CF/paquete-902991e
PC=$P/deploy/etapa4/sensor1/__pycache__
F=$PC/evaluar_ecarga.cpython-312.pyc
N=$(basename "$F")
SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c
parar() { echo "PARADA $1: $2"; echo "RESULTADO archivar rc=$1"; exit "$1"; }
sha() { sha256sum < "$1" | cut -c1-64; }
inst() {  # inst DESTINO_PREFIJO: estructura (dirs sin mtime) + sha de cada fichero regular
  find "$P" \( -type d -printf 'd %m %u %p\n' \) -o -printf '%y %m %s %T@ %u %p\n' | sort > "$1.estructura" || return 1
  (cd "$P" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$1.sha256" || return 1
}
echo "INFO $VERSION $(id -un) $(hostname) $(date -u +%FT%TZ)"
[[ "$TS" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || parar 4 "TS inválido: '$TS'"
D=$CF/archivo-cache-pyc-$TS
echo "INFO destino $D"

# ---------- precondiciones (nada se ha cambiado todavía)
[ "$(id -un)" = "$U" ] || parar 4 "usuario $(id -un), se exige $U"
[ -z "${BANCO_CF:-}${BANCO_USUARIO:-}${BANCO_ESP:-}" ] && echo "INFO modo real (sin variables BANCO_*)" || echo "INFO MODO_BANCO CF=$CF U=$U ESP=$ESP"
[ -d "$P" ] && [ ! -L "$P" ] || parar 4 "no existe el paquete $P"
[ -d "$PC" ] && [ ! -L "$PC" ] || parar 4 "__pycache__ ausente o enlace: $PC"
[ -e "$F" ] || [ -L "$F" ] || parar 4 "AUSENTE: $F"
[ ! -L "$F" ] || parar 4 "es un enlace simbólico: $F -> $(readlink "$F")"
[ -f "$F" ] || parar 4 "no es un fichero regular: $F"
h=$(sha "$F") || parar 4 "no se puede leer $F"
echo "INFO sha256 original $h"
[ "$h" = "$ESP" ] || parar 4 "hash DIFERENTE: $h (se esperaba $ESP)"
contenido=$(find "$PC" -mindepth 1 -printf '%p\n') || parar 4 "no se puede listar $PC"
[ "$contenido" = "$F" ] || parar 4 "__pycache__ contiene algo más que el fichero autorizado: $(printf '%s' "$contenido" | tr '\n' ' ')"
grep -qF "$N" "$P/SHA256SUMS" && parar 4 "el fichero figura en el manifiesto del paquete (no sería caché ajena)"
[ "$(sha "$P/SHA256SUMS")" = "$SUMAS" ] || parar 4 "SHA256SUMS del paquete distinto de $SUMAS"
case "$D/" in "$P"/*|"$CF"/paquete-*) parar 4 "el destino cae dentro de un paquete";; esac
[ ! -e "$D" ] && [ ! -L "$D" ] || parar 4 "el destino ya existe (no se sobrescribe): $D"

# ---------- destino nuevo + metadatos + instantánea antes
mkdir -m 0750 "$D" || parar 4 "no se pudo crear $D"
{
  echo "fichero_original $F"
  echo "sha256 $h"
  stat -c 'tamano_bytes %s
propietario %U:%G (uid %u gid %g)
permisos %A (%a)
tipo %F
inodo %i enlaces %h
nacimiento %w
modificacion %y
cambio_estado %z
ultimo_acceso %x' "$F"
  echo "contenido_de___pycache__:"; ls -la --time-style=full-iso "$PC"
  echo "stat_completo:"; stat "$F"
  echo "registrado $(date -u +%FT%TZ) por $(id -un)@$(hostname) con $VERSION"
} > "$D/metadatos.txt" || parar 4 "no se pudieron escribir los metadatos (nada retirado)"
inst "$D/antes" || parar 4 "instantánea previa fallida (nada retirado)"
c0=$(cd "$P" && sha256sum -c --strict --quiet SHA256SUMS 2>&1); r=$?
[ $r -eq 0 ] || parar 4 "el paquete no verifica antes de actuar (rc $r): $(printf '%s' "$c0" | head -3 | tr '\n' ';')"
echo "INFO antes: $(wc -l < "$D/antes.sha256") ficheros regulares en el paquete (480 del manifiesto + SHA256SUMS + la caché)"

# ---------- copia y verificación de la copia
cp --preserve=mode,timestamps -- "$F" "$D/$N" || parar 3 "cp falló (original NO retirado)"
hc=$(sha "$D/$N") || parar 3 "no se lee la copia (original NO retirado)"
[ "$hc" = "$ESP" ] || parar 3 "la copia tiene otro hash: $hc (original NO retirado)"
cmp -s -- "$F" "$D/$N" || parar 3 "cmp: la copia difiere (original NO retirado)"
[ "$(stat -c %s "$F")" = "$(stat -c %s "$D/$N")" ] || parar 3 "tamaño distinto (original NO retirado)"
echo "COPIA_VERIFICADA $D/$N sha256 $hc tamano $(stat -c %s "$D/$N") mtime_conservado $(stat -c %y "$D/$N")"

# ---------- retirada del original (solo ese fichero) y de __pycache__ si quedó vacío
rm -- "$F" || parar 5 "rm falló: $F"
[ ! -e "$F" ] || parar 5 "el original sigue presente tras rm"
echo "RETIRADO $F"
if [ -z "$(find "$PC" -mindepth 1 -print -quit)" ]; then rmdir -- "$PC" && echo "RETIRADO_DIR_VACIO $PC" || parar 5 "rmdir falló: $PC"
else echo "INFO $PC no está vacío: se conserva"; fi

# ---------- instantánea después y diferencia exacta
inst "$D/despues" || parar 5 "instantánea posterior fallida"
diff "$D/antes.estructura" "$D/despues.estructura" > "$D/diferencia.estructura"; de=$?
diff "$D/antes.sha256" "$D/despues.sha256" > "$D/diferencia.sha256"; dh=$?
[ $de -le 1 ] && [ $dh -le 1 ] || parar 5 "diff falló ($de/$dh)"
obt_e=$(grep '^[<>]' "$D/diferencia.estructura")
obt_h=$(grep '^[<>]' "$D/diferencia.sha256")
echo "DIFERENCIA_ESTRUCTURA:"; printf '%s\n' "$obt_e"
echo "DIFERENCIA_SHA256:"; printf '%s\n' "$obt_h"
[ "$obt_h" = "< $ESP  ./deploy/etapa4/sensor1/__pycache__/$N" ] || parar 5 "la diferencia de contenidos no es solo la caché"
[ "$(printf '%s\n' "$obt_e" | grep -c .)" = 2 ] && printf '%s\n' "$obt_e" | grep -q "^< d [0-7]* $U $PC\$" \
  && printf '%s\n' "$obt_e" | grep -q "^< f [0-7]* 27980 [0-9.]* $U $F\$" || parar 5 "la diferencia de estructura no es solo la caché y su __pycache__"
c1=$(cd "$P" && sha256sum -c --strict --quiet SHA256SUMS 2>&1); r=$?
[ $r -eq 0 ] || parar 5 "el paquete no verifica después (rc $r): $(printf '%s' "$c1" | head -3 | tr '\n' ';')"
echo "INFO despues: $(wc -l < "$D/despues.sha256") ficheros regulares; sha256sum -c del manifiesto OK; SHA256SUMS $(sha "$P/SHA256SUMS")"
(cd "$D" && sha256sum metadatos.txt "$N" antes.estructura antes.sha256 despues.estructura despues.sha256 diferencia.estructura diferencia.sha256) > "$D/SHA256SUMS" \
  || parar 5 "no se pudo sellar $D"
echo "SELLO $D/SHA256SUMS $(sha "$D/SHA256SUMS")"; cat "$D/SHA256SUMS"
echo "RESULTADO archivar rc=0"
exit 0
