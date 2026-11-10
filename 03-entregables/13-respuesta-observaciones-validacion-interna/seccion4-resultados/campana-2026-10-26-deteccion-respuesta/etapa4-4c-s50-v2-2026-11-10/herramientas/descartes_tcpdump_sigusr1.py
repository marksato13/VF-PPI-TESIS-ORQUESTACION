#!/usr/bin/env python3
"""Descartes del proceso tcpdump de captura a partir de las lecturas SIGUSR1 ya archivadas por s40 (4C, s50 v2, 2026-11-10).

tcpdump solo informa «N packets dropped by kernel» al terminar o al recibir SIGUSR1, y su contador es ACUMULADO desde que
arrancó el proceso. En la 4C el vigía y el muestreador de salud mandan SIGUSR1 cada 30 s y `s40` guarda las respuestas del
journal en `salud/tcpdump-anillo.log`. Con el contador acumulado, una última lectura posterior al fin de cada episodio con
valor 0 y el MISMO proceso desde su arranque demuestra 0 descartes del proceso en todo ese tiempo.

Salida: el JSON que ya consume `generar_respaldos.py --descartes-tcpdump` (el del 3B: `pid`, `proceso_desde`, `momento`,
`packets_captured`, `packets_received_by_filter`, `dropped_by_kernel`), más las comprobaciones hechas. Una medición que NO se
puede demostrar (log ausente o ilegible, sin lecturas, líneas mal formadas, más de un PID, PID distinto del servicio, servicio
reiniciado entre el inicio y el fin, contadores que decrecen, hora del servicio no UTC) escribe `dropped_by_kernel: null`
(«no medido») y NUNCA 0. Alcance: solo el proceso tcpdump; no cubre pérdidas aguas arriba (switch/SPAN).

Uso:
  python3 descartes_tcpdump_sigusr1.py --salud-captura <salud_captura.py> --log salud/tcpdump-anillo.log \
      --servicios-inicio estado-inicial/servicios.txt --servicios-fin copias/servicios-fin.txt --salida descartes-tcpdump.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
from pathlib import Path

VERSION = "2026-11-10.1"
UNIDAD = "ppi-motor-capture.service"


def _cargar(ruta: Path, nombre: str):
    espec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(mod)
    return mod


def leer_servicios(path: Path) -> dict:
    """{Id: {clave: valor}} de un `systemctl show -p MainPID -p NRestarts -p Id -p ActiveState -p ActiveEnterTimestamp`."""
    out, cur = {}, {}
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() + [""]:
        if not ln.strip():
            if cur.get("Id"):
                out[cur["Id"]] = cur
            cur = {}
        elif "=" in ln:
            k, v = ln.split("=", 1)
            cur[k.strip()] = v.strip()
    return out


def hora_servicio(txt: str):
    """«Mon 2026-11-09 19:28:12 UTC» -> epoch. Solo UTC; otra zona o formato -> None."""
    m = re.match(r"^\w{3} (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC$", (txt or "").strip())
    if not m:
        return None
    return dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp()


def medir(sc, log: Path, s_ini: dict, s_fin: dict, unidad: str = UNIDAD) -> dict:
    motivos, val = [], []
    r = {"fuente": f"lecturas SIGUSR1 de tcpdump ({unidad}) archivadas por s40 en {log.name}", "version": VERSION,
         "pid": None, "proceso_desde": None, "momento": None, "packets_captured": None, "packets_received_by_filter": None,
         "dropped_by_kernel": None, "lecturas": 0,
         "alcance": "contador acumulado del proceso tcpdump desde su arranque; no cubre pérdidas aguas arriba (switch/SPAN)"}
    ini, fin = s_ini.get(unidad), s_fin.get(unidad)
    if not ini or not fin:
        motivos.append(f"la unidad {unidad} no figura en servicios-inicio/servicios-fin")
    else:
        try:
            pid_i, pid_f = int(ini.get("MainPID", "")), int(fin.get("MainPID", ""))
        except ValueError:
            pid_i = pid_f = 0
        if pid_i <= 0 or pid_i != pid_f:
            motivos.append(f"MainPID de {unidad} no demostrado o distinto entre inicio ({ini.get('MainPID')}) y fin ({fin.get('MainPID')})")
        if ini.get("ActiveEnterTimestamp") != fin.get("ActiveEnterTimestamp") or ini.get("NRestarts") != fin.get("NRestarts"):
            motivos.append("el servicio de captura se reinició entre el inicio y el fin (ActiveEnterTimestamp/NRestarts distintos)")
        desde = hora_servicio(ini.get("ActiveEnterTimestamp", ""))
        if desde is None:
            motivos.append(f"ActiveEnterTimestamp no interpretable o no UTC: {ini.get('ActiveEnterTimestamp')!r}")
        if pid_i > 0 and not motivos:
            r["pid"], r["proceso_desde"] = pid_i, desde
            val.append(f"servicio: mismo MainPID {pid_i}, mismo ActiveEnterTimestamp y NRestarts al inicio y al fin")
    try:
        texto = log.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        motivos.append(f"log ilegible ({e.__class__.__name__})")
        texto = ""
    lecturas = sc.leer_tcpdump_log(log) if texto else []
    menciones = sum(1 for ln in texto.splitlines() if "packets captured" in ln)
    r["lecturas"] = len(lecturas)
    if not lecturas:
        motivos.append("sin lecturas SIGUSR1 en el log")
    if menciones != len(lecturas):
        motivos.append(f"{menciones - len(lecturas)} línea(s) con «packets captured» que no se pudieron interpretar")
    if lecturas:
        if any(x["t"] is None or x["pid"] is None for x in lecturas):
            motivos.append("lecturas sin hora o sin PID")
        else:
            lecturas.sort(key=lambda x: x["t"])
            pids = sorted({x["pid"] for x in lecturas})
            if len(pids) != 1:
                motivos.append(f"lecturas de más de un PID: {pids} (el contador se reinicia con cada proceso)")
            elif r["pid"] is not None and pids[0] != r["pid"]:
                motivos.append(f"las lecturas son del PID {pids[0]}, no del MainPID del servicio ({r['pid']})")
            elif r["pid"] is not None:
                val.append(f"{len(lecturas)} lecturas de un único PID {pids[0]}")
            for k, nombre in (("capturados", "capturados"), ("recibidos_filtro", "recibidos"), ("descartados_kernel", "descartados")):
                if any(y[k] < x[k] for x, y in zip(lecturas, lecturas[1:])):
                    motivos.append(f"el contador de {nombre} decrece entre lecturas")
            ult = lecturas[-1]
            r["momento"], r["packets_captured"] = ult["t"], ult["capturados"]
            r["packets_received_by_filter"] = ult["recibidos_filtro"]
            r["primera_lectura"], r["ultima_lectura"] = lecturas[0]["t"], ult["t"]
            r["hueco_max_s"] = round(max((y["t"] - x["t"] for x, y in zip(lecturas, lecturas[1:])), default=0.0), 1)
            r["maximo_dropped"] = max(x["descartados_kernel"] for x in lecturas)
            if not motivos:
                r["dropped_by_kernel"] = ult["descartados_kernel"]
                val.append(f"contadores crecientes; última lectura {ult['descartados_kernel']} descartados")
    r["validaciones"], r["motivos_no_medido"] = val, motivos
    if motivos:
        r["dropped_by_kernel"] = None
        r["pid"] = r["pid"]
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salud-captura", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--servicios-inicio", required=True, type=Path)
    ap.add_argument("--servicios-fin", required=True, type=Path)
    ap.add_argument("--unidad", default=UNIDAD)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)
    sc = _cargar(a.salud_captura, "salud_captura")
    try:
        s_ini, s_fin = leer_servicios(a.servicios_inicio), leer_servicios(a.servicios_fin)
    except OSError as e:
        s_ini = s_fin = {}
        print(f"  servicios ilegibles ({e.__class__.__name__})")
    r = medir(sc, a.log, s_ini, s_fin, a.unidad)
    a.salida.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    if r["dropped_by_kernel"] is None:
        print("  descartes de tcpdump: NO MEDIDO —", "; ".join(r["motivos_no_medido"]))
    else:
        print(f"  descartes de tcpdump: {r['dropped_by_kernel']} acumulados (PID {r['pid']}, {r['lecturas']} lecturas, "
              f"desde {dt.datetime.fromtimestamp(r['proceso_desde'], dt.timezone.utc).isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
