#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consume marcas.jsonl (Kali) + un recorte de motor_decision.log (sensor) y
produce, por EPISODIO: deteccion del modelo / heuristico / combinado y la
latencia t1-t0. Alimenta 4.2 (Tabla 8 en vivo + entrada para 30-metricas.py) y
4.4 (t0, t1). Todo offline, sin tocar el sensor.

Criterio: una ventana del log pertenece al episodio E si su `logged_at` cae en
[t0(E), t_fin(E)+margen]. Modelo detecta = score < threshold; heuristico = campo
`heuristico` no nulo; combinado = decision != PERMIT (o cualquiera de los dos).

Uso:
  python analizar_vivo.py --marcas marcas.jsonl --log motor_slice.jsonl \
     --entity 10.10.20.30 --margen 150 --out <dir>
"""
from __future__ import annotations
import argparse, json, csv, pathlib
from datetime import datetime

def ts(v):
    try: return float(v)
    except (TypeError, ValueError): pass
    s = str(v).strip().replace("Z", "+00:00")
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

def cargar_episodios(marcas_path):
    ini, fin = {}, {}
    fam = {}
    for ln in pathlib.Path(marcas_path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln: continue
        m = json.loads(ln)
        if m.get("familia") == "clock": continue
        eid = m["id"]; fam[eid] = m["familia"]
        if m["fase"] == "inicio": ini[eid] = float(m["wall"])
        elif m["fase"] == "fin": fin[eid] = float(m["wall"])
    eps = []
    for eid in ini:
        eps.append({"id": eid, "familia": fam.get(eid, ""),
                    "t0": ini[eid], "t_fin": fin.get(eid, ini[eid])})
    eps.sort(key=lambda e: e["t0"])
    return eps

def cargar_log(log_path, entity):
    filas = []
    for ln in pathlib.Path(log_path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or '"decision"' not in ln: continue
        try: d = json.loads(ln)
        except json.JSONDecodeError: continue
        if entity and d.get("entity_ip") != entity: continue
        la = ts(d.get("logged_at"))
        if la is None: la = ts(d.get("window_end_utc"))
        sc = d.get("score")
        filas.append({"la": la,
                      "model": (sc is not None and float(sc) < float(d.get("threshold", -1e9))),
                      "heur": d.get("heuristico") not in (None, "null"),
                      "heur_obj": d.get("heuristico"),
                      "decision": d.get("decision")})
    return filas

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marcas", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--entity", default="10.10.20.30")
    ap.add_argument("--margen", type=float, default=150.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

    eps = cargar_episodios(a.marcas)
    log = cargar_log(a.log, a.entity)

    detalle = []; abl = []
    for e in eps:
        lo, hi = e["t0"], e["t_fin"] + a.margen
        ventanas = [f for f in log if f["la"] is not None and lo <= f["la"] <= hi]
        tm = sorted(f["la"] for f in ventanas if f["model"])
        th = sorted(f["la"] for f in ventanas if f["heur"])
        ta = sorted(f["la"] for f in ventanas if f["model"] or f["heur"])
        reglas = sorted({(f["heur_obj"] or {}).get("heuristico") for f in ventanas if f["heur"] and isinstance(f["heur_obj"], dict)})
        acciones = sorted({(f["heur_obj"] or {}).get("accion") for f in ventanas if f["heur"] and isinstance(f["heur_obj"], dict)})
        detalle.append({
            "id": e["id"], "familia": e["familia"], "n_ventanas": len(ventanas),
            "modelo": bool(tm), "heuristico": bool(th), "combinado": bool(ta),
            "reglas": "|".join(r for r in reglas if r), "acciones": "|".join(x for x in acciones if x),
            "t1_modelo_s": round(tm[0]-e["t0"],1) if tm else None,
            "t1_heur_s": round(th[0]-e["t0"],1) if th else None,
            "t1_any_s": round(ta[0]-e["t0"],1) if ta else None,
        })
        abl.append({"id": e["id"], "familia": e["familia"],
                    "detected_by_model": bool(tm), "detected_by_heuristic": bool(th)})

    # Tabla 8 por familia (episodios)
    fams = {}
    for d in detalle:
        f = fams.setdefault(d["familia"], {"tot":0,"m":0,"h":0,"c":0})
        f["tot"]+=1; f["m"]+=d["modelo"]; f["h"]+=d["heuristico"]; f["c"]+=d["combinado"]
    L = ["# Tabla 8 (campana en vivo, modelo limpio) - ablacion por episodio", "",
         "| Familia | Episodios | IF limpio | Heuristicos | Hibrido (OR) |", "|---|---:|---:|---:|---:|"]
    T = {"tot":0,"m":0,"h":0,"c":0}
    for fa in sorted(fams):
        d=fams[fa]
        for k in T: T[k]+=d[k]
        L.append("| %s | %d | %d/%d | %d/%d | %d/%d |" % (fa,d["tot"],d["m"],d["tot"],d["h"],d["tot"],d["c"],d["tot"]))
    L.append("| **Total** | **%d** | **%d/%d** | **%d/%d** | **%d/%d** |" % (T["tot"],T["m"],T["tot"],T["h"],T["tot"],T["c"],T["tot"]))
    (out/"Tabla8-campana.md").write_text("\n".join(L), encoding="utf-8")

    with open(out/"detalle-por-episodio.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(detalle[0].keys()) if detalle else
                         ["id","familia","n_ventanas","modelo","heuristico","combinado","reglas","acciones","t1_modelo_s","t1_heur_s","t1_any_s"])
        w.writeheader(); [w.writerow(d) for d in detalle]

    (out/"ablacion-campana.json").write_text(json.dumps(
        {"episodios":[{"id":e["id"],"familia":e["familia"],"t_inicio":e["t0"],"t_fin":e["t_fin"]} for e in eps],
         "ablacion": abl}, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Episodios:", len(eps), "| con log:", sum(1 for d in detalle if d["n_ventanas"]>0))
    print("Totales -> IF %d/%d  heur %d/%d  hibrido %d/%d" % (T["m"],T["tot"],T["h"],T["tot"],T["c"],T["tot"]))
    print("Salidas:", out)

if __name__ == "__main__":
    raise SystemExit(main())
