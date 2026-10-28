#!/usr/bin/env bash
# PREP 43 — sensor: CPU real de produccion y candidato en 60 s (delta de utime+stime de /proc) y duracion de ciclo
# (intervalo entre lotes de registros). Solo lectura.
P=$(systemctl show -p MainPID --value ppi-motor); C=$(cat $HOME/cf-prep-20261028/candidato/motor.pid)
t(){ awk '{print $14+$15}' /proc/$1/stat; }
a=$(t $P); b=$(t $C); sleep 60; a2=$(t $P); b2=$(t $C); hz=$(getconf CLK_TCK)
echo "## p43 $(date -u +%FT%T.%3NZ) CPU ultimos 60 s: produccion $(( (a2-a)*100/hz/60 )) %  candidato $(( (b2-b)*100/hz/60 )) %"
for L in $HOME/cyberflow/logs/motor_decision.log $HOME/cf-prep-20261028/candidato/logs/motor_decision.log; do
python3 - "$L" <<'PY'
import json, sys, time
ts = []
for l in open(sys.argv[1]).readlines()[-3000:]:
    try: r = json.loads(l)
    except ValueError: continue
    if r.get("event") == "decision" and r["logged_at"] > time.time() - 600: ts.append(r["logged_at"])
c = [ts[0]] if ts else []
for x, y in zip(ts, ts[1:]):
    if y - x > 0.3: c.append(y)
d = [y - x for x, y in zip(c, c[1:])]
print(f"  {sys.argv[1].split('/')[-3]}: lotes {len(c)} en 10 min, intervalo medio {sum(d)/max(len(d),1):.1f} s, max {max(d) if d else 0:.1f} s")
PY
done
