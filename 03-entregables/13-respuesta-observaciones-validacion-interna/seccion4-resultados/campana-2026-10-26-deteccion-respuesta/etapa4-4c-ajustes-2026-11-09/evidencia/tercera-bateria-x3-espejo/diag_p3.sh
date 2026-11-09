echo "## $(date -u +%FT%TZ)"
python3 - <<'PY'
import json, os, datetime as dt
V = os.path.expanduser("~/cf-e4/4c/vigia/vigia.jsonl")
rs = [json.loads(l) for l in open(V)]
f = lambda e: dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%H:%M:%SZ")
for r in rs[-5:]:
    p = r.get("permiso") or {}
    print(f(r["epoch"]), p.get("estado"), p.get("causas"), "marcas_nuevas", r.get("marcas_nuevas"))
PY
echo "== Kali: último estado del generador"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 kali 'K=/home/adminatacante/cf-e4-4c; tail -n 3 $K/generador.stdout | cut -c1-170; echo "permiso: $(head -c 260 $K/permiso.json)"; tail -n 2 $K/corrida/marcas.jsonl | cut -c1-200; echo "vivo: $(pgrep -fc "[g]enerar_campana.py --config")"' 2>&1
echo "== Sensor1: anillo (ficheros de 5 s)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'ls -l --time-style=+%T /var/lib/ppi-motor-capture 2>/dev/null | tail -4; echo "hora: $(date -u +%T)"; uptime; free -m | head -2; df -h /home | tail -1; echo "motor: $(systemctl is-active ppi-motor) cap: $(systemctl is-active ppi-motor-capture) NR=$(systemctl show -p NRestarts --value ppi-motor-capture)"; tail -n 2 ~/cf-e4/4c/salud/muestras.jsonl | cut -c1-120' 2>&1
