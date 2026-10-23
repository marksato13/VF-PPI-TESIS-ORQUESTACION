#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica los heuristicos VIGENTES (heuristicos.py) a un features.csv por ventana
(el que emite extract_multilayer_v2.py en el replay) y marca la primera ventana que
dispara, con regla y accion. Complementa a 20-puntuar-por-ventana.py (que solo da el
modelo) para cerrar el componente heuristico en el camino de replay (4.2/4.3).

Uso:
  python heuristicos_por_ventana.py --csv features.csv \
     --heuristicos /ruta/a/producto-main/scripts/engine/heuristicos.py \
     --t-inicio <epoch o ISO>   [--salida-csv por-ventana-heur.csv]
Imprime JSON con primera_alerta (window_end_utc, regla, accion, t_deteccion_s) y conteo.
"""
from __future__ import annotations
import argparse, csv, json, importlib.util
from datetime import datetime

def ts(v):
    try: return float(v)
    except (TypeError, ValueError): pass
    s = str(v).strip().replace("Z", "+00:00")
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

def cargar(path):
    spec = importlib.util.spec_from_file_location("heuristicos", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--heuristicos", required=True)
    ap.add_argument("--t-inicio", required=True)
    ap.add_argument("--salida-csv", default="")
    a = ap.parse_args()
    H = cargar(a.heuristicos)
    t0 = ts(a.t_inicio)
    with open(a.csv, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    primera = None; n = 0; reglas = {}
    salida = []
    for r in filas:
        v = H.evaluar(r)
        we = r.get("window_end_utc", "")
        disparo = bool(v)
        if disparo:
            n += 1; reglas[v["heuristico"]] = reglas.get(v["heuristico"], 0) + 1
            te = ts(we)
            if te is not None and (primera is None or te < primera["epoch"]):
                primera = {"epoch": te, "window_end_utc": we, "regla": v["heuristico"],
                           "accion": v["accion"], "motivo": v["motivo"]}
        salida.append({"window_end_utc": we, "heuristico": v["heuristico"] if v else "",
                       "accion": v["accion"] if v else "", "motivo": v["motivo"] if v else ""})
    if primera and t0 is not None:
        primera["t_deteccion_s"] = round(primera["epoch"] - t0, 3)
    if a.salida_csv:
        with open(a.salida_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["window_end_utc","heuristico","accion","motivo"])
            w.writeheader(); [w.writerow(s) for s in salida]
    print(json.dumps({"version_umbrales": H.VERSION_UMBRALES, "ventanas": len(filas),
                      "con_alerta": n, "reglas": reglas, "primera_alerta": primera},
                     indent=2, ensure_ascii=False))

if __name__ == "__main__":
    raise SystemExit(main())
