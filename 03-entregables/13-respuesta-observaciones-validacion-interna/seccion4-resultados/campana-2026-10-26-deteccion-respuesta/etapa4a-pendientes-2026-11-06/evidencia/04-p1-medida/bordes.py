"""Explica 1 193 578 (comparador 4A: muestras DENTRO de la ventana) frente a 1 201 704 (salud_captura 2026-11-06.1:
muestras que ACOTAN la ventana desde fuera). Datos: tests/datos/eve-stats-20261104-0200-0740.jsonl (EVE stats reales)."""
import datetime as dt
import json
import sys

D = dt.datetime(2026, 11, 4, 6, 26, 55, tzinfo=dt.timezone.utc).timestamp()
A = dt.datetime(2026, 11, 4, 7, 26, 55, tzinfo=dt.timezone.utc).timestamp()
m = []
for l in open(sys.argv[1], encoding="utf-8"):
    e = json.loads(l)
    t = dt.datetime.strptime(e["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
    c = e["stats"]["capture"]
    m.append((t, c["kernel_packets"], c["kernel_drops"], e["stats"]["uptime"]))
m.sort()
dentro = [x for x in m if D <= x[0] <= A]
antes = max(x for x in m if x[0] <= D)
despues = min(x for x in m if x[0] >= A)
f = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]
print("ventana            %s – %s  (%.1f s)" % (f(D), f(A), A - D))
print("A) comparador 4A: primera y última muestra DENTRO")
print("   %s  kernel_packets=%d" % (f(dentro[0][0]), dentro[0][1]))
print("   %s  kernel_packets=%d" % (f(dentro[-1][0]), dentro[-1][1]))
print("   muestras %d, cobertura %.1f s, paquetes %d" % (len(dentro), dentro[-1][0] - dentro[0][0], dentro[-1][1] - dentro[0][1]))
print("B) salud_captura .1: muestras que ACOTAN desde fuera (≤ desde, ≥ hasta, a ≤ 10 s)")
print("   %s  kernel_packets=%d  (%.2f s antes de desde)" % (f(antes[0]), antes[1], D - antes[0]))
print("   %s  kernel_packets=%d  (%.2f s después de hasta)" % (f(despues[0]), despues[1], despues[0] - A))
print("   cobertura %.2f s, paquetes %d" % (despues[0] - antes[0], despues[1] - antes[1]))
print("diferencia B−A = %d paquetes = %d (borde inicial %s→%s) + %d (borde final %s→%s)" % (
    (despues[1] - antes[1]) - (dentro[-1][1] - dentro[0][1]),
    dentro[0][1] - antes[1], f(antes[0]), f(dentro[0][0]),
    despues[1] - dentro[-1][1], f(dentro[-1][0]), f(despues[0])))
print("descartes: A %d, B %d" % (dentro[-1][2] - dentro[0][2], despues[2] - antes[2]))
