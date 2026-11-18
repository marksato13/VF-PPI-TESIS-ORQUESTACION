import sys, json, collections, datetime
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path(r"C:\Users\markp\desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10")
sys.path.insert(0, str(BASE / "herramientas")); sys.path.insert(0, str(BASE / "instrumentacion")); sys.path.insert(0, str(BASE / "revision-evidencia-b2"))
import lector_pcap as L
W = Path(r"C:\Users\markp\cf-b4"); K, SRV = "10.10.20.30", "10.10.30.10"
mar = [json.loads(l) for l in open(W/"kali/corrida/marcas.jsonl", encoding="utf8") if l.strip()]
ep = lambda s: datetime.datetime.fromisoformat(s).timestamp()
ini = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"]=="inicio"}
fin = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"]=="fin"}
esc = [e for e in ini if e.startswith("escaneo") and e in fin]
syn = collections.defaultdict(lambda: collections.Counter()); rst = collections.Counter(); sa = collections.Counter()
lo, hi = min(ini[e] for e in esc)-5, max(fin[e] for e in esc)+5
for f in sorted((W/"pcap").glob("*.pcap")):
    for ts, s, d, pr, sp, dp, fl, pl, pre in L.paquetes(f):
        if ts < lo or ts > hi or pr != 6: continue
        if s == K and d == SRV and (fl & 2) and not (fl & 16): syn["syn"][int(ts)] += 1
        elif s == SRV and d == K and (fl & 18) == 18: syn["synack"][int(ts)] += 1
        elif s == SRV and d == K and (fl & 4): syn["rst"][int(ts)] += 1
for e in esc:
    t0, t1 = ini[e], fin[e]; n = int(t1-t0)
    def tr(c, a, b): return sum(c[x] for x in range(int(t0)+a, int(t0)+b))
    print(e, "dur", round(t1-t0), "| SYN primeros 2 s:", tr(syn["syn"],0,2), "| 2-10 s:", tr(syn["syn"],2,10), "| 10-30 s:", tr(syn["syn"],10,30), "| 30-60 s:", tr(syn["syn"],30,60), "| ultimos 30 s:", tr(syn["syn"],max(0,n-30),n), "| total SYN:", tr(syn["syn"],0,n), "| SYN-ACK:", tr(syn["synack"],0,n), "| RST srv:", tr(syn["rst"],0,n))