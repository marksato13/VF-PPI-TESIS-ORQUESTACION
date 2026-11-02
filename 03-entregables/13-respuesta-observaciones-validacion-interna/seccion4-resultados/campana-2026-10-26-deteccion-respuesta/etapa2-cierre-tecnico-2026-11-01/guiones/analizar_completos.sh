#!/usr/bin/env bash
# analizar_3b.py (sin modificar) sobre los replays completos del 3B: el propio replay hace de
# registro "en vivo" y de inventario; integridad v2, calidad de fuentes y destinos son los del 3B.
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
C="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
E="$C/ejecucion-3b-2026-11-01/evidencia/sensor"
V="$C/revision-3b-2026-11-01/resultados/sensor/integridad-v2.json"
R="$S/replay"
cd "$C/scripts"
for n in ref-orig15-periodico cand-e5-eventos; do
  L="$R/completo-$n"
  out="$S/cierre-res/analisis-3b-$n"
  rm -rf "$out"; mkdir -p "$out"
  python analizar_3b.py --marcas "$E/copias/marcas.jsonl" --motor "$L/motor_decision.log" \
    --config "$E/herramientas/config-campana-3b.json" --ciclos "$L/_state/ciclos.jsonl" \
    --inventario "$L/motor_decision.log" --inventario-rango "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z" \
    --destinos "$E/analisis/destinos-3b.csv" --integridad "$V" --calidad-fuentes "$E/analisis/calidad-fuentes.json" \
    --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "replay cierre Etapa 2: $n" \
    --salida "$out" > "$out.stdout" 2> "$out.stderr"
  echo "$n rc=$?"
done
