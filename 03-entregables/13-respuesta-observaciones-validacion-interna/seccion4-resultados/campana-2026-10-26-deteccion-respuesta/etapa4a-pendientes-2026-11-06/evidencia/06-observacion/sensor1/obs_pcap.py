#!/usr/bin/env python3
"""[SENSOR1 m4rk] O2/O3 de la observación fija P4 (ventana 04:50:00Z–05:50:00Z del 2026-11-06). SOLO LECTURA.

El anillo guarda ~17 min, así que cada fichero se lee en cuanto está CERRADO (ya existe uno más nuevo) y antes de
que el anillo lo borre. Por fichero: cabecera global pcap, todos los registros completos (cabecera de 16 bytes +
incl_len), primer y último instante. Una línea JSON por fichero en pcap.jsonl. No escribe en el anillo.
"""
import json
import os
import struct
import sys
import time

D = "/var/lib/ppi-motor-capture"
O = os.path.expanduser("~/cf-e4p/observacion-p4-20261106T0450Z")
FIN = 1793945490  # 2026-11-06 05:51:30Z
os.makedirs(O, exist_ok=True)


def leer(p):
    r = {"fichero": os.path.basename(p)}
    try:
        with open(p, "rb") as f:
            b = f.read()
    except OSError as e:
        r["error"] = f"lectura: {e}"
        return r
    r["bytes"] = len(b)
    if len(b) < 24:
        r["error"] = "cabecera global incompleta"
        return r
    magic = b[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        e = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        e = ">"
    else:
        r["error"] = "magic desconocido"
        return r
    div = 1e9 if magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d") else 1e6
    i, n, t0, t1 = 24, 0, None, None
    while i < len(b):
        if i + 16 > len(b):
            r["error"] = f"cabecera de registro incompleta en {i}"
            break
        s, us, incl, _orig = struct.unpack(e + "IIII", b[i:i + 16])
        if i + 16 + incl > len(b):
            r["error"] = f"registro incompleto en {i}"
            break
        t = s + us / div
        t0 = t if t0 is None else t0
        t1 = t
        n += 1
        i += 16 + incl
    r.update(registros=n, primero=t0, ultimo=t1)
    return r


vistos = set()
salida = os.path.join(O, "pcap.jsonl")
if os.path.exists(salida):
    with open(salida) as f:
        vistos = {json.loads(l)["fichero"] for l in f if l.strip()}
while time.time() <= FIN + 30:
    fs = sorted(x for x in os.listdir(D) if x.startswith("live-") and x.endswith(".pcap"))
    with open(salida, "a") as out:
        for x in fs[:-1]:            # el último sigue abierto
            if x in vistos:
                continue
            r = leer(os.path.join(D, x))
            r["leido_en"] = time.time()
            out.write(json.dumps(r) + "\n")
            vistos.add(x)
    time.sleep(30)
print("fin", time.time(), file=sys.stderr)

