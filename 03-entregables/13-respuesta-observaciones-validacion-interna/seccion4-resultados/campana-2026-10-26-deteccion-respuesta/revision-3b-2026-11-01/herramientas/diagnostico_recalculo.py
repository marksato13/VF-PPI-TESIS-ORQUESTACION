#!/usr/bin/env python3
"""Diagnóstico de las reconstrucciones no exactas: recálculo v1 (original) frente a v2 (corregido) y al registro.

Para cada decisión: pk10 y score registrados, recalculados v1 y v2; tipo de diferencia (exacta, puntuación distinta,
sin puntuación: fila con 0 paquetes, null != 0, o sin fila); características que difieren entre v1 y v2; señales IF a
los tres α con el score registrado (lo que usa el análisis) y con el score v1 (efecto hipotético si se hubiera usado
el recálculo); efecto sobre la primera señal y la categoría del episodio.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import analizar as an  # noqa: E402


def leer(p: Path) -> dict:
    return {(r["entity_ip"], r["window_end_utc"]): r for r in map(json.loads, open(p, encoding="utf-8"))}


def tipo(r: dict) -> str:
    if r.get("pk10_recalculado") is None:
        return "sin_fila"
    if r["coincide_pk10"] and r["coincide_score"]:
        return "exacta"
    if r["score_recalculado"] is None and r["score_registrado"] is not None:
        return "sin_puntuacion (fila con 0 paquetes; null no es 0)"
    return "puntuacion_distinta"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v1", required=True, type=Path)
    ap.add_argument("--v2", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--analisis", required=True, type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()
    U = an.umbrales_de(json.load(open(a.config, encoding="utf-8")))
    v1, v2 = leer(a.v1), leer(a.v2)
    A = json.load(open(a.analisis, encoding="utf-8"))["episodios"]

    def sen(s, pk):
        return {al: bool(s is not None and pk and s < U[al]) for al in an.ALFAS}

    filas, resumen = [], {"decisiones_v1": len(v1), "decisiones_v2": len(v2),
                          "exactas_v1": sum(1 for r in v1.values() if tipo(r) == "exacta"),
                          "exactas_v2": sum(1 for r in v2.values() if tipo(r) == "exacta"),
                          "claves_solo_v1": len(set(v1) - set(v2)), "claves_solo_v2": len(set(v2) - set(v1))}
    for k in sorted(set(v1) | set(v2), key=lambda k: k[1]):
        r1, r2 = v1.get(k), v2.get(k)
        t1, t2 = (tipo(r1) if r1 else "falta"), (tipo(r2) if r2 else "falta")
        if t1 == "exacta" and t2 == "exacta":
            continue
        base = r1 or r2
        difs = []
        if r1 and r2 and r1["caracteristicas"] and r2["caracteristicas"]:
            for n, x in r2["caracteristicas"].items():
                y = r1["caracteristicas"].get(n)
                if x is None or y is None or abs(x - y) > 1e-6 * max(1.0, abs(x)):
                    difs.append({"caracteristica": n, "v1": y, "v2": x})
        eid = base["episodio_id"]
        ep = A.get(eid, {})
        v = next((w for w in ep.get("ventanas", []) if w["window_end_utc"] == k[1]), {})
        sr = sen(base["score_registrado"], base["pk10_registrado"])
        s1 = sen(r1["score_recalculado"], r1["pk10_recalculado"]) if r1 else None
        filas.append({
            "episodio": eid, "window_end_utc": k[1],
            "pk10": {"registrado": base["pk10_registrado"], "v1": r1 and r1["pk10_recalculado"],
                     "v2": r2 and r2["pk10_recalculado"]},
            "score": {"registrado": base["score_registrado"], "v1": r1 and r1["score_recalculado"],
                      "v2": r2 and r2["score_recalculado"]},
            "tipo_v1": t1, "tipo_v2": t2,
            "caracteristicas_que_difieren_v1_v2": difs,
            "senal_IF_con_score_registrado": sr, "senal_IF_con_score_v1": s1,
            "efecto_hipotetico_si_se_usara_v1": {al: (sr[al], s1[al]) for al in an.ALFAS if s1 and sr[al] != s1[al]},
            "ventana_en_el_episodio": {k2: v.get(k2) for k2 in ("estado", "atribucion", "senales")} if v else None,
            "primera_senal_episodio": {cf: (ep[cf]["primera"] or {}).get("window_end_utc") for cf in an.CONFIGS} if ep else None,
            "categoria_episodio": {cf: ep[cf]["categoria"] for cf in an.CONFIGS} if ep else None,
            "efecto_real_sobre_el_analisis": "ninguno: el análisis usa el registro en vivo, no el recálculo"})
    resumen["no_exactas_v1"] = sum(1 for f in filas if f["tipo_v1"] != "exacta")
    resumen["no_exactas_v2"] = sum(1 for f in filas if f["tipo_v2"] != "exacta")
    a.salida.write_text(json.dumps({"resumen": resumen, "filas": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resumen))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
