#!/usr/bin/env python3
"""Ampliacion de la sensibilidad de alfa de la Tabla 6-a (anade alfa=0,008 y 0,005).

MISMO protocolo que calibrar_alfa.py (no reentrena, no toca modelo/escalador/umbral desplegado,
no usa prueba ni ataques para fijar umbrales):
  - IF limpio 'if_limpio_2026_10' congelado; scores = score_samples calculados en el sensor.
  - Umbral = cuantil lineal de score_samples en VALIDACION; alerta si score_samples < umbral.
  - Validacion sin Kali = 65633 - 80 ventanas de 10.10.20.30 = 65553 (calibracion de la Tabla 6-a).
  - Evaluacion = 65421 normales (N) + 84 ataque (P) = 65505.
Solo usa los artefactos existentes en datos-sensor/ (hashes verificados). No ejecuta ataques ni campanas.

Salidas (ademas de actualizar SENSIBILIDAD-ALFA.{csv,md} en su sitio):
  TABLA6a-comparacion-alfa.{csv,md}      tabla canonica (sin Kali, 9 alfas, 10 columnas)
  umbrales-alfa-precision-completa.json  umbrales con precision completa + registro del procedimiento
  COMPARACION-VENTANAS-ALFA.{md,csv}     0,01 vs 0,008 ; 0,008 vs 0,005 ; 0,03 vs 0,01
  NOTA-INTERPRETACION-ALFA.md            compromiso deteccion/falsas alarmas, dominancia, recomendacion
  MANIFIESTO-AMPLIACION-ALFA-2026-10-27.json
"""
import csv, gzip, hashlib, json, pathlib, datetime
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
SEN = AQUI / "datos-sensor"
KALI = "10.10.20.30"
# α ampliados (se conservan todos los previos y se anaden 0,008 y 0,005)
ALFAS = [0.005, 0.008, 0.010, 0.020, 0.025, 0.030, 0.040, 0.050, 0.100]
ALFAS_NUEVOS = {0.005, 0.008}
U_OP = -0.5693969936322356  # umbral desplegado (alfa 0,05 sobre validacion COMPLETA); NO se cambia
REF_INDEP = {  # comprobacion independiente (enunciado), variante sin Kali; se reproduce, no se fuerza
    0.01: dict(TP=50, FP=567, TN=64854, FN=34),
    0.03: dict(umbral=-0.5898535710336618, TP=54, FP=1723, TN=63698, FN=30),
    0.05: dict(umbral=-0.5694578968203694, TP=54, FP=2955, TN=62466, FN=30),
}
PARES = [("0.010", "0.008"), ("0.008", "0.005"), ("0.030", "0.010")]  # (alfa mayor, alfa menor)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def sha_lf(p):
    b = pathlib.Path(p).read_bytes()
    if p.suffix.lower() in (".md", ".csv", ".json", ".py", ".svg", ".txt"):
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


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


def escribir(p, texto):
    pathlib.Path(p).write_text(texto, encoding="utf-8", newline="\n")


