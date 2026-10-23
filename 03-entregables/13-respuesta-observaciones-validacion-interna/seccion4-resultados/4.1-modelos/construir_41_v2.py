#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye (local) TABLA6/7 md+csv, ALFA-F6 md+csv y la figura ROC/PR a resolucion
COMPLETA desde los scores completos. Lee metricas.json + scores-todos-candidatos.csv.gz.
"""
import json, csv, gzip, pathlib
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, average_precision_score
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\_campana\resultados-2026-10-23\eval41\v2")
M = json.loads((D/"metricas.json").read_text(encoding="utf-8"))

# ---------- TABLA 6 ----------
c = M["tabla6_clean"]
def pct(x): return "%.2f %%" % (100*x)
t6 = [["TP", c["TP"], "ventanas de ataque detectadas / 84"],
      ["FP", c["FP"], "ventanas normales marcadas / 65 421"],
      ["TN", c["TN"], "- / 65 421"], ["FN", c["FN"], "- / 84"],
      ["Precision", "%.4f (%s)"%(c["precision"],pct(c["precision"])), "TP/(TP+FP) = 54/3015"],
      ["Recall (TPR)", "%.4f (%s)"%(c["recall"],pct(c["recall"])), "TP/(TP+FN) = 54/84"],
      ["F1", "%.4f"%c["F1"], "2PR/(P+R)"],
      ["FPR", "%.4f (%s)"%(c["FPR"],pct(c["FPR"])), "FP/(FP+TN) = 2961/65421"],
      ["Especificidad", "%.4f (%s)"%(c["specificity"],pct(c["specificity"])), "TN/(TN+FP)"],
      ["ROC-AUC", "%.4f"%c["roc_auc"], "ranking (anomalia = -score_samples)"],
      ["Average Precision (AP)", "%.4f"%c["average_precision"], "sklearn average_precision_score"]]
L6=["# Tabla 6 - IF limpio `if_limpio_2026_10` (umbral score_samples < -0,5693969936322356)","",
    "Clase positiva = ataque (84 ventanas Kali, nota M) vs 65 421 normales (oro=test). **Anomalia estadistica, no ataque confirmado por paquete.** Sumas verificadas: TP+FN=84, TN+FP=65421, total=65505.","",
    "| Indicador | Valor | Numerador/denominador |","|---|---|---|"]
for r in t6: L6.append("| %s | %s | %s |"%(r[0],r[1],r[2]))
L6+=["","## Deteccion por familia (etiqueta PROXY observable de nota M; no ground-truth)","",
     "| Familia | Ventanas | Detectadas | TPR |","|---|---:|---:|---:|"]
pf=M["per_familia_proxy"]
for f in ("HTTP","escaneo","DNS"):
    d=pf[f]; L6.append("| %s | %d | %d | %s |"%(f,d["n"],d["det"],pct(d["det"]/d["n"]) if d["n"] else "-"))
L6.append("| **Total** | **84** | **54** | **64,29 %** |")
(D/"TABLA6.md").write_text("\n".join(L6),encoding="utf-8")
with open(D/"TABLA6.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["indicador","valor","numerador_denominador"])
    for r in t6: w.writerow([r[0], (("%.10f"%c[k]) if False else r[1]), r[2]])

# ---------- TABLA 7 ----------
rows=M["tabla7"]; dup=M["variantes_identicas"]
dup_names=set(n for v in dup.values() for n in v)
L7=["# Tabla 7 - Comparacion de configuraciones (mismas 84 + 65 421 ventanas, mismo etiquetado)","",
    "Precision/Recall/FPR en %; F1/ROC-AUC/AP en [0,1]. Umbral propio de cada modelo (de su manifiesto, precision completa).","",
    "| Configuracion | Entrenamiento | Precision | Recall | F1 | FPR | ROC-AUC | AP |","|---|---|---:|---:|---:|---:|---:|---:|"]
for r in rows:
    nota = " _(= IF uniform, identico)_" if r["modelo"]=="IF exact (lab)" else ""
    L7.append("| %s%s | %s | %s | %s | %.4f | %s | %.4f | %.4f |"%(
        r["modelo"],nota,r["origen"],pct(r["precision"]),pct(r["recall"]),r["F1"],pct(r["FPR"]),r["roc_auc"],r["average_precision"]))
L7+=["","**Lecturas honestas:**",
 "- **El IF limpio NO gana en todas las metricas:** ROC-AUC limpio 0,9247 > contaminado 0,9228, pero **AP contaminado 0,2026 > limpio 0,1858** y FPR contaminado 4,45 % < limpio 4,53 %. Son **equivalentes** (diferencias dentro del ruido de muestra; mismo TP=54, mismo recall 64,3 %). Conclusion: **limpiar la contaminacion NO degrado la deteccion.**",
 "- `IF uniform` e `IF exact` son **identicos** (mismo vector de scores): hay 8 configuraciones distintas, no 9.",
 "- Candidatos de **laboratorio**: recall alto pero **FPR 29-99,6 %** (inservibles en esta red); OCSVM marca el 99,6 % del normal (ROC-AUC 0,455, bajo el azar); LOF ROC-AUC 0,299.",
 "- Es una comparacion de **transferencia** al entorno objetivo (los datos de entrenamiento difieren), **no** una prueba aislada de superioridad del algoritmo IF.",
 "- **Det@FPR5% retirada**: el calculo anterior fijaba el corte sobre los negativos de TEST (fuga); ademas OCSVM/LOF no alcanzan el 5 % por empates. La sensibilidad correcta (corte en validacion) esta en `ALFA-F6`."]
(D/"TABLA7.md").write_text("\n".join(L7),encoding="utf-8")
with open(D/"TABLA7.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["configuracion","origen","precision","recall","F1","FPR","roc_auc","average_precision","umbral","sha256","variante_identica_de"])
    for r in rows:
        w.writerow([r["modelo"],r["origen"],r["precision"],r["recall"],r["F1"],r["FPR"],r["roc_auc"],r["average_precision"],r["umbral"],r["sha256"],
                    "IF uniform (lab)" if r["modelo"]=="IF exact (lab)" else ""])

# ---------- ALFA (F6) ----------
al=M["alfa_sensibilidad"]
La=["# F6 - Sensibilidad a alfa (cortes calculados en VALIDACION, aplicados a TEST; sin reentrenar)","",
    "alfa=0,05 es la configuracion CONGELADA (reproduce el umbral operativo). Los demas son analisis de sensibilidad, no una re-seleccion.","",
    "| alfa | Umbral (score_samples) | FPR observado (test) | Recall | Precision | F1 |","|---:|---:|---:|---:|---:|---:|"]
for a in al:
    La.append("| %s | %.6f | %s | %s | %s | %.4f |"%(a["alfa"],a["umbral"],pct(a["fpr_obs"]),pct(a["recall"]),pct(a["precision"]),a["F1"]))
La+=["","- n validacion = "+str(al[0]["n_val"])+". El umbral de alfa=0,05 (-0,56946) reproduce el operativo (-0,56940); FPR test 4,52 %.",
 "- Bajar alfa recorta FPR **y** recall; subirlo gana poco recall a gran costo de FPR. La literatura puede sustentar el **procedimiento** de calibracion por percentil, no que 0,05 sea optimo para esta red.",
 "- No habia una **meta de aceptacion** de FPR/recall definida de antemano mas alla del objetivo de ~5 % de FPR fijado en validacion; no se inventa una post-hoc."]
(D/"ALFA-F6.md").write_text("\n".join(La),encoding="utf-8")
with open(D/"ALFA-F6.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["alfa","umbral","fpr_obs","recall","precision","F1"])
    for a in al: w.writerow([a["alfa"],a["umbral"],a["fpr_obs"],a["recall"],a["precision"],a["F1"]])

# ---------- FIGURA (scores completos) ----------
with gzip.open(D/"scores-todos-candidatos.csv.gz","rt",encoding="utf-8") as f:
    rd=csv.reader(f); header=next(rd); data=list(rd)
mod_cols=[(i,h.split("::",1)[1]) for i,h in enumerate(header) if h.startswith("score::")]
lab_i=header.index("label")
y=np.array([int(r[lab_i]) for r in data])
prev=y.mean()
estilos=["-","--","-.",":"]
fig,(axr,axp)=plt.subplots(1,2,figsize=(13,5.6))
for k,(ci,nombre) in enumerate(mod_cols):
    s=np.array([float(r[ci]) for r in data]); anom=-s
    fpr,tpr,_=roc_curve(y,anom); rec,prc=None,None
    pr_p,pr_r,_=precision_recall_curve(y,anom)
    clean=nombre.startswith("IF limpio")
    lw=3.0 if clean else 1.3; ls=estilos[k%4]
    axr.plot(fpr,tpr,ls,lw=lw,label="%s (AUC %.3f)"%(nombre,roc_auc_score(y,anom)),zorder=6 if clean else 2)
    axp.plot(pr_r,pr_p,ls,lw=lw,drawstyle="steps-post",label="%s (AP %.3f)"%(nombre,average_precision_score(y,anom)),zorder=6 if clean else 2)
axr.plot([0,1],[0,1],color="#999",lw=1,ls=(0,(1,1)),label="azar")
axr.set_title("ROC"); axr.set_xlabel("FPR"); axr.set_ylabel("TPR"); axr.grid(alpha=.25); axr.legend(fontsize=6,loc="lower right")
axp.axhline(prev,color="#999",lw=1,ls=(0,(1,1)),label="prevalencia %.4f"%prev)
axp.set_title("Precision-Recall"); axp.set_xlabel("Recall"); axp.set_ylabel("Precision"); axp.grid(alpha=.25); axp.legend(fontsize=6,loc="upper right")
fig.suptitle("CyberFlow 4.1 - evaluacion sobre esta red (84 ataque + 65 421 normal) - scores completos",fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig(D/"figura-roc-pr-v2.png",dpi=300); fig.savefig(D/"figura-roc-pr-v2.svg")
print("OK. prevalencia=%.5f modelos=%d"%(prev,len(mod_cols)))
print("figura:",D/"figura-roc-pr-v2.png")
