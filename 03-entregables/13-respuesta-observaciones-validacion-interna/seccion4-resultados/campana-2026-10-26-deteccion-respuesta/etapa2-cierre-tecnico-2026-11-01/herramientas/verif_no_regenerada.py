"""Comprueba si una ventana no evaluada (ventana_no_regenerada) tiene contenido de la entidad en su
propio horizonte [A-230, ...] y en el horizonte de una ancla anterior [A0-230, ...].
Uso (desde el repo): python verif_no_regenerada.py archivo-pcap entidad A_iso A0_iso [excl_protocolos]"""
import datetime as dt, ipaddress, sys
from pathlib import Path
sys.path.insert(0, "scripts/features")
import extract_multilayer_v3 as v3
v2 = v3.v2
d, ent, A, A0 = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
ts = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
A, A0 = ts(A), ts(A0)
red = ipaddress.ip_network("10.10.0.0/16")
ctx = []
for f in sorted(d.glob("live-*.pcap")):
    st = dt.datetime.strptime(f.stem[5:], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
    if st < A0 - 260 or st > A + 20:
        continue
    for m, tr in v2.iter_pcap_frames(f):
        c = v3.parse_con_contexto(m, tr)
        if c is not None and c.packet.protocol not in (112, 240):
            ctx.append(c)
ctx.sort(key=lambda c: c.packet.timestamp)
for nombre, corte in (("propio", A - 230), ("ancla_anterior", A0 - 230)):
    sel = [c for c in ctx if corte <= c.packet.timestamp <= A + 0.005]
    paq, _ = v3.deduplicar_espejo(sel)
    obs = v2.attribute_packets(paq, red)
    e60 = [o for o in obs if o.entity_ip == ent and A - 60 < o.timestamp <= A]
    e30 = [o for o in e60 if o.timestamp > A - 30]
    otros = {}
    for o in obs:
        if A - 60 < o.timestamp <= A and o.entity_ip != ent and o.peer_ip == ent:
            otros[o.entity_ip] = otros.get(o.entity_ip, 0) + 1
    print(nombre, "corte", round(A - corte), "s: obs de", ent, "en (A-60,A]:", len(e60), "en (A-30,A]:", len(e30),
          "| paquetes de/hacia", ent, "atribuidos a otros:", otros)
