#!/usr/bin/env python3
"""Figuras 4.2 desde registros publicados, sin inferencia ni acceso a las VMs.

python generar.py [--solo-auditar]
Datos y código de evaluación fijados a 0305589. No ejecuta evaluar_componentes.py,
no carga modelos y no modifica los resultados originales. Requiere numpy,
Matplotlib, Pillow y PyMuPDF, además del historial Git del repositorio.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
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

SOURCE = "03055893722a941449624fef19036fd08929a51f"
DATA41 = "028de214fb2ddc809f6eb4876574ada647b3dafb"
REPOSITORY = "https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION"
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
BASE = HERE.parent.relative_to(ROOT).as_posix()
COMP41 = str(Path(BASE).parent.parent / "4.1-modelos/comparacion-metodos-2026-10-25").replace("\\", "/")
CONFIGS = ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03")
LABELS = ("IF\nα=0,05", "IF\nα=0,03", "Heur.", "Híbrido\nα=0,05", "Híbrido\nα=0,03")
ROWLABELS = ("IF α=0,05", "IF α=0,03", "Heurísticos", "Híbrido α=0,05", "Híbrido α=0,03")
COLORS = ("#0072B2", "#0072B2", "#009E73", "#D55E00", "#D55E00")
EPISODES = tuple(f"e{family}-r{rep}" for family in (3, 4, 1) for rep in (1, 2, 3))
KEYS = ("campaign_id", "entity_ip", "window_end_utc")


def safe_path(path):
    p = str(Path(path).absolute())
    return Path("\\\\?\\" + p) if os.name == "nt" and not p.startswith("\\\\?\\") else Path(p)


OUT = safe_path(HERE)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(rel, commit=SOURCE):
    return subprocess.check_output(["git", "-C", str(ROOT), "cat-file", "blob", f"{commit}:{rel}"])


def rows(raw, zipped=False):
    if zipped:
        raw = gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


def instant(value):
    return dt.datetime.fromisoformat(value)


def boolean(value):
    require(str(value) in ("0", "1", "si", "no", "True", "False"), "Booleano ausente o inválido")
    return str(value) in ("1", "si", "True")


def close(a, b, message):
    require(math.isclose(float(a), float(b), abs_tol=1e-13, rel_tol=2e-14), message)


def text(name, value):
    (OUT / name).write_text(value.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def save_json(name, data):
    text(name, json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def save_csv(name, data):
    with (OUT / name).open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(data[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def metrics(y, pred):
    tp = int(np.sum((y == 1) & pred)); fp = int(np.sum((y == 0) & pred))
    tn = int(np.sum((y == 0) & ~pred)); fn = int(np.sum((y == 1) & ~pred))
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return dict(TP=tp, FP=fp, TN=tn, FN=fn, precision=precision, recall=recall,
                F1=2 * precision * recall / (precision + recall), FPR=fp / (fp + tn), n=len(y))


def audit():
    hashes, cache = {}, {}
    hash_issues = []
    manifest_raw = blob(BASE + "/MANIFIESTO-APORTE.json")
    manifest = json.loads(manifest_raw)
    hashes[BASE + "/MANIFIESTO-APORTE.json"] = sha(manifest_raw)
    # Auditar toda la publicación, sin pretender verificar de nuevo los PCAP externos.
    for name, expected in manifest["archivos_publicados_sha256"].items():
        raw = blob(BASE + "/" + name)
        if sha(raw) != expected:
            require(not name.endswith(".gz"), "Hash binario incorrecto: " + name)
            crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            require(sha(crlf) == expected, "Discrepancia de contenido sin explicar: " + name)
            hash_issues.append({"archivo": name, "hash_git_LF": sha(raw), "hash_manifiesto_CRLF": expected,
                                "causa_verificada": "Normalización CRLF a LF al publicar en Git; reconstruir CRLF reproduce exactamente el hash declarado"})
        local = safe_path(HERE.parent / name).read_bytes()
        require(local == raw or (not name.endswith(".gz") and local.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n")),
                "Copia local con contenido distinto del commit: " + name)
        cache[name] = raw
        hashes[BASE + "/" + name] = sha(raw)
    cfg = json.loads(cache["config-aporte.json"])
    registry = rows(cache["resultados/episodios-registro.csv"])
    ep_windows = rows(cache["resultados/episodios-ventanas.csv.gz"], True)
    metadata = json.loads(cache["resultados/episodios-metadatos.json"])
    published_metrics = json.loads(cache["resultados/ventanas-metricas.json"])
    pred_rows = rows(cache["resultados/ventanas-predicciones.csv.gz"], True)
    table8 = rows(cache["resultados/TABLA8-componentes.csv"])
    table_windows = rows(cache["resultados/VENTANAS-metricas.csv"])
    consolidated = json.loads(cache["resultados/resultados-aporte.json"])
    verified_thresholds = json.loads(cache["resultados/umbrales-verificados.json"])
    accumulated = json.loads(cache["resultados/contraste-acumulador-vivo.json"])
    original = rows(cache["resultados/reproduccion-original.csv"])
    require(len(original) == 9 and all(boolean(r["coincide"]) for r in original), "Antecedente no reproducido")
    historical = {c: sum(boolean(r[k]) for r in original) for c, k in
                  (("IF", "det_modelo"), ("Heurísticos", "det_heur"), ("Híbrido", "det_combinado"))}
    require(tuple(historical.values()) == (6, 7, 9), "Histórico diferente")
    require(cfg["modelo"]["sha256_esperado"] == "df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60", "Modelo incorrecto")
    require(cfg["heuristicos"]["version"] == "2026-10-06.2", "Reglas diferentes")
    source_code = cache["evaluar_componentes.py"].decode("utf-8")
    require('preds["HIB_" + a] = preds["IF_" + a] | heur' in source_code, "Combinación no comprobada")

    def reference41(name):
        rel = COMP41 + "/" + name
        raw = blob(rel)
        require(raw == blob(rel, DATA41), "Los datos 4.1 cambiaron entre commits")
        hashes[rel] = sha(raw)
        return raw

    manifest41 = json.loads(reference41("MANIFIESTO-COMPARACION.json"))
    score_bytes = reference41("salidas/puntuaciones-IF.csv.gz")
    require(sha(score_bytes) == manifest41["salidas_sha256"]["salidas/puntuaciones-IF.csv.gz"], "Hash scores IF incorrecto")
    score_rows = rows(score_bytes, True)
    calibration = [float(r["puntuacion_anomalia"]) for r in score_rows if r["conjunto"] == "validacion"]
    require(len(calibration) == 65553 and all(math.isfinite(x) for x in calibration), "Validación incorrecta")
    thresholds = {}
    for alpha in (0.05, 0.03):
        a = str(alpha)
        thresholds[a] = -float(np.quantile(calibration, 1 - alpha, method="linear"))
        close(thresholds[a], verified_thresholds["umbrales"][a]["umbral_score_samples"], "Umbral distinto")
        close(thresholds[a], consolidated["umbrales"][a], "Umbral consolidado distinto")
    reference_map = {tuple(r[k] for k in KEYS): (int(r["etiqueta"]), -float(r["puntuacion_anomalia"]))
                     for r in score_rows if r["conjunto"] in ("prueba_normal", "ataque")}
    require(len(pred_rows) == len(reference_map) == 65505, "Población distinta de Tabla 7")
    prediction_map = {tuple(r[k] for k in KEYS): r for r in pred_rows}
    require(len(prediction_map) == len(pred_rows) and prediction_map.keys() == reference_map.keys(), "Claves duplicadas o cobertura distinta")
    require(all(int(r["etiqueta"]) == reference_map[k][0] for k, r in prediction_map.items()), "Etiquetas diferentes")
    y = np.array([int(r["etiqueta"]) for r in pred_rows])
    require(Counter(y.tolist()) == {0: 65421, 1: 84}, "Etiquetas o conteos incorrectos")
    s = np.array([float(r["score_samples"]) for r in pred_rows])
    require(np.all(np.isfinite(s)), "Scores no finitos")
    max_score_delta = max(abs(float(r["score_samples"]) - reference_map[k][1]) for k, r in prediction_map.items())
    require(max_score_delta < 2e-16, "Scores distintos de Tabla 7")
    require(sum(r["entity_ip"] == "10.10.20.30" and r["etiqueta"] == "0" for r in pred_rows) == 74, "Se perdieron las 74 normales Kali")
    require(sum(float(r["packet_count_10s"]) == 0 and r["etiqueta"] == "0" for r in pred_rows) == 45558, "Se filtraron ventanas sin paquetes")
    predictions = {c: np.array([boolean(r[c]) for r in pred_rows]) for c in CONFIGS}
    window_metrics = {}
    for a in ("0.05", "0.03"):
        require(np.array_equal(predictions["IF_" + a], s < thresholds[a]), "Operador o umbral IF incorrecto")
        require(np.array_equal(predictions["HIB_" + a], predictions["IF_" + a] | predictions["HEUR"]), "Híbrido distinto de las señales verificadas")
    for c in CONFIGS:
        result = metrics(y, predictions[c])
        trow = next(r for r in table_windows if r["poblacion"] == "principal" and r["configuracion"] == c)
        for key, value in result.items():
            close(value, published_metrics["principal"][c][key], "Métrica JSON distinta: " + c + " " + key)
            close(value, trow[key], "Métrica CSV distinta: " + c + " " + key)
        window_metrics[c] = result
    # Separar señales de aplicación: no hay simulación de feed/nftables.
    overlaps_windows = {}
    for a in ("0.05", "0.03"):
        i, h = predictions["IF_" + a], predictions["HEUR"]
        overlaps_windows[a] = {"ambos": int(np.sum(i & h & (y == 1))), "solo_IF": int(np.sum(i & ~h & (y == 1))),
                               "solo_heur": int(np.sum(~i & h & (y == 1))), "ninguno": int(np.sum(~i & ~h & (y == 1)))}
        require(overlaps_windows[a] == published_metrics["solape_ataques_" + a], "Solape por ventana distinto")

    require(set(metadata) == set(EPISODES) and len(registry) == 45, "Episodios/configuraciones incompletos")
    index = {(r["episodio"], r["configuracion"]): r for r in registry}
    require(len(index) == 45, "Duplicados por episodio/configuración")
    ekeys = [(r["episodio"], r["entity_ip"], r["window_end_utc"]) for r in ep_windows]
    require(len(ekeys) == len(set(ekeys)), "Ventanas de episodio duplicadas")
    matrix = np.zeros((9, 5), dtype=int)
    exported_episodes = []
    truncated = np.zeros((9, 5), dtype=int)
    strict = np.zeros((9, 5), dtype=int)
    accumulated_matrix = np.zeros((9, 5), dtype=int)
    late = []
    for ie, episode in enumerate(EPISODES):
        meta = metadata[episode]
        start, end = map(instant, meta["intervalo_atribucion"])
        attack_end = instant(meta["ultimo_paquete_ataque"])
        require((end - attack_end).total_seconds() == 60 and start == instant(meta["T0_orquestador"]), "Intervalo distinto")
        eligible = []
        for row in (r for r in ep_windows if r["episodio"] == episode):
            require(math.isfinite(float(row["score_samples"])), "Score de episodio no finito")
            actual_attribution = row["entity_ip"] == meta["origen"] and start <= instant(row["window_end_utc"]) <= end
            require(boolean(row["atribuible"]) == actual_attribution, "Atribución distinta")
            for a in ("0.05", "0.03"):
                require(boolean(row["HIB_" + a]) == (boolean(row["IF_" + a]) or boolean(row["HEUR"])), "Solape episodio no coincide")
            if actual_attribution:
                eligible.append(row)
        for ic, config in enumerate(CONFIGS):
            source = index[episode, config]
            signals = sorted([r for r in eligible if boolean(r[config])], key=lambda r: r["window_end_utc"])
            require(boolean(source["detectado"]) == bool(signals), "Detección agregada distinta")
            require(int(source["ventanas_con_senal"]) == len(signals), "Conteos de señales distintos")
            require(int(source["ventanas_atribuibles"]) == len(eligible), "Conteos atribuibles distintos")
            if signals:
                require(source["primera_senal_window_end"] == signals[0]["window_end_utc"], "Primera señal diferente")
            matrix[ie, ic] = int(bool(signals))
            strict[ie, ic] = int(any(instant(r["window_end_utc"]) <= attack_end for r in signals))
            if signals and not strict[ie, ic]:
                late.append({"episodio": episode, "configuracion": config,
                             "primera_senal": source["primera_senal_window_end"], "fin_ataque": meta["ultimo_paquete_ataque"]})
            truncated[ie, ic] = int(boolean(source["detectado_sensibilidad_historia_truncada"]))
            accumulated_matrix[ie, ic] = int(accumulated["episodios"][episode][config]["detectado"])
            exported_episodes.append({"episodio": episode, "familia": meta["familia"], "configuracion": config,
                                      "Tabla8_fin_mas60": int(matrix[ie, ic]), "solo_T0_fin": int(strict[ie, ic]),
                                      "historia_observada_elegible": int(truncated[ie, ic]),
                                      "acumulador_repuntuado": int(accumulated_matrix[ie, ic]),
                                      "T0": meta["T0_orquestador"], "primer_paquete": meta["primer_paquete_ataque"],
                                      "ultimo_paquete": meta["ultimo_paquete_ataque"], "fin_atribucion": meta["intervalo_atribucion"][1],
                                      "primera_senal": source["primera_senal_window_end"],
                                      "latencia_T0_s": source["latencia_desde_T0_s"],
                                      "componente": source["componente"], "accion_propuesta": source["accion"],
                                      "origen": meta["origen"], "destino": meta["destino"], "evidencia": source["evidencia"]})
    labels8 = ("IF 0,05", "IF 0,03", "Heuristicos", "Hibrido 0,05", "Hibrido 0,03")
    for prefix, family in (("e3", "DNS inusual (alta entropia)"), ("e4", "Inundacion HTTP"), ("e1", "Escaneo de puertos")):
        table_row = next(r for r in table8 if r["Familia"] == family)
        indices = [i for i, e in enumerate(EPISODES) if e.startswith(prefix)]
        for i, col in enumerate(labels8):
            require(table_row[col] == f"{int(matrix[indices, i].sum())}/3", "Tabla 8 por familia distinta")
    require(matrix.sum(0).tolist() == [6, 6, 9, 9, 9], "Total distinto")
    require(strict.sum(0).tolist() == [4, 4, 7, 7, 7], "Revisar sensibilidad de intervalo")
    require(truncated.sum(0).tolist() == [3, 3, 7, 7, 7], "Revisar historia truncada")
    require(accumulated_matrix.sum(0).tolist() == [8, 6, 9, 9, 9], "Revisar acumulador")
    episode_overlap = {}
    comp_csv = rows(cache["resultados/complementariedad-episodios.csv"])
    for a, ic in (("0.05", 0), ("0.03", 1)):
        counts = Counter()
        for ie, episode in enumerate(EPISODES):
            i, h = bool(matrix[ie, ic]), bool(matrix[ie, 2])
            label = "ambos" if i and h else ("solo IF" if i else ("solo heuristicos" if h else "ninguno"))
            require(next(r["clase"] for r in comp_csv if r["episodio"] == episode and r["alfa"] == a) == label, "Clasificación de solape distinta")
            counts[label] += 1
        episode_overlap[a] = {k: counts[k] for k in ("ambos", "solo IF", "solo heuristicos", "ninguno")}
    sensitivity = np.vstack([matrix.sum(0), strict.sum(0), truncated.sum(0), accumulated_matrix.sum(0)])
    report = {"source_commit": SOURCE, "calibration_origin_commit": DATA41, "input_sha256": hashes,
              "historical": {"model": "if_recalibrado_2026_09", "rules": "2026-09-30.1 con DNS 0,45", "counts": historical,
                             "shown_in_current_figure": False},
              "counts_windows": {"normal": 65421, "attack": 84, "all": 65505, "kali_normal_retained": 74, "zero_packet_normal_retained": 45558},
              "validation_count": 65553, "thresholds_score_samples": thresholds, "score_comparison_max_delta": max_score_delta,
              "window_metrics": window_metrics, "window_attack_overlap": overlaps_windows,
              "episode_matrix": matrix.tolist(), "episode_overlap": episode_overlap,
              "sensitivity_counts": sensitivity.tolist(), "late_detections_vs_last_packet": late,
              "extra_FP_hybrid_vs_IF": {a: window_metrics["HIB_" + a]["FP"] - window_metrics["IF_" + a]["FP"] for a in ("0.05", "0.03")},
              "source_manifest_newline_discrepancies": hash_issues,
              "unexplained_discrepancies": [],
              "scope": "Auditoría de los registros publicados; no reprocesa los PCAP externos ni vuelve a ejecutar los heurísticos sobre características crudas.",
              "source_cautions": ["Tabla 8 usa T0–último paquete +60 s, no exclusivamente durante el ataque",
                                 "capture_start se fija artificialmente 60 s antes de la primera observación; esto no recupera historia ausente",
                                 "Los heurísticos actuales se ajustaron a la vista de estos episodios",
                                 "Acumulador en vivo repuntuado no equivale a un nuevo ensayo en vivo con IF limpio",
                                 "FPR de señales, no de bloqueos; muchas alarmas DNS afectan una entidad nunca-bloquear"],
              "raw_capture_replay_repeated": False, "word_modified": False, "deployment_modified": False}
    return report, matrix, sensitivity, exported_episodes


def configure():
    matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9,
                               "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                               "axes.spines.top": False, "axes.spines.right": False,
                               "figure.facecolor": "white", "axes.facecolor": "white",
                               "svg.fonttype": "none", "pdf.fonttype": 42, "path.simplify": False,
                               "svg.hashsalt": "cyberflow-componentes-0305589"})


def draw_main(report, matrix):
    configure()
    fig = plt.figure(figsize=(18 / 2.54, 11.2 / 2.54), dpi=150)
    left = fig.add_axes([0.15, 0.37, 0.34, 0.52])
    right = fig.add_axes([0.70, 0.37, 0.275, 0.52])
    left.set(xlim=(-0.5, 4.5), ylim=(8.5, -0.5), xticks=np.arange(5), xticklabels=LABELS,
             yticks=np.arange(9), yticklabels=[f"{family} {r}" for family in ("DNS", "Inund. HTTP", "Escaneo") for r in (1, 2, 3)])
    left.set_title("(a) Episodios (n = 9)", loc="left", pad=12)
    left.axhspan(2.5, 5.5, color="0.96", zorder=0)
    for row in (2.5, 5.5):
        left.axhline(row, color="0.78", lw=0.6)
    left.tick_params(axis="both", length=0, pad=5)
    for spine in left.spines.values():
        spine.set_visible(False)
    for ie in range(9):
        for ic, color in enumerate(COLORS):
            marker = "o" if matrix[ie, ic] else "_"
            line, = left.plot([ic], [ie], linestyle="none", marker=marker, markersize=4.8 if matrix[ie, ic] else 5.0,
                              color=color if matrix[ie, ic] else "0.55")
            line.set_gid(f"episodio-{EPISODES[ie]}-{CONFIGS[ic]}")
    for ic, total in enumerate(matrix.sum(0)):
        left.text(ic, -0.24, f"{int(total)}/9", transform=left.get_xaxis_transform(), ha="center", va="center", fontsize=8)
    left.text(-0.55, -0.24, "Total", transform=left.get_xaxis_transform(), ha="right", va="center", fontsize=8)
    y = np.arange(5)
    right.set(ylim=(4.6, -0.6), xlim=(0, 7.5), yticks=y, yticklabels=ROWLABELS, xticks=(0, 2, 4, 6))
    right.set_title("(b) Ventanas (n = 65 505)", loc="left", pad=12)
    right.text(0, 1.01, "65 421 normales · 84 ataques", transform=right.transAxes, fontsize=7.5, va="bottom")
    right.set_xlabel("FPR (%)", labelpad=5)
    right.tick_params(axis="y", length=0, pad=5)
    right.grid(axis="x", color="0.9", lw=0.6)
    right.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}".replace(".", ",")))
    for ic, (c, color) in enumerate(zip(CONFIGS, COLORS)):
        m = report["window_metrics"][c]
        marker = "s" if c == "HEUR" else ("o" if c.endswith("0.05") else "D")
        point, = right.plot([100 * m["FPR"]], [ic], marker=marker, markersize=4.5, color=color, linestyle="none", zorder=4)
        point.set_gid("fpr-" + c)
        right.annotate(f"{m['FP']:,} FP\n{m['TP']} TP".replace(",", " "), (100 * m["FPR"], ic),
                       xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, linespacing=1.2)
    fig.legend(handles=[Line2D([], [], color="0.25", marker="o", markersize=4.8, linestyle="none", label="Señal atribuible"),
                        Line2D([], [], color="0.55", marker="_", markersize=5, linestyle="none", label="Sin señal")],
               frameon=False, ncol=2, loc="center", bbox_to_anchor=(0.31, 0.195), fontsize=8, handletextpad=0.3, columnspacing=0.8)
    fig.text(0.70, 0.245, "FP: señales, no bloqueos", fontsize=8)
    fig.text(0.08, 0.14, "Por episodio (ambos α): ambos 6 · solo IF 0 · solo heurísticos 3 · ninguno 0.", fontsize=8)
    fig.text(0.08, 0.085, "Recálculo offline; episodios y ventanas de campañas distintas. Sin validación independiente.", fontsize=7.7)
    fig.text(0.08, 0.045, "Episodios: T0–fin + 60 s; elegibilidad reconstruida. Heurísticos ajustados con esta batería.", fontsize=7.7)
    return fig, {"name": "componentes", "size_cm": [18, 11.2], "axes": [list(left.get_position().bounds), list(right.get_position().bounds)]}


def draw_sensitivity(sensitivity):
    configure()
    fig = plt.figure(figsize=(18 / 2.54, 9 / 2.54), dpi=150)
    ax = fig.add_axes([0.36, 0.29, 0.61, 0.53])
    ax.set(xlim=(-0.5, 4.5), ylim=(3.5, -0.5))
    for row in range(4):
        for col in range(5):
            ax.add_patch(plt.Rectangle((col - 0.5, row - 0.5), 1, 1,
                                      facecolor=plt.get_cmap("Blues")(sensitivity[row, col] / 9),
                                      edgecolor="white", linewidth=0.7))
    ax.set(xticks=np.arange(5), xticklabels=LABELS, yticks=np.arange(4),
           yticklabels=("Tabla 8: T0–fin + 60 s", "Solo intervalo T0–fin", "Historia observada ≥ 60 s", "Acumulador repuntuado"))
    ax.tick_params(length=0, pad=7)
    for row in range(4):
        for col in range(5):
            ax.text(col, row, f"{int(sensitivity[row, col])}/9", ha="center", va="center", fontsize=9,
                    color="white" if sensitivity[row, col] >= 7 else "black")
    fig.text(0.06, 0.93, "Sensibilidad del recálculo por episodio", fontsize=10)
    fig.text(0.06, 0.86, "Mismos nueve episodios; diferentes criterios de atribución o tratamiento de la historia.", fontsize=8)
    fig.text(0.06, 0.15, "T0–fin: exige señal antes del último paquete; dos escaneos dejan de contar como detectados.", fontsize=7.7)
    fig.text(0.06, 0.10, "El acumulador se repuntúa offline: no es un nuevo ensayo en vivo con IF limpio.", fontsize=7.7)
    fig.text(0.06, 0.05, "No se selecciona la variante con mejor resultado. La Tabla 8 y sus condiciones se conservan.", fontsize=7.7)
    return fig, {"name": "sensibilidad", "size_cm": [18, 9]}


def export(fig, info, report):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in fig.findobj(Text):
        if artist.get_visible() and artist.get_text():
            b = artist.get_window_extent(renderer)
            require(b.x0 >= -0.5 and b.y0 >= -0.5 and b.x1 <= fig.bbox.x1 + 0.5 and b.y1 <= fig.bbox.y1 + 0.5,
                    "Texto recortado: " + artist.get_text())
    for ax in fig.axes:
        labels = [label for label in ax.get_xticklabels() if label.get_visible()]
        for a, b in zip(labels, labels[1:]):
            require(not a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)), "Rótulos X solapados")
    info["text_bounds_and_adjacent_xlabels_checked"] = True
    for ext in ("png", "svg", "pdf"):
        buffer = io.BytesIO()
        metadata = {"Date": None, "Creator": "CyberFlow; puntuaciones y señales publicadas " + SOURCE} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None, "Creator": "CyberFlow; evaluación " + SOURCE} if ext == "pdf" else None)
        fig.savefig(buffer, format=ext, dpi=600, metadata=metadata)
        raw = buffer.getvalue()
        if ext == "svg":
            raw = ("\n".join(line.rstrip() for line in raw.decode().splitlines()) + "\n").encode()
        (OUT / (info["name"] + "." + ext)).write_bytes(raw)
    plt.close(fig)
    with Image.open(io.BytesIO((OUT / (info["name"] + ".png")).read_bytes())) as image:
        info["png_pixels"] = list(image.size)
        require(abs(image.info["dpi"][0] - 600) < 0.1, "PNG no es 600 dpi")
    tree = ET.fromstring((OUT / (info["name"] + ".svg")).read_bytes())
    require(not tree.findall(".//{http://www.w3.org/2000/svg}image"), "SVG rasterizado")
    if info["name"] == "componentes":
        ns = {"s": "http://www.w3.org/2000/svg"}
        groups = {node.get("id"): node for node in tree.iter() if node.get("id")}
        width, height = np.asarray(info["size_cm"]) / 2.54 * 72
        l, b, w, h = info["axes"][1]
        for ic, c in enumerate(CONFIGS):
            use = groups["fpr-" + c].find(".//s:use", ns)
            expected_x = (l + w * (100 * report["window_metrics"][c]["FPR"]) / 7.5) * width
            expected_y = (1 - b - h * (4.6 - ic) / 5.2) * height
            require(max(abs(float(use.get("x")) - expected_x), abs(float(use.get("y")) - expected_y)) < 2e-6, "Punto FPR desplazado")
        require(len([k for k in groups if k.startswith("episodio-")]) == 45, "Matriz incompleta en SVG")
    with pymupdf.open(stream=(OUT / (info["name"] + ".pdf")).read_bytes(), filetype="pdf") as doc:
        require(len(doc) == 1 and not doc[0].get_images(), "PDF no vectorial")
        for font in doc[0].get_fonts():
            require(len(doc.extract_font(font[0])[3]) > 0, "Fuente no incrustada")
        for block in doc[0].get_text("blocks"):
            require(doc[0].rect.contains(pymupdf.Rect(block[:4])), "PDF con texto recortado")
        pix = doc[0].get_pixmap(dpi=180)
        preview = "previa.png" if info["name"] == "componentes" else "previa-sens.png"
        (OUT / preview).write_bytes(pix.tobytes("png"))
        with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
            buffer = io.BytesIO()
            image.convert("L").save(buffer, format="PNG")
            (OUT / ("gris.png" if info["name"] == "componentes" else "gris-sens.png")).write_bytes(buffer.getvalue())
    return info


def documentation(report):
    table = ["| Configuración | TP | FP | TN | FN | FPR |", "|---|---:|---:|---:|---:|---:|"]
    for c, m in report["window_metrics"].items():
        table.append(f"| {c} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {100*m['FPR']:.6f} % |")
    text("control.md", "\n".join([
        "# Verificación de las figuras de componentes", "", f"Fuente única: `{SOURCE}`. Sin actualizaciones posteriores al inicio.", "",
        "Se verifican los bytes del commit y los hashes del antecedente/evaluación. En 15 archivos de texto el manifiesto fuente declara hashes de CRLF mientras Git publicó LF: reconstruir CRLF reproduce exactamente esos 15 hashes. No hay diferencias de contenido; los hashes reales LF y la prueba se documentan en control.json. Este nuevo manifiesto usa los bytes publicados, sin modificar el manifiesto original.", "",
        "Se reconstruyen detección y primera señal de cada episodio desde el registro por ventana, se contrasta Tabla 8 y se recalculan las cinco matrices por ventana desde las predicciones guardadas. No se ejecuta otra inferencia ni se reprocesan los PCAP externos.", "",
        "Histórico (solo antecedente, no graficado como actual): modelo contaminado 6/9, heurísticos antiguos 7/9, híbrido 9/9. IF actual: joblib df547da0…, reglas 2026-10-06.2, umbrales −0.5694578968203693 y −0.5898535710336615, operador score_samples < umbral. Los cuantiles se comprueban con 65 553 scores de validación; ninguna validación se usa como evaluación.", "",
        "## Episodios", "", "Tabla 8: 6/9, 6/9, 9/9, 9/9, 9/9. Ambos componentes: 6; solo IF: 0; solo heurísticos: 3; ninguno: 0, en ambos alfas. Fuerza bruta no evaluada: no se dibuja como cero.", "",
        "La fuente usa [T0, último paquete+60 s]. Dos escaneos tienen su primera señal después del último paquete. Si se exige señal dentro de T0–fin, los totales pasan a 4/9, 4/9, 7/9, 7/9, 7/9. Esto es una sensibilidad derivada de marcas publicadas, no una sustitución de Tabla 8 ni otra prueba.", "",
        "La elegibilidad del replay principal se reconstruyó fijando capture_start 60 s antes de la primera observación. No recupera paquetes ausentes. Con historia observada y elegibilidad real los totales son 3/9, 3/9, 7/9, 7/9, 7/9. Al repuntuar el acumulador: 8/9, 6/9, 9/9, 9/9, 9/9; no equivale a un nuevo ensayo en vivo. Las reglas se ajustaron con estos episodios. Se muestran las sensibilidades para no esconder estas dependencias.", "",
        "## Ventanas", "", "65 421 normales +84 ataques, 65 505 claves únicas iguales a Tabla 7. Se conservan 74 normales Kali y 45 558 normales sin paquetes. IF sin guarda operativa, como Tabla 7. Heurísticos e híbrido son señales binarias verificadas, no aplicación de LIMIT/BLOCK. No se atribuye AUC/AP al híbrido.", "", *table, "",
        "El híbrido añade 462/469 FP sin nuevos TP sobre IF. Entre los 84 ataques: ambos 47, solo IF 7, solo heurísticos 0, ninguno 30. No mezclar con los nueve episodios de otra campaña.", "",
        "Control normal de 294,8 s y 61 ventanas, configuración operativa y sensibilidad sin Kali permanecen en los archivos fuente; no se combinan con las métricas de la figura. No se reetiquetan ni se modifican exclusiones.", "",
        "La comprobación de metadatos/exportaciones se guarda en control.json. Reutilizar estos datos no valida de forma independiente la elección de α. Las figuras conservan las limitaciones del análisis de origen.",
    ]) + "\n")
    text("README.md", f"""# Versión gráfica de la sección 4.2

