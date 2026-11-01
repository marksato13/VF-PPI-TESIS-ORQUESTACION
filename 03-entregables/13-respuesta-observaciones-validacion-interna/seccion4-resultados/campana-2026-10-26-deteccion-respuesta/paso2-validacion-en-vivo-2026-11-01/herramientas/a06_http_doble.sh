#!/usr/bin/env bash
# Solo lectura: por que el EVE muestra ~2 transacciones HTTP por intento del generador (T1).
B=$HOME/cf-paso2-20261101T0254Z
python3 - $B/copias/eve-segmento.json <<'PY'
import json, sys, collections
from datetime import datetime
ini, fin = 1793505059.754, 1793505149.044 + 3
def ep(s): return datetime.strptime(s[:26] + s[26:].replace(":", ""), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
http = []
flows = collections.Counter()
for l in open(sys.argv[1], errors="replace"):
    if '"10.10.20.30"' not in l: continue
    try: e = json.loads(l)
    except Exception: continue
    if e.get("src_ip") != "10.10.20.30" or e.get("dest_ip") != "10.10.30.10": continue
    t = ep(e["timestamp"])
    if not (ini <= t <= fin): continue
    if e.get("event_type") == "http": http.append(e)
    if e.get("event_type") == "flow": flows[e.get("dest_port")] += 1
print("eventos http:", len(http), " flow por puerto destino:", dict(flows))
k1 = collections.Counter((e["src_port"], e.get("tx_id"), e["http"].get("url")) for e in http)
print("claves (src_port,tx_id,url):", len(k1), " con >1 evento:", sum(1 for v in k1.values() if v > 1))
print("distribucion eventos por clave:", collections.Counter(k1.values()))
print("url:", collections.Counter(e["http"].get("url") for e in http).most_common(4))
print("tx_id:", collections.Counter(e.get("tx_id") for e in http).most_common(4))
print("metodo:", collections.Counter(e["http"].get("http_method") for e in http).most_common(3))
print("user-agent:", collections.Counter(e["http"].get("http_user_agent") for e in http).most_common(3))
print("in_iface:", collections.Counter(e.get("in_iface") for e in http).most_common(3), " vlan:", collections.Counter(str(e.get("vlan")) for e in http).most_common(3))
fl = collections.Counter(e.get("flow_id") for e in http)
print("flow_id distintos:", len(fl), " eventos por flow_id:", collections.Counter(fl.values()))
sp = collections.Counter(e["src_port"] for e in http)
print("src_port distintos:", len(sp), " eventos por src_port:", collections.Counter(sp.values()).most_common(5))
PY
