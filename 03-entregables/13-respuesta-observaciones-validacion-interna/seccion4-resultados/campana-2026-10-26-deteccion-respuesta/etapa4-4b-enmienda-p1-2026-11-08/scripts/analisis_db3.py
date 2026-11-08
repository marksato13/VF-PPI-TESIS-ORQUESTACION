#!/usr/bin/env python3
"""DB-3 (PROPUESTA, sin aprobar) aplicado a un control de la 4B: L1 y L2 por entidad y α, con las ventanas faltantes por cotas.

Lee el motor vivo, el inventario (replay) y la salud EVE como control_4b.py; no escribe en ningún host. Usa limites_db3.py.
  analisis_db3.py --motor motor_decision.log --inventario replay/motor_decision.log --config config-campana-4c.json \
     --desde ISO --hasta ISO --salud-captura salud_captura.py --incrementos incrementos.jsonl --tcpdump-anillo tcpdump-anillo.log \
     --suricata-eve eve-segmento.json [--ahora EPOCH] [--min-c0-horas 2] --salida db3-4b.json

Ventana FALTANTE de una entidad = ventana requerida (del inventario) sin decisión C0: no evaluada, ausente, o decidida pero C1/C2/C3.
No se marca ni ALERT ni PERMIT: ver DB-3-PROPUESTA.md §4. Población de selección: los seis perfiles; el resto se reporta aparte.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402
import control_4b as c4  # noqa: E402
import limites_db3 as db  # noqa: E402
import poblacion  # noqa: E402

VERSION = "2026-11-08.1 (propuesta)"
PERFILES = tuple(f"10.10.20.{n}" for n in range(21, 27))
ALFAS = {"0.05": "IF_0.05", "0.03": "IF_0.03", "0.01": "IF_0.01"}


def evaluar_alfa(datos: dict, min_c0_horas: float = 2.0, l1: float = 1.0, l2: float = 0.10) -> dict:
    """Veredicto de UN α. ``datos`` = {ip: {"alertas": [epoch de ventana en ALERT], "c0": n ventanas C0 decididas,
    "faltan": [epoch de ventanas requeridas sin decisión C0], "req": n ventanas requeridas}}.
    Un α solo es elegible si LOS SEIS perfiles están presentes y cada uno cumple de forma concluyente con ≥ min_c0_horas de C0."""
    ent = {}
    for ip, d in datos.items():
        e = db.evaluar_entidad(d["alertas"], d["c0"], len(d["alertas"]), d["faltan"], d["req"] * 10.0 / 3600, l1, l2)
        e["ventanas_requeridas"], e["ventanas_c0_decididas"], e["ventanas_faltantes"] = d["req"], d["c0"], len(d["faltan"])
        h_c0 = d["c0"] * 10.0 / 3600
        e["horas_c0"] = round(h_c0, 3)
        if h_c0 < min_c0_horas:
            e["decision"] = "no_concluyente" if e["decision"] != "no_cumple" else "no_cumple"
            e["motivo_extra"] = f"menos de {min_c0_horas} h C0 observadas"
        ent[ip] = e
    sel = {ip: ent[ip] for ip in PERFILES if ip in ent}
    faltan_sel = [ip for ip in PERFILES if ip not in ent]
    v = db.veredicto_alfa(sel) if sel else {"alfa": "no_concluyente", "entidades": {}, "elegible": False}
    if faltan_sel:                       # una entidad de selección sin ventanas no puede dar un α concluyente
        v = {"alfa": "no_cumple" if v["alfa"] == "no_cumple" else "no_concluyente",
             "entidades": {**v["entidades"], **{ip: "sin_ventanas" for ip in faltan_sel}}, "elegible": False}
    return {"veredicto_alfa": v, "seleccion": sel, "reportadas_aparte": {ip: e for ip, e in ent.items() if ip not in PERFILES}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--inventario", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--salud-captura", required=True, type=Path)
    ap.add_argument("--incrementos", required=True, type=Path)
    ap.add_argument("--tcpdump-anillo", required=True, type=Path)
    ap.add_argument("--suricata-eve", type=Path, action="append", required=True)
    ap.add_argument("--ahora", type=float, default=None)
    ap.add_argument("--min-c0-horas", type=float, default=2.0)
    ap.add_argument("--l1", type=float, default=1.0, help="avisos por entidad y hora (propuesta)")
    ap.add_argument("--l2", type=float, default=0.10, help="fracción de ventanas decididas en ALERT (propuesta)")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)

    cfg = json.load(open(a.config, encoding="utf-8"))
    U = an.umbrales_de(cfg)
    pob = poblacion.cargar_poblacion(cfg)
    desde, hasta = an.como_epoch(a.desde), an.como_epoch(a.hasta)
    sc = c4.cargar_salud(a.salud_captura)
    ahora = a.ahora if a.ahora is not None else time.time()
    lect = sc.leer_eve_stats([Path(f) for f in a.suricata_eve], desde=desde - 2 * c4.HORIZONTE_S)
    incs = c4._jsonl(a.incrementos)
    clasif = c4.Clasificador(sc, incs, sc.leer_tcpdump_log(a.tcpdump_anillo), 5.0, lect, ahora)

    regs, _, _ = an.leer_motor(a.motor)
    inv, _, _ = an.leer_motor(a.inventario)
    vivo = {(r["entity_ip"], r["_wend"]): r for r in regs if desde <= r["_wend"] <= hasta}
    req = defaultdict(set)
    for r in inv:
        if desde <= r["_wend"] <= hasta and not poblacion.excluida(r["entity_ip"], pob):
            req[r["entity_ip"]].add(r["_wend"])
    for ip, w in vivo:                       # una decisión viva siempre es una ventana requerida
        if not poblacion.excluida(ip, pob):
            req[ip].add(w)

    res = {"version": VERSION, "intervalo_utc": [an.iso(desde), an.iso(hasta)], "min_c0_horas": a.min_c0_horas,
           "limites_propuestos": {"L1_avisos_por_entidad_y_hora": a.l1, "L2_fraccion_en_alerta": a.l2,
                                  "separacion_aviso_s": db.SEPARACION_AVISO_S},
           "poblacion_seleccion": list(PERFILES), "alfas": {}}
    por_ip_base = {}
    for ip, ws in sorted(req.items()):
        c0 = {w: vivo[(ip, w)] for w in ws if (ip, w) in vivo and clasif.clase(w)["clase"] == "C0"}
        faltan = sorted(w for w in ws if w not in c0)
        por_ip_base[ip] = (c0, faltan, len(ws))
    for alfa, cfgname in ALFAS.items():
        datos = {ip: {"alertas": sorted(w for w, r in c0.items() if an.senales(r, U)[cfgname]), "c0": len(c0), "faltan": faltan, "req": n_req}
                 for ip, (c0, faltan, n_req) in por_ip_base.items()}
        res["alfas"][alfa] = evaluar_alfa(datos, a.min_c0_horas, a.l1, a.l2)
    a.salida.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({al: res["alfas"][al]["veredicto_alfa"]["alfa"] for al in ALFAS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
