#!/usr/bin/env bash
# PREFLIGHT 18 — sensor: todas las ALERT registradas entre 07:02 y 07:07 (cualquier IP) para atribuir la entrada
# LIMIT del feed de 07:04:10-07:06:50. Solo lectura.
set -u
echo "## p18  $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
python3 - "$HOME/cyberflow/logs/motor_decision.log" <<'PY'
import sys,json,datetime
for l in open(sys.argv[1]):
    try: r=json.loads(l)
    except Exception: continue
    if r.get("decision")!="PERMIT" and "2026-10-28T07:00"<=r.get("window_end_utc","")<"2026-10-28T07:07":
        print("   ",r["window_end_utc"],"logged",datetime.datetime.utcfromtimestamp(float(r["logged_at"])).strftime("%H:%M:%S"),
              r["entity_ip"],r["decision"],r.get("detector_name"),"score",r.get("score"))
PY
