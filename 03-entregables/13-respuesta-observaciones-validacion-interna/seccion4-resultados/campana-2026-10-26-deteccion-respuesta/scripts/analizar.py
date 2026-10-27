#!/usr/bin/env python3
"""Analizador de la campaña A (detección). No ejecuta la campaña; procesa sus registros.

Entradas:
  --marcas    marcas.jsonl del generador (eventos inicio/fin, reloj de pared y monotónico)
  --motor     motor_decision.log del sensor (registros 'decision'; logged_at = hora REAL de emisión)
  --config    config-campana.json (umbrales, origen); por defecto ../config-campana.json
  --control   "desde,hasta" (epoch o ISO): ventana de control normal para la FPR
  --etiquetas CSV entity_ip,window_end_utc,etiqueta: SOLO con esto se calculan métricas por ventana
  --destinos  CSV episodio_id,window_end_utc,destino (una fila por destino; puede haber varias por ventana):
              evidencia de atribución por destino desde PCAP/EVE

Reglas (ver config-campana.json y PLAN):
  - La detección OPERATIVA se clasifica por logged_at (emisión real); window_end NO es la emisión.
  - Cobertura: un episodio es evaluable solo si el motor registró de forma continua todo [inicio, fin+60] y
    hay ventanas de la Kali en todas las anclas del ataque. Una sola ventana NO es cobertura suficiente.
  - Score null = IF no aplicable (p.ej. sin paquetes en 10 s): la fila SE CONSERVA; el heurístico se evalúa igual.
  - Emitido en vivo (ALERT del motor, umbral DESPLEGADO) ≠ configuración derivada (recalculada con otro umbral).
  - Atribución: con evidencia de destino -> 'origen+destino'; sin ella -> 'incompleta' (no es detección confirmada).
  - Una ventana cuyo intervalo (window_end-60, window_end] no solapa el ataque no cuenta como detección del ataque.
  - Sin etiquetas suficientes NO se fabrican métricas por ventana.
"""
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PASO_S = 10
HORIZONTE_S = 60                      # horizonte de la característica más larga
TOL_CONTINUIDAD_S = 2 * PASO_S        # hueco máximo tolerado en el registro del motor
CONFIGS = ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03")
REQ_MOTOR = ("logged_at", "entity_ip", "window_end_utc", "threshold", "decision", "packet_count_10s")
AUTH_DETECTOR = "auth_failure_heuristic"


