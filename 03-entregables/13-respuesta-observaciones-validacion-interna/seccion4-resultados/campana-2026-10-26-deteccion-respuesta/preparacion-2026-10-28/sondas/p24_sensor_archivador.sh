#!/usr/bin/env bash
# PREP 24 — sensor: arranca el archivador revisado (sha HEAD 2181af5f) hacia un directorio NUEVO de preparacion
# (no de campana) para conservar PCAP full-SPAN de los casos de diagnostico antes/despues. PID guardado.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
A=$HOME/bin/archivar_captura.sh; BASE=$HOME/cf-prep-20261028; DST=$BASE/archivo-diagnostico-$(date -u +%H%M%S)
echo "## p24  inicio=$(ts)"
echo "  archivador sha=$(sha256sum "$A" | cut -c1-64)"
[ -e "$DST" ] && { echo "ABORTO: existe $DST"; exit 2; }
echo "  destino: $DST  | disco: $(df -hP "$HOME" | awk 'NR==2{print $4" libres ("$5")"}')"
echo "  ens37 antes: $(awk '/ens37/{print "rx_packets="$3" rx_drop="$5}' /proc/net/dev)"
setsid nohup bash -c 'A="$1"; D="$2"; "$A" "$D" 20 > "$D.salida" 2>&1 & p=$!; echo "$p" > "$D.pid"; wait "$p"; echo "$?" > "$D.rc"' _ "$A" "$DST" >/dev/null 2>&1 < /dev/null &
for i in $(seq 1 10); do [ -s "$DST.pid" ] && break; sleep 0.5; done
P=$(cat "$DST.pid"); echo "  PID=$P cmdline=$(tr '\0' ' ' < /proc/$P/cmdline)"
echo "$DST" > "$BASE/ARCHIVO_DIAGNOSTICO"
sleep 25; echo "  ESTADO.txt: $(cat "$DST/ESTADO.txt" 2>/dev/null)"; echo "  ficheros: $(ls "$DST"/live-*.pcap 2>/dev/null | wc -l)"
echo "## fin=$(ts)"
