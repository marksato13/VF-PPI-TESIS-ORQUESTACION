set -u
C=/home/m4rk/cf-e4/cierre4a; EV=$(ls -d $C/sudo-B-* | tail -n 1); PY=/home/m4rk/cyberflow/.venv/bin/python
echo "evidencia $EV"; cat $EV/t-restart-suricata.txt; cat $EV/rc.txt
systemctl show suricata -p ActiveState -p MainPID -p ExecMainStartTimestamp -p NRestarts
grep -nE 'Engine started|threads|ring|AFP|af-packet|rror|nable|alloc' /var/log/suricata/suricata.log | tail -n 15
echo "== hueco EVE alrededor del reinicio"
T=$(cut -d. -f1 $EV/t-restart-suricata.txt)
$PY - $T <<'EOF'
import json, sys, datetime as dt
T = float(sys.argv[1]); ant = None; desp = None
with open("/var/log/suricata/eve.json", "rb") as fh:
    fh.seek(0, 2); fh.seek(max(0, fh.tell() - 80_000_000)); fh.readline()
    for l in fh:
        try: ts = json.loads(l)["timestamp"]
        except Exception: continue
        t = dt.datetime.strptime(ts[:26] + ts[-5:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
        if t < T: ant = t
        elif desp is None and t > T: desp = t
f = lambda x: dt.datetime.fromtimestamp(x, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]
print("ultimo EVE antes", f(ant), "primero despues", f(desp), "hueco_s", round(desp - ant, 3))
EOF
grep -E '^Date:|capture.kernel_(packets|drops)' /var/log/suricata/stats.log | tail -n 3
tail -n 1 $C/salud/fino.jsonl | $PY -c 'import json,sys; d=json.loads(sys.stdin.read()); s=d["suricata"] or {}; print("fino pid", s.get("pid"), "hilos", len(s.get("hilos",{})), "rss_kb", s.get("rss_kb"), "mem", d["mem_disponible_kb"], "err", d.get("errores"))'
for n in muestrear fino; do echo "$n vivo: $(kill -0 $(cat $C/salud/$n.pid) 2>/dev/null && echo si || echo NO)"; done
