#!/usr/bin/env bash
# PASO3A s04 — sensor (solo lectura): telemetria de las peticiones de preparacion de b11 (05:27:00-05:27:02 UTC)
set -u
B=$HOME/cf-paso3a-20261101T0523Z; mkdir -p $B/preparacion-auth
echo "## s04 $(date -u +%FT%T.%3NZ)"
sudo -n grep 'cf-preparacion-paso3a-20261101T0523Z' /var/log/suricata/eve.json > $B/preparacion-auth/eve-http-preparacion.jsonl
python3 - $B/preparacion-auth/eve-http-preparacion.jsonl <<'PY'
import json, sys
for l in open(sys.argv[1]):
    e = json.loads(l)
    if e.get("event_type") != "http": continue
    h = e["http"]
    print("  %s vlan=%s %s:%s -> %s:%s %s %s status=%s ua=%s" % (e["timestamp"][11:23], e.get("vlan"), e["src_ip"], e["src_port"],
          e["dest_ip"], e["dest_port"], h.get("http_method"), h.get("url"), h.get("status"), h.get("http_user_agent")))
PY
echo "  eventos http (todas las VLAN): $(grep -c '"event_type":"http"' $B/preparacion-auth/eve-http-preparacion.jsonl)"
echo "## decisiones del motor para 10.10.20.30, ventanas 05:26:50-05:28:30"
grep '"entity_ip": "10.10.20.30"' $HOME/cyberflow/logs/motor_decision.log | python3 -c '
import json, sys
for l in sys.stdin:
    r = json.loads(l)
    w = r.get("window_end_utc", "")
    if not ("2026-11-01T05:26:50" <= w[:19] <= "2026-11-01T05:28:30"): continue
    f = r.get("features") or {}
    ks = [k for k in f if k.startswith("http_")]
    print("  wend=%s dec=%s score=%s heur=%s pk10=%s escrito=+%.1fs" % (w[11:19], r.get("decision"), r.get("score"), (r.get("heuristico") or {}).get("heuristico"), r.get("packet_count_10s"), float(r["logged_at"]) - __import__("datetime").datetime.fromisoformat(w.replace("Z","+00:00")).timestamp()))
    print("     ", {k: f[k] for k in ks} if ks else ("claves del registro: %s" % sorted(r)[:40]))
' | tee $B/preparacion-auth/decisiones-kali.txt
echo "## fin"
