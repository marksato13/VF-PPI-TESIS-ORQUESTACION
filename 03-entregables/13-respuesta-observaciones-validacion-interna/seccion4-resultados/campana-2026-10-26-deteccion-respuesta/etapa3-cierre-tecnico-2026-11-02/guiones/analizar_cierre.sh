#!/usr/bin/env bash
# Cierre tecnico de la Etapa 3: analizar_3b.py (SIN MODIFICAR) sobre el replay del cierre con los
# mismos argumentos que e3; comparaciones con sec-opt-6b6ef82 (Etapa 2) y con e3-b1ee393 (Etapa 3);
# cambios de auth_failure y recorrido hasta el feed; via rapida por episodio; matriz de reglas.
# Uso: N=cierre-<hash>-e5-eventos bash analizar_cierre.sh
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
C="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
H2="$C/etapa2-cierre-pendientes-2026-11-01/herramientas"
REPO="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa3"
E="$C/ejecucion-3b-2026-11-01/evidencia/sensor"
V="$C/revision-3b-2026-11-01/resultados/sensor/integridad-v2.json"
n="${N:?falta N}"
L="$S/replay/$n"; X="$S/cierreres"; out="$X/analisis-3b-$n"
E3="$S/replay/e3-b1ee393-e5-eventos"
rm -rf "$out"; mkdir -p "$out" "$X/comparaciones"
cd "$C/scripts"
python analizar_3b.py --marcas "$E/copias/marcas.jsonl" --motor "$L/motor_decision.log" \
  --config "$E/herramientas/config-campana-3b.json" --ciclos "$L/_state/ciclos.jsonl" \
  --inventario "$L/motor_decision.log" --inventario-rango "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z" \
  --destinos "$E/analisis/destinos-3b.csv" --integridad "$V" --calidad-fuentes "$E/analisis/calidad-fuentes.json" \
  --control "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z" --etiqueta "replay cierre Etapa 3: $n" \
  --salida "$out" > "$out.stdout" 2> "$out.stderr"
echo "analizar_3b rc=$?"
cd "$X"
# vivo_revisado <- sec-ref-953a436, replay_ref <- sec-opt-6b6ef82, replay_cand <- cierre
python "$H2/comparar_25.py" "$S/p2res/analisis-3b-sec-ref-953a436/analisis-3b.json" \
  "$S/p2res/analisis-3b-sec-opt-6b6ef82/analisis-3b.json" "$out/analisis-3b.json" \
  comparaciones/25-ref-vs-opt-vs-cierre.json > comparaciones/25-ref-vs-opt-vs-cierre.stdout
# e3 como referencia directa del cierre
python "$H2/comparar_25.py" "$S/p2res/analisis-3b-sec-ref-953a436/analisis-3b.json" \
  "$S/e3res/analisis-3b-e3-b1ee393-e5-eventos/analisis-3b.json" "$out/analisis-3b.json" \
  comparaciones/25-ref-vs-e3-vs-cierre.json > comparaciones/25-ref-vs-e3-vs-cierre.stdout
python "$H2/comparar_completos.py" "$S/replay/sec-opt-6b6ef82" "$L" comparaciones/sec-opt-6b6ef82-vs-$n.json > /dev/null
python "$H2/comparar_completos.py" "$E3" "$L" comparaciones/e3-b1ee393-vs-$n.json
python "$H2/rendimiento_secuencial.py" "$S/datos3b/marcas.jsonl" "$L" "$X/rendimiento-$n.json" > /dev/null
cd "$REPO"
python scripts/etapa3/cambios_auth_failure.py "$E3/motor_decision.log" "$L/motor_decision.log" \
  "$S/cierre/viejo/scripts/engine/publicar_feed_v2.py" scripts/engine/publicar_feed_v2.py \
  "$X/cambios-auth-failure-e3-vs-$n.json" > "$X/cambios-auth-failure.stdout"
python scripts/etapa3/via_rapida_episodios.py "$S/datos3b/marcas.jsonl" "$out/analisis-3b.json" \
  "$S/e3/rapido-3b-k8.jsonl" "$X/via-rapida-episodios-$n.json" > /dev/null
python scripts/etapa3/matriz_reglas.py "$L/motor_decision.log" "$S/datos3b/marcas.jsonl" "$X/matriz-reglas-$n.json" > /dev/null
python scripts/etapa3/observacion_dns.py "$X/observacion-3b-ensayo.json" "$S/datos3b/copias/eve-segmento.json" \
  --excluir 10.10.20.30 > "$X/observacion-3b-ensayo.stdout"
echo FIN
