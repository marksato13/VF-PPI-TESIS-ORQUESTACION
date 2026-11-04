set -u
# Solo lectura: formato real de las fuentes v2 para el panel
F=/home/m4rk/feed-v2
echo "=== unidad ppi-dashboard"; systemctl cat ppi-dashboard | grep -vE '^\s*#' | grep -v '^$'
systemctl show ppi-dashboard -p ActiveState -p ActiveEnterTimestamp -p MainPID
echo "=== dashboard desplegado"; ls -l /home/m4rk/cyberflow/scripts/engine/dashboard.py; sha256sum /home/m4rk/cyberflow/scripts/engine/dashboard.py; cd /home/m4rk/cyberflow && git log --oneline -1 2>/dev/null; git status --short 2>/dev/null | head
echo "=== feed-v2"; ls -l $F
echo "=== feed.json"; head -c 1500 $F/feed.json; echo
echo "=== estado.json"; head -c 800 $F/estado.json; echo
echo "=== traza (ultimas con nuevos no vacios)"; grep -v '"nuevos": \[\]' $F/traza.jsonl | grep -v '"nuevos":\[\]' | tail -3 | cut -c1-1500
echo "=== traza tipos (todo)"; python3 -c '
import json,collections
c=collections.Counter();ev=collections.Counter();n=0
for l in open("/home/m4rk/feed-v2/traza.jsonl"):
    d=json.loads(l); ev[d.get("evento")]+=1; n+=1
    for x in d.get("nuevos",[]): c[(x.get("tipo"),x.get("accion"),x.get("regla"))]+=1
print(n,dict(ev)); [print(" ",k,v) for k,v in c.most_common(20)]
print("claves",sorted(d.keys()))'
echo "=== senales-if (2)"; tail -2 $F/senales-if.jsonl
echo "=== senales-rapidas (2)"; tail -2 $F/senales-rapidas.jsonl
echo "=== decision del motor con decision_id (1 ALERT y 1 heuristico)"
L=/home/m4rk/cyberflow/logs/motor_decision.log
tail -3000 $L | grep '"decision": "ALERT"' | tail -1 | cut -c1-1800; echo
tail -20000 $L | grep '"heuristico": {' | tail -1 | cut -c1-1800; echo
echo "=== acuses v1 (dir)"; ls -l /home/m4rk/feed/acuses 2>&1 | head
