#!/usr/bin/env python3
"""Revisión exclusivamente gráfica de las curvas CyberFlow: datos y versión fijados.

python generar.py [--solo-auditar]
La auditoría original se carga como código verificado del commit 9ac4fbe,
sin ejecutar su main ni escribir en las carpetas anteriores. Requiere el historial
Git, numpy, scikit-learn, Matplotlib, Pillow y PyMuPDF. No carga estimadores.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
import numpy as np
from PIL import Image
import PIL
import pymupdf
import sklearn

DATA_COMMIT = "028de214fb2ddc809f6eb4876574ada647b3dafb"
PREVIOUS_COMMIT = "9ac4fbe04b51b012f363f42752589ed7b6dc2042"
REPO = "https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION"
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
PREVIOUS_DIR = HERE.parent
PREVIOUS_REL = PREVIOUS_DIR.relative_to(ROOT).as_posix()


def longpath(path):
    """Soportar la subcarpeta solicitada sin cambiar configuración de Windows/Git."""
    p = str(Path(path).absolute())
    return Path("\\\\?\\" + p) if os.name == "nt" and not p.startswith("\\\\?\\") else Path(p)


OUT = longpath(HERE)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def source_blob(commit, rel):
    return git("cat-file", "blob", f"{commit}:{rel}")


def write_text(name, content):
    (OUT / name).write_text(content.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(name, obj):
    write_text(name, json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def load_and_audit():
    previous_inputs = {}

    def previous(name):
        rel = PREVIOUS_REL + "/" + name
        raw = source_blob(PREVIOUS_COMMIT, rel)
        previous_inputs[rel] = sha(raw)
        return raw

    old_manifest_bytes = previous("MANIFIESTO-FIGURA.json")
    old_manifest = json.loads(old_manifest_bytes)
    require(old_manifest["source_commit"] == DATA_COMMIT, "La figura anterior usa otros datos")

    def checked_previous(name):
        raw = previous(name)
        require(sha(raw) == old_manifest["outputs_sha256"][name], "Hash previo incorrecto: " + name)
        require((PREVIOUS_DIR / name).read_bytes() == raw, "Versión anterior modificada localmente: " + name)
        return raw

    original_code = checked_previous("generar_figura.py")
    original_report = json.loads(checked_previous("VERIFICACION-FIGURA.json"))
    original_points = checked_previous("puntos-operativos.csv")
    for name in ("curvas-roc.csv", "curvas-pr.csv"):
        checked_previous(name)
    module = {"__name__": "auditoria_cyberflow_fijada", "__file__": str(PREVIOUS_DIR / "generar_figura.py")}
    exec(compile(original_code, str(PREVIOUS_DIR / "generar_figura.py"), "exec"), module)
    report, curves = module["audit"]()
    coordinate_report = module["validate_coordinates"](report, curves)
    require(report["input_sha256"] == old_manifest["inputs_sha256"], "Las entradas no coinciden con la primera figura")
    require(report["points"] == original_report["points"], "Puntos distintos de la primera figura")
    require(report["methods"] == original_report["methods"], "Curvas o métricas distintas de la primera figura")
    report.update({
        "previous_figure_commit": PREVIOUS_COMMIT,
        "source_selection": "Datos 028de21; figura y auditoría previa 9ac4fbe. Al iniciar, HEAD y origin/main eran 9ac4fbe, sin commits posteriores.",
        "coordinate_reference": coordinate_report,
        "previous_inputs_sha256": previous_inputs,
        "previous_data_metrics_points_identical": True,
        "design_changes": ["Figura principal sin marcadores ni leyenda alfa", "Referencias en leyendas fuera de los paneles",
                           "Títulos cortos de ampliación", "Marcadores reducidos, sin desplazamiento",
                           "Mismas curvas completas, mismos colores y estilos, mismo grosor entre métodos"],
    })
    return report, curves, original_points, module["METHODS"], module["NAMES"]


COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00")
STYLES = ("-", (0, (4, 2)), (0, (1.2, 1.8)), (0, (5, 2, 1, 2)), (0, (8, 2.5)))
ALPHA_MARKERS = ((0.05, "o", 4.2), (0.03, "D", 3.2))


def draw(report, curves, methods, names, zoom=False):
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 9,
        "axes.titlesize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 0.65, "lines.linewidth": 1.05,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "path.simplify": False, "agg.path.chunksize": 0,
        "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.hashsalt": "cyberflow-legibilidad-028de21", "savefig.facecolor": "white",
    })
    height_cm = 11.2 if zoom else 10.0
    fig = plt.figure(figsize=(18 / 2.54, height_cm / 2.54), dpi=150)
    positions = [[0.085, 0.375 if zoom else 0.365, 0.385, 0.565],
                 [0.595, 0.375 if zoom else 0.365, 0.385, 0.565]]
    axs = [fig.add_axes(pos) for pos in positions]
    handles = [[], []]
    for method, color, style in zip(methods, COLORS, STYLES):
        c, metrics = curves[method], report["methods"][method]
        roc, = axs[0].plot(c["fpr"], c["tpr"], color=color, linestyle=style,
                           label=f"{names[method]}  (ROC-AUC = {metrics['roc_auc']:.4f})")
        pr, = axs[1].step(c["recall"], c["precision"], where="post", color=color, linestyle=style,
                          label=f"{names[method]}  (AP = {metrics['ap']:.4f})")
        roc.set_gid("ROC-" + method)
        pr.set_gid("PR-" + method)
        handles[0].append(roc)
        handles[1].append(pr)
        if zoom:
            for alpha, marker, size in ALPHA_MARKERS:
                p = next(p for p in report["points"] if p["metodo"] == method and p["alfa"] == alpha)
                for is_pr, (ax, x, y) in enumerate(((axs[0], p["FPR_prueba"], p["recall"]),
                                                   (axs[1], p["recall"], p["precision"]))):
                    line, = ax.plot([x], [y], linestyle="none", marker=marker, markersize=size,
                                    markerfacecolor="none", markeredgecolor=color, markeredgewidth=0.75, zorder=6)
                    line.set_gid(f"operativo-{method}-{alpha}-{is_pr}")
    if zoom:
        axs[0].set(xlim=(0, 0.065), ylim=(0.45, 1), xticks=(0, 0.02, 0.04, 0.06))
        axs[1].set(xlim=(0.50, 0.98), ylim=(0, 0.045), xticks=(0.5, 0.6, 0.7, 0.8, 0.9), yticks=(0, 0.01, 0.02, 0.03, 0.04))
        titles = ("(a) Ampliación ROC", "(b) Ampliación PR")
    else:
        for ax in axs:
            ax.set(xlim=(0, 1), ylim=(0, 1), xticks=np.linspace(0, 1, 6), yticks=np.linspace(0, 1, 6))
        titles = ("(a) Curvas ROC", "(b) Curvas precisión–recall")
        diagonal, = axs[0].plot([0, 1], [0, 1], color="0.50", linewidth=0.8,
                                linestyle=(0, (3, 3)), label="Referencia aleatoria", zorder=0)
        diagonal.set_gid("referencia-aleatoria")
        handles[0].append(diagonal)
    prevalence = axs[1].axhline(report["prevalence"], color="0.40", linewidth=0.8,
                                linestyle=(0, (3, 3)), label="Prevalencia: 0,1282 %", zorder=5)
    prevalence.set_gid("referencia-prevalencia")
    handles[1].append(prevalence)
    for ax, title in zip(axs, titles):
        ax.set_title(title, loc="left", pad=9)
        ax.grid(True, color="0.91", linewidth=0.5, zorder=0)
        ax.tick_params(length=3, width=0.6, pad=3)
        fmt = FuncFormatter(lambda value, _: f"{value:g}".replace(".", ","))
        ax.xaxis.set_major_formatter(fmt)
        ax.yaxis.set_major_formatter(fmt)
    axs[0].set_xlabel("Tasa de falsos positivos", labelpad=5)
    axs[0].set_ylabel("Tasa de verdaderos positivos", labelpad=5)
    axs[1].set_xlabel("Recall", labelpad=5)
    axs[1].set_ylabel("Precisión", labelpad=5)
    legends = []
    for x, lines in zip((0.085, 0.595), handles):
        legends.append(fig.legend(handles=lines, loc="upper left", bbox_to_anchor=(x, 0.290 if zoom else 0.255),
                                  frameon=False, handlelength=2.9, handletextpad=0.65,
                                  borderaxespad=0, labelspacing=0.32))
    footers = []
    if zoom:
        footers.append(fig.text(0.085, 0.077, "ROC-AUC y AP corresponden a las curvas completas.", fontsize=8, va="center"))
        symbols = [Line2D([], [], color="0.2", marker=marker, markersize=size,
                          markeredgewidth=0.75, markerfacecolor="none", linestyle="none",
                          label=f"α = {alpha:.2f}".replace(".", ",")) for alpha, marker, size in ALPHA_MARKERS]
        legend = fig.legend(handles=symbols, loc="lower center", bbox_to_anchor=(0.55, 0.008),
                            frameon=False, ncol=2, handletextpad=0.5, columnspacing=1.8, borderaxespad=0)
        legends.append(legend)
        footers.append(fig.text(0.085, 0.026, "Configuraciones de validación:", fontsize=8, va="center"))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    for artist in fig.findobj(Text):
        if artist.get_visible() and artist.get_text():
            b = artist.get_window_extent(renderer)
            if b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > fig.bbox.x1 + 0.5 or b.y1 > fig.bbox.y1 + 0.5:
                outside.append(artist.get_text())
    require(not outside, f"Texto fuera del lienzo: {outside}")
    for legend in legends[:2]:
        require(legend.get_window_extent(renderer).y1 < axs[0].get_window_extent(renderer).y0 - 20, "Leyenda invade panel")
        for footer in footers:
            require(not legend.get_window_extent(renderer).overlaps(footer.get_window_extent(renderer)), "Leyenda invade nota inferior")
    require(not legends[0].get_window_extent(renderer).overlaps(legends[1].get_window_extent(renderer)), "Leyendas se solapan")
    for ax in axs:
        plotted = [line for line in ax.lines if (line.get_gid() or "").startswith(("ROC-", "PR-"))]
        require(len(plotted) == 5 and {line.get_linewidth() for line in plotted} == {1.05}, "Grosor o número de curvas distinto")
        require(all(line.get_marker() == "None" for line in plotted), "Curvas con marcadores no solicitados")
    basename = "ampliacion" if zoom else "principal"
    for ext in ("png", "svg", "pdf"):
        buffer = io.BytesIO()
        metadata = {"Date": None, "Creator": "CyberFlow; revisión de legibilidad; datos " + DATA_COMMIT} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None, "Creator": "CyberFlow; datos " + DATA_COMMIT} if ext == "pdf" else None)
        fig.savefig(buffer, format=ext, dpi=600, metadata=metadata)
        raw = buffer.getvalue()
        if ext == "svg":
            raw = ("\n".join(line.rstrip() for line in raw.decode("utf-8").splitlines()) + "\n").encode("utf-8")
        (OUT / (basename + "." + ext)).write_bytes(raw)
    info = {"name": basename, "size_cm": [18, height_cm], "axes_positions": positions,
            "roc_limits": [list(axs[0].get_xlim()), list(axs[0].get_ylim())],
            "pr_limits": [list(axs[1].get_xlim()), list(axs[1].get_ylim())],
            "font_sizes_pt": [8, 9], "method_line_width_pt": 1.05,
            "operating_markers": 20 if zoom else 0, "alpha_legend": zoom,
            "texts_outside_canvas": outside, "legends_overlap": False,
            "path_simplification": False, "pr_drawstyle": "steps-post; recall decreciente",
            "method_order": list(methods), "colors": list(COLORS)}
    plt.close(fig)
    return info


def verify_export(info, report, curves):
    name = info["name"]
    zoom = name == "ampliacion"
    width, height = np.asarray(info["size_cm"]) / 2.54 * 72
    tree = ET.fromstring((OUT / (name + ".svg")).read_bytes())
    ns = {"s": "http://www.w3.org/2000/svg"}
    groups = {node.get("id"): node for node in tree.iter() if node.get("id")}
    require(not tree.findall(".//s:image", ns), "SVG rasterizado")
    number = r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?"

    def transform(x, y, pr):
        left, bottom, w, h = info["axes_positions"][pr]
        (xl, xh), (yl, yh) = info["pr_limits" if pr else "roc_limits"]
        xx = (left + w * (np.asarray(x) - xl) / (xh - xl)) * width
        yy = (1 - bottom - h * (np.asarray(y) - yl) / (yh - yl)) * height
        return np.column_stack((np.atleast_1d(xx), np.atleast_1d(yy)))

    info["svg_curve_checks"] = {}
    for method, c in curves.items():
        for pr in (0, 1):
            group = groups[("PR-" if pr else "ROC-") + method]
            path = group.find("s:path", ns)
            require(path is not None, "Trazado ausente")
            if not zoom:
                xy = np.asarray([float(v) for v in re.findall(number, path.get("d"))]).reshape(-1, 2)
                x, y = (np.repeat(c["recall"], 2)[1:], np.repeat(c["precision"], 2)[:-1]) if pr else (c["fpr"], c["tpr"])
                expected = transform(x, y, pr)
                require(xy.shape == expected.shape, "Vértices omitidos o simplificados")
                delta = float(np.max(np.abs(xy - expected)))
                require(delta < 2e-6, "Trazado SVG distinto de los datos")
                info["svg_curve_checks"][("PR-" if pr else "ROC-") + method] = {"vertices": len(xy), "max_serialization_delta_pt": delta}
    ids = [key for key in groups if key.startswith("operativo-")]
    require(len(ids) == info["operating_markers"], "Número de marcadores incorrecto")
    if zoom:
        for p in report["points"]:
            for pr in (0, 1):
                group = groups[f"operativo-{p['metodo']}-{p['alfa']}-{pr}"]
                use = group.find(".//s:use", ns)
                require(use is not None, "Marcador ausente")
                x, y = (p["recall"], p["precision"]) if pr else (p["FPR_prueba"], p["recall"])
                expected = transform(x, y, pr)[0]
                require(float(np.max(np.abs(expected - [float(use.get("x")), float(use.get("y"))]))) < 2e-6,
                        "Punto operativo desplazado")
    else:
        require(not any("α" in (node.text or "") for node in tree.iter()), "Leyenda alfa en la principal")
    baseline_path = groups["referencia-prevalencia"].find("s:path", ns)
    baseline_xy = np.asarray([float(v) for v in re.findall(number, baseline_path.get("d"))]).reshape(-1, 2)
    require(np.max(np.abs(baseline_xy[:, 1] - transform(0, report["prevalence"], 1)[0, 1])) < 2e-6, "Prevalencia desplazada")
    with Image.open(io.BytesIO((OUT / (name + ".png")).read_bytes())) as image:
        require(abs(image.info["dpi"][0] - 600) < 0.1, "DPI incorrecto")
        info["png_pixels"] = list(image.size)
        info["png_dpi"] = list(image.info["dpi"])
        require(image.size == tuple(int(cm / 2.54 * 600) for cm in info["size_cm"]), "Tamaño PNG incorrecto")
    with pymupdf.open(stream=(OUT / (name + ".pdf")).read_bytes(), filetype="pdf") as doc:
        require(len(doc) == 1, "PDF con páginas de más")
        page = doc[0]
        require(not page.get_images(), "PDF rasterizado")
        require(np.max(np.abs(np.array([page.rect.width, page.rect.height]) - [width, height])) < 1e-4, "Tamaño PDF incorrecto")
        for font in page.get_fonts():
            require(len(doc.extract_font(font[0])[3]) > 0, "Fuente PDF no incrustada")
        for block in page.get_text("blocks"):
            require(page.rect.contains(pymupdf.Rect(block[:4])), "Texto PDF recortado")
        pix = page.get_pixmap(dpi=180)
        preview = "zoom-previa.png" if zoom else "previa.png"
        (OUT / preview).write_bytes(pix.tobytes("png"))
        with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
            buffer = io.BytesIO()
            image.convert("L").save(buffer, format="PNG")
            (OUT / ("zoom-gris.png" if zoom else "gris.png")).write_bytes(buffer.getvalue())
        info["pdf_vectorial_fonts_embedded_no_clipped_text"] = True
    return info


def write_reports(report, names):
    write_json("control.json", report)
    rows = ["# Verificación de la revisión de legibilidad", "",
            f"Datos: `{DATA_COMMIT}`. Referencia gráfica: `{PREVIOUS_COMMIT}`. Sin actualizaciones posteriores al comenzar.", "",
            "## Datos y resultados preservados", "",
            "SHA-256, claves y etiquetas comprobados en los cinco archivos. Sin claves duplicadas, puntuaciones no finitas ni filtros adicionales. Curvas: 65 421 normales + 84 ataques = 65 505; cero filas de validación. Validación: 65 553 solo para cuantiles 1−α lineales; detección estricta score > umbral. Se conservan las 74 normales Kali y todas las ventanas sin paquetes recientes.", "",
            "AUC/AP, diez matrices de confusión, umbrales y coordenadas coinciden exactamente con la Tabla 7 y la primera publicación. Los CSV de curvas de 9ac4fbe se contrastan sin pérdida de precisión; no se duplican en esta revisión. `puntos.csv` es idéntico por bytes al CSV operativo anterior.", "",
            "| Método | ROC-AUC | AP | ΔAUC vs JSON | ΔAP vs JSON |", "|---|---:|---:|---:|---:|"]
    for m, metrics in report["methods"].items():
        rows.append(f"| {names[m]} | {metrics['roc_auc']:.13f} | {metrics['ap']:.13f} | {metrics['delta_auc_json']} | {metrics['delta_ap_json']} |")
    rows += ["", "| Método | α | Umbral | TP | FP | TN | FN |", "|---|---:|---:|---:|---:|---:|---:|"]
    for p in report["points"]:
        rows.append(f"| {names[p['metodo']]} | {p['alfa']} | {p['umbral_anomalia']!r} | {p['TP']} | {p['FP']} | {p['TN']} | {p['FN']} |")
    rows += ["", "## Comprobación de las imágenes", "",
             "Principal: ejes completos 0–1, sin círculos/rombos ni leyenda alfa; cinco curvas, referencias fuera de los paneles, grosor uniforme. Los vértices SVG de las diez curvas se contrastan contra todos los vértices calculados; no se omite ninguno. PR steps-post sobre recall decreciente, área escalonada igual a AP; sin trapecios PR ni suavizado.", "",
             "Ampliación del mismo experimento: ROC FPR [0; 0,065], TPR [0,45; 1]; PR recall [0,50; 0,98], precisión [0; 0,045]. Círculo abierto α=0,05, rombo abierto α=0,03, en ese orden. Marcadores de 4,2 y 3,2 pt, sin desplazamiento. Sus veinte posiciones SVG se contrastan con las matrices. Algunos trazados coinciden; las coordenadas no se separan artificialmente.", "",
             "Prevalencia 84/65 505 = 0,0012823448591710556 (0,1282 %): su posición real se comprueba también en el SVG. AUC y AP de la ampliación corresponden a las curvas completas, no a las áreas ampliadas.", "",
             "PNG 600 dpi; SVG sin imágenes raster; PDF vectorial con fuentes incrustadas. Comprobación de cajas de texto sin recortes ni leyendas solapadas. Previsualizaciones desde PDF a 180 dpi, en color y gris. Los parámetros y comprobaciones detalladas figuran en `control.json`.", "",
             "Se trata de una evaluación reutilizada por ventana, no un nuevo test independiente. No se cargan modelos ni se cambia el Word o el despliegue."]
    write_text("control.md", "\n".join(rows) + "\n")


def write_readme():
    previous_url = f"{REPO}/tree/{PREVIOUS_COMMIT}/{PREVIOUS_REL}"
    write_text("README.md", f"""# Revisión de legibilidad de ROC y precisión–recall

