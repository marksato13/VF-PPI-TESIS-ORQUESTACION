#!/usr/bin/env bash
# Verifica MANIFIESTO.sha256 contra los blobs de origin/main (lo que sirve GitHub), sin checkout.
set -u
R="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio"
P="03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa3-cierre-tecnico-2026-11-02"
cd "$R" || exit 2
git fetch -q origin
echo "origin/main = $(git rev-parse --short origin/main)"
ok=0; mal=0
while read -r h f; do
  f="${f#\*}"; g=$(git show "origin/main:$P/$f" | sha256sum | cut -d' ' -f1)
  if [ "$g" = "$h" ]; then ok=$((ok+1)); else mal=$((mal+1)); echo "DISTINTO: $f"; fi
done < <(git show "origin/main:$P/MANIFIESTO.sha256")
echo "coinciden=$ok distintos=$mal"
