from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score, roc_curve, precision_recall_curve


ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "03-entregables" / "13-respuesta-observaciones-validacion-interna" / "seccion4-resultados" / "_campana" / "resultados-2026-10-23" / "eval41" / "v2"
FULL = OUT / "scores-todos-candidatos-full.csv.gz"
METRICS = OUT / "metricas.json"
P1 = OUT / "p1-reconciliacion.json"
P3 = OUT / "p3-ventanas-cero.json"
MANIFEST = OUT / "run-manifest.json"
EDITORIAL = OUT.parent.parent.parent.parent / "4.1-modelos"

EXPECTED_HASH = "6e98219fb79a187b7256e664a4791a0619be70a68d9a23eee1e61c45de98ffc8"
NORMAL = 65421
ATTACK = 84
TOTAL = NORMAL + ATTACK


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_scores() -> tuple[list[dict[str, str]], list[str]]:
    with gzip.open(FULL, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    if len(rows) != 65505:
        raise ValueError(f"Se esperaban 65505 filas, se obtuvieron {len(rows)}")
    if len({row["idx"] for row in rows}) != len(rows):
        raise ValueError("Hay índices repetidos en el respaldo completo")
    if sum(row["label"] == "1" for row in rows) != ATTACK:
        raise ValueError("El número de ventanas de ataque no coincide con 84")
    if sum(row["label"] == "0" for row in rows) != NORMAL:
        raise ValueError("El número de ventanas normales no coincide con 65421")
    return rows, fields


def model_metrics(rows: list[dict[str, str]], field: str, threshold: float) -> dict[str, float | int]:
    y = np.asarray([int(row["label"]) for row in rows])
    scores = np.asarray([float(row[field]) for row in rows], dtype=float)
    if not np.isfinite(scores).all():
        raise ValueError(f"Valores no finitos en {field}")
    pred = scores < threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    anomaly = -scores
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {
        "TP": int(tp),
        "FP": int(fp),
        "TN": int(tn),
        "FN": int(fn),
        "precision": precision,
        "recall": recall,
        "F1": f1,
        "FPR": fpr,
        "roc_auc": float(roc_auc_score(y, anomaly)),
        "average_precision": float(average_precision_score(y, anomaly)),
    }


def update_alpha_outputs() -> dict[str, object]:
    p1 = json.loads(P1.read_text(encoding="utf-8"))
    values = []
    for entry in p1["alfa_val_total"]:
        values.append({
            "alfa": entry["alfa"],
            "umbral": entry["umbral"],
            "fpr_obs": entry["fpr_obs"],
            "recall": entry["recall"],
            "precision": entry["precision"],
            "F1": entry["F1"],
        })
    with (OUT / "ALFA-F6.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["alfa", "umbral", "fpr_obs", "recall", "precision", "F1"])
        writer.writeheader()
        writer.writerows(values)
    return {"n_val": p1["n_val_total"], "values": values}


def update_metrics(alpha: dict[str, object]) -> dict[str, object]:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    metrics["alfa_sensibilidad"] = alpha["values"]
    metrics["alfa_sensibilidad_n_val"] = alpha["n_val"]
    metrics["alfa_sensibilidad_n_val_complementaria"] = json.loads(P1.read_text(encoding="utf-8"))["n_val_sin_kali"]
    METRICS.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics


def make_figure(rows: list[dict[str, str]], metrics: dict[str, object]) -> None:
    names = []
    for item in metrics["tabla7"]:
        names.append((item["modelo"], item["sha256"], item["umbral"]))
    y = np.asarray([int(row["label"]) for row in rows])
    colors = plt.cm.tab10(np.linspace(0, 1, len(names)))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), constrained_layout=True)
    for (name, _, threshold), color in zip(names, colors):
        field = f"score::{name}"
        score = np.asarray([float(row[field]) for row in rows], dtype=float)
        anomaly = -score
        fpr, tpr, _ = roc_curve(y, anomaly)
        precision, recall, _ = precision_recall_curve(y, anomaly)
        axes[0].plot(fpr, tpr, color=color, linewidth=1.7, label=name)
        axes[1].plot(recall, precision, color=color, linewidth=1.7, label=name)
    prevalence = ATTACK / TOTAL
    axes[0].plot([0, 1], [0, 1], color="#999999", linestyle="--", linewidth=0.9)
    axes[1].axhline(prevalence, color="#999999", linestyle="--", linewidth=0.9, label=f"Prevalencia = {prevalence:.3%}")
    axes[0].set_title("(a) Curva ROC")
    axes[1].set_title("(b) Curva precisión-recall")
    axes[0].set_xlabel("Tasa de falsos positivos")
    axes[0].set_ylabel("Recall / TPR")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precisión")
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1.02)
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1.02)
    axes[0].grid(alpha=0.2)
    axes[1].grid(alpha=0.2)
    axes[1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=7, frameon=False)
    fig.suptitle("Comparación de configuraciones sobre 65 505 ventanas", fontsize=13)
    fig.savefig(OUT / "figura-roc-pr-v2.png", dpi=300)
    fig.savefig(OUT / "figura-roc-pr-v2.svg")
    fig.savefig(OUT / "figura-roc-pr-v2.pdf")
    plt.close(fig)


