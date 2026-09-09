#!/usr/bin/env bash
# Instala los agentes y habilidades a nivel de USUARIO, en ~/.claude/.
#
# Viven aqui, versionados, pero se usan desde cualquier carpeta: tanto en el
# repositorio del producto como en este. Si solo estuvieran en uno de los dos,
# dejarian de cargarse al trabajar en el otro.
#
# Es idempotente: repetirlo solo actualiza.
set -euo pipefail
aqui="$(cd "$(dirname "$0")" && pwd)"
destino="$HOME/.claude"

mkdir -p "$destino/agents" "$destino/skills"

n=0
for f in "$aqui"/agents/*.md; do
  cp -f "$f" "$destino/agents/"; n=$((n+1))
done
m=0
for d in "$aqui"/skills/*/; do
  s="$(basename "$d")"
  rm -rf "$destino/skills/$s"
  cp -r "$d" "$destino/skills/$s"; m=$((m+1))
done

printf '  %s agentes y %s habilidades en %s\n' "$n" "$m" "$destino"
printf '  disponibles desde cualquier carpeta, no solo desde un repositorio\n'

# Aviso util: las definiciones se leen al arrancar la sesion.
printf '\n  Si no aparecen, reinicia la sesion de Claude Code.\n'
