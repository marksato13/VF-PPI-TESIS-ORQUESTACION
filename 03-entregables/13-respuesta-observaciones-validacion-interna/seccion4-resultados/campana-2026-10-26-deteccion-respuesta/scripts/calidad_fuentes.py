#!/usr/bin/env python3
"""Calidad de las fuentes por episodio (preparación 3A, 2026-11-01). Solo lee evidencias; no toca captura ni Suricata.

Separa cuatro cosas que NO son equivalentes:
  1. archivo           conservación y continuidad de los PCAP del SPAN (archivar.log del archivador): ficheros de
                       15 s de ppi-motor-capture archivados sin fallo y sin huecos entre inicios consecutivos.
  2. tcpdump_socket    descartes del socket AF_PACKET de tcpdump. tcpdump solo los informa AL TERMINAR el proceso
                       ("N packets dropped by kernel"); con ppi-motor-capture en marcha durante toda la campaña NO hay
                       medida por intervalo. Se declara "no_medido": es incertidumbre residual, no un cero.
  3. suricata          capture.kernel_drops de stats.log (contador acumulado, muestras cada ~8 s). El delta se toma
                       entre la última muestra <= desde y la primera >= hasta (cota CONSERVADORA: puede incluir
                       descartes de los segundos de alrededor, nunca omite los del intervalo).
  4. interfaz          rx_dropped de ens37 (muestreador). Su significado no está determinado en este laboratorio
                       (vmxnet3 en modo promiscuo; rx_missed/rx_fifo/rx_nohandler = 0, crece también sin carga). Se
                       informa; NO clasifica el episodio.

Clasificación por episodio, sobre [inicio - margen, fin + margen] (margen = 60 s, el horizonte de las ventanas):
  insuficiente  falta archivo (fallo de copia, fichero perdido, hueco entre ficheros > 15 s + tolerancia) o no hay
                muestras de Suricata que acoten el intervalo -> la ausencia de detección NO se puede atribuir al
                detector; el episodio sale de la comparación principal.
  degradada     archivo completo pero Suricata registró descartes de kernel en el intervalo -> la observación L7
                (HTTP/DNS de EVE, base de los heurísticos y de parte de las 28 características) puede estar
                incompleta; el episodio sale de la comparación principal (criterio independiente del resultado).
  completa      archivo continuo y 0 descartes de Suricata en el intervalo. Persiste la incertidumbre de (2) y (4).
En todos los casos las detecciones confirmadas se conservan visibles: una fuente degradada no anula una señal
observada, solo impide concluir una ausencia.

Uso (sensor o local con copias):
  python3 calidad_fuentes.py --marcas marcas.jsonl --stats stats-inicio.log stats-fin.log \
      --archivador archivo-pcap/archivar.log [--muestras recursos/muestras.jsonl] --salida calidad-fuentes.json
"""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402

MARGEN_S = 60.0
DURACION_PCAP_S = 15.0
TOL_PCAP_S = 2.0
_FECHA = re.compile(r"^Date: (\d+)/(\d+)/(\d{4}) -- (\d\d):(\d\d):(\d\d)")
_CONTADOR = re.compile(r"^(capture\.kernel_(?:packets|drops))\s*\|\s*Total\s*\|\s*(\d+)")
_OK = re.compile(r"^(\S+Z) OK (live-(\d{14})\.pcap) ")
_FALLO = re.compile(r"^(\S+Z) .*(FALLO|PERDIDO|perdido)")


def leer_stats(paths) -> list:
    """[(epoch, kernel_packets, kernel_drops)] ordenado y sin duplicados. stats.log usa fecha M/D/YYYY (UTC)."""
    out, t, cur = {}, None, {}
    for p in paths:
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = _FECHA.match(ln)
            if m:
                if t is not None and len(cur) == 2:
                    out[t] = (cur["capture.kernel_packets"], cur["capture.kernel_drops"])
                mo, d, y, hh, mi, ss = map(int, m.groups())
                t = datetime(y, mo, d, hh, mi, ss, tzinfo=timezone.utc).timestamp(); cur = {}
                continue
            m = _CONTADOR.match(ln)
            if m and t is not None:
                cur[m.group(1)] = int(m.group(2))
        if t is not None and len(cur) == 2:
            out[t] = (cur["capture.kernel_packets"], cur["capture.kernel_drops"])
    return sorted((k, *v) for k, v in out.items())


def delta_stats(serie, desde, hasta) -> dict:
    antes = [s for s in serie if s[0] <= desde]
    despues = [s for s in serie if s[0] >= hasta]
    if not antes or not despues:
        return {"medido": False, "motivo": "no hay muestras de stats.log que acoten el intervalo"}
    a, b = antes[-1], despues[0]
    if b[1] < a[1] or b[2] < a[2]:
        return {"medido": False, "motivo": "contador reiniciado (Suricata reiniciado) dentro del intervalo"}
    return {"medido": True, "muestra_desde_utc": an.iso(a[0]), "muestra_hasta_utc": an.iso(b[0]),
            "kernel_packets": b[1] - a[1], "kernel_drops": b[2] - a[2]}


