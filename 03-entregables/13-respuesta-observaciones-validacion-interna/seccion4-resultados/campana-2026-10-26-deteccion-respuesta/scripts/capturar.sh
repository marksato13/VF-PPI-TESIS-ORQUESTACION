#!/usr/bin/env bash
# Captura PCAP CONTINUA sin huecos durante la ventana de campaña (corre en el sensor).
#   [SENSOR m4rk] -> lo ejecuto yo. Interfaz espejo verificada: ens37 (PROMISC, sin IP).
# Archiva en paralelo al anillo del motor (que recicla a ~19 min) para conservar >=120 s antes y >=90 s
# después de cada episodio. Rotación por tamaño; nombres con marca de tiempo (NO sobrescribe); al terminar
# imprime estadísticas de tcpdump (recibidos / descartados por kernel).
#
# Uso: capturar.sh [IFAZ] [DIR]    (por defecto ens37 y /var/lib/cf-campana). Ctrl-C para parar al final.
set -uo pipefail
IFAZ="${1:-ens37}"
DEST="${2:-/var/lib/cf-campana}"
sudo install -d -o tcpdump -g "$(id -gn)" -m 2750 "$DEST" 2>/dev/null || mkdir -p "$DEST"
echo "interfaz: $IFAZ ; destino: $DEST"
df -h "$DEST" | awk 'NR==2{print "espacio: "$4" libres, "$5" usado"}'
echo "throughput de referencia (anillo, ~1 min): mídelo con estimar_espacio.sh antes de una campaña larga."
PREF="$DEST/campana-$(date -u +%Y%m%d%H%M%S)"
echo "capturando -> ${PREF}-NNN.pcap (ficheros de 200 MB). tcpdump imprime estadísticas al salir."
# -n sin DNS; -s 0 completo; -C 200 MB por fichero con sufijo incremental (no sobrescribe por el prefijo con hora);
# --print-statistics / al recibir SIGINT tcpdump informa 'packets received/dropped by kernel'.
exec sudo /usr/bin/tcpdump -i "$IFAZ" -n -s 0 -U -w "${PREF}-%03d.pcap" -C 200 -Z tcpdump