Fuente: [{SOURCE}]({REPOSITORY}/commit/{SOURCE}); revisión gráfica nueva, separada de los datos originales.

Advertencia de trazabilidad: 15 hashes del manifiesto fuente corresponden a saltos CRLF; el commit contiene LF. La equivalencia exacta se verifica y documenta en `control.json`, sin alterar los originales. El manifiesto de estas figuras registra los hashes reales del commit.

- `componentes.png`, `.svg`, `.pdf`: matriz de nueve episodios y FPR de las cinco configuraciones sobre las 65 505 ventanas de Tabla 7. Son poblaciones distintas, indicadas en paneles separados.
- `sensibilidad.png`, `.svg`, `.pdf`: cuatro condiciones de atribución/historia sobre los mismos nueve episodios. No son nuevos experimentos ni una selección del mejor resultado.
- `previa.png`, `previa-sens.png`: renderizados PDF a 180 dpi para inspección al tamaño de inserción; `gris.png`, `gris-sens.png`: control visual en gris.
- `episodios.csv`: 45 registros utilizados, con las cuatro condiciones, primera señal, origen y destino.
- `ventanas.csv`: métricas recalculadas de las cinco configuraciones desde las predicciones completas publicadas.
- `generar.py`: auditoría y generación; `control.md`, `control.json`: verificación y límites; `MANIFIESTO.json`: commits, hashes y versiones.

