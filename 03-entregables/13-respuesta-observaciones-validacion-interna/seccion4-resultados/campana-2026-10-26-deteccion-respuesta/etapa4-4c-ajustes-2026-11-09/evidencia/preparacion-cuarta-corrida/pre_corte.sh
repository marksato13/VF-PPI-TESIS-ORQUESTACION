ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'echo "-- NIC ens37 (vmxnet3): carrier_changes=$(cat /sys/class/net/ens37/carrier_changes) up=$(cat /sys/class/net/ens37/carrier_up_count) down=$(cat /sys/class/net/ens37/carrier_down_count) carrier=$(cat /sys/class/net/ens37/carrier) speed=$(cat /sys/class/net/ens37/speed 2>/dev/null)"
echo "-- kernel/journal sobre ens37/vmxnet3 desde 15:00Z:"; journalctl --no-pager --since "2026-11-09 15:00:00 UTC" 2>/dev/null | grep -iE "vmxnet3|ens37|carrier|link is (up|down)|NIC Link" | tail -6 | cut -c1-200; echo "(fin; si no hay líneas, no hubo eventos de enlace registrados)"
python3 - <<PY
import os, datetime as dt
L = [l.split() for l in open(os.path.expanduser("~/espejo-1s-20261109.log")) if len(l.split()) == 3]
t = [dt.datetime.strptime(a[0], "%H:%M:%S") for a in L]; rx = [int(a[1]) for a in L]; dr = [int(a[2]) for a in L]
r = [(L[i][0], (rx[i]-rx[i-1]) / max(1, (t[i]-t[i-1]).total_seconds()), dr[i]-dr[i-1]) for i in range(1, len(L))]
ini = [i for i in range(len(r)) if r[i][1] < 20 and (i == 0 or r[i-1][1] >= 20)]
print("tráfico en los 6 s previos a cada corte (pkt/s) y rx_dropped en ese lapso:")
for i in ini:
    ant = r[max(0, i-6):i]
    print("  corte", r[i][0], "| previos:", [int(x[1]) for x in ant], "| rx_dropped +%d" % sum(x[2] for x in ant))
pk = sorted(r, key=lambda x: -x[1])[:5]
print("picos más altos:", [(h, int(v)) for h, v, _ in pk])
PY'
