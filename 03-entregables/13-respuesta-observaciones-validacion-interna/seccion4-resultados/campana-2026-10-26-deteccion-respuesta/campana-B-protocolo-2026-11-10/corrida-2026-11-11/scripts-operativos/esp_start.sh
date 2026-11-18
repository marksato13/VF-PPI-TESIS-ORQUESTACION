set -u
L=$HOME/espejo-1s-B-nueva-20261111.log
[ -e "$L" ] && { echo "PARAR: ya existe $L"; exit 2; }
setsid nohup bash -c 'END=$((SECONDS+1800)); while [ $SECONDS -lt $END ]; do read -r rx dr < <(awk "/ens37/{print \$3,\$5}" /proc/net/dev); echo "$(date -u +%T) $rx $dr"; sleep 1; done' >> "$L" 2>&1 < /dev/null &
echo "espejo 1 s iniciado $(date -u +%FT%TZ) -> $L (1800 s)"
sleep 3; tail -2 "$L"