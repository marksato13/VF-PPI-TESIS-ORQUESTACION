#!/usr/bin/env python3
"""Sensibilidad de alfa del IF congelado if_limpio_2026_10, con y sin las 80 ventanas Kali de validacion.

Entradas (todas con hash en el manifiesto):
  datos-sensor/  puntuaciones calculadas en el sensor con el pipeline desplegado (sensor_calib.py)
  ../../_campana/resultados-2026-10-23/eval41/v2/scores-todos-candidatos-full.csv.gz  (export canonico 4.1)
  ../../_campana/resultados-2026-10-23/eval41/v2/metricas.json                         (ROC-AUC/AP canonicos)

No reentrena, no toca el modelo ni el escalador, no usa prueba ni ataques para fijar umbrales.
Uso:  python calibrar_alfa.py
"""
import csv, gzip, hashlib, json, pathlib, subprocess, datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, precision_recall_curve

AQUI = pathlib.Path(__file__).resolve().parent
SEN = AQUI / "datos-sensor"
V2 = AQUI.parent.parent / "_campana" / "resultados-2026-10-23" / "eval41" / "v2"
EXPORT = V2 / "scores-todos-candidatos-full.csv.gz"
METRICAS = V2 / "metricas.json"
KALI = "10.10.20.30"
ALFAS = [0.01, 0.02, 0.025, 0.03, 0.04, 0.05, 0.10]
U_OP = -0.5693969936322356
REF_INDEP = {  # comprobacion independiente previa (enunciado), se reproduce, no se fuerza
    0.03: dict(umbral=-0.5898535710336618, TP=54, FN=30, FP=1723, TN=63698),
    0.05: dict(umbral=-0.5694578968203694, TP=54, FN=30, FP=2955, TN=62466),
}
COL_IF = "score::IF limpio (desplegado)"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def leer_gz(p):
    with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clave(r):
    return (r["campaign_id"], r["entity_ip"], r["window_end_utc"])


def q(a, alfa):
    return float(np.quantile(a, alfa, method="linear"))


def metricas(thr, s_norm, s_ata):
    tp = int(np.sum(s_ata < thr)); fn = len(s_ata) - tp
    fp = int(np.sum(s_norm < thr)); tn = len(s_norm) - fp
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn)
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(TP=tp, FN=fn, FP=fp, TN=tn, precision=prec, recall=rec, F1=f1, FPR=fp / (fp + tn))


def git(repo, *a):
    try:
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return "no disponible (%s)" % e.__class__.__name__


def escribir(p, texto):
    p.write_text(texto, encoding="utf-8", newline="\n")


