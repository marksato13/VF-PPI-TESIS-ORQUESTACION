#!/usr/bin/env bash
# PASO2 s00 — bastion: alcance de todos los hosts por alias y relojes (mismo metodo que p34 de la preparacion).
# Solo lectura.
set -u
echo "## s00 bastion $(hostname) $(date -u +%FT%T.%3NZ)"
for h in sensor1 kali srvdmz clientes admin sensor2 suricata; do
  o=$(ssh -n -o BatchMode=yes -o ConnectTimeout=6 $h 'echo "$(hostname) $(whoami) up=$(uptime -p)"' 2>&1); echo "  $h rc=$? $o"
done
echo "## servidor protegido desde el bastion"
curl -s -o /dev/null -m 5 -w '  http://10.10.30.10/ %{http_code} %{time_total}s\n' http://10.10.30.10/
curl -sk -o /dev/null -m 5 -w '  https://10.10.30.10/ %{http_code} %{time_total}s\n' https://10.10.30.10/
curl -sk -o /dev/null -m 5 -w '  panel https://10.10.60.11:8788/ %{http_code}\n' https://10.10.60.11:8788/
echo "## relojes (referencia: bastion)"
chronyc tracking 2>&1 | grep -E 'Reference|System time|Leap' | sed 's/^/  /'
python3 - <<'PY'
import subprocess, time, statistics
REM = ("python3 -u -c 'import sys,time\nfor l in sys.stdin:\n print(repr(time.time()),flush=True)'; "
       "echo NTP $(timedatectl show -p NTPSynchronized --value) TZ=$(timedatectl show -p Timezone --value)")
for n in ("sensor1", "kali", "srvdmz", "clientes"):
    p = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", n, REM],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    try:
        p.stdin.write("x\n"); p.stdin.flush(); p.stdout.readline()
        m = []
        for i in range(9):
            t0 = time.time(); p.stdin.write("x\n"); p.stdin.flush(); r = float(p.stdout.readline()); t1 = time.time()
            m.append((r - (t0 + t1) / 2, (t1 - t0) / 2, t1 - t0)); time.sleep(0.15)
        p.stdin.close(); ntp = p.stdout.read().strip(); p.wait(timeout=10)
        b = min(m, key=lambda x: x[2]); med = statistics.median(x[0] for x in m)
        print("  %-8s mejor=%+.4f s inc=+-%.4f s mediana=%+.4f s  |d|+inc<=1s: %s  %s"
              % (n, b[0], b[1], med, "SI" if abs(b[0]) + b[1] <= 1 else "NO", ntp))
    except Exception as e:
        print("  %-8s NO SE PUDO MEDIR: %s" % (n, e)); p.kill()
PY
echo "## fin $(date -u +%FT%T.%3NZ)"
