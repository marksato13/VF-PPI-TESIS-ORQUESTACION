"""Comprobación de tablas publicadas; solo lectura, sin inferencia ni entrenamiento."""
import csv
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FUENTE = REPO / "03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25"


def cargar_csv(nombre):
    with (FUENTE / nombre).open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def metricas(fila):
    tp, fp, tn, fn = (int(fila[k]) for k in ("TP", "FP", "TN", "FN"))
    assert tp + fn == 84 and fp + tn == 65421
    assert tp + fp + tn + fn == 65505
    return dict(precision=tp / (tp + fp), recall=tp / (tp + fn),
                F1=2 * tp / (2 * tp + fp + fn), FPR_prueba=fp / (fp + tn))


def main():
    tabla = cargar_csv("TABLA7-comparacion-completa.csv")
    resultados = json.loads((FUENTE / "resultados-comparacion.json").read_text(encoding="utf-8-sig"))
    indice = {(f["metodo"], float(f["alfa"])): f for f in resultados["tabla"]}
    assert len(tabla) == len(indice) == 10
    for f in tabla:
        original = indice[f["metodo"], float(f["alfa"])]
        for k in ("TP", "FP", "TN", "FN", "n_validacion", "n_normales_prueba", "n_ataques"):
            assert int(f[k]) == original[k]
        for k, v in metricas(f).items():
            assert math.isclose(v, float(f[k]), rel_tol=0, abs_tol=1e-12)
            assert math.isclose(v, original[k], rel_tol=0, abs_tol=1e-12)
        assert int(f["n_validacion"]) == 65553
    print("OK: 10/10 matrices Tabla 7; CSV = JSON; cuatro métricas exactas a tolerancia 1e-12.")
    complemento = cargar_csv("TABLA7c-alfa0.01.csv")
    assert len(complemento) == 5
    for f in complemento:
        m = metricas(f)
        for k, columna in (("precision", "precision_pct"), ("recall", "recall_pct"), ("FPR_prueba", "FPR_prueba_pct")):
            assert abs(100 * m[k] - float(f[columna])) <= 0.005000001
        assert abs(m["F1"] - float(f["F1"])) <= 0.000050001
    print("OK: 5/5 matrices Tabla 7c; porcentajes a 2 decimales y F1 a 4.")
    for alfa, tp, fp, tn, fn in (("operativo 0.05 / 65633", 54, 2961, 62460, 30),
                                ("analítico 0.05 / 65553", 54, 2955, 62466, 30),
                                ("analítico 0.03 / 65553", 54, 1723, 63698, 30),
                                ("analítico 0.01 / 65553", 50, 567, 64854, 34)):
        m = metricas(dict(TP=tp, FP=fp, TN=tn, FN=fn))
        print(alfa, {k: round(v * 100, 6) for k, v in m.items()})
    print("Prevalencia (%):", 100 * 84 / 65505)
    manifiesto = json.loads((FUENTE / "MANIFIESTO-COMPARACION.json").read_text(encoding="utf-8-sig"))
    for nombre in ("TABLA7-comparacion-completa.csv", "resultados-comparacion.json", "config-comparacion.json"):
        bruto = (FUENTE / nombre).read_bytes()
        lf = bruto.replace(b"\r\n", b"\n")
        esperado = (manifiesto["codigo_sha256"] if nombre == "config-comparacion.json" else manifiesto["salidas_sha256"])[nombre]
        variantes = {"bytes locales": bruto, "LF": lf, "CRLF reconstruido": lf.replace(b"\n", b"\r\n")}
        coincidencias = [k for k, v in variantes.items() if hashlib.sha256(v).hexdigest() == esperado]
        assert coincidencias, (nombre, "hash no coincide ni con LF ni con CRLF")
        print("SHA-256", nombre, esperado, "coincide:", ", ".join(coincidencias))


if __name__ == "__main__":
    main()
