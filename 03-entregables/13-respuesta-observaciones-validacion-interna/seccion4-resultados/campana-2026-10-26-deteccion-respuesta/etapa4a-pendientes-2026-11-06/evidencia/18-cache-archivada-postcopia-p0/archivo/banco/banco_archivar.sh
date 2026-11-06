#!/usr/bin/env bash
# [LAPTOP Docker, sin red] Banco del guion archivar_cache.sh antes de usarlo en Sensor1.
# Paquete real 902991e (git archive del bundle) + una caché simulada de 27980 bytes. Variables BANCO_* solo aquí.
# Casos: correcto · hash distinto · enlace simbólico · ausente · __pycache__ con otro fichero · destino existente ·
#        fichero que no es regular. En todos los casos de parada se exige: rc 4 y paquete sin ningún cambio.
set -u -o pipefail
G=/a/archivar_cache.sh
fallos=0
ok()  { echo "PASA  $1"; }
mal() { echo "FALLA $1"; fallos=$((fallos + 1)); }
W=/tmp/w; rm -rf "$W"; mkdir -p "$W"
git clone -q --bare /b/producto.bundle "$W/repo.git"
preparar() {
  rm -rf "$W/cf"; mkdir -p "$W/cf/paquete-902991e"
  git -C "$W/repo.git" -c core.autocrlf=false archive 902991ec077c9495a99e1075cb26af35ae980507 | tar -x -C "$W/cf/paquete-902991e"
  (cd "$W/cf/paquete-902991e" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > ../S && mv ../S SHA256SUMS)
  mkdir "$W/cf/paquete-902991e/deploy/etapa4/sensor1/__pycache__"
  head -c 27980 /dev/urandom > "$W/cf/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc"
  ESPB=$(sha256sum < "$W/cf/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc" | cut -c1-64)
}
foto() { (cd "$W/cf" && find . -printf '%y %m %s %p\n' | LC_ALL=C sort; find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum); }
correr() { BANCO_CF="$W/cf" BANCO_USUARIO=$(id -un) BANCO_ESP="${1:-$ESPB}" TS=20261106T230000Z bash -s < "$G" > "$W/out" 2>&1; echo $?; }
F=deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc

preparar; [ "$(sha256sum < "$W/cf/paquete-902991e/SHA256SUMS" | cut -c1-64)" = 8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c ] \
  && ok "paquete de prueba = 902991e (SUMAS 8480f0e0…)" || mal "paquete de prueba distinto"

# 1. correcto
rc=$(correr); D="$W/cf/archivo-cache-pyc-20261106T230000Z"
if [ "$rc" = 0 ] && [ ! -e "$W/cf/paquete-902991e/$F" ] && [ ! -e "$W/cf/paquete-902991e/deploy/etapa4/sensor1/__pycache__" ] \
   && [ "$(sha256sum < "$D/evaluar_ecarga.cpython-312.pyc" | cut -c1-64)" = "$ESPB" ] \
   && (cd "$W/cf/paquete-902991e" && sha256sum -c --strict --quiet SHA256SUMS) && (cd "$D" && sha256sum -c --quiet SHA256SUMS) \
   && grep -q '^RETIRADO_DIR_VACIO ' "$W/out" && [ "$(find "$W/cf/paquete-902991e" -type f | wc -l)" = 481 ]; then ok "correcto: copia verificada, original y __pycache__ retirados, 480+1 ficheros, paquete verifica"
else mal "correcto (rc $rc)"; cat "$W/out"; fi
rc=$(correr); [ "$rc" = 4 ] && grep -qi 'ausente' "$W/out" && ok "segunda ejecución (ya archivado): __pycache__ ausente -> rc 4" || mal "segunda ejecución rc $rc"

parada() {  # parada NOMBRE PATRON [ESP]: exige rc 4, el patrón en la salida, el paquete intacto y sin destino creado
  local antes rc; antes=$(foto); rc=$(correr "${3:-}")
  if [ "$rc" = 4 ] && grep -q "$2" "$W/out" && [ "$(foto)" = "$antes" ]; then ok "$1 -> rc 4, nada cambiado"
  else mal "$1 (rc $rc)"; cat "$W/out"; fi
}
preparar; parada "hash distinto" "hash DIFERENTE" "$(printf '0%.0s' {1..64})"
preparar; mv "$W/cf/paquete-902991e/$F" "$W/cf/otro.pyc"; ln -s "$W/cf/otro.pyc" "$W/cf/paquete-902991e/$F"; parada "enlace simbólico" "enlace simbólico"
preparar; rm "$W/cf/paquete-902991e/$F"; parada "ausente" "AUSENTE"
preparar; : > "$W/cf/paquete-902991e/deploy/etapa4/sensor1/__pycache__/otro.cpython-312.pyc"; parada "__pycache__ con otro .pyc" "algo más"
preparar; mkdir "$W/cf/archivo-cache-pyc-20261106T230000Z"; parada "destino existente" "ya existe"
preparar; rm "$W/cf/paquete-902991e/$F"; mkdir "$W/cf/paquete-902991e/$F"; parada "no regular (directorio)" "no es un fichero regular"
echo "RESULTADO_BANCO fallos=$fallos"
exit $((fallos > 0))
