set -u
# Cierre de la observación técnica de 60 min (solo lectura salvo detener el muestreador propio)
D=/home/m4rk/cf-e4/4a; S=$D/salud; PY=/home/m4rk/cyberflow/.venv/bin/python
E=/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py
INI=$(cat $D/inicio-observacion.txt)
ahora=$(date -u +%s); ini_s=$(date -u -d "$INI" +%s)
[ $((ahora - ini_s)) -ge 3600 ] || { echo "PARADA: solo $((ahora - ini_s)) s de observación"; exit 1; }
p=$(cat $S/muestrear.pid); kill "$p" && echo "muestreador $p detenido"
FIN=$(date -u +%FT%TZ); echo "$FIN" > $D/fin-observacion.txt
echo "ventana: $INI -> $FIN ($((ahora - ini_s)) s)"
J="journalctl --no-pager -o short-iso-precise --since $INI --until $FIN"
$J -u ppi-motor-capture > $S/journal-captura.txt
$J -u ppi-via-rapida@ens37 > $S/journal-via-rapida.txt
$J -u ppi-motor > $S/journal-motor.txt
$J -u ppi-publicar-feed-v2 > $S/journal-publicador-v2.txt
$J -u suricata > $S/journal-suricata.txt
wc -l $S/journal-*.txt
echo "--- errores en journals"; grep -iEc 'traceback|error|exception' $S/journal-*.txt
$PY -I $E intervalos $S/muestras.jsonl $S/incrementos.jsonl
$PY -I $E clasificar --incrementos $S/incrementos.jsonl --tcpdump-log $S/journal-captura.txt \
   --tcpdump-log $S/journal-via-rapida.txt --desde "$INI" --hasta "$FIN" > $S/clasificacion.json; echo "clasificar rc=$?"
cut -c1-1500 $S/clasificacion.json
echo "--- resumen de muestras"
$PY -I - "$S/muestras.jsonl" <<'EOF'
import json,sys,statistics as st
M=[json.loads(l) for l in open(sys.argv[1])]
def q(v,p): v=sorted(v); return v[min(len(v)-1,int(p*len(v)))] if v else None
gap=[b['t']-a['t'] for a,b in zip(M,M[1:])]
print('muestras',len(M),'hueco max s',round(max(gap),2),'mediana',round(st.median(gap),2))
mo=[m['motor'] for m in M if m.get('motor',{}).get('ok')]
for k in ('duracion_s','ventanas_pendientes','antiguedad_s','retraso_pcap_s'):
    v=[x[k] for x in mo if x.get(k) is not None]; print('motor',k,'p50',q(v,.5),'p95',q(v,.95),'max',max(v) if v else None)
print('motor ok',len(mo),'/',len(M))
vr=[m['via_rapida'] for m in M if isinstance(m.get('via_rapida'),dict)]
print('via_rapida ok',sum(1 for x in vr if x.get('ok')),'/',len(vr),'claves',list(vr[-1].keys()) if vr else None)
for k in ('antiguedad_s',):
    v=[x.get(k) for x in vr if x.get(k) is not None]; print(' via',k,'p95',q(v,.95),'max',max(v) if v else None)
an=[m['anillo'] for m in M if isinstance(m.get('anillo'),dict)]
print('anillo ok',sum(1 for x in an if x.get('ok')),'/',len(an),'claves',list(an[-1].keys()) if an else None)
I=[m['interfaz'] for m in M]; rx=[(b['rx_packets']-a['rx_packets'])/(M[i+1]['t']-M[i]['t']) for i,(a,b) in enumerate(zip(I,I[1:])) if a.get('ok') and b.get('ok')]
print('ens37 rx pps p50',round(q(rx,.5)),'p95',round(q(rx,.95)),'max',round(max(rx)),'rx_missed',I[-1].get('rx_missed_errors')-I[0].get('rx_missed_errors'),'rx_dropped(nic) delta',I[-1]['rx_dropped']-I[0]['rx_dropped'])
su=[m['suricata'] for m in M if m.get('suricata',{}).get('ok')]
print('suricata kernel_drops delta',su[-1]['kernel_drops']-su[0]['kernel_drops'],'packets delta',su[-1]['kernel_packets']-su[0]['kernel_packets'])
print('unidades ultima muestra:',json.dumps(M[-1].get('unidades'))[:600])
EOF
echo "--- ciclos del motor en la ventana"
$PY -I - /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl "$INI" "$FIN" <<'EOF'
import json,sys,datetime as dt,collections
a=dt.datetime.fromisoformat(sys.argv[2].replace('Z','+00:00')).timestamp(); b=dt.datetime.fromisoformat(sys.argv[3].replace('Z','+00:00')).timestamp()
C=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
W=[c for c in C if a<=c.get('fin_ciclo',0)<=b]
d=sorted(c['duracion_s'] for c in W); q=lambda p:d[min(len(d)-1,int(p*len(d)))]
print('ciclos',len(W),'dur p50',q(.5),'p95',q(.95),'max',d[-1],'decididas',sum(c.get('decididas',0) for c in W),'disparos',dict(collections.Counter(c.get('disparo') for c in W)))
f=[c['fin_ciclo'] for c in W]; g=[y-x for x,y in zip(f,f[1:])]; print('separación max entre ciclos s',round(max(g),2))
print('claves',sorted(W[-1].keys()))
EOF
echo "--- decisiones del motor en la ventana"
$PY -I - /home/m4rk/cyberflow/logs/motor_decision.log "$INI" "$FIN" <<'EOF'
import json,sys,collections
import datetime as dt
a,b=[dt.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp() for x in sys.argv[2:4]]
R=[];bad=0
for l in open(sys.argv[1],errors='replace'):
    try: d=json.loads(l)
    except Exception: bad+=1; continue
    t=d.get('logged_at')
    if isinstance(t,(int,float)) and a<=t<=b: R.append(d)
