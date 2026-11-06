#!/usr/bin/env python3
"""S2 y S3 de E-carga v2 (= O2 y O3) desde DIR/obs_pcap/pcap.jsonl de obs_pcap.py. SOLO LECTURA.
Mismo cálculo que el análisis O2/O3 del 06-nov (evidencia/06-observacion/obs_sensor_post.sh).

  derivar_pcap.py PCAP.jsonl DESDE HASTA [--rotacion 5] -> JSON
  S2 (O2) todos los ficheros del anillo cuyo nombre (hora de inicio) cae en [DESDE, HASTA) se leyeron sin error de
          formato, incluido el primero, que debe empezar a <= rotación + 2 s de DESDE. Sin ficheros: null.
  S3 (O3) salto máximo entre nombres consecutivos <= 7 s. Con menos de dos ficheros: null.
          (La rotación de eve.json se informa aparte desde el listado de /var/log/suricata.)
"""
import argparse
import datetime as dt
import json


def t_nombre(r):
    return dt.datetime.strptime(r["fichero"][5:19], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()


def derivar(lineas, desde, hasta, rotacion=5.0):
    rs = []
    for l in lineas:
        if l.strip():
            rs.append(json.loads(l))
    v = sorted((r for r in rs if desde <= t_nombre(r) < hasta), key=t_nombre)
    res = {"version": "derivar_pcap 2026-11-06.1", "periodo": [desde, hasta], "ficheros": len(v)}
    if not v:
        res["S2"] = {"valor": None, "motivo": "ningún fichero del anillo empieza en la ventana"}
        res["S3"] = {"valor": None, "motivo": "sin ficheros"}
        return res
    err = [r["fichero"] for r in v if r.get("error")]
    primero = v[0]["fichero"]
    tarde = t_nombre(v[0]) - desde
    res["S2"] = {"valor": not err and tarde <= rotacion + 2, "errores": err[:20], "primero": primero,
                 "primero_tras_desde_s": round(tarde, 1), "ultimo": v[-1]["fichero"],
                 "registros": sum(r.get("registros", 0) or 0 for r in v),
                 "vacios": sum(1 for r in v if not r.get("registros"))}
    if len(v) < 2:
        res["S3"] = {"valor": None, "motivo": "menos de dos ficheros"}
        return res
    sn = [t_nombre(b) - t_nombre(a) for a, b in zip(v, v[1:])]
    sp = [b["primero"] - a["ultimo"] for a, b in zip(v, v[1:]) if a.get("ultimo") and b.get("primero")]
    res["S3"] = {"valor": max(sn) <= 7.0, "salto_max_nombres_s": round(max(sn), 1),
                 "hueco_max_paquetes_s": round(max(sp), 3) if sp else None,
                 "esperados": int((hasta - desde) // rotacion), "faltan_nombres": int((hasta - desde) // rotacion) - len(v)}
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pcap")
    ap.add_argument("desde", type=float)
    ap.add_argument("hasta", type=float)
    ap.add_argument("--rotacion", type=float, default=5.0)
    a = ap.parse_args()
    with open(a.pcap, encoding="utf-8") as fh:
        print(json.dumps(derivar(fh, a.desde, a.hasta, a.rotacion), ensure_ascii=False, indent=1))
