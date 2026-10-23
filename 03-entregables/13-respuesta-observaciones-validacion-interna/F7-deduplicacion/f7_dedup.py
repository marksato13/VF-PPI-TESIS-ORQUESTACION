#!/usr/bin/env python3
# F7 - Cuantifica la deduplicacion del espejo SPAN con la funcion REAL del extractor
# (deduplicar_espejo) y muestra que el trafico parecido pero legitimo se conserva.
import sys, json, pathlib, collections
sys.path.insert(0, "/home/m4rk/cyberflow/scripts/features")
import extract_multilayer_v2 as v2
import extract_multilayer_v3 as v3
pcaps = [p for p in sys.argv[1:] if pathlib.Path(p).exists()]
res = {}
for pc in pcaps:
    ctx = [c for c in (v3.parse_con_contexto(ts, fr) for ts, fr in v2.iter_pcap_frames(pathlib.Path(pc))) if c is not None]
    kept, n_desc = v3.deduplicar_espejo(ctx)
    # replicar el criterio para obtener los pares y sus diferencias
    guard = {}; pares = []
    orden = sorted(range(len(ctx)), key=lambda i: ctx[i].packet.timestamp)
    for i in orden:
        a = ctx[i]; p = a.packet
        k = (p.protocol, p.src_ip, p.dst_ip, p.src_port, p.dst_port, a.ip_id, p.ip_length, p.tcp_seq, p.icmp_type, p.icmp_id)
        j = guard.get(k)
        if j is not None:
            b = ctx[j]; dt = p.timestamp - b.packet.timestamp; dttl = abs(p.ttl - b.packet.ttl)
            if dt <= 0.005 and dttl <= 1:
                pares.append((b, a, dt, dttl))
                if p.ttl > b.packet.ttl: guard[k] = i
                continue
        guard[k] = i
    # trafico similar legitimo: misma 5-tupla a <=5 ms pero distinto id IP / secuencia (se CONSERVA)
    ult = {}; similares = 0
    for c in sorted(kept, key=lambda q: q.timestamp):
        k5 = (c.protocol, c.src_ip, c.dst_ip, c.src_port, c.dst_port)
        t = ult.get(k5)
        if t is not None and c.timestamp - t <= 0.005: similares += 1
        ult[k5] = c.timestamp
    dist = collections.Counter(d for *_, d in pares)
    ej = {}
    for b, a, dt, dttl in pares:
        key = "dTTL=%d" % dttl
        if key not in ej:
            pb, pa = b.packet, a.packet
            ej[key] = {"proto": pb.protocol, "src": pb.src_ip, "dst": pb.dst_ip, "sport": pb.src_port, "dport": pb.dst_port,
                       "ip_id": b.ip_id, "ip_length": pb.ip_length, "tcp_seq": pb.tcp_seq,
                       "vlan_a": b.vlan, "vlan_b": a.vlan, "ttl_a": pb.ttl, "ttl_b": pa.ttl, "dt_us": round(dt * 1e6, 1)}
    res[pc] = {"tramas_ipv4": len(ctx), "copias_quitadas_funcion": n_desc, "pares_replicados": len(pares),
               "coinciden": n_desc == len(pares), "pct_quitado": round(100 * n_desc / len(ctx), 3) if ctx else 0,
               "dist_dTTL": dict(dist), "dt_max_us": round(max((d for _, _, d, _ in pares), default=0) * 1e6, 1),
               "similares_legitimos_conservados": similares, "ejemplos": ej}
print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
