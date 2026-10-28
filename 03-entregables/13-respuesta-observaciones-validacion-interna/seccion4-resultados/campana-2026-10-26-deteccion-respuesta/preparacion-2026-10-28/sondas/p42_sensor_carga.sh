#!/usr/bin/env bash
# PREP 42 — sensor: carga durante la comparacion y frescura del log de produccion. Solo lectura.
echo "## p42 $(date -u +%FT%T.%3NZ) load=$(cut -d' ' -f1-3 /proc/loadavg) mem_libre=$(free -m | awk '/Mem/{print $7}') MB"
ps -eo pid,pcpu,rss,etime,args --sort=-pcpu | head -5 | cut -c1-150 | sed 's/^/  /'
python3 -c "import json,time; l=open('$HOME/cyberflow/logs/motor_decision.log').readlines()[-1]; print('  prod: ultima linea hace', round(time.time()-json.loads(l)['logged_at'],1), 's')"
