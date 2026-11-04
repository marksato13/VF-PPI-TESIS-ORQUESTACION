set -u
# [Sensor1 m4rk] Control a mitad del ensayo: solo criterios de reversión (no se mira el resultado de descartes para decidir nada).
C=/home/m4rk/cf-e4/cierre4a; PY=/home/m4rk/cyberflow/.venv/bin/python
date -u +%T
systemctl show suricata -p ActiveState -p MainPID -p NRestarts --value | tr '\n' ' '; echo
grep -E 'MemAvailable' /proc/meminfo
awk '{ if (index($0, "2026-11-04 06:16:5") || f) {f=1; print} }' /var/log/suricata/suricata.log | grep -iE 'error|unable|alloc|mmap' | grep -v 'no rules' | tail -n 5 || true
tail -n 120 $C/salud/fino.jsonl | $PY -c '
import json,sys
m=[json.loads(l) for l in sys.stdin]; e=[x.get("eve_bytes") for x in m]
par=0; mx=0
for a,b in zip(e,e[1:]):
    par = par+1 if a==b else 0; mx=max(mx,par)
print("ultimos 120 s: eve parada max", mx, "s; pids", {(x.get("suricata") or {}).get("pid") for x in m}, "mem_min", min(x["mem_disponible_kb"] for x in m), "errores", sum(1 for x in m if x.get("errores")))'
for n in muestrear fino; do echo "$n vivo: $(kill -0 $(cat $C/salud/$n.pid) 2>/dev/null && echo si || echo NO)"; done
