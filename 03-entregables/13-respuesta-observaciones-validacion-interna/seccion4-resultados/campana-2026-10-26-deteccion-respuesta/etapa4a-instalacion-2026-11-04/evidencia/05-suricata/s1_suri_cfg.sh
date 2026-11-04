set -u
echo "--- af-packet ens37 (bloque activo)"; sed -n '612,690p' /etc/suricata/suricata.yaml | grep -vE '^\s*#\s' | grep -v '^\s*$'
grep -nE '^max-pending-packets|^runmode|^#?runmode' /etc/suricata/suricata.yaml
echo "--- ethtool ens37"; ethtool -g ens37 2>&1 | head -12; ethtool -l ens37 2>&1 | head -12; ethtool -i ens37 2>&1 | head -3
cat /sys/class/net/ens37/statistics/rx_dropped /sys/class/net/ens37/statistics/rx_missed_errors 2>/dev/null
echo "--- eve 03:05:36-03:05:52: eventos por par (top)"
python3 - <<'EOF'
import json,collections
c=collections.Counter();b=collections.Counter()
with open('/var/log/suricata/eve.json',errors='replace') as f:
    for l in f:
        if '"timestamp":"2026-11-04T03:05:' not in l[:60] and '"timestamp":"2026-11-04T03:06:' not in l[:60]: continue
        try: d=json.loads(l)
        except Exception: continue
        ts=d.get('timestamp','')[11:19]
        if d.get('event_type')=='flow':
            fl=d.get('flow',{}); st=fl.get('start','')[11:19]; en=fl.get('end','')[11:19]
            if st<='03:05:52' and en>='03:05:36':
                k=(d.get('src_ip'),d.get('dest_ip'),d.get('dest_port'),d.get('proto'),d.get('app_proto'))
                b[k]+=fl.get('pkts_toserver',0)+fl.get('pkts_toclient',0)
        elif '03:05:36'<=ts<='03:05:52':
            c[(d.get('event_type'),d.get('src_ip'),d.get('dest_ip'),d.get('dest_port'))]+=1
print('flujos solapados (paquetes totales del flujo):')
for k,v in b.most_common(12): print('  ',v,k)
print('eventos no-flow en el tramo:')
for k,v in c.most_common(12): print('  ',v,k)
EOF
