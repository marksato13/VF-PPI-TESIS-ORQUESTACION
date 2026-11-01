# PASO3B s60 — sensor (solo lectura de la evidencia): rutas absolutas, tamano y sha256 de los voluminosos que NO se suben a Git
set -u; B=$HOME/cf-3b-20261101T0721Z; O=$B/voluminosos-sha256.txt
[ -e "$O" ] && { echo "PARAR: existe $O"; exit 2; }
{ echo "# host=$(hostname) usuario=$(id -un) generado=$(date -u +%FT%TZ)"; echo "# sha256  bytes  ruta_absoluta"
  for f in $B/archivo-pcap/live-*.pcap $B/copias/eve-segmento.json $B/copias/stats-inicio.log $B/eve/stats-inicio.log; do
    echo "$(sha256sum "$f" | cut -c1-64)  $(stat -c %s "$f")  $(readlink -f "$f")"; done; } > $O
echo "pcap: $(grep -c 'live-.*\.pcap' $O)  bytes_pcap: $(grep 'live-' $O | awk '{s+=$2} END{print s}')  lineas: $(wc -l < $O)  sha_lista: $(sha256sum $O | cut -c1-64)"
head -4 $O; tail -3 $O
