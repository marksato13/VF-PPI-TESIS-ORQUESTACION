#!/usr/bin/env python3
"""Analizador de la campaña A (detección). No ejecuta la campaña; procesa sus registros.

Entradas:
  --marcas       marcas.jsonl del generador (eventos inicio/fin con reloj de pared y monotónico)
  --motor        motor_decision.log del sensor (registros 'decision' con logged_at = hora REAL de emisión)
  --config       config-campana.json (umbrales, origen); por defecto ../config-campana.json
  --control      (opcional) "desde,hasta" en epoch o ISO: ventana de control normal para la FPR
  --etiquetas    (opcional) CSV entity_ip,window_end_utc,etiqueta: SOLO con esto se calculan métricas por ventana
  --destinos     (opcional) CSV episodio_id,window_end_utc,destino: refuerza la atribución por destino

Reglas:
  - La detección OPERATIVA se clasifica por logged_at (emisión real), NUNCA por window_end.
  - "Emitido en vivo" = registro con decision==ALERT. "Derivado" = configuración recomputada sobre la ventana
    observada (IF_0.03, HEUR LIMIT, híbridos) que el motor NO emitió como ALERT. No se mezclan.
  - Sin etiquetas suficientes NO se fabrican métricas por ventana (TP/FP).
"""
from __future__ import annotations
import argparse, csv, json, math, sys
from datetime import datetime, timezone
from pathlib import Path

PASO_S = 10
HORIZONTE_S = 60
CONFIGS = ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03")
REQ_MOTOR = ("logged_at", "entity_ip", "window_end_utc", "score", "threshold", "decision", "packet_count_10s")


