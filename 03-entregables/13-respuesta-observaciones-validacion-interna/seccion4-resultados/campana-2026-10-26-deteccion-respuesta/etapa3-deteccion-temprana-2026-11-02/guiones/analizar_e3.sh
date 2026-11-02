#!/usr/bin/env bash
# analizar_3b.py (SIN MODIFICAR) sobre el replay completo de la candidata de la Etapa 3, con los
# mismos argumentos que el cierre de pendientes de la Etapa 2; comparacion con sec-opt-6b6ef82;
# via rapida por episodio; matriz de reglas.
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
C="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
H2="$C/etapa2-cierre-pendientes-2026-11-01/herramientas"
REPO="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa3"
E="$C/ejecucion-3b-2026-11-01/evidencia/sensor"
V="$C/revision-3b-2026-11-01/resultados/sensor/integridad-v2.json"
n=e3-b1ee393-e5-eventos
L="$S/replay/$n"; out="$S/e3res/analisis-3b-$n"
rm -rf "$out"; mkdir -p "$out" "$S/e3res/comparaciones"
cd "$C/scripts"
python analizar_3b.py --marcas "$E/copias/marcas.jsonl" --motor "$L/motor_decision.log" \
  --config "$E/herramientas/config-campana-3b.json" --ciclos "$L/_state/ciclos.jsonl" \
  --inventario "$L/motor_decision.log" --inventario-rango "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z" \
  --destinos "$E/analisis/destinos-3b.csv" --integridad "$V" --calidad-fuentes "$E/analisis/calidad-fuentes.json" \
  --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "replay Etapa 3: $n" \
  --salida "$out" > "$out.stdout" 2> "$out.stderr"
echo "analizar_3b rc=$?"
cd "$S/e3res"
# vivo_revisado <- sec-ref-953a436, replay_ref <- sec-opt-6b6ef82, replay_cand <- Etapa 3
python "$H2/comparar_25.py" "$S/p2res/analisis-3b-sec-ref-953a436/analisis-3b.json" \
  "$S/p2res/analisis-3b-sec-opt-6b6ef82/analisis-3b.json" "$out/analisis-3b.json" \
  comparaciones/25-ref-vs-opt-vs-e3.json
python "$H2/comparar_completos.py" "$S/replay/sec-opt-6b6ef82" "$L" comparaciones/sec-opt-6b6ef82-vs-$n.json
cd "$REPO"
python scripts/etapa3/via_rapida_episodios.py "$S/datos3b/marcas.jsonl" "$out/analisis-3b.json" \
  "$S/e3/rapido-3b-k8.jsonl" "$S/e3res/via-rapida-episodios-$n.json"
python scripts/etapa3/matriz_reglas.py "$L/motor_decision.log" "$S/datos3b/marcas.jsonl" "$S/e3res/matriz-reglas-$n.json"
