set -u
# Lectura (no modifica nada): incrementos de kernel_drops de Suricata desde el inicio de la observación
date -u +%FT%TZ
ls -l --time-style=+%FT%T /var/log/suricata/ | head -20
python3 - <<'EOF'
import re,datetime
ini=datetime.datetime(2026,11,4,2,19,45)
rows=[];cur=None
with open('/var/log/suricata/stats.log',errors='replace') as f:
    for line in f:
        m=re.match(r'Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)',line)
        if m:
            mo,d,y,H,M,S=map(int,m.groups()); cur={'t':datetime.datetime(y,mo,d,H,M,S)}; rows.append(cur); continue
        m=re.match(r'(capture\.kernel_packets|capture\.kernel_drops|decoder\.pkts|tcp\.reassembly_gap|flow\.memuse|tcp\.memuse|detect\.alert)\s+\|\s+Total\s+\|\s+(\d+)',line)
        if m and cur is not None: cur[m.group(1)]=int(m.group(2))
print('lecturas stats.log:',len(rows),'primera',rows[0]['t'] if rows else None,'ultima',rows[-1]['t'] if rows else None)
# zona horaria de stats.log: hora local del sensor
import time; print('TZ local offset s:',-time.timezone, time.tzname)
off=datetime.timedelta(seconds=-time.timezone)
w=[r for r in rows if r['t']-off>=ini]
print('lecturas en la ventana:',len(w))
tot_p=tot_d=0;nz=[]
for a,b in zip(w,w[1:]):
    if 'capture.kernel_packets' not in a or 'capture.kernel_packets' not in b: continue
    dp=b['capture.kernel_packets']-a['capture.kernel_packets']; dd=b.get('capture.kernel_drops',0)-a.get('capture.kernel_drops',0)
    if dp<0: print('REINICIO contador en',b['t']); continue
    tot_p+=dp; tot_d+=dd
    if dd>0: nz.append((str(b['t']),dp,dd,round((b['t']-a['t']).total_seconds())))
print('paquetes',tot_p,'drops',tot_d,'tasa',(tot_d/tot_p if tot_p else None))
print('intervalos con drops:',len(nz))
for x in nz[:60]: print('  ',x)
if w: print('ultimo:',{k:v for k,v in w[-1].items()})
EOF
echo "--- suricata unidad / hilos"
systemctl show suricata -p ActiveEnterTimestamp -p NRestarts -p MemoryCurrent
ps -L -o tid,pcpu,comm -p $(pidof suricata) | sort -k2 -nr | head -15
grep -nE '^\s*(af-packet|  - interface|    threads|    cluster-type|    ring-size|    block-size|    use-mmap|    tpacket-v3|max-pending-packets|runmode)' /etc/suricata/suricata.yaml | head -30
echo "--- logrotate suricata"; cat /etc/logrotate.d/suricata 2>/dev/null; grep -h suricata /var/lib/logrotate/status 2>/dev/null
nproc; uptime; free -m; df -h /var/log | tail -1