def main():
    proc = json.loads((SEN / "sensor-procedencia.json").read_text(encoding="utf-8"))
    for nombre, h in proc["salidas_sha256"].items():
        assert sha(SEN / nombre) == h, "hash de entrada no coincide: %s" % nombre

    val = leer_gz(SEN / "scores-validacion-65633.csv.gz")
    nor = leer_gz(SEN / "scores-prueba-normal-65421.csv.gz")
    ata = leer_gz(SEN / "scores-ataques-84.csv.gz")
    assert (len(val), len(nor), len(ata)) == (65633, 65421, 84), "conteos de particiones"
    sv = np.array([float(r["score_samples"]) for r in val])
    kali = np.array([r["entity_ip"] == KALI for r in val])
    sv_nk = sv[~kali]
    sn = np.array([float(r["score_samples"]) for r in nor])
    sa = np.array([float(r["score_samples"]) for r in ata])
    assert kali.sum() == 80 and len(sv_nk) == 65553, "exclusion Kali de validacion"

    # --- tabla (ambas variantes) ---
    filas = []
    for etq, base in (("validacion_original_65633", sv), ("validacion_sin_kali_65553", sv_nk)):
        for a in ALFAS:
            thr = q(base, a); m = metricas(thr, sn, sa)
            filas.append(dict(validacion=etq, n_validacion=int(len(base)), alfa=a, umbral=thr,
                              fpr_en_validacion=float(np.mean(base < thr)), **m))

    def fila(etq, a):
        return next(f for f in filas if f["validacion"] == etq and abs(f["alfa"] - a) < 1e-12)

    # --- verificaciones ---
    chk = {"identidades_conteo": [], "reproduccion_refs": {}, "umbral_desplegado": {}}
    for f in filas:
        assert f["TP"] + f["FN"] == 84, "TP+FN!=84 en %s a=%s" % (f["validacion"], f["alfa"])
        assert f["FP"] + f["TN"] == 65421, "FP+TN!=65421 en %s a=%s" % (f["validacion"], f["alfa"])
    for a, ref in REF_INDEP.items():
        f = fila("validacion_sin_kali_65553", a)
        chk["reproduccion_refs"][str(a)] = {k: {"esperado": v, "obtenido": f[k],
                                                 "coincide": (abs(f[k] - v) < 1e-12 if k == "umbral" else f[k] == v)}
                                            for k, v in ref.items()}
    # el umbral desplegado = q05 de la validacion COMPLETA
    chk["umbral_desplegado"] = {"q05_validacion_original": fila("validacion_original_65633", 0.05)["umbral"],
                                "U_OP_declarado": U_OP,
                                "coincide": abs(fila("validacion_original_65633", 0.05)["umbral"] - U_OP) < 1e-12}
    monot = all(fila("validacion_sin_kali_65553", ALFAS[i])["FP"] <= fila("validacion_sin_kali_65553", ALFAS[i + 1])["FP"]
                for i in range(len(ALFAS) - 1))
    chk["fp_monotono_no_decreciente_sinKali"] = monot

    # --- SENSIBILIDAD-ALFA.{csv,md} (actualiza el fichero existente, mismo formato, ambas variantes) ---
    cols = ["validacion", "n_validacion", "alfa", "umbral", "fpr_en_validacion", "TP", "FN", "FP", "TN",
            "precision", "recall", "F1", "FPR"]
    with open(AQUI / "SENSIBILIDAD-ALFA.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    md = ["# Sensibilidad de α — IF congelado `if_limpio_2026_10`", "",
          "Umbral = cuantil lineal de `score_samples` en validación; alerta si `score_samples < umbral`.",
          "Evaluación: mismas 65 421 ventanas normales (N) y 84 de ataque (P). FPR = FP/65 421; recall = TP/84;",
          "precisión = TP/(TP+FP). Validación sin Kali = 65 633 − 80 ventanas de `10.10.20.30`.",
          "Ampliación 2026-10-27: añadidos α = 0,008 y 0,005 (procedimiento idéntico; `ampliar_alfa.py`).", "",
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

    # --- TABLA6a-comparacion-alfa.{csv,md}: canonica (sin Kali), 10 columnas del enunciado ---
    t6cols = ["alfa", "umbral", "TP", "FP", "TN", "FN", "precision_pct", "recall_pct", "F1", "FPR_pct"]
    t6 = []
    for a in ALFAS:
        f = fila("validacion_sin_kali_65553", a)
        t6.append(dict(alfa=a, umbral=repr(f["umbral"]), TP=f["TP"], FP=f["FP"], TN=f["TN"], FN=f["FN"],
                       precision_pct=round(100 * f["precision"], 2), recall_pct=round(100 * f["recall"], 2),
                       F1=round(f["F1"], 4), FPR_pct=round(100 * f["FPR"], 2)))
    with open(AQUI / "TABLA6a-comparacion-alfa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=t6cols, lineterminator="\n"); w.writeheader(); w.writerows(t6)
    md6 = ["# Tabla 6-a — Comparación de los valores de α (IF limpio `if_limpio_2026_10`, validación sin Kali n=65 553)", "",
           "Umbral = cuantil lineal de `score_samples` en validación sin Kali; alerta si `score_samples < umbral`.",
           "Evaluación: 65 421 ventanas normales + 84 de ataque = 65 505. Clasificación con el **umbral de precisión completa**",
           "(columna Umbral en `TABLA6a-comparacion-alfa.csv` / `umbrales-alfa-precision-completa.json`), no con el redondeado.",
           "Verificado por fila: TP+FN=84 y FP+TN=65 421. Filas nuevas (2026-10-27): α=0,005 y α=0,008.", "",
           "| α | Umbral | TP | FP | TN | FN | Precisión (%) | Recall (%) | F1 | FPR (%) |",
           "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for a in ALFAS:
        f = fila("validacion_sin_kali_65553", a)
        marca = " (nuevo)" if a in ALFAS_NUEVOS else ""
        md6.append("| %s%s | %.10f | %d | %d | %d | %d | %.2f | %.2f | %.4f | %.2f |" % (
            ("%g" % a).replace(".", ","), marca, f["umbral"], f["TP"], f["FP"], f["TN"], f["FN"],
            100 * f["precision"], 100 * f["recall"], f["F1"], 100 * f["FPR"]))
    md6 += ["", "Referencias reproducidas (sin Kali): α=0,01 → TP=50, FP=567, TN=64 854, FN=34; "
            "α=0,03 → 54/1 723/63 698/30; α=0,05 → 54/2 955/62 466/30.",
            "El umbral desplegado operativo (−0,5693969936322356) proviene de α=0,05 sobre la validación **completa** "
            "(65 633); aquí la calibración es **sin Kali**. No se cambia el α desplegado."]
    escribir(AQUI / "TABLA6a-comparacion-alfa.md", "\n".join(md6) + "\n")

    # --- umbrales con precision completa + registro del procedimiento ---
    umbrales = {
        "procedimiento": {
            "modelo": "if_limpio_2026_10 (congelado); sha256 joblib desplegado "
                      "df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60",
            "score": "score_samples del pipeline (scaler+IsolationForest); mayor = mas normal",
            "umbral": "numpy.quantile(score_samples_validacion, alfa, method='linear')",
            "regla_clasificacion": "alerta si score_samples < umbral (estricto)",
            "validacion_original": 65633, "validacion_sin_kali": 65553,
            "evaluacion_normales": 65421, "evaluacion_ataques": 84,
            "no_reentrena": True, "no_usa_prueba_ni_ataques_para_umbral": True,
            "umbral_desplegado_sin_cambios": U_OP,
        },
        "umbrales_full_precision": {
            etq: {("%.3f" % a): repr(fila(etq, a)["umbral"]) for a in ALFAS}
            for etq in ("validacion_original_65633", "validacion_sin_kali_65553")
        },
    }
    escribir(AQUI / "umbrales-alfa-precision-completa.json", json.dumps(umbrales, indent=2, ensure_ascii=False) + "\n")

    # --- comparacion de ventanas que cambian de clasificacion ---
    def thr_nk(a): return fila("validacion_sin_kali_65553", a)["umbral"]
    ata_keys = [clave(r) for r in ata]
    ata_time = {clave(r): r["window_end_utc"] for r in ata}
    comp = {}
    filas_cambio = []
    for hi, lo in PARES:
        ah, al = float(hi), float(lo)
        th, tl = thr_nk(ah), thr_nk(al)
        fh, fl = fila("validacion_sin_kali_65553", ah), fila("validacion_sin_kali_65553", al)
        tp_hi = {k for k, x in zip(ata_keys, sa) if x < th}
        tp_lo = {k for k, x in zip(ata_keys, sa) if x < tl}
        tp_perdidos = sorted(tp_hi - tp_lo, key=lambda k: ata_time[k])   # ventanas de ataque que dejan de detectarse
        fp_evitados = fh["FP"] - fl["FP"]
        def fptp(fr):
            return (None if fr["TP"] == 0 else round(fr["FP"] / fr["TP"], 3))
        comp["%s_vs_%s" % (hi, lo)] = {
            "alfa_mayor": ah, "alfa_menor": al,
            "umbral_mayor": repr(th), "umbral_menor": repr(tl),
            "FP_mayor": fh["FP"], "FP_menor": fl["FP"], "FP_evitados": fp_evitados,
            "TP_mayor": fh["TP"], "TP_menor": fl["TP"], "TP_perdidos": fh["TP"] - fl["TP"],
            "FP_por_TP_mayor": fptp(fh), "FP_por_TP_menor": fptp(fl),
            "ventanas_ataque_que_dejan_de_detectarse": [
                {"clave": "|".join(k), "window_end_utc": ata_time[k],
                 "score_samples": next(float(x) for kk, x in zip(ata_keys, sa) if kk == k)}
                for k in tp_perdidos],
        }
        for k in tp_perdidos:
            filas_cambio.append({"comparacion": "%s_vs_%s" % (hi, lo), "campaign_id": k[0], "entity_ip": k[1],
                                 "window_end_utc": k[2],
                                 "score_samples": next(float(x) for kk, x in zip(ata_keys, sa) if kk == k),
                                 "estado_alfa_mayor": "detectada", "estado_alfa_menor": "no_detectada"})
    with open(AQUI / "COMPARACION-VENTANAS-ALFA.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["comparacion", "campaign_id", "entity_ip", "window_end_utc",
                                          "score_samples", "estado_alfa_mayor", "estado_alfa_menor"],
                           lineterminator="\n"); w.writeheader(); w.writerows(filas_cambio)
    cmd = ["# Comparación de ventanas al reducir α (IF limpio, validación sin Kali)", "",
           "Columna FP/TP = falsas alarmas por detección correcta (FP÷TP); **no es «fiabilidad»** y **no** es",
           "criterio único de selección. Si TP=0 queda indefinida.", "",
           "**Limitación (datos de este conjunto):** el fichero de ataques (`scores-ataques-84.csv.gz`) solo trae",
           "`campaign_id, entity_ip, window_end_utc, score_samples` (84 ventanas, todas de `10.10.20.30`). **No** incluye",
           "etiqueta de escenario ni de episodio, así que aquí se identifican las ventanas por su **clave original** y su",
           "`window_end_utc`, pero **no** se puede comprobar cobertura por episodio ni detección durante el ataque: perder",
           "una ventana **no** equivale a perder un ataque completo. Esa comprobación queda pendiente de la campaña A.", ""]
    for hi, lo in PARES:
        c = comp["%s_vs_%s" % (hi, lo)]
        cmd += ["## α = %s → α = %s" % (hi.replace(".", ","), lo.replace(".", ",")),
                "- FP evitados: **%d** (%d → %d)." % (c["FP_evitados"], c["FP_mayor"], c["FP_menor"]),
                "- TP perdidos: **%d** (%d → %d)." % (c["TP_perdidos"], c["TP_mayor"], c["TP_menor"]),
                "- FP/TP: %s → %s." % (c["FP_por_TP_mayor"], c["FP_por_TP_menor"]),
                "- Ventanas de ataque que dejan de detectarse (%d):" % len(c["ventanas_ataque_que_dejan_de_detectarse"])]
        if c["ventanas_ataque_que_dejan_de_detectarse"]:
            for v in c["ventanas_ataque_que_dejan_de_detectarse"]:
                cmd.append("  - `%s` (score %.6f)" % (v["clave"], v["score_samples"]))
        else:
            cmd.append("  - (ninguna)")
        cmd.append("")
    escribir(AQUI / "COMPARACION-VENTANAS-ALFA.md", "\n".join(cmd) + "\n")

    # --- dominancia (Pareto) sobre sin Kali: dominada si otra tiene >= TP con <= FP y mejora estricta en uno ---
    pts = [(a, fila("validacion_sin_kali_65553", a)["TP"], fila("validacion_sin_kali_65553", a)["FP"]) for a in ALFAS]
    dominadas = []
    for a, tp, fp in pts:
        for b, tp2, fp2 in pts:
            if (b != a) and (tp2 >= tp) and (fp2 <= fp) and ((tp2 > tp) or (fp2 < fp)):
                dominadas.append((a, b)); break
    dom_set = sorted({a for a, _ in dominadas})
    no_dom = [a for a in ALFAS if a not in dom_set]

    # --- nota de interpretacion ---
    def row(a): return fila("validacion_sin_kali_65553", a)
    nota = ["# Nota de interpretación — sensibilidad de α (IF limpio, validación sin Kali)", "",
            "## Compromiso detección ↔ falsas alarmas",
            "Al subir α el umbral sube y se alerta más: aumentan TP y FP a la vez; al bajar α ocurre lo contrario.",
            "En este conjunto, el recall por **ventanas** va de %.2f %% (α=0,005) a %.2f %% (α=0,10), y la FPR de %.2f %% a %.2f %%."
            % (100 * row(0.005)["recall"], 100 * row(0.10)["recall"], 100 * row(0.005)["FPR"], 100 * row(0.10)["FPR"]),
            "El TP por ventanas se estanca en 54 entre α=0,03 y α=0,05 (mismas 54 ventanas), mientras los FP siguen subiendo.", "",
            "## Configuraciones dominadas",
            "Una configuración está **dominada** si otra logra al menos tantos TP con no más FP y mejora estrictamente uno de los dos.",
            "Dominadas: %s." % (", ".join(("%g" % a).replace(".", ",") for a in dom_set) or "ninguna"),
            "No dominadas (frente de Pareto en TP/FP por ventana): %s."
            % ", ".join(("%g" % a).replace(".", ",") for a in no_dom), "",
            "## Qué α merece la pena incluir en la campaña A (sujeto a comprobación de cobertura)",
            "- **α = 0,05**: es el **desplegado**; se incluye como referencia operativa (no se cambia ahora).",
            "- **α = 0,03**: mismo TP por ventana que 0,04–0,05 (54) con **menos FP** (1 723 vs 2 299/2 955) → domina a 0,04 y 0,05 en este conjunto.",
            "- **α = 0,01** y **α = 0,008**: menos FP, pero pierden TP por ventana; útiles para ver el extremo de baja FPR.",
            "- **α = 0,005**: extremo de mínima FPR; mayor pérdida de TP por ventana.",
            "Recomendación (pendiente de cobertura por episodio y detección durante el ataque, que estos datos **no** permiten",
            "comprobar): llevar a la campaña A **al menos α ∈ {0,05 (desplegado), 0,03, 0,01}**, y opcionalmente 0,008 y 0,005",
            "para trazar el extremo de baja FPR. La elección definitiva debe mirar cobertura por **episodio** (no por ventana),",
            "no solo estos conteos.", "",
            "## Límites de esta lectura",
            "- Estos datos **ya se usaron** para comparar y orientar la elección de α: elegir aquí el “mejor” **no** es una validación independiente.",
            "- El recall y los TP son **por ventana**; perder una ventana **no** es perder un ataque. No hay etiqueta de episodio en este conjunto.",
            "- **No** se afirma que un α menor cause lentitud o inestabilidad: no hay mediciones de rendimiento aquí.",
            "- FP/TP se ofrece como indicador complementario de falsas alarmas por detección correcta, no como criterio único.", "",
            "## Archivos que requerirían actualización si luego se cambia el α seleccionado (no se tocan ahora)",
            "- `config-campana.json` (`umbrales`, `modelo.alpha`/umbral operativo) y el umbral del motor desplegado.",
            "- Fila del IF en la Tabla 7 (`comparacion-metodos-2026-10-25/TABLA7-*`) y la figura ROC-PR de puntos operativos.",
            "- `figura-sensibilidad-alfa.*` y `figura-roc-pr-puntos-operativos.*` de este directorio (regenerar con los 9 α).",
            "- Word del artículo (Tabla 6-a, Tabla 7 y texto asociado) — **no** se edita aquí.",
            "- `calibrar_alfa.py` (lista `ALFAS` y `U_OP`) si se adopta el conjunto ampliado como canónico.", ""]
    escribir(AQUI / "NOTA-INTERPRETACION-ALFA.md", "\n".join(nota) + "\n")

    # --- manifiesto de la ampliacion (hashes LF de lo publicado) ---
    nuevas = ["ampliar_alfa.py", "TABLA6a-comparacion-alfa.csv", "TABLA6a-comparacion-alfa.md",
              "umbrales-alfa-precision-completa.json", "COMPARACION-VENTANAS-ALFA.csv", "COMPARACION-VENTANAS-ALFA.md",
              "NOTA-INTERPRETACION-ALFA.md", "SENSIBILIDAD-ALFA.csv", "SENSIBILIDAD-ALFA.md"]
    man = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "proposito": "ampliacion de la sensibilidad de alfa (anade 0,008 y 0,005) sobre los artefactos existentes; "
                        "no cambia modelo, umbral desplegado, servicios ni Word",
           "protocolo_identico_a": "calibrar_alfa.py (2026-10-24)",
           "discrepancia_65633_vs_65553": "el fichero de validacion tiene 65633 filas; la Tabla 6-a calibra con 65553 "
                                          "= 65633 - 80 ventanas de 10.10.20.30 (Kali). Documentado y verificado aqui.",
           "limitacion_episodios": "scores-ataques-84 no trae escenario/episodio; no se puede comprobar cobertura por "
                                   "episodio ni deteccion durante el ataque con estos datos (pendiente de campana A).",
           "entradas_sensor_sha256_verificadas": proc["salidas_sha256"],
           "verificaciones": chk,
           "alfas": ALFAS,
           "salidas_sha256_lf": {n: sha_lf(AQUI / n) for n in nuevas},
           "manifiesto_original_historico": "MANIFIESTO-CALIBRACION-ALFA.json (estado 2026-10-24)"}
    escribir(AQUI / "MANIFIESTO-AMPLIACION-ALFA-2026-10-27.json", json.dumps(man, indent=2, ensure_ascii=False) + "\n")

    # --- resumen por consola ---
    print(json.dumps({"verificaciones": chk, "dominadas": [("%g" % a) for a in dom_set],
                      "no_dominadas": [("%g" % a) for a in no_dom],
                      "comparaciones": {k: {kk: v[kk] for kk in ("FP_evitados", "TP_perdidos",
                                       "FP_por_TP_mayor", "FP_por_TP_menor")} for k, v in comp.items()}},
                     indent=1, ensure_ascii=False))
    print("\nTABLA 6-a (sin Kali):")
    for a in ALFAS:
        f = fila("validacion_sin_kali_65553", a)
        print("  a=%.3f thr=%.10f TP=%d FP=%d TN=%d FN=%d prec=%.2f%% rec=%.2f%% F1=%.4f FPR=%.2f%%" % (
            a, f["umbral"], f["TP"], f["FP"], f["TN"], f["FN"],
            100 * f["precision"], 100 * f["recall"], f["F1"], 100 * f["FPR"]))


if __name__ == "__main__":
    main()
