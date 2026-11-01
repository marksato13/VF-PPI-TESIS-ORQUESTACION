#!/usr/bin/env bash
# PASO2 s12 — sensor: arranca el muestreador de recursos y el archivador full-SPAN revisado (sha 2181af5f) hacia
# un directorio NUEVO; anota el desplazamiento inicial de eve.json para extraer despues el segmento. Sin sudo.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; A=$HOME/bin/archivar_captura.sh; DST=$B/archivo-pcap
echo "## s12 $(date -u +%FT%T.%3NZ)"
[ "$(sha256sum $A | cut -c1-64)" = 2181af5f8406e3aa4f41a26e24d7ec83bfaf72eee06aa3ee564e2dbba5639eb6 ] || { echo "ABORTO: archivador no es el revisado"; exit 2; }
[ -e "$DST" ] && { echo "ABORTO: existe $DST"; exit 2; }
mkdir -p "$DST" "$B/eve"
stat -c '{"t":%Y,"inode":%i,"size":%s}' /var/log/suricata/eve.json > "$B/eve/inicio.json"; date +%s.%N >> "$B/eve/inicio.json"; cat "$B/eve/inicio.json"
cp -p /var/log/suricata/stats.log "$B/eve/stats-inicio.log" 2>/dev/null; echo "  stats.log copiado"
setsid nohup bash "$B/herramientas/sensor_muestrear.sh" > /dev/null 2>&1 < /dev/null &
setsid nohup bash -c 'A="$1"; D="$2"; "$A" "$D" 20 > "$D.salida" 2>&1 & p=$!; echo "$p" > "$D.pid"; wait "$p"; echo "$?" > "$D.rc"' _ "$A" "$DST" >/dev/null 2>&1 < /dev/null &
sleep 30
echo "  muestreador pid=$(cat $B/recursos/muestreo.pid) muestras=$(wc -l < $B/recursos/muestras.jsonl)"; tail -1 $B/recursos/muestras.jsonl
P=$(cat "$DST.pid"); echo "  archivador PID=$P cmdline=$(tr '\0' ' ' < /proc/$P/cmdline)"
echo "  ESTADO.txt: $(cat "$DST/ESTADO.txt" 2>/dev/null)  ficheros=$(ls "$DST"/live-*.pcap 2>/dev/null | wc -l)"; tail -3 "$DST/archivar.log" 2>/dev/null
echo "## fin $(date -u +%FT%T.%3NZ)"
