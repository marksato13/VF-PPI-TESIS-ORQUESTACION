"""Desglose de los 5 escaneos breves del 3B sobre el PCAP archivado (sin motor).

Para cada episodio: marcas de inicio/fin del orquestador, primer y ultimo SYN del origen de
ensayo (10.10.20.30) al destino (10.10.30.10), SYN totales, puertos distintos, pico por
segundo y duracion de la rafaga util (primer a ultimo SYN).
Uso: python desglose_breves.py <archivo-pcap> <marcas.jsonl> <salida.json>  (desde el repo)
"""
import collections
import datetime as dt
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, "scripts/engine")
from trocear_pcap import leer_paquetes  # noqa: E402

SRC, DST = bytes([10, 10, 20, 30]), bytes([10, 10, 30, 10])


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def episodios(marcas):
    ini, fin = {}, {}
    for linea in open(marcas, encoding="utf-8"):
        r = json.loads(linea)
        e = r.get("episodio_id", "")
        if not e.startswith("escaneo_breve"):
            continue
        t = dt.datetime.fromisoformat(r["reloj"]["pared_utc"]).timestamp()
        (ini if r["evento"] == "inicio" else fin)[e] = t
    return sorted((ini[e], fin[e], e) for e in ini if e in fin)


def rafaga(d, t0, t1):
    syn = []
    puertos = set()
    for f in sorted(d.glob("live-*.pcap")):
        stamp = dt.datetime.strptime(f.stem[5:], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
        if stamp > t1 + 30 or stamp < t0 - 60:
            continue
        _, it = leer_paquetes(f)
        for t, raw in it:
            if not t0 <= t <= t1:
                continue
            p = raw[16:]
            if p[12:14] == b"\x81\x00":
                p = p[4:]
            if p[12:14] != b"\x08\x00":
                continue
            ip = p[14:]
            ihl = (ip[0] & 15) * 4
            if ip[12:16] != SRC or ip[16:20] != DST or ip[9] != 6:
                continue
            tcp = ip[ihl:]
            fl = tcp[13]
            if fl & 0x02 and not fl & 0x10:
                syn.append(t)
                puertos.add(struct.unpack(">H", tcp[2:4])[0])
    return sorted(syn), puertos


def main():
    d, marcas, salida = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    filas = []
    for ini, fin, e in episodios(marcas):
        syn, puertos = rafaga(d, ini - 5, fin + 5)
        por_s = collections.Counter(int(t) for t in syn)
        # Rafaga principal: tramo con mas SYN separando por huecos > 2 s (el descubrimiento de
        # host de nmap queda aparte, segundos antes).
        tramos, actual = [], []
        for t in syn:
            if actual and t - actual[-1] > 2:
                tramos.append(actual)
                actual = []
            actual.append(t)
        if actual:
            tramos.append(actual)
        rp = max(tramos, key=len) if tramos else []
        filas.append({
            "episodio": e, "inicio_marca": iso(ini), "fin_marca": iso(fin),
            "duracion_marcas_s": round(fin - ini, 3),
            "primer_syn": iso(syn[0]) if syn else None, "ultimo_syn": iso(syn[-1]) if syn else None,
            "rafaga_util_s": round(syn[-1] - syn[0], 3) if syn else None,
            "syn": len(syn), "puertos_distintos": len(puertos),
            "pico_syn_por_s": max(por_s.values()) if por_s else 0,
            "rafaga_principal_inicio": iso(rp[0]) if rp else None,
            "rafaga_principal_fin": iso(rp[-1]) if rp else None,
            "rafaga_principal_s": round(rp[-1] - rp[0], 3) if rp else None,
            "rafaga_principal_syn": len(rp), "syn_fuera_rafaga": len(syn) - len(rp),
            "rafaga_principal_inicio_epoch": rp[0] if rp else None,
            "primer_syn_epoch": syn[0] if syn else None, "ultimo_syn_epoch": syn[-1] if syn else None,
        })
    json.dump(filas, open(salida, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for f in filas:
        print(f["episodio"], f["inicio_marca"], f["fin_marca"], f["primer_syn"], f["ultimo_syn"],
              f["rafaga_util_s"], f["syn"], f["puertos_distintos"], f["pico_syn_por_s"],
              f["rafaga_principal_inicio"], f["rafaga_principal_s"], f["rafaga_principal_syn"])


main()
