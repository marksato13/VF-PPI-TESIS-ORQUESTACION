#!/usr/bin/env python3
"""Tabla 7-c (alfa = 0,01) para los cinco detectores, con los MISMOS artefactos y protocolo que 7-a/7-b.

Reutiliza las puntuaciones por metodo ya publicadas (salidas/puntuaciones-<METODO>.csv.gz), cuyos hashes se
VERIFICAN contra MANIFIESTO-COMPARACION.json. No reentrena, no re-puntua, no toca modelos, figuras, Word,
servicios ni las tablas 7-a/7-b. Solo anade alfa=0,01: umbral propio por modelo = cuantil 1-alfa (lineal) de
SUS puntuaciones de validacion; anomalia si puntuacion > umbral (misma regla y orientacion que la comparacion).

Uso: python tabla7c_alfa001.py
"""
import csv, gzip, hashlib, json, pathlib
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

AQUI = pathlib.Path(__file__).resolve().parent
SAL = AQUI / "salidas"
MAN = json.loads((AQUI / "MANIFIESTO-COMPARACION.json").read_text(encoding="utf-8"))
METODOS = ["IF", "OCSVM", "LOF", "EllipticEnvelope", "PCA"]   # mismo orden que 7-a/7-b
ALFA = 0.01
N_VAL, N_NOR, N_ATA = 65553, 65421, 84
# ROC-AUC / AP de la comparacion (resultados-comparacion.json); deben coincidir (solo cambia el umbral)
REF_AUC_AP = {
    "IF": (0.9247265513258084, 0.18580688397625872),
    "OCSVM": (0.869071457322936, 0.6356616971916291),
    "LOF": (0.9762796422584565, 0.029066072188399145),
    "EllipticEnvelope": (0.9179326428604184, 0.3811037448703374),
    "PCA": (0.9486616355167738, 0.5944055724226315),
}
# comprobacion previa del IF (enunciado), escala score_samples; se reproduce, no se fuerza
REF_IF = {"umbral_escala_original": -0.6223889502095352, "TP": 50, "FP": 567, "TN": 64854, "FN": 34}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha_lf(p):
    b = pathlib.Path(p).read_bytes()
    if pathlib.Path(p).suffix.lower() in (".md", ".csv", ".json", ".py"):
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def leer_gz(p):
    with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clave(r):
    return (r["campaign_id"], r["entity_ip"], r["window_end_utc"])


