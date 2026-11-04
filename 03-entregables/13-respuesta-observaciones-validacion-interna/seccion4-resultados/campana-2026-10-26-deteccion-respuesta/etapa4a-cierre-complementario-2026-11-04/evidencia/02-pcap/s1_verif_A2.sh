set -u
PY=/home/m4rk/cyberflow/.venv/bin/python
echo "== por qué se reinició el motor"
systemctl show ppi-motor -p BindsTo -p PartOf -p Requires -p After -p Requisite
systemctl cat ppi-motor | grep -E 'BindsTo|PartOf|Requires|After'
journalctl --no-pager -o short-iso-precise -u ppi-motor --since "2026-11-04 06:12:40" --until "2026-11-04 06:12:55" | head -n 8
echo "== primer fichero del NUEVO tcpdump y rotaciones (validez)"
for f in live-20261104061246.pcap live-20261104061251.pcap live-20261104061256.pcap live-20261104061301.pcap; do
  $PY - /var/lib/ppi-motor-capture/$f <<'EOF'
import struct, sys, os
p = sys.argv[1]
try:
    b = open(p, 'rb').read()
except OSError as e:
    print(os.path.basename(p), "ERROR", e); sys.exit()
n = 0; off = 24
while off + 16 <= len(b):
    off += 16 + struct.unpack('<I', b[off+8:off+12])[0]; n += 1
st = os.stat(p)
print(os.path.basename(p), "legible", "magic", b[:4].hex(), "paquetes", n, "completo", off == len(b), "modo", oct(st.st_mode & 0o777), "gid", st.st_gid)
EOF
done
echo "== el motor procesó esos ficheros (marca_pcap de los ciclos)"
tail -n 300 /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl | $PY -c '
import json,sys,datetime as dt
for l in sys.stdin:
    c=json.loads(l)
    if c.get("inicio_ciclo",0) < 1793772766: continue
    f=lambda x: dt.datetime.fromtimestamp(x, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3] if isinstance(x,(int,float)) else x
    print(c["ciclo_n"], c["disparo"], "inicio", f(c["inicio_ciclo"]), "marca_pcap", f(c.get("marca_pcap")), "dur", c["duracion_s"], "pkts?", c.get("paquetes_nuevos", c.get("pcap_nuevos")))
' | head -n 8
echo "== procesos con --aplicar/--enforce (sin contar el propio grep)"
ps -eo pid,args | grep -E -- '--aplicar|--enforce' | grep -v -E 'grep' || echo ninguno
stat -c '%n %y' /home/m4rk/feed/feed.json