## Reproducir

Se necesita el historial Git con el commit fuente y el de calibración 4.1. Bibliotecas: numpy, Matplotlib, Pillow y PyMuPDF. No se necesita SSH, PCAP, joblib ni entorno del sensor para reproducir esta imagen, porque se auditan los registros publicados, no la generación original de esos registros.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde `{HERE}`:

```powershell
python generar.py --solo-auditar
python generar.py
```

`--solo-auditar` no escribe archivos. Las imágenes son de 18 cm de ancho a 600 dpi; SVG/PDF vectoriales. No se toca el Word, los modelos, las reglas ni el despliegue.

## Lectura prudente

El histórico 6/9–7/9–9/9 corresponde al IF contaminado y reglas anteriores; no se representa como resultado actual. La principal reproduce la Tabla 8 offline bajo su criterio T0–fin+60 s y elegibilidad reconstruida; el complemento muestra que las detecciones dependen de esas decisiones y de la historia. Ninguna figura presenta el 9/9 como detección durante los nueve ataques o como validación independiente.

FP son señales sobre referencia normal, no bloqueos de usuarios. No se calcula ni asigna ROC-AUC/AP al híbrido. En ventanas, el híbrido no aumenta los TP y sí aumenta FP; en episodios los heurísticos cubren los mismos nueve episodios que el híbrido. El IF llega diez segundos antes que los heurísticos en HTTP-r3, dato disponible en el registro fuente, aunque no se infiera superioridad global de ese caso.
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-auditar", action="store_true")
    args = parser.parse_args()
    report, matrix, sensitivity, episode_rows = audit()
    print("AUDITORÍA OK: 29 archivos de origen; discrepancias CRLF/LF explicadas:", len(report["source_manifest_newline_discrepancies"]))
    print("45 registros de episodio, 65505 predicciones, umbrales y cinco matrices coincidentes; sin diferencias numéricas.")
    print("Tabla 8:", matrix.sum(0).tolist(), "/9")
    print("Sensibilidad T0-fin:", sensitivity[1].tolist(), "/9")
    print("FP:", {c: m["FP"] for c, m in report["window_metrics"].items()})
    if args.solo_auditar:
        return
    save_csv("episodios.csv", episode_rows)
    save_csv("ventanas.csv", [{"configuracion": c, **m} for c, m in report["window_metrics"].items()])
    report["exports"] = [export(*draw_main(report, matrix), report), export(*draw_sensitivity(sensitivity), report)]
    save_json("control.json", report)
    documentation(report)
    files = [p for p in OUT.iterdir() if p.is_file() and p.name != "MANIFIESTO.json"]
    save_json("MANIFIESTO.json", {"source_commit": SOURCE, "calibration_reference": DATA41, "repository": REPOSITORY,
               "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "no_later_updates_at_start": True,
               "versions": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__,
                            "Pillow": PIL.__version__, "PyMuPDF": pymupdf.VersionBind},
               "inputs_sha256": report["input_sha256"], "outputs_sha256": {p.name: sha(p.read_bytes()) for p in sorted(files)},
               "raw_replay_repeated": False, "original_results_modified": False, "word_modified": False, "deployment_modified": False,
               "self_hash": "Omitido para evitar autorreferencia; Git identifica el manifiesto."})
    for p in sorted(OUT.iterdir()):
        if p.is_file():
            print(str(HERE / p.name))


if __name__ == "__main__":
    main()
