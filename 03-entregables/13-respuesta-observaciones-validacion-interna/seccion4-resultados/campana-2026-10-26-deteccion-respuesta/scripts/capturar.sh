#!/usr/bin/env bash
# Captura PCAP CONTINUA sin huecos durante la ventana de campaña (corre en el sensor).
# No reemplaza al anillo del motor; archiva en paralelo para conservar >=120 s antes y >=90 s después
# de cada episodio. Rotación por tamaño para no perder nada.
#   [SENSOR m4rk] -> lo ejecuto yo (o root si la interfaz lo exige)
# Uso: capturar.sh <interfaz-espejo> <dir-destino>   (Ctrl-C para parar al terminar la campaña)
set -euo pipefail
IFAZ="${1:?interfaz espejo, p.ej. ens192}"
DEST="${2:?directorio de archivado con espacio suficiente}"
mkdir -p "$DEST"
echo "espacio en $DEST:"; df -h "$DEST" | awk 'NR==2{print $4" libres, "$5" usado"}'
echo "capturando $IFAZ -> $DEST/campana-%Y%m%d%H%M%S.pcap (ficheros de 200 MB). Ctrl-C para parar."
# -n sin resolución DNS; sin filtro para no perder tráfico; rotación por tamaño.
exec tcpdump -i "$IFAZ" -n -s 0 -w "$DEST/campana-%Y%m%d%H%M%S.pcap" -C 200 -Z "$(whoami)"
