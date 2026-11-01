#!/usr/bin/env bash
# PASO3A s11 — sensor, SOLO LECTURA: referencias verificables del motor instalado (blob git del fichero desplegado
# frente al blob en el commit 24f8a80 y en HEAD del clon) y sha256 completos.
set -u
cd ~/cyberflow
echo "## s11 $(date -u +%FT%T.%3NZ)"
echo "  HEAD del clon: $(git rev-parse HEAD 2>&1) rama: $(git rev-parse --abbrev-ref HEAD 2>&1)"
echo "  24f8a80 -> $(git rev-parse --verify 24f8a80^{commit} 2>&1)  $(git log -1 --format='%ci %s' 24f8a80 2>&1)"
echo "  ramas que contienen 24f8a80: $(git branch -a --contains 24f8a80 2>&1 | tr '\n' ' ')"
for f in scripts/engine/motor_decision.py scripts/engine/motor_incremental.py scripts/engine/heuristicos.py \
         scripts/features/extract_multilayer_v2.py scripts/features/extract_multilayer_v3.py \
         scripts/engine/publicar_feed.py scripts/engine/escalada.py scripts/engine/feed.py scripts/engine/agente_enforce.py \
         configs/features/multilayer-v2.json; do
  dep=$(git hash-object $f 2>/dev/null); c=$(git rev-parse 24f8a80:$f 2>/dev/null); h=$(git rev-parse HEAD:$f 2>/dev/null)
  ult=$(git log -1 --format=%h 24f8a80 -- $f 2>/dev/null)
  echo "  $f sha256=$(sha256sum $f | cut -c1-64) blob_desplegado=$dep blob_24f8a80=$c ($([ "$dep" = "$c" ] && echo IGUAL || echo DISTINTO)) ultimo_commit_en_24f8a80=$ult blob_HEAD=$h"
done
for f in artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json; do
  echo "  $f sha256=$(sha256sum $f | cut -c1-64)"
done
echo "  git status (resumen): $(git status --porcelain 2>&1 | wc -l) entradas; modificados rastreados:"
git status --porcelain --untracked-files=no 2>&1 | head -20 | sed 's/^/    /'
echo "## fin"
