#!/usr/bin/env bash
# PASO2 c01 — bastion: condiciones de inicio de episodio segun CRITERIOS-DEFINITIVOS (solo lectura).
# NORMAL_FIN = inicio real de T1 (o "ahora" antes de T1); FIN_ANT = fin real del episodio anterior (o 0).
set -u
NORMAL_FIN=1793505059.753; FIN_ANT=1793505862.037
echo "## c01 $(date -u +%FT%T.%3NZ)  kali curl=$(ssh -n kali 'pgrep -c curl') generador=$(ssh -n kali 'pgrep -fc kali_episodio_tecnico')"
ssh sensor1 "NORMAL_FIN=$NORMAL_FIN FIN_ANT=$FIN_ANT bash -s" <<'EOS'
echo "  motor $(systemctl is-active ppi-motor) NR=$(systemctl show -p NRestarts --value ppi-motor) PID=$(systemctl show -p MainPID --value ppi-motor) | captura $(systemctl is-active ppi-motor-capture) | suricata $(systemctl is-active suricata) | archivador: $(cut -c1-60 ~/cf-paso2-20261101T0254Z/archivo-pcap/ESTADO.txt)"
python3 - <<'PY'
import json, os, time, statistics
from datetime import datetime
T_N = datetime.fromisoformat("2026-11-01T03:20:00+00:00").timestamp()
nf = os.environ["NORMAL_FIN"]; NF = time.time() if nf == "ahora" else float(nf)
FA = float(os.environ["FIN_ANT"])
cs = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/_state/ciclos.jsonl")]
norm = [c for c in cs if T_N <= c["inicio_ciclo"] < NF]
pn = sorted(c["ventanas_pendientes"] for c in norm); dn = sorted(c["duracion_s"] for c in norm)
p95 = pn[int(round(0.95 * (len(pn) - 1)))]
u6 = cs[-6:]
m6 = statistics.mean(c["ventanas_pendientes"] for c in u6)
print("  normal [03:20, %s): ciclos=%d dur p50=%.2f max=%.2f >9.5=%d | pendientes p50=%s p95=%s max=%s" % (
    time.strftime("%H:%M:%S", time.gmtime(NF)), len(norm), statistics.median(dn), dn[-1], sum(d > 9.5 for d in dn), pn[len(pn)//2], p95, pn[-1]))
print("  6 ultimos: dur=%s pend=%s media=%.1f" % ([round(c["duracion_s"], 2) for c in u6], [c["ventanas_pendientes"] for c in u6], m6))
desde = time.time() - FA if FA > 0 else None
c1 = all(c["duracion_s"] < 9.5 for c in u6); c2 = m6 <= p95; c3 = desde is None or desde >= 230
print("  ciclos<9.5=%s  pend_media<=p95normal=%s  >=230s desde fin anterior=%s (%s)  => LISTO=%s" % (c1, c2, c3, None if desde is None else round(desde), c1 and c2 and c3))
PY
tail -1 ~/cf-paso2-20261101T0254Z/recursos/muestras.jsonl | python3 -c 'import json,sys;m=json.loads(sys.stdin.read());print("  memavail=%.0f MB rss=%.0f MB swapusado=%.0f MB pswpout=%s" % (m["memavail_kb"]/1024,m["rss_kb"]/1024,(m["swaptotal_kb"]-m["swapfree_kb"])/1024,m["pswpout"]))'
EOS
