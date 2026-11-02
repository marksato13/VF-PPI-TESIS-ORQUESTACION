"""Cortes del Isolation Forest desplegado sobre flow_duration_mean_30s, en segundos.

Si ningun corte cae entre el valor truncado por el horizonte de 230 s y el valor real, el
recorrido de la fila por cada arbol (y por tanto el score) no cambia.
Uso: python -I cortes_duracion.py modelo.joblib manifiesto.json salida.json"""
import json, sys
import joblib
import numpy as np

modelo = joblib.load(sys.argv[1])
man = json.load(open(sys.argv[2], encoding="utf-8"))
nombres = man["detectors"]["if_limpio_2026_10"]["features"]
i = nombres.index("flow_duration_mean_30s")
pasos = getattr(modelo, "steps", None)
print("tipo", type(modelo).__name__, [(n, type(p).__name__) for n, p in pasos] if pasos else "")
if pasos:
    pre = [p for _, p in pasos[:-1]]
    bosque = pasos[-1][1]
else:
    pre, bosque = [], modelo


def a_original(v):
    """Invierte las transformaciones previas (columna i) para un valor escalado v."""
    x = np.zeros((1, len(nombres)))
    x[0, i] = v
    for p in reversed(pre):
        x = p.inverse_transform(x)
    return float(x[0, i])


info = {"feature_index": i, "preprocesado": [type(p).__name__ for p in pre]}
for p in pre:
    for a in ("center_", "scale_", "mean_", "var_", "data_min_", "data_max_", "quantiles_"):
        if hasattr(p, a):
            v = getattr(p, a)
            info[f"{type(p).__name__}.{a}"] = (np.asarray(v)[..., i].tolist() if np.ndim(v) else v)
cortes = []
for est, feats in zip(bosque.estimators_, bosque.estimators_features_):
    t = est.tree_
    for n in range(t.node_count):
        if t.children_left[n] != -1 and feats[t.feature[n]] == i:
            cortes.append(a_original(float(t.threshold[n])))
cortes = sorted(cortes)
c = np.array(cortes)
info.update({
    "n_arboles": len(bosque.estimators_), "n_cortes": len(cortes),
    "corte_min_s": float(c.min()), "corte_max_s": float(c.max()),
    "percentiles_cortes_s": {p: float(np.percentile(c, p)) for p in (50, 90, 99)},
    "cortes_ge": {str(k): int((c >= k).sum()) for k in (60, 120, 180, 200, 220, 228, 230)},
    "max_samples": getattr(bosque, "max_samples_", None),
})
json.dump(info, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
print(json.dumps(info)[:1500])
