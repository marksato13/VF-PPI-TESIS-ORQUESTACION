#!/usr/bin/env python3
"""Lector mínimo de PCAP clásicos (libpcap, Ethernet, IPv4/TCP/UDP) con la biblioteca estándar. Solo lectura. Devuelve por paquete:
(ts, src, dst, proto, sport, dport, flags, plen, prefijo_payload). No reensambla flujos ni interpreta nada más."""
import socket
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def paquetes(ruta):
    d = Path(ruta).read_bytes()
    if len(d) < 24:
        return
    mag = d[:4]
    if mag == b"\xd4\xc3\xb2\xa1":
        e, ns = "<", False
    elif mag == b"\xa1\xb2\xc3\xd4":
        e, ns = ">", False
    elif mag == b"\x4d\x3c\xb2\xa1":
        e, ns = "<", True
    else:
        raise ValueError("no es un pcap clásico: " + str(ruta))
    off, n = 24, len(d)
    hdr = struct.Struct(e + "IIII")
    while off + 16 <= n:
        s, u, cap, _orig = hdr.unpack_from(d, off)
        off += 16
        if off + cap > n:
            break                                                     # fichero truncado: se descarta el último paquete incompleto
        p, off = d[off:off + cap], off + cap
        ts = s + u / (1e9 if ns else 1e6)
        i = 12
        et = (p[i] << 8) | p[i + 1] if len(p) > 13 else 0
        while et in (0x8100, 0x88a8) and len(p) > i + 6:             # etiquetas VLAN
            i += 4
            et = (p[i] << 8) | p[i + 1]
        if et != 0x0800:
            continue
        ip = i + 2
        if len(p) < ip + 20 or (p[ip] >> 4) != 4:
            continue
        ihl, proto = (p[ip] & 15) * 4, p[ip + 9]
        src, dst = socket.inet_ntoa(p[ip + 12:ip + 16]), socket.inet_ntoa(p[ip + 16:ip + 20])
        t = ip + ihl
        if proto == 6 and len(p) >= t + 20:
            sp, dp = struct.unpack_from(">HH", p, t)
            fl, doff = p[t + 13], (p[t + 12] >> 4) * 4
            tot = struct.unpack_from(">H", p, ip + 2)[0]
            plen = max(0, tot - ihl - doff)
            yield ts, src, dst, 6, sp, dp, fl, plen, p[t + doff:t + doff + 16]
        elif proto == 17 and len(p) >= t + 8:
            sp, dp = struct.unpack_from(">HH", p, t)
            yield ts, src, dst, 17, sp, dp, 0, max(0, len(p) - t - 8), p[t + 8:t + 24]
