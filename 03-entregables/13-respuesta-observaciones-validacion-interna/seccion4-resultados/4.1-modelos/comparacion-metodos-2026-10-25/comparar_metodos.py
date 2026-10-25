#!/usr/bin/env python3
"""Comparacion de cinco detectores de novedad sobre las mismas ventanas de CyberFlow.

IF congelado (if_limpio_2026_10, no se reentrena) frente a One-Class SVM, LOF (novelty=True),
Elliptic Envelope y PCA con error de reconstruccion. Configuracion fijada antes de entrenar en
config-comparacion.json. Umbral comun: cuantil 1-alfa (lineal) de la puntuacion de anomalia en
las 65 553 ventanas de validacion; anomalia si puntuacion > umbral.

Uso (offline, en el laptop; --datos = copia de solo lectura de los artefactos del sensor):
  python comparar_metodos.py --datos DIR --metodo IF|OCSVM|LOF|EllipticEnvelope|PCA
  python comparar_metodos.py --datos DIR --consolidar
"""
import argparse, csv, datetime, gzip, hashlib, json, os, pathlib, platform, subprocess, sys, time, warnings

import numpy as np
import sklearn
from sklearn.metrics import roc_auc_score, average_precision_score

AQUI = pathlib.Path(__file__).resolve().parent
CAL = AQUI.parent / "calibracion-alfa-2026-10-24"
SEN = CAL / "datos-sensor"
SAL = AQUI / "salidas"
CFG = json.loads((AQUI / "config-comparacion.json").read_text(encoding="utf-8"))
SEMILLA = CFG["semilla"]
ALFAS = CFG["alfas"]
KALI = "10.10.20.30"
METODOS = ["IF", "OCSVM", "LOF", "EllipticEnvelope", "PCA"]
ARCH = {  # ruta dentro de --datos -> clave en sensor-procedencia.json
    "preliminar/limpio-2026-10/particionado-limpio.csv": "particionado_limpio",
    "preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib": "modelo_desplegado",
    "preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json": "manifiesto_desplegable",
    "preliminar/limpio-2026-10/if_limpio_2026_10.json": "informe_entrenamiento",
    "aprendizaje/oro/oro.csv": "oro_prueba_normal",
    "aprendizaje/ataques/ataques-nota-M.csv": "ataques_nota_M",
}
REF_IF = {  # comprobacion previa (enunciado); se verifica, no se fuerza
    0.03: dict(umbral_original=-0.5898535710336618, TP=54, FP=1723, TN=63698, FN=30),
    0.05: dict(umbral_original=-0.5694578968203694, TP=54, FP=2955, TN=62466, FN=30),
}
REF_AUC, REF_AP = 0.9247265513, 0.1858068840


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer(p):
    op = gzip.open if str(p).endswith(".gz") else open
    with op(p, "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clave(r):
    return (r["campaign_id"], r["entity_ip"], r["window_end_utc"])


def equipo():
    info = {"sistema": platform.platform(), "cpu": platform.processor(), "nucleos_logicos": os.cpu_count(),
            "python": sys.version.split()[0], "sklearn": sklearn.__version__, "numpy": np.__version__}
    try:
        import scipy; info["scipy"] = scipy.__version__
    except ImportError:
        pass
    try:
        import psutil; info["ram_gb"] = round(psutil.virtual_memory().total / 2**30, 1)
    except ImportError:
        pass
    if sys.platform == "win32":
        try:
            info["cpu"] = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_Processor).Name"],
                                         capture_output=True, text=True, timeout=30).stdout.strip() or info["cpu"]
        except Exception:  # noqa: BLE001
            pass
    return info


