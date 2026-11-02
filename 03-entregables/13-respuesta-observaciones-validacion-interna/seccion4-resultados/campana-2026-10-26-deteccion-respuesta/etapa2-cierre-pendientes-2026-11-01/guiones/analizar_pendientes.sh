#!/usr/bin/env bash
# analizar_3b.py (sin modificar) sobre las corridas secuenciales completas de la referencia
# (953a436) y de la optimizada (6b6ef82). Mismos argumentos que el cierre tecnico.
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
C="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
E="$C/ejecucion-3b-2026-11-01/evidencia/sensor"
V="$C/revision-3b-2026-11-01/resultados/sensor/integridad-v2.json"
cd "$C/scripts"
for n in sec-opt-6b6ef82 sec-ref-953a436; do
  L="$S/replay/$n"; out="$S/p2res/analisis-3b-$n"
  rm -rf "$out"; mkdir -p "$out"
  python analizar_3b.py --marcas "$E/copias/marcas.jsonl" --motor "$L/motor_decision.log" \
    --config "$E/herramientas/config-campana-3b.json" --ciclos "$L/_state/ciclos.jsonl" \
    --inventario "$L/motor_decision.log" --inventario-rango "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z" \
    --destinos "$E/analisis/destinos-3b.csv" --integridad "$V" --calidad-fuentes "$E/analisis/calidad-fuentes.json" \
    --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "replay pendientes Etapa 2: $n" \
    --salida "$out" > "$out.stdout" 2> "$out.stderr"
  echo "$n rc=$?"
done
cd "$S/p2res"
python "$S/comparar_25.py" "$S/cierre-res/analisis-3b-cand-e5-eventos/analisis-3b.json" \
  analisis-3b-sec-ref-953a436/analisis-3b.json analisis-3b-sec-opt-6b6ef82/analisis-3b.json \
  comparaciones/25-publicado-vs-ref-vs-opt.json
