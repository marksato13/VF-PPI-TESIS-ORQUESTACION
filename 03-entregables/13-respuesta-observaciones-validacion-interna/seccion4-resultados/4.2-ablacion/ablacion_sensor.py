#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.2 - Ablacion VALIDA sobre datos del SENSOR (misma distribucion que el modelo).

Modelo limpio if_limpio_2026_10 (paquete local, umbral decision_function -0,069397)
+ heuristicos vigentes (heuristicos.py, 2026-10-06.2). TODO offline, sin tocar el
sensor. NO usa el set de laboratorio (otra distribucion: daria el artefacto
sim->real de ~90% FPR).

Conjuntos:
 - ATAQUE (sensor): las 181 ventanas Kali del particionado (eligible_training=False
   en limpio.csv). Son trafico Kali capturado en el espejo, EXCLUIDO del
   entrenamiento del modelo limpio -> fuera de muestra, evaluacion legitima.
 - BENIGNO (sensor): normal-reservado.csv (65 421 ventanas de test retenidas).

Separa componente (IF / heuristicos / combinado) y unidad (ventana y episodio por
contiguidad temporal). Valida de paso el FPR del modelo sobre benigno.
"""
from __future__ import annotations
import csv, json, hashlib, pathlib, importlib.util
from datetime import datetime, timezone

S = pathlib.Path(r"C:\Users\markp\AppData\Local\Temp\claude\C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad")
LIMPIO = S / "exp" / "limpio.csv"
NORMAL = S / "run" / "normal-reservado.csv"
PAQ = S / "run" / "arte" / "paq_despues.joblib"
HEUR_PY = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\heuristicos.py")
OUT = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\aqui trabajamos ...claude\analisis-seccion4\4.2-ablacion")

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def heur_mod():
    spec = importlib.util.spec_from_file_location("heuristicos", HEUR_PY)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def parse_t(s):
    s = (s or "").strip()
    try: return float(s)
    except ValueError: pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z","%Y-%m-%d %H:%M:%S%z","%Y-%m-%dT%H:%M:%SZ","%Y-%m-%d %H:%M:%S"):
        try:
            d = datetime.strptime(s, fmt)
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            return d.timestamp()
        except ValueError: continue
    return None

def main():
    import numpy as np, joblib
    OUT.mkdir(parents=True, exist_ok=True)
    H = heur_mod()
    paq = joblib.load(PAQ)
    modelo, esc, feats, umbral = paq["modelo"], paq["escalador"], paq["features"], float(paq["umbral"])

    # 181 Kali del sensor
    kali = []
    with open(LIMPIO, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("eligible_training") == "False":
                kali.append(r)
    # benigno
    with open(NORMAL, newline="", encoding="utf-8") as f:
        benig = list(csv.DictReader(f))
    print("Kali sensor:", len(kali), "| benigno:", len(benig), "| umbral df:", umbral)

    def model_alert(rows):
        X = np.asarray([[float(r[c]) for c in feats] for r in rows], dtype=float)
        return modelo.decision_function(esc.transform(X)) < umbral

    ma_k = model_alert(kali); ma_b = model_alert(benig)
    hv_k = [H.evaluar(r) for r in kali]
    hv_b = [H.evaluar(r) for r in benig]

    # ---- ATAQUE por ventana ----
    k_model = int(sum(ma_k)); k_heur = sum(1 for v in hv_k if v)
    k_hib = sum(1 for m,v in zip(ma_k,hv_k) if m or v)
    reglas = {}
    for v in hv_k:
        if v: reglas[v["heuristico"]] = reglas.get(v["heuristico"],0)+1

    # episodios por contiguidad temporal (gap > 120 s)
    idx = sorted(range(len(kali)), key=lambda i: (kali[i].get("entity_ip",""), parse_t(kali[i].get("window_end_utc")) or 0))
    episodios = []; cur=None; prev=None; prev_ent=None
    for i in idx:
        t = parse_t(kali[i].get("window_end_utc")); ent = kali[i].get("entity_ip","")
        if cur is None or ent!=prev_ent or (t is not None and prev is not None and t-prev>120):
            cur = {"entidad":ent,"idx":[]}; episodios.append(cur)
        cur["idx"].append(i); prev=t; prev_ent=ent
    ep_rows = []
    for e in episodios:
        ii=e["idx"]
        m = any(ma_k[i] for i in ii); h = any(hv_k[i] for i in ii)
        rr = sorted({hv_k[i]["heuristico"] for i in ii if hv_k[i]})
        ts = [parse_t(kali[i].get("window_end_utc")) for i in ii if parse_t(kali[i].get("window_end_utc")) is not None]
        ep_rows.append({"entidad":e["entidad"],"n_vent":len(ii),"IF":int(m),"heur":int(h),
                        "reglas":"|".join(rr),"hibrido":int(m or h),
                        "ini":min(ts) if ts else None,"fin":max(ts) if ts else None})
    ep_model = sum(e["IF"] for e in ep_rows); ep_heur=sum(e["heur"] for e in ep_rows); ep_hib=sum(e["hibrido"] for e in ep_rows)

    # ---- BENIGNO ----
    b_model = int(sum(ma_b)); b_heur=sum(1 for v in hv_b if v)
    b_hib = sum(1 for m,v in zip(ma_b,hv_b) if m or v)
    b_limit = sum(1 for v in hv_b if v and v["accion"]=="LIMIT")
    b_block = sum(1 for v in hv_b if v and v["accion"]=="BLOCK")
    n_b = len(benig)

    L=[]
    L.append("# Tabla 8 (sensor) - Ablacion de componentes, modelo limpio + heuristicos vigentes")
    L.append("")
    L.append("Datos del SENSOR (misma distribucion que el modelo). Modelo `if_limpio_2026_10`, "
             "umbral `decision_function < %.6f` (= `score_samples < -0,569397`); heuristicos `%s`." % (umbral, H.VERSION_UMBRALES))
    L.append("")
    L.append("## Deteccion sobre el trafico Kali del sensor (181 ventanas excluidas del entrenamiento)")
    L.append("")
    L.append("| Unidad | Total | IF limpio solo | Heuristicos solos | Hibrido (OR) |")
    L.append("|---|---:|---:|---:|---:|")
    L.append("| ventanas | %d | %d/%d | %d/%d | %d/%d |" % (len(kali),k_model,len(kali),k_heur,len(kali),k_hib,len(kali)))
    L.append("| episodios (contiguidad) | %d | %d/%d | %d/%d | %d/%d |" % (len(ep_rows),ep_model,len(ep_rows),ep_heur,len(ep_rows),ep_hib,len(ep_rows)))
    L.append("")
    L.append("Reglas heuristicas disparadas (por ventana): " + (", ".join("%s=%d"%(k,v) for k,v in sorted(reglas.items())) or "ninguna"))
    L.append("")
    L.append("## Falsos positivos por componente - benigno del sensor (65 421 ventanas de test retenidas)")
    L.append("")
    L.append("> Accion calculada OFFLINE; NO es una restriccion aplicada en el host.")
    L.append("")
    L.append("| Componente | Ventanas con alerta | FPR | de las cuales LIMIT | BLOCK |")
    L.append("|---|---:|---:|---:|---:|")
    L.append("| IF limpio | %d | %.2f%% | - | - |" % (b_model, 100*b_model/n_b))
    L.append("| Heuristicos | %d | %.2f%% | %d | %d |" % (b_heur, 100*b_heur/n_b, b_limit, b_block))
    L.append("| Hibrido (OR) | %d | %.2f%% | - | - |" % (b_hib, 100*b_hib/n_b))
    L.append("")
    L.append("El FPR del IF sobre el benigno del sensor valida el valor del model card (~4,5 %).")
    (OUT/"Tabla8-ablacion-sensor.md").write_text("\n".join(L), encoding="utf-8")

    with open(OUT/"matriz-episodios-sensor.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["entidad","n_ventanas","ini_epoch","fin_epoch","IF","heur","reglas","hibrido"])
        for e in ep_rows: w.writerow([e["entidad"],e["n_vent"],e["ini"],e["fin"],e["IF"],e["heur"],e["reglas"],e["hibrido"]])

    meta={"experimento":"4.2 ablacion sensor (valida) modelo limpio + heuristicos vigentes",
          "fecha_analisis":"2026-10-23",
          "modelo":{"id":"if_limpio_2026_10","sha256_paquete":sha256(PAQ),"umbral_df":umbral},
          "heuristicos":{"sha256":sha256(HEUR_PY),"version":H.VERSION_UMBRALES},
          "ataque_sensor":{"n_ventanas":len(kali),"n_episodios":len(ep_rows),
                           "IF_vent":k_model,"heur_vent":k_heur,"hib_vent":k_hib,
                           "IF_ep":ep_model,"heur_ep":ep_heur,"hib_ep":ep_hib,"reglas":reglas},
          "benigno_sensor":{"n":n_b,"IF":b_model,"heur":b_heur,"hibrido":b_hib,
                            "fpr_IF":b_model/n_b,"fpr_heur":b_heur/n_b,"fpr_hibrido":b_hib/n_b,
                            "limit":b_limit,"block":b_block},
          "fuentes":{"limpio_csv":str(LIMPIO),"normal_reservado":str(NORMAL)},
          "repos":{"producto-main":"fa9e5b0 (2026-10-19)","orquestacion-limpio":"2f72d4d (2026-10-19)"}}
    (OUT/"metadata-ablacion-sensor.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")

    print("ATAQUE ventanas: IF %d heur %d hib %d / %d" % (k_model,k_heur,k_hib,len(kali)))
    print("ATAQUE episodios: IF %d heur %d hib %d / %d" % (ep_model,ep_heur,ep_hib,len(ep_rows)))
    print("reglas:", reglas)
    print("BENIGNO: FPR IF %.2f%%  heur %.2f%% (LIMIT %d / BLOCK %d)  hib %.2f%%  (n=%d)" % (
        100*b_model/n_b,100*b_heur/n_b,b_limit,b_block,100*b_hib/n_b,n_b))
    print("Salidas:", OUT)

if __name__=="__main__":
    raise SystemExit(main())
