#!/usr/bin/env python3
"""Métricas comparativas OFFLINE para CyberFlow vs Suricata (y ablación interna).

Calcula, sobre artefactos ya capturados (sin red, sin SSH), las métricas del plan
de evaluación (nota `29`): TPR/FPR/Precisión/F1, latencia por episodio, cobertura y
la ablación modelo-vs-heurísticos.

## Unidad de evaluación (declarada, importa para la honestidad)
- **Detección por EPISODIO:** un episodio cuenta como detectado si al menos una
  marca de detección (epoch) cae dentro de su ventana `[t_inicio, t_fin]`.
- **TPR / recall** se mide sobre episodios (ataques).
- **FPR** se mide sobre **ventanas benignas** (no sobre episodios): proporción de
  ventanas de tráfico normal que produjeron una detección.
- **Precisión / F1** mezclan TP (por episodio) y FP (por ventana benigna). Es una
  aproximación pragmática y se reporta con esa salvedad explícita en el informe.

## Forma del JSON de entrada del CLI
    {
      "episodios": [
        {"id": "E1-scan-1", "familia": "scan",
         "t_inicio": 1791323358, "t_fin": 1791323450, "entidad_ip": "10.10.20.30"}
      ],
      "detecciones": {"E1-scan-1": [1791323370.0, 1791323380.0]},
      "benignas": {"total": 527, "con_deteccion": 0},
      "ablacion": [
        {"id": "E1-scan-1", "detected_by_model": true, "detected_by_heuristic": false}
      ]
    }
Uso: python3 30-metricas.py entrada.json   (imprime el informe JSON)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys


def _detectado(ep: dict, epochs: list) -> bool:
    ini, fin = float(ep["t_inicio"]), float(ep["t_fin"])
    return any(ini <= float(e) <= fin for e in (epochs or []))


def metricas_deteccion(episodios: list, detecciones: dict,
                       ventanas_benignas_total: int,
                       ventanas_benignas_con_deteccion: int) -> dict:
    """TP/FP/FN/TN y las métricas derivadas. Ver unidad de evaluación en el docstring."""
    tp = sum(1 for ep in episodios if _detectado(ep, detecciones.get(ep["id"], [])))
    fn = len(episodios) - tp
    fp = int(ventanas_benignas_con_deteccion)
    tn = int(ventanas_benignas_total) - fp

    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / ventanas_benignas_total if ventanas_benignas_total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * tpr / (precision + tpr)) if (precision + tpr) else 0.0
    total = tp + tn + fp + fn
    exactitud = (tp + tn) / total if total else 0.0
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "TPR_recall": round(tpr, 4),
        "FPR": round(fpr, 4),
        "precision": round(precision, 4),
        "F1": round(f1, 4),
        "exactitud": round(exactitud, 4),
        "_nota_unidad": "TPR sobre episodios; FPR sobre ventanas benignas; "
                        "precision/F1 mezclan ambas unidades (aproximación).",
    }


def latencia_por_episodio(episodios: list, detecciones: dict) -> dict:
    """Latencia = primera detección dentro de la ventana − t_inicio, por episodio."""
    por_id = {}
    for ep in episodios:
        ini, fin = float(ep["t_inicio"]), float(ep["t_fin"])
        dentro = sorted(float(e) for e in detecciones.get(ep["id"], []) if ini <= float(e) <= fin)
        por_id[ep["id"]] = round(dentro[0] - ini, 1) if dentro else None
    valores = [v for v in por_id.values() if v is not None]
    resumen = {
        "mediana_s": round(statistics.median(valores), 1) if valores else None,
        "min_s": min(valores) if valores else None,
        "max_s": max(valores) if valores else None,
        "n_con_latencia": len(valores),
    }
    return {"por_episodio": por_id, "resumen": resumen}


def cobertura(episodios_detectados: int, total: int) -> dict:
    return {"detectados": episodios_detectados, "total": total,
            "fraccion": round(episodios_detectados / total, 4) if total else 0.0}


def ablacion(por_episodio: list) -> dict:
    """Cobertura por configuración: modelo, heurísticos, combinado (OR)."""
    total = len(por_episodio)
    det_modelo = [e["id"] for e in por_episodio if e.get("detected_by_model")]
    det_heur = [e["id"] for e in por_episodio if e.get("detected_by_heuristic")]
    det_comb = [e["id"] for e in por_episodio
                if e.get("detected_by_model") or e.get("detected_by_heuristic")]
    return {
        "modelo": cobertura(len(det_modelo), total),
        "heuristicos": cobertura(len(det_heur), total),
        "combinado": cobertura(len(det_comb), total),
    }


def informe(datos: dict) -> dict:
    episodios = datos.get("episodios", [])
    detecciones = datos.get("detecciones", {})
    benignas = datos.get("benignas", {}) or {}
    rep = {
        "n_episodios": len(episodios),
        "metricas": metricas_deteccion(
            episodios, detecciones,
            int(benignas.get("total", 0)),
            int(benignas.get("con_deteccion", 0))),
        "latencia": latencia_por_episodio(episodios, detecciones),
    }
    detectados = sum(1 for ep in episodios if _detectado(ep, detecciones.get(ep["id"], [])))
    rep["cobertura"] = cobertura(detectados, len(episodios))
    if datos.get("ablacion"):
        rep["ablacion"] = ablacion(datos["ablacion"])
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description="Métricas comparativas offline (nota 29).")
    ap.add_argument("entrada", help="JSON con episodios/detecciones/benignas/ablacion")
    a = ap.parse_args()
    with open(a.entrada, encoding="utf-8") as f:
        datos = json.load(f)
    print(json.dumps(informe(datos), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