# --------------------------------------------------------------------------- datos
def cargar(datos):
    datos = pathlib.Path(datos)
    proc = json.loads((SEN / "sensor-procedencia.json").read_text(encoding="utf-8"))
    hashes = {}
    for rel, k in ARCH.items():
        h = sha(datos / rel)
        assert h == proc["entradas_sha256"][k], "hash distinto: %s" % rel
        hashes[rel] = h
    man = json.loads((datos / "preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json").read_text())
    inf = json.loads((datos / "preliminar/limpio-2026-10/if_limpio_2026_10.json").read_text())
    feats = man["detectors"]["if_limpio_2026_10"]["features"]
    assert feats == inf["features"] and len(feats) == 28

    lim = leer(datos / "preliminar/limpio-2026-10/particionado-limpio.csv")
    oro = leer(datos / "aprendizaje/oro/oro.csv")
    ata = leer(datos / "aprendizaje/ataques/ataques-nota-M.csv")
    k80 = {clave(r) for r in leer(CAL / "validacion-kali-80-excluidas.csv")}

    tr_all = [r for r in lim if r["particion"] == "train"]
    tr = [r for r in tr_all if r["eligible_training"] == "True"]
    va_all = [r for r in lim if r["particion"] == "validation"]
    va = [r for r in va_all if clave(r) not in k80]
    te = [r for r in lim if r["particion"] == "test"]
    excl_va = [r for r in va_all if clave(r) in k80]

    aud = {"particionado_filas": len(lim), "train_particion": len(tr_all), "train_elegible": len(tr),
           "train_excluidas_bandera": len(tr_all) - len(tr),
           "train_excluidas_entidades": sorted({r["entity_ip"] for r in tr_all if r["eligible_training"] != "True"}),
           "train_kali_elegibles_conservadas": sum(r["entity_ip"] == KALI for r in tr),
           "validacion_original": len(va_all), "validacion_excluidas_80": len(excl_va),
           "validacion_comparacion": len(va),
           "excluidas_80_son_todas_las_kali_de_validacion": {clave(r) for r in va_all if r["entity_ip"] == KALI} == k80,
           "prueba_normal": len(oro), "prueba_normal_kali_conservadas": sum(r["entity_ip"] == KALI for r in oro),
           "ataques": len(ata), "evaluacion_total": len(oro) + len(ata)}
    assert (aud["train_elegible"], aud["validacion_comparacion"], aud["prueba_normal"], aud["ataques"]) == (203967, 65553, 65421, 84)
    assert len(k80) == 80 and len(excl_va) == 80

    K = {"train": set(map(clave, tr)), "val": set(map(clave, va)), "oro": set(map(clave, oro)), "ata": set(map(clave, ata)),
         "excl181": {clave(r) for r in tr_all if r["eligible_training"] != "True"}, "excl80": k80}
    aud["oro_igual_particion_test"] = K["oro"] == set(map(clave, te))
    aud["solapes"] = {a + "∩" + b: len(K[a] & K[b]) for i, a in enumerate(K) for b in list(K)[i + 1:]}
    assert aud["oro_igual_particion_test"] and all(v == 0 for v in aud["solapes"].values())

    def X(rows):
        return np.asarray([[float(r[c]) for c in feats] for r in rows], dtype=np.float64)

    D = {"feats": feats, "aud": aud, "hashes": hashes, "datos": datos,
         "tr": tr, "va": va, "oro": oro, "ata": ata,
         "Xtr": X(tr), "Xva": X(va), "Xoro": X(oro), "Xata": X(ata)}
    calidad = {}
    for n in ("Xtr", "Xva", "Xoro", "Xata"):
        a = D[n]
        calidad[n] = {"filas": a.shape[0], "columnas": a.shape[1], "no_finitos": int((~np.isfinite(a)).sum())}
        assert calidad[n]["no_finitos"] == 0
    sd = D["Xtr"].std(axis=0)
    calidad["constantes_en_entrenamiento"] = [f for f, s in zip(feats, sd) if s == 0]
    calidad["rango_entrenamiento"] = {f: [float(lo), float(hi)] for f, lo, hi in zip(feats, D["Xtr"].min(0), D["Xtr"].max(0))}
    calidad["filas_duplicadas_entrenamiento"] = int(len(D["Xtr"]) - len(np.unique(D["Xtr"], axis=0)))
    pc = "packet_count_10s"
    calidad["ventanas_sin_paquetes_recientes(packet_count_10s==0)"] = {
        n: (sum(float(r[pc]) == 0 for r in D[n]) if pc in D[n][0] else "columna ausente") for n in ("tr", "va", "oro", "ata")}
    D["calidad"] = calidad
    return D


