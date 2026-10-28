#!/usr/bin/env bash
# PREFLIGHT 15 — sensor: (1) decisiones del motor vs features para ventanas con trafico benigno del preflight;
# (2) si la Kali llego a entrar al feed tras las ALERT de 07:04 (journal del publicador). Solo lectura.
set -u
L=$HOME/cyberflow/logs/motor_decision.log
echo "## p15  $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
python3 - "$L" <<'PY'
import sys,json,datetime
W={"2026-10-28T06:58:40+00:00","2026-10-28T06:58:50+00:00","2026-10-28T06:59:50+00:00","2026-10-28T07:04:00+00:00","2026-10-28T07:04:50+00:00"}
for l in open(sys.argv[1]):
    try: r=json.loads(l)
    except Exception: continue
    ip=r.get("entity_ip","")
    if r.get("window_end_utc") in W and (ip=="10.10.20.30" or ip in ["10.10.20.%d"%i for i in range(21,27)]):
        we=datetime.datetime.fromisoformat(r["window_end_utc"]).timestamp()
        print("   ",r["window_end_utc"],ip,r.get("decision"),r.get("detector_name"),"pk10",r.get("packet_count_10s"),
              "logged-window_end=%.2fs"%(float(r["logged_at"])-we))
PY
echo "## journal del publicador 07:03-07:08 (menciones de 10.10.20.30 / LIMIT / BLOCK)"
sudo -n journalctl -u cyberflow-publicar-feed.service --since '2026-10-28 07:03:30' --until '2026-10-28 07:08:00' --no-pager 2>&1 | grep -E '10\.10\.20\.30|LIMIT|BLOCK|entradas' | head -n 10 | sed 's/^/    /'
echo "  (unidades del publicador: $(systemctl list-units --all --no-legend '*feed*' | awk '{print $1}' | tr '\n' ' '))"
