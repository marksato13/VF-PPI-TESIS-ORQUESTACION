#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.2 - Ablacion de componentes con el MODELO LIMPIO (if_limpio_2026_10) y los
heuristicos VIGENTES (heuristicos.py, VERSION_UMBRALES 2026-10-06.2).

OFFLINE, reproducible, sin tocar el sensor. Conjunto de evaluacion: el set de
LABORATORIO v2 (multilayer-v2-anomalies.csv = 179 ventanas de ataque; -normal.csv
= 1373 ventanas benignas). NO es la bateria de 9 episodios de replay (nota 26):
esa no conservo datos por ventana ni PCAP (ver el inventario). Aqui la unidad
"episodio" es cada campaign_id (una corrida corta con 1-N ventanas).

Separa, como exige el encargo:
 - componente: IF limpio solo / heuristicos solos / combinado (OR),
 - unidad: por VENTANA y por EPISODIO (campaign_id), ademas por familia,
 - benigno: FPR de cada componente sobre las mismas ventanas normales + cuantas
   ventanas benignas generarian LIMIT y BLOCK (accion calculada OFFLINE, no una
   restriccion realmente aplicada).
"""
from __future__ import annotations
import csv, json, hashlib, sys, pathlib, importlib.util

BASE_CF = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW")
PRODUCTO = BASE_CF / "producto-main"
ANOM = PRODUCTO / "artifacts" / "dataset" / "multilayer-v2-anomalies.csv"
NORM = PRODUCTO / "artifacts" / "dataset" / "multilayer-v2-normal.csv"
HEUR_PY = PRODUCTO / "scripts" / "engine" / "heuristicos.py"
PAQ = pathlib.Path(r"C:\Users\markp\AppData\Local\Temp\claude\C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\run\arte\paq_despues.joblib")
OUT = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\aqui trabajamos ...claude\analisis-seccion4\4.2-ablacion")

def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def cargar_heuristicos():
    spec = importlib.util.spec_from_file_location("heuristicos", HEUR_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def familia(campaign_id: str) -> str:
    c = campaign_id.upper()
    if "DNS-ENTROPY" in c or "DNS-NX" in c:
        return "DNS (alta entropia / NXDOMAIN)"
    if "PORT-SCAN" in c or "SYN-RATE" in c or "UDP-PROBE" in c:
        return "Escaneo / recon (L3-L4)"
    if "PASSWORD-SPRAY" in c or "AUTH-FAIL" in c:
        return "Fuerza bruta / auth (L7)"
    return "Otro: " + c

def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main() -> int:
    import numpy as np, joblib
    OUT.mkdir(parents=True, exist_ok=True)
    heur = cargar_heuristicos()
    paq = joblib.load(PAQ)
    modelo, escalador, feats, umbral = paq["modelo"], paq["escalador"], paq["features"], float(paq["umbral"])
    print("Paquete limpio: umbral(decision_function) = %.6f  | n_features = %d" % (umbral, len(feats)))
    print("Heuristicos VERSION_UMBRALES =", heur.VERSION_UMBRALES)

    def puntuar(rows):
        X = np.asarray([[float(r[c]) for c in feats] for r in rows], dtype=float)
        df = escalador.transform(X)
        return modelo.decision_function(df)

    def evaluar_set(rows):
        """Devuelve lista por fila: (model_alert, heur_dict_or_None)."""
        sc = puntuar(rows)
        out = []
        for r, s in zip(rows, sc):
            v = heur.evaluar(r)
            out.append((bool(s < umbral), v))
        return out, sc

    # ---- ANOMALIAS ----
    anom = leer(ANOM)
    res_a, sc_a = evaluar_set(anom)
    # agregacion por episodio (campaign_id) y por familia
    eps = {}   # campaign_id -> dict
    for r, (m_alert, hv) in zip(anom, res_a):
        cid = r["campaign_id"]; fam = familia(cid)
        e = eps.setdefault(cid, {"familia": fam, "n_vent": 0, "model": False,
                                 "heur": False, "reglas": set(), "acciones": set()})
        e["n_vent"] += 1
        if m_alert: e["model"] = True
        if hv:
            e["heur"] = True; e["reglas"].add(hv["heuristico"]); e["acciones"].add(hv["accion"])

    # por familia (por EPISODIO y por VENTANA)
    fams = {}
    for cid, e in eps.items():
        f = fams.setdefault(e["familia"], {"ep_total":0,"ep_model":0,"ep_heur":0,"ep_hib":0,
                                           "vt_total":0,"vt_model":0,"vt_heur":0,"vt_hib":0})
        f["ep_total"] += 1
        if e["model"]: f["ep_model"] += 1
        if e["heur"]:  f["ep_heur"]  += 1
        if e["model"] or e["heur"]: f["ep_hib"] += 1
    for r, (m_alert, hv) in zip(anom, res_a):
        f = fams[familia(r["campaign_id"])]
        f["vt_total"] += 1
        if m_alert: f["vt_model"] += 1
        if hv:      f["vt_heur"]  += 1
        if m_alert or hv: f["vt_hib"] += 1

    # ---- BENIGNO ----
    norm = leer(NORM)
    res_n, sc_n = evaluar_set(norm)
    def fpr(rows, res, particion=None):
        sel = [(m,h) for r,(m,h) in zip(rows,res) if (particion is None or r["partition"]==particion)]
        n = len(sel)
        fm = sum(1 for m,h in sel if m)
        fh = sum(1 for m,h in sel if h)
        fc = sum(1 for m,h in sel if m or h)
        limit = sum(1 for m,h in sel if h and h["accion"]=="LIMIT")
        block = sum(1 for m,h in sel if h and h["accion"]=="BLOCK")
        return {"n":n,"model":fm,"heur":fh,"hibrido":fc,"limit":limit,"block":block,
                "fpr_model": fm/n if n else 0, "fpr_heur": fh/n if n else 0,
                "fpr_hibrido": fc/n if n else 0}
    particiones = sorted(set(r["partition"] for r in norm))
    fpr_test = fpr(norm, res_n, "test") if "test" in particiones else None
    fpr_todo = fpr(norm, res_n, None)

    # ===== SALIDAS =====
    # Tabla 8 por familia (episodios)
    def frac(a,b): return "%d/%d" % (a,b)
    orden = ["DNS (alta entropia / NXDOMAIN)","Escaneo / recon (L3-L4)","Fuerza bruta / auth (L7)"]
    orden = [f for f in orden if f in fams] + [f for f in fams if f not in orden]
    lineas = []
    lineas.append("# Tabla 8 - Ablacion de componentes (modelo limpio `if_limpio_2026_10` + heuristicos `%s`)" % heur.VERSION_UMBRALES)
    lineas.append("")
    lineas.append("Conjunto: laboratorio v2 (Kali), %d ventanas de ataque en %d episodios (campaign_id)." % (len(anom), len(eps)))
    lineas.append("Unidad EPISODIO: un episodio cuenta como detectado por un componente si >=1 de sus ventanas dispara ese componente.")
    lineas.append("")
    lineas.append("## Por EPISODIO")
    lineas.append("")
    lineas.append("| Familia | Episodios | IF limpio solo | Heuristicos solos | Hibrido (OR) |")
    lineas.append("|---|---:|---:|---:|---:|")
    tot = {"ep_total":0,"ep_model":0,"ep_heur":0,"ep_hib":0,"vt_total":0,"vt_model":0,"vt_heur":0,"vt_hib":0}
    for f in orden:
        d = fams[f]
        for k in tot: tot[k]+=d[k]
        lineas.append("| %s | %d | %s | %s | %s |" % (f, d["ep_total"],
            frac(d["ep_model"],d["ep_total"]), frac(d["ep_heur"],d["ep_total"]), frac(d["ep_hib"],d["ep_total"])))
    lineas.append("| **Total** | **%d** | **%s** | **%s** | **%s** |" % (tot["ep_total"],
        frac(tot["ep_model"],tot["ep_total"]), frac(tot["ep_heur"],tot["ep_total"]), frac(tot["ep_hib"],tot["ep_total"])))
    lineas.append("")
    lineas.append("## Por VENTANA")
    lineas.append("")
    lineas.append("| Familia | Ventanas | IF limpio solo | Heuristicos solos | Hibrido (OR) |")
    lineas.append("|---|---:|---:|---:|---:|")
    for f in orden:
        d = fams[f]
        lineas.append("| %s | %d | %s | %s | %s |" % (f, d["vt_total"],
            frac(d["vt_model"],d["vt_total"]), frac(d["vt_heur"],d["vt_total"]), frac(d["vt_hib"],d["vt_total"])))
    lineas.append("| **Total** | **%d** | **%s** | **%s** | **%s** |" % (tot["vt_total"],
        frac(tot["vt_model"],tot["vt_total"]), frac(tot["vt_heur"],tot["vt_total"]), frac(tot["vt_hib"],tot["vt_total"])))
    lineas.append("")
    lineas.append("## Falsos positivos por componente (ventanas benignas de laboratorio v2)")
    lineas.append("")
    lineas.append("> Accion calculada OFFLINE sobre ventanas; NO es una restriccion aplicada en el host.")
    lineas.append("")
    lineas.append("| Conjunto benigno | n | FPR IF | FPR heuristicos | FPR hibrido | vent. LIMIT | vent. BLOCK |")
    lineas.append("|---|---:|---:|---:|---:|---:|---:|")
    def fila_fpr(nombre, d):
        return "| %s | %d | %.2f%% | %.2f%% | %.2f%% | %d | %d |" % (nombre, d["n"],
            100*d["fpr_model"], 100*d["fpr_heur"], 100*d["fpr_hibrido"], d["limit"], d["block"])
    if fpr_test: lineas.append(fila_fpr("particion=test", fpr_test))
    lineas.append(fila_fpr("todas (train+val+test)", fpr_todo))
    (OUT/"Tabla8-ablacion-limpio.md").write_text("\n".join(lineas), encoding="utf-8")

    # CSV por familia
    with open(OUT/"Tabla8-ablacion-limpio.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["familia","episodios","ep_IF","ep_heur","ep_hibrido","ventanas","vt_IF","vt_heur","vt_hibrido"])
        for fa in orden:
            d=fams[fa]; w.writerow([fa,d["ep_total"],d["ep_model"],d["ep_heur"],d["ep_hib"],d["vt_total"],d["vt_model"],d["vt_heur"],d["vt_hib"]])
        w.writerow(["TOTAL",tot["ep_total"],tot["ep_model"],tot["ep_heur"],tot["ep_hib"],tot["vt_total"],tot["vt_model"],tot["vt_heur"],tot["vt_hib"]])

    # Matriz por episodio
    with open(OUT/"matriz-por-episodio.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["campaign_id","familia","n_ventanas","IF_detecta","heur_detecta","reglas_heur","acciones","hibrido_detecta","aporta"])
        for cid in sorted(eps):
            e=eps[cid]
            aporta = "ambos" if (e["model"] and e["heur"]) else ("solo_IF" if e["model"] else ("solo_heuristico" if e["heur"] else "ninguno"))
            w.writerow([cid,e["familia"],e["n_vent"],int(e["model"]),int(e["heur"]),
                        "|".join(sorted(e["reglas"])),"|".join(sorted(e["acciones"])),int(e["model"] or e["heur"]),aporta])

    # Metadata reproducible
    meta = {
        "experimento": "4.2 ablacion offline modelo limpio + heuristicos vigentes",
        "fecha_analisis": "2026-10-23",
        "modelo": {"id":"if_limpio_2026_10","paquete":str(PAQ),"sha256_paquete":sha256(PAQ),
                   "umbral_decision_function":umbral,"n_features":len(feats),"features":feats},
        "heuristicos": {"archivo":str(HEUR_PY),"sha256":sha256(HEUR_PY),"version":heur.VERSION_UMBRALES},
        "datos": {"anomalias":str(ANOM),"sha256_anomalias":sha256(ANOM),"n_anom":len(anom),
                  "normal":str(NORM),"sha256_normal":sha256(NORM),"n_normal":len(norm),
                  "particiones_normal":particiones},
        "criterio_deteccion": "episodio detectado = >=1 ventana dispara el componente; ventana = la propia ventana",
        "benigno_test": fpr_test, "benigno_todo": fpr_todo,
        "repos": {"producto-main":"fa9e5b0 (2026-10-19)","orquestacion-limpio":"2f72d4d (2026-10-19)"},
        "nota": "Set de laboratorio v2; NO es la bateria de 9 episodios de replay (nota 26), cuyos datos por ventana/PCAP no se conservaron.",
    }
    (OUT/"metadata-ablacion-limpio.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")

    print("\n== RESUMEN ==")
    print("Episodios(campaign_id): IF %d/%d | heur %d/%d | hibrido %d/%d" % (
        tot["ep_model"],tot["ep_total"],tot["ep_heur"],tot["ep_total"],tot["ep_hib"],tot["ep_total"]))
    print("Ventanas: IF %d/%d | heur %d/%d | hibrido %d/%d" % (
        tot["vt_model"],tot["vt_total"],tot["vt_heur"],tot["vt_total"],tot["vt_hib"],tot["vt_total"]))
    if fpr_test:
        print("Benigno test: FPR IF %.2f%% heur %.2f%% hibrido %.2f%% (n=%d)" % (
            100*fpr_test["fpr_model"],100*fpr_test["fpr_heur"],100*fpr_test["fpr_hibrido"],fpr_test["n"]))
    print("Benigno todo: FPR IF %.2f%% heur %.2f%% hibrido %.2f%% (n=%d)" % (
        100*fpr_todo["fpr_model"],100*fpr_todo["fpr_heur"],100*fpr_todo["fpr_hibrido"],fpr_todo["n"]))
    print("Salidas en:", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
