#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atribucion SIN solape: cada ventana del motor va a UN solo episodio, por frontera
temporal [t0_i, t0_{i+1}). Evita el doble conteo del margen fijo (ver confound de la
campana 2026-10-23: el enforcement ralentizo las herramientas del atacante y los
episodios se alargaron). Produce Tabla 8 por familia + detalle por episodio + t1.
Uso: python atribuir_campana.py <marcas.jsonl> <motor_slice.jsonl> <out_dir>
"""
import json, sys, csv, pathlib
from datetime import datetime

marcas_p, motor_p, outd = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
outd.mkdir(parents=True, exist_ok=True)

def ts(v):
    try: return float(v)
    except (TypeError, ValueError): pass
    s = str(v).strip().replace("Z", "+00:00")
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

mk = [json.loads(l) for l in open(marcas_p, encoding="utf-8") if l.strip()]
eps = []
for m in mk:
    if m.get("fase") == "inicio":
        eps.append({"id": m["id"], "familia": m["familia"], "t0": float(m["wall"])})
fin = {m["id"]: float(m["wall"]) for m in mk if m.get("fase") == "fin"}
eps.sort(key=lambda e: e["t0"])
for i, e in enumerate(eps):
    e["hasta"] = eps[i+1]["t0"] if i+1 < len(eps) else float("inf")
    e["t_fin_ataque"] = fin.get(e["id"], e["t0"])

motor = []
for l in open(motor_p, encoding="utf-8"):
    l = l.strip()
    if not l: continue
    try: d = json.loads(l)
    except json.JSONDecodeError: continue
    la = ts(d.get("logged_at"))
    if la is None: continue
    sc = d.get("score"); th = d.get("threshold")
    model = (sc is not None and th is not None and float(sc) < float(th))
    hv = d.get("heuristico") if isinstance(d.get("heuristico"), dict) else None
    motor.append({"la": la, "model": model, "heur": bool(hv),
                  "regla": (hv or {}).get("heuristico"), "accion": (hv or {}).get("accion"),
                  "decision": d.get("decision")})

det = []
for e in eps:
    w = [m for m in motor if e["t0"] <= m["la"] < e["hasta"]]
    tm = sorted(m["la"] for m in w if m["model"])
    th_ = sorted(m["la"] for m in w if m["heur"])
    ta = sorted(m["la"] for m in w if m["model"] or m["heur"])
    reglas = sorted({m["regla"] for m in w if m["heur"] and m["regla"]})
    acc = sorted({m["accion"] for m in w if m["heur"] and m["accion"]})
    det.append({"id": e["id"], "familia": e["familia"], "n_ventanas": len(w),
                "dur_ataque_s": round(e["t_fin_ataque"]-e["t0"], 1),
                "IF": int(bool(tm)), "heur": int(bool(th_)), "hibrido": int(bool(tm or th_)),
                "reglas": "|".join(reglas), "acciones": "|".join(acc),
                "t1_modelo_s": round(tm[0]-e["t0"], 1) if tm else None,
                "t1_heur_s": round(th_[0]-e["t0"], 1) if th_ else None,
                "t1_any_s": round(ta[0]-e["t0"], 1) if ta else None})

fam = {}
for d in det:
    f = fam.setdefault(d["familia"], {"n":0,"IF":0,"heur":0,"hib":0})
    f["n"]+=1; f["IF"]+=d["IF"]; f["heur"]+=d["heur"]; f["hib"]+=d["hibrido"]
orden = ["dns","flood","scan","brute"]
orden = [f for f in orden if f in fam] + [f for f in fam if f not in orden]
L = ["# Tabla 8 (campana 2026-10-23, modelo limpio if_limpio_2026_10 + heuristicos 2026-10-06.2)",
     "", "Atribucion sin solape: cada ventana -> un solo episodio por frontera [t0_i, t0_i+1).",
     "", "| Familia | Episodios | IF limpio | Heuristicos | Hibrido (OR) |", "|---|---:|---:|---:|---:|"]
T={"n":0,"IF":0,"heur":0,"hib":0}
for f in orden:
    d=fam[f]
    for k in T: T[k]+=d[k]
    L.append("| %s | %d | %d/%d | %d/%d | %d/%d |"%(f,d["n"],d["IF"],d["n"],d["heur"],d["n"],d["hib"],d["n"]))
L.append("| **Total** | **%d** | **%d/%d** | **%d/%d** | **%d/%d** |"%(T["n"],T["IF"],T["n"],T["heur"],T["n"],T["hib"],T["n"]))
(outd/"Tabla8-campana-sin-solape.md").write_text("\n".join(L), encoding="utf-8")
with open(outd/"detalle-episodios-sin-solape.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=list(det[0].keys())); w.writeheader(); [w.writerow(x) for x in det]

print("\n".join(L)); print("\n-- detalle --")
for d in det:
    print("%-10s n=%-3d dur=%6ss IF=%d heur=%d hib=%d reglas=%s t1=%s" % (
        d["id"], d["n_ventanas"], d["dur_ataque_s"], d["IF"], d["heur"], d["hibrido"], d["reglas"], d["t1_any_s"]))
