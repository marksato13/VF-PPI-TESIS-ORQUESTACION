#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.1 - Evaluacion del modelo LIMPIO + comparacion de candidatos sobre el MISMO
conjunto (oro 65421 normal + ataques-nota-M 84 ataque). Corre EN EL SENSOR (lectura).
No reentrena. Alimenta raw a score_samples (Pipelines con escalador dentro -> no doble
escalado). Emite Tabla 6, Tabla 7, metricas.json, curvas (ROC/PR) y scores por ventana.
"""
import json, csv, hashlib, pathlib
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, precision_recall_curve
import joblib

ART = pathlib.Path("/home/m4rk/cyberflow/artifacts")
ORO = ART/"aprendizaje"/"oro"/"oro.csv"
ATA = ART/"aprendizaje"/"ataques"/"ataques-nota-M.csv"
MANIF_LIMPIO = ART/"preliminar"/"limpio-2026-10"/"manifest-if-limpio-2026-10.json"
MANIF_RECAL = ART/"preliminar"/"manifest-if-recalibrado.json"
MANIF_CAND = ART/"model"/"manifest.json"
OUT = pathlib.Path("/tmp/campana-limpio/eval41"); OUT.mkdir(parents=True, exist_ok=True)

def sha(p):
    try: return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    except OSError: return None

man = json.loads(MANIF_LIMPIO.read_text(encoding="utf-8"))
def buscar(o, k):
    if isinstance(o, dict):
        if k in o and isinstance(o[k], list): return o[k]
        for v in o.values():
            r = buscar(v, k)
            if r: return r
    return None
feats = buscar(man, "features")
UMBRAL_LIMPIO = -0.5693969936322356

def thr_recal():
    try:
        m = json.loads(MANIF_RECAL.read_text(encoding="utf-8"))
        def f(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "threshold" and isinstance(v, (int, float)): return float(v)
                    r = f(v)
                    if r is not None: return r
            return None
        return f(m)
    except OSError: return None

def leer(p, label):
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    X = np.asarray([[float(r[c]) for c in feats] for r in rows], dtype=float)
    return rows, X, np.full(len(rows), label, dtype=int)

rn, Xn, yn = leer(ORO, 0)
ra, Xa, ya = leer(ATA, 1)
X = np.vstack([Xn, Xa]); y = np.concatenate([yn, ya])
print("normal", len(Xn), "ataque", len(Xa), "features", len(feats))

def scores(model, M):
    try: return np.asarray(model.score_samples(M), float)
    except Exception:
        try: return np.asarray(model.decision_function(M), float)
        except Exception: return None

MODELOS = [
    ("IF limpio (desplegado)", ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib", "esta red", UMBRAL_LIMPIO),
    ("IF recalibrado (contaminado, respaldo)", ART/"preliminar"/"if_recalibrado_desplegable.joblib", "esta red", -0.568892),
    ("IF scaled (lab)", ART/"model"/"candidates"/"if_scaled_weighted.joblib", "laboratorio", None),
    ("IF primary (lab)", ART/"model"/"candidates"/"if_primary_weighted.joblib", "laboratorio", None),
    ("IF uniform (lab)", ART/"model"/"candidates"/"if_uniform.joblib", "laboratorio", None),
    ("IF exact (lab)", ART/"model"/"candidates"/"if_exact_collapsed.joblib", "laboratorio", None),
    ("OCSVM (lab)", ART/"model"/"candidates"/"ocsvm_scaled.joblib", "laboratorio", None),
    ("LOF (lab)", ART/"model"/"candidates"/"lof_scaled.joblib", "laboratorio", None),
    ("Elliptic Envelope (lab)", ART/"model"/"candidates"/"elliptic_envelope_scaled.joblib", "laboratorio", None),
]

metr = {}; curvas = {}; filas7 = []
scores_clean_norm = scores_clean_att = None
for nombre, ruta, origen, umbral in MODELOS:
    if not ruta.exists():
        print("FALTA", nombre, ruta); continue
    mdl = joblib.load(ruta)
    sn = scores(mdl, Xn); sa = scores(mdl, Xa)
    if sn is None:
        print("sin score", nombre); continue
    anom = np.concatenate([-sn, -sa])
    roc = float(roc_auc_score(y, anom)); ap = float(average_precision_score(y, anom))
    # Det @ FPR 5% : corte en percentil 95 de -sn (normal)
    cut = float(np.quantile(-sn, 0.95))
    det5 = float(np.mean(-sa >= cut)); fpr5 = float(np.mean(-sn >= cut))
    fila = {"modelo": nombre, "origen": origen, "roc_auc": round(roc,4), "ap": round(ap,4),
            "det_fpr5": round(det5,4), "fpr5_real": round(fpr5,4)}
    if umbral is not None:
        yp = (np.concatenate([sn, sa]) < umbral).astype(int)
        tp = int(((y==1)&(yp==1)).sum()); fp = int(((y==0)&(yp==1)).sum())
        tn = int(((y==0)&(yp==0)).sum()); fn = int(((y==1)&(yp==0)).sum())
        prec = tp/(tp+fp) if tp+fp else 0.0; rec = tp/(tp+fn) if tp+fn else 0.0
        f1 = 2*prec*rec/(prec+rec) if prec+rec else 0.0
        fila.update({"umbral": umbral, "TP":tp,"FP":fp,"TN":tn,"FN":fn,
                     "precision":round(prec,4),"recall":round(rec,4),"F1":round(f1,4),
                     "FPR":round(fp/(fp+tn),4)})
    metr[nombre] = fila; filas7.append(fila)
    fpr_c, tpr_c, _ = roc_curve(y, anom); pr_p, pr_r, _ = precision_recall_curve(y, anom)
    def ds(a, n=200):
        a = np.asarray(a);
        if len(a)<=n: return [round(float(x),5) for x in a]
        idx = np.linspace(0, len(a)-1, n).astype(int); return [round(float(a[i]),5) for i in idx]
    curvas[nombre] = {"roc":{"fpr":ds(fpr_c),"tpr":ds(tpr_c)}, "pr":{"recall":ds(pr_r),"precision":ds(pr_p)}}
    if nombre.startswith("IF limpio"):
        scores_clean_norm, scores_clean_att = sn, sa

(OUT/"metricas.json").write_text(json.dumps(metr, indent=2, ensure_ascii=False), encoding="utf-8")
(OUT/"curvas.json").write_text(json.dumps(curvas, ensure_ascii=False), encoding="utf-8")

# Tabla 6 (clean) + Tabla 7
c = metr["IF limpio (desplegado)"]
L6 = ["# Tabla 6 - IF limpio sobre oro (65421 normal) + 84 ataque", "",
      "| TP | FP | TN | FN | Precision | Recall | F1 | FPR | ROC-AUC | AP |",
      "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
      "| %d | %d | %d | %d | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f |" % (
        c["TP"],c["FP"],c["TN"],c["FN"],c["precision"],c["recall"],c["F1"],c["FPR"],c["roc_auc"],c["ap"]),
      "", "AP = average_precision_score (area PR por suma ponderada de recalls, sklearn). Clase positiva = anomalia; score = -score_samples."]
(OUT/"TABLA6.md").write_text("\n".join(L6), encoding="utf-8")

L7 = ["# Tabla 7 - Comparacion de candidatos sobre las MISMAS ventanas (84+65421)", "",
      "| Modelo | Entrenamiento | ROC-AUC | AP | Det@FPR5% | FPR5 real | FPR propio | Recall propio |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
for f in filas7:
    L7.append("| %s | %s | %.4f | %.4f | %.3f | %.3f | %s | %s |" % (
        f["modelo"], f["origen"], f["roc_auc"], f["ap"], f["det_fpr5"], f["fpr5_real"],
        ("%.4f"%f["FPR"]) if "FPR" in f else "-", ("%.4f"%f["recall"]) if "recall" in f else "-"))
L7.append("")
L7.append("Candidatos de laboratorio y el IF de esta red tienen condiciones de entrenamiento distintas:")
L7.append("esto mide TRANSFERENCIA a la red objetivo, no superioridad intrinseca del algoritmo.")
(OUT/"TABLA7.md").write_text("\n".join(L7), encoding="utf-8")

# scores por ventana del modelo limpio
with open(OUT/"scores-clean-por-ventana.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["campaign_id","window_end_utc","label","score_samples","umbral","decision"])
    for r,s in zip(rn, scores_clean_norm):
        w.writerow([r.get("campaign_id"),r.get("window_end_utc"),0,round(float(s),6),UMBRAL_LIMPIO, "ALERT" if s<UMBRAL_LIMPIO else "PERMIT"])
    for r,s in zip(ra, scores_clean_att):
        w.writerow([r.get("campaign_id"),r.get("window_end_utc"),1,round(float(s),6),UMBRAL_LIMPIO, "ALERT" if s<UMBRAL_LIMPIO else "PERMIT"])

print("\n=== TABLA 7 ===")
print("\n".join(L7))
print("\n=== TABLA 6 ===")
print("\n".join(L6[:6]))
print("\nsha oro", sha(ORO)[:16], "sha ataques", sha(ATA)[:16])
print("OUT", OUT)
