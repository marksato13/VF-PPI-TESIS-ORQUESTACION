#!/usr/bin/env python3
"""Audita y dibuja puntuaciones existentes. No carga ni ajusta estimadores.

Entradas leídas de blobs Git de un único commit inmutable, no del working tree.
Ejecutar desde cualquier directorio: python RUTA/generar_figura.py [--solo-auditar].
Requiere numpy, scikit-learn, matplotlib, Pillow y PyMuPDF.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import sklearn
from sklearn.metrics import (
    average_precision_score, precision_recall_curve, roc_auc_score, roc_curve,
)

SOURCE = "028de214fb2ddc809f6eb4876574ada647b3dafb"
REPOSITORY = "https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION"
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
BASE = HERE.parent.relative_to(ROOT).as_posix()
METHODS = ("IF", "OCSVM", "LOF", "EllipticEnvelope", "PCA")
NAMES = {m: ("Elliptic Envelope" if m == "EllipticEnvelope" else m) for m in METHODS}
ALPHAS = (0.05, 0.03)
KEYS = ("campaign_id", "entity_ip", "window_end_utc")
COUNTS = {"validacion": 65553, "prueba_normal": 65421, "ataque": 84}
REFERENCE = {
    "IF": (0.9247265513, 0.1858068840),
    "OCSVM": (0.8690714573, 0.6356616972),
    "LOF": (0.9762796423, 0.0290660722),
    "EllipticEnvelope": (0.9179326429, 0.3811037449),
    "PCA": (0.9486616355, 0.5944055724),
}
EXPECTED = {
    "IF": {0.05: (54, 2955, 62466, 30), 0.03: (54, 1723, 63698, 30)},
    "OCSVM": {0.05: (71, 3319, 62102, 13), 0.03: (59, 1958, 63463, 25)},
    "LOF": {0.05: (79, 3766, 61655, 5), 0.03: (77, 2314, 63107, 7)},
    "EllipticEnvelope": {0.05: (48, 3039, 62382, 36), 0.03: (44, 1785, 63636, 40)},
    "PCA": {0.05: (71, 3539, 61882, 13), 0.03: (71, 2116, 63305, 13)},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(path, value):
    path.write_text(value.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def json_out(name, value):
    text(HERE / name, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def csv_out(name, columns, rows):
    with (HERE / name).open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([repr(float(x)) if isinstance(x, (float, np.floating)) else x for x in row])


def read_csv_bytes(data, compressed=False):
    raw = gzip.decompress(data) if compressed else data
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


def close(a, b, description):
    require(math.isclose(float(a), float(b), abs_tol=1e-13, rel_tol=2e-14),
            f"Discrepancia {description}: {a!r} frente a {b!r}")


def independent_metrics(y, s):
    """AUC por pares y AP por conteos agrupados; sin usar las curvas de sklearn."""
    normal = np.sort(s[y == 0])
    positive = s[y == 1]
    lower = np.searchsorted(normal, positive, side="left")
    upper = np.searchsorted(normal, positive, side="right")
    auc = float(np.sum((lower + upper) / 2) / (len(normal) * len(positive)))
    order = np.argsort(-s, kind="stable")
    sorted_s, sorted_y = s[order], y[order]
    ends = np.r_[np.flatnonzero(np.diff(sorted_s)), len(s) - 1]
    tp = np.cumsum(sorted_y)[ends]
    ap = float(np.sum(np.diff(np.r_[0, tp]) / len(positive) * (tp / (ends + 1))))
    return auc, ap


def audit():
    source_actual = git("rev-parse", SOURCE + "^{commit}").decode().strip()
    require(source_actual == SOURCE, "Commit fuente distinto")
    blobs, hashes = {}, {}

    def blob(name):
        if name not in blobs:
            blobs[name] = git("cat-file", "blob", f"{SOURCE}:{BASE}/{name}")
            hashes[f"{BASE}/{name}"] = sha(blobs[name])
        return blobs[name]

    manifest = json.loads(blob("MANIFIESTO-COMPARACION.json"))

    def verified(name, section):
        data = blob(name)
        require(sha(data) == manifest[section][name], f"SHA-256 incorrecto: {name}")
        # También detectar ediciones locales, sin usarlas como entrada.
        require((HERE.parent / name).read_bytes() == data, f"Working tree distinto del commit: {name}")
        return data

    config = json.loads(verified("config-comparacion.json", "codigo_sha256"))
    source_code = verified("comparar_metodos.py", "codigo_sha256").decode("utf-8")
    results = json.loads(verified("resultados-comparacion.json", "salidas_sha256"))
    table = read_csv_bytes(verified("TABLA7-comparacion-completa.csv", "salidas_sha256"))
    require(config["calibracion"]["puntuacion_comun"] == "mayor = mas anomalo", "Orientación no confirmada")
    require("puntuacion > umbral" in config["calibracion"]["regla"], "Regla distinta")
    require("np.sum(sa > thr)" in source_code and "np.sum(sn > thr)" in source_code, "Regla estricta no encontrada")
    require(len(table) == 10 and not results["faltantes"], "Tabla incompleta")
    report = {
        "source_commit": SOURCE, "repository": REPOSITORY,
        "source_selection": "HEAD local y origin/main consultado coinciden con 028de21; sin revisiones posteriores al comenzar.",
        "counts_expected": COUNTS, "evaluation_n": 65505,
        "positive_label": 1, "negative_label": 0,
        "prevalence": 84 / 65505,
        "validation_rows_used_in_curves": 0,
        "direction": "Mayor puntuación_anomalia = mayor anomalía; verificado en configuración y código fuente fijados.",
        "input_sha256": hashes, "methods": {}, "points": [],
        "discrepancies": [],
        "tolerances": {"metrics_vs_table_atol": 1e-13, "metrics_rtol": 2e-14,
                       "rounded_reference_atol": 5.1e-11, "counts": "igualdad exacta"},
        "no_packet_windows": {"reference_normal": results["calidad"]["ventanas_sin_paquetes_recientes(packet_count_10s==0)"]["oro"],
                              "source": "metadato de resultados-comparacion.json; las puntuaciones no contienen packet_count_10s",
                              "filter_applied": False},
        "training": False, "estimator_loading": False, "deployment_changes": False,
    }
    reference_keys = None
    curves = {}
    for method in METHODS:
        scores_name = f"salidas/puntuaciones-{method}.csv.gz"
        rows = read_csv_bytes(verified(scores_name, "salidas_sha256"), compressed=True)
        meta = json.loads(verified(f"salidas/meta-{method}.json", "salidas_sha256"))
        require(meta["metodo"] == method and meta["puntuaciones_sha256"] == sha(blobs[scores_name]), "Asociación método/archivo incorrecta")
        require(meta["config"]["puntuacion"] == config["metodos"][method]["puntuacion"], "Convención de puntuación distinta")
        require(len(rows) == 131058, f"Cantidad total incorrecta: {method}")
        key_map, partitions = {}, {c: [] for c in COUNTS}
        for row in rows:
            key = tuple(row[k] for k in KEYS)
            require(all(key) and key not in key_map, f"Clave vacía o duplicada en {method}: {key}")
            group = row["conjunto"]
            require(group in COUNTS, f"Conjunto inesperado: {group}")
            label = int(row["etiqueta"])
            require(label == int(group == "ataque"), f"Etiqueta distinta: {method} {key}")
            score = float(row["puntuacion_anomalia"])
            require(math.isfinite(score), f"Puntuación no finita: {method} {key}")
            key_map[key] = (group, label)
            partitions[group].append((key, label, score))
        require({g: len(v) for g, v in partitions.items()} == COUNTS, f"Conteos distintos: {method}")
        if reference_keys is None:
            reference_keys = key_map
        else:
            require(key_map == reference_keys, f"Claves, etiquetas o particiones diferentes: {method}")
        # Se conservan TODAS las normales y ataques, sin filtrar IP ni actividad.
        evaluation = partitions["prueba_normal"] + partitions["ataque"]
        ev_keys = {r[0] for r in evaluation}
        val_keys = {r[0] for r in partitions["validacion"]}
        require(not (ev_keys & val_keys), f"Validación mezclada con evaluación: {method}")
        kali = sum(r[0][1] == "10.10.20.30" for r in partitions["prueba_normal"])
        require(kali == 74, f"No se conservaron las 74 normales Kali: {method}")
        y = np.array([r[1] for r in evaluation], dtype=np.int64)
        s = np.array([r[2] for r in evaluation], dtype=np.float64)
        sv = np.array([r[2] for r in partitions["validacion"]], dtype=np.float64)
        require(len(s) == 65505 and np.sum(y) == 84, "Evaluación incorrecta")
        auc, ap = float(roc_auc_score(y, s)), float(average_precision_score(y, s))
        independent_auc, independent_ap = independent_metrics(y, s)
        close(auc, independent_auc, method + " AUC independiente")
        close(ap, independent_ap, method + " AP independiente")
        fpr, tpr, roc_thresholds = roc_curve(y, s, pos_label=1, drop_intermediate=False)
        precision, recall, pr_thresholds = precision_recall_curve(y, s, pos_label=1, drop_intermediate=False)
        close(np.trapezoid(tpr, fpr), auc, method + " área ROC")
        step_ap = float(-np.sum(np.diff(recall) * precision[:-1]))
        close(step_ap, ap, method + " área escalonada PR (AP)")
        ref_auc, ref_ap = REFERENCE[method]
        require(abs(auc - ref_auc) <= 5.1e-11 and abs(ap - ref_ap) <= 5.1e-11, "No coincide con referencias redondeadas")
        close(auc, results["metodos"][method]["roc_auc"], method + " JSON AUC")
        close(ap, results["metodos"][method]["ap"], method + " JSON AP")
        method_table = [r for r in table if r["metodo"] == method]
        require(len(method_table) == 2, "Faltan filas de tabla")
        for row in method_table:
            close(auc, row["roc_auc"], method + " tabla AUC")
            close(ap, row["ap"], method + " tabla AP")
        curves[method] = {"fpr": fpr, "tpr": tpr, "roc_thresholds": roc_thresholds,
                          "precision": precision, "recall": recall, "pr_thresholds": pr_thresholds}
        report["methods"][method] = {
            "counts": {g: len(v) for g, v in partitions.items()},
            "duplicate_keys": 0, "nonfinite_scores": 0, "same_keys_labels_partitions": True,
            "normal_kali_conserved": kali, "validation_evaluation_overlap": 0,
            "roc_auc": auc, "ap": ap, "independent_auc": independent_auc,
            "independent_ap": independent_ap, "ap_step_area": step_ap,
            "delta_auc_rounded_reference": auc - ref_auc, "delta_ap_rounded_reference": ap - ref_ap,
            "delta_auc_json": auc - results["metodos"][method]["roc_auc"],
            "delta_ap_json": ap - results["metodos"][method]["ap"],
            "roc_coordinates": len(fpr), "pr_coordinates": len(recall),
            "direction_source": config["metodos"][method]["puntuacion"],
        }
        sn, sa = sorted(s[y == 0]), sorted(s[y == 1])
        for alpha in ALPHAS:
            threshold = float(np.quantile(sv, 1 - alpha, method="linear"))
            pred = s > threshold
            tp, fp = int(np.sum(pred & (y == 1))), int(np.sum(pred & (y == 0)))
            tn, fn = 65421 - fp, 84 - tp
            require((tp, fp, tn, fn) == EXPECTED[method][alpha], f"Matriz distinta: {method} {alpha}")
            require(tp == len(sa) - bisect_right(sa, threshold), "Conteo positivo independiente distinto")
            require(fp == len(sn) - bisect_right(sn, threshold), "Conteo negativo independiente distinto")
            point = {"metodo": method, "alfa": alpha, "umbral_anomalia": threshold,
                     "TP": tp, "FP": fp, "TN": tn, "FN": fn, "FPR_prueba": fp / 65421,
                     "recall": tp / 84, "precision": tp / (tp + fp),
                     "FPR_validacion": float(np.mean(sv > threshold)),
                     "empates_validacion": int(np.sum(sv == threshold)),
                     "empates_evaluacion": int(np.sum(s == threshold))}
            trow = next(r for r in method_table if float(r["alfa"]) == alpha)
            jrow = next(r for r in results["tabla"] if r["metodo"] == method and r["alfa"] == alpha)
            point["diferencias_tabla"] = {k: float(point[k]) - float(trow[k]) for k in point if k in trow and k not in ("metodo",)}
            for key in point.keys() & trow.keys() - {"metodo", "diferencias_tabla"}:
                close(point[key], trow[key], f"{method} {alpha} tabla {key}")
                close(point[key], jrow[key], f"{method} {alpha} JSON {key}")
            # Verificación exacta de pertenencia al escalón, no selección del más cercano.
            idx = int(np.searchsorted(pr_thresholds, threshold, side="right"))
            close(precision[idx], point["precision"], "Punto PR exacto")
            close(recall[idx], point["recall"], "Recall PR exacto")
            require(np.any((fpr == point["FPR_prueba"]) & (tpr == point["recall"])), "Punto ROC no pertenece a la curva")
            point["verificado_en_curvas_sin_aproximacion"] = True
            report["points"].append(point)
    report["input_sha256"] = dict(sorted(hashes.items()))
    report["unique_keys_per_file"] = len(reference_keys)
    report["evaluation_keyset_sha256"] = sha("\n".join("\t".join(k) for k in sorted(ev_keys)).encode())
    report["validation_keyset_sha256"] = sha("\n".join("\t".join(k) for k in sorted(val_keys)).encode())
    return report, curves


def write_verification(report):
    json_out("VERIFICACION-FIGURA.json", report)
    lines = ["# Verificación de curvas y puntos operativos", "",
             f"Fuente única: `{SOURCE}`. No existen revisiones posteriores al comenzar la tarea.", "",
             "## Auditoría previa", "",
             "- SHA-256 de las cinco puntuaciones, metadatos, tabla, JSON, configuración y código: coincidentes con el manifiesto y los blobs del commit.",
             "- Cada archivo: 131 058 filas, sin claves duplicadas, claves vacías ni puntuaciones no finitas.",
             "- Claves, particiones y etiquetas idénticas entre los cinco archivos.",
             "- Curvas: 65 505 observaciones = 65 421 normales (0) + 84 ataques (1). Cero filas de validación en las curvas.",
             "- Validación: 65 553 filas, usadas solo para cuantiles lineales 1−α. Regla estricta: puntuación > umbral.",
             "- Se conservan las 74 normales de 10.10.20.30. No se filtran ventanas por actividad; las 45 558 normales sin paquetes recientes constan en el JSON fuente.",
             "- Mayor puntuación representa mayor anomalía en los cinco métodos, según configuración y código de generación verificados.",
             "- Sin carga de modelos, reentrenamiento, repuntuación, acceso al sensor ni cambios de despliegue.", "",
             "## Métricas recalculadas", "",
             "| Método | ROC-AUC | AP | ΔAUC vs JSON | ΔAP vs JSON |", "|---|---:|---:|---:|---:|"]
    for m in METHODS:
        r = report["methods"][m]
        lines.append(f"| {NAMES[m]} | {r['roc_auc']:.13f} | {r['ap']:.13f} | {r['delta_auc_json']:.3g} | {r['delta_ap_json']:.3g} |")
    lines += ["", "Referencias redondeadas del encargo: diferencias absolutas ≤ 5,1·10⁻¹¹; detalle completo en JSON. AUC contrastada por pares normal/ataque; AP por conteos independientes agrupados y por el área de escalones, no por trapecios PR.", "",
              "## Puntos operativos (orden 0,05; 0,03)", "",
              "| Método | α | Umbral anomalía | TP | FP | TN | FN | FPR prueba | Recall | Precisión |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for p in report["points"]:
        lines.append(f"| {NAMES[p['metodo']]} | {p['alfa']} | {p['umbral_anomalia']!r} | {p['TP']} | {p['FP']} | {p['TN']} | {p['FN']} | {p['FPR_prueba']:.12f} | {p['recall']:.12f} | {p['precision']:.12f} |")
    lines += ["", "Diez matrices idénticas a la Tabla 7 y al JSON; umbrales y tasas dentro de tolerancias de coma flotante (JSON). Conteos contrastados mediante búsqueda binaria independiente. No hay empates con los cuantiles. Los puntos se calcularon directamente, sin buscar un vecino ni desplazar coordenadas.", "",
              "## Representación y límites de lectura", "",
              "- Todas las puntuaciones y umbrales distintos se utilizan; `drop_intermediate=False` en ROC y PR; `path.simplify=False`.",
              "- PR: `steps-post` sobre recall decreciente devuelto por scikit-learn. Su área es −ΣΔrecall·precision[:-1], igual a Average Precision. No se usa integración trapezoidal PR.",
              f"- Prevalencia: 84/65 505 = {84 / 65505:.15f} ({100 * 84 / 65505:.9f} %), dibujada en su altura real.",
              "- El desequilibrio hace que los puntos PR se concentren junto al eje inferior; la ampliación se entrega como complemento, no como sustitución de los paneles 0–1.",
              "- Los solapamientos se mantienen en coordenadas reales. Círculo abierto = α 0,05; rombo abierto = α 0,03, con tamaños distintos.",
              "- Métricas por ventana sobre evaluación reutilizada; no es un test independiente. Las curvas no demuestran superioridad universal ni equivalen al rendimiento operativo del sistema híbrido.",
              "- Esta comparación usa 65 553 filas de validación, no las 65 633 del umbral operativo desplegado. Los puntos son configuraciones de referencia, no umbrales óptimos."]
    if "visual" in report:
        lines += ["", "## Validación de exportaciones", "", json.dumps(report["visual"], ensure_ascii=False, indent=2)]
    text(HERE / "VERIFICACION-FIGURA.md", "\n".join(lines) + "\n")


def export_coordinates(report, curves):
    csv_out("curvas-roc.csv", ["metodo", "indice", "umbral_inclusion_ge", "FPR", "TPR"],
            ((m, i, threshold, x, y) for m in METHODS
             for i, (threshold, x, y) in enumerate(zip(curves[m]["roc_thresholds"], curves[m]["fpr"], curves[m]["tpr"]))))
    csv_out("curvas-pr.csv", ["metodo", "indice", "umbral_inclusion_ge", "recall", "precision", "punto_terminal_sin_umbral"],
            ((m, i, curves[m]["pr_thresholds"][i] if i < len(curves[m]["pr_thresholds"]) else "",
              r, p, int(i == len(curves[m]["pr_thresholds"]))) for m in METHODS
             for i, (r, p) in enumerate(zip(curves[m]["recall"], curves[m]["precision"]))))
    columns = ["metodo", "alfa", "umbral_anomalia", "TP", "FP", "TN", "FN", "FPR_prueba", "recall", "precision", "FPR_validacion", "empates_validacion", "empates_evaluacion"]
    csv_out("puntos-operativos.csv", columns, ([p[c] for c in columns] for p in report["points"]))


def validate_coordinates(report, curves):
    """Verifica los CSV finales, no solo los arrays utilizados para dibujar."""
    coordinate_report = {}
    for filename, xs, ys, ts in (("curvas-roc.csv", "FPR", "TPR", "roc_thresholds"),
                                 ("curvas-pr.csv", "recall", "precision", "pr_thresholds")):
        rows = read_csv_bytes((HERE / filename).read_bytes())
        coordinate_report[filename] = {"rows": len(rows), "float64_roundtrip_exact": True}
        for m in METHODS:
            subset = [r for r in rows if r["metodo"] == m]
            c = curves[m]
            expected_x = c["fpr"] if xs == "FPR" else c["recall"]
            expected_y = c["tpr"] if ys == "TPR" else c["precision"]
            require(np.array_equal([float(r[xs]) for r in subset], expected_x), filename + " x alteradas")
            require(np.array_equal([float(r[ys]) for r in subset], expected_y), filename + " y alteradas")
            require([int(r["indice"]) for r in subset] == list(range(len(expected_x))), "Índices incompletos")
            thresholds = [float(r["umbral_inclusion_ge"]) for r in subset if r["umbral_inclusion_ge"]]
            require(np.array_equal(thresholds, c[ts]), filename + " umbrales alterados")
    point_rows = read_csv_bytes((HERE / "puntos-operativos.csv").read_bytes())
    require(len(point_rows) == 10, "CSV de puntos incompleto")
    for row, p in zip(point_rows, report["points"]):
        require(row["metodo"] == p["metodo"], "Orden de métodos diferente")
        for key in row.keys() - {"metodo"}:
            require(float(row[key]) == p[key], "CSV de punto alterado: " + key)
    coordinate_report["puntos-operativos.csv"] = {"rows": 10, "float64_roundtrip_exact": True}
    return coordinate_report


def draw(report, curves, zoom=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    from matplotlib.text import Text

    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 9,
        "axes.titlesize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 0.65, "lines.linewidth": 1.05,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "path.simplify": False, "agg.path.chunksize": 0,
        "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.hashsalt": "cyberflow-roc-pr-five-028de21", "savefig.facecolor": "white",
    })
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]
    styles = ["-", (0, (4, 2)), (0, (1.2, 1.8)), (0, (5, 2, 1, 2)), (0, (8, 2.5))]
    fig = plt.figure(figsize=(18 / 2.54, 11 / 2.54), dpi=150)
    axs = [fig.add_axes([0.085, 0.395, 0.385, 0.535]), fig.add_axes([0.595, 0.395, 0.385, 0.535])]
    lines = [[], []]
    for method, color, style in zip(METHODS, colors, styles):
        c, metrics = curves[method], report["methods"][method]
        line, = axs[0].plot(c["fpr"], c["tpr"], color=color, linestyle=style,
                            label=f"{NAMES[method]}  (ROC-AUC = {metrics['roc_auc']:.4f})")
        line.set_gid(f"ROC-{method}")
        pr, = axs[1].step(c["recall"], c["precision"], where="post", color=color, linestyle=style,
                          label=f"{NAMES[method]}  (AP = {metrics['ap']:.4f})")
        pr.set_gid(f"PR-{method}")
        lines[0].append(line)
        lines[1].append(pr)
        for alpha, symbol, size in ((0.05, "o", 6.3), (0.03, "D", 4.2)):
            p = next(p for p in report["points"] if p["metodo"] == method and p["alfa"] == alpha)
            for ax, x, y in ((axs[0], p["FPR_prueba"], p["recall"]), (axs[1], p["recall"], p["precision"])):
                marker, = ax.plot([x], [y], linestyle="none", marker=symbol, markersize=size,
                                  markerfacecolor="none", markeredgecolor=color, markeredgewidth=0.9, zorder=6)
                marker.set_gid(f"punto-{method}-{alpha}-{ax is axs[1]}")
    axs[0].plot([0, 1], [0, 1], color="0.55", linewidth=0.8, linestyle=(0, (3, 3)), zorder=0)
    axs[1].axhline(report["prevalence"], color="0.42", linewidth=0.85, linestyle=(0, (3, 3)), zorder=5)
    titles = ("(a) Curvas ROC", "(b) Curvas precisión–recall")
    if zoom:
        titles = ("(a) ROC: ampliación operativa", "(b) PR: ampliación operativa")
        axs[0].set(xlim=(0, 0.065), ylim=(0.45, 1), xticks=np.arange(0, 0.061, 0.02))
        axs[1].set(xlim=(0.5, 0.98), ylim=(0, 0.045), xticks=np.arange(0.5, 1, 0.1), yticks=np.arange(0, 0.041, 0.01))
    else:
        for ax in axs:
            ax.set(xlim=(0, 1), ylim=(0, 1), xticks=np.arange(0, 1.01, 0.2), yticks=np.arange(0, 1.01, 0.2))
        axs[0].text(0.42, 0.36, "Referencia aleatoria", rotation=36, color="0.4", fontsize=8)
    if zoom:
        axs[1].annotate("Prevalencia = 0,1282 %", xy=(0.78, report["prevalence"]), xycoords="data",
                        xytext=(0.04, 0.05), textcoords="axes fraction", fontsize=8,
                        color="0.30", arrowprops={"arrowstyle": "-", "color": "0.45", "lw": 0.65})
    else:
        axs[1].text(0.97, 0.81, "Prevalencia:\n0,1282 %\n(junto al eje)",
                    transform=axs[1].transAxes, fontsize=8, color="0.35", ha="right", va="top", linespacing=1.3)
    for ax, title in zip(axs, titles):
        ax.set_title(title, loc="left", pad=9)
        ax.grid(True, color="0.91", linewidth=0.5, zorder=0)
        ax.tick_params(length=3, width=0.6, pad=3)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}".replace(".", ",")))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}".replace(".", ",")))
    axs[0].set_xlabel("Tasa de falsos positivos", labelpad=5)
    axs[0].set_ylabel("Tasa de verdaderos positivos", labelpad=5)
    axs[1].set_xlabel("Recall", labelpad=5)
    axs[1].set_ylabel("Precisión", labelpad=5)
    legends = []
    for x, handles in zip((0.085, 0.595), lines):
        legends.append(fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(x, 0.276),
                                  frameon=False, handlelength=2.8, handletextpad=0.65,
                                  borderaxespad=0, labelspacing=0.42))
    symbols = [Line2D([], [], color="0.2", marker="o", markersize=6.3, markerfacecolor="none", linestyle="none", label="α = 0,05"),
               Line2D([], [], color="0.2", marker="D", markersize=4.2, markerfacecolor="none", linestyle="none", label="α = 0,03")]
    legends.append(fig.legend(handles=symbols, loc="lower center", bbox_to_anchor=(0.55, 0.008),
                              frameon=False, ncol=2, handletextpad=0.5, columnspacing=1.8, borderaxespad=0))
    fig.text(0.085, 0.026, "Configuraciones de validación:", fontsize=8, va="center")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    box = fig.bbox
    outside = []
    for artist in fig.findobj(Text):
        if artist.get_visible() and artist.get_text():
            bounds = artist.get_window_extent(renderer)
            if bounds.x0 < -0.5 or bounds.y0 < -0.5 or bounds.x1 > box.x1 + 0.5 or bounds.y1 > box.y1 + 0.5:
                outside.append(artist.get_text())
    require(not outside, f"Textos fuera del lienzo: {outside}")
    require(all(legend.get_window_extent(renderer).y1 < axs[0].get_window_extent(renderer).y0 - 20 for legend in legends), "Leyenda invade panel")
    basename = "ampliacion" if zoom else "roc-pr-cinco"
    fig.savefig(HERE / (basename + ".png"), dpi=600)
    fig.savefig(HERE / (basename + ".svg"), metadata={"Date": None, "Creator": "CyberFlow; Matplotlib; datos " + SOURCE})
    fig.savefig(HERE / (basename + ".pdf"), metadata={"CreationDate": None, "ModDate": None, "Creator": "CyberFlow; Matplotlib; datos " + SOURCE})
    # LF evita alterar hashes de SVG al pasar por Git.
    p = HERE / (basename + ".svg")
    text(p, "\n".join(line.rstrip() for line in p.read_text(encoding="utf-8").splitlines()) + "\n")
    plt.close(fig)
    return {"name": basename, "size_cm": [18, 11], "font_points": [8, 9],
            "texts_outside_canvas": outside, "line_width_equal_all_methods": True,
            "path_simplification": False, "roc_bounds": [list(axs[0].get_xlim()), list(axs[0].get_ylim())],
            "pr_bounds": [list(axs[1].get_xlim()), list(axs[1].get_ylim())]}


def validate_exports(plots):
    import pymupdf as fitz
    from PIL import Image
    for plot in plots:
        name = plot["name"]
        with Image.open(HERE / (name + ".png")) as image:
            plot["png_pixels"] = list(image.size)
            plot["png_dpi"] = list(image.info["dpi"])
            require(image.size == (4251, 2598), "Dimensiones PNG inesperadas")
            require(abs(image.info["dpi"][0] - 600) < 0.1, "DPI incorrecto")
        svg = ET.parse(HERE / (name + ".svg")).getroot()
        require(not svg.findall(".//{http://www.w3.org/2000/svg}image"), "SVG con imagen raster")
        ids = {node.get("id") for node in svg.iter()}
        require(all(f"{kind}-{m}" in ids for m in METHODS for kind in ("ROC", "PR")), "Curvas/métodos ausentes en SVG")
        plot["svg_has_raster_images"] = False
        with fitz.open(HERE / (name + ".pdf")) as doc:
            require(len(doc) == 1, "PDF de más de una página")
            page = doc[0]
            require(not page.get_images(), "PDF contiene imágenes raster")
            require(abs(page.rect.width * 2.54 / 72 - 18) < 1e-5, "PDF no mide 18 cm")
            plot["pdf_has_raster_images"] = False
            plot["pdf_text_extracted"] = page.get_text().strip()
            for method in METHODS:
                require(NAMES[method] in plot["pdf_text_extracted"], "Método ausente del PDF")
            blocks_outside = []
            for block in page.get_text("blocks"):
                if not page.rect.contains(fitz.Rect(block[:4])):
                    blocks_outside.append(block[4])
            require(not blocks_outside, "Texto PDF recortado")
            plot["pdf_text_blocks_outside_page"] = blocks_outside
            # Renderización PDF a tamaño de inserción y 180 dpi para inspección visual.
            page.get_pixmap(dpi=180).save(HERE / (name + "-revision-180dpi.png"))
    return plots


def write_readme():
    text(HERE / "README.md", f"""# Figura ROC y precisión–recall: cinco detectores

