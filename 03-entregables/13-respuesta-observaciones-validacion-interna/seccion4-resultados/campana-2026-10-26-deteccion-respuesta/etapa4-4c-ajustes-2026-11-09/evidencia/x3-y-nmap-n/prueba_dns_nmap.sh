echo "## prueba DNS de nmap (solo -sL: resolución, sin sondas al destino) $(date -u +%FT%TZ)"
KA="ssh -n -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
T0=$(date -u +%FT%T)
$KA 'nmap -sL 10.10.30.10 2>&1 | tail -3'
sleep 12
T1=$(date -u +%FT%T)
$KA 'nmap -sL -n 10.10.30.10 2>&1 | tail -3'
sleep 8
T2=$(date -u +%FT%T)
echo "ventanas: sin -n [$T0,$T1]  con -n [$T1,$T2]"
ssh -n -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "python3 - <<PY
import json, collections
A, B, C = '$T0', '$T1', '$T2'
c = {'sin_n': collections.Counter(), 'con_n': collections.Counter()}
for l in open('/var/log/suricata/eve.json', errors='replace'):
    if '10.10.20.30' not in l or '10.10.10.2' not in l: continue
    try: j = json.loads(l)
    except Exception: continue
    t = j.get('timestamp', '')[:19]
    if not (A <= t <= C): continue
    if j.get('src_ip') == '10.10.20.30' and j.get('dest_port') == 53:
        k = 'sin_n' if t < B else 'con_n'
        c[k][(j['dest_ip'], j.get('event_type'))] += 1
for k, v in c.items(): print(k, dict(v) or 'ningún flujo DNS de la Kali')
PY"
