#!/usr/bin/env python3
"""Figura 5 (ampliación ROC y PR): añade α = 0,01 conservando α = 0,05 y 0,03.

Reutiliza, con hash verificado:
  - curvas-roc.csv / curvas-pr.csv (carpeta padre): curvas COMPLETAS por modelo (no cambian).
  - puntos.csv (= puntos-operativos.csv): puntos operativos de α=0,05 (○) y 0,03 (◇), según Tablas 7-a/7-b.
  - salidas/puntuaciones-<METODO>.csv.gz: para calibrar α=0,01 (△) por modelo con el MISMO protocolo
    (umbral = cuantil 1−α lineal de la validación de cada modelo; anomalía si puntuación > umbral).
No reentrena, no re-puntúa, no suaviza, no modifica scores, curvas, tablas, Figura 4 (principal.*),
Word, modelos ni configuración. Solo actualiza ampliacion.{png,svg,pdf} y sus previsualizaciones zoom.

Uso: python ampliacion_alfa001.py   (la ruta larga de Windows se maneja internamente).
"""
import csv, gzip, hashlib, io, json, datetime, os, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
from PIL import Image
import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
PADRE = HERE.parent
COMP = PADRE.parent
SAL = COMP / "salidas"
METHODS = ["IF", "OCSVM", "LOF", "EllipticEnvelope", "PCA"]
NAMES = {m: ("Elliptic Envelope" if m == "EllipticEnvelope" else m) for m in METHODS}
COLORS = {"IF": "#0072B2", "OCSVM": "#D55E00", "LOF": "#009E73", "EllipticEnvelope": "#CC79A7", "PCA": "#E69F00"}
STYLES = {"IF": "-", "OCSVM": (0, (4, 2)), "LOF": (0, (1.2, 1.8)), "EllipticEnvelope": (0, (5, 2, 1, 2)), "PCA": (0, (8, 2.5))}
ALPHA_MARKERS = [(0.05, "o", 4.2), (0.03, "D", 3.2), (0.01, "^", 4.6)]
N_NOR, N_ATA = 65421, 84
PREVAL = 84 / 65505
H_CURVAS = {"curvas-roc.csv": "08ebcd74e084efc6348e6c56e7b336a40a2edbbeedfa89898589ff2c76ecb4a8",
            "curvas-pr.csv": "e760a2a1249d54b6776df5ae2daebc0d73e0407ff4490fdb9146b5b592b9ef2f"}
H_PUNTOS = "0d26e881fec105bc071f5ffb9e474f77e004c604f1e32ac200877f7e24e98220"
REF_01 = {"IF": (50, 567, 64854, 34), "OCSVM": (57, 708, 64713, 27), "LOF": (36, 975, 64446, 48),
          "EllipticEnvelope": (40, 570, 64851, 44), "PCA": (67, 825, 64596, 17)}
REF_AUC_AP = {"IF": (0.9247265513258084, 0.18580688397625872), "OCSVM": (0.869071457322936, 0.6356616971916291),
              "LOF": (0.9762796422584565, 0.029066072188399145), "EllipticEnvelope": (0.9179326428604184, 0.3811037448703374),
              "PCA": (0.9486616355167738, 0.5944055724226315)}


def LP(p):
    s = str(pathlib.Path(p).absolute())
    return ("\\\\?\\" + s) if os.name == "nt" and not s.startswith("\\\\?\\") else s


