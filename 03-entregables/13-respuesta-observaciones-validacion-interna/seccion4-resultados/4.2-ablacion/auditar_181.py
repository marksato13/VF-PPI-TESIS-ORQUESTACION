#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.2 (1) - Auditoria de etiquetas de las 181 ventanas excluidas del entrenamiento.

`eligible_training=False` significa EXCLUIDA del entrenamiento, NO "maliciosa". Esta
auditoria etiqueta cada una de las 181 ventanas segun evidencia de ataque y separa
las INCIERTAS, para no presentar 50/181 ni 54/181 como "recall".

Criterio de respaldo (ataque respaldado) -- conservador y declarado:
 - dispara un heuristico determinista (port_scan/brute_force/http_abuse/dns_entropy), O
 - cae en la rafaga activa DOCUMENTADA de la Kali (27-sep 21:35-22:05 UTC, nota).
Las demas quedan como INCIERTAS (excluidas por precaucion; sin regla de ataque ni
dentro de la rafaga documentada). NO se parte una rafaga continua en episodios.
"""
from __future__ import annotations
import csv, json, pathlib, importlib.util
from datetime import datetime, timezone

S = pathlib.Path(r"C:\Users\markp\AppData\Local\Temp\claude\C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad")
LIMPIO = S / "exp" / "limpio.csv"
PAQ = S / "run" / "arte" / "paq_despues.joblib"
HEUR_PY = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\heuristicos.py")
OUT = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\aqui trabajamos ...claude\analisis-seccion4\4.2-ablacion")
# repo (para dejarlo versionado tambien)
OUT_REPO = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion")

RAFAGA_INI = datetime(2026, 9, 27, 21, 35, tzinfo=timezone.utc).timestamp()
RAFAGA_FIN = datetime(2026, 9, 27, 22, 5, tzinfo=timezone.utc).timestamp()

def ts(s):
    s = (s or "").strip().replace("Z", "+00:00")
    try: return float(s)
    except ValueError: pass
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

def heur_mod():
    spec = importlib.util.spec_from_file_location("heuristicos", HEUR_PY)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    import numpy as np, joblib
    H = heur_mod()
    paq = joblib.load(PAQ)
    modelo, esc, feats, umbral = paq["modelo"], paq["escalador"], paq["features"], float(paq["umbral"])
    k = []
    with open(LIMPIO, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("eligible_training") == "False":
                k.append(r)
    X = np.asarray([[float(r[c]) for c in feats] for r in k], dtype=float)
    scores = modelo.decision_function(esc.transform(X))

    filas = []
    n_resp = n_inc = n_rafaga = n_heur = 0
    for r, sc in zip(k, scores):
        t = ts(r.get("window_end_utc"))
        v = H.evaluar(r)
        en_rafaga = (t is not None and RAFAGA_INI <= t <= RAFAGA_FIN)
        model_alert = bool(sc < umbral)
        respaldada = bool(v) or en_rafaga
        etiqueta = "ataque_respaldado" if respaldada else "incierto"
        if respaldada: n_resp += 1
        else: n_inc += 1
        if en_rafaga: n_rafaga += 1
        if v: n_heur += 1
        filas.append({
            "entity_ip": r.get("entity_ip"), "window_end_utc": r.get("window_end_utc"),
            "en_rafaga_documentada": int(en_rafaga),
            "heuristico": (v or {}).get("heuristico", ""), "accion": (v or {}).get("accion", ""),
            "model_alerta": int(model_alert), "score_df": round(float(sc), 4),
            "packet_count_10s": r.get("packet_count_10s"),
            "flow_attempt_count_30s": r.get("flow_attempt_count_30s"),
            "syn_count_10s": r.get("syn_count_10s"),
            "http_request_count_60s": r.get("http_request_count_60s"),
            "dns_query_count_60s": r.get("dns_query_count_60s"),
            "etiqueta_auditada": etiqueta,
        })

    # deteccion SOLO sobre el subconjunto respaldado (no sobre 181)
    resp = [f for f in filas if f["etiqueta_auditada"] == "ataque_respaldado"]
    det_model_resp = sum(1 for f in resp if f["model_alerta"])
    det_heur_resp = sum(1 for f in resp if f["heuristico"])
    det_hib_resp = sum(1 for f in resp if f["model_alerta"] or f["heuristico"])
    # rango temporal
    ts_all = sorted(ts(r.get("window_end_utc")) for r in k if ts(r.get("window_end_utc")))
    span = (datetime.utcfromtimestamp(ts_all[0]).isoformat()+"Z", datetime.utcfromtimestamp(ts_all[-1]).isoformat()+"Z") if ts_all else (None, None)
    entidades = {}
    for r in k:
        e = r.get("entity_ip"); entidades[e] = entidades.get(e, 0) + 1

    for d in (OUT, OUT_REPO):
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "auditoria-181-ventanas.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys())); w.writeheader(); [w.writerow(x) for x in filas]

    md = []
    md.append("# 4.2 (1) - Auditoria de etiquetas de las 181 ventanas excluidas")
    md.append("")
    md.append("`eligible_training=False` = EXCLUIDA del entrenamiento, **no** = maliciosa. Por eso NO se")
    md.append("presenta 50/181 ni 54/181 como *recall*. Se etiqueta cada ventana y se separan las inciertas.")
    md.append("")
    md.append("## Composicion")
    md.append("")
    md.append("- Total excluidas: **%d**" % len(k))
    md.append("- Entidades: %s" % ", ".join("%s=%d" % (e, n) for e, n in sorted(entidades.items(), key=lambda x:-x[1])))
    md.append("- Rango temporal (una sola rafaga continua, NO se parte en episodios): %s -> %s" % span)
    md.append("- En la **rafaga activa documentada** (27-sep 21:35-22:05 UTC): **%d**" % n_rafaga)
    md.append("- Disparan un **heuristico** determinista: **%d**" % n_heur)
    md.append("")
    md.append("## Resultado de la auditoria")
    md.append("")
    md.append("**Las %d caen TODAS dentro del periodo de ataque documentado** (27-sep 21:35-22:05 UTC)," % n_rafaga)
    md.append("una sola rafaga continua. Pero eso es una etiqueta de **PERIODO**, no una verdad por-ventana de")
    md.append("trafico malicioso activo: dentro de una rafaga hay ventanas de 10 s de baja intensidad o huecos.")
    md.append("Por eso NO se declara recall por-ventana sobre estas 181.")
    md.append("")
    md.append("| Etiqueta | Ventanas |")
    md.append("|---|---:|")
    md.append("| en periodo de ataque documentado | %d |" % n_rafaga)
    md.append("| de ellas, con senal fuerte (dispara heuristico) | %d |" % n_heur)
    md.append("| incierto (fuera de rafaga / sin regla) | %d |" % n_inc)
    md.append("")
    md.append("## Fraccion de ventanas del periodo marcadas por cada componente (NO es recall)")
    md.append("")
    md.append("| Componente | Ventanas marcadas / total del periodo |")
    md.append("|---|---:|")
    md.append("| IF limpio | %d/%d |" % (det_model_resp, len(resp)))
    md.append("| Heuristicos | %d/%d |" % (det_heur_resp, len(resp)))
    md.append("| Hibrido (OR) | %d/%d |" % (det_hib_resp, len(resp)))
    md.append("")
    md.append("> Esto NO es un recall de laboratorio: las 181 son contaminacion ambiental de una sola")
    md.append("> rafaga, no una bateria curada con ground truth por familia. El recall formal por familia")
    md.append("> sale de la bateria instrumentada nueva (4.2 paso 2), no de aqui.")
    md.append("")
    md.append("Detalle por ventana: `auditoria-181-ventanas.csv`.")
    texto = "\n".join(md)
    for d in (OUT, OUT_REPO):
        (d / "AUDITORIA-181-VENTANAS.md").write_text(texto, encoding="utf-8")

    print("181 -> respaldadas %d (rafaga %d, heur %d) | inciertas %d" % (n_resp, n_rafaga, n_heur, n_inc))
    print("deteccion sobre respaldadas (n=%d): IF %d  heur %d  hibrido %d" % (len(resp), det_model_resp, det_heur_resp, det_hib_resp))
    print("span:", span)
    print("OK ->", OUT_REPO)

if __name__ == "__main__":
    raise SystemExit(main())
