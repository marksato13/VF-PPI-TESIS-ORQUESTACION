#!/usr/bin/env bash
# PREP 44 — sensor: las 5 discrepancias residuales del candidato. Para cada clave: paquetes de la entidad en
# (we-10, we] con su fichero y su marca de tiempo, limites del fichero, marca_pcap/inicio_ciclo del candidato.
# Ademas, orden temporal del anillo: paquetes con timestamp anterior al ultimo paquete del fichero previo. Solo lectura.
set -u
echo "## p44 $(date -u +%FT%T.%3NZ)"
$HOME/cyberflow/.venv/bin/python - <<'PY'
import sys, json, glob, os
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/cyberflow/scripts/features"))
import extract_multilayer_v2 as v2, extract_multilayer_v3 as v3
A = Path.home() / "cf-prep-20261028/archivo-diagnostico-073542"
C = Path.home() / "cf-prep-20261028/candidato/logs/motor_decision.log"
casos = [("10.10.40.10", "2026-10-28T08:16:30+00:00"), ("10.10.40.10", "2026-10-28T08:09:10+00:00"),
         ("10.10.10.57", "2026-10-28T08:22:40+00:00"), ("10.10.10.20", "2026-10-28T08:09:10+00:00"),
         ("10.10.10.20", "2026-10-28T08:22:40+00:00")]
f = v2.parse_eve_timestamp
lo, hi = f("2026-10-28T08:08:30+00:00"), f("2026-10-28T08:23:30+00:00")
fich = sorted(A.glob("live-*.pcap"), key=lambda p: p.name)
info, paq = [], []
prev_max = None; fuera_orden = 0; fuera_max = 0.0
for p in fich:
    ts = [t for t, _ in v2.iter_pcap_frames(p)]
    if not ts or ts[-1] < lo - 60 or ts[0] > hi + 60:
        continue
    noord = sum(1 for a, b in zip(ts, ts[1:]) if b < a)
    if prev_max is not None:
        atras = [prev_max - t for t in ts if t < prev_max]
        fuera_orden += len(atras); fuera_max = max([fuera_max] + atras)
    info.append((p.name, ts[0], ts[-1], len(ts), noord))
    prev_max = max(prev_max or 0, max(ts))
    for t, tr in v2.iter_pcap_frames(p):
        c = v3.parse_con_contexto(t, tr)
        if c is not None:
            paq.append((p.name, c))
print(f"  ficheros {len(info)}; paquetes con ts anterior al maximo de ficheros previos: {fuera_orden} (retraso max {fuera_max:.3f} s); "
      f"desorden dentro de fichero: {sum(x[4] for x in info)}")
reg = {}
for l in open(C):
    if '"window_end_utc"' in l:
        r = json.loads(l); reg[(r["entity_ip"], r["window_end_utc"])] = r
for ip, we_s in casos:
    we = f(we_s); r = reg.get((ip, we_s), {})
    print(f"## {ip} {we_s}: cand pk10={r.get('packet_count_10s')} inicio_ciclo-we={r.get('inicio_ciclo',0)-we:+.2f} marca_pcap-we={r.get('marca_pcap',0)-we:+.2f} pendiente={r.get('pendiente_desde') is not None}")
    sel = [(n, c) for n, c in paq if we - 10 < c.packet.timestamp <= we and ip in (c.packet.src_ip, c.packet.dst_ip)]
    for n, c in sel[:12]:
        fi = next(x for x in info if x[0] == n)
        pk = c.packet
        print(f"   t-we={pk.timestamp-we:+.3f} {pk.src_ip}->{pk.dst_ip} proto={pk.protocol} vlan={c.vlan} fichero={n[5:20]} [{fi[1]-we:+.2f},{fi[2]-we:+.2f}] "
              f"cerrado_antes_de_decidir={'?' if not r else fi[2] <= r.get('marca_pcap', 0)}")
    print(f"   paquetes de la entidad (src o dst) en la ventana, sin deduplicar: {len(sel)}")
PY
