#!/usr/bin/env bash
# Etapa 2, pendientes del cierre: corridas SECUENCIALES (nunca dos a la vez) de referencia y candidata.
# Mismo arnes (4694e38), mismas entradas congeladas, mismo modelo y misma configuracion (5 s, eventos).
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
D="$S/datos3b"
R="$S/replay"
ARNES="C:/Users/markp/AppData/Local/Temp/wcand/scripts/engine/replay_motor.py"
EXC=10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32
PY="$S/venv-modelo/Scripts/python.exe"
LOG="$R/secuencial-progreso.log"
correr() {  # nombre arbol desde hasta [extra arnes...]
  local n="$1" arbol="$2" desde="$3" hasta="$4"; shift 4
  local out="$R/$n"
  rm -rf "$out"; mkdir -p "$out"
  echo "$(date -u +%FT%TZ) inicio $n $(git -C "$arbol" rev-parse --short HEAD)" >> "$LOG"
  ( cd "$arbol" && "$PY" -I "$ARNES" --motor scripts/engine/motor_decision.py \
    --pcap-dir "$R/anillo-e5-completo" --eve "$D/copias/eve-segmento.json" --desde "$desde" --hasta "$hasta" \
    --reloj coste --salida "$out" "$@" -- \
    --model-path "$D/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib" \
    --manifest-path "$D/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json" \
    --detector-name if_limpio_2026_10 --entity-network 10.10.0.0/16 --excluir "$EXC" \
    --excluir-protocolos 112,240 --history-seconds 230 --step-seconds 10 --disparo eventos \
    --volcar-caracteristicas "$out/caracteristicas.jsonl" > "$out/stdout.txt" 2> "$out/stderr.txt" )
  echo "$(date -u +%FT%TZ) fin $n rc=$?" >> "$LOG"
}
REF=C:/Users/markp/AppData/Local/Temp/w953
CAND=C:/Users/markp/AppData/Local/Temp/wcand
F0=2026-11-01T07:24:40Z; F1=2026-11-01T10:05:40Z
correr sec-ref-953a436 "$REF" $F0 $F1
correr sec-cand-862404e "$CAND" $F0 $F1
# Perfil por etapa (envolturas del arnes) en las inundaciones r1-r4, con historia previa
correr perfil-ref-953a436 "$REF" 2026-11-01T08:05:00Z 2026-11-01T08:40:00Z --perfilar
correr perfil-cand-862404e "$CAND" 2026-11-01T08:05:00Z 2026-11-01T08:40:00Z --perfilar
echo "$(date -u +%FT%TZ) TODO_TERMINADO" >> "$LOG"