def sha(p):
    h = hashlib.sha256()
    with open(LP(p), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_text(p):
    with open(LP(p), "r", encoding="utf-8") as f:
        return f.read()


def write_text(p, txt):
    with open(LP(p), "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)


def write_bytes(p, b):
    with open(LP(p), "wb") as f:
        f.write(b)


def read_bytes(p):
    with open(LP(p), "rb") as f:
        return f.read()


def leer(p):
    op = gzip.open if str(p).endswith(".gz") else open
    with op(LP(p), "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha_lf(p):
    b = read_bytes(p)
    if pathlib.Path(p).suffix.lower() in (".svg", ".csv", ".py", ".json", ".md"):
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def cargar():
    from sklearn.metrics import roc_auc_score, average_precision_score
    for n, h in H_CURVAS.items():
        assert sha(PADRE / n) == h, "hash de curva distinto: %s" % n
    assert sha(HERE / "puntos.csv") == H_PUNTOS, "puntos.csv no coincide con puntos-operativos.csv"
    man = json.loads(read_text(COMP / "MANIFIESTO-COMPARACION.json"))

    roc = {m: {"fpr": [], "tpr": []} for m in METHODS}
    for r in leer(PADRE / "curvas-roc.csv"):
        roc[r["metodo"]]["fpr"].append(float(r["FPR"])); roc[r["metodo"]]["tpr"].append(float(r["TPR"]))
    pr = {m: {"recall": [], "precision": []} for m in METHODS}
    for r in leer(PADRE / "curvas-pr.csv"):
        pr[r["metodo"]]["recall"].append(float(r["recall"])); pr[r["metodo"]]["precision"].append(float(r["precision"]))

    puntos = {}
    for r in leer(HERE / "puntos.csv"):
        a = float(r["alfa"])
        puntos[(r["metodo"], a)] = dict(TP=int(r["TP"]), FP=int(r["FP"]), TN=int(r["TN"]), FN=int(r["FN"]),
                                        roc_x=float(r["FPR_prueba"]), roc_y=float(r["recall"]), pr_x=float(r["recall"]),
                                        pr_y=float(r["precision"]), umbral=r["umbral_anomalia"])
    for m in METHODS:
        p = SAL / ("puntuaciones-%s.csv.gz" % m)
        assert sha(p) == man["salidas_sha256"]["salidas/puntuaciones-%s.csv.gz" % m], "puntuaciones %s" % m
        rows = leer(p)
        sv = np.array([float(r["puntuacion_anomalia"]) for r in rows if r["conjunto"] == "validacion"])
        sn = np.array([float(r["puntuacion_anomalia"]) for r in rows if r["conjunto"] == "prueba_normal"])
        sa = np.array([float(r["puntuacion_anomalia"]) for r in rows if r["conjunto"] == "ataque"])
        assert (len(sv), len(sn), len(sa)) == (65553, N_NOR, N_ATA), m
        thr = float(np.quantile(sv, 0.99, method="linear"))
        tp = int(np.sum(sa > thr)); fn = N_ATA - tp; fp = int(np.sum(sn > thr)); tn = N_NOR - fp
        assert (tp, fp, tn, fn) == REF_01[m], "α=0,01 no reproduce conteos en %s: %s" % (m, (tp, fp, tn, fn))
        y = np.r_[np.zeros(N_NOR), np.ones(N_ATA)]; sc = np.r_[sn, sa]
        auc = float(roc_auc_score(y, sc)); ap = float(average_precision_score(y, sc))
        assert abs(auc - REF_AUC_AP[m][0]) < 1e-9 and abs(ap - REF_AUC_AP[m][1]) < 1e-9, "AUC/AP %s" % m
        puntos[(m, 0.01)] = dict(TP=tp, FP=fp, TN=tn, FN=fn, roc_x=fp / N_NOR, roc_y=tp / N_ATA,
                                 pr_x=tp / N_ATA, pr_y=tp / (tp + fp), umbral=repr(thr))
    return roc, pr, puntos, man


def dibujar(roc, pr, puntos):
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8, "axes.linewidth": 0.65,
        "lines.linewidth": 1.05, "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "path.simplify": False,
        "svg.fonttype": "none", "pdf.fonttype": 42, "savefig.facecolor": "white"})
    H = 12.9
    fig = plt.figure(figsize=(18 / 2.54, H / 2.54), dpi=150)
    pos = [[0.085, 0.44, 0.385, 0.50], [0.595, 0.44, 0.385, 0.50]]
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
        for a, mk, sz in ALPHA_MARKERS:
            p = puntos[(m, a)]
            axs[0].plot([p["roc_x"]], [p["roc_y"]], linestyle="none", marker=mk, markersize=sz,
                        markerfacecolor="none", markeredgecolor=col, markeredgewidth=0.8, zorder=6)
            axs[1].plot([p["pr_x"]], [p["pr_y"]], linestyle="none", marker=mk, markersize=sz,
                        markerfacecolor="none", markeredgecolor=col, markeredgewidth=0.8, zorder=6)
    axs[0].set(xlim=(0, 0.065), ylim=(0.40, 1.0), xticks=(0, 0.02, 0.04, 0.06), yticks=(0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0))
    axs[1].set(xlim=(0.40, 0.98), ylim=(0, 0.09), xticks=(0.4, 0.5, 0.6, 0.7, 0.8, 0.9), yticks=(0, 0.02, 0.04, 0.06, 0.08))
    prev = axs[1].axhline(PREVAL, color="0.40", linewidth=0.8, linestyle=(0, (3, 3)), label="Prevalencia: 0,1282 %", zorder=5)
    hpr.append(prev)
    for ax, t in zip(axs, ("(a) Ampliación ROC", "(b) Ampliación precisión–recall")):
        ax.set_title(t, loc="left", pad=9)
        ax.grid(True, color="0.91", linewidth=0.5, zorder=0)
        ax.tick_params(length=3, width=0.6, pad=3)
        fmt = FuncFormatter(lambda v, _: ("%g" % v).replace(".", ","))
        ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    axs[0].set_xlabel("Tasa de falsos positivos", labelpad=5); axs[0].set_ylabel("Tasa de verdaderos positivos", labelpad=5)
    axs[1].set_xlabel("Recall", labelpad=5); axs[1].set_ylabel("Precisión", labelpad=5)
    legs = []
    for x, lines in zip((0.085, 0.595), (hroc, hpr)):
        legs.append(fig.legend(handles=lines, loc="upper left", bbox_to_anchor=(x, 0.355), frameon=False,
                               handlelength=2.9, handletextpad=0.65, borderaxespad=0, labelspacing=0.32))
    nota1 = fig.text(0.085, 0.122, "ROC-AUC y AP corresponden a las curvas completas.", fontsize=8, va="center")
    nota2 = fig.text(0.085, 0.084, "Configuraciones de validación (umbral = cuantil 1−α):", fontsize=8, va="center")
    simbolos = [Line2D([], [], color="0.2", marker=mk, markersize=sz, markeredgewidth=0.8, markerfacecolor="none",
                       linestyle="none", label=("α = %g" % a).replace(".", ",")) for a, mk, sz in ALPHA_MARKERS]
    legs.append(fig.legend(handles=simbolos, loc="lower center", bbox_to_anchor=(0.5, 0.006), frameon=False,
                           ncol=3, handletextpad=0.5, columnspacing=2.2, borderaxespad=0))
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    fuera = [a.get_text() for a in fig.findobj(Text) if a.get_visible() and a.get_text()
             and (a.get_window_extent(rend).x0 < -0.5 or a.get_window_extent(rend).y0 < -0.5
                  or a.get_window_extent(rend).x1 > fig.bbox.x1 + 0.5 or a.get_window_extent(rend).y1 > fig.bbox.y1 + 0.5)]
    assert not fuera, "texto fuera del lienzo: %s" % fuera
    for lg in legs[:2]:
        assert lg.get_window_extent(rend).y1 < axs[0].get_window_extent(rend).y0 - 12, "leyenda invade panel"
    assert not legs[0].get_window_extent(rend).overlaps(legs[1].get_window_extent(rend)), "leyendas de detectores se solapan"
    for footer in (nota1, nota2):
        fb = footer.get_window_extent(rend)
        assert not legs[2].get_window_extent(rend).overlaps(fb), "leyenda alfa invade una nota"
        for lg in legs[:2]:
            assert not lg.get_window_extent(rend).overlaps(fb), "leyenda de detectores invade una nota"
    for m in METHODS:
        for a, _, _ in ALPHA_MARKERS:
            p = puntos[(m, a)]
            assert 0 <= p["roc_x"] <= 0.065 and 0.40 <= p["roc_y"] <= 1.0, ("ROC fuera", m, a)
            assert 0.40 <= p["pr_x"] <= 0.98 and 0 <= p["pr_y"] <= 0.09, ("PR fuera", m, a)
    for ext in ("png", "svg", "pdf"):
        buf = io.BytesIO()
        meta = {"Date": None, "Creator": "CyberFlow; ampliacion 3 alfas"} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None, "Creator": "CyberFlow; ampliacion 3 alfas"} if ext == "pdf" else None)
        fig.savefig(buf, format=ext, dpi=600, metadata=meta)
        raw = buf.getvalue()
        if ext == "svg":
            raw = ("\n".join(l.rstrip() for l in raw.decode("utf-8").splitlines()) + "\n").encode("utf-8")
        write_bytes(HERE / ("ampliacion." + ext), raw)
    plt.close(fig)
    with pymupdf.open(stream=read_bytes(HERE / "ampliacion.pdf"), filetype="pdf") as doc:
        pix = doc[0].get_pixmap(dpi=180)
        write_bytes(HERE / "zoom-previa.png", pix.tobytes("png"))
        with Image.open(io.BytesIO(pix.tobytes("png"))) as im:
            b = io.BytesIO(); im.convert("L").save(b, format="PNG"); write_bytes(HERE / "zoom-gris.png", b.getvalue())
    with Image.open(io.BytesIO(read_bytes(HERE / "ampliacion.png"))) as im:
        dpi = im.info.get("dpi", (0, 0))[0]; size = im.size
    assert abs(dpi - 600) < 1, "dpi png != 600 (%s)" % dpi
    return {"png_dpi": dpi, "png_size": list(size)}


