#!/usr/bin/env bash
# Banco del recorrido completo de la enmienda P1 (contenedor sin red). Corre s50 (4b) de punta a punta con las herramientas
# reales sobre datos REALES del 3B (motor, ciclos, inventario) y salud/EVE sintéticos, en cuatro corridas:
#   A  eventos + guiones ORIGINALES + salud congelada   -> reproduce el defecto: toda ventana C3
#   B  limpio   + guiones ENMENDADOS + salud P1          -> todo C0 y las cifras del control publicado del 3B
#   C  eventos  + guiones ENMENDADOS + salud P1          -> C0 / C1 / C3 según el diseño, periodo completo C3
#   D  limpio, SIN segmento EVE                          -> s50 se detiene (rc 2): sin EVE no se mide Suricata
# Montajes: /e (enmienda), /herr (herramientas planas), /orig_g (guiones originales), /orig_s (control_4b original),
#           /d3b (3B real), /congelada (salud_captura de ec78ca5), /out (salidas).
set -u
OUT=${OUT:-/out}; mkdir -p "$OUT"
export HERR=/herr D3B=/d3b CONGELADA=/congelada/salud_captura.py AQUI=/e/tests
CD=2026-11-01T07:32:00Z; CH=2026-11-01T08:05:00Z; ID=2026-11-01T07:24:40Z; IH=2026-11-01T10:05:30Z
corrida() {   # nombre escenario variante guiones [control_4b_original]
  export HOME=/tmp/h-$1; mkdir -p "$HOME"
  ( [ -n "${5:-}" ] && export CONTROL_4B=$5; python3 /e/tests/generar_entorno_4b.py "$HOME" "$2" "$3" > "$OUT/gen-$1.json" 2> "$OUT/gen-$1.err" ) || { echo "FALLO generador $1"; cat "$OUT/gen-$1.err"; return 1; }
  [ "${SIN_EVE:-0}" = 1 ] && rm -f "$HOME/cf-e4/4b/copias/eve-segmento.json"
  bash "$4/s50_analisis_e4.sh" 4b "$ID" "$IH" "$CD" "$CH" > "$OUT/s50-$1.txt" 2>&1; echo $? > "$OUT/s50-$1.rc"
  [ -f "$HOME/cf-e4/4b/analisis/control-4b.json" ] && cp "$HOME/cf-e4/4b/analisis/control-4b.json" "$OUT/control-4b-$1.json"
  for f in salud-control-anillo salud-control-via; do [ -f "$HOME/cf-e4/4b/analisis/$f.json" ] && cp "$HOME/cf-e4/4b/analisis/$f.json" "$OUT/$f-$1.json"; done
  cp "$HOME/cf-e4/4b/analisis/ESTADO-PASOS.tsv" "$OUT/estado-pasos-$1.tsv" 2>/dev/null
  echo "corrida $1: rc=$(cat "$OUT/s50-$1.rc")"
}
for g in s10_sensor_archivo_e4.sh s50_analisis_e4.sh; do bash -n "/e/guiones/$g" && echo "sintaxis OK $g"; done
corrida A eventos congelada /orig_g /orig_s/control_4b.py
corrida B limpio p1 /e/guiones
corrida C eventos p1 /e/guiones
SIN_EVE=1 corrida D limpio p1 /e/guiones
python3 /e/tests/verificar_banco_4b.py "$OUT"; echo "RC_VERIFICAR=$?"