def write_editorial(metrics: dict[str, object], p1: dict[str, object], p3: dict[str, object]) -> None:
    clean = metrics["tabla6_clean"]
    text = f"""# Base editorial para la sección 4.1

Fecha de cierre: 2026-10-23. Este documento no sustituye la sección 4 del Word; sirve como base verificable para redactarla sin inventar resultados.

## A. Presentación de la evaluación

Se evaluó el modelo operativo `if_limpio_2026_10`, un Pipeline congelado con escalador, Isolation Forest y umbral `score_samples < -0,5693969936322356`. La unidad de análisis es la ventana temporal de 10 s por entidad, no el episodio. El conjunto evaluado contiene 65 421 ventanas normales de prueba y 84 ventanas etiquetadas como ataque, para 65 505 observaciones. La evaluación es reutilizada: el conjunto ya participó en decisiones de desarrollo el 14/10/2026 y no constituye un test ciego independiente.

La calibración se realizó sobre 65 633 ventanas de validación. Este conjunto incluye 80 ventanas de la entidad Kali, 17 con actividad observable. No se encontró evidencia independiente que permita confirmar que esas 17 ventanas correspondan a ataques; se conservan como parte de la calibración operativa, pero su normalidad no está verificada.

## B. Tabla 6: IF limpio

| Indicador | Valor |
|---|---:|
| TP | {clean['TP']} |
| FP | {clean['FP']} |
| TN | {clean['TN']} |
| FN | {clean['FN']} |
| Precisión | {clean['precision']:.4%} |
| Recall | {clean['recall']:.4%} |
| F1 | {clean['F1']:.4f} |
| FPR | {clean['FPR']:.4%} |
| ROC-AUC | {clean['roc_auc']:.4f} |
| AP | {clean['average_precision']:.4f} |

## C. Interpretación

El IF detectó 54 de 84 ventanas etiquetadas como ataque y produjo 2 961 falsas alarmas sobre 65 421 ventanas normales. La precisión fue 54/(54+2 961) = 1,79 %. La baja precisión no debe ocultarse: la prevalencia fue 84/65 505 = 0,128 %, por lo que un FPR de 4,53 % genera muchas más alarmas normales que verdaderos positivos. ROC-AUC mide la capacidad de ordenar observaciones normales y anómalas; no garantiza que el umbral operativo tenga buena precisión. Aunque el sistema traduzca una señal aislada del IF a LIMIT reversible, LIMIT también puede afectar tráfico legítimo y su costo no se resuelve con la métrica de ranking.

## D. Tabla 7: configuraciones

La comparación usa las mismas 65 505 ventanas y el umbral propio de cada configuración. Los candidatos de laboratorio y los modelos entrenados con datos de esta red tienen distinto origen; por tanto, el resultado mide transferencia al entorno objetivo, no superioridad intrínseca de Isolation Forest. IF limpio y IF contaminado detectaron ambos 54/84, pero difirieron en FP, ROC-AUC y AP. No se afirma equivalencia estadística ni superioridad. IF uniform e IF exact son variantes idénticas y deben presentarse como una única configuración con duplicación documentada.

## E. Figura ROC/PR

La figura muestra el comportamiento de ranking de las nueve configuraciones usando los scores de precisión completa. El panel (a) resume ROC-AUC y el panel (b) muestra precisión frente a recall con la prevalencia real de 0,128 % como referencia. La figura no reemplaza la decisión en el umbral congelado: una curva favorable puede coexistir con una precisión operativa baja.

## F. Sensibilidad y ventanas sin actividad

Los cortes de sensibilidad se calcularon sobre la validación original de 65 633 y se aplicaron a test; alpha = 0,05 reproduce el umbral operativo y no se presenta como óptimo. Al reducir alpha disminuyen simultáneamente FPR y recall; al aumentarlo, el recall sube con un costo mayor en FPR. La validación sin Kali, de 65 553 ventanas, es únicamente complementaria.

En la auditoría del test normal, 19 863 ventanas tuvieron paquetes en los últimos 10 s y presentaron 2 837 FP, FPR 14,28 %. Otras 12 208 no tuvieron paquetes recientes pero sí actividad retrospectiva y presentaron 124 FP. Las 33 350 restantes no mostraron actividad en los contadores revisados y presentaron 0 FP. El 4,53 % global depende de esta composición. Offline, el evaluador puntúa todas las ventanas; en vivo, una ventana sin paquetes omite el IF, pero todavía puede pasar por la evaluación de heurísticos antes de determinar la acción final. Por ello los 124 FP no son directamente el FPR operativo del sistema completo.

## G. Limitaciones

- La evaluación está reutilizada y no es un test ciego independiente.
- Las 80 ventanas Kali dentro de validación incluyen actividad observable, pero no tienen confirmación independiente de ser ataques.
- Las familias de ataque son proxies observables; no deben presentarse como ground truth confirmado.
- La evaluación de 4.1 corresponde al IF solo; el híbrido pertenece a 4.2.
- Los resultados no se extrapolan automáticamente a otra red ni a IPv6.

## Matriz de afirmaciones

| Afirmación permitida | Evidencia | Limitación |
|---|---|---|
| IF limpio detecta 54/84 y obtiene FPR 4,53 % en esta evaluación. | Tabla 6 y `metricas.json`. | Evaluación reutilizada; FPR del IF offline, no del sistema completo. |
| La precisión es 1,79 % con 2 961 FP. | Matriz de confusión de Tabla 6. | Prevalencia 0,128 %; LIMIT no elimina el costo de falsos positivos. |
| Los candidatos de laboratorio transfieren mal a esta red. | Tabla 7: FPR de 29,07 % a 99,57 %. | No demuestra superioridad intrínseca de IF. |
| Alpha = 0,05 reproduce el umbral operativo. | `p1-reconciliacion.json` y `ALFA-F6.csv`. | No demuestra que sea óptimo; no hubo meta de aceptación previa más específica. |
| El FPR global depende de ventanas con y sin actividad reciente. | `p3-ventanas-cero.json`. | Offline y motor vivo no aplican exactamente la misma ruta de decisión. |

## Correcciones necesarias en el Word

1. Sustituir en el resumen y palabras clave `One-Class SVM` por `Isolation Forest` cuando describan el modelo operativo.
2. En 3.3.3, después de `Validación: 65 633`, añadir que incluye 80 ventanas de Kali, 17 con actividad observable, sin confirmarlas como ataques.
3. En 3.3.5, conservar que el umbral no usa test ni ataque para seleccionarse, pero añadir que la composición de validación contiene esas 80 ventanas de normalidad no verificada.
4. En 3.3.7 y Tabla 5, añadir que la evaluación de 65 505 ventanas es reutilizada y que la unidad primaria es la ventana; la cobertura por episodio pertenece al análisis complementario.
5. En 3.6 y Tabla 5, cambiar `ataques identificados por familia` por `ventanas de actividad etiquetadas por familia proxy observable`.
6. Insertar la Tabla 6, Tabla 7, la figura ROC/PR y este bloque de limitaciones en la sección 4.1, que todavía no aparece en el Word revisado.

## Estado

- VERIFICADO: hash, filas, scores completos, matrices y métricas.
- CORREGIDO: sensibilidad alpha, figura y manifiesto editorial.
- CONSERVADO: modelo, escalador, umbral y despliegue sin cambios.
- PENDIENTE: incorporar estos textos y tablas al Word; test ciego independiente; confirmación externa de familias; replay ET Open no pertenece a 4.1.
"""
    (EDITORIAL / "BASE-EDITORIAL-4.1.md").write_text(text, encoding="utf-8")