def escalador(D):
    """StandardScaler congelado del pipeline desplegado; no se reajusta."""
    import joblib
    p = D["datos"] / "preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mdl = joblib.load(p)
    sc = mdl.named_steps["scaler"]
    info = {"origen": "if_limpio_2026_10_desplegable.joblib::scaler", "clase": type(sc).__name__,
            "n_features_in": int(sc.n_features_in_), "n_samples_seen": int(sc.n_samples_seen_),
            "with_mean": sc.with_mean, "with_std": sc.with_std,
            "avisos_carga": sorted({str(x.message)[:200] for x in w})}
    js = D["datos"] / "escalador-congelado.json"
    if js.exists():  # parametros exportados en el sensor con sklearn 1.9.0
        e = json.loads(js.read_text())
        info["igual_a_export_sensor"] = (np.array_equal(np.array([float(x) for x in e["mean_"]]), sc.mean_)
                                         and np.array_equal(np.array([float(x) for x in e["scale_"]]), sc.scale_))
    assert info["n_features_in"] == 28
    return mdl, sc, info


# --------------------------------------------------------------------------- metodos
def ajustar(nombre, Ztr):
    cfg = CFG["metodos"][nombre]
    p = cfg.get("params_efectivos", cfg.get("params", {}))  # params_efectivos solo si hay desviacion registrada
    diag = {"params_usados": p}
    if nombre == "OCSVM":
        from sklearn.svm import OneClassSVM
        m = OneClassSVM(**p).fit(Ztr)
        diag["n_vectores_soporte"] = int(len(m.support_))
        diag["gamma_efectivo"] = float(1.0 / (Ztr.shape[1] * Ztr.var()))
        f = lambda Z: -m.score_samples(Z)
    elif nombre == "LOF":
        from sklearn.neighbors import LocalOutlierFactor
        m = LocalOutlierFactor(**p).fit(Ztr)
        diag["algoritmo_efectivo"] = m._fit_method
        diag["n_neighbors_efectivo"] = int(m.n_neighbors_)
        f = lambda Z: -m.score_samples(Z)
    elif nombre == "EllipticEnvelope":
        from sklearn.covariance import EllipticEnvelope
        m = EllipticEnvelope(**p).fit(Ztr)
        ev = np.linalg.eigvalsh(m.covariance_)
        diag.update(espectro_covarianza=[float(x) for x in ev],
                    autovalores_menores_1e_6=int(np.sum(ev < 1e-6)), rango_precision=int(np.linalg.matrix_rank(m.precision_)))
        diag.update(n_soporte_mcd=int(m.support_.sum()), autovalor_min=float(ev.min()), autovalor_max=float(ev.max()),
                    numero_condicion=float(ev.max() / ev.min()) if ev.min() > 0 else "infinito")
        f = lambda Z: -m.score_samples(Z)  # = distancia de Mahalanobis^2 (MCD)
    elif nombre == "PCA":
        from sklearn.decomposition import PCA
        m = PCA(n_components=None, svd_solver="full").fit(Ztr)
        acum = np.cumsum(m.explained_variance_ratio_)
        k = int(np.searchsorted(acum, 0.95) + 1)
        V, mu = m.components_[:k], m.mean_
        diag.update(k=k, varianza_explicada_k=float(acum[k - 1]), varianza_acumulada=[float(x) for x in acum])

        def f(Z):
            C = (Z - mu) @ V.T
            R = Z - (mu + C @ V)
            return np.einsum("ij,ij->i", R, R)
    else:
        raise ValueError(nombre)
    return f, diag


