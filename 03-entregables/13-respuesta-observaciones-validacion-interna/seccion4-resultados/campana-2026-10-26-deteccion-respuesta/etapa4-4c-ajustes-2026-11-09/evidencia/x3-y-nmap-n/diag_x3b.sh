echo "## $(date -u +%FT%TZ)"
echo "== comando completo del escaneo y ventana"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali 'K=/home/adminatacante/cf-e4-4c; grep "escaneo_breve-r4" $K/corrida/marcas.jsonl | python3 -c "
import sys,json
for l in sys.stdin:
    j=json.loads(l); print(j[\"evento\"], j.get(\"comando\"), j.get(\"reloj\",{}).get(\"pared_utc\"))
"; echo "vivo ahora: $(pgrep -fc "[g]enerar_campana.py --config")"; tail -n 3 $K/generador.stdout | cut -c1-160; echo "rc: $(cat $K/generador.rc 2>/dev/null)"' 2>&1 | cut -c1-400
echo "== Sensor1: flujos DNS de la Kali (EVE) a 10.10.10.21 vs 10.10.10.20 entre 12:44 y 12:51Z"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import json, collections
c = collections.Counter(); ejem = {}
for l in open("/var/log/suricata/eve.json", errors="replace"):
    if "10.10.20.30" not in l or "10.10.10.2" not in l: continue
    try: j = json.loads(l)
    except Exception: continue
    t = j.get("timestamp", "")[:19]
    if not ("2026-11-09T12:44" <= t <= "2026-11-09T12:51:00"): continue
    if j.get("src_ip") == "10.10.20.30" and j.get("dest_ip", "").startswith("10.10.10.2") and j.get("dest_port") == 53:
        k = (j["dest_ip"], j.get("event_type"), j.get("proto"))
        c[k] += 1; ejem.setdefault(k, t)
for k, v in sorted(c.items()): print(k, v, "primer evento", ejem[k])
PY'
