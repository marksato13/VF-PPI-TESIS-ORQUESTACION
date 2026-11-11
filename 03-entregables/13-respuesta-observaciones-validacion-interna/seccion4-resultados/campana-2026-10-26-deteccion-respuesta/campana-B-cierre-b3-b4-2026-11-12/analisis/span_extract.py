import sys, pickle
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path(r"C:\Users\markp\desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10")
sys.path.insert(0, str(BASE / "herramientas")); sys.path.insert(0, str(BASE / "instrumentacion")); sys.path.insert(0, str(BASE / "revision-evidencia-b2"))
import lector_pcap as L
W = Path(r"C:\Users\markp\cf-b4"); K, SRV = "10.10.20.30", "10.10.30.10"
k2s = []; s2k = []
for f in sorted((W/"pcap").glob("*.pcap")):
    for ts, s, d, pr, sp, dp, fl, pl, pre in L.paquetes(f):
        if s == K and d == SRV: k2s.append((ts, pr, dp, fl))
        elif s == SRV and d == K: s2k.append((ts, pr, sp, fl))
pickle.dump({"k2s": k2s, "s2k": s2k}, open(W/"span-kali-srv.pkl", "wb"))
print(len(k2s), len(s2k))