set -u
B=~/cf-e4/4c
[ -e $B/analisis-v2 ] && { echo "PARAR: ya existe $B/analisis-v2"; exit 2; }
[ "$(sha256sum ~/cf-e4/s50_analisis_e4_v2.sh | cut -c1-64)" = 890e4588ce75f896b783a9392073ca6ce9509d12e64d76b3c5708d59831e44b5 ] || { echo "PARAR: hash del s50 v2"; exit 2; }
echo "v1 antes: $(cd $B/analisis && sha256sum -c --quiet SHA256SUMS 2>&1 | wc -l) discrepancias; $(find $B/analisis -type f | wc -l) ficheros"
nohup setsid env ANALISIS_NOMBRE=analisis-v2 bash ~/cf-e4/s50_analisis_e4_v2.sh 4c 2026-11-09T20:45:38Z 2026-11-09T23:53:51Z 2026-11-09T21:23:00Z 2026-11-09T21:53:00Z > $B/s50-v2.log 2>&1 < /dev/null &
sleep 6
echo "lanzado $(date -u +%T)Z; procesos s50: $(pgrep -fc "[s]50_analisis_e4_v2")"; head -3 $B/s50-v2.log | cut -c1-200
