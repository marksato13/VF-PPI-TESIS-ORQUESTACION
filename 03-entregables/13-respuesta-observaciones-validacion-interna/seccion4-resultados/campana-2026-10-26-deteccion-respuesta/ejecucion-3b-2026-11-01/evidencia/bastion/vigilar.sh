#!/usr/bin/env bash
# vigilancia: una linea por minuto (solo lectura del sensor)
while :; do
  ssh -n -o BatchMode=yes -o ConnectTimeout=8 sensor1 'B=$HOME/cf-3b-20261101T0721Z
  P=$(systemctl show -p MainPID --value ppi-motor)
  c=$(tail -n 6 $HOME/cyberflow/logs/_state/ciclos.jsonl | python3 -c "import sys,json,time
cs=[json.loads(l) for l in sys.stdin]; print(\"dur=%s pend=%s edad=%.0f\" % ([round(c[\"duracion_s\"],2) for c in cs],[c[\"ventanas_pendientes\"] for c in cs], time.time()-cs[-1][\"fin_ciclo\"]))")
  m=$(tail -1 $B/recursos/muestras.jsonl | python3 -c "import sys,json;m=json.loads(sys.stdin.read());print(\"rss=%.0fMB avail=%.0fMB load1=%s\" % (m[\"rss_kb\"]/1024,m[\"memavail_kb\"]/1024,m[\"load1\"]))")
  d=$(tail -n 400 /var/log/suricata/stats.log | grep capture.kernel_drops | tail -1 | awk "{print \$NF}")
  echo "$(date -u +%FT%TZ) motor=$(systemctl is-active ppi-motor) pid=$P NR=$(systemctl show -p NRestarts --value ppi-motor) enforce=$(tr "\0" " " < /proc/$P/cmdline | grep -c -- --enforce) cap=$(systemctl is-active ppi-motor-capture) sur=$(systemctl is-active suricata) drops=$d | $c | $m | arch: $(cat $B/archivo-pcap/ESTADO.txt | cut -c1-60) | disco=$(df -P / | awk "NR==2{print \$5}")"' >> $HOME/cf-3b-20261101T0721Z/vigilancia.log 2>&1
  sleep 60
done