Revisión de diseño de [la figura original]({previous_url}); no es otro experimento.

- Datos fijados a `{DATA_COMMIT}`; primera publicación y auditoría reutilizable fijadas a `{PREVIOUS_COMMIT}`. HEAD y origin/main al iniciar: 9ac4fbe, sin commits posteriores.
- `principal.png`, `.svg`, `.pdf`: 18 × 10 cm, PNG 600 dpi; cinco curvas completas 0–1, sin marcadores ni leyenda alfa. Referencias en las leyendas bajo cada panel.
- `ampliacion.png`, `.svg`, `.pdf`: 18 × 11,2 cm; mismos datos, colores, estilos y métricas. Conserva diez configuraciones (veinte marcadores en total): círculo abierto α=0,05, rombo abierto α=0,03. No se desplazan coordenadas.
- `previa.png` y `zoom-previa.png`: renderizados PDF a 180 dpi para revisión al tamaño de inserción.
- `gris.png` y `zoom-gris.png`: las mismas previsualizaciones en escala de grises para comprobar los patrones de línea.
- `generar.py`: código reproducible. La auditoría de la primera publicación se carga de Git tras verificar su hash; no se ejecuta su generador ni se escribe en las carpetas anteriores.
- `puntos.csv`: copia exacta del CSV anterior, umbrales y diez matrices preservados.
- `control.md` y `control.json`: verificaciones numéricas y de exportación.
- `MANIFIESTO.json`: commits, versiones y hashes de todas las entradas y salidas. Los CSV completos de curvas permanecen en [la versión original]({previous_url}), identificados por commit y hash.

