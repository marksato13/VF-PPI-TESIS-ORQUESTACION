#!/bin/bash
# Solo lectura: datos para el procedimiento de instalacion del paso 2.
D=~/cyberflow; R=~/cf-p1/referencia; C=~/cf-p1/candidato
echo "== dependencias del motor: desplegado vs 7b275b8 vs candidato"
for f in scripts/engine/motor_decision.py scripts/engine/heuristicos.py scripts/features/extract_multilayer_v2.py \
         scripts/features/extract_multilayer_v3.py scripts/engine/motor_incremental.py configs/features/multilayer-v2.json; do
  printf '%-45s %s %s %s\n' "$f" "$(sha256sum $D/$f 2>/dev/null | cut -c1-12 || echo -)" \
    "$(sha256sum $R/$f 2>/dev/null | cut -c1-12)" "$(sha256sum $C/$f 2>/dev/null | cut -c1-12)"
done
echo "== diferencias desplegado vs 7b275b8 en scripts/engine y scripts/features"
diff -rq $D/scripts/engine $R/scripts/engine 2>&1 | grep -v __pycache__ | head -20
diff -rq $D/scripts/features $R/scripts/features 2>&1 | grep -v __pycache__ | head -10
echo "== permisos"
ls -la $D/scripts/engine/motor_decision.py $D/scripts/engine/heuristicos.py $D/scripts/engine/
stat -c '%U:%G %a %n' $D/logs $D/logs/_state 2>&1
ls -la $D/logs/_state 2>&1 | head
echo "== logrotate"
ls /etc/logrotate.d/ | grep -i -E "ppi|cyber|motor"
for f in /etc/logrotate.d/*; do grep -l "cyberflow" "$f" 2>/dev/null; done | while read f; do echo "-- $f"; cat "$f"; done
echo "== servicios que leen el log"
systemctl list-units --type=service --no-pager 2>/dev/null | grep -i -E "ppi|cyber"
echo "== tamano por registro de ciclo (candidato R2)"
head -c 2000 ~/cf-p1/r2-cand-verif/_state/ciclos.jsonl | head -1 | wc -c
wc -lc ~/cf-p1/r2-cand-verif/_state/ciclos.jsonl