def write_manifest(metrics: dict[str, object], fields: list[str], alpha: dict[str, object]) -> None:
    files = [
        "scores-todos-candidatos-full.csv.gz",
        "TABLA6.md",
        "TABLA7.md",
        "ALFA-F6.csv",
        "ALFA-F6.md",
        "metricas.json",
        "figura-roc-pr-v2.png",
        "figura-roc-pr-v2.svg",
        "figura-roc-pr-v2.pdf",
    ]
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_scores": {"file": FULL.name, "sha256": sha256(FULL), "rows": 65505, "fields": fields},
        "expected_hash_match": sha256(FULL) == EXPECTED_HASH,
        "metrics_source": "metricas.json + recomputacion directa desde scores-todos-candidatos-full.csv.gz",
        "figure_script": "cerrar_pendientes_41.py",
        "figure_method": "ROC y precision-recall sobre score=-score_samples; todas las observaciones; prevalencia 84/65505",
        "alpha_source": {"file": "p1-reconciliacion.json", "n_val": alpha["n_val"]},
        "files": {name: sha256(OUT / name) for name in files},
        "model_or_deployment_changes": False,
    }
    (OUT / "MANIFIESTO-4.1-CANONICO.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    actual_hash = sha256(FULL)
    if actual_hash != EXPECTED_HASH:
        raise ValueError(f"Hash inesperado: {actual_hash}")
    rows, fields = load_scores()
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    for item in metrics["tabla7"]:
        field = f"score::{item['modelo']}"
        actual = model_metrics(rows, field, float(item["umbral"]))
        for key in ("TP", "FP", "TN", "FN"):
            if actual[key] != item[key]:
                raise ValueError(f"{item['modelo']} {key}: archivo={actual[key]} metricas={item[key]}")
        for key in ("roc_auc", "average_precision", "precision", "recall", "F1", "FPR"):
            if not math.isclose(actual[key], float(item[key]), rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"{item['modelo']} {key}: archivo={actual[key]} metricas={item[key]}")
    alpha = update_alpha_outputs()
    metrics = update_metrics(alpha)
    make_figure(rows, metrics)
    write_manifest(metrics, fields, alpha)
    write_editorial(metrics, json.loads(P1.read_text(encoding="utf-8")), json.loads(P3.read_text(encoding="utf-8")))
    print(json.dumps({"hash": actual_hash, "rows": len(rows), "models": 9, "alpha_n_val": alpha["n_val"], "figure": ["png", "svg", "pdf"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