def main():
    datos = {}
    claves = {}
    for m in METODOS:
        p = SAL / ("puntuaciones-%s.csv.gz" % m)
        h = sha(p)
        esperado = MAN["salidas_sha256"]["salidas/puntuaciones-%s.csv.gz" % m]
        assert h == esperado, "hash distinto en %s (no son los mismos artefactos de 7-a/7-b)" % m
        rows = leer_gz(p)
        g = {c: [r for r in rows if r["conjunto"] == c] for c in ("validacion", "prueba_normal", "ataque")}
        assert (len(g["validacion"]), len(g["prueba_normal"]), len(g["ataque"])) == (N_VAL, N_NOR, N_ATA), m
        datos[m] = {c: np.array([float(r["puntuacion_anomalia"]) for r in g[c]]) for c in g}
        claves[m] = {c: [clave(r) for r in g[c]] for c in g}

    # mismas claves de ventana para los cinco modelos (y mismo orden)
    base = claves[METODOS[0]]
    mismas_claves = all(claves[m][c] == base[c] for m in METODOS for c in ("validacion", "prueba_normal", "ataque"))
    assert mismas_claves, "las claves de ventana difieren entre modelos"

    filas, umbrales, verif = [], {}, {}
    for m in METODOS:
        sv, sn, sa = datos[m]["validacion"], datos[m]["prueba_normal"], datos[m]["ataque"]
        thr = float(np.quantile(sv, 1 - ALFA, method="linear"))
        tp = int(np.sum(sa > thr)); fn = N_ATA - tp
        fp = int(np.sum(sn > thr)); tn = N_NOR - fp
        assert tp + fn == 84 and fp + tn == 65421, m
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / 84
        f1 = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        f1_harm = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        assert abs(f1 - f1_harm) < 1e-12, m
        fpr_prueba = fp / 65421
        fpr_val = float(np.mean(sv > thr))
        y = np.r_[np.zeros(N_NOR), np.ones(N_ATA)]; sc = np.r_[sn, sa]
        auc = float(roc_auc_score(y, sc)); ap = float(average_precision_score(y, sc))
        ref_auc, ref_ap = REF_AUC_AP[m]
        assert abs(auc - ref_auc) < 1e-9 and abs(ap - ref_ap) < 1e-9, "AUC/AP no coincide en %s" % m
        orig = None if m == "PCA" else -thr   # escala original = score_samples (para los que usan -score_samples)
        filas.append(dict(metodo=m, TP=tp, FP=fp, TN=tn, FN=fn, precision=prec, recall=rec, F1=f1,
                          FPR_validacion=fpr_val, FPR_prueba=fpr_prueba, roc_auc=auc, ap=ap,
                          empates_validacion=int(np.sum(sv == thr)),
                          empates_evaluacion=int(np.sum(sn == thr) + np.sum(sa == thr))))
        umbrales[m] = {"umbral_anomalia": repr(thr),
                       "umbral_escala_original": (None if orig is None else repr(orig)),
                       "regla": ("error de reconstruccion > umbral" if m == "PCA" else "-score_samples > umbral  (== score_samples < -umbral)"),
                       "convencion_puntuacion": "mayor = mas anomalo"}
    # verificacion IF
    fIF = next(f for f in filas if f["metodo"] == "IF")
    verif["IF"] = {"umbral_escala_original": {"esperado": REF_IF["umbral_escala_original"],
                                              "obtenido": float(umbrales["IF"]["umbral_escala_original"]),
                                              "coincide": abs(float(umbrales["IF"]["umbral_escala_original"]) - REF_IF["umbral_escala_original"]) < 1e-12}}
    for k in ("TP", "FP", "TN", "FN"):
        verif["IF"][k] = {"esperado": REF_IF[k], "obtenido": fIF[k], "coincide": fIF[k] == REF_IF[k]}

    # ---- CSV (columnas del enunciado + FPR val. + empates, conservando las de 7-a/7-b) ----
    cols = ["metodo", "TP", "FP", "TN", "FN", "precision_pct", "recall_pct", "F1",
            "FPR_validacion_pct", "FPR_prueba_pct", "roc_auc", "ap", "umbral_anomalia", "umbral_escala_original",
            "empates_validacion", "empates_evaluacion"]
    with open(AQUI / "TABLA7c-alfa0.01.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(cols)
        for f in filas:
            w.writerow([f["metodo"], f["TP"], f["FP"], f["TN"], f["FN"],
                        round(100 * f["precision"], 2), round(100 * f["recall"], 2), round(f["F1"], 4),
                        round(100 * f["FPR_validacion"], 2), round(100 * f["FPR_prueba"], 2),
                        repr(f["roc_auc"]), repr(f["ap"]),
                        umbrales[f["metodo"]]["umbral_anomalia"], umbrales[f["metodo"]]["umbral_escala_original"],
                        f["empates_validacion"], f["empates_evaluacion"]])

    pct = lambda x: ("%.2f %%" % (100 * x)).replace(".", ",")
    num = lambda x, d=4: ("%.*f" % (d, x)).replace(".", ",")
    mil = lambda n: "{:,}".format(n).replace(",", " ")
    L = ["# Tabla 7-c — Comparación de detectores con α = 0,01 (evaluación por ventana)", "",
         "Mismos artefactos y protocolo que las Tablas 7-a (α=0,05) y 7-b (α=0,03): entrenamiento 203 967 ventanas "
         "elegibles (181 excluidas), validación 65 553 para calibrar, evaluación 65 421 normales + 84 ataques = 65 505, "
         "mismas 28 características y escalador congelado. Umbral **propio por modelo** = cuantil 1−α (interpolación "
         "lineal) de SUS puntuaciones de validación; anomalía si puntuación > umbral. Se reutilizan las puntuaciones "
         "ya publicadas (`salidas/puntuaciones-*.csv.gz`, hashes verificados); **no** se reentrena ni se re-puntúa. "
         "ROC-AUC y AP se calculan con las puntuaciones continuas orientadas a anomalía y **no dependen de α** "
         "(coinciden con 7-a/7-b). Precisión/recall/FPR en %; F1, ROC-AUC y AP en escala 0–1.", "",
         "| Método | TP | FP | TN | FN | Precisión | Recall | F1 | FPR val. | FPR prueba | ROC-AUC | AP |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in filas:
        L.append("| %s | %d | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
            f["metodo"], f["TP"], mil(f["FP"]), mil(f["TN"]), f["FN"], pct(f["precision"]), pct(f["recall"]),
            num(f["F1"]), pct(f["FPR_validacion"]), pct(f["FPR_prueba"]), num(f["roc_auc"]), num(f["ap"])))
    L += ["",
          "Verificado por fila: TP+FN=84, FP+TN=65 421, Precisión=TP/(TP+FP), Recall=TP/84, F1=2TP/(2TP+FP+FN), "
          "FPR prueba=FP/65 421. FPR val. = FP_validación/65 553 (≈ α por construcción).",
          "IF reproduce la comprobación previa: umbral (escala `score_samples`) = −0,622388950209535 (coincide con "
          "−0,6223889502095352 hasta 1e−12; la diferencia de último dígito viene de negar la escala de anomalía), "
          "TP=50, FP=567, TN=64 854, FN=34 (exactos).",
          "ROC-AUC/AP idénticos a 7-a/7-b (mismas puntuaciones, solo cambia el umbral).", "",
          "## Umbrales (precisión completa en `umbrales-7c-precision-completa.json`)", "",
          "| Método | Umbral (anomalía, >) | Umbral escala original (`score_samples <`) |",
          "|---|---:|---:|"]
    for m in METODOS:
        L.append("| %s | `%s` | %s |" % (m, umbrales[m]["umbral_anomalia"],
                  "—" if umbrales[m]["umbral_escala_original"] is None else "`%s`" % umbrales[m]["umbral_escala_original"]))
    (AQUI / "TABLA7c-alfa0.01.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

    # ---- umbrales precision completa ----
    (AQUI / "umbrales-7c-precision-completa.json").write_text(json.dumps({
        "alfa": ALFA, "n_validacion": N_VAL,
        "procedimiento": "umbral = numpy.quantile(puntuacion_anomalia_validacion, 1-alfa, method='linear') por modelo; "
                         "anomalia si puntuacion > umbral; puntuacion mayor = mas anomalo; clasificacion con precision completa.",
        "umbrales": umbrales}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # ---- nota ----
    nota = ["# Nota — Tabla 7-c (α = 0,01): detección frente a falsas alarmas", "",
            "## Procedencia",
            "Mismos datos, modelos, escalador y puntuaciones que las Tablas 7-a/7-b (`salidas/puntuaciones-*.csv.gz`, "
            "hashes verificados contra `MANIFIESTO-COMPARACION.json`). Solo cambia el umbral: cuantil 0,99 de la "
            "puntuación de validación de **cada** modelo (no se aplica el umbral del IF a los demás). No se reentrena, "
            "no se re-puntúa, no se tocan 7-a/7-b, figuras, Word, servicios ni configuración desplegada.", "",
            "## Lectura (sin anticipar un ganador)",
            "Bajar α a 0,01 sube el umbral y reduce las alertas: respecto a 0,03/0,05 caen los FP y, en la mayoría de "
            "modelos, también algún TP. ROC-AUC y AP **no cambian** (no dependen del umbral), así que el orden por "
            "capacidad de ranking es el mismo que en 7-a/7-b; lo que cambia es el punto de operación.",
            "Los conteos son **por ventana**, no por episodio: perder una ventana no equivale a perder un ataque "
            "completo. La cobertura por episodio y la detección durante el ataque **no** se pueden comprobar con estos "
            "datos (el conjunto de ataques no trae escenario/episodio) y quedan pendientes de la campaña A.",
            "No se afirma que el IF sea el mejor; cada modelo se reporta con sus TP/FP y sus AUC/AP, incluidos los "
            "desfavorables (p. ej. AP muy baja de LOF pese a su recall alto).", "",
            "## Límite de interpretación",
            "Estos datos ya se usaron para **orientar** la elección de α; por tanto, elegir aquí el “mejor” punto **no** "
            "es una confirmación independiente. La decisión operativa de α no se cambia en este entregable.", ""]
    (AQUI / "NOTA-TABLA7C.md").write_text("\n".join(nota) + "\n", encoding="utf-8", newline="\n")

    # ---- manifiesto propio (no modifica MANIFIESTO-COMPARACION.json) ----
    salidas = ["tabla7c_alfa001.py", "TABLA7c-alfa0.01.csv", "TABLA7c-alfa0.01.md",
               "umbrales-7c-precision-completa.json", "NOTA-TABLA7C.md"]
    import datetime
    manc = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "proposito": "Tabla 7-c (alfa=0,01) anadida con los mismos artefactos y protocolo que 7-a/7-b; no modifica "
                         "las tablas previas, modelos, figuras, Word ni configuracion desplegada.",
            "alfa": ALFA, "mismas_claves_de_ventana_los_5_modelos": mismas_claves,
            "entradas_verificadas_sha256": {("salidas/puntuaciones-%s.csv.gz" % m): MAN["salidas_sha256"]["salidas/puntuaciones-%s.csv.gz" % m] for m in METODOS},
            "manifiesto_comparacion_referencia": "MANIFIESTO-COMPARACION.json (no modificado)",
            "roc_auc_ap_coinciden_con_7a_7b": {m: {"roc_auc": REF_AUC_AP[m][0], "ap": REF_AUC_AP[m][1]} for m in METODOS},
            "verificacion_IF": verif["IF"],
            "salidas_sha256_lf": {n: sha_lf(AQUI / n) for n in salidas}}
    (AQUI / "MANIFIESTO-TABLA7C.json").write_text(json.dumps(manc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print("mismas_claves_5_modelos:", mismas_claves)
    print("verificacion_IF:", json.dumps(verif["IF"], ensure_ascii=False))
    print("\nTABLA 7-c (alfa=0,01):")
    for f in filas:
        print("  %-16s TP=%2d FP=%4d TN=%5d FN=%2d prec=%.2f%% rec=%.2f%% F1=%.4f FPRval=%.2f%% FPRprueba=%.2f%% AUC=%.4f AP=%.4f emp_val=%d" % (
            f["metodo"], f["TP"], f["FP"], f["TN"], f["FN"], 100*f["precision"], 100*f["recall"], f["F1"],
            100*f["FPR_validacion"], 100*f["FPR_prueba"], f["roc_auc"], f["ap"], f["empates_validacion"]))


if __name__ == "__main__":
    main()
