"""SYN por segundo del origen de ensayo al destino del escaneo breve (PCAP archivado del 3B)."""
import collections, struct, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, "scripts/engine")
from trocear_pcap import leer_paquetes
d = Path(sys.argv[1]); t0, t1 = float(sys.argv[2]), float(sys.argv[3])
src, dst = bytes([10,10,20,30]), bytes([10,10,30,10])
syn = collections.Counter(); puertos = collections.defaultdict(set); otros = collections.Counter()
for f in sorted(d.glob("live-*.pcap")):
    stamp = dt.datetime.strptime(f.stem[5:], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
    if stamp > t1 + 30 or stamp < t0 - 60: continue
    cab, it = leer_paquetes(f)
    for t, raw in it:
        if not t0 <= t <= t1: continue
        p = raw[16:]
        if p[12:14] == b"\x81\x00": p = p[4:]
        if p[12:14] != b"\x08\x00": continue
        ip = p[14:]; ihl = (ip[0] & 15) * 4
        if ip[12:16] != src or ip[16:20] != dst: continue
        if ip[9] != 6: otros[int(t)] += 1; continue
        tcp = ip[ihl:]; fl = tcp[13]; dport = struct.unpack(">H", tcp[2:4])[0]
        if fl & 0x02 and not fl & 0x10:
            syn[int(t)] += 1; puertos[int(t)].add(dport)
acum = 0
for s in range(int(t0), int(t1) + 1):
    acum += syn[s]
    print(dt.datetime.fromtimestamp(s, dt.timezone.utc).strftime("%H:%M:%S"), "syn", syn[s], "puertos", len(puertos[s]), "acum", acum, "no_tcp", otros[s])
