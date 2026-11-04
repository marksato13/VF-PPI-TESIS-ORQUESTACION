set -u
. /etc/os-release; echo "$PRETTY_NAME"; tcpdump --version 2>&1 | head -3; dpkg -l tcpdump libcap-ng0 2>/dev/null | tail -2
id tcpdump; getent group tcpdump m4rk
L=~/cyberflow/logs/motor_decision.log
echo "### qué líneas contienen PermissionError (tipos de evento)"
grep 'PermissionError' $L | python3 -c '
import sys,json,collections
c=collections.Counter(); ej={}
for l in sys.stdin:
    try: r=json.loads(l)
    except Exception: c["nojson"]+=1; continue
    e=r.get("event"); c[e]+=1
    if e not in ej: ej[e]=l
print(c)
for e,l in ej.items():
    r=json.loads(l)
    def walk(o,p=""):
        if isinstance(o,dict):
            for k,v in o.items(): walk(v,p+"."+k)
        elif isinstance(o,list):
            for i,v in enumerate(o[:3]): walk(v,p+"[%d]"%i)
        elif isinstance(o,str) and "Permission" in o: print(e,p,o[:200])
    walk(r)
'
echo "### ciclos con ilegibles"
C=~/cyberflow/logs/_state-e4/ciclos.jsonl; ls -l $C; head -c 600 $C; echo
python3 - $C <<'EOF'
import json,sys
n=0; k=set()
for l in open(sys.argv[1]):
    r=json.loads(l); n+=1
    for kk,v in r.items():
        if "ilegib" in kk and v: k.add((kk,str(v)[:200]))
print(n,"ciclos;", sorted(k)[:10])
EOF
grep -l ilegib ~/cyberflow-e4/ec78ca5/scripts/engine/*.py
grep -n -B3 -A12 'ilegib' ~/cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py | head -80
