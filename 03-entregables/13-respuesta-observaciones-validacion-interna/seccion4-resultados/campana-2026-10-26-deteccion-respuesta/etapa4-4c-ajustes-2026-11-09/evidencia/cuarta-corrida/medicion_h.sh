ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
F=~/espejo-1s-h-20261109.log
if [ -e $F ]; then echo "ya existe $F"; tail -1 $F; else
nohup setsid sh -c "i=0; while [ \$i -lt 2400 ]; do echo \"\$(date -u +%T) \$(cat /sys/class/net/ens37/statistics/rx_packets) \$(cat /sys/class/net/ens37/statistics/rx_dropped)\"; i=\$((i+1)); sleep 1; done" > $F 2>&1 < /dev/null &
sleep 2; echo "medición H iniciada $(date -u +%T)Z (2400 s)"; fi'

