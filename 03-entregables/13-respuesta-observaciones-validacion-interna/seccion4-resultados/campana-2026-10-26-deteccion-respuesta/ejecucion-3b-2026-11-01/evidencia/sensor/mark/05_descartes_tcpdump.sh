#!/usr/bin/env bash
# PASO3B mark/05 — lo ejecuta Mark (sudo con contraseña). Mide los descartes del proceso REAL de captura
# (ppi-motor-capture, tcpdump) enviandole SIGUSR1: tcpdump escribe sus estadisticas acumuladas en el journal y SIGUE
# capturando (no se para ni se reinicia). Mismo procedimiento que en la primera campaña A (2026-10-29).
#   [BASTION gadmin] ssh -t sensor1 'bash ~/cf-3b-20261101T0721Z/mark/05_descartes_tcpdump.sh'; echo "rc_ssh=$?"
set -u
B=$HOME/cf-3b-20261101T0721Z; O=$B/copias/descartes-tcpdump.json; J=$B/copias/descartes-tcpdump-journal.txt
P=$(systemctl show -p MainPID --value ppi-motor-capture); DESDE=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor-capture)
echo "## mark/05 $(date -u +%FT%T.%3NZ) tcpdump PID=$P desde $DESDE"
[ "$P" -gt 0 ] || { echo "PARAR: sin PID"; exit 2; }
sudo -v || { echo "NO EJECUTADO: sudo rechazado"; exit 2; }
T0=$(date -u '+%F %T'); M=$(date +%s.%N)
sudo kill -USR1 "$P"; rc=$?; echo "  kill -USR1 rc=$rc"
sleep 3
sudo journalctl --no-pager -u ppi-motor-capture --since "$T0" -o short-iso > "$J"; cat "$J" | sed 's/^/  | /'
python3 - "$J" "$P" "$DESDE" "$M" "$O" <<'PY'
import sys, re, json, subprocess
j, pid, desde, m, o = sys.argv[1:]
t = open(j).read()
g = lambda pat: (lambda x: int(x.group(1)) if x else None)(re.search(r"(\d+) " + pat, t))
d = {"fuente": "journalctl -u ppi-motor-capture tras SIGUSR1 a tcpdump pid %s (ejecutado por Mark con sudo)" % pid,
     "pid": int(pid), "proceso_desde": float(subprocess.check_output(["date", "-d", desde, "+%s"]).decode()),
     "momento": float(m), "packets_captured": g("packets captured"), "packets_received_by_filter": g("packets received by filter"),
     "dropped_by_kernel": g("packets dropped by kernel"),
     "alcance": "contador acumulado del proceso tcpdump desde %s; no cubre perdidas aguas arriba (switch/SPAN)" % desde}
json.dump(d, open(o, "w"), indent=1); print(json.dumps(d, indent=1))
sys.exit(0 if d["dropped_by_kernel"] is not None else 1)
PY
r=$?; echo "  servicio tras la medicion: $(systemctl is-active ppi-motor-capture) PID=$(systemctl show -p MainPID --value ppi-motor-capture) NR=$(systemctl show -p NRestarts --value ppi-motor-capture)"
sha256sum "$O" "$J"; exit $r
