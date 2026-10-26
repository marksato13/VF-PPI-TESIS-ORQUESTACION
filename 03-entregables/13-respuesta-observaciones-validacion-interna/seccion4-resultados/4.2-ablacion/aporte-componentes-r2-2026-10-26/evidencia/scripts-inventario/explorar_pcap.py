"""Exploracion: lineas de tiempo y efecto de respuesta en los PCAP de la bateria (05-oct)."""
import csv, json, sys, collections
from datetime import datetime, timezone
from pathlib import Path

D = Path(sys.argv[1])
sys.path.insert(0, str(D / "cyberflow/scripts/features"))
import extract_multilayer_v2 as v2  # noqa
import extract_multilayer_v3 as v3  # noqa

KALI, BAST, SRV, DNS = "10.10.20.30", "10.10.10.30", "10.10.30.10", "10.10.10.20"
f = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M:%S.%f")[:-3] if t else "-"
SYN, ACK, RST, FIN = 0x02, 0x10, 0x04, 0x01

for ep in sys.argv[2:]:
    d = D / "piloto" / ep
    ctx = []
    for r in sorted(d.glob("live-*.pcap")):
        for m, tr in v2.iter_pcap_frames(r):
            c = v3.parse_con_contexto(m, tr)
            if c is not None:
                ctx.append(c)
    pk, dups = v3.deduplicar_espejo(ctx)
    pk.sort(key=lambda p: p.timestamp)
    filas = list(csv.DictReader(open(d / "features.csv", encoding="utf-8")))
    cs = {round(datetime.fromisoformat(x["window_end_utc"]).timestamp() - float(x["history_coverage_s"]), 3)
          for x in filas if float(x["history_coverage_s"]) < 60}.pop()
    t0 = cs + 25
    print(f"\n===== {ep}  T0(Tsf)={f(t0)}  pcap {f(pk[0].timestamp)}..{f(pk[-1].timestamp)}  dups={dups}")
    # sesiones SSH que tocan a la Kali o al sensor
    ses = collections.OrderedDict()
    for p in pk:
        if p.protocol == 6 and 22 in (p.src_port, p.dst_port) and (KALI in (p.src_ip, p.dst_ip) or "10.10.60.11" in (p.src_ip, p.dst_ip)):
            k = tuple(sorted(((p.src_ip, p.src_port), (p.dst_ip, p.dst_port))))
            s = ses.setdefault(k, {"syn": None, "fin": [], "rst": None, "first": p.timestamp, "last": p.timestamp, "n": 0})
            s["n"] += 1; s["last"] = p.timestamp
            if p.tcp_flags & SYN and not p.tcp_flags & ACK: s["syn"] = s["syn"] or p.timestamp
            if p.tcp_flags & FIN: s["fin"].append((p.src_ip, p.timestamp))
            if p.tcp_flags & RST: s["rst"] = p.timestamp
    for k, s in ses.items():
        fins = ", ".join(f"{ip}@{f(t)}" for ip, t in s["fin"][:3])
        print(f"  ssh {k[0][0]}:{k[0][1]}<->{k[1][0]}:{k[1][1]} n={s['n']} syn={f(s['syn'])} first={f(s['first'])} last={f(s['last'])} fin=[{fins}]")
    # efecto: por segundo, salientes de la Kali al objetivo y respuestas
    tgt = DNS if ep.startswith("e3") else SRV
    seg = collections.defaultdict(lambda: [0, 0, 0, 0])   # kali->tgt, syn kali, synack tgt, rst tgt / dns resp
    for p in pk:
        s = int(p.timestamp)
        if p.src_ip == KALI and p.dst_ip == tgt:
            seg[s][0] += 1
            if p.protocol == 6 and p.tcp_flags & SYN and not p.tcp_flags & ACK: seg[s][1] += 1
        elif p.src_ip == tgt and p.dst_ip == KALI:
            if p.protocol == 6 and p.tcp_flags & SYN and p.tcp_flags & ACK: seg[s][2] += 1
            elif p.protocol == 6 and p.tcp_flags & RST: seg[s][3] += 1
            elif p.protocol == 17: seg[s][3] += 1
    ks = sorted(seg)
    if ks:
        print(f"  ataque Kali->{tgt}: primero {f(min(p.timestamp for p in pk if p.src_ip==KALI and p.dst_ip==tgt))} ultimo {f(max(p.timestamp for p in pk if p.src_ip==KALI and p.dst_ip==tgt))}")
        # resumen por bloques de 5 s
        b = collections.defaultdict(lambda: [0, 0, 0, 0])
        for s in ks:
            for i in range(4): b[(s // 5) * 5][i] += seg[s][i]
        print("  bloque(5s)  kali->tgt  SYN  SYNACK  RST/respDNS")
        for s in sorted(b):
            print(f"  {f(s)[:8]}  {b[s][0]:6d} {b[s][1]:5d} {b[s][2]:6d} {b[s][3]:6d}")
