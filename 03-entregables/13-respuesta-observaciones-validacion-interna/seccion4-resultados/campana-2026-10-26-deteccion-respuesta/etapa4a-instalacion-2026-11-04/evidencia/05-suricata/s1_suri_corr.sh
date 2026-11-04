set -u
# Correlación (solo lectura) del intervalo con drops 03:05:39-03:05:47 y de los drops de hoy
echo "--- journal 03:05:15-03:06:15 (todas las unidades)"
journalctl --no-pager --since "2026-11-04 03:05:15" --until "2026-11-04 03:06:15" -o short-iso | cut -c1-220 | head -60
echo "--- muestras del muestreador alrededor"
python3 - <<'EOF'
import json
prev=None
for l in open('/home/m4rk/cf-e4/4a/salud/muestras.jsonl'):
    d=json.loads(l); t=d['utc'][11:19]
    i=d.get('interfaz',{}); s=d.get('suricata',{}); m=d.get('motor',{}); a=d.get('anillo',{})
    if prev and '03:04:30'<=t<='03:07:00':
        dt=d['t']-prev['t']; pi=prev.get('interfaz',{})
        rx=(i.get('rx_packets',0)-pi.get('rx_packets',0))/dt if i.get('ok') and pi.get('ok') else None
        print(t,'rx_pps=%s'%(round(rx) if rx is not None else None),'rx_dropped=',i.get('rx_dropped'),
              'suri=',{k:s.get(k) for k in ('kernel_drops','kernel_packets') if k in s},
              'motor=',{k:m.get(k) for k in list(m)[:6]})
    prev=d
print('claves interfaz:',list(json.loads(l).get('interfaz',{}).keys()))
print('claves suricata:',list(json.loads(l).get('suricata',{}).keys()))
print('claves motor:',list(json.loads(l).get('motor',{}).keys()))
EOF
echo "--- ciclos del motor 03:05-03:07"
python3 - <<'EOF'
import json
L=open('/home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl').read().splitlines()
print('lineas',len(L)); print('ultima',L[-1][:400])
for l in L[-400:]:
    if '03:05' in l or '03:06' in l: print(l[:300])
EOF
echo "--- drops de hoy en stats.log (intervalos con drops)"
python3 - <<'EOF'
import re,datetime
rows=[];cur=None
for line in open('/var/log/suricata/stats.log',errors='replace'):
    m=re.match(r'Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)',line)
    if m:
        mo,d,y,H,M,S=map(int,m.groups()); cur={'t':datetime.datetime(y,mo,d,H,M,S)}; rows.append(cur); continue
    m=re.match(r'(capture\.kernel_packets|capture\.kernel_drops)\s+\|\s+Total\s+\|\s+(\d+)',line)
    if m and cur is not None: cur[m.group(1)]=int(m.group(2))
for a,b in zip(rows,rows[1:]):
    dd=b.get('capture.kernel_drops',0)-a.get('capture.kernel_drops',0)
    if dd>0: print(b['t'],'dp',b.get('capture.kernel_packets',0)-a.get('capture.kernel_packets',0),'dd',dd)
EOF
echo "--- eve.json: estadisticas de drops por dia (eve stats, ultimos gz)"
for f in /var/log/suricata/eve.json.1.gz /var/log/suricata/eve.json.2.gz /var/log/suricata/eve.json.3.gz; do
  echo "$f"; zcat "$f" | grep '"event_type":"stats"' | python3 -c '
import sys,json
prev=None;n=0;out=[]
for l in sys.stdin:
    d=json.loads(l);c=d["stats"].get("capture",{});k=c.get("kernel_drops",0);p=c.get("kernel_packets",0)
    if prev and k>prev[1]: out.append((d["timestamp"][11:19],p-prev[0],k-prev[1]))
    prev=(p,k);n+=1
print(" lecturas",n,"intervalos con drops",len(out),"drops",sum(x[2] for x in out))
for x in sorted(out,key=lambda x:-x[2])[:8]: print("  ",x)'
done
