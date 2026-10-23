#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cierra los 3 flecos de 4.1 (corre EN EL SENSOR, lectura):
 1) Deteccion por familia del MODELO LIMPIO, con el criterio OBSERVABLE de la nota M
    (errata): DNS si dns_query_count_60s>0; si no, HTTP si http_request_count_60s>0;
    en otro caso escaneo.
 2) Tabla 7 COMPLETA: cada candidato a su umbral propio -> Precision/Recall/F1/FPR
    (+ ROC-AUC, AP), sobre las MISMAS 84+65421 ventanas.
 3) Hashes (joblibs) + versiones + umbrales, en un auxiliar.
"""
import json, csv, hashlib, pathlib
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
import joblib, sklearn, numpy

ART = pathlib.Path("/home/m4rk/cyberflow/artifacts")
ORO = ART/"aprendizaje"/"oro"/"oro.csv"
ATA = ART/"aprendizaje"/"ataques"/"ataques-nota-M.csv"
MANIF_LIMPIO = ART/"preliminar"/"limpio-2026-10"/"manifest-if-limpio-2026-10.json"
MANIF_CAND = ART/"model"/"manifest.json"
OUT = pathlib.Path("/tmp/campana-limpio/eval41"); OUT.mkdir(parents=True, exist_ok=True)
U_LIMPIO = -0.5693969936322356; U_RECAL = -0.568892

man = json.loads(MANIF_LIMPIO.read_text(encoding="utf-8"))
def buscar(o,k):
    if isinstance(o,dict):
        if k in o and isinstance(o[k],list): return o[k]
        for v in o.values():
            r=buscar(v,k)
            if r: return r
    return None
feats = buscar(man,"features")
cand = json.loads(MANIF_CAND.read_text(encoding="utf-8"))
THR = {k: v["threshold_used"] for k,v in cand.get("evaluation",{}).items() if isinstance(v,dict) and "threshold_used" in v}
MH = cand.get("model_hashes",{})

def leer(p,label):
    rows=list(csv.DictReader(open(p,newline="",encoding="utf-8")))
    X=np.asarray([[float(r[c]) for c in feats] for r in rows],float)
    return rows, X, np.full(len(rows),label,int)
rn,Xn,yn = leer(ORO,0); ra,Xa,ya = leer(ATA,1)
X=np.vstack([Xn,Xa]); y=np.concatenate([yn,ya])

def sc_samples(m,M):
    try: return np.asarray(m.score_samples(M),float), "score_samples"
    except Exception:
        try: return np.asarray(m.decision_function(M),float), "decision_function"
        except Exception: return None,None

def sha(p):
    try: return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    except OSError: return None

# ---- FLECO 1: familia (criterio observable nota M) ----
def familia(r):
    # Prioridad de la nota M (errata): HTTP primero, luego DNS, resto escaneo.
    if float(r.get("http_request_count_60s",0) or 0) > 0: return "HTTP"
    if float(r.get("dns_query_count_60s",0) or 0) > 0: return "DNS"
    return "escaneo"
fam_lbl = [familia(r) for r in ra]
limpio = joblib.load(ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib")
sa_limpio,_ = sc_samples(limpio, Xa)
det_limpio = (sa_limpio < U_LIMPIO)
fam = {}
for f,d in zip(fam_lbl, det_limpio):
    fam.setdefault(f,{"n":0,"det":0}); fam[f]["n"]+=1; fam[f]["det"]+=int(d)
famL = ["# 4.1 (fleco 1) - Deteccion por familia del MODELO LIMPIO", "",
        "Criterio OBSERVABLE (nota M, errata): DNS si dns_query_count_60s>0; si no HTTP si http_request_count_60s>0; resto escaneo.", "",
        "| Familia | Ventanas | Detectadas (IF limpio) | TPR |", "|---|---:|---:|---:|"]
for f in ("HTTP","escaneo","DNS"):
    if f in fam:
        d=fam[f]; famL.append("| %s | %d | %d | %.1f%% |"%(f,d["n"],d["det"],100*d["det"]/d["n"] if d["n"] else 0))
tot_n=sum(d["n"] for d in fam.values()); tot_d=sum(d["det"] for d in fam.values())
famL.append("| **Total** | **%d** | **%d** | **%.1f%%** |"%(tot_n,tot_d,100*tot_d/tot_n))
famL.append(""); famL.append("Contraste nota M (modelo contaminado, mismo criterio): HTTP 35/43 - escaneo 19/33 - DNS 0/8.")
(OUT/"DETECCION-POR-FAMILIA-limpio.md").write_text("\n".join(famL),encoding="utf-8")
(OUT/"deteccion-por-familia.json").write_text(json.dumps({"criterio":"observable nota M","familias":fam},indent=2,ensure_ascii=False),encoding="utf-8")

# ---- FLECO 2: Tabla 7 completa (umbral propio) ----
MODELOS = [
    ("IF limpio (desplegado)","esta red", ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib", U_LIMPIO),
    ("IF recalibrado (contaminado)","esta red", ART/"preliminar"/"if_recalibrado_desplegable.joblib", U_RECAL),
    ("IF scaled (lab)","laboratorio", ART/"model"/"candidates"/"if_scaled_weighted.joblib", THR.get("if_scaled_weighted")),
    ("IF primary (lab)","laboratorio", ART/"model"/"candidates"/"if_primary_weighted.joblib", THR.get("if_primary_weighted")),
    ("IF uniform (lab)","laboratorio", ART/"model"/"candidates"/"if_uniform.joblib", THR.get("if_uniform")),
    ("IF exact (lab)","laboratorio", ART/"model"/"candidates"/"if_exact_collapsed.joblib", THR.get("if_exact_collapsed")),
    ("OCSVM (lab)","laboratorio", ART/"model"/"candidates"/"ocsvm_scaled.joblib", THR.get("ocsvm_scaled")),
    ("LOF (lab)","laboratorio", ART/"model"/"candidates"/"lof_scaled.joblib", THR.get("lof_scaled")),
    ("Elliptic Envelope (lab)","laboratorio", ART/"model"/"candidates"/"elliptic_envelope_scaled.joblib", THR.get("elliptic_envelope_scaled")),
]
filas=[]; hashes={}
for nombre,origen,ruta,umbral in MODELOS:
    if not ruta.exists(): continue
    m=joblib.load(ruta); ss,fn = sc_samples(m,X)
    if ss is None: continue
    hashes[nombre]={"ruta":str(ruta),"sha256":sha(ruta),"score_fn":fn,"umbral":umbral}
    anom=-ss; roc=float(roc_auc_score(y,anom)); ap=float(average_precision_score(y,anom))
    row={"modelo":nombre,"origen":origen,"roc_auc":round(roc,4),"ap":round(ap,4)}
    if umbral is not None:
        yp=(ss<umbral).astype(int)
        tp=int(((y==1)&(yp==1)).sum()); fp=int(((y==0)&(yp==1)).sum())
        tn=int(((y==0)&(yp==0)).sum()); fn2=int(((y==1)&(yp==0)).sum())
        prec=tp/(tp+fp) if tp+fp else 0.0; rec=tp/(tp+fn2) if tp+fn2 else 0.0
        f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
        row.update({"TP":tp,"FP":fp,"TN":tn,"FN":fn2,"precision":round(prec,4),"recall":round(rec,4),
                    "F1":round(f1,4),"FPR":round(fp/(fp+tn),4)})
    filas.append(row)
cols=["modelo","origen","TP","FP","TN","FN","precision","recall","F1","FPR","roc_auc","ap"]
with open(OUT/"tabla7-completa.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
    for r in filas: w.writerow({c:r.get(c,"") for c in cols})
L=["# 4.1 (fleco 2) - Tabla 7 completa (cada modelo a su umbral propio; mismas 84+65421)","",
   "| Modelo | Entrenamiento | Precision | Recall | F1 | FPR | ROC-AUC | AP |","|---|---|---:|---:|---:|---:|---:|---:|"]
def g(r,k): return ("%.4f"%r[k]) if k in r else "-"
for r in filas:
    L.append("| %s | %s | %s | %s | %s | %s | %.4f | %.4f |"%(r["modelo"],r["origen"],g(r,"precision"),g(r,"recall"),g(r,"F1"),g(r,"FPR"),r["roc_auc"],r["ap"]))
L.append(""); L.append("Nota: precision/F1 bajos por el desbalance extremo (84 vs 65421). Candidatos de lab vs IF de esta red = transferencia, no superioridad intrinseca.")
(OUT/"TABLA7-completa.md").write_text("\n".join(L),encoding="utf-8")

# ---- FLECO 3: hashes + deps ----
aux={"versiones":{"scikit_learn":sklearn.__version__,"joblib":joblib.__version__,"numpy":numpy.__version__,
                  "manifest_cand_scikit_learn":cand.get("scikit_learn"),"manifest_cand_numpy":cand.get("numpy")},
     "umbrales":{m[0]:m[3] for m in MODELOS},
     "hashes_modelos":hashes, "model_hashes_manifest":MH,
     "datos":{"oro":{"ruta":str(ORO),"sha256":sha(ORO),"n":len(rn)},
              "ataques":{"ruta":str(ATA),"sha256":sha(ATA),"n":len(ra)}},
     "features_orden":feats,
     "comando":"python3 eval_4_1.py && python3 cerrar_41.py (en el sensor, venv py3.14/sklearn1.9.0)"}
(OUT/"hashes-deps-aux.json").write_text(json.dumps(aux,indent=2,ensure_ascii=False),encoding="utf-8")

print("== FAMILIA (limpio) =="); print("\n".join(famL[4:12]))
print("\n== TABLA 7 completa =="); print("\n".join(L[:14]))
print("\nsklearn",sklearn.__version__,"| n_familias",{f:fam[f]["n"] for f in fam})
print("OUT",OUT)