## Reproducción

Se necesitan los dos commits en el historial local, numpy, scikit-learn, Matplotlib, Pillow y PyMuPDF. No se necesita acceso al sensor. Las rutas largas de Windows se manejan internamente sin cambiar la configuración del sistema. Los datos, las métricas y las coordenadas son reproducibles; el renderizado puede cambiar en otras versiones de bibliotecas o fuentes.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde la carpeta de esta revisión:
`{HERE}`.

```powershell
python generar.py --solo-auditar
python generar.py
```

La opción de auditoría no escribe archivos.

## Lectura y alcance

Paleta Okabe–Ito y cinco patrones de línea diferentes, idénticos en ambos paneles; grosor 1,05 pt para todos los métodos. No se destaca IF. No hay explicaciones dentro de los paneles.

Límites de ampliación: ROC FPR 0–0,065, TPR 0,45–1; PR recall 0,50–0,98, precisión 0–0,045. La nota bajo las leyendas aclara que ROC-AUC y AP pertenecen a las curvas completas. Las curvas o puntos que se superponen conservan sus posiciones; los dos alfas usan tamaños y formas distintos. No son umbrales óptimos.

PR mantiene cada escalón, sin interpolación suave, envolvente ni área trapezoidal: `steps-post` sobre recall decreciente; AP = −ΣΔrecall·precision[:-1]. ROC y PR se calculan con todas las puntuaciones de evaluación, nunca con predicciones binarias. Validación se usa solo para los diez cuantiles.

