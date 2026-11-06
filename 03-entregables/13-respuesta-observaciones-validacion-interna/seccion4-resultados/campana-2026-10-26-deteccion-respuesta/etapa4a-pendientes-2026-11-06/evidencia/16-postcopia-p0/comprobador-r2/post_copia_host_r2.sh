#!/usr/bin/env bash
# Comprobación POST-COPIA del paquete 902991e en UN host (r2). SOLO LECTURA: no crea, modifica ni borra nada.
# Sustituye a ../../15-traslado-902991e/post_copia_host.sh (r1), que se conserva intacto.
#
# Cada comprobación termina en uno de tres estados:
#   OK      se cumplen todos sus requisitos;
#   FALLO   la lectura funcionó y el contenido no es el exigido (ausente, distinto, inesperado);
#   ERROR   no se pudo leer o una orden falló: NUNCA cuenta como vacío, cero ni éxito.
# Salida: líneas «CHECK <id> <OK|FALLO|ERROR> <detalle>», líneas «INFO …» que no deciden, y como ÚLTIMA línea
#   RESULTADO <host> rc=<n> estado=<CONFORME|NO_CONFORME|ERROR_LECTURA> ok=<k>/<total>
# Códigos: 0 CONFORME (todas OK) · 1 NO_CONFORME (algún FALLO, ningún ERROR) · 3 ERROR_LECTURA (algún ERROR)
#          2 USO (falta N o no existe ~/cf-e4).
set -u -o pipefail
VERSION_COMPROBADOR="post_copia_host r2 2026-11-06.1"
N=${N:-}
C=902991e
SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c
EVALUADOR=53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f
ECARGA=e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80
VS14='VERSION = "evaluar_s14 2026-11-06.2"'
VCE='VERSION = "construir_entrada 2026-11-06.3"'
FICHEROS=480
CF="$HOME/cf-e4"; P="$CF/paquete-$C"; MARCA="$CF/paquete-$C.VERIFICADO.txt"; AVISO="$CF/paquete-a12deae.NO-USAR.txt"
total=0; ok=0; fallos=0; errores=0
chk() {  # chk ID ESTADO DETALLE
  total=$((total + 1))
  case "$2" in OK) ok=$((ok + 1));; FALLO) fallos=$((fallos + 1));; *) errores=$((errores + 1));; esac
  printf 'CHECK %s %s %s\n' "$1" "$2" "$3"
}
terminar() {
  local rc est
  if [ "$errores" -gt 0 ]; then rc=3; est=ERROR_LECTURA
  elif [ "$fallos" -gt 0 ] || [ "$ok" -ne "$total" ] || [ "$total" -eq 0 ]; then rc=1; est=NO_CONFORME
  else rc=0; est=CONFORME; fi
  printf 'RESULTADO %s rc=%s estado=%s ok=%s/%s\n' "$N" "$rc" "$est" "$ok" "$total"
  exit "$rc"
}
# hash de un fichero: imprime el sha256 o devuelve 1 (ausente) / 2 (existe pero no se puede leer)
hash_de() {
  [ -e "$1" ] || [ -L "$1" ] || return 1
  local h; h=$(sha256sum < "$1" 2>/dev/null | cut -c1-64) || return 2
  [ ${#h} -eq 64 ] || return 2
  printf '%s' "$h"
}
comparar_hash() {  # comparar_hash ID FICHERO ESPERADO
  local h r; h=$(hash_de "$2"); r=$?
  case $r in
    0) [ "$h" = "$3" ] && chk "$1" OK "$h" || chk "$1" FALLO "obtenido $h, esperado $3";;
    1) chk "$1" FALLO "ausente: $2";;
    *) chk "$1" ERROR "no se puede leer: $2";;
  esac
}
version() {  # version ID FICHERO LINEA
  if [ ! -e "$2" ]; then chk "$1" FALLO "ausente: $2"; return; fi
  grep -qxF "$3" "$2" 2>/dev/null; local r=$?
  case $r in 0) chk "$1" OK "$3";; 1) chk "$1" FALLO "sin la línea exacta: $3";; *) chk "$1" ERROR "grep rc $r en $2";; esac
}

[ -n "$N" ] || { echo "USO: N=<host> bash -s"; echo "RESULTADO ? rc=2 estado=USO ok=0/0"; exit 2; }
echo "INFO $N $(id -un 2>/dev/null) $(hostname 2>/dev/null) $(date -u +%FT%TZ 2>/dev/null) $VERSION_COMPROBADOR"
[ -d "$CF" ] || { echo "RESULTADO $N rc=2 estado=USO ok=0/0"; exit 2; }

# 1. Paquete
if [ -d "$P" ] && [ ! -L "$P" ]; then chk paquete OK "$P"; else chk paquete FALLO "no existe el directorio $P"; fi

# 2. Marca VERIFICADO: exactamente una línea SUMAS= y es la esperada
if [ ! -e "$MARCA" ]; then chk marca FALLO "ausente: $MARCA"
else
  lineas=$(grep -c '^SUMAS=' "$MARCA" 2>/dev/null); r=$?
  if [ $r -ge 2 ]; then chk marca ERROR "grep rc $r en $MARCA"
  elif [ "$lineas" != 1 ]; then chk marca FALLO "$lineas líneas SUMAS= (se exige 1)"
  else
    grep -qxF "SUMAS=$SUMAS" "$MARCA" 2>/dev/null; r=$?
    case $r in 0) chk marca OK "SUMAS=$SUMAS";; 1) chk marca FALLO "SUMAS distinto: $(grep '^SUMAS=' "$MARCA" | head -1)";;
      *) chk marca ERROR "grep rc $r en $MARCA";; esac
  fi
fi

