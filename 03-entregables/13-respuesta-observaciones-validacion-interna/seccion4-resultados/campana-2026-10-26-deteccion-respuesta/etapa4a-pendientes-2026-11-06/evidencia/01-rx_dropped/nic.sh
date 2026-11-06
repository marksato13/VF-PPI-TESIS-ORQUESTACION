set -u
# [SENSOR1 m4rk] Solo lecturas (sysfs, ethtool -S, ip -s, /proc). Sin cambiar offloads, driver ni parámetros.
I=ens37; N=${1:-60}
leer() {
  echo "t=$(date +%s.%N)"
  for c in rx_packets rx_dropped rx_missed_errors rx_fifo_errors rx_over_errors rx_errors rx_crc_errors rx_frame_errors rx_length_errors rx_nohandler multicast; do
    printf '%s=%s\n' $c "$(cat /sys/class/net/$I/statistics/$c 2>/dev/null || echo NA)"; done
  ip -s -s -j link show $I | python3 -c 'import json,sys; s=json.load(sys.stdin)[0]["stats64"]["rx"]; print("ip_json_rx=" + json.dumps(s, sort_keys=True))'
  ethtool -S $I | awk '/Rx Queue#/{q=$3} /drv dropped rx total|drop err|drop fcs|rx buf alloc fail|pkts rx OOB|pkts rx err|LRO pkts rx|ucast pkts rx|mcast pkts rx|bcast pkts rx/{gsub(/^ +/,""); print "q" q " " $0}'
  awk '{print "softnet_cpu" NR-1 "_dropped=" strtonum("0x"$2) " time_squeeze=" strtonum("0x"$3)}' /proc/net/softnet_stat
}
echo "### offloads (solo lectura)"; ethtool -k $I | grep -E 'rx-vlan-offload|rx-vlan-filter|generic-receive|large-receive|rx-checksumming|receive-hashing' ; ethtool -l $I 2>/dev/null | tail -5
echo "### taps AF_PACKET en el host"; cat /proc/net/packet | awk 'NR>1{print "proto=" $4 " iface_idx=" $5 " rmem=" $7 " inode=" $9}' | sort | uniq -c
echo "ifindex $I = $(cat /sys/class/net/$I/ifindex)"
echo "### módulos 8021q/llc/stp/bridge cargados:"; lsmod | grep -E '^(8021q|llc|stp|bridge|psnap|p8022) ' || echo "ninguno"
echo "### lectura 1"; leer > /tmp/nic1.txt; cat /tmp/nic1.txt
sleep $N
echo "### lectura 2 (+$N s)"; leer > /tmp/nic2.txt; cat /tmp/nic2.txt
python3 - /tmp/nic1.txt /tmp/nic2.txt <<'EOF'
import sys, re, json
def p(f):
    d = {}
    for l in open(f):
        l = l.strip()
        if l.startswith("ip_json_rx="):
            for k, v in json.loads(l[11:]).items(): d["ip." + k] = v
        elif l.startswith("q"):
            m = re.match(r"(q\d+) (.+): (\d+)$", l)
            if m: d[m.group(1) + "." + m.group(2)] = int(m.group(3))
        elif "=" in l:
            for kv in l.split():
                k, v = kv.split("=", 1)
                try: d[k] = float(v)
                except ValueError: pass
    return d
a, b = p(sys.argv[1]), p(sys.argv[2])
dt = b["t"] - a["t"]
print("### incrementos en %.1f s" % dt)
for k in sorted(b):
    if k == "t" or k not in a: continue
    dv = b[k] - a[k]
    if dv or k in ("rx_dropped", "rx_nohandler", "rx_missed_errors", "rx_fifo_errors"):
        print("%-40s %+12.0f  (%.2f/s)" % (k, dv, dv / dt))
drv = sum(b[k] - a[k] for k in b if k.endswith("drv dropped rx total") and k in a)
print("SUMA drv dropped rx total (driver vmxnet3) = %+.0f ; rx_dropped (sysfs) = %+.0f ; diferencia (núcleo) = %+.0f" % (
    drv, b["rx_dropped"] - a["rx_dropped"], b["rx_dropped"] - a["rx_dropped"] - drv))
EOF
uname -r; modinfo vmxnet3 2>/dev/null | grep -E '^(version|filename|srcversion)'
