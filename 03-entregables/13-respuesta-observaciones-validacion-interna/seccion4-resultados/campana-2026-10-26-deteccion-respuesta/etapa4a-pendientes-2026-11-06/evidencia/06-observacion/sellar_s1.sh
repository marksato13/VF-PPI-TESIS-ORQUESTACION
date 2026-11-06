set -u
# [SENSOR1 m4rk] Detiene SOLO el verificador propio obs_pcap.py (FIN mal calculado: 06:11:30Z en vez de 05:51:30Z),
# comprueba que no queda ningún muestreador propio y sella la carpeta de la observación. Mensajes a stderr.
S=~/cf-e4p/observacion-p4-20261106T0450Z
propios() { ps -eo pid=,args= | awk '$2=="python3" && $3=="/home/m4rk/cf-e4p/obs_pcap.py" {print $1}
  $3=="-I" && $4 ~ /herramientas-20261106\/salud_captura.py$/ && $5=="muestrear" {print $1}'; }
for p in $(propios); do
  if ps -o args= -p $p | grep -q obs_pcap.py; then
    echo "$(date -u +%FT%TZ) detenido obs_pcap.py PID $p (FIN mal calculado: 06:11:30Z); última línea: $(tail -1 $S/pcap.jsonl | cut -c1-80)" >> $S/incidencias.txt
    kill $p
  fi
done
sleep 2
[ -z "$(propios)" ] || { echo "PARADA: siguen $(propios)" >&2; exit 1; }
[ -f $S/SHA256SUMS ] || { cp ~/cf-e4p/obs_pcap.py ~/cf-e4p/obs_pcap.log $S/
  ( cd $S && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS ); }
( cd $S && sha256sum -c --quiet SHA256SUMS && echo "Sensor1 sellado: $(wc -l < SHA256SUMS) ficheros; SHA256SUMS $(sha256sum SHA256SUMS | cut -c1-16)" >&2 ) || exit 1
cat $S/incidencias.txt >&2
tar -C ~/cf-e4p -czf - observacion-p4-20261106T0450Z
