#!/usr/bin/env bash
# PREP 50 — sensor: procesos que aun refieren al archivo de diagnostico; parada del archivador (proceso mio) si sigue.
set -u
echo "## p50 $(date -u +%FT%T.%3NZ)"
ps -eo pid,ppid,etime,args | grep -F 'archivo-diagnostico-073542' | grep -v grep | sed 's/^/  /'
for pid in $(ps -eo pid,args | grep -F 'archivar_captura.sh /home/m4rk/cf-prep-20261028/archivo-diagnostico-073542' | grep -v grep | awk '{print $1}'); do
  echo "  parando $pid"; kill $pid; done
sleep 25
echo "  quedan: $(ps -eo args | grep -F 'archivo-diagnostico-073542' | grep -vc grep)"
ps -eo pid,ppid,etime,args | grep -F 'archivo-diagnostico-073542' | grep -v grep | sed 's/^/  /'
echo "  ficheros $(ls ~/cf-prep-20261028/archivo-diagnostico-073542/live-*.pcap | wc -l); rc=$(cat ~/cf-prep-20261028/archivo-diagnostico-073542.rc 2>/dev/null)"
