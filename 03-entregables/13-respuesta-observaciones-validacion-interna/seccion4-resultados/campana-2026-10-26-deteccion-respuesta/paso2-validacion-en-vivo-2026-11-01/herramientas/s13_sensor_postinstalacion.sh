#!/usr/bin/env bash
# PASO2 s13 — sensor: comprobaciones posteriores a la instalacion (solo lectura).
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; C=$HOME/cyberflow/logs/_state/ciclos.jsonl; LOG=$HOME/cyberflow/logs/motor_decision.log
T0=$(cat $B/reinicio.t)
echo "## s13 $(date -u +%FT%T.%3NZ)  (reinicio hace $(python3 -c "import time;print(round(time.time()-$T0))") s)"
for u in ppi-motor ppi-motor-capture suricata ppi-dashboard; do echo "  $u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u)"; done
echo "  publicador: $(sudo -n journalctl --no-pager -u ppi-publicar-feed.service --since '-3 min' -o cat | grep -F '{"block"' | tail -1)"
echo "  feed generado hace $(python3 -c "import json,time;print(round(time.time()-float(json.load(open('$HOME/feed/feed.json'))['generado'])))") s"
echo "  journal motor desde reinicio (Traceback/Error): $(sudo -n journalctl --no-pager -u ppi-motor --since "@${T0%.*}" | grep -ciE 'traceback|error|exception')"
echo "  eve.json crece: $(stat -c %s /var/log/suricata/eve.json) ; mtime $(stat -c %y /var/log/suricata/eve.json)"
echo "  archivador: $(cat $B/archivo-pcap/ESTADO.txt)"
echo "  eve_window.jsonl (ya no se escribe): $(stat -c %y $HOME/cyberflow/logs/_state/eve_window.jsonl)"
python3 - "$C" "$LOG" "$T0" <<'PY'
import json, sys, collections, statistics
C, LOG, T0 = sys.argv[1], sys.argv[2], float(sys.argv[3])
cs = [json.loads(x) for x in open(C)]
d = [c["duracion_s"] for c in cs]
print("  ciclos: %d  p50=%.2f  max=%.2f  >9.5 s: %d" % (len(d), statistics.median(d), max(d), sum(x > 9.5 for x in d)))
print("  claves de un ciclo:", sorted(cs[-1]))
regs = [json.loads(x) for x in open(LOG) if x.strip()]
k = collections.Counter((r["entity_ip"], r["window_end_utc"]) for r in regs if r.get("event") in ("decision", "ventana_no_evaluada"))
print("  registros vigentes: %d  claves duplicadas: %d" % (len(regs), sum(n - 1 for n in k.values() if n > 1)))
nuevos = [r for r in regs if r.get("logged_at", 0) >= T0 and r.get("event") in ("decision", "ventana_no_evaluada")]
print("  tras reinicio: %d registros; con decidido_en: %d; decidido_en>logged_at: %d" % (len(nuevos), sum("decidido_en" in r for r in nuevos), sum(r.get("decidido_en", 0) > r["logged_at"] for r in nuevos)))
ent = collections.Counter(r["entity_ip"] for r in nuevos)
print("  entidades tras reinicio:", dict(sorted(ent.items())))
print("  decisiones:", dict(collections.Counter((r.get("decision"), r.get("heuristico")) for r in nuevos if r.get("event") == "decision")))
PY
echo "## EVE: transacciones de preparacion (agente cf-preparacion-paso2)"
tail -c 30000000 /var/log/suricata/eve.json | grep -F 'cf-preparacion-paso2' | python3 -c '
import sys,json
for l in sys.stdin:
    e=json.loads(l); h=e.get("http",{}); print("  ",e.get("timestamp"),e.get("event_type"),e.get("src_ip"),"->",e.get("dest_ip"),e.get("dest_port"),h.get("url"),h.get("status"))'
echo "## fin $(date -u +%FT%T.%3NZ)"
