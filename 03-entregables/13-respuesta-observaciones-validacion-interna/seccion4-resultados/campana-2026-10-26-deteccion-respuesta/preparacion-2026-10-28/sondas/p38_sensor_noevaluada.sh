#!/usr/bin/env bash
# PREP 38 — sensor: examina las ventanas no evaluadas del candidato: su registro, las observaciones EVE de esa entidad
# alrededor de window_end (que crean la ventana) y la decision de produccion. Solo lectura.
set -u
C=$HOME/cf-prep-20261028/candidato/logs/motor_decision.log
echo "## p38 $(date -u +%FT%T.%3NZ)  no evaluadas: $(grep -c '"ventana_no_evaluada"' $C)"
grep '"ventana_no_evaluada"' $C | head -5 | cut -c1-600 | sed 's/^/  /'
python3 - <<'PY'
import json, os
from datetime import datetime, timezone
C = os.path.expanduser("~/cf-prep-20261028/candidato/logs/motor_decision.log")
P = os.path.expanduser("~/cyberflow/logs/motor_decision.log")
ne = [json.loads(l) for l in open(C) if '"ventana_no_evaluada"' in l][:5]
f = lambda iso: datetime.fromisoformat(iso).timestamp()
for r in ne:
    ip, we = r["entity_ip"], f(r["window_end_utc"])
    print(f"## {ip} {r['window_end_utc']}  pendiente_desde-we={r['pendiente_desde']-we:+.1f}s  inicio_ciclo-we={r['inicio_ciclo']-we:+.1f}s  marca_pcap-we={r['marca_pcap']-we:+.1f}s")
    for l in open(P):
        if f'"{ip}"' in l and r["window_end_utc"] in l and '"decision"' in l:
            d = json.loads(l); print(f"   prod: pk10={d['packet_count_10s']} det={d.get('detector_name')} logged_at-we={d['logged_at']-we:+.1f}s")
    n = 0
    with open("/var/log/suricata/eve.json", errors="replace") as fh:
        fh.seek(max(0, os.path.getsize("/var/log/suricata/eve.json") - 120_000_000))
        for l in fh:
            if f'"{ip}"' not in l:
                continue
            try:
                e = json.loads(l)
            except ValueError:
                continue
            t = datetime.fromisoformat(e["timestamp"].replace("+0000", "+00:00")).timestamp()
            if we - 15 <= t <= we + 5:
                n += 1
                if n <= 6:
                    print(f"   eve t-we={t-we:+.2f} {e.get('event_type')} {e.get('src_ip')}->{e.get('dest_ip')}:{e.get('dest_port')} flow_start={e.get('flow',{}).get('start','')}")
    print(f"   eventos EVE de la entidad en [we-15, we+5]: {n}")
PY
