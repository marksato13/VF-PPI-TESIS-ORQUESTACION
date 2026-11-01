#!/usr/bin/env bash
# PASO2 m01 — bastion: vigilancia (solo lectura) del sensor y de la Kali; evalua las condiciones para iniciar
# un episodio: >=230 s desde el fin del anterior (lo comprueba quien llama), 6 ultimos ciclos < 9,5 s,
# ventanas_pendientes sin crecer y ningun curl en la Kali.
set -u
echo "## m01 $(date -u +%FT%T.%3NZ)"
echo "  kali curl=$(ssh -n kali 'pgrep -c curl')  generador=$(ssh -n kali 'pgrep -fc kali_episodio_tecnico')"
ssh sensor1 'bash -s' <<'EOS'
B=$HOME/cf-paso2-20261101T0254Z
echo "  motor $(systemctl is-active ppi-motor) NR=$(systemctl show -p NRestarts --value ppi-motor) | captura $(systemctl is-active ppi-motor-capture) | suricata $(systemctl is-active suricata)"
echo "  archivador: $(cat $B/archivo-pcap/ESTADO.txt)"
python3 - <<'PY'
import json, time, statistics
from datetime import datetime
C = "/home/m4rk/cyberflow/logs/_state/ciclos.jsonl"
cs = [json.loads(x) for x in open(C).readlines()[-40:]]
ult = cs[-6:]
print("  ultimos 6 ciclos: dur=%s  pend=%s" % ([round(c["duracion_s"], 2) for c in ult], [c["ventanas_pendientes"] for c in ult]))
p12 = [c["ventanas_pendientes"] for c in cs[-12:]]
print("  pendientes 12 ciclos: %s  | dur max 40 ciclos=%.2f  | hace %.0f s del ultimo ciclo" % (p12, max(c["duracion_s"] for c in cs), time.time() - cs[-1]["fin_ciclo"]))
ok = all(c["duracion_s"] < 9.5 for c in ult) and p12[-1] <= max(p12[:6])
LOG = "/home/m4rk/cyberflow/logs/motor_decision.log"
with open(LOG, "rb") as f:
    f.seek(0, 2); f.seek(max(0, f.tell() - 3_000_000)); lines = f.read().splitlines()[1:]
regs = [json.loads(x) for x in lines if b'"decidido_en"' in x]
now = time.time()
rec = [r for r in regs if r["decidido_en"] > now - 60]
lag = sorted(r["decidido_en"] - datetime.fromisoformat(r["window_end_utc"]).timestamp() for r in rec)
if lag:
    print("  retraso decidido_en-window_end (60 s): n=%d p50=%.1f max=%.1f" % (len(lag), lag[len(lag)//2], lag[-1]))
k = [r for r in regs if r.get("entity_ip") == "10.10.20.30" and r["decidido_en"] > now - 600]
print("  10.10.20.30 en 10 min: %d registros, %s" % (len(k), sorted({(r.get("decision"), (r.get("heuristico") or {}).get("tipo") if isinstance(r.get("heuristico"), dict) else r.get("heuristico")) for r in k}, key=str)))
print("  LISTO_PARA_EPISODIO(ciclos y pendientes)=%s" % ok)
PY
tail -1 $B/recursos/muestras.jsonl | python3 -c 'import json,sys;m=json.loads(sys.stdin.read());print("  rss=%.0f MB hwm=%.0f MB memavail=%.0f MB swapusado=%.0f MB pswpout=%s load1=%s" % (m["rss_kb"]/1024,m["hwm_kb"]/1024,m["memavail_kb"]/1024,(m["swaptotal_kb"]-m["swapfree_kb"])/1024,m["pswpout"],m["load1"]))'
EOS
