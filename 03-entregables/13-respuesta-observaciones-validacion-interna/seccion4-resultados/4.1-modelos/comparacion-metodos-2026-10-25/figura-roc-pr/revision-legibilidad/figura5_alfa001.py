#!/usr/bin/env python3
"""Figura con curvas ROC y precision-recall completas (0-1) + puntos operativos de alfa = 0,01.

Reutiliza SIN cambios: curvas-roc.csv / curvas-pr.csv (hash verificado), las puntuaciones congeladas
salidas/puntuaciones-<METODO>.csv.gz (hash del MANIFIESTO-COMPARACION.json) y la configuracion grafica de
generar.py (principal): 18 x 10 cm, DejaVu Sans 8/9 pt, linea 1,05 pt, rejilla, leyendas bajo cada panel.
Umbral alfa=0,01 = cuantil 0,99 (lineal) de la validacion de cada modelo; anomalia si puntuacion > umbral
(mayor puntuacion = mas anomalo). No reentrena, no re-puntua, no toca principal.*, ampliacion.*, tablas ni Word.
Salida: figura5-alfa001.{png,svg,pdf}, figura5-alfa001-puntos.csv, MANIFIESTO-FIGURA5-ALFA001.json.
"""
import csv, datetime, hashlib, importlib.util, io, json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("amp", HERE / "ampliacion_alfa001.py")
amp = importlib.util.module_from_spec(spec); spec.loader.exec_module(amp)
METHODS, NAMES, COLORS, STYLES = amp.METHODS, amp.NAMES, amp.COLORS, amp.STYLES
REF_AUC_AP, PREVAL = amp.REF_AUC_AP, amp.PREVAL
MK, MS, MW = "^", 5.2, 0.9


def dibujar(roc, pr, puntos):
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8, "axes.linewidth": 0.65,
        "lines.linewidth": 1.05, "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "path.simplify": False,
        "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white",
        "svg.hashsalt": "cyberflow-figura5-alfa001"})
    fig = plt.figure(figsize=(18 / 2.54, 10.0 / 2.54), dpi=150)
    pos = [[0.085, 0.365, 0.385, 0.565], [0.595, 0.365, 0.385, 0.565]]
    axs = [fig.add_axes(p) for p in pos]
    hroc, hpr = [], []
    for m in METHODS:
        col, st = COLORS[m], STYLES[m]
        auc, ap = REF_AUC_AP[m]
        l0, = axs[0].plot(roc[m]["fpr"], roc[m]["tpr"], color=col, linestyle=st,
                          label="%s  (ROC-AUC = %s)" % (NAMES[m], ("%.4f" % auc).replace(".", ",")))
        l1, = axs[1].step(pr[m]["recall"], pr[m]["precision"], where="post", color=col, linestyle=st,
                          label="%s  (AP = %s)" % (NAMES[m], ("%.4f" % ap).replace(".", ",")))
        hroc.append(l0); hpr.append(l1)
    diag, = axs[0].plot([0, 1], [0, 1], color="0.50", linewidth=0.8, linestyle=(0, (3, 3)),
                        label="Referencia aleatoria", zorder=0)
    hroc.append(diag)
    prev = axs[1].axhline(PREVAL, color="0.40", linewidth=0.8, linestyle=(0, (3, 3)),
                          label="Prevalencia: 0,1282 %", zorder=5)
    hpr.append(prev)
    for m in METHODS:   # marcadores encima de las curvas
        p = puntos[(m, 0.01)]
        for ax, x, y in ((axs[0], p["roc_x"], p["roc_y"]), (axs[1], p["pr_x"], p["pr_y"])):
            ax.plot([x], [y], linestyle="none", marker=MK, markersize=MS, markerfacecolor="white",
                    markeredgecolor=COLORS[m], markeredgewidth=MW, zorder=7)
    for ax, t in zip(axs, ("(a) Curvas ROC", "(b) Curvas precisión–recall")):
        ax.set(xlim=(0, 1), ylim=(0, 1), xticks=np.linspace(0, 1, 6), yticks=np.linspace(0, 1, 6))
        ax.set_title(t, loc="left", pad=9)
        ax.grid(True, color="0.91", linewidth=0.5, zorder=0)
        ax.tick_params(length=3, width=0.6, pad=3)
        fmt = FuncFormatter(lambda v, _: ("%g" % v).replace(".", ","))
        ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    axs[0].set_xlabel("Tasa de falsos positivos", labelpad=5); axs[0].set_ylabel("Tasa de verdaderos positivos", labelpad=5)
    axs[1].set_xlabel("Recall", labelpad=5); axs[1].set_ylabel("Precisión", labelpad=5)
    legs = []
    for x, lines in zip((0.085, 0.595), (hroc, hpr)):
        legs.append(fig.legend(handles=lines, loc="upper left", bbox_to_anchor=(x, 0.255), frameon=False,
                               handlelength=2.9, handletextpad=0.65, borderaxespad=0, labelspacing=0.32))
    simb = Line2D([], [], color="0.2", marker=MK, markersize=MS, markeredgewidth=MW, markerfacecolor="white",
                  linestyle="none", label="α = 0,01")
    # leyenda de un solo simbolo en zonas vacias de cada panel (no mueve nada de lo existente)
    inroc = axs[0].legend(handles=[simb], loc="lower right", frameon=True, framealpha=1, edgecolor="0.85",
                          fancybox=False, borderpad=0.5, handletextpad=0.4, borderaxespad=0.6)
    inpr = axs[1].legend(handles=[simb], loc="upper right", frameon=True, framealpha=1, edgecolor="0.85",
                         fancybox=False, borderpad=0.5, handletextpad=0.4, borderaxespad=0.6)
    for lg in (inroc, inpr):
        lg.set_zorder(8)
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    fuera = [a.get_text() for a in fig.findobj(Text) if a.get_visible() and a.get_text()
             and (a.get_window_extent(rend).x0 < -0.5 or a.get_window_extent(rend).y0 < -0.5
                  or a.get_window_extent(rend).x1 > fig.bbox.x1 + 0.5 or a.get_window_extent(rend).y1 > fig.bbox.y1 + 0.5)]
    assert not fuera, "texto fuera del lienzo: %s" % fuera
    for lg in legs:
        assert lg.get_window_extent(rend).y1 < axs[0].get_window_extent(rend).y0 - 20, "leyenda invade panel"
    assert not legs[0].get_window_extent(rend).overlaps(legs[1].get_window_extent(rend)), "leyendas solapadas"
    # el recuadro del simbolo no debe tapar ninguna curva: se comprueba contra los vertices de cada curva
    for ax, lg, xs_ys in ((axs[0], inroc, [(roc[m]["fpr"], roc[m]["tpr"]) for m in METHODS]),
                          (axs[1], inpr, [(pr[m]["recall"], pr[m]["precision"]) for m in METHODS])):
        bb = lg.get_window_extent(rend)
        for x, y in xs_ys:
            pts = ax.transData.transform(np.c_[x, y])
            dentro = (pts[:, 0] > bb.x0) & (pts[:, 0] < bb.x1) & (pts[:, 1] > bb.y0) & (pts[:, 1] < bb.y1)
            assert not dentro.any(), "simbolo tapa vertices: %s" % (np.c_[x, y][dentro][:5].tolist(),)
    base = HERE / "figura5-alfa001"
    for ext in ("png", "svg", "pdf"):
        buf = io.BytesIO()
        meta = {"Date": None, "Creator": "CyberFlow; figura 5 alfa 0,01"} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None, "Creator": "CyberFlow; figura 5 alfa 0,01"} if ext == "pdf" else None)
        fig.savefig(buf, format=ext, dpi=600, metadata=meta)
        raw = buf.getvalue()
        if ext == "svg":
            raw = ("\n".join(l.rstrip() for l in raw.decode("utf-8").splitlines()) + "\n").encode("utf-8")
        amp.write_bytes(str(base) + "." + ext, raw)
    plt.close(fig)
    with Image.open(io.BytesIO(amp.read_bytes(str(base) + ".png"))) as im:
        return {"png_dpi": im.info.get("dpi", (0, 0))[0], "png_size": list(im.size), "size_cm": [18, 10.0]}