Fuente única: [{SOURCE}]({REPOSITORY}/commit/{SOURCE}). Sin actualizaciones posteriores al iniciar la tarea. Entradas leídas de blobs Git fijados; se comprueba además que las copias locales coincidan. No se mezclan candidatos históricos.

## Entregables

- `roc-pr-cinco.png`: figura principal, 18 × 11 cm, 600 dpi; ambos paneles y ejes completos 0–1.
- La misma figura en `.svg` y `.pdf`, vectoriales, con texto conservado y fuentes TrueType incrustadas en PDF.
- `ampliacion.png`, `.svg`, `.pdf`: ampliación explícita de los puntos operativos; no sustituye la figura principal.
- `*-revision-180dpi.png`: renderizados desde los PDF para revisión a tamaño de inserción.
- `curvas-roc.csv` y `curvas-pr.csv`: todas las coordenadas de todos los umbrales; precisión de ida y vuelta de float64 mediante `repr`.
- `puntos-operativos.csv`: las diez configuraciones, primero α = 0,05 y luego α = 0,03 para cada método.
- `VERIFICACION-FIGURA.md` / `.json`: conteos, hashes, métricas, matrices, diferencias y comprobación de las exportaciones.
- `generar_figura.py`: auditoría y generación reproducibles, sin carga ni ajuste de modelos.
- `MANIFIESTO-FIGURA.json`: commit fuente, versiones, hashes de entradas y salidas.