def main():
    roc, pr, puntos, man = cargar()
    info = dibujar(roc, pr, puntos)
    cols = ["metodo", "alfa", "marcador", "roc_x_FPR", "roc_y_recall", "pr_x_recall", "pr_y_precision",
            "TP", "FP", "TN", "FN", "umbral_anomalia"]
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n"); w.writerow(cols)
    for m in METHODS:
        for a, marker, _ in ALPHA_MARKERS:
            p = puntos[(m, a)]
            w.writerow([m, a, marker, repr(p["roc_x"]), repr(p["roc_y"]), repr(p["pr_x"]), repr(p["pr_y"]),
                        p["TP"], p["FP"], p["TN"], p["FN"], p["umbral"]])
    write_text(HERE / "puntos-15-operativos.csv", buf.getvalue())

    salidas = ["ampliacion.png", "ampliacion.svg", "ampliacion.pdf", "zoom-previa.png", "zoom-gris.png",
               "puntos-15-operativos.csv", "ampliacion_alfa001.py"]
    manc = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "proposito": "Figura 5 (ampliacion) actualizada con alfa=0,01 (triangulos) conservando 0,05 (circulo) y "
                         "0,03 (rombo). Curvas y datos sin cambios; no toca principal.* (Figura 4), tablas, Word, modelos ni config.",
            "entradas_verificadas_sha256": {**H_CURVAS, "puntos.csv": H_PUNTOS,
                **{("salidas/puntuaciones-%s.csv.gz" % m): man["salidas_sha256"]["salidas/puntuaciones-%s.csv.gz" % m] for m in METHODS}},
            "alfa_0.01_conteos_reproducidos": {m: dict(zip(("TP", "FP", "TN", "FN"), REF_01[m])) for m in METHODS},
            "roc_auc_ap_curvas_sin_cambios": {m: {"roc_auc": REF_AUC_AP[m][0], "ap": REF_AUC_AP[m][1]} for m in METHODS},
            "render": info,
            "supersede": "Reemplaza los bytes de ampliacion.{png,svg,pdf} y zoom-previa/zoom-gris de la revision de 2 alfas "
                         "(MANIFIESTO.json / control.* historicos). principal.* intactos.",
            "salidas_sha256_lf": {n: sha_lf(HERE / n) for n in salidas}}
    write_text(HERE / "MANIFIESTO-AMPLIACION-ALFA001.json", json.dumps(manc, indent=2, ensure_ascii=False) + "\n")
    print("render:", info)
    print("\n15 puntos operativos:")
    for m in METHODS:
        for a, marker, _ in ALPHA_MARKERS:
            p = puntos[(m, a)]
            print("  %-16s a=%.2f %s ROC=(%.6f,%.6f) PR=(%.6f,%.6f) TP=%d FP=%d" % (
                m, a, marker, p["roc_x"], p["roc_y"], p["pr_x"], p["pr_y"], p["TP"], p["FP"]))


if __name__ == "__main__":
    main()
