#!/usr/bin/env bash
# PASO3B s11 — sensor: arranca el muestreador de recursos (guion aprobado del paso 2, cambiando SOLO la linea del
# directorio). Correccion del primer intento de s10, cuyo sed sustituyo la linea entera y fallo con 'R: unbound'.
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; S=$B/herramientas/sensor_muestrear.sh
pgrep -f "cf-3b-$ID/herramientas/sensor_muestrear" && { echo "PARAR: ya hay muestreador"; exit 2; }
awk -v id="$ID" 'NR==5{print "ID=" id "; R=$HOME/cf-3b-$ID/recursos; mkdir -p \"$R\"; O=$R/muestras.jsonl"; next} {print}' \
  $HOME/cf-paso2-20261101T0254Z/herramientas/sensor_muestrear.sh > "$S"
echo "## s11 $(date -u +%FT%T.%3NZ) diff frente al guion del paso 2:"; diff $HOME/cf-paso2-20261101T0254Z/herramientas/sensor_muestrear.sh "$S" | sed 's/^/  /'
setsid nohup bash "$S" > "$B/recursos/muestreo.out" 2>&1 < /dev/null &
sleep 12
echo "  muestreador PID=$(cat $B/recursos/muestreo.pid) muestras=$(wc -l < $B/recursos/muestras.jsonl) out='$(cat $B/recursos/muestreo.out)'"
tail -1 $B/recursos/muestras.jsonl | cut -c1-200
echo "  paso 2 sin tocar: $(stat -c '%n %y' $HOME/cf-paso2-20261101T0254Z/recursos/muestreo.pid)"
echo "## fin $(date -u +%FT%T.%3NZ)"
