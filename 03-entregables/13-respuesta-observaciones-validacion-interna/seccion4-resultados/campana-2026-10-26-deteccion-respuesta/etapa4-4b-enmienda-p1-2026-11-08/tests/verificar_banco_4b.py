#!/usr/bin/env python3
"""Comprueba las salidas del banco del recorrido completo (banco_4b_completo.sh). Imprime OK/FALLO por comprobación."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
fallos = 0


def ok(cond, msg):
    global fallos
    print(("OK    " if cond else "FALLO ") + msg)
    if not cond:
        fallos += 1


def cargar(n):
    p = OUT / n
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def rc(n):
    p = OUT / f"s50-{n}.rc"
    return int(p.read_text().strip()) if p.exists() else None


def utc(h, m, s=0):
    return dt.datetime(2026, 11, 1, h, m, s, tzinfo=dt.timezone.utc).timestamp()


CD, CH = utc(7, 32), utc(8, 5)
PUBLICADO = {"IF_0.05": 395, "IF_0.03": 254, "IF_0.01": 83, "HEUR": 92, "HIB_0.05": 466, "HIB_0.03": 336, "HIB_0.01": 171}

# ---------------------------------------------------------------------------------------------- A: el defecto
a = cargar("control-4b-A.json")
ok(a is not None, "A: el control original termina y escribe control-4b.json")
if a:
    d = a["detector"]
    n = d["ventanas_decididas"]
    ok(n == 2644, f"A: 2 644 ventanas decididas del control del 3B ({n})")
    ok(d["ventanas_por_clase"]["C3"] == n and d["ventanas_por_clase"]["C0"] == 0,
       "A: DEFECTO REPRODUCIDO: con la salud congelada (stats.log sin kernel_drops) las 2 644 ventanas son C3 y ninguna C0")
    ok("Suricata sin medida completa en el periodo" in str(d["motivos_por_clase"].get("C3", {})) or
       "Suricata sin medida completa en el periodo" in json.dumps(d["motivos_por_clase"]),
       "A: el motivo del C3 es «Suricata sin medida completa»")

# ---------------------------------------------------------------------------------------------- B: limpio + P1
ok(rc("B") == 0, f"B: s50 enmendado con datos sanos: rc 0 ({rc('B')})")
b = cargar("control-4b-B.json")
ok(b is not None, "B: control-4b.json escrito")
if b:
    d = b["detector"]
    n = d["ventanas_decididas"]
    c0 = d["por_clase"].get("C0", {}).get("if_y_configuraciones", {})
    ok(d["ventanas_por_clase"]["C0"] == n == 2644, f"B: las 2 644 ventanas son C0 ({d['ventanas_por_clase']})")
    ok(all(c0.get(k, {}).get("falsas_alarmas") == v for k, v in PUBLICADO.items()),
       "B: las cifras de C0 coinciden con el control publicado del 3B (IF 395/254/83, HEUR 92, HIB 466/336/171)")
    s = d["suricata_por_ventana"]["ventanas_decididas_por_categoria"]
    ok(s == {"cero_descartes": n, "descartes": 0, "datos_faltantes": 0}, f"B: las tres categorías por ventana: {s}")
    pc = b["periodo_completo"]["anillo_if_heur"]
    ok((pc["clase"], pc["suricata_categoria"], pc["suricata_estado"]) == ("C0", "cero_descartes", "cero_explicito"),
       "B: periodo completo C0 / cero_descartes / cero_explicito")
    ok(b["fuentes"]["suricata_eve"]["muestras_leidas"] > 400, "B: muestras EVE leídas > 400")
for f in ("anillo", "via"):
    x = cargar(f"salud-control-{f}-B.json")
    ok(x is not None and x["clase"] == "C0" and x["info"]["suricata"]["estado"] == "cero_explicito",
       f"B: a2/a3 ({f}) clasifican el periodo con EVE: C0 / cero_explicito")

# ---------------------------------------------------------------------------------------------- C: eventos + P1
ok(rc("C") == 0, f"C: s50 enmendado con eventos: rc 0 ({rc('C')})")
c = cargar("control-4b-C.json")
motor = OUT / "motor-C.log"
if c:
    d = c["detector"]
    n = d["ventanas_decididas"]
    vc = d["ventanas_por_clase"]
    ok(vc["C0"] + vc["C1"] + vc["C3"] == n == 2644 and vc["C0"] and vc["C1"] and vc["C3"],
       f"C: ventanas por clase C0/C1/C3 = {vc['C0']}/{vc['C1']}/{vc['C3']} (suman {n})")
    s = d["suricata_por_ventana"]
    cat = s["ventanas_decididas_por_categoria"]
    ok(cat["cero_descartes"] == vc["C0"] and cat["descartes"] == vc["C1"] and cat["datos_faltantes"] == vc["C3"],
       f"C: categorías de Suricata = clases ({cat})")
    est = s["datos_faltantes_decididas_por_estado"]
    ok(set(est) == {"ausente", "cobertura_insuficiente"}, f"C: estados de datos faltantes conservados ({est})")
    ok(s["tramos_con_datos_faltantes_total"] == 2, f"C: dos tramos con datos faltantes ({s['tramos_con_datos_faltantes']})")
    pc = c["periodo_completo"]["anillo_if_heur"]
    ok(pc["clase"] == "C3" and pc["suricata_categoria"] == "datos_faltantes", f"C: periodo completo C3 / datos_faltantes ({pc['suricata_estado']})")
    ok(pc["suricata"]["descartes_parciales"] == 23 and pc["suricata"]["descartes"] is None,
       "C: el periodo informa 23 descartes parciales observados y NO afirma un total (hay datos faltantes)")
    c0 = d["por_clase"]["C0"]["if_y_configuraciones"]
    ok(all(c0[k]["falsas_alarmas"] <= v for k, v in PUBLICADO.items()) and c0["ventanas"] == vc["C0"],
       "C: las tasas de C0 usan solo ventanas con cero descartes y no superan el control completo del 3B")
    ok("if_y_configuraciones" in d["por_clase"]["C1"] and "if_y_configuraciones" not in d["por_clase"]["C3"],
       "C: C1 se publica aparte y C3 no entra en ninguna tasa")
    # oráculo geométrico independiente (ventanas «seguras» según el diseño de los eventos)
    import gzip
    import shutil
    raiz = Path("/d3b")
    reg = {}
    with gzip.open(raiz / "copias/motor_decision.log.gz", "rt", encoding="utf-8") as fh:
        for l in fh:
            if '"event": "decision"' in l or '"event":"decision"' in l:
                r = json.loads(l)
                w = dt.datetime.fromisoformat(r["window_end_utc"].replace("Z", "+00:00")).timestamp()
                if CD <= w <= CH:
                    reg[(r["entity_ip"], r["window_end_utc"])] = w
    rafaga, hueco, sin = (utc(7, 44, 52), utc(7, 45, 0)), (utc(7, 52, 10), utc(7, 53, 50)), (utc(7, 58, 0), utc(7, 58, 40))

    def solapa(w, ab, m=0):
        return max(0.0, min(w, ab[1] + m) - max(w - 60, ab[0] - m))
    s0 = s1 = s3 = nsafe = 0
    for w in reg.values():
        malos = solapa(w, hueco, 25) > 0 or solapa(w, sin, 25) > 0
        if not malos and solapa(w, rafaga, 25) == 0:
            s0 += 1
        elif not malos and rafaga[0] > w - 60 + 10 and rafaga[1] < w - 10:
            s1 += 1
        elif solapa(w, hueco) >= 30 or solapa(w, sin) >= 30:
            s3 += 1
    inseg = len(reg) - s0 - s1 - s3
    ok(len(reg) == n, f"C: el oráculo ve las mismas {len(reg)} decisiones")
    ok(s0 <= vc["C0"] <= s0 + inseg and s1 <= vc["C1"] <= s1 + inseg and s3 <= vc["C3"] <= s3 + inseg,
       f"C: clases dentro de las cotas del oráculo geométrico (seguras C0/C1/C3 = {s0}/{s1}/{s3}, inseguras {inseg})")
for f in ("anillo", "via"):
    x = cargar(f"salud-control-{f}-C.json")
    ok(x is not None and x["clase"] == "C3" and x["info"]["suricata"]["estado"] in ("ausente", "cobertura_insuficiente"),
       f"C: a2/a3 ({f}) clasifican el periodo con EVE: C3 y estado «{x and x['info']['suricata']['estado']}»")

# ---------------------------------------------------------------------------------------------- D: sin segmento EVE
ok(rc("D") == 2, f"D: sin eve-segmento.json s50 se detiene con rc 2 ({rc('D')})")
t = (OUT / "s50-D.txt").read_text(encoding="utf-8", errors="replace") if (OUT / "s50-D.txt").exists() else ""
ok("PARAR: falta el segmento EVE" in t, "D: el mensaje dice que falta el segmento EVE")
ok(not (OUT / "control-4b-D.json").exists(), "D: no se escribe ningún control sin datos de Suricata")

print("RESULTADO:", "todas las comprobaciones OK" if not fallos else f"HAY {fallos} FALLOS")
sys.exit(1 if fallos else 0)
