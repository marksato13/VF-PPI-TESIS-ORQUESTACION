#!/usr/bin/env bash
# PASO2 — sensor: muestreo de recursos cada 5 s en JSONL (CPU y RSS del motor, memoria, swap, carga, PSI,
# contadores de ens37 y del anillo). Solo lectura. Se para con kill del PID guardado en recursos/muestreo.pid.
set -u
ID=20261101T0721Z; R=$HOME/cf-3b-$ID/recursos; mkdir -p "$R"; O=$R/muestras.jsonl
echo $$ > "$R/muestreo.pid"
HZ=$(getconf CLK_TCK)
while :; do
  P=$(systemctl show -p MainPID --value ppi-motor)
  read -r ut st < <(awk '{print $14, $15}' /proc/$P/stat 2>/dev/null || echo "0 0")
  rss=$(awk '/VmRSS/{print $2}' /proc/$P/status 2>/dev/null); hwm=$(awk '/VmHWM/{print $2}' /proc/$P/status 2>/dev/null)
  ma=$(awk '/MemAvailable/{print $2}' /proc/meminfo); sf=$(awk '/SwapFree/{print $2}' /proc/meminfo); stt=$(awk '/SwapTotal/{print $2}' /proc/meminfo)
  pin=$(awk '/pswpin/{print $2}' /proc/vmstat); pout=$(awk '/pswpout/{print $2}' /proc/vmstat)
  read -r l1 l5 l15 _ < /proc/loadavg
  cpu=$(awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8, $5+$6}' /proc/stat)
  psi=$(awk '/^some/{print $2}' /proc/pressure/memory | cut -d= -f2)
  rx=$(awk '/ens37/{print $3, $5}' /proc/net/dev)
  printf '{"t":%s,"pid":%s,"utime":%s,"stime":%s,"hz":%s,"rss_kb":%s,"hwm_kb":%s,"memavail_kb":%s,"swapfree_kb":%s,"swaptotal_kb":%s,"pswpin":%s,"pswpout":%s,"load1":%s,"cpu_total_idle":"%s","psi_mem_some10":%s,"ens37_rx_drop":"%s","anillo":%s}\n' \
    "$(date +%s.%N)" "${P:-0}" "${ut:-0}" "${st:-0}" "$HZ" "${rss:-0}" "${hwm:-0}" "$ma" "$sf" "$stt" "$pin" "$pout" "$l1" "$cpu" "${psi:-0}" "$rx" \
    "$(ls /var/lib/ppi-motor-capture/ 2>/dev/null | wc -l)" >> "$O"
  sleep 5
done
