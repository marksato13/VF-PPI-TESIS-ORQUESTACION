S="ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
for i in 1 2 3; do
  echo "$(date -u +%T)Z ens37 rx_packets: $($S 'cat /sys/class/net/ens37/statistics/rx_packets') | permiso: $(tail -1 ~/cf-e4/4c/vigia/vigia.jsonl | python3 -c "import sys,json; r=json.load(sys.stdin); p=r['permiso']; print(p['estado'], ';'.join(p['causas'])[:80])")"
  [ $i -lt 3 ] && sleep 30
done
echo "-- ping de control para ver si el espejo lo recibe (bastión -> srv-dmz, 20 paquetes):"
A=$($S 'cat /sys/class/net/ens37/statistics/rx_packets'); ping -c 20 -i 0.2 10.10.30.10 >/dev/null 2>&1; B=$($S 'cat /sys/class/net/ens37/statistics/rx_packets'); echo "paquetes nuevos en ens37 durante el ping: $((B-A)) (si el espejo funcionara, >= 40)"
