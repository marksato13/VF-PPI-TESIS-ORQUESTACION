#!/usr/bin/env bash
# Instalador del stack. Idempotente: repetirlo no rompe nada ni reinstala.
#
#   sudo stack/install.sh              todo
#   sudo stack/install.sh base docs    solo esos bloques
#
# Bloques:  base  docs  docker  backup
. "$(dirname "$0")/install/comun.sh"
exige_root
cd "$(dirname "$0")"

BLOQUES=("$@")
[ ${#BLOQUES[@]} -eq 0 ] && BLOQUES=(base docs docker backup)

declare -A SCRIPT=(
  [base]=install/00-base.sh [docs]=install/10-docs.sh
  [docker]=install/20-docker.sh [backup]=install/30-backup.sh
)

# 'base' siempre primero: los demas dependen de el.
if [[ " ${BLOQUES[*]} " != *" base "* ]]; then
  BLOQUES=(base "${BLOQUES[@]}")
fi

fallos=0
for b in "${BLOQUES[@]}"; do
  s="${SCRIPT[$b]:-}"
  [ -n "$s" ] || { rojo "Bloque desconocido: $b"; exit 2; }
  if bash "$s"; then :; else rojo "FALLO el bloque $b"; fallos=$((fallos+1)); fi
done

echo
if [ "$fallos" -eq 0 ]; then
  verde "Instalacion terminada sin fallos."
else
  rojo "$fallos bloque(s) fallaron. El resto si quedo instalado."
fi
echo "Comprueba el resultado con:   stack/verify.sh"
exit "$fallos"
