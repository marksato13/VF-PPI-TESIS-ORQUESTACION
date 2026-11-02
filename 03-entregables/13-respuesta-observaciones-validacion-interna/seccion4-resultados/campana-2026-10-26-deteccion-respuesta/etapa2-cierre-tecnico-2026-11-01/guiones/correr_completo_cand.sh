#!/usr/bin/env bash
# Replays de la Etapa 2 sobre el tramo 08:40-09:05 del 3B (secuencial: el reloj "coste" mide CPU real).
set -u
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
D="$S/datos3b"
R="$S/replay"
REPO="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa2"
DESDE="${DESDE:-2026-11-01T07:24:40Z}"
HASTA="${HASTA:-2026-11-01T10:05:40Z}"
PREF="${PREF:-tramo}"
EXC=10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32
PY="$S/venv-modelo/Scripts/python.exe"
cd "$REPO"
correr() {  # nombre anillo disparo [extra arnes...]
  local n="$1" anillo="$2" disparo="$3"; shift 3
  local out="$R/$PREF-$n"
  rm -rf "$out"; mkdir -p "$out"
  echo "$(date -u +%T) inicio $n" >> "$R/$PREF-progreso.log"
  "$PY" -I scripts/engine/replay_motor.py --motor scripts/engine/motor_decision.py \
    --pcap-dir "$anillo" --eve "$D/copias/eve-segmento.json" --desde "$DESDE" --hasta "$HASTA" \
    --reloj coste --salida "$out" "$@" -- \
    --model-path "$D/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib" \
    --manifest-path "$D/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json" \
    --detector-name if_limpio_2026_10 --entity-network 10.10.0.0/16 --excluir "$EXC" \
    --excluir-protocolos 112,240 --history-seconds 230 --step-seconds 10 --disparo "$disparo" \
    --volcar-caracteristicas "$out/caracteristicas.jsonl" > "$out/stdout.txt" 2> "$out/stderr.txt"
  echo "$(date -u +%T) fin $n rc=$?" >> "$R/$PREF-progreso.log"
}

correr cand-e5-eventos "$R/anillo-e5-completo" eventos