def leer_archivador(path) -> dict:
    inicios, fallos = [], []
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = _OK.match(ln)
        if m:
            inicios.append(datetime.strptime(m.group(3), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp())
        elif _FALLO.match(ln):
            fallos.append(ln.strip())
    return {"inicios": sorted(set(inicios)), "fallos": fallos}


def continuidad(arch: dict, desde, hasta, duracion: float = DURACION_PCAP_S) -> dict:
    """¿Los ficheros archivados cubren [desde, hasta] sin huecos? Se juzga por el inicio que lleva el nombre
    (ficheros de `duracion` s: 15 hasta el 3B, 5 con la rotación de la Etapa 4); un hueco > duracion +
    tolerancia entre inicios consecutivos es pérdida de archivo."""
    ini = arch["inicios"]
    dentro = [t for t in ini if desde - duracion - TOL_PCAP_S <= t <= hasta]
    if not dentro:
        return {"continuo": False, "motivo": "ningún PCAP archivado cubre el intervalo"}
    huecos = [(a, b) for a, b in zip(dentro, dentro[1:]) if b - a > duracion + TOL_PCAP_S]
    cubre_ini = dentro[0] <= desde
    cubre_fin = dentro[-1] + duracion >= hasta
    fallos = [f for f in arch["fallos"] if desde - 60 <= an.ep_iso(f.split()[0]) <= hasta + 120]
    ok = cubre_ini and cubre_fin and not huecos and not fallos
    return {"continuo": ok, "ficheros": len(dentro), "cubre_inicio": cubre_ini, "cubre_fin": cubre_fin,
            "huecos": [{"desde_utc": an.iso(a), "hasta_utc": an.iso(b), "s": round(b - a, 1)} for a, b in huecos],
            "fallos_archivador": fallos,
            **({} if ok else {"motivo": "; ".join(x for x in [
                None if cubre_ini else "no cubre el inicio", None if cubre_fin else "no cubre el fin",
                f"{len(huecos)} hueco(s)" if huecos else None,
                f"{len(fallos)} fallo(s) del archivador" if fallos else None] if x)})}


def leer_muestras(path) -> list:
    out = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(ln)
            pk, dr = (int(x) for x in str(d["ens37_rx_drop"]).split())
            out.append((float(d["t"]), pk, dr))
        except (ValueError, KeyError, TypeError):
            continue
    return sorted(out)


def calidad_episodio(ep, serie, arch, muestras, margen=MARGEN_S, duracion=DURACION_PCAP_S) -> dict:
    if ep.get("fin_ep") is None:
        return {"estado": "insuficiente", "motivos": ["episodio sin fin"]}
    desde, hasta = ep["inicio_ep"] - margen, ep["fin_ep"] + margen
    sur = delta_stats(serie, desde, hasta) if serie else {"medido": False, "motivo": "sin stats.log"}
    con = continuidad(arch, desde, hasta, duracion) if arch else {"continuo": False, "motivo": "sin registro del archivador"}
    itf = {"medido": False, "motivo": "sin muestras"}
    if muestras:
        a = [m for m in muestras if m[0] <= desde]
        b = [m for m in muestras if m[0] >= hasta]
        if a and b:
            itf = {"medido": True, "rx_packets": b[0][1] - a[-1][1], "rx_dropped": b[0][2] - a[-1][2],
                   "significado": "no determinado; se informa sin clasificar"}
    motivos = []
    if not con["continuo"]:
        motivos.append("archivo: " + con.get("motivo", "no continuo"))
    if not sur["medido"]:
        motivos.append("suricata: " + sur["motivo"])
    if motivos:
        estado = "insuficiente"
    elif sur["kernel_drops"] > 0:
        estado = "degradada"; motivos.append(f"suricata: {sur['kernel_drops']} descartes de kernel en el intervalo")
    else:
        estado = "completa"
    return {"estado": estado, "motivos": motivos, "intervalo_utc": [an.iso(desde), an.iso(hasta)],
            "archivo": con, "suricata": sur,
            "tcpdump_socket": {"medido": False, "motivo": "tcpdump solo informa descartes al terminar el proceso; "
                                                          "incertidumbre residual declarada"},
            "interfaz_ens37": itf}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--stats", nargs="+", type=Path, default=[])
    ap.add_argument("--archivador", type=Path)
    ap.add_argument("--muestras", type=Path)
    ap.add_argument("--margen", type=float, default=MARGEN_S)
    ap.add_argument("--duracion-pcap", type=float, default=DURACION_PCAP_S,
                    help="rotación del anillo en s (-G): 15 hasta el 3B; 5 en la Etapa 4")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()
    eps, inc = an.leer_marcas(a.marcas)
    serie = leer_stats(a.stats) if a.stats else []
    arch = leer_archivador(a.archivador) if a.archivador else None
    mu = leer_muestras(a.muestras) if a.muestras else []
    res = {eid: calidad_episodio(ep, serie, arch, mu, a.margen, a.duracion_pcap) for eid, ep in eps.items()}
    a.salida.write_text(json.dumps({
        "definicion": __doc__.split("Uso (")[0].strip(), "margen_s": a.margen, "duracion_pcap_s": a.duracion_pcap,
        "fuentes": {"stats": [str(p) for p in a.stats], "archivador": str(a.archivador) if a.archivador else None,
                    "muestras": str(a.muestras) if a.muestras else None, "muestras_stats": len(serie)},
        "incidencias_marcas": inc, "episodios": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: (v["estado"], v["motivos"]) for k, v in res.items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
