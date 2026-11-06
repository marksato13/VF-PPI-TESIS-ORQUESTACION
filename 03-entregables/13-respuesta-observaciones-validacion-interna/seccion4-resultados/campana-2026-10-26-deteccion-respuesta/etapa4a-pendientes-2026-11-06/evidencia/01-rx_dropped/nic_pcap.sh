set -u
# [SENSOR1 m4rk] Solo lecturas: rx_dropped antes/después de ~70 s y análisis de los PCAP del anillo ya escritos en
# ese intervalo (tipos de trama). No captura nada nuevo, no cambia la interfaz.
I=ens37; C=/var/lib/ppi-motor-capture
r0=$(cat /sys/class/net/$I/statistics/rx_dropped); o0=$(ip -s -s -j link show $I | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["stats64"]["rx"]["otherhost"])'); t0=$(date +%s)
sleep 70
r1=$(cat /sys/class/net/$I/statistics/rx_dropped); o1=$(ip -s -s -j link show $I | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["stats64"]["rx"]["otherhost"])'); t1=$(date +%s)
echo "rx_dropped +$((r1-r0)) otherhost +$((o1-o0)) en $((t1-t0)) s (t0=$t0 t1=$t1)"
ls -l $C | head -3
python3 - $C $t0 $t1 $((r1-r0)) <<'EOF'
import os, sys, struct, datetime as dt, collections
d, t0, t1, drop = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
fich = []
for n in sorted(os.listdir(d)):
    if not n.startswith("live-"): continue
    ini = dt.datetime.strptime(n[5:19], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
    if t0 + 5 <= ini and ini + 5 <= t1 - 5: fich.append((ini, n))
cnt = collections.Counter(); tot = 0; tmin = tmax = None
for ini, n in fich:
    try:
        b = open(os.path.join(d, n), "rb").read()
    except OSError as e:
        print("no legible", n, e.__class__.__name__); continue
    mag = struct.unpack("<I", b[:4])[0]
    e = "<" if mag in (0xa1b2c3d4, 0xa1b23c4d) else ">"
    lt = struct.unpack(e + "I", b[20:24])[0]
    p = 24
    while p + 16 <= len(b):
        ts, tu, incl, orig = struct.unpack(e + "IIII", b[p:p + 16]); p += 16
        pk = b[p:p + incl]; p += incl
        if len(pk) < 14 or lt != 1: continue
        tot += 1
        tmin = ts if tmin is None else min(tmin, ts); tmax = ts if tmax is None else max(tmax, ts)
        et = struct.unpack(">H", pk[12:14])[0]
        if et in (0x8100, 0x88a8) and len(pk) >= 18:
            vid = struct.unpack(">H", pk[14:16])[0] & 0xfff
            inner = struct.unpack(">H", pk[16:18])[0]
            cnt[("vlan%d" % vid, "802.3/LLC" if inner <= 1500 else "%04x" % inner)] += 1
        else:
            cnt[("sin_vlan", "802.3/LLC" if et <= 1500 else "%04x" % et)] += 1
dur = len(fich) * 5
print("ficheros analizados:", len(fich), "(%d s)" % dur, "tramas:", tot)
for k, v in cnt.most_common(25):
    print("%-10s %-10s %8d  %.2f/s" % (k[0], k[1], v, v / dur if dur else 0))
manej = {"0800", "0806", "86dd", "88cc"}
sin = sum(v for (vl, t), v in cnt.items() if vl != "sin_vlan" and t not in manej)
print("VLAN con VID!=0 y ethertype interno sin manejador en este host (no IPv4/ARP/IPv6/LLDP): %.2f/s" % (sin / dur if dur else 0))
print("rx_dropped del mismo intervalo: %.2f/s" % (drop / (t1 - t0)))
EOF