## Reproducción

La raíz del repositorio se localiza automáticamente. El commit fuente debe estar disponible en Git. Versiones exactas de las bibliotecas en el manifiesto; no hace falta conexión al sensor. Las curvas y conteos son reproducibles; otras versiones de fuentes o renderizadores pueden cambiar los bytes de los gráficos.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde la raíz local del repositorio:
`C:\\Users\\markp\\Desktop\\PY-MEGATRON\\PY - PERSONAL\\TESIS\\CYBERFLOW\\orquestacion-limpio`.

```powershell
python "{str(HERE / 'generar_figura.py')}" --solo-auditar
python "{str(HERE / 'generar_figura.py')}"
```

## Convenciones

Curvas exclusivamente con 65 421 normales y 84 ataques (65 505). Validación (65 553) solo para cuantiles. Todas las observaciones de cada conjunto se conservan, incluidas 74 normales Kali y las ventanas sin paquetes recientes. Mayor puntuación = más anómalo. Sin submuestreo, suavizado, búsqueda de hiperparámetros ni cambios al despliegue.

Los umbrales en CSV de curvas representan inclusión `score >= threshold`, convención de scikit-learn. ROC comienza con `inf`. En PR la última fila es el punto terminal (recall 0, precisión 1), sin umbral. En `puntos-operativos.csv` la regla es estricta `score > quantile(validacion, 1−α, method='linear')`; las coordenadas se calculan de sus matrices, no por proximidad a una curva.