print('registros',len(R),'lineas no JSON (todo el log)',bad)
print('eventos',dict(collections.Counter(d.get('event') for d in R)))
ids=collections.Counter(d.get('decision_id') for d in R if d.get('decision_id'))
print('decision_id duplicados',sum(1 for k,v in ids.items() if v>1))
dec=[d for d in R if 'decision_if' in d]
print('con decision_if',len(dec),'decision_if',dict(collections.Counter(d.get('decision_if') for d in dec)))
print('con auth_failure',sum(1 for d in R if 'auth_failure' in json.dumps(d)))
print('decision (desplegada)',dict(collections.Counter(d.get('decision') for d in R)))
print('ventanas por src_ip',dict(collections.Counter(d.get('src_ip') or d.get('ip') for d in R).most_common(12)))
EOF
echo "--- publicador v2: traza en la ventana"
$PY -I - /home/m4rk/feed-v2/traza.jsonl "$INI" "$FIN" <<'EOF'
import json,sys,collections
import datetime as dt
a,b=[dt.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp() for x in sys.argv[2:4]]
P=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
W=[p for p in P if a<=float(p.get('publicado_en') or 0)<=b]
print('publicaciones',len(W),'eventos',dict(collections.Counter(p.get('evento') for p in W)),'politica',set(p.get('politica') for p in W))
s=[p.get('secuencia') for p in W]; print('secuencia', s[:1], s[-1:], 'monotona', all(y>x for x,y in zip(s,s[1:])))
N=[n for p in W for n in p.get('nuevos',[])]
print('nuevos por tipo',dict(collections.Counter(n.get('tipo') for n in N)),'por accion',dict(collections.Counter(n.get('accion') for n in N)))
c=collections.Counter(n.get('evento_id') for n in N if n.get('tipo')=='nueva'); print('evento_id "nueva" duplicados',sum(1 for v in c.values() if v>1))
for n in N[:5]: print('  ',json.dumps(n)[:300])
EOF
echo "--- señales IF en la ventana"; awk -v a="$INI" -v b="$FIN" 'index($0,"logged_at")' /home/m4rk/feed-v2/senales-if.jsonl | $PY -I -c '
import sys,json,collections
import datetime as dt; a,b=[dt.datetime.fromisoformat(x.replace("Z","+00:00")).timestamp() for x in sys.argv[1:3]]; L=[json.loads(l) for l in sys.stdin]
W=[d for d in L if a<=float(d.get("logged_at") or 0)<=b]
print("senales IF",len(W),"por ip",dict(collections.Counter(d["ip"] for d in W)))' "$INI" "$FIN"
echo "--- señales rápidas: $(wc -l < /home/m4rk/feed-v2/senales-rapidas.jsonl)"
echo "--- procesos que apliquen (no debe haber)"; pgrep -af -- '--enforce|--aplicar' | grep -v pgrep || echo ninguno
echo "--- memoria/reinicios"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata ppi-dashboard; do echo "$u $(systemctl show $u -p ActiveState -p NRestarts -p MemoryCurrent | tr '\n' ' ')"; done
ps -o pid,rss,etime,cmd -C python3,python,tcpdump | cut -c1-140
echo "--- intensidad de perfiles (eve http/flow desde el inicio)"
$PY -I - /var/log/suricata/eve.json "$INI" "$FIN" <<'EOF'
import json,sys,collections
a=sys.argv[2][:19];b=sys.argv[3][:19]
h=collections.Counter();fp=collections.Counter();fb=collections.Counter();fl=collections.Counter()
for l in open(sys.argv[1],errors='replace'):
    t=l[14:33] if l.startswith('{"timestamp":"') else ''
    if not (a<=t<=b): continue
    try: d=json.loads(l)
    except Exception: continue
    s=d.get('src_ip'); e=d.get('event_type')
    if e=='http': h[(s,d.get('dest_ip'))]+=1
    elif e=='flow':
        f=d['flow']; k=(s,d.get('dest_ip'),d.get('app_proto') or d.get('proto')); fl[k]+=1; fp[k]+=f.get('pkts_toserver',0)+f.get('pkts_toclient',0); fb[k]+=f.get('bytes_toserver',0)+f.get('bytes_toclient',0)
mins=(len(range(0)) or 1)
print('http por origen->destino:'); [print('  ',v,k) for k,v in h.most_common(15)]
print('flujos (n, paquetes, MB) por origen->destino/app:')
for k,v in fl.most_common(20): print('  ',v,fp[k],round(fb[k]/1e6,2),k)
EOF
echo "--- verificación final Sensor1"
R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1); bash ~/cf-e4/paquete/deploy/etapa4/sensor1/verificar_sensor1.sh "$R" 2>&1 | tail -40
