#!/usr/bin/env bash
# PREFLIGHT 13 — sensor: (a) contador ens37 vs paquetes en el PCAP en la MISMA ventana (90 s); (b) visibilidad de las
# transacciones benignas del preflight en el PCAP archivado, EVE, decisiones del motor. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
R=/var/lib/ppi-motor-capture; DST=$(cat "$HOME/cf-preflight-20261028/ULTIMA_PRUEBA"); L=$HOME/cyberflow/logs/motor_decision.log
echo "## p13  inicio=$(ts)"
echo "## (a) ens37 /proc/net/dev vs PCAP en la misma ventana"
read -r b1 p1 d1 < <(awk '/ens37/{print $2,$3,$5}' /proc/net/dev); t1=$(date +%s.%N)
sleep 90
read -r b2 p2 d2 < <(awk '/ens37/{print $2,$3,$5}' /proc/net/dev); t2=$(date +%s.%N)
sleep 35   # que se cierren los ficheros que cubren [t1,t2]
n=0; for f in $(ls -1 $R/live-*.pcap | sort); do
  c=$(tcpdump -ttnr "$f" 2>/dev/null | awk -v a="$t1" -v b="$t2" '$1>=a && $1<=b' | wc -l); n=$((n+c)); done
echo "  ventana [$t1, $t2] ($(awk -v a=$t1 -v b=$t2 'BEGIN{printf "%.1f",b-a}') s)"
echo "  ens37 rx_packets +$((p2-p1))  rx_dropped +$((d2-d1))  rx_bytes +$((b2-b1))"
echo "  paquetes en el PCAP con marca en la ventana: $n"
awk -v n=$n -v p=$((p2-p1)) -v d=$((d2-d1)) 'BEGIN{printf "  PCAP/rx_packets = %.4f ; PCAP/(rx_packets+rx_dropped) = %.4f\n", n/p, n/(p+d)}'
echo "  (rx_dropped de la NIC incluye tramas que la pila descarta despues de la copia a los sockets de captura, p.ej."
echo "   protocolo desconocido; no es por si solo perdida de tcpdump. Los descartes del propio tcpdump siguen NO MEDIDOS.)"
echo "## (b1) PCAP archivado ($DST): transacciones del preflight"
F=$(ls -1 "$DST"/live-*.pcap | sort)
cnt(){ local flt="$1"; local s=0 c; for f in $F; do c=$(tcpdump -nr "$f" "$flt" 2>/dev/null | wc -l); s=$((s+c)); done; echo $s; }
echo "  Kali->DC udp/53:            $(cnt 'src host 10.10.20.30 and dst host 10.10.10.20 and udp port 53') paquetes"
echo "  Kali<->srv tcp/80:          $(cnt 'host 10.10.20.30 and host 10.10.30.10 and tcp port 80') paquetes"
echo "  Kali<->srv tcp/18081:       $(cnt 'host 10.10.20.30 and host 10.10.30.10 and tcp port 18081') paquetes"
echo "  respuestas HTTP en :18081 (cuerpo legible):"; for f in $F; do tcpdump -nAr "$f" 'src host 10.10.30.10 and tcp src port 18081' 2>/dev/null | grep -oE 'HTTP/1\.[01] [0-9]{3}'; done | sort | uniq -c | sed 's/^/    /'
echo "  nombres pfmarca/preflight en DNS del PCAP:"; for f in $F; do tcpdump -nr "$f" 'udp port 53 and host 10.10.20.30' 2>/dev/null | grep -oE '(pfmarca[0-9]|preflight)-[0-9]+\.lab-ppi'; done | sort -u | sed 's/^/    /'
echo "  perfiles legitimos (06:58:39-06:58:46) por origen:"
for i in 21 22 23 24 25 26; do echo "    10.10.20.$i: $(cnt "src host 10.10.20.$i") paquetes"; done
echo "## (b2) EVE"
grep -E 'pfmarca[12]-|preflight-[0-9]+\.lab-ppi' /var/log/suricata/eve.json | python3 -c '
import sys,json
for l in sys.stdin:
  e=json.loads(l); d=e.get("dns",{})
  q=d.get("rrname") or (d.get("queries") or [{}])[0].get("rrname"); print("   ",e["timestamp"],e["event_type"],e.get("src_ip"),"->",e.get("dest_ip"),q,d.get("type"),d.get("rcode",""))' | head -8
grep '"event_type":"http"' /var/log/suricata/eve.json | grep 'cf-preflight-2026-10-28' | python3 -c '
import sys,json
for l in sys.stdin:
  e=json.loads(l); h=e["http"]; print("   ",e["timestamp"],e["src_ip"],"->",e["dest_ip"]+":"+str(e["dest_port"]),h.get("http_method"),h.get("url"),h.get("status"))'
echo "  eventos de los perfiles .21-.26 en EVE desde 06:58:
"; grep -E '"src_ip":"10\.10\.20\.2[1-6]"' /var/log/suricata/eve.json | python3 -c '
import sys,json,collections
c=collections.Counter()
for l in sys.stdin:
  e=json.loads(l)
  if e["timestamp"]>="2026-10-28T06:58": c[(e["src_ip"],e["event_type"])]+=1
for k,v in sorted(c.items()): print("    %s %-6s %d"%(k[0],k[1],v))'
echo "## (b3) decisiones del motor (entidades del preflight, desde 06:58)"
python3 - "$L" <<'PY'
import sys,json,collections
c=collections.defaultdict(lambda: collections.Counter())
for l in open(sys.argv[1]):
    try: r=json.loads(l)
    except Exception: continue
    ip=r.get("entity_ip","")
    if (ip=="10.10.20.30" or ip.startswith("10.10.20.2")) and r.get("window_end_utc","")>="2026-10-28T06:58":
        c[ip][(r.get("decision"),r.get("detector_name"))]+=1
for ip in sorted(c): print("   ",ip,dict(c[ip]))
PY
echo "## fin=$(ts)"