def main():
    proc = json.loads((SEN / "sensor-procedencia.json").read_text(encoding="utf-8"))
    for nombre, h in proc["salidas_sha256"].items():          # integridad de lo traido del sensor
        assert sha(SEN / nombre) == h, nombre

    val = leer_gz(SEN / "scores-validacion-65633.csv.gz")
    nor = leer_gz(SEN / "scores-prueba-normal-65421.csv.gz")
    ata = leer_gz(SEN / "scores-ataques-84.csv.gz")
    assert (len(val), len(nor), len(ata)) == (65633, 65421, 84)
    sv = np.array([float(r["score_samples"]) for r in val])
    kali = np.array([r["entity_ip"] == KALI for r in val])
    sv_nk, sv_k = sv[~kali], sv[kali]
    sn = np.array([float(r["score_samples"]) for r in nor])
    sa = np.array([float(r["score_samples"]) for r in ata])
    assert kali.sum() == 80 and len(sv_nk) == 65553

    # --- alineacion con el export canonico de 4.1 (mismo modelo, mismas ventanas, mismos scores)
    exp = leer_gz(EXPORT)
    e_nor = {clave(r): float(r[COL_IF]) for r in exp if r["label"] in ("0", "normal", "benigno")}
    e_ata = {clave(r): float(r[COL_IF]) for r in exp if r["label"] not in ("0", "normal", "benigno")}
    alin = {"filas_export": len(exp), "normales_export": len(e_nor), "ataques_export": len(e_ata)}
    alin["claves_normales_iguales"] = set(e_nor) == {clave(r) for r in nor}
    alin["claves_ataques_iguales"] = set(e_ata) == {clave(r) for r in ata}
    alin["max_abs_dif_normales"] = max(abs(e_nor[clave(r)] - float(r["score_samples"])) for r in nor)
    alin["max_abs_dif_ataques"] = max(abs(e_ata[clave(r)] - float(r["score_samples"])) for r in ata)
    y = np.r_[np.zeros(len(sn)), np.ones(len(sa))]; s = -np.r_[sn, sa]
    can = json.loads(METRICAS.read_text(encoding="utf-8"))
    auc, ap = float(roc_auc_score(y, s)), float(average_precision_score(y, s))
    alin["roc_auc_recalculado"], alin["ap_recalculado"] = auc, ap
    alin["roc_auc_canonico"], alin["ap_canonico"] = can_if(can, "roc_auc"), can_if(can, "average_precision")

    # --- sensibilidad de alfa (umbral solo desde validacion)
    filas = []
    for etq, base in (("validacion_original_65633", sv), ("validacion_sin_kali_65553", sv_nk)):
        for a in ALFAS:
            thr = q(base, a)
            m = metricas(thr, sn, sa)
            filas.append(dict(validacion=etq, n_validacion=len(base), alfa=a, umbral=thr,
                              fpr_en_validacion=float(np.mean(base < thr)), **m))

    # --- reproduccion de la comprobacion previa e identidades 0,03 vs 0,05
    def fila(etq, a):
        return next(f for f in filas if f["validacion"] == etq and f["alfa"] == a)
    repro = {}
    for a, ref in REF_INDEP.items():
        f = fila("validacion_sin_kali_65553", a)
        repro[str(a)] = {k: {"esperado": v, "obtenido": f[k], "coincide": (abs(f[k] - v) < 1e-12 if k == "umbral" else f[k] == v)}
                         for k, v in ref.items()}
    t03, t05 = fila("validacion_sin_kali_65553", 0.03)["umbral"], fila("validacion_sin_kali_65553", 0.05)["umbral"]
    pos03 = {clave(r) for r, x in zip(ata, sa) if x < t03}
    pos05 = {clave(r) for r, x in zip(ata, sa) if x < t05}
    fp03 = {clave(r) for r, x in zip(nor, sn) if x < t03}
    fp05 = {clave(r) for r, x in zip(nor, sn) if x < t05}
    ident = {"umbral_003": t03, "umbral_005": t05,
             "tp_003": len(pos03), "tp_005": len(pos05), "tp_identicos": pos03 == pos05,
             "fp_003": len(fp03), "fp_005": len(fp05), "fp_003_subconjunto_de_005": fp03 <= fp05,
             "fp_que_se_eliminan": len(fp05 - fp03),
             "ataques_entre_umbrales": int(np.sum((sa >= t03) & (sa < t05))),
             "score_ataque_detectado_mas_alto": float(max(x for x in sa if x < t05)),
             "score_ataque_no_detectado_mas_bajo": float(min(x for x in sa if x >= t05)),
             "ventanas_tp": sorted("|".join(k) for k in pos05)}
    ident["alfa_003_vs_005_validacion_original"] = {
        "tp_identicos": {clave(r) for r, x in zip(ata, sa) if x < fila("validacion_original_65633", 0.03)["umbral"]}
                        == {clave(r) for r, x in zip(ata, sa) if x < fila("validacion_original_65633", 0.05)["umbral"]}}

    # --- 80 ventanas Kali de validacion, conservadas aparte
    with open(AQUI / "validacion-kali-80-excluidas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["campaign_id", "entity_ip", "window_end_utc", "packet_count_10s", "score_samples",
                    "bajo_umbral_desplegado"])
        for r, x in zip([r for r, k in zip(val, kali) if k], sv_k):
            w.writerow([r["campaign_id"], r["entity_ip"], r["window_end_utc"], r["packet_count_10s"], repr(float(x)), int(x < U_OP)])

    # --- salidas tabulares
    cols = ["validacion", "n_validacion", "alfa", "umbral", "fpr_en_validacion", "TP", "FN", "FP", "TN",
            "precision", "recall", "F1", "FPR"]
    with open(AQUI / "SENSIBILIDAD-ALFA.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    md = ["# Sensibilidad de α — IF congelado `if_limpio_2026_10`", "",
          "Umbral = cuantil lineal de `score_samples` en validación; alerta si `score_samples < umbral`.",
          "Evaluación: mismas 65 421 ventanas normales (N) y 84 de ataque (P). FPR = FP/65 421; recall = TP/84;",
          "precisión = TP/(TP+FP). Validación sin Kali = 65 633 − 80 ventanas de `10.10.20.30`.", "",
          "| Validación | α | Umbral | FPR val. | TP | FN | FP | TN | Precisión | Recall | F1 | FPR |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in filas:
        md.append("| %s | %.3f | %.6f | %.4f | %d | %d | %d | %d | %.2f %% | %.2f %% | %.4f | %.2f %% |" % (
            "original (65 633)" if r["validacion"].startswith("validacion_original") else "sin Kali (65 553)",
            r["alfa"], r["umbral"], r["fpr_en_validacion"], r["TP"], r["FN"], r["FP"], r["TN"],
            100 * r["precision"], 100 * r["recall"], r["F1"], 100 * r["FPR"]))
    md += ["", "Las filas α = 0,05 con validación original reproducen el umbral desplegado (−0,5693969936322356).",
           "Elegir α mirando estas columnas de evaluación es una **selección posterior**: el conjunto de evaluación",
           "deja de ser una prueba independiente para esa elección."]
    escribir(AQUI / "SENSIBILIDAD-ALFA.md", "\n".join(md) + "\n")

    traz = [
        ("particionado-limpio.csv (filas totales)", proc["conteos"]["particionado_filas"], "", "entrada declarada del entrenamiento (sha 5ef83b32…)"),
        ("descartadas por banda de guarda", proc["conteos"]["particiones"]["descartada_guarda"], "−2 778", "60 s al inicio de cada bloque; no pertenecen a ninguna partición"),
        ("partición train", proc["conteos"]["particiones"]["train"], "", ""),
        ("  excluidas del entrenamiento (eligible_training=False)", proc["exclusiones_entrenamiento"]["filas_distintas_limpio_vs_notaL"], "−181",
         "Kali 10.10.20.30, ráfaga 27-sep 21:35–22:05 UTC; única diferencia entre particionado-limpio y nota-L"),
        ("  entrenamiento efectivo", proc["modelo"]["informe_filas"]["train"], "203 967", "coincide con el informe del modelo"),
        ("partición validation (calibración original)", proc["conteos"]["particiones"]["validation"], "65 633", "idéntica en nota-L"),
        ("  ventanas Kali en validación (excluidas solo de la nueva calibración)", 80, "−80", "normalidad no confirmada; NO se etiquetan como ataque"),
        ("  validación sin Kali (nueva calibración)", 65553, "65 553", ""),
        ("partición test = oro (prueba normal)", proc["conteos"]["particiones"]["test"], "65 421", "mismas claves y valores; incluye 74 ventanas de 10.10.20.30, sin cambios"),
        ("ataques nota M (evaluación)", proc["conteos"]["ataques_filas"], "84", "0 solapes con train/validation/test"),
    ]
    with open(AQUI / "TRAZABILIDAD-DATOS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["conjunto", "filas", "variacion", "nota"]); w.writerows(traz)
    escribir(AQUI / "TRAZABILIDAD-DATOS.md", "# Trazabilidad de datos\n\n| Conjunto | Filas | Variación | Nota |\n|---|---:|---:|---|\n" +
             "".join("| %s | %s | %s | %s |\n" % (a, f"{b:,}".replace(",", " "), c, d) for a, b, c, d in traz) +
             "\nLas tres exclusiones son distintas: 2 778 por banda de guarda (antes de particionar), 181 del "
             "entrenamiento (ráfaga Kali del 27-sep, ya aplicadas al entrenar el modelo vigente) y 80 de validación "
             "(solo para esta nueva calibración). Entrenamiento, prueba y ataques no cambian.\n")

    # --- figura de sensibilidad (dos paneles, misma escala de alfa)
    C = {"validacion_original_65633": ("#2563eb", "o", "-", "Validación original (n = 65 633)"),
         "validacion_sin_kali_65553": ("#d97706", "s", "--", "Validación sin Kali (n = 65 553)")}
    coma = FuncFormatter(lambda v, _: ("%g" % v).replace(".", ","))
    pos = list(range(len(ALFAS)))          # alfas equiespaciados: son los valores evaluados, no una escala continua
    dmax = max(abs(fila("validacion_original_65633", a)["umbral"] - fila("validacion_sin_kali_65553", a)["umbral"]) for a in ALFAS)
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.9), constrained_layout=True)
    for etq, (col, mk, ls, lab) in C.items():
        fs = [f for f in filas if f["validacion"] == etq]
        grande = etq.startswith("validacion_original")
        for i, k in ((0, "recall"), (1, "FPR")):
            ax[i].plot(pos, [100 * f[k] for f in fs], color=col, marker=mk, ls=ls, lw=2 if grande else 1.6,
                       ms=10 if grande else 5.5, mfc="white" if grande else col, mec=col, mew=1.8, label=lab,
                       zorder=2 if grande else 3)
    ax[0].set_title("Recall sobre 84 ventanas de ataque", fontsize=10); ax[0].set_ylabel("Recall (%)")
    ax[1].set_title("FPR sobre 65 421 ventanas normales", fontsize=10); ax[1].set_ylabel("FPR (%)")
    for x in ax:
        x.set_xlabel("α (cuantil de validación)"); x.set_xticks(pos)
        x.set_xticklabels([("%g" % a).replace(".", ",") for a in ALFAS])
        x.yaxis.set_major_formatter(coma)
        x.grid(alpha=0.25); x.spines[["top", "right"]].set_visible(False)
        x.axvline(ALFAS.index(0.05), color="#6b7280", lw=1, ls=":")
    ax[0].text(ALFAS.index(0.05) + 0.08, ax[0].get_ylim()[0] + 0.4, "α desplegado", fontsize=7.5, color="#6b7280")
    ax[0].legend(frameon=False, loc="upper left", fontsize=8)
    fig.suptitle("Sensibilidad de α del IF congelado if_limpio_2026_10 (umbral solo desde validación). Las curvas se "
                 "superponen:\nla diferencia máxima de umbral entre ambas validaciones es %s" % ("%.1e" % dmax).replace(".", ","),
                 fontsize=9)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(AQUI / f"figura-sensibilidad-alfa.{ext}", dpi=300, metadata=None if ext != "png" else {"Software": None})
    plt.close(fig)

    # --- ROC / PR del IF con puntos operativos (las curvas no dependen del umbral)
    fpr_c, tpr_c, _ = roc_curve(y, s); pr_p, pr_r, _ = precision_recall_curve(y, s)
    # el desplegado y el de sin Kali con alfa 0,05 casi coinciden: anillo grande debajo, relleno encima
    pts = [("α = 0,05, validación original (desplegado)", fila("validacion_original_65633", 0.05), "#111827", "o", 13, "none"),
           ("α = 0,05, sin Kali", fila("validacion_sin_kali_65553", 0.05), "#d97706", "s", 6, None),
           ("α = 0,03, sin Kali (selección posterior)", fila("validacion_sin_kali_65553", 0.03), "#dc2626", "D", 7, None)]
    coma = FuncFormatter(lambda v, _: ("%g" % v).replace(".", ","))
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.9), constrained_layout=True)
    ax[0].plot(fpr_c, tpr_c, color="#2563eb", lw=2, label=("IF limpio (ROC-AUC = %.4f)" % auc).replace(".", ","))
    ax[0].plot([0, 1], [0, 1], color="#9ca3af", lw=1, ls=":")
    ax[1].step(pr_r, pr_p, where="post", color="#2563eb", lw=2, label=("IF limpio (AP = %.4f)" % ap).replace(".", ","))
    ax[1].axhline(84 / 65505, color="#9ca3af", lw=1, ls=":", label="Prevalencia = 0,128 %")
    ins = ax[0].inset_axes([0.42, 0.30, 0.54, 0.40])
    ins.plot(fpr_c, tpr_c, color="#2563eb", lw=1.6)
    ins.set_xlim(0, 0.07); ins.set_ylim(0.55, 0.72); ins.tick_params(labelsize=6.5); ins.grid(alpha=0.25)
    ins.xaxis.set_major_formatter(coma); ins.yaxis.set_major_formatter(coma)
    ins.set_title("detalle FPR 0–0,07", fontsize=7)
    for lab, f, col, mk, ms, mfc in pts:
        kw = dict(marker=mk, color=col, ms=ms, ls="none", mec=col, mew=1.8, mfc=mfc if mfc else col, label=lab)
        ax[0].plot(f["FPR"], f["recall"], **kw)
        ins.plot(f["FPR"], f["recall"], **{**kw, "label": None})
        ax[1].plot(f["recall"], f["precision"], **kw)
    ax[0].set(xlabel="Tasa de falsos positivos", ylabel="Recall (TPR)", title="ROC")
    ax[1].set(xlabel="Recall", ylabel="Precisión (escala log)", title="Precisión–recall", yscale="log")
    ax[0].legend(frameon=False, fontsize=7, loc="lower right"); ax[1].legend(frameon=False, fontsize=7, loc="upper right")
    for x in ax:
        x.grid(alpha=0.25); x.spines[["top", "right"]].set_visible(False)
        x.xaxis.set_major_formatter(coma)
    ax[0].yaxis.set_major_formatter(coma)
    ax[1].yaxis.set_major_formatter(FuncFormatter(lambda v, _: ("%g" % v).replace(".", ",")))
    for ext in ("png", "svg", "pdf"):
        fig.savefig(AQUI / f"figura-roc-pr-puntos-operativos.{ext}", dpi=300)
    plt.close(fig)

    # --- variantes de Tablas 6 y 7 (no sustituyen a las canónicas)
    f03 = fila("validacion_sin_kali_65553", 0.03)
    t6 = [("TP", f03["TP"], "/ 84"), ("FP", f03["FP"], "/ 65 421"), ("TN", f03["TN"], "/ 65 421"), ("FN", f03["FN"], "/ 84"),
          ("Precisión", "%.4f (%.2f %%)" % (f03["precision"], 100 * f03["precision"]), "TP/(TP+FP) = %d/%d" % (f03["TP"], f03["TP"] + f03["FP"])),
          ("Recall (TPR)", "%.4f (%.2f %%)" % (f03["recall"], 100 * f03["recall"]), "TP/84"),
          ("F1", "%.5f" % f03["F1"], "2PR/(P+R)"),
          ("FPR", "%.4f (%.2f %%)" % (f03["FPR"], 100 * f03["FPR"]), "FP/65 421"),
          ("ROC-AUC", "%.5f" % auc, "sin cambio: no depende del umbral"),
          ("Average Precision (AP)", "%.5f" % ap, "sin cambio: no depende del umbral"),
          ("Umbral", repr(f03["umbral"]), "cuantil 0,03 de validación sin Kali (selección posterior)")]
    with open(AQUI / "TABLA6-variante-alfa0.03-sinKali.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["indicador", "valor", "numerador_denominador"]); w.writerows(t6)
    with open(AQUI / "TABLA7-fila-IF-variante-alfa0.03-sinKali.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["configuracion", "origen", "precision", "recall", "F1", "FPR", "roc_auc", "average_precision", "umbral", "nota"])
        w.writerow(["IF limpio, α = 0,03 sin Kali (selección posterior; no desplegado)", "esta red", f03["precision"], f03["recall"],
                    f03["F1"], f03["FPR"], auc, ap, f03["umbral"],
                    "Mismo modelo y scores que la fila 'IF limpio (desplegado)'; solo cambia el umbral. Otras filas sin recalibrar."])

    res = {"alineacion_con_export_4.1": alin, "reproduccion_comprobacion_previa": repro,
           "identidades_003_vs_005_sin_kali": ident, "sensibilidad": filas,
           "kali_validacion": {"n": int(kali.sum()), "bajo_umbral_desplegado": int(np.sum(sv_k < U_OP)),
                               "umbral_q05_original_menos_sin_kali": q(sv, 0.05) - q(sv_nk, 0.05)}}
    escribir(AQUI / "resultados-calibracion-alfa.json", json.dumps(res, indent=2, ensure_ascii=False) + "\n")

    repo = AQUI
    salidas = sorted(p for p in AQUI.iterdir() if p.is_file() and p.name not in ("MANIFIESTO-CALIBRACION-ALFA.json",)
                     and p.suffix not in (".pyc",))
    man = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "proposito": "nueva calibración offline (sensibilidad de α); no cambia el sistema desplegado",
           "modelo": {"id": "if_limpio_2026_10", "sha256_joblib_desplegado": proc["entradas_sha256"]["modelo_desplegado"],
                      "pipeline": proc["modelo"]["pasos_pipeline"], "features_28_orden_verificado": proc["modelo"]["orden_features_igual_informe"],
                      "umbral_desplegado_sin_cambios": U_OP},
           "entradas_sensor_sha256": proc["entradas_sha256"],
           "entradas_locales_sha256": {"scores-todos-candidatos-full.csv.gz": sha(EXPORT), "metricas.json": sha(METRICAS)},
           "datos_sensor_sha256": proc["salidas_sha256"] | {"sensor-procedencia.json": sha(SEN / "sensor-procedencia.json")},
           "runtime_sensor": proc["runtime"],
           "repositorios": {
               "documentacion": {"url": "https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION", "rama": git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
                                 "commit_base": git(repo, "rev-parse", "HEAD")},
               "implementacion": {"url": "https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos",
                                  "nota": "no se ejecuta código del repo; el sensor usa su copia desplegada (sin .git). Ver NOTA."}},
           "salidas_sha256": {p.name: sha(p) for p in salidas}}
    escribir(AQUI / "MANIFIESTO-CALIBRACION-ALFA.json", json.dumps(man, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"alineacion": alin, "reproduccion": repro,
                      "identidades": {k: v for k, v in ident.items() if k != "ventanas_tp"}}, indent=1, ensure_ascii=False))
    for r in filas:
        print("%-27s a=%.3f thr=%.10f TP=%d FN=%d FP=%d TN=%d prec=%.4f rec=%.4f F1=%.4f FPR=%.4f" % (
            r["validacion"], r["alfa"], r["umbral"], r["TP"], r["FN"], r["FP"], r["TN"], r["precision"], r["recall"], r["F1"], r["FPR"]))


def can_if(can, k):
    """Busca la metrica k del IF limpio en metricas.json sin asumir su estructura exacta."""
    def walk(o):
        if isinstance(o, dict):
            if k in o and any("limpio" in str(v).lower() for v in o.values() if isinstance(v, str)):
                return o[k]
            for kk, v in o.items():
                if "limpio" in str(kk).lower() and isinstance(v, dict) and k in v:
                    return v[k]
                r = walk(v)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = walk(v)
                if r is not None:
                    return r
        return None
    return walk(can)


if __name__ == "__main__":
    main()
