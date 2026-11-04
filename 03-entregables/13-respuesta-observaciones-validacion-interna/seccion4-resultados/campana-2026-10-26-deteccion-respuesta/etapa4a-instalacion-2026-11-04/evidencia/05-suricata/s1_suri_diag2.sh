set -u
suricata -V 2>&1 | head -1
ethtool -k ens37 2>/dev/null | grep -E '^(generic-receive-offload|large-receive-offload|rx-vlan-offload|rx-checksumming|generic-segmentation)'
ip -s link show ens37 | head -8
grep -iE 'ring|af-packet|AFP|warn|drop|thread|mtu|offload|GRO|LRO' /var/log/suricata/suricata.log 2>/dev/null | tail -25 | cut -c1-220
grep -nE '^max-pending-packets|^ *max-pending-packets|^default-packet-size' /etc/suricata/suricata.yaml
echo "--- carga por CPU (mpstat no) /proc/stat softirq y ksoftirqd"
grep -E 'NET_RX' /proc/softirqs
ps -eo pid,pcpu,comm | grep -E 'ksoftirqd|suricata' | head
echo "--- drops por dia en eve (gz 4..7) con hora"
for f in /var/log/suricata/eve.json.4.gz /var/log/suricata/eve.json.5.gz /var/log/suricata/eve.json.7.gz; do
  zcat "$f" | grep '"event_type":"stats"' | python3 -c '
import sys,json
prev=None;o=[];n=0
for l in sys.stdin:
    d=json.loads(l);c=d["stats"].get("capture",{});k=c.get("kernel_drops",0);p=c.get("kernel_packets",0);n+=1
    if prev and k>prev[1] and p>=prev[0]: o.append((d["timestamp"][:19],p-prev[0],k-prev[1]))
    prev=(p,k)
print(sys.argv[1],"lecturas",n,"intervalos",len(o),"drops",sum(x[2] for x in o),"pps_mediana_en_drop",sorted(x[1]//8 for x in o)[len(o)//2] if o else None)' "$f"
done