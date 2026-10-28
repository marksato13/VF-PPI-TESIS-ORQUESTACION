#!/usr/bin/env bash
# PREP 45 — sensor: separa la comparacion post-despliegue por version del motor de produccion (registro con
# marca_pcap = motor corregido, sin ella = anterior) y resume cada parte; registros alrededor del reinicio. Solo lectura.
set -u
echo "## p45 $(date -u +%FT%T.%3NZ)"
python3 - <<'PY'
import json, os, collections
D = os.path.expanduser("~/cf-prep-20261028/diagnostico/comparacion-motores-postdespliegue-0840-0853.jsonl")
L = os.path.expanduser("~/cyberflow/logs/motor_decision.log")
ver, lat, eventos = {}, collections.defaultdict(list), collections.Counter()
from datetime import datetime
for l in open(L):
    if '"window_end_utc"' not in l or '"2026-10-28T08:' not in l:
        continue
    r = json.loads(l)
    if not ("2026-10-28T08:40:00" <= r["window_end_utc"][:19] <= "2026-10-28T08:53:00"):
        continue
    eventos[r["event"]] += 1
    if r["event"] != "decision":
        print("   no evaluada:", json.dumps(r)[:300]); continue
    v = "corregido" if "marca_pcap" in r else "anterior"
    ver[(r["entity_ip"], r["window_end_utc"])] = v
    lat[v].append(r["logged_at"] - datetime.fromisoformat(r["window_end_utc"]).timestamp())
print("   eventos en el log de produccion para ventanas 08:40-08:53:", dict(eventos))
c = collections.defaultdict(collections.Counter)
for l in open(D):
    f = json.loads(l); k = tuple(f["clave"])
    if "prod" not in f:
        continue
    v = ver.get(k, "?"); pk, pc = f["prod"][0], f["completo_pk10"]
    c[v]["decisiones"] += 1
    if pc is None: c[v]["sin_referencia"] += 1
    elif pk == 0 and pc > 0: c[v]["cero_con_trafico"] += 1
    elif pk != pc: c[v]["conteo_distinto"] += 1
    else: c[v]["pk10_igual_completo"] += 1
for v in c:
    xs = sorted(lat[v]); q = lambda p: xs[min(len(xs)-1, int(p*len(xs)))]
    print(f"   motor {v}: {dict(c[v])}  logged_at-we mediana {q(.5):.1f} p95 {q(.95):.1f} max {xs[-1]:.1f} s")
PY
echo "## candidato: parada tras esta verificacion"
