set -u
O=~/evidencia-etapa4/observacion-p4-20261106T0450Z
ps -eo args= | awk '$1=="bash" && $2=="/home/gadmin/cf-e4p/obs_muestreo.sh"' | grep -q . && { echo "PARADA muestreo bastión"; exit 1; }
[ -f $O/SHA256SUMS ] || { cp ~/cf-e4p/obs_muestreo.sh $O/; ( cd $O && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS ); }
( cd $O && sha256sum -c --quiet SHA256SUMS && echo "bastión sellado: $(wc -l < SHA256SUMS) ficheros; SHA256SUMS $(sha256sum SHA256SUMS | cut -c1-16)" )
tar -C ~/evidencia-etapa4 -czf ~/cf-e4p/obs-bastion.tgz observacion-p4-20261106T0450Z; sha256sum ~/cf-e4p/obs-*.tgz