PR se dibuja con `steps-post` sobre recall decreciente: AP = −ΣΔrecall·precision[:-1]. Se conserva cada umbral (`drop_intermediate=False`). No se calcula área trapezoidal PR ni envolvente de precisión. ROC se representa con todos los vértices empíricos. Cada método tiene el mismo grosor en ambos paneles, colores Okabe–Ito y estilo de línea diferenciado. Círculo abierto grande = α 0,05; rombo abierto pequeño = α 0,03. No hay desplazamientos de coordenadas.

Prevalencia = 84/65 505 = {84 / 65505:.15f}, marcada a su altura real; no se eleva para hacerla visible.

## Lectura y alcance

El panel PR completo comprime puntos operativos de precisión ≈ 0,016–0,033 cerca del eje. Algunas curvas y marcadores se superponen; la ampliación separada permite inspeccionarlos sin cambiar la figura principal ni los datos. Todas las métricas de leyenda pertenecen al conjunto completo, también en la ampliación.

ROC-AUC y AP resumen aspectos diferentes de la ordenación: se muestran los valores recalculados aunque su ranking difiera. La comparación es por ventana y reutiliza la evaluación; no es una nueva prueba independiente ni una selección de umbrales óptimos. La fuente usa 65 553 ventanas de validación; no confundirla con las 65 633 del umbral operativo desplegado. El Word y el sistema vivo no se modifican.
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-auditar", action="store_true")
    args = parser.parse_args()
    report, curves = audit()
    print("AUDITORÍA: cinco archivos; claves/etiquetas idénticas; 65553 validación + 65421 normales + 84 ataques; discrepancias: 0.")
    for method in METHODS:
        r = report["methods"][method]
        print(f"{method}: ROC-AUC={r['roc_auc']:.13f}; AP={r['ap']:.13f}")
    if args.solo_auditar:
        return
    export_coordinates(report, curves)
    report["coordinate_exports"] = validate_coordinates(report, curves)
    plots = [draw(report, curves), draw(report, curves, zoom=True)]
    report["visual"] = validate_exports(plots)
    write_verification(report)
    write_readme()
    import matplotlib
    import PIL
    import pymupdf as fitz
    outputs = [p for p in HERE.iterdir() if p.is_file() and p.name != "MANIFIESTO-FIGURA.json"]
    json_out("MANIFIESTO-FIGURA.json", {
        "source_commit": SOURCE, "source_repository": REPOSITORY, "source_path": BASE,
        "source_selection": report["source_selection"],
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__,
                     "matplotlib": matplotlib.__version__, "Pillow": PIL.__version__, "PyMuPDF": fitz.VersionBind},
        "platform": platform.platform(), "inputs_sha256": report["input_sha256"],
        "outputs_sha256": {p.name: sha(p.read_bytes()) for p in sorted(outputs)},
        "self_hash": "Omitido para evitar autorreferencia; Git identifica los bytes del manifiesto.",
        "encoding": "UTF-8; LF; CSV float64 round-trip repr",
        "models_retrained": False, "deployment_modified": False, "word_modified": False,
    })
    print("Exportaciones completas:")
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            print(f"{p} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: no dar la figura por definitiva: {exc}", file=sys.stderr)
        raise