Se mantienen las 74 normales Kali y las ventanas sin paquetes recientes. No se reentrena, repuntúa, reetiqueta ni filtra. No se edita el Word ni se modifica el sistema. La evaluación sigue siendo reutilizada y por ventana: el cambio de diseño no cambia conclusiones.
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-auditar", action="store_true")
    args = parser.parse_args()
    report, curves, points, methods, names = load_and_audit()
    print("AUDITORÍA OK: datos, hashes, claves, etiquetas, métricas, umbrales y diez matrices preservados.")
    if args.solo_auditar:
        return
    (OUT / "puntos.csv").write_bytes(points)
    report["design_exports"] = [verify_export(draw(report, curves, methods, names, zoom), report, curves) for zoom in (False, True)]
    write_reports(report, names)
    write_readme()
    outputs = [p for p in OUT.iterdir() if p.is_file() and p.name != "MANIFIESTO.json"]
    write_json("MANIFIESTO.json", {
        "data_commit": DATA_COMMIT, "previous_figure_commit": PREVIOUS_COMMIT, "repository": REPO,
        "starting_head_and_remote_main": PREVIOUS_COMMIT, "later_updates_at_start": [],
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__,
                     "matplotlib": matplotlib.__version__, "Pillow": PIL.__version__, "PyMuPDF": pymupdf.VersionBind},
        "platform": platform.platform(),
        "inputs_sha256_by_commit": {DATA_COMMIT: report["input_sha256"], PREVIOUS_COMMIT: report["previous_inputs_sha256"]},
        "outputs_sha256": {p.name: sha(p.read_bytes()) for p in sorted(outputs)},
        "self_hash": "Excluido para evitar autorreferencia; identificado por el commit de publicación.",
        "data_metrics_thresholds_points_unchanged": True, "previous_files_modified": False,
        "word_modified": False, "models_retrained": False, "deployment_modified": False,
    })
    for p in sorted(OUT.iterdir()):
        if p.is_file():
            print(f"{HERE / p.name} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
