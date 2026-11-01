#!/usr/bin/env bash
# PASO2 s40 — sensor: cierre ordenado. Para el archivador (barrido final persistido) y el muestreador (procesos
# propios), extrae las copias definitivas y registra el estado final. No toca el motor ni servicios.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; D=$B/archivo-pcap
echo "## s40 $(date -u +%FT%T.%3NZ)"
date +%s.%N > $B/cierre.t
P=$(cat $D.pid); echo "  archivador PID=$P -> TERM (barrido final)"; kill -TERM $P
for i in $(seq 1 60); do [ -s $D.rc ] && break; sleep 1; done
echo "  archivador rc=$(cat $D.rc 2>/dev/null)  ESTADO: $(cat $D/ESTADO.txt)"; tail -4 $D/archivar.log | sed 's/^/   | /'
echo "  pcaps archivados: $(ls $D/live-*.pcap | wc -l)  tamano: $(du -sh $D | cut -f1)"
M=$(cat $B/recursos/muestreo.pid); kill -TERM $M && echo "  muestreador $M parado ($(wc -l < $B/recursos/muestras.jsonl) muestras)"
bash $B/herramientas/s20_copiar.sh copias
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json $B/copias/ 2>/dev/null && echo "  feed final copiado"
sudo -n journalctl --no-pager -u ppi-motor --since "@$(cut -d. -f1 $B/reinicio.t)" -o short-iso > $B/copias/journal-motor.txt
sudo -n journalctl --no-pager -p warning --since "@$(cut -d. -f1 $B/reinicio.t)" -o short-iso > $B/copias/journal-avisos-sistema.txt
echo "  journal motor: $(wc -l < $B/copias/journal-motor.txt) lineas, trazas: $(grep -ciE 'traceback|exception' $B/copias/journal-motor.txt) | avisos sistema: $(wc -l < $B/copias/journal-avisos-sistema.txt)"
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard; do echo "  $u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u) PID=$(systemctl show -p MainPID --value $u)"; done
echo "  motor sha: $(sha256sum $HOME/cyberflow/scripts/engine/motor_decision.py $HOME/cyberflow/scripts/engine/motor_incremental.py | cut -c1-16 | tr '\n' ' ')"
echo "  --enforce en argv: '$(tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-motor)/cmdline | grep -o -- --enforce)'"
( cd $B/copias && sha256sum * > SHA256SUMS ); echo "## fin $(date -u +%FT%T.%3NZ)"
