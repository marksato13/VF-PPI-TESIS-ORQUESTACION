#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.1 - Figura ROC + PR de ESTA evaluacion (84 ataque + 65421 normal), modelo limpio
y candidatos. Lee curvas.json (coords ROC/PR por modelo) + metricas.json (AUC/AP para
la leyenda). Exporta PNG 300 DPI + SVG. Uso: python figura_roc_pr.py <dir_eval41>
"""
import json, sys, pathlib
d = pathlib.Path(sys.argv[1])
cur = json.loads((d/"curvas.json").read_text(encoding="utf-8"))
met = json.loads((d/"metricas.json").read_text(encoding="utf-8"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

orden = [m for m in cur.keys()]
def destaca(n): return n.startswith("IF limpio")
fig, (axr, axp) = plt.subplots(1, 2, figsize=(12, 5.2))
for n in orden:
    r = cur[n]["roc"]; mm = met.get(n, {})
    lw = 2.6 if destaca(n) else 1.2
    axr.plot(r["fpr"], r["tpr"], lw=lw, label="%s (AUC %.3f)" % (n, mm.get("roc_auc", 0)),
             zorder=5 if destaca(n) else 2)
axr.plot([0,1],[0,1],"--",color="#888",lw=1); axr.set_title("ROC"); axr.set_xlabel("FPR"); axr.set_ylabel("TPR")
axr.legend(fontsize=6.5, loc="lower right"); axr.grid(alpha=0.25)
for n in orden:
    p = cur[n]["pr"]; mm = met.get(n, {})
    lw = 2.6 if destaca(n) else 1.2
    axp.plot(p["recall"], p["precision"], lw=lw, label="%s (AP %.3f)" % (n, mm.get("ap", 0)),
             zorder=5 if destaca(n) else 2)
axp.set_title("Precision-Recall"); axp.set_xlabel("Recall"); axp.set_ylabel("Precision")
axp.legend(fontsize=6.5, loc="upper right"); axp.grid(alpha=0.25)
fig.suptitle("CyberFlow — evaluacion sobre esta red (84 ataque + 65 421 normal)", fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.96])
png = d/"figura-roc-pr.png"
fig.savefig(png, dpi=300); fig.savefig(d/"figura-roc-pr.svg")
print("OK:", png)
