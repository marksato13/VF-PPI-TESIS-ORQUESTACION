#!/usr/bin/env bash
# Estima el espacio de la captura de la campaña a partir del throughput REAL del anillo del motor.
#   [SENSOR m4rk] -> lo ejecuto yo. Solo lectura.
# Mide el tamaño de los PCAP del anillo en una ventana y extrapola a la duración prevista de la campaña.
set -uo pipefail
ANILLO=/var/lib/ppi-motor-capture
# duración prevista: 25 episodios; cada uno calentamiento/contexto(ya contado una vez) + ataque + observación
# por defecto estima con 25 episodios * (90 ataque + 90 obs + 120 contexto) + 60 calentamiento ~= 7 500 s.
DUR_S="${1:-7500}"
sz=$(sudo find "$ANILLO" -maxdepth 1 -name 'live-*.pcap' -printf '%s %T@\n' 2>/dev/null | sort -k2 -n)
n=$(echo "$sz" | wc -l)
bytes=$(echo "$sz" | awk '{s+=$1} END{print s+0}')
t0=$(echo "$sz" | head -1 | awk '{print $2}')
t1=$(echo "$sz" | tail -1 | awk '{print $2}')
python3 - "$bytes" "$t0" "$t1" "$DUR_S" "$n" <<'PY'
import sys
b,t0,t1,dur,n=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5])
span=max(1.0,t1-t0)
mibps=b/1048576/span
print(f"anillo: {n} ficheros, {b/1048576:.1f} MiB en {span:.0f} s => {mibps*3600:.0f} MiB/h base")
est=mibps*dur
print(f"duracion prevista {dur:.0f} s => ~{est/1024:.2f} GiB base (SIN picos de ataque)")
print("picos: una inundacion/escaneo multiplica el ritmo; multiplicar por un factor prudente (x5-x10) "
      "para los tramos de ataque. Reservar holgura; hoy hay ~21 GiB libres en /.")
PY
