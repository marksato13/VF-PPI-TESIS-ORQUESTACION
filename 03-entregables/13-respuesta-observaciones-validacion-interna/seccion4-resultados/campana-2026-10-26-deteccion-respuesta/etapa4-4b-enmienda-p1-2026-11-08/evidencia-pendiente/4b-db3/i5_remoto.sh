SC=$HOME/cyberflow-e4/herramientas-20261106/salud_captura.py
echo "== $(date -u +%FT%TZ)"
ls -la /var/log/suricata/eve.json* | awk '{print "   " $5 " " $6 " " $7 " " $8 " " $9}' | head -5
echo "== I5 (solo eve.json actual)"; python3 $SC i5 --eve /var/log/suricata/eve.json > $HOME/.i5a.json 2>&1; echo "rc=$?"
python3 - <<'PY'
import json, os
j = json.load(open(os.path.expanduser("~/.i5a.json")))
print({k: v for k, v in j.items() if not isinstance(v, (list, dict))})
for k, v in j.items():
    if isinstance(v, (list, dict)): print(k, "=", json.dumps(v)[:400])
PY
echo "== I5 (eve.json + rotado)"; ls /var/log/suricata/eve.json.1 >/dev/null 2>&1 && { python3 $SC i5 --eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json.1 > $HOME/.i5b.json 2>&1; echo "rc=$?"; python3 -c "
import json, os
j = json.load(open(os.path.expanduser('~/.i5b.json'))); print({k: v for k, v in j.items() if not isinstance(v, (list, dict))})"; } || echo "no existe eve.json.1"
rm -f $HOME/.i5a.json $HOME/.i5b.json
echo "== eventos stats en la cola de eve.json (cuántos en los últimos 30 min):"
python3 - <<'PY'
import json, time, datetime as dt
n = 0; ult = None; primero = None
with open("/var/log/suricata/eve.json", "rb") as f:
    f.seek(0, 2); s = f.tell(); f.seek(max(0, s - 12_000_000))
    for l in f.read().splitlines()[1:]:
        if b'"event_type":"stats"' in l:
            try: j = json.loads(l)
            except Exception: continue
            t = dt.datetime.fromisoformat(j["timestamp"]).timestamp()
            if t >= time.time() - 1800:
                n += 1; ult = j["timestamp"]; primero = primero or j["timestamp"]
print("stats en 30 min:", n, "primero", primero, "ultimo", ult)
PY