def ep_iso(s) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def como_epoch(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return ep_iso(v)


def iso(ep) -> str:
    return datetime.fromtimestamp(ep, timezone.utc).isoformat()


def familia(esc: str) -> str:
    return {"dns_inusual": "DNS inusual", "inundacion_http": "Inundación HTTP", "escaneo_breve": "Escaneo breve",
            "escaneo_sostenido": "Escaneo sostenido", "fuerza_bruta_http": "Fuerza bruta HTTP"}.get(esc, esc)


# ------------------------------------------------------------------- lectura y validación
def leer_marcas(path: Path):
    eps, inc = {}, []
    for ln, linea in enumerate(open(path, encoding="utf-8"), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            inc.append(f"marcas:{ln}: no es JSON"); continue
        ev = e.get("evento")
        if ev == "inicio":
            eps[e["episodio_id"]] = {"escenario": e.get("escenario"), "repeticion": e.get("repeticion"),
                                     "destino": e.get("destino"), "inicio_ep": ep_iso(e["reloj"]["pared_utc"]),
                                     "fin_ep": None, "estado": "sin_fin"}
        elif ev == "fin":
            ep = eps.get(e["episodio_id"])
            if ep is None:
                inc.append(f"marcas:{ln}: fin sin inicio {e['episodio_id']}")
            else:
                ep["fin_ep"] = ep_iso(e["reloj"]["pared_utc"]); ep["estado"] = e.get("estado", "completo")
    for eid, ep in eps.items():
        if ep["estado"] == "sin_fin":
            inc.append(f"episodio {eid}: inicio sin fin (incompleto)")
    return eps, inc


def leer_motor(path: Path):
    """Conserva filas con score null (IF no aplicable). Distingue null (no aplicable) de ausente/no numérico (error)."""
    regs, inc, claves = [], [], defaultdict(int)
    for ln, linea in enumerate(open(path, encoding="utf-8"), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            r = json.loads(linea)
        except json.JSONDecodeError:
            inc.append(f"motor:{ln}: no es JSON"); continue
        if r.get("event") != "decision":
            continue
        falta = [k for k in REQ_MOTOR if k not in r]
        if falta:
            inc.append(f"motor:{ln}: faltan claves {falta}"); continue
        try:
            r["_logged"] = float(r["logged_at"]); r["_wend"] = ep_iso(r["window_end_utc"])
            r["_pk10"] = float(r["packet_count_10s"])
        except (ValueError, TypeError) as ex:
            inc.append(f"motor:{ln}: valor inválido ({ex})"); continue
        sc = r.get("score", "__ausente__")
        if sc is None:
            r["_score"], r["_score_estado"] = None, "no_aplicable"       # IF no puntuó (válido)
        elif sc == "__ausente__":
            r["_score"], r["_score_estado"] = None, "ausente_error"
            inc.append(f"motor:{ln}: score ausente (error)")
        else:
            try:
                r["_score"], r["_score_estado"] = float(sc), "ok"
            except (ValueError, TypeError):
                r["_score"], r["_score_estado"] = None, "no_numerico_error"
                inc.append(f"motor:{ln}: score no numérico {sc!r}")
        claves[(r["entity_ip"], r["window_end_utc"])] += 1
        regs.append(r)
    dups = {f"{ip}|{w}": n for (ip, w), n in claves.items() if n > 1}
    if dups:
        inc.append(f"ventanas duplicadas (entity_ip|window_end): {len(dups)} — se deduplican")
    visto, dedup = set(), []
    for r in regs:
        k = (r["entity_ip"], r["window_end_utc"])
        if k in visto:
            continue
        visto.add(k); dedup.append(r)
    dedup.sort(key=lambda r: r["_logged"])
    return dedup, inc, dups


# ------------------------------------------------------------------- señales por ventana
def senales(r: dict, u05: float, u03: float) -> dict:
    """Señal por componente, con score null a salvo, y separación emitido/derivado por componente."""
    sc, pk = r.get("_score"), r.get("_pk10", 0)
    if_valida = (sc is not None) and (pk > 0)
    if05 = bool(if_valida and sc < u05)
    if03 = bool(if_valida and sc < u03)
    heur_field = r.get("heuristico") is not None
    det = r.get("decision") == "ALERT"
    auth_emitio = det and r.get("detector_name") == AUTH_DETECTOR        # regla heredada: SÍ emite ALERT
    modelo_emitio = det and r.get("detector_name") != AUTH_DETECTOR      # el modelo desplegado emitió ALERT
    heur_sig = bool(heur_field or auth_emitio)                           # componente 'heurísticos' (sin duplicar)
    g = {"IF_0.05": if05, "IF_0.03": if03, "HEUR": heur_sig,
         "HIB_0.05": bool(if05 or heur_sig), "HIB_0.03": bool(if03 or heur_sig),
         "if_valida": if_valida, "modelo_emitio_alert": modelo_emitio, "auth_emitio_alert": auth_emitio,
         "heuristico_registrado_en_vivo": heur_field}
    g["base"] = {
        "IF_0.05": "emitido_por_modelo_desplegado" if modelo_emitio else "derivado(umbral_recalibrado)",
        "IF_0.03": "derivado(umbral_no_desplegado)",
        "HEUR": "emitido_ALERT(auth_heredada)" if auth_emitio else ("registrada_en_vivo" if heur_field else "-"),
        "HIB_0.05": "derivado(feed)", "HIB_0.03": "derivado(feed)"}
    return g


# ------------------------------------------------------------------- cobertura temporal
def cobertura(ep: dict, regs_global: list, regs_kali: list) -> dict:
    """¿El motor registró de forma continua [inicio, fin+60] y hay ventanas de la Kali en todas las anclas del ataque?"""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    if ep["estado"] != "completo" or fin is None:
        return {"suficiente": False, "motivo": "episodio incompleto/sin fin", "motor_continuo": False}
    lim = fin + HORIZONTE_S
    # 1) continuidad del motor: NO se deduce de que existan registros; se exige que cubran el intervalo sin huecos
    glog = sorted(r["_logged"] for r in regs_global if ini - PASO_S <= r["_logged"] <= lim + PASO_S)
    if not glog:
        return {"suficiente": False, "motivo": "sin registros del motor en el intervalo (posible pérdida)",
                "motor_continuo": False}
    hueco = max((b - a for a, b in zip(glog, glog[1:])), default=0.0)
    cubre_ini = glog[0] <= ini + TOL_CONTINUIDAD_S
    cubre_fin = glog[-1] >= lim - TOL_CONTINUIDAD_S
    motor_continuo = hueco <= TOL_CONTINUIDAD_S and cubre_ini and cubre_fin
    # 2) anclas de la Kila esperadas durante el ataque (window_end en (inicio, fin])
    import math
    esperadas = [a for a in range(int(math.ceil((ini + 1) / PASO_S) * PASO_S), int(fin) + 1, PASO_S)]
    obs = {int(round(r["_wend"])) for r in regs_kali if ini < r["_wend"] <= fin}
    faltan = [a for a in esperadas if a not in obs]
    suf = motor_continuo and not faltan and len(esperadas) >= 1
    mot = "ok" if suf else (
        "motor no continuo (hueco o no cubre el intervalo)" if not motor_continuo else
        f"faltan {len(faltan)} de {len(esperadas)} anclas de la Kali durante el ataque (pérdida de datos)")
    return {"suficiente": suf, "motivo": mot, "motor_continuo": motor_continuo,
            "anclas_ataque_esperadas": len(esperadas), "anclas_ataque_observadas": len(esperadas) - len(faltan),
            "hueco_motor_max_s": round(hueco, 1), "cubre_inicio": cubre_ini, "cubre_fin_mas_60": cubre_fin}


# ------------------------------------------------------------------- evidencia de destino
def _evidencia_destino_cubre(destinos, eid, kali, ini, fin):
    """¿La evidencia de destino cubre TODAS las ventanas de la Kali durante el ataque (window_end en (ini,fin])?

    No basta con que el mapa exista: un mapa vacío o con claves ausentes no permite confirmar NI descartar la
    atribución de cada ventana, así que el episodio no es evaluable para esta comparación. Cubrir el intervalo
    (aunque ninguna ventana sea del ataque) sí permite confirmar una AUSENCIA con observación completa.
    """
    if destinos is None:
        return {"cubre": False, "motivo": "ausente (no se aportó --destinos)"}
    if fin is None:
        return {"cubre": False, "motivo": "sin fin de episodio"}
    atk = [r for r in kali if ini < r["_wend"] <= fin]            # ventanas de la Kali durante el ataque
    sin_dest = [iso(r["_wend"]) for r in atk if (eid, r["window_end_utc"]) not in destinos]
    tiene_episodio = any(k[0] == eid for k in destinos)
    if not atk:
        # no hay ventanas de la Kali durante el ataque -> la cobertura temporal ya lo marca; aquí informamos
        return {"cubre": bool(tiene_episodio), "motivo": "" if tiene_episodio else
                "sin entradas para este episodio", "ventanas_ataque": 0}
    if sin_dest:
        return {"cubre": False, "ventanas_ataque": len(atk), "ventanas_sin_destino": len(sin_dest),
                "motivo": ("vacía o sin entradas de este episodio" if not tiene_episodio else
                           f"incompleta: {len(sin_dest)}/{len(atk)} ventanas del ataque sin destino")}
    return {"cubre": True, "ventanas_ataque": len(atk), "motivo": ""}


# ------------------------------------------------------------------- atribución
def atribuir(destinos, eid, wend_utc, ep_destino):
    """Devuelve (incluir, atribucion, confirmada)."""
    if destinos is None:
        return True, "solo_origen_incompleta", False
    lst = destinos.get((eid, wend_utc))
    if lst is None:
        return True, "incompleta(sin_destino_en_evidencia)", False      # criterio previo (origen), sin confirmar
    if ep_destino in lst:
        return True, "origen+destino", True
    return False, "otro_destino(no_es_este_ataque)", False               # anomalía hacia otro destino -> no cuenta


# ------------------------------------------------------------------- clasificación por episodio
def clasificar(ep, regs_global, origen, u05, u03, destinos, integridad_apto=None):
    """integridad_apto: True/False/None. None = integridad DESCONOCIDA (no verificada) => NO evaluable."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    eid = f"{ep['escenario']}-r{ep['repeticion']}"
    kali = [r for r in regs_global if r["entity_ip"] == origen]
    cob = cobertura(ep, regs_global, kali)
    # Evidencia de destino VÁLIDA que CUBRE el intervalo: no basta con que exista el mapa; cada ventana de la Kali
    # durante el ataque (window_end en (inicio, fin]) debe tener entrada de destino, para poder confirmar O descartar
    # la atribución de cada una. Un mapa vacío o con claves ausentes NO cubre el intervalo.
    cov = _evidencia_destino_cubre(destinos, eid, kali, ini, fin)
    destino_cubre = cov["cubre"]
    evaluable = bool(cob["suficiente"] and destino_cubre and integridad_apto is True)
    res = {"evaluable": evaluable, "cobertura": cob, "estado_generador": ep["estado"],
           "evidencia_destino": cov, "integridad_apto": integridad_apto,
           "motivo_no_evaluable": None if evaluable else
           ("; ".join(x for x in [None if cob["suficiente"] else "cobertura:" + cob["motivo"],
                                  None if destino_cubre else "evidencia de destino " + cov["motivo"],
                                  None if integridad_apto is True else
                                  ("integridad desconocida" if integridad_apto is None else "integridad no apta")]
                      if x))}
    if fin is None:
        for c in CONFIGS:
            res[c] = {"categoria": "no_evaluable", "motivo": "sin fin de episodio"}
        res["senales_previas_o_ambiguas"] = []; res["senales_observadas_sin_confirmar"] = []
        return res
    lim = fin + HORIZONTE_S
    dentro = [r for r in kali if ini <= r["_logged"] <= lim]
    previas, observadas = [], []
    for c in CONFIGS:
        d_conf = d_obs = p_conf = p_obs = None
        for r in dentro:
            g = senales(r, u05, u03)
            if not g[c]:
                continue
            incluir, atrib, conf = atribuir(destinos, eid, r["window_end_utc"], ep.get("destino"))
            if not incluir:
                continue                                 # otro destino: no es este ataque
            w0, w1 = r["_wend"] - HORIZONTE_S, r["_wend"]
            solapa = w1 > ini and w0 < fin               # (window_end-60, window_end] ∩ [inicio, fin]
            rel = ("durante_actividad" if (solapa and r["_logged"] <= fin)
                   else "posterior" if (solapa and r["_logged"] > fin)
                   else "previa" if r["_wend"] <= ini else "ambigua")
            reg = {"configuracion": c, "window_end_utc": r["window_end_utc"], "logged_at_utc": iso(r["_logged"]),
                   "desde_inicio_generador_s": round(r["_logged"] - ini, 1),
                   "tras_fin_generador_s": round(r["_logged"] - fin, 1), "relacion_temporal": rel,
                   "atribucion": atrib, "atribucion_confirmada": conf, "base": g["base"][c],
                   "score": r.get("_score"), "score_estado": r.get("_score_estado"),
                   "detector_name": r.get("detector_name")}
            if rel in ("previa", "ambigua"):
                previas.append(reg)
            elif rel == "durante_actividad":
                if conf and d_conf is None:
                    d_conf = reg
                elif not conf:
                    d_obs = d_obs or reg; observadas.append(reg)
            else:  # posterior
                if conf and p_conf is None:
                    p_conf = reg
                elif not conf:
                    p_obs = p_obs or reg; observadas.append(reg)
        senal_observada = bool(d_conf or d_obs or p_conf or p_obs)
        deteccion_confirmada = bool(d_conf)
        if not evaluable:
            cat, reg = "no_evaluable", (d_conf or d_obs or p_conf or p_obs or {"motivo": res["motivo_no_evaluable"]})
        elif d_conf:
            cat, reg = "durante", d_conf
        elif d_obs or p_obs:
            cat, reg = "observada_sin_confirmar", (d_obs or p_obs)
        elif p_conf:
            cat, reg = "posterior", p_conf
        else:
            cat, reg = "sin_deteccion", {}
        res[c] = {"categoria": cat, "senal_observada": senal_observada,
                  "deteccion_confirmada": deteccion_confirmada,
                  "primera_fiable": bool(deteccion_confirmada and evaluable), **reg}
    res["senales_previas_o_ambiguas"] = previas
    res["senales_observadas_sin_confirmar"] = observadas
    # compartidas/exclusivas durante el ataque, SOLO sobre ventanas con atribución CONFIRMADA
    comp = {"ambos_0.05": 0, "solo_IF_0.05": 0, "solo_HEUR": 0, "ninguno_0.05": 0,
            "nota": "solo ventanas con atribución confirmada" if destino_cubre else
            "evidencia de destino no cubre el intervalo: no se computa (atribución no confirmable)"}
    if destino_cubre:
        for r in dentro:
            if not (r["_wend"] > ini and r["_wend"] - HORIZONTE_S < fin and r["_logged"] <= fin):
                continue
            inc, _, conf = atribuir(destinos, eid, r["window_end_utc"], ep.get("destino"))
            if not inc or not conf:
                continue
            g = senales(r, u05, u03)
            k = ("ambos_0.05" if g["IF_0.05"] and g["HEUR"] else "solo_IF_0.05" if g["IF_0.05"]
                 else "solo_HEUR" if g["HEUR"] else "ninguno_0.05")
            comp[k] += 1
    res["compartidas_durante_0.05"] = comp
    return res


# ------------------------------------------------------------------- control normal (FPR)
def fpr_control(regs, desde, hasta, u05, u03, excluidas):
    v = [r for r in regs if desde <= r["_logged"] <= hasta and r["entity_ip"] not in excluidas]
    n = len(v)
    out = {"ventanas": n, "denominador": n, "desde": iso(desde), "hasta": iso(hasta)}
    if n == 0:
        out["aviso"] = "sin ventanas en el control"; return out
    for c in CONFIGS:
        fa = sum(1 for r in v if senales(r, u05, u03)[c])
        out[c] = {"falsas_alarmas": fa, "tasa": round(fa / n, 6)}
    return out


# ------------------------------------------------------------------- métricas por ventana (solo con etiquetas)
def metricas_por_ventana(regs, etiquetas, u05, u03):
    pares = [(r, etiquetas[(r["entity_ip"], r["window_end_utc"])]) for r in regs
             if (r["entity_ip"], r["window_end_utc"]) in etiquetas]
    if not pares:
        return {"calculadas": False, "motivo": "ninguna ventana coincide con el fichero de etiquetas"}
    out = {"calculadas": True, "n_etiquetadas": len(pares), "denominador": len(pares)}
    for c in CONFIGS:
        tp = fp = tn = fn = 0
        for r, y in pares:
            p = 1 if senales(r, u05, u03)[c] else 0
            y = int(y)
            tp += p and y; fp += p and not y; tn += (not p) and (not y); fn += (not p) and y
        out[c] = {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
                  "precision": round(tp / (tp + fp), 6) if tp + fp else None,
                  "recall": round(tp / (tp + fn), 6) if tp + fn else None,
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
    ap.add_argument("--integridad", help="integridad.json de verificar_integridad.py; sin él, integridad DESCONOCIDA")
    ap.add_argument("--salida", default="analisis")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    u05, u03 = cfg["umbrales"]["0.05"], cfg["umbrales"]["0.03"]
    desplegado = cfg["umbrales"].get("desplegado_referencia")
    origen = cfg.get("origen") or "10.10.20.30"
    excluidas = set(cfg.get("combinacion_real", {}).get("exclusiones", {}).get("NUNCA_BLOQUEAR", []))

    eps, inc_m = leer_marcas(Path(a.marcas))
    regs, inc_r, dups = leer_motor(Path(a.motor))
    destinos = None
    if a.destinos:
        destinos = defaultdict(list)
        for row in csv.DictReader(open(a.destinos, encoding="utf-8")):
            destinos[(row["episodio_id"], row["window_end_utc"])].append(row["destino"])
        destinos = dict(destinos)
    # integridad por episodio: apto True/False; sin fichero o episodio ausente => None (DESCONOCIDA)
    integridad = {}
    if a.integridad:
        rep = json.load(open(a.integridad, encoding="utf-8"))
        for e in rep.get("episodios", []):
            integridad[e["episodio_id"]] = bool(e.get("apto"))

    por_ep, tabla = {}, {}
    for eid, ep in eps.items():
        c = clasificar(ep, regs, origen, u05, u03, destinos, integridad.get(eid))
        por_ep[eid] = c
        fam = familia(ep["escenario"])
        t = tabla.setdefault(fam, {"evaluables": [], "no_evaluables": [], **{cf: 0 for cf in CONFIGS}})
        if c["evaluable"]:
            t["evaluables"].append(eid)
            for cf in CONFIGS:
                if c[cf]["categoria"] == "durante":
                    t[cf] += 1
        else:
            t["no_evaluables"].append(eid)

    salida = {
        "fuentes": {"marcas": a.marcas, "motor": a.motor, "config": a.config},
        "umbrales": {"0.05_recalibrado": u05, "0.03_recalibrado": u03, "0.05_desplegado_en_vivo": desplegado},
        "nota_umbral": "el motor emitió en vivo con el umbral DESPLEGADO; IF_0.05/0.03 recalculados son derivados.",
        "clasificacion_por": "logged_at (emisión real) + solape de la ventana con el ataque; window_end ≠ emisión",
        "atribucion_destino": "con --destinos" if destinos is not None else "sin evidencia de destino (incompleta)",
        "integridad_fuentes": ("de " + a.integridad) if a.integridad else "DESCONOCIDA (no se pasó --integridad); "
                               "ningún episodio se declara evaluable sin verificación de integridad",
        "calidad_datos": {"incidencias_marcas": inc_m, "incidencias_motor": inc_r, "ventanas_duplicadas": len(dups),
                          "episodios_incompletos": [e for e, v in eps.items() if v["estado"] != "completo"]},
        "tabla8": tabla, "episodios": por_ep}
    salida["control_normal_fpr"] = (fpr_control(regs, *map(como_epoch, a.control.split(",")), u05, u03, excluidas)
                                    if a.control else {"calculado": False, "motivo": "no se pasó --control"})
    if a.etiquetas:
        et = {(r["entity_ip"], r["window_end_utc"]): r["etiqueta"]
              for r in csv.DictReader(open(a.etiquetas, encoding="utf-8"))}
        salida["metricas_por_ventana"] = metricas_por_ventana(regs, et, u05, u03)
    else:
        salida["metricas_por_ventana"] = {"calculadas": False, "motivo": "sin --etiquetas no se fabrican métricas"}

    sd = Path(a.salida); sd.mkdir(parents=True, exist_ok=True)
    (sd / "analisis.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    _tabla_md(sd / "TABLA8.md", tabla, salida)
    print(json.dumps({"tabla8": tabla, "calidad": salida["calidad_datos"]}, ensure_ascii=False, indent=1))
    return 0


def _tabla_md(path, tabla, salida):
    L = ["# Tabla 8 — campaña A (generada por analizar.py)", "",
         "Celda: episodios con **detección durante** / episodios **evaluables** (cobertura suficiente).",
         "Clasificación por `logged_at` y solape de la ventana con el ataque. Las configuraciones derivadas",
         "offline no son alertas emitidas en vivo (el motor usó el umbral desplegado).", "",
         "| Familia | Evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |",
         "|---|---|---|---|---|---|---|"]
    for fam, t in tabla.items():
        n = len(t["evaluables"])
        L.append(f"| {fam} | {n} | " + " | ".join(f"{t[c]}/{n}" if n else "—" for c in CONFIGS) + " |")
    noev = ", ".join(e for t in tabla.values() for e in t["no_evaluables"]) or "ninguno"
    L += ["", f"No evaluables: {noev}", "",
          "Métricas por ventana: " + ("calculadas" if salida["metricas_por_ventana"].get("calculadas")
                                       else "no calculadas (" + salida["metricas_por_ventana"]["motivo"] + ")")]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