def main():
    roc, pr, puntos, man = amp.cargar()
    info = dibujar(roc, pr, puntos)
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n")
    w.writerow(["metodo", "alfa", "FPR", "TPR_recall", "precision", "TP", "FP", "TN", "FN", "umbral_anomalia"])
    for m in METHODS:
        p = puntos[(m, 0.01)]
        w.writerow([m, 0.01, repr(p["roc_x"]), repr(p["roc_y"]), repr(p["pr_y"]), p["TP"], p["FP"], p["TN"], p["FN"], p["umbral"]])
    amp.write_text(HERE / "figura5-alfa001-puntos.csv", buf.getvalue())
    salidas = ["figura5-alfa001.png", "figura5-alfa001.svg", "figura5-alfa001.pdf", "figura5-alfa001-puntos.csv", "figura5_alfa001.py"]
    manc = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "proposito": "Figura 5 (curvas completas ROC y PR) con los puntos operativos de alfa=0,01. Curvas, puntuaciones, "
                         "umbrales y procedimiento sin cambios; principal.*, ampliacion.*, tablas y Word intactos.",
            "entradas_verificadas_sha256": {**amp.H_CURVAS, "puntos.csv": amp.H_PUNTOS,
                **{("salidas/puntuaciones-%s.csv.gz" % m): man["salidas_sha256"]["salidas/puntuaciones-%s.csv.gz" % m] for m in METHODS}},
            "alfa_0.01_conteos_reproducidos": {m: dict(zip(("TP", "FP", "TN", "FN"), amp.REF_01[m])) for m in METHODS},
            "render": info, "salidas_sha256_lf": {n: amp.sha_lf(HERE / n) for n in salidas}}
    amp.write_text(HERE / "MANIFIESTO-FIGURA5-ALFA001.json", json.dumps(manc, indent=2, ensure_ascii=False) + "\n")
    print("render:", info)
    for m in METHODS:
        p = puntos[(m, 0.01)]
        print("  %-16s FPR=%.4f %%  recall=%.4f %%  prec=%.4f %%  TP=%d FP=%d umbral=%s" % (
            m, 100 * p["roc_x"], 100 * p["roc_y"], 100 * p["pr_y"], p["TP"], p["FP"], p["umbral"]))


if __name__ == "__main__":
    main()
