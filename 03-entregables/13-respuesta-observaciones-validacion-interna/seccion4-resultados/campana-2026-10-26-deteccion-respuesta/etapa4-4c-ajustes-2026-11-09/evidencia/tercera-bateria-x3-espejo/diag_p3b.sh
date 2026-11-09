echo "## $(date -u +%FT%TZ)"
python3 - <<'PY'
import json, os, datetime as dt
V = os.path.expanduser("~/cf-e4/4c/vigia/vigia.jsonl")
rs = [json.loads(l) for l in open(V)]
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%SZ")
for r in rs[-4:]:
    p = r.get("permiso") or {}
    print(f(r["epoch"]), p.get("estado"), p.get("causas"), "marcas_nuevas", r.get("marcas_nuevas"))
PY
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd /var/lib/ppi-motor-capture && ls --time-style=+%T -l | awk "{print \$6, \$5, \$7}" | grep -E "^15:2[5-9]" | awk "{print \$1, \$2, \$3}" | tr "\n" ";" ; echo; echo "-- huecos (>7 s entre inicios) en el anillo actual:"; ls | sed -n "s/^live-\(2026[0-9]*\)\.pcap$/\1/p" | python3 -c "
import sys, datetime as dt
t=[dt.datetime.strptime(l.strip(),\"%Y%m%d%H%M%S\") for l in sys.stdin if l.strip()]
t.sort()
for a,b in zip(t,t[1:]):
    d=(b-a).total_seconds()
    if d>7: print(a.strftime(\"%H:%M:%S\"),\"->\",b.strftime(\"%H:%M:%S\"),int(d),\"s\")
"; echo "-- tcpdump anillo, tráfico de la interfaz (rx_packets) cada 5 s:"; cat /sys/class/net/ens37/statistics/rx_packets; sleep 5; cat /sys/class/net/ens37/statistics/rx_packets' 2>&1