def guardar_puntuaciones(nombre, D, s):
    SAL.mkdir(exist_ok=True)
    p = SAL / ("puntuaciones-%s.csv.gz" % nombre)
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["conjunto", "campaign_id", "entity_ip", "window_end_utc", "etiqueta", "puntuacion_anomalia"])
    for conj, rows, et in (("validacion", D["va"], 0), ("prueba_normal", D["oro"], 0), ("ataque", D["ata"], 1)):
        for r, v in zip(rows, s[conj]):
            w.writerow([conj, r["campaign_id"], r["entity_ip"], r["window_end_utc"], et, repr(float(v))])
    with open(p, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
        gz.write(buf.getvalue().encode("utf-8"))  # mtime=0: mismo contenido -> mismo hash
    return p


def correr(nombre, D):
    mdl, sc, info_sc = escalador(D)
    Z = {k: sc.transform(D[k]) for k in ("Xtr", "Xva", "Xoro", "Xata")}
    meta = {"metodo": nombre, "inicio_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "config": CFG["metodos"][nombre], "escalador": info_sc, "equipo": equipo()}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if nombre == "IF":
            # puntuaciones canonicas: las del sensor (pipeline desplegado); aqui solo se verifican
            sv = {clave(r): float(r["score_samples"]) for r in leer(SEN / "scores-validacion-65633.csv.gz")}
            so = {clave(r): float(r["score_samples"]) for r in leer(SEN / "scores-prueba-normal-65421.csv.gz")}
            sa = {clave(r): float(r["score_samples"]) for r in leer(SEN / "scores-ataques-84.csv.gz")}
            s = {"validacion": -np.array([sv[clave(r)] for r in D["va"]]),
                 "prueba_normal": -np.array([so[clave(r)] for r in D["oro"]]),
                 "ataque": -np.array([sa[clave(r)] for r in D["ata"]])}
            t0 = time.perf_counter()
            loc = {"validacion": -mdl.score_samples(D["Xva"]), "prueba_normal": -mdl.score_samples(D["Xoro"]),
                   "ataque": -mdl.score_samples(D["Xata"])}
            meta["t_inferencia_s"] = time.perf_counter() - t0
            meta["t_ajuste_s"] = None
            meta["diagnostico"] = {"fuente_puntuaciones": "sensor (datos-sensor/*.csv.gz)",
                                   "max_abs_dif_repuntuacion_local": {k: float(np.max(np.abs(loc[k] - s[k]))) for k in s},
                                   "modelo_params": {k: str(v) for k, v in mdl.named_steps["model"].get_params().items()}}
        else:
            t0 = time.perf_counter()
            f, diag = ajustar(nombre, Z["Xtr"])
            meta["t_ajuste_s"] = time.perf_counter() - t0
            t0 = time.perf_counter()
            s = {"validacion": f(Z["Xva"]), "prueba_normal": f(Z["Xoro"]), "ataque": f(Z["Xata"])}
            meta["t_inferencia_s"] = time.perf_counter() - t0
            meta["diagnostico"] = diag
    meta["avisos"] = sorted({"%s: %s" % (x.category.__name__, str(x.message)[:300]) for x in w})
    for k, v in s.items():
        assert np.all(np.isfinite(v)), (nombre, k)
    meta["n_puntuadas"] = {k: int(len(v)) for k, v in s.items()}
    p = guardar_puntuaciones(nombre, D, s)
    meta["puntuaciones_sha256"] = sha(p)
    meta["fin_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (SAL / ("meta-%s.json" % nombre)).write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: meta[k] for k in ("metodo", "t_ajuste_s", "t_inferencia_s", "diagnostico", "avisos")}, ensure_ascii=False, default=str)[:3000])


# --------------------------------------------------------------------------- consolidacion
def metricas(sv, sn, sa, alfa):
    thr = float(np.quantile(sv, 1 - alfa, method="linear"))
    tp = int(np.sum(sa > thr)); fn = len(sa) - tp
    fp = int(np.sum(sn > thr)); tn = len(sn) - fp
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn)
    return dict(umbral_anomalia=thr, TP=tp, FP=fp, TN=tn, FN=fn, precision=prec, recall=rec,
                F1=2 * prec * rec / (prec + rec) if prec + rec else 0.0,
                FPR_validacion=float(np.mean(sv > thr)), FPR_prueba=fp / (fp + tn),
                empates_validacion=int(np.sum(sv == thr)), empates_evaluacion=int(np.sum(sn == thr) + np.sum(sa == thr)))


def consolidar(D):
    filas, res = [], {"auditoria": D["aud"], "calidad": D["calidad"], "metodos": {}, "faltantes": []}
    for nombre in METODOS:
        pm = SAL / ("meta-%s.json" % nombre)
        if not pm.exists():
            res["faltantes"].append(nombre); continue
        meta = json.loads(pm.read_text(encoding="utf-8"))
        ps = SAL / ("puntuaciones-%s.csv.gz" % nombre)
        assert sha(ps) == meta["puntuaciones_sha256"], nombre
        rows = leer(ps)
        s = {c: np.array([float(r["puntuacion_anomalia"]) for r in rows if r["conjunto"] == c])
             for c in ("validacion", "prueba_normal", "ataque")}
        assert (len(s["validacion"]), len(s["prueba_normal"]), len(s["ataque"])) == (65553, 65421, 84)
        y = np.r_[np.zeros(65421), np.ones(84)]; sc = np.r_[s["prueba_normal"], s["ataque"]]
        auc, ap = float(roc_auc_score(y, sc)), float(average_precision_score(y, sc))
        sin_pq = np.array([float(r["packet_count_10s"]) == 0 for r in D["oro"]])
        res["metodos"][nombre] = {"meta": meta, "roc_auc": auc, "ap": ap, "diagnostico_evaluacion": {
            "normales_prueba_con_puntuacion>=mayor_ataque": int(np.sum(s["prueba_normal"] >= s["ataque"].max())),
            "normales_prueba_con_puntuacion>=menor_ataque": int(np.sum(s["prueba_normal"] >= s["ataque"].min())),
            "valores_distintos_validacion": int(len(np.unique(s["validacion"]))),
            "puntuacion_ventanas_sin_paquetes_prueba": {"min": float(s["prueba_normal"][sin_pq].min()),
                                                         "max": float(s["prueba_normal"][sin_pq].max())}}}
        detectados = {}
        for a in ALFAS:
            m = metricas(s["validacion"], s["prueba_normal"], s["ataque"], a)
            thr = m["umbral_anomalia"]
            detectados[str(a)] = sorted(i for i, v in enumerate(s["ataque"]) if v > thr)
            m["FP_en_ventanas_sin_paquetes"] = int(np.sum(s["prueba_normal"][sin_pq] > thr))
            if nombre == "PCA":
                conv = "error de reconstruccion ||z-z_hat||^2 > umbral"; orig = None
            else:
                conv = "-score_samples > umbral"; orig = -m["umbral_anomalia"]
            filas.append(dict(metodo=nombre, alfa=a, n_validacion=65553, n_normales_prueba=65421, n_ataques=84, **m,
                              umbral_escala_original=orig, regla_escala_original=None if orig is None else "score_samples < umbral",
                              convencion=conv, roc_auc=auc, ap=ap, t_ajuste_s=meta["t_ajuste_s"], t_inferencia_s=meta["t_inferencia_s"]))
        res["metodos"][nombre]["ataques_detectados_idx"] = detectados
    # solapamiento de ataques detectados (indices de fila en ataques-nota-M.csv)
    res["solapamiento_ataques"] = {}
    for a in map(str, ALFAS):
        sets = {n: set(v["ataques_detectados_idx"][a]) for n, v in res["metodos"].items()}
        union = set().union(*sets.values()) if sets else set()
        res["solapamiento_ataques"][a] = {
            "union": len(union), "ninguno": 84 - len(union),
            "todos": len(set.intersection(*sets.values())) if sets else 0,
            "pares": {x + "∩" + y: len(sets[x] & sets[y]) for i, x in enumerate(sets) for y in list(sets)[i + 1:]},
            "solo_uno": {n: len(v - set().union(*(w for m2, w in sets.items() if m2 != n))) for n, v in sets.items()}}
    # verificacion del IF de referencia
    if "IF" in res["metodos"]:
        ver = {"roc_auc": {"esperado": REF_AUC, "obtenido": res["metodos"]["IF"]["roc_auc"]},
               "ap": {"esperado": REF_AP, "obtenido": res["metodos"]["IF"]["ap"]}}
        for a, ref in REF_IF.items():
            f = next(x for x in filas if x["metodo"] == "IF" and x["alfa"] == a)
            ver[str(a)] = {k: {"esperado": v, "obtenido": f["umbral_escala_original"] if k == "umbral_original" else f[k],
                               "diferencia": (f["umbral_escala_original"] if k == "umbral_original" else f[k]) - v}
                           for k, v in ref.items()}
        res["verificacion_IF"] = ver
    res["tabla"] = filas
    # CSV completo
    cols = list(filas[0].keys())
    with open(AQUI / "TABLA7-comparacion-completa.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(cols)
        for f in filas:
            w.writerow([repr(f[c]) if isinstance(f[c], float) else f[c] for c in cols])
    # tabla legible
    pct = lambda x: ("%.2f %%" % (100 * x)).replace(".", ",")
    num = lambda x, d=4: ("%.*f" % (d, x)).replace(".", ",")
    mil = lambda n: "{:,}".format(n).replace(",", " ")
    L = ["# Tabla 7 — Comparación de detectores de novedad (evaluación por ventana)", "",
         "Entrenamiento: 203 967 ventanas normales elegibles. Umbral: cuantil 1−α (interpolación lineal) de la puntuación de anomalía "
         "en las 65 553 ventanas de validación; anomalía si puntuación > umbral. Evaluación: 65 421 normales + 84 ataques. "
         "ROC-AUC y AP con puntuaciones continuas (no dependen de α). FPR val. = 65 553 ventanas; FPR prueba = 65 421.", ""]
    for a in ALFAS:
        L += ["## α = %s" % str(a).replace(".", ","), "",
              "| Método | TP | FP | TN | FN | Precisión | Recall | F1 | FPR val. | FPR prueba | ROC-AUC | AP |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for f in (x for x in filas if x["alfa"] == a):
            L.append("| %s | %d | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
                f["metodo"], f["TP"], mil(f["FP"]), mil(f["TN"]), f["FN"], pct(f["precision"]), pct(f["recall"]),
                num(f["F1"]), pct(f["FPR_validacion"]), pct(f["FPR_prueba"]), num(f["roc_auc"]), num(f["ap"])))
        L.append("")
    L += ["## Umbrales y tiempos", "", "| Método | α | Umbral (anomalía, >) | Umbral en escala original | t ajuste (s) | t inferencia 131 058 (s) |",
          "|---|---:|---:|---:|---:|---:|"]
    for f in filas:
        L.append("| %s | %s | %r | %s | %s | %s |" % (f["metodo"], str(f["alfa"]).replace(".", ","), f["umbral_anomalia"],
                 "—" if f["umbral_escala_original"] is None else repr(f["umbral_escala_original"]) + " (score_samples <)",
                 "congelado" if f["t_ajuste_s"] is None else num(f["t_ajuste_s"], 1), num(f["t_inferencia_s"], 1)))
    if res["faltantes"]:
        L += ["", "**Sin resultado:** " + ", ".join(res["faltantes"])]
    (AQUI / "TABLA7-comparacion.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    (AQUI / "resultados-comparacion.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n",
                                                      encoding="utf-8", newline="\n")
    # manifiesto
    man = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "equipo": equipo(), "semilla": SEMILLA,
           "entradas_sha256": dict(D["hashes"], **{
               "calibracion-alfa-2026-10-24/validacion-kali-80-excluidas.csv": sha(CAL / "validacion-kali-80-excluidas.csv"),
               **{"datos-sensor/" + p.name: sha(p) for p in sorted(SEN.glob("scores-*.csv.gz"))},
               "datos-sensor/sensor-procedencia.json": sha(SEN / "sensor-procedencia.json")}),
           "codigo_sha256": {"comparar_metodos.py": sha(AQUI / "comparar_metodos.py"),
                             "config-comparacion.json": sha(AQUI / "config-comparacion.json")},
           "documentacion_sha256": {p.name: sha(p) for p in (AQUI / "AUDITORIA-DATOS.json", AQUI / "NOTA-COMPARACION.md",
                                                             AQUI / "REFERENCIAS-VERIFICADAS.md", AQUI / "README.md") if p.exists()},
           "salidas_sha256": {**{"salidas/" + p.name: sha(p) for p in sorted(SAL.iterdir())},
                              **{p.name: sha(p) for p in (AQUI / "TABLA7-comparacion-completa.csv", AQUI / "TABLA7-comparacion.md",
                                                          AQUI / "resultados-comparacion.json")}}}
    (AQUI / "MANIFIESTO-COMPARACION.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))
    print(json.dumps(res.get("verificacion_IF"), indent=1, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--metodo", choices=METODOS)
    g.add_argument("--consolidar", action="store_true")
    g.add_argument("--auditar", action="store_true")
    a = ap.parse_args()
    np.random.seed(SEMILLA)
    D = cargar(a.datos)
    if a.auditar:
        SAL.mkdir(exist_ok=True)
        (AQUI / "AUDITORIA-DATOS.json").write_text(json.dumps({"auditoria": D["aud"], "calidad": D["calidad"], "entradas_sha256": D["hashes"]},
                                                              indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"auditoria": D["aud"], "calidad": {k: v for k, v in D["calidad"].items() if k != "rango_entrenamiento"}},
                         indent=1, ensure_ascii=False))
    elif a.consolidar:
        consolidar(D)
    else:
        correr(a.metodo, D)
