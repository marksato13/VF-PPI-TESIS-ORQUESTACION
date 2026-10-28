#!/usr/bin/env bash
# PREFLIGHT 11a — sensor: ARRANCA una prueba breve del archivador revisado (~/bin/archivar_captura.sh, sha de HEAD)
# en un directorio NUEVO de preflight, separado de la campana. Solo se detendra este proceso (PID guardado).
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
A=$HOME/bin/archivar_captura.sh
BASE=$HOME/cf-preflight-20261028
DST=$BASE/archivador-$(date -u +%H%M%S)
echo "## p11a  inicio=$(ts)  epoch=$(date +%s.%N)"
echo "  archivador: $(sha256sum "$A" | cut -c1-64) (HEAD: 2181af5f8406e3aa4f41a26e24d7ec83bfaf72eee06aa3ee564e2dbba5639eb6)"
[ -e "$DST" ] && { echo "  ABORTO: $DST ya existe (no se sobrescribe evidencia)"; exit 2; }
mkdir -p "$BASE"
echo "  destino nuevo: $DST"
echo "  ens37 antes: $(awk '/ens37/{print "rx_bytes="$2" rx_packets="$3" rx_drop="$5}' /proc/net/dev)"
echo "  anillo antes: $(ls -1 /var/lib/ppi-motor-capture/live-*.pcap | wc -l) ficheros, activo=$(ls -1t /var/lib/ppi-motor-capture/live-*.pcap | head -1 | xargs basename)"
setsid nohup bash -c 'A="$1"; D="$2"; "$A" "$D" 20 > "$D.salida" 2>&1 & p=$!; echo "$p" > "$D.pid"; wait "$p"; echo "$?" > "$D.rc"' _ "$A" "$DST" >/dev/null 2>&1 < /dev/null &
for i in 1 2 3 4 5 6 7 8 9 10; do [ -s "$DST.pid" ] && break; sleep 0.5; done
P=$(cat "$DST.pid" 2>/dev/null)
echo "  PID archivador=$P  cmdline=$(tr '\0' ' ' < /proc/$P/cmdline 2>/dev/null)"
sleep 3
echo "  ESTADO.txt: $(cat "$DST/ESTADO.txt" 2>/dev/null || echo '(aun no)')"
echo "  salida: $(head -5 "$DST.salida" 2>/dev/null | tr '\n' '|')"
echo "$DST" > "$BASE/ULTIMA_PRUEBA"
echo "## fin=$(ts)"
