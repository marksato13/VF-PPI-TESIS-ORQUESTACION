#!/usr/bin/env bash
# PREP 46 — sensor: para la instancia candidata y el archivador de diagnostico (conservando sus ficheros) y
# registra el estado final de servicios, motor, captura, espacio y hashes. Las paradas son de procesos mios.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
P=$HOME/cf-prep-20261028
echo "## p46 inicio=$(ts)"
C=$(cat $P/candidato/motor.pid); echo "  candidato PID=$C cmd=$(tr '\0' ' ' < /proc/$C/cmdline 2>/dev/null | cut -c1-110)"
kill $C && sleep 3; echo "  [$(ts)] candidato vivo tras SIGTERM: $(kill -0 $C 2>/dev/null && echo SI || echo NO); lineas finales $(wc -l < $P/candidato/logs/motor_decision.log)"
for pid in $(pgrep -f 'archivo-diagnostico-073542'); do echo "  archivador PID=$pid $(tr '\0' ' ' < /proc/$pid/cmdline | cut -c1-120)"; kill $pid; done
sleep 2; echo "  [$(ts)] archivador vivo: $(pgrep -f 'archivo-diagnostico-073542' >/dev/null && echo SI || echo NO); ficheros $(ls $P/archivo-diagnostico-073542/live-*.pcap | wc -l), $(du -sh $P/archivo-diagnostico-073542 | cut -f1)"
echo "## estado final"
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard ppi-publicar-feed.timer cyberflow-acumular.timer; do echo "  $u $(systemctl is-active $u)/$(systemctl is-enabled $u 2>/dev/null) NR=$(systemctl show -p NRestarts --value $u 2>/dev/null)"; done
M=$(systemctl show -p MainPID --value ppi-motor); echo "  ppi-motor PID=$M desde=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor) enforce_en_argv=$(tr '\0' ' ' < /proc/$M/cmdline | grep -c -- '--enforce')"
sha256sum $HOME/cyberflow/scripts/engine/motor_decision.py $P/respaldo-motor/motor_decision.py.4c41ec44 | sed 's/^/  /'
echo "  ultimas 60 s del motor: $(python3 -c "
import json,time
n=z=e=0
for l in open('$HOME/cyberflow/logs/motor_decision.log').readlines()[-3000:]:
    r=json.loads(l)
    if r.get('logged_at',0)>time.time()-60:
        n+=1; e+= r['event']!='decision'; z+= r.get('packet_count_10s')==0
print(f'{n} registros, {z} con pk10=0, {e} no-decision')")"
echo "  ultimo PCAP del anillo: $(ls -1t /var/lib/ppi-motor-capture/live-*.pcap | head -1)"
df -h / | tail -1 | sed 's/^/  disco: /'
echo "  du diagnostico: $(du -sh $P | cut -f1)"
echo "## fin=$(ts)"
