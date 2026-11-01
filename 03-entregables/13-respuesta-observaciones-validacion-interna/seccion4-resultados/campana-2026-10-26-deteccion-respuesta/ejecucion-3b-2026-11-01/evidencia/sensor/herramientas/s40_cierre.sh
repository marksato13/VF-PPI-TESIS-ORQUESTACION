#!/usr/bin/env bash
# PASO3B s40 — sensor: cierre ordenado DESPUES de verificar las condiciones 1-5. Para el archivador (barrido final y
# FIN OK persistidos) y el muestreador (procesos propios), copia las fuentes definitivas y el estado final.
# No toca el motor ni servicios (sigue en sombra).
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; D=$B/archivo-pcap; C=$B/copias
echo "## s40 $(date -u +%FT%T.%3NZ)"
grep -q '^rc=0' $B/replay/rc.txt 2>/dev/null || { echo "PARAR: la repeticion no ha terminado con rc=0 ($(cat $B/replay/rc.txt 2>&1))"; exit 2; }
date +%s.%N > $B/cierre.t
P=$(cat $D.pid); echo "  archivador PID=$P -> TERM (barrido final)"; kill -TERM $P
for i in $(seq 1 90); do [ -s $D.rc ] && break; sleep 1; done
echo "  archivador rc=$(cat $D.rc 2>/dev/null)  ESTADO: $(cat $D/ESTADO.txt)"; tail -4 $D/archivar.log | sed 's/^/   | /'
echo "  pcaps archivados: $(ls $D/live-*.pcap | wc -l)  tamano: $(du -sh $D | cut -f1)"
echo "  FALLO/PERDIDO en archivar.log: $(grep -cE ' FALLO |PERDIDO' $D/archivar.log)"
M=$(cat $B/recursos/muestreo.pid); kill -TERM $M && echo "  muestreador $M parado ($(wc -l < $B/recursos/muestras.jsonl) muestras)"
cp -p $HOME/cyberflow/logs/_state/ciclos.jsonl $C/ciclos.jsonl
cp -p $HOME/cyberflow/logs/motor_decision.log $C/motor_decision.log
echo "  motor_decision.log: inodo $(stat -c %i $HOME/cyberflow/logs/motor_decision.log) (inicio: $(cat $B/eve/motor-inicio.txt))"
cp -p $B/eve/stats-inicio.log $C/stats-inicio.log; cp -p /var/log/suricata/stats.log $C/stats-fin.log
cp -p $B/recursos/muestras.jsonl $C/muestras.jsonl; cp -p $D/ESTADO.txt $C/archivador-ESTADO.txt; cp -p $D/archivar.log $C/archivar.log
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json $C/ && sha256sum $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json | tee $C/sha256-feed-final.txt | sed 's/^/  /'
S=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)
sudo -n journalctl --no-pager -u ppi-motor --since "$S" -o short-iso > $C/journal-motor.txt
sudo -n journalctl --no-pager -u ppi-motor-capture -u suricata --since "2026-11-01 07:00:00" -o short-iso > $C/journal-captura-suricata.txt
sudo -n journalctl --no-pager -p warning --since "2026-11-01 07:00:00" -o short-iso > $C/journal-avisos-sistema.txt
echo "  journal motor: $(wc -l < $C/journal-motor.txt) lineas, trazas: $(grep -ciE 'traceback|exception' $C/journal-motor.txt) | captura/suricata: $(wc -l < $C/journal-captura-suricata.txt) | avisos: $(wc -l < $C/journal-avisos-sistema.txt)"
systemctl show -p Id,MainPID,NRestarts,ActiveState,ActiveEnterTimestamp ppi-motor.service ppi-motor-capture.service suricata.service ppi-publicar-feed.timer > $C/servicios-fin.txt
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard; do echo "  $u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u) PID=$(systemctl show -p MainPID --value $u)"; done
cd $HOME/cyberflow && sha256sum -c $B/estado-inicial/sha256-esperado.txt 2>&1 | sed 's/^/  fin /'
P=$(systemctl show -p MainPID --value ppi-motor); echo "  --enforce en argv: '$(tr '\0' ' ' < /proc/$P/cmdline | grep -o -- --enforce)'"
( cd $C && sha256sum * > SHA256SUMS ); echo "## fin $(date -u +%FT%T.%3NZ)"
