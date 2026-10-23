#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 - Reproduce TODAS las metricas DESDE el respaldo gz (no desde memoria) y compara
con metricas.json. Comprueba el efecto del redondeo a 6 decimales (empates, AP, AUC)."""
import json, csv, gzip, pathlib
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
D=pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\_campana\resultados-2026-10-23\eval41\v2")
M=json.loads((D/"metricas.json").read_text(encoding="utf-8"))
thr={r["modelo"]:r["umbral"] for r in M["tabla7"]}
with gzip.open(D/"scores-todos-candidatos-full.csv.gz","rt",encoding="utf-8") as f:
    rd=csv.reader(f); H=next(rd); rows=list(rd)
li=H.index("label"); y=np.array([int(r[li]) for r in rows]); idx=H.index("idx")
cols={h.split("::",1)[1]:i for i,h in enumerate(H) if h.startswith("score::")}
# integridad
ids=[r[idx] for r in rows]
print("filas",len(rows),"idx_unicos",len(set(ids)),"pos",int(y.sum()),"neg",int((y==0).sum()))
nonfinite=0
rep={}; disc=[]
for nombre,ci in cols.items():
    s=np.array([float(r[ci]) for r in rows]); nonfinite+=int((~np.isfinite(s)).sum())
    u=thr[nombre]; yp=(s<u).astype(int); anom=-s
    tp=int(((y==1)&(yp==1)).sum()); fp=int(((y==0)&(yp==1)).sum()); tn=int(((y==0)&(yp==0)).sum()); fn=int(((y==1)&(yp==0)).sum())
    prec=tp/(tp+fp) if tp+fp else 0; rec=tp/(tp+fn) if tp+fn else 0; f1=2*prec*rec/(prec+rec) if prec+rec else 0
    fpr=fp/(fp+tn) if fp+tn else 0; roc=float(roc_auc_score(y,anom)); ap=float(average_precision_score(y,anom))
    rep[nombre]=dict(TP=tp,FP=fp,TN=tn,FN=fn,precision=prec,recall=rec,F1=f1,FPR=fpr,roc_auc=roc,average_precision=ap)
    orig=next((x for x in M["tabla7"] if x["modelo"]==nombre),{})
    for k in ("TP","FP","roc_auc","average_precision"):
        if k in orig:
            d=abs(rep[nombre][k]-orig[k])
            if (k in ("TP","FP") and d!=0) or (k in ("roc_auc","average_precision") and d>5e-4):
                disc.append("%s.%s respaldo=%s metricas.json=%s"%(nombre,k,rep[nombre][k],orig[k]))
print("no_finitos",nonfinite)
print("discrepancias respaldo-vs-metricas.json:", disc if disc else "NINGUNA (coinciden)")
# empates en el umbral (6 decimales): cuantos scores == umbral redondeado
for nombre,ci in list(cols.items())[:2]:
    s=np.array([float(r[ci]) for r in rows]); u=thr[nombre]
    ties=int(np.sum(np.isclose(s,round(u,6),atol=5e-7)))
    print("empates~umbral %s: %d"%(nombre,ties))
(D/"p2-reproduccion.json").write_text(json.dumps({"filas":len(rows),"idx_unicos":len(set(ids)),"no_finitos":nonfinite,"discrepancias":disc,"recomputado":rep},indent=2,ensure_ascii=False,default=float),encoding="utf-8")
print("OK ->",D/"p2-reproduccion.json")
