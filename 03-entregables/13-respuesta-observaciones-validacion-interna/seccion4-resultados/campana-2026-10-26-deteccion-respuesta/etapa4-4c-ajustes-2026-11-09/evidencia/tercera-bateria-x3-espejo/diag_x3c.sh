echo "## $(date -u +%FT%TZ)"
echo "== bastión: conexiones hacia la Kali (puerto local)"
ss -tnp 2>/dev/null | grep "10.10.20.30" | awk '{print $1, $4, $5}' | head -5
echo "== bastión: ControlMaster/accesos"
tail -n 3 ~/cf-e4/4c/accesos-kali.log | cut -c1-200
echo "== vigía: cancelación (ronda y causa)"
python3 - <<'PY'
import json, os, datetime as dt
V = os.path.expanduser("~/cf-e4/4c/vigia/vigia.jsonl")
rs = [json.loads(l) for l in open(V)]
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%SZ")
for r in rs[-3:]:
    p = r.get("permiso") or {}
    print(f(r["epoch"]), p.get("estado"), p.get("causas"), "marcas_nuevas", r.get("marcas_nuevas"))
PY
echo "== Sensor1: eventos EVE de la Kali hacia el bastión (todos los de hoy desde 15:00Z)"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import json, collections
c = collections.Counter(); ej = {}
for l in open("/var/log/suricata/eve.json", errors="replace"):
    if "10.10.20.30" not in l or "10.10.10.30" not in l: continue
    try: j = json.loads(l)
    except Exception: continue
    t = j.get("timestamp", "")[:19]
    if t < "2026-11-09T15:00:00": continue
    if j.get("src_ip") == "10.10.20.30" and j.get("dest_ip") == "10.10.10.30":
        k = (j.get("event_type"), j.get("proto"), j.get("dest_port"), j.get("src_port"))
        c[k] += 1; ej.setdefault(k, (t, (j.get("flow") or {}).get("start", "")[:19], (j.get("flow") or {}).get("state"), (j.get("flow") or {}).get("reason"), (j.get("flow") or {}).get("pkts_toserver"), (j.get("flow") or {}).get("pkts_toclient")))
for k, v in sorted(c.items(), key=lambda x: str(x)): print(k, v, "primer:", ej[k])
PY'
