import sys, pickle
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path(r"C:\Users\markp\desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10")
sys.path.insert(0, str(BASE / "herramientas")); sys.path.insert(0, str(BASE / "instrumentacion")); sys.path.insert(0, str(BASE / "revision-evidencia-b2"))
import lector_pcap as L
K, SRV, DC1 = "10.10.20.30", "10.10.30.10", "10.10.10.20"
for tramo, pdir in (("b3", r"C:\Users\markp\cf-b3\pcap"), ("b4", r"C:\Users\markp\cf-b4\pcap")):
    out = {"srv": [], "dc1": []}; n = 0
    for f in sorted(Path(pdir).glob("*.pcap")):
        n += 1
        for ts, s, d, pr, sp, dp, fl, pl, pre in L.paquetes(f):
            if s == K and d == SRV: out["srv"].append((ts, pr, dp, fl))
            elif s == K and d == DC1: out["dc1"].append((ts, pr, dp, fl))
    for k in out: out[k].sort()
    pickle.dump(out, open(r"C:\Users\markp\cf-b4\span-origen-%s.pkl" % tramo, "wb"))
    print(tramo, n, "pcap", len(out["srv"]), "->srv", len(out["dc1"]), "->dc1", flush=True)