#!/usr/bin/env bash
# PREP 35 — sensor: actividad real de los perfiles .21-.26 (EVE ultimos 10 min, decisiones del motor, paquetes en el
# ultimo PCAP archivado), archivador, espacio, captura y Suricata. Solo lectura.
set -u
echo "## p35  $(date -u +%FT%T.%3NZ)"
A=$HOME/cf-prep-20261028/archivo-diagnostico-073542
python3 - "$A" <<'PY'
import json, sys, time, collections, glob, os
from datetime import datetime
lim = time.time() - 600
ev = collections.defaultdict(collections.Counter)
with open("/var/log/suricata/eve.json", encoding="utf-8", errors="replace") as fh:
    fh.seek(max(0, os.path.getsize("/var/log/suricata/eve.json") - 300_000_000))
    for l in fh:
        if '"src_ip":"10.10.20.2' not in l and '"dest_ip":"10.10.20.2' not in l:
            continue
        try:
            e = json.loads(l)
        except ValueError:
            continue
        t = datetime.fromisoformat(e["timestamp"].replace("+0000", "+00:00")).timestamp()
        if t < lim:
            continue
        for ip in (e.get("src_ip"), e.get("dest_ip")):
            if ip and ip.startswith("10.10.20.2") and len(ip) == 11:
                ev[ip][e.get("event_type")] += 1
print("## EVE ultimos 10 min por IP de perfil (event_type: n)")
for ip in [f"10.10.20.2{i}" for i in range(1, 7)]:
    print(f"   {ip}: {dict(ev[ip].most_common(6))}")
dec = collections.Counter(); pk = collections.Counter()
with open(os.path.expanduser("~/cyberflow/logs/motor_decision.log"), encoding="utf-8") as fh:
    fh.seek(max(0, os.path.getsize(fh.name) - 40_000_000))
    for l in fh:
        if '"event": "decision"' not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if float(r["logged_at"]) >= lim and r["entity_ip"].startswith("10.10.20.2") and len(r["entity_ip"]) == 11:
            dec[r["entity_ip"]] += 1; pk[r["entity_ip"]] += int(r["packet_count_10s"])
print("## motor produccion ultimos 10 min: decisiones / suma pk10 por IP")
for ip in [f"10.10.20.2{i}" for i in range(1, 7)]:
    print(f"   {ip}: decisiones {dec[ip]}  pk10 total {pk[ip]}")
PY
echo "## archivador: $(ls $A/live-*.pcap 2>/dev/null | wc -l) ficheros, $(du -sh $A | cut -f1); proceso vivo: $(pgrep -f 'archivo-diagnostico-073542' >/dev/null && echo SI || echo NO)"
echo "## espacio"; df -h / /var/lib/ppi-motor-capture /var/log/suricata 2>/dev/null | sed 's/^/   /' | sort -u
echo "## servicios: ppi-motor $(systemctl is-active ppi-motor) NR=$(systemctl show -p NRestarts --value ppi-motor) | ppi-motor-capture $(systemctl is-active ppi-motor-capture) NR=$(systemctl show -p NRestarts --value ppi-motor-capture) | suricata $(systemctl is-active suricata) | ppi-dashboard $(systemctl is-active ppi-dashboard)"
echo "## eve.json: $(stat -c '%s bytes mtime %y' /var/log/suricata/eve.json)"
echo "## candidato: vivo=$(kill -0 $(cat $HOME/cf-prep-20261028/candidato/motor.pid) 2>/dev/null && echo SI || echo NO) lineas=$(wc -l < $HOME/cf-prep-20261028/candidato/logs/motor_decision.log) errores=$(grep -ciE 'error|traceback' $HOME/cf-prep-20261028/candidato/motor.out)"
echo "## fin $(date -u +%FT%T.%3NZ)"