# 3. SHA256SUMS interno = SUMAS
comparar_hash sumas-interno "$P/SHA256SUMS" "$SUMAS"

# 4. Hashes de todos los ficheros del manifiesto
if [ -r "$P/SHA256SUMS" ]; then
  salida=$(cd "$P" && sha256sum -c --strict --quiet SHA256SUMS 2>&1); r=$?
  case $r in
    0) chk hashes OK "sha256sum -c --strict: todos correctos";;
    1) chk hashes FALLO "$(printf '%s' "$salida" | head -5 | tr '\n' ';')";;
    *) chk hashes ERROR "sha256sum -c rc $r: $(printf '%s' "$salida" | head -3 | tr '\n' ';')";;
  esac
elif [ -e "$P/SHA256SUMS" ]; then chk hashes ERROR "SHA256SUMS ilegible"
else chk hashes FALLO "sin SHA256SUMS"; fi

# 5. Inventario exacto: lista del manifiesto = ficheros presentes (sin SHA256SUMS), y son FICHEROS
if [ -r "$P/SHA256SUMS" ] && [ -d "$P" ]; then
  esperados=$(sed -E 's/^[0-9a-f]{64}  //' "$P/SHA256SUMS" | LC_ALL=C sort); r1=$?
  presentes=$(cd "$P" && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort); r2=$?
  if [ $r1 -ne 0 ] || [ $r2 -ne 0 ]; then chk inventario ERROR "lectura fallida (sed rc $r1, find rc $r2)"
  else
    ne=$(printf '%s\n' "$esperados" | grep -c .); np=$(printf '%s\n' "$presentes" | grep -c .)
    faltan=$(comm -23 <(printf '%s\n' "$esperados") <(printf '%s\n' "$presentes") | grep . | head -5 | tr '\n' ' ')
    sobran=$(comm -13 <(printf '%s\n' "$esperados") <(printf '%s\n' "$presentes") | grep . | head -5 | tr '\n' ' ')
    if [ -z "$faltan" ] && [ -z "$sobran" ] && [ "$ne" -eq "$FICHEROS" ] && [ "$np" -eq "$FICHEROS" ]; then
      chk inventario OK "$np ficheros, ninguno ausente, ninguno inesperado"
    else chk inventario FALLO "manifiesto $ne, presentes $np (se exigen $FICHEROS); ausentes: ${faltan:-ninguno}; inesperados: ${sobran:-ninguno}"; fi
  fi
else chk inventario ERROR "sin SHA256SUMS legible o sin paquete"; fi

# 6-7. Evaluador y manifiesto de E-carga
comparar_hash evaluador "$P/deploy/etapa4/sensor1/evaluar_ecarga.py" "$EVALUADOR"
comparar_hash ecarga-sha256sums "$P/deploy/etapa4/ecarga/SHA256SUMS" "$ECARGA"
if [ -r "$P/deploy/etapa4/ecarga/SHA256SUMS" ]; then
  salida=$(cd "$P/deploy/etapa4/ecarga" && sha256sum -c --strict --quiet SHA256SUMS 2>&1); r=$?
  case $r in 0) chk ecarga-verifica OK "sha256sum -c";; 1) chk ecarga-verifica FALLO "$(printf '%s' "$salida" | head -3 | tr '\n' ';')";;
    *) chk ecarga-verifica ERROR "sha256sum -c rc $r";; esac
else chk ecarga-verifica FALLO "sin ecarga/SHA256SUMS legible"; fi

# 8. Versiones
version version-evaluar_s14 "$P/deploy/etapa4/ecarga/evaluar_s14.py" "$VS14"
version version-construir_entrada "$P/deploy/etapa4/ecarga/construir_entrada.py" "$VCE"

# 9. Aviso de sustitución junto a paquete-a12deae
if [ ! -d "$CF/paquete-a12deae" ]; then chk aviso FALLO "no existe paquete-a12deae junto al que debe estar el aviso"
elif [ ! -e "$AVISO" ]; then chk aviso FALLO "ausente: $AVISO"
else
  grep -qF "SUSTITUIDO por ~/cf-e4/paquete-$C" "$AVISO" 2>/dev/null; r=$?
  case $r in 0) chk aviso OK "$(head -1 "$AVISO")";; 1) chk aviso FALLO "el aviso no nombra paquete-$C";; *) chk aviso ERROR "grep rc $r";; esac
fi

# 10. Sin restos parciales del traslado
restos=$(find "$CF" -maxdepth 1 -name ".paquete-$C.parcial.*" 2>/dev/null); r=$?
if [ $r -ne 0 ]; then chk sin-parciales ERROR "find rc $r en $CF"
elif [ -n "$restos" ]; then chk sin-parciales FALLO "restos: $(printf '%s' "$restos" | tr '\n' ' ')"
else chk sin-parciales OK "ningún .paquete-$C.parcial.*"; fi

# Informativo (no decide): registro del traslado y estado de paquete-a12deae
for l in "$CF"/traslado-902991e.*.log; do [ -e "$l" ] && echo "INFO registro $(basename "$l"): $(tail -1 "$l" 2>&1)"; done
if [ -r "$CF/paquete-a12deae/deploy/etapa4/ecarga/SHA256SUMS" ]; then
  (cd "$CF/paquete-a12deae/deploy/etapa4/ecarga" && sha256sum -c --strict --quiet SHA256SUMS > /dev/null 2>&1); r=$?
  echo "INFO paquete-a12deae ecarga/SHA256SUMS $(sha256sum < "$CF/paquete-a12deae/deploy/etapa4/ecarga/SHA256SUMS" | cut -c1-8) verifica_rc=$r ficheros=$(find "$CF/paquete-a12deae" -type f | wc -l)"
fi
terminar
