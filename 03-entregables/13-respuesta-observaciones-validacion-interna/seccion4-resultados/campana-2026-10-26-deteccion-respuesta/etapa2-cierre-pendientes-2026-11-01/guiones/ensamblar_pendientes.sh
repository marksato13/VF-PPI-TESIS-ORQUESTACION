#!/usr/bin/env bash
# Copia a la carpeta publicada las salidas de los pendientes (comprimidas las grandes).
set -eu
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
P="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa2-cierre-pendientes-2026-11-01"
R="$P/resultados"
mkdir -p "$R/replays" "$R/rendimiento" "$R/comparaciones" "$R/diagnostico" "$R/pruebas" "$P/herramientas" "$P/guiones"
for n in sec-ref-953a436 sec-cand-862404e sec-opt-6b6ef82 perfil-ref-953a436 perfil-cand-862404e perfil-opt-6b6ef82; do
  o="$R/replays/$n"; mkdir -p "$o"; i="$S/replay/$n"
  gzip -n -9 -c "$i/caracteristicas.jsonl" > "$o/caracteristicas.jsonl.gz"
  gzip -n -9 -c "$i/ciclos-arnes.jsonl" > "$o/ciclos-arnes.jsonl.gz"
  gzip -n -9 -c "$i/_state/ciclos.jsonl" > "$o/ciclos-motor.jsonl.gz"
  gzip -n -9 -c "$i/motor_decision.log" > "$o/motor_decision.log.gz"
  cp "$i/stderr.txt" "$o/stderr.txt"
done
cp "$S/replay/secuencial-progreso.log" "$R/replays/"
cp "$S"/p2res/rendimiento/* "$R/rendimiento/"
cp "$S"/p2res/comparaciones/* "$R/comparaciones/"
cp "$S"/p2res/diagnostico/* "$R/diagnostico/"
cp "$S"/p2res/pruebas/* "$R/pruebas/"
for n in sec-ref-953a436 sec-opt-6b6ef82; do
  rm -rf "$R/analisis-3b-$n"; cp -r "$S/p2res/analisis-3b-$n" "$R/"
  cp "$S/p2res/analisis-3b-$n.stdout" "$S/p2res/analisis-3b-$n.stderr" "$R/"
done
cp "$S"/rendimiento_secuencial.py "$S"/comparar_completos.py "$S"/diagnostico_14.py "$S"/tabla_rendimiento.py "$S"/comparar_25.py "$P/herramientas/"
cp "$S"/correr_secuencial.sh "$S"/correr_secuencial_opt.sh "$S"/analizar_pendientes.sh "$S"/ensamblar_pendientes.sh "$P/guiones/"
echo ok
