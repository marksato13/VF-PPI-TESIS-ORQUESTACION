#!/usr/bin/env python3
"""Calibracion alfa del IF congelado if_limpio_2026_10 - parte que corre EN EL SENSOR (solo lectura).

Puntua con el pipeline desplegado (escalador + IF) validacion, prueba normal y ataques,
y verifica procedencia: hashes, orden de caracteristicas, conteos, solapes y las
181 exclusiones de entrenamiento. No reentrena, no escribe en ~/cyberflow.
Salida: ~/analisis/calib-alfa-2026-10-24/
"""
import csv, gzip, hashlib, json, pathlib, collections, sys, datetime
import numpy as np, joblib, sklearn

A = pathlib.Path("/home/m4rk/cyberflow/artifacts")
D = A / "preliminar" / "limpio-2026-10"
F = {
    "modelo_desplegado": D / "if_limpio_2026_10_desplegable.joblib",
    "manifiesto_desplegable": D / "manifest-if-limpio-2026-10.json",
    "informe_entrenamiento": D / "if_limpio_2026_10.json",
    "particionado_limpio": D / "particionado-limpio.csv",
    "particionado_nota_L": A / "aprendizaje" / "base" / "particionado-nota-L.csv",
    "oro_prueba_normal": A / "aprendizaje" / "oro" / "oro.csv",
    "ataques_nota_M": A / "aprendizaje" / "ataques" / "ataques-nota-M.csv",
}
OUT = pathlib.Path.home() / "analisis" / "calib-alfa-2026-10-24"
OUT.mkdir(parents=True, exist_ok=True)
KALI = "10.10.20.30"
U_OP = -0.5693969936322356

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def leer(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def clave(r):
    return (r["campaign_id"], r["entity_ip"], r["window_end_utc"])

res = {"generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "host": "cyberflow-sensor (10.10.60.11)", "modo": "solo lectura",
       "runtime": {"python": sys.version.split()[0], "sklearn": sklearn.__version__, "numpy": np.__version__},
       "entradas_sha256": {k: sha(v) for k, v in F.items()}}

man = json.loads(F["manifiesto_desplegable"].read_text())
inf = json.loads(F["informe_entrenamiento"].read_text())
det = man["detectors"]["if_limpio_2026_10"]
feats = det["features"]
mdl = joblib.load(F["modelo_desplegado"])
res["modelo"] = {
    "sha256_declarado_manifiesto": det["model_sha256"],
    "sha256_coincide": det["model_sha256"] == res["entradas_sha256"]["modelo_desplegado"],
    "pasos_pipeline": [n for n, _ in mdl.steps],
    "n_features_in": int(mdl.n_features_in_),
    "orden_features_igual_informe": feats == inf["features"],
    "features": feats,
    "umbral_desplegado": det["calibration"]["threshold"],
    "regla": det["calibration"]["comparison"] + " (" + det["calibration"]["score_function"] + ")",
    "alpha_desplegado": det["calibration"]["alpha"],
    "informe_entrada_sha256": inf["entrada_sha256"],
    "informe_entrada_es_particionado_limpio": inf["entrada_sha256"] == res["entradas_sha256"]["particionado_limpio"],
    "informe_filas": inf["filas"],
}
assert res["modelo"]["sha256_coincide"] and res["modelo"]["orden_features_igual_informe"]
assert mdl.n_features_in_ == len(feats) == 28

def X(rows):
    return np.asarray([[float(r[c]) for c in feats] for r in rows], dtype=float)

lim = leer(F["particionado_limpio"])
notaL = leer(F["particionado_nota_L"])
oro = leer(F["oro_prueba_normal"])
ata = leer(F["ataques_nota_M"])

# --- conteos y la diferencia limpio vs nota-L (181 exclusiones de entrenamiento)
part = collections.Counter(r["particion"] for r in lim)
tr = [r for r in lim if r["particion"] == "train"]
elig = collections.Counter(r["eligible_training"] for r in tr)
assert len(lim) == len(notaL)
dif_cols = collections.Counter(); filas_dif = []
for a, b in zip(lim, notaL):
    assert clave(a) == clave(b)
    dc = [c for c in a if a[c] != b.get(c)]
    if dc:
        filas_dif.append((a, b, dc)); dif_cols.update(dc)
excl_tr = [a for a, b, dc in filas_dif]
res["conteos"] = {
    "particionado_filas": len(lim), "particiones": dict(part),
    "train_eligible_training": dict(elig),
    "kali_por_particion": dict(collections.Counter(r["particion"] for r in lim if r["entity_ip"] == KALI)),
    "oro_filas": len(oro), "oro_kali": sum(r["entity_ip"] == KALI for r in oro),
    "ataques_filas": len(ata), "ataques_entidades": dict(collections.Counter(r["entity_ip"] for r in ata)),
}
res["exclusiones_entrenamiento"] = {
    "filas_distintas_limpio_vs_notaL": len(filas_dif), "columnas_que_difieren": dict(dif_cols),
    "particion_de_esas_filas": dict(collections.Counter(a["particion"] for a in excl_tr)),
    "entidades": dict(collections.Counter(a["entity_ip"] for a in excl_tr)),
    "valores_limpio": dict(collections.Counter(tuple(a[c] for c in dif_cols) for a in excl_tr)),
    "valores_notaL": dict(collections.Counter(tuple(b[c] for c in dif_cols) for _, b, _ in filas_dif)),
    "rango_window_end_utc": [min(a["window_end_utc"] for a in excl_tr), max(a["window_end_utc"] for a in excl_tr)] if excl_tr else None,
}
res["exclusiones_entrenamiento"]["valores_limpio"] = {str(k): v for k, v in res["exclusiones_entrenamiento"]["valores_limpio"].items()}
res["exclusiones_entrenamiento"]["valores_notaL"] = {str(k): v for k, v in res["exclusiones_entrenamiento"]["valores_notaL"].items()}

val = [r for r in lim if r["particion"] == "validation"]
test = [r for r in lim if r["particion"] == "test"]
# validacion identica en nota-L (misma fila, mismos valores)
val_L = [r for r in notaL if r["particion"] == "validation"]
res["validacion_identica_notaL"] = all(a == b for a, b in zip(val, val_L)) and len(val) == len(val_L)

# --- solapes por clave (campaign_id, entity_ip, window_end_utc)
K = {n: set(map(clave, rs)) for n, rs in (("train", tr), ("validation", val), ("test", test), ("oro", oro), ("ataques", ata))}
res["solapes"] = {
    "oro_igual_test_particion": K["oro"] == K["test"],
    "claves_unicas": {n: len(s) for n, s in K.items()},
    "ataques∩validation": len(K["ataques"] & K["validation"]),
    "ataques∩train": len(K["ataques"] & K["train"]),
    "ataques∩test": len(K["ataques"] & K["test"]),
    "validation∩test": len(K["validation"] & K["test"]),
    "validation∩train": len(K["validation"] & K["train"]),
}
# oro con los mismos valores que la particion test (puntuar oro == puntuar test)
tmap = {clave(r): r for r in test}
res["solapes"]["oro_mismos_valores_features_que_test"] = all(
    all(float(r[c]) == float(tmap[clave(r)][c]) for c in feats) for r in oro)

# --- puntuaciones con el pipeline congelado
sv, so, sa = mdl.score_samples(X(val)), mdl.score_samples(X(oro)), mdl.score_samples(X(ata))
res["reproduccion_umbral"] = {
    "q05_validacion_completa_linear": float(np.quantile(sv, 0.05, method="linear")),
    "umbral_desplegado": U_OP,
    "diferencia": float(np.quantile(sv, 0.05, method="linear")) - U_OP,
    "fp_oro_umbral_desplegado": int(np.sum(so < U_OP)), "tp_ataques_umbral_desplegado": int(np.sum(sa < U_OP)),
}

def volcar(nombre, rows, scores, extra=None):
    p = OUT / nombre
    with gzip.open(p, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        cab = ["campaign_id", "entity_ip", "window_end_utc"] + (list(extra) if extra else []) + ["score_samples"]
        w.writerow(cab)
        for r, s in zip(rows, scores):
            w.writerow([r["campaign_id"], r["entity_ip"], r["window_end_utc"]] + [r.get(c, "") for c in (extra or [])] + [repr(float(s))])
    return p

volcar("scores-validacion-65633.csv.gz", val, sv, extra=["packet_count_10s"])
volcar("scores-prueba-normal-65421.csv.gz", oro, so)
volcar("scores-ataques-84.csv.gz", ata, sa, extra=["familia_proxy"] if "familia_proxy" in ata[0] else None)
with open(OUT / "exclusiones-entrenamiento-181.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n"); cols = ["campaign_id", "entity_ip", "window_end_utc", "particion"] + sorted(dif_cols)
    w.writerow(cols + ["valor_notaL::" + c for c in sorted(dif_cols)])
    for a, b, _ in filas_dif:
        w.writerow([a[c] for c in cols] + [b[c] for c in sorted(dif_cols)])
res["salidas_sha256"] = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "sensor-procedencia.json"}
(OUT / "sensor-procedencia.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: res[k] for k in ("modelo", "conteos", "exclusiones_entrenamiento", "validacion_identica_notaL", "solapes", "reproduccion_umbral")}, indent=1, ensure_ascii=False, default=str)[:6000])
print("SALIDAS", json.dumps(res["salidas_sha256"]))