def ep_iso(s) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def como_epoch(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return ep_iso(v)


def familia(escenario: str) -> str:
    return {"dns_inusual": "DNS inusual", "inundacion_http": "Inundación HTTP",
            "escaneo_breve": "Escaneo breve", "escaneo_sostenido": "Escaneo sostenido",
            "fuerza_bruta_http": "Fuerza bruta HTTP"}.get(escenario, escenario)


# ------------------------------------------------------------------- lectura y validación
def leer_marcas(path: Path):
    episodios, inc = {}, []
    for ln, linea in enumerate(open(path, encoding="utf-8"), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            inc.append(f"marcas.jsonl:{ln}: no es JSON")
            continue
        ev = e.get("evento")
        if ev == "inicio":
            episodios[e["episodio_id"]] = {
                "escenario": e.get("escenario"), "repeticion": e.get("repeticion"),
                "destino": e.get("destino"), "comando": e.get("comando"),
                "inicio": e["reloj"]["pared_utc"], "inicio_ep": ep_iso(e["reloj"]["pared_utc"]),
                "fin": None, "fin_ep": None, "estado": "sin_fin"}
        elif ev == "fin":
            ep = episodios.get(e["episodio_id"])
            if ep is None:
                inc.append(f"marcas.jsonl:{ln}: fin sin inicio para {e['episodio_id']}")
            else:
                ep["fin"] = e["reloj"]["pared_utc"]
                ep["fin_ep"] = ep_iso(e["reloj"]["pared_utc"])
                ep["estado"] = e.get("estado", "completo")
    for eid, ep in episodios.items():
        if ep["estado"] == "sin_fin":
            inc.append(f"episodio {eid}: inicio sin fin (incompleto)")
    return episodios, inc


def leer_motor(path: Path):
    regs, inc, claves = [], [], {}
    for ln, linea in enumerate(open(path, encoding="utf-8"), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            r = json.loads(linea)
        except json.JSONDecodeError:
            inc.append(f"motor:{ln}: no es JSON")
            continue
        if r.get("event") != "decision":
            continue
        falta = [k for k in REQ_MOTOR if k not in r]
        if falta:
            inc.append(f"motor:{ln}: faltan claves {falta}")
            continue
        try:
            r["_logged"] = float(r["logged_at"])
            r["_wend"] = ep_iso(r["window_end_utc"])
            r["_score"] = float(r["score"])
            r["_pk10"] = float(r["packet_count_10s"])
        except (ValueError, TypeError) as ex:
            inc.append(f"motor:{ln}: valor inválido ({ex})")
            continue
        k = (r["entity_ip"], r["window_end_utc"])
        claves[k] = claves.get(k, 0) + 1
        regs.append(r)
    dups = {f"{ip}|{w}": n for (ip, w), n in claves.items() if n > 1}
    if dups:
        inc.append(f"ventanas duplicadas (entity_ip|window_end): {len(dups)} — se deduplican para el conteo")
    # dedup por (entity_ip, window_end) conservando la primera; los duplicados quedan reportados en 'inc'/'dups'
    visto, dedup = set(), []
    for r in regs:
        k = (r["entity_ip"], r["window_end_utc"])
        if k in visto:
            continue
        visto.add(k)
        dedup.append(r)
    dedup.sort(key=lambda r: r["_logged"])
    return dedup, inc, dups


# ------------------------------------------------------------------- señales por ventana
def senales(r: dict, u05: float, u03: float) -> dict:
    tiene_pk = r["_pk10"] > 0
    if05 = tiene_pk and r["_score"] < u05
    if03 = tiene_pk and r["_score"] < u03
    heur = r.get("heuristico") is not None
    return {"IF_0.05": if05, "IF_0.03": if03, "HEUR": heur,
            "HIB_0.05": if05 or heur, "HIB_0.03": if03 or heur,
            "emitido_alert": r.get("decision") == "ALERT"}


def discontinuidades(wends: list[float]) -> int:
    if len(wends) < 2:
        return 0
    ws = sorted(set(wends))
    return sum(1 for a, b in zip(ws, ws[1:]) if round(b - a) > PASO_S)


# ------------------------------------------------------------------- clasificación por episodio
def clasificar(ep: dict, regs: list[dict], origen: str, u05: float, u03: float,
               destinos: dict | None) -> dict:
    """D/P/N/NE por configuración, usando logged_at (emisión). Atribución por origen (+destino si se aporta)."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    evaluable = ep["estado"] == "completo" and fin is not None
    lim = (fin + HORIZONTE_S) if fin else None
    # registros de la Kali emitidos dentro del intervalo del episodio
    dentro = [r for r in regs if r["entity_ip"] == origen and ini <= r["_logged"] <= (lim or ini)]
    # cobertura: ¿hay ventanas de la Kali que cubran [ini, lim]? (para poder afirmar "sin detección")
    cobertura_ok = evaluable and bool(dentro) and discontinuidades([r["_wend"] for r in dentro]) == 0
    res = {"evaluable": evaluable, "cobertura_continua": cobertura_ok,
           "n_ventanas_kali_en_intervalo": len(dentro), "estado_generador": ep["estado"]}
    for cfg in CONFIGS:
        firmas = []
        for r in dentro:
            s = senales(r, u05, u03)
            if not s[cfg]:
                continue
            if destinos is not None:
                dst = destinos.get((ep_id_de(ep), r["window_end_utc"]))
                if dst is not None and dst != ep.get("destino"):
                    continue  # anomalía de la Kali hacia otro destino: no es este ataque
            firmas.append((r, s))
        durante = [(r, s) for r, s in firmas if r["_logged"] <= fin]
        posterior = [(r, s) for r, s in firmas if fin < r["_logged"] <= lim]
        if durante:
            r, s = durante[0]
            cat = "durante"
        elif posterior:
            r, s = posterior[0]
            cat = "posterior"
        elif not evaluable or not cobertura_ok:
            cat, r, s = "no_evaluable", None, None
        else:
            cat, r, s = "sin_deteccion", None, None
        celda = {"categoria": cat}
        if r is not None:
            celda.update({
                "logged_at_utc": datetime.fromtimestamp(r["_logged"], timezone.utc).isoformat(),
                "desde_inicio_generador_s": round(r["_logged"] - ini, 1),
                "tras_fin_generador_s": round(r["_logged"] - fin, 1),
                "window_end_utc": r["window_end_utc"],
                "score": round(r["_score"], 6), "emitido_en_vivo": s["emitido_alert"],
                "detector_name": r.get("detector_name"),
                "heuristico": (r.get("heuristico") or {}).get("heuristico") if r.get("heuristico") else None,
                "atribucion": "origen+destino" if destinos is not None else "solo_origen(pendiente_destino_PCAP)"})
        res[cfg] = celda
    # compartidas/exclusivas durante el ataque (ventanas evaluadas de la Kali)
    comp = {"ambos_0.05": 0, "solo_IF_0.05": 0, "solo_HEUR": 0, "ninguno_0.05": 0}
    for r in [x for x in dentro if x["_logged"] <= (fin or ini)]:
        s = senales(r, u05, u03)
        if s["IF_0.05"] and s["HEUR"]:
            comp["ambos_0.05"] += 1
        elif s["IF_0.05"]:
            comp["solo_IF_0.05"] += 1
        elif s["HEUR"]:
            comp["solo_HEUR"] += 1
        else:
            comp["ninguno_0.05"] += 1
    res["compartidas_durante_0.05"] = comp
    return res


def ep_id_de(ep: dict) -> str:
    return f"{ep['escenario']}-r{ep['repeticion']}"


# ------------------------------------------------------------------- control normal (FPR)
def fpr_control(regs, desde, hasta, origen, u05, u03, excluidas: set) -> dict:
    v = [r for r in regs if desde <= r["_logged"] <= hasta and r["entity_ip"] not in excluidas]
    n = len(v)
    out = {"ventanas": n, "denominador": n,
           "desde": datetime.fromtimestamp(desde, timezone.utc).isoformat(),
           "hasta": datetime.fromtimestamp(hasta, timezone.utc).isoformat()}
    if n == 0:
        out["aviso"] = "sin ventanas en la ventana de control"
        return out
    for cfg in CONFIGS:
        fa = sum(1 for r in v if senales(r, u05, u03)[cfg])
        out[cfg] = {"falsas_alarmas": fa, "tasa": round(fa / n, 6)}
    return out


# ------------------------------------------------------------------- métricas por ventana (solo con etiquetas)
def metricas_por_ventana(regs, etiquetas: dict, u05, u03) -> dict:
    pares = [(r, etiquetas[(r["entity_ip"], r["window_end_utc"])]) for r in regs
             if (r["entity_ip"], r["window_end_utc"]) in etiquetas]
    if not pares:
        return {"calculadas": False, "motivo": "ninguna ventana del motor coincide con el fichero de etiquetas"}
    out = {"calculadas": True, "n_etiquetadas": len(pares), "denominador": len(pares)}
    for cfg in CONFIGS:
        tp = fp = tn = fn = 0
        for r, y in pares:
            p = 1 if senales(r, u05, u03)[cfg] else 0
            y = int(y)
            tp += p and y; fp += p and not y; tn += (not p) and (not y); fn += (not p) and y
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        out[cfg] = {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
                    "precision": round(prec, 6) if prec is not None else None,
                    "recall": round(rec, 6) if rec is not None else None,
                    "FPR": round(fp / (fp + tn), 6) if fp + tn else None}
    return out


# ------------------------------------------------------------------- principal
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True)
    ap.add_argument("--motor", required=True)
    ap.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "config-campana.json"))
    ap.add_argument("--control")
    ap.add_argument("--etiquetas")
    ap.add_argument("--destinos")
    ap.add_argument("--salida", default="analisis")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    u05 = cfg["umbrales"]["0.05"]
    u03 = cfg["umbrales"]["0.03"]
    origen = cfg.get("origen")
    if not origen:  # config-campana.json lo lleva dentro de escenarios.lista.*.origen
        esc = cfg.get("escenarios", {})
        lista = esc.get("lista") if isinstance(esc, dict) else None
        origen = (next(iter(lista.values()))["origen"] if isinstance(lista, dict) and lista else "10.10.20.30")
    excluidas = set(cfg.get("combinacion_real", {}).get("exclusiones", {}).get("NUNCA_BLOQUEAR", []))

    episodios, inc_m = leer_marcas(Path(a.marcas))
    regs, inc_r, dups = leer_motor(Path(a.motor))
    destinos = None
    if a.destinos:
        destinos = {}
        for row in csv.DictReader(open(a.destinos, encoding="utf-8")):
            destinos[(row["episodio_id"], row["window_end_utc"])] = row["destino"]

    por_ep, tabla = {}, {}
    for eid, ep in episodios.items():
        c = clasificar(ep, regs, origen, u05, u03, destinos)
        por_ep[eid] = c
        fam = familia(ep["escenario"])
        tabla.setdefault(fam, {"evaluables": [], "no_evaluables": [], **{cfg_: 0 for cfg_ in CONFIGS}})
        if c["evaluable"] and c["cobertura_continua"]:
            tabla[fam]["evaluables"].append(eid)
            for cfg_ in CONFIGS:
                if c[cfg_]["categoria"] == "durante":
                    tabla[fam][cfg_] += 1
        else:
            tabla[fam]["no_evaluables"].append(eid)

    salida = {
        "fuentes": {"marcas": a.marcas, "motor": a.motor, "config": a.config},
        "umbrales": {"0.05": u05, "0.03": u03}, "origen": origen,
        "clasificacion_por": "logged_at (hora real de emisión); window_end NO se usa para emisión",
        "calidad_datos": {"incidencias_marcas": inc_m, "incidencias_motor": inc_r,
                          "ventanas_duplicadas": len(dups),
                          "episodios_incompletos": [e for e, v in episodios.items() if v["estado"] != "completo"],
                          "episodios_sin_cobertura_motor": [e for e, c in por_ep.items()
                                                            if c["n_ventanas_kali_en_intervalo"] == 0]},
        "tabla8": tabla, "episodios": por_ep}

    if a.control:
        d, h = a.control.split(",")
        salida["control_normal_fpr"] = fpr_control(regs, como_epoch(d), como_epoch(h), origen, u05, u03, excluidas)
    else:
        salida["control_normal_fpr"] = {"calculado": False, "motivo": "no se pasó --control"}

    if a.etiquetas:
        et = {(r["entity_ip"], r["window_end_utc"]): r["etiqueta"]
              for r in csv.DictReader(open(a.etiquetas, encoding="utf-8"))}
        salida["metricas_por_ventana"] = metricas_por_ventana(regs, et, u05, u03)
    else:
        salida["metricas_por_ventana"] = {"calculadas": False,
                                          "motivo": "sin --etiquetas no se fabrican métricas por ventana"}

    sd = Path(a.salida)
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "analisis.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    _tabla_md(sd / "TABLA8.md", tabla, salida)
    print(json.dumps({"tabla8": tabla, "calidad": salida["calidad_datos"]}, ensure_ascii=False, indent=1))
    return 0


def _tabla_md(path: Path, tabla: dict, salida: dict):
    L = ["# Tabla 8 — campaña A (generada por analizar.py)", "",
         "Celda: episodios con **detección durante la ejecución** / episodios evaluables. Clasificación por",
         "`logged_at` (emisión real). Las configuraciones derivadas offline no son alertas emitidas en vivo.", "",
         "| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |",
         "|---|---|---|---|---|---|---|"]
    for fam, t in tabla.items():
        n = len(t["evaluables"])
        cel = [f"{t[c]}/{n}" if n else "—" for c in CONFIGS]
        L.append(f"| {fam} | {n} | " + " | ".join(cel) + " |")
    L += ["", f"Episodios no evaluables: " +
          (", ".join(e for t in tabla.values() for e in t["no_evaluables"]) or "ninguno"),
          "", "Métricas por ventana: " +
          ("calculadas" if salida["metricas_por_ventana"].get("calculadas") else
           "no calculadas (" + salida["metricas_por_ventana"]["motivo"] + ")")]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
