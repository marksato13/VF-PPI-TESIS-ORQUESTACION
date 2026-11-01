#!/usr/bin/env bash
# PREFLIGHT 10b — relojes desde el BASTION (referencia chrony). Por host: UNA sesion SSH persistente (subproceso con
# tuberias) y 9 muestras; desfase = t_remoto - (t0+t1)/2, incertidumbre = (t1-t0)/2. Se informa la muestra de menor
# RTT y la mediana. Ademas, estado NTP propio de cada host. Tolerancia de la preparacion: |desfase| <= 1 s.
set -u
echo "## p10b relojes  inicio=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)  referencia=bastion $(hostname)"
chronyc tracking 2>&1 | grep -E 'Reference|System time|RMS offset|Root dispersion' | sed 's/^/  /'
python3 - <<'PY'
import subprocess, time, statistics, os
H = [("sensor","cyberflow-to-sensor","m4rk@10.10.60.11"), ("kali","cyberflow-to-atacante","adminatacante@10.10.20.30"),
     ("srv-dmz","cyberflow-to-srv","adminsrvdmz@10.10.30.10"), ("clientes","cyberflow-to-clientes","adminclientes@10.10.20.20")]
REM = ("python3 -u -c 'import sys,time\nfor l in sys.stdin:\n print(repr(time.time()),flush=True)'; "
       "echo NTP $(timedatectl show -p NTPSynchronized --value) $(timedatectl show-timesync -p ServerName --value 2>/dev/null)")
for n, k, u in H:
    t = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    p = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-i", os.path.expanduser("~/.ssh/" + k), u, REM],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    try:
        p.stdin.write("x\n"); p.stdin.flush(); p.stdout.readline()          # calentamiento (descarta conexion)
        m = []
        for i in range(9):
            t0 = time.time(); p.stdin.write("x\n"); p.stdin.flush(); r = float(p.stdout.readline()); t1 = time.time()
            m.append((r - (t0 + t1) / 2, (t1 - t0) / 2, t1 - t0)); time.sleep(0.15)
        p.stdin.close(); ntp = p.stdout.read().strip(); p.wait(timeout=10)
        b = min(m, key=lambda x: x[2]); med = statistics.median(x[0] for x in m)
        print("  [%s] %-8s mejor desfase=%+.4f s inc=+-%.4f s | mediana=%+.4f s | rango=[%+.4f,%+.4f] | |desfase|<=1 s: %s | %s"
              % (t, n, b[0], b[1], med, min(x[0] for x in m), max(x[0] for x in m), "SI" if abs(b[0]) + b[1] <= 1 else "NO", ntp))
    except Exception as e:
        print("  [%s] %-8s NO SE PUDO MEDIR: %s %s" % (t, n, e, p.stderr.read()[:200] if p.stderr else ""))
        p.kill()
PY
echo "## fin=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
