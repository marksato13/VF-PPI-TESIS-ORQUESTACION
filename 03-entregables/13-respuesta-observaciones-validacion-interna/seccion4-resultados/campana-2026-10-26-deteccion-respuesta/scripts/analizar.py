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
  - Siete configuraciones, en este orden: IF 0,05 · IF 0,03 · IF 0,01 · heurísticos · híbrido 0,05 · 0,03 · 0,01.
    Los tres α son tres cortes del MISMO score_samples por ventana; los heurísticos se calculan una vez.
  - Umbrales en escala score_samples, con precisión completa, leídos de la config (sin valores por defecto) y
    contrastados con la calibración de 4.1 cuando el fichero está accesible. Señal IF: score < umbral (estricto).
    Escala de anomalía equivalente: anomalia = -score, umbral_anomalia = -umbral, señal si anomalia > umbral_anomalia.
  - Las 7 configuraciones son CLASIFICACIONES COMPARATIVAS DERIVADAS de los registros (análisis de componentes y
    umbrales). Su tiempo (logged_at del registro usado) es la disponibilidad de esa evidencia, NO la latencia de
    emisión de la configuración. Ninguna se etiqueta como «emitida», ni siquiera IF_0.05: su umbral recalibrado
    (65 553) no es el desplegado (65 633) aunque ambas clasificaciones coincidan en una ventana.
  - Las EMISIONES OBSERVADAS (decisiones ALERT y señales heurísticas registradas en vivo) se listan aparte, con
    registro, emisor, decisión, logged_at/window_end, modelo/score/umbral REGISTRADOS y atribución; no son una octava
    configuración. El emisor y el umbral se toman del registro: si faltan o no identifican la configuración, se
    declaran «desconocido» (no se rellenan con el valor esperado ni se deduce una emisión de un score).
  - Un registro de decisión SIN la clave threshold se conserva (con incidencia archivo:línea) si tiene los campos
    para leerlo y ubicarlo (REQ_MOTOR). Su umbral registrado queda desconocido, distinguiendo clave ausente de null;
    no da latencia confirmada. Las clasificaciones comparativas usan sus propios umbrales de análisis.
  - Eventos 'ventana_no_evaluada' (motor corregido, producto 7b275b8; #59): registros de CALIDAD Y COBERTURA, aparte
    de las decisiones y de las emisiones observadas. No traen score, decisión ni etiqueta: no son TP/FP/TN/FN, ni
    PERMIT, ni alerta. Se conservan con motivo (pcap_incompleto, ventana_no_regenerada o cualquier otro, marcado no
    reconocido), campos de disponibilidad y respaldo (archivo, sha256, línea). Se relacionan con el episodio por el
    INTERVALO de la ventana (window_end-60, window_end], no por el instante de escritura (que puede ser ~170 s
    posterior): ventana del ataque (window_end en (inicio, fin]) -> el ancla falta y el episodio no es evaluable, igual
    que antes de #59 (el motivo ahora separa «registrada como no evaluada» de «sin registro»); ventana que solapa el
    final (window_end en (fin, fin+60)) -> solo deja incompleta la relación «posterior»; fuera -> sin efecto. Sin score
    el IF no es evaluable en esa ventana para ningún α; el heurístico queda desconocido; el híbrido solo prueba
    detección con un positivo confirmado. Una detección confirmada se mantiene visible; la ausencia no se afirma.
    En el control y las métricas por ventana se informan aparte (cobertura = evaluadas / (evaluadas + no evaluadas));
    las tasas son sobre ventanas evaluadas. Duplicados: se cuentan una vez. Conflicto con una decisión de la misma
    clave: prevalece la decisión y el evento queda en 'conflictos'. Nada se descarta en silencio.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PASO_S = 10
HORIZONTE_S = 60                      # horizonte de la característica más larga
TOL_CONTINUIDAD_S = 2 * PASO_S        # hueco máximo tolerado en el registro del motor
ALFAS = ("0.05", "0.03", "0.01")      # orden de salida; claves de config["umbrales"]
CONFIGS = ("IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01")
ALFAS_COMPARTIDAS = ("0.05", "0.01")  # solapamiento IF/heurísticos: el existente (0,05) + el añadido (0,01)
CLAVE_CALIBRACION = {"0.05": "0.050", "0.03": "0.030", "0.01": "0.010"}
REQ_MOTOR = ("logged_at", "entity_ip", "window_end_utc", "decision", "packet_count_10s")  # leer y ubicar en el tiempo
CLAVE_UMBRAL = "threshold"            # umbral REGISTRADO: si falta, el registro se conserva como evidencia incompleta
UMBRAL_DESCONOCIDO = {"clave_ausente": "desconocido (el registro no contiene la clave threshold)",
                      "null": "desconocido (threshold registrado como null)",
                      "no_numerico": "desconocido (threshold registrado no numérico)"}
AUTH_DETECTOR = "auth_failure_heuristic"
EVENTO_NO_EVALUADA = "ventana_no_evaluada"
REQ_NO_EVALUADA = ("logged_at", "entity_ip", "window_end_utc")   # ubicar la ventana y el instante de escritura
CAMPOS_DISPONIBILIDAD = ("pendiente_desde", "inicio_ciclo", "marca_pcap", "marca_eve", "pcaps_ilegibles")
MOTIVOS_NO_EVALUADA = {  # producto scripts/engine/motor_decision.py, main(), bloque de pendientes (commit 7b275b8)
    "pcap_incompleto": "los PCAP cerrados no cubrían la ventana al vencer la espera",
    "ventana_no_regenerada": "los PCAP la cubrían, pero build_rows ya no generaba la ventana (historia podada)"}


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
        r["_ln"] = ln                                                    # referencia al registro de respaldo
        try:
            r["_logged"] = float(r["logged_at"]); r["_wend"] = ep_iso(r["window_end_utc"])
            r["_pk10"] = float(r["packet_count_10s"])
        except (ValueError, TypeError) as ex:
            inc.append(f"motor:{ln}: valor inválido ({ex})"); continue
        if estado_umbral_registrado(r) == "clave_ausente":               # no se sustituye por ningún umbral
            r["_incidencias"] = [f"falta la clave '{CLAVE_UMBRAL}'"]
            inc.append(f"motor:{ln} ({path}): falta la clave '{CLAVE_UMBRAL}'; registro conservado, umbral "
                       "registrado desconocido")
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


def leer_no_evaluadas(path: Path, decisiones: list, ref_motor: dict) -> dict:
    """Eventos 'ventana_no_evaluada' como registros de calidad/cobertura (no son decisiones). No se inventa score,
    decisión, etiqueta ni señal. Devuelve {'vigentes': [...], 'registros', 'incidencias', 'duplicados', 'conflictos'}:
    'vigentes' son los que se cuentan (uno por clave entity_ip|window_end, sin decisión para esa clave)."""
    evs, inc = [], []
    for ln, linea in enumerate(open(path, encoding="utf-8"), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            r = json.loads(linea)
        except json.JSONDecodeError:
            continue                                                     # ya consta en las incidencias del motor
        if not isinstance(r, dict) or r.get("event") != EVENTO_NO_EVALUADA:
            continue
        falta = [k for k in REQ_NO_EVALUADA if r.get(k) is None]
        if falta:
            inc.append(f"motor:{ln}: {EVENTO_NO_EVALUADA}: faltan claves {falta}; no se puede ubicar la ventana "
                       "(no se cuenta; queda solo esta incidencia)"); continue
        try:
            logged, wend = float(r["logged_at"]), ep_iso(r["window_end_utc"])
            if not math.isfinite(logged):
                raise ValueError(f"logged_at no finito {r['logged_at']!r}")
        except (ValueError, TypeError) as ex:
            inc.append(f"motor:{ln}: {EVENTO_NO_EVALUADA}: valor inválido ({ex}); no se cuenta"); continue
        diag = []
        mot = r.get("motivo")
        if mot is None:
            est = "ausente"; diag.append("motivo ausente")
        elif isinstance(mot, str) and mot in MOTIVOS_NO_EVALUADA:
            est = "reconocido"
        else:
            est = "no_reconocido"; diag.append(f"motivo no reconocido {mot!r} (se conserva tal cual)")
        disp = {k: r[k] for k in CAMPOS_DISPONIBILIDAD if k in r}
        diag += [f"{k} no numérico ({v!r})" for k, v in disp.items() if not _numero(v)]
        pend = disp.get("pendiente_desde")
        mp = disp.get("marca_pcap")
        e = {"registro_id": f"motor:{ln}", "evento": EVENTO_NO_EVALUADA, "entity_ip": r["entity_ip"],
             "window_end_utc": r["window_end_utc"],
             "intervalo_ventana_utc": [iso(wend - HORIZONTE_S), iso(wend)],
             "logged_at": r["logged_at"], "logged_at_utc": iso(logged),
             "escrito_tras_window_end_s": round(logged - wend, 1),
             "motivo": mot if mot is not None else "desconocido (motivo ausente)", "motivo_estado": est,
             "motivo_significado": MOTIVOS_NO_EVALUADA.get(mot) if est == "reconocido" else None,
             "disponibilidad": disp,
             "campos_disponibilidad_ausentes": [k for k in CAMPOS_DISPONIBILIDAD if k not in r],
             "espera_desde_pendiente_s": round(logged - pend, 1) if _numero(pend) else None,
             "marca_pcap_menos_window_end_s": round(mp - wend, 1) if _numero(mp) else None,
             "diagnosticos": diag,
             "respaldo": {**ref_motor, "linea": ln},
             "_logged": logged, "_wend": wend, "_clave": (r["entity_ip"], r["window_end_utc"])}
        if diag:
            inc.append(f"motor:{ln}: {EVENTO_NO_EVALUADA}: " + "; ".join(diag) + " (registro conservado)")
        evs.append(e)
    dec = {(r["entity_ip"], r["window_end_utc"]): f"motor:{r['_ln']}" for r in decisiones}
    grupos = defaultdict(list)
    for e in evs:
        grupos[e["_clave"]].append(e)
    vigentes, duplicados, conflictos = [], [], []
    for k, lst in grupos.items():
        ids = [e["registro_id"] for e in lst]
        if len(lst) > 1:
            duplicados.append({"clave": f"{k[0]}|{k[1]}", "registros": ids,
                               "motivos": [e["motivo"] for e in lst],
                               "regla": "la ventana se cuenta UNA vez (primer registro); todos se conservan"})
            inc.append(f"{EVENTO_NO_EVALUADA} duplicada {k[0]}|{k[1]}: {', '.join(ids)} — se cuenta una vez")
        if k in dec:
            conflictos.append({"clave": f"{k[0]}|{k[1]}", "registro_decision": dec[k], "registros_no_evaluada": ids,
                               "regla": "prevalece la decisión registrada para clasificar; el evento se conserva "
                                        "aquí y NO se cuenta como ventana no evaluada"})
            inc.append(f"conflicto {k[0]}|{k[1]}: decisión {dec[k]} y {EVENTO_NO_EVALUADA} {', '.join(ids)} — "
                       "prevalece la decisión")
            estado = "conflicto_con_decision"
        else:
            vigentes.append(lst[0]); estado = "contada"
        for i, e in enumerate(lst):
            e["estado_en_analisis"] = estado if (i == 0 or estado != "contada") else "duplicado_no_contado"
    vigentes.sort(key=lambda e: e["_logged"])
    return {"vigentes": vigentes, "registros": evs, "incidencias": inc, "duplicados": duplicados,
            "conflictos": conflictos}


def publico(e: dict) -> dict:
    """Registro sin las claves internas (_logged, _wend, _clave)."""
    return {k: v for k, v in e.items() if not k.startswith("_")}


# ------------------------------------------------------------------- umbrales
def umbrales_de(cfg: dict) -> dict:
    """Umbrales por α en escala score_samples, tal cual (float de precisión completa). Sin valores por defecto:
    un α ausente, de texto o no finito aborta (no se clasifica con un valor redondeado ni inventado)."""
    um = cfg.get("umbrales", {})
    U = {}
    for a in ALFAS:
        v = um.get(a)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise SystemExit(f"config: umbrales['{a}'] ausente o no numérico ({v!r}); no se usa valor por defecto")
        U[a] = float(v)
    return U


def orden_umbrales(U: dict) -> bool:
    """Con score < u estricto, IF_0.01 ⊆ IF_0.03 ⊆ IF_0.05 solo si u_0.01 <= u_0.03 <= u_0.05."""
    return U["0.01"] <= U["0.03"] <= U["0.05"]


def umbral_escala_anomalia(u: float) -> float:
    """anomalia = -score_samples  =>  umbral_anomalia = -u; score < u  <=>  anomalia > -u (la negación es exacta).
    Se transforma el umbral canónico; NO se recalcula un cuantil sobre la escala de anomalía (puede diferir 1 ULP)."""
    return -u


def verificar_procedencia(cfg: dict, cfg_path: Path, U: dict) -> dict:
    """Contrasta los umbrales con el fichero de calibración de 4.1 si está accesible. Discrepancia => aborta."""
    f = cfg.get("umbrales", {}).get("fuente") or {}
    if not f.get("archivo"):
        return {"estado": "no_verificada", "motivo": "la config no declara umbrales.fuente"}
    p = (cfg_path.parent / f["archivo"]).resolve()
    if not p.is_file():
        return {"estado": "no_verificada", "motivo": f"fuente no accesible aquí: {f['archivo']}"}
    datos = p.read_bytes()
    sha_lf = hashlib.sha256(datos.replace(b"\r\n", b"\n")).hexdigest()
    col = json.loads(datos.decode("utf-8"))["umbrales_full_precision"][f["columna"]]
    distintos = {a: (U[a], col.get(CLAVE_CALIBRACION[a])) for a in ALFAS
                 if col.get(CLAVE_CALIBRACION[a]) is None or float(col[CLAVE_CALIBRACION[a]]) != U[a]}
    if distintos:
        raise SystemExit(f"umbrales de la config != calibración {f['archivo']} [{f['columna']}]: {distintos}")
    return {"estado": "verificada", "archivo": f["archivo"], "columna": f["columna"], "sha256_lf": sha_lf,
            "sha256_coincide_con_config": sha_lf == f.get("sha256_lf"),
            "comparacion": "igualdad exacta de float (sin redondeo) para " + ", ".join(ALFAS)}


# ------------------------------------------------------------------- señales por ventana
# Procedencia de las configuraciones comparativas: TODAS derivadas de los registros (ninguna es una emisión).
# Antes de 2026-10-28.2: IF_0.05 = "emitido_por_modelo_desplegado" si el registro era ALERT (incorrecto: el umbral
# recalibrado no es el desplegado); HEUR = "emitido_ALERT(auth_heredada)" / "registrada_en_vivo" (eso es evidencia
# observada de la ventana, que ahora va en 'evidencia_registrada', no en la base de la configuración).
BASE_DERIVADA = {
    "IF_0.05": "derivado(umbral_recalibrado_0.05; distinto del desplegado)",
    "IF_0.03": "derivado(umbral_no_desplegado)",
    "IF_0.01": "derivado(umbral_no_desplegado)",
    "HEUR": "derivado(componente_heuristico_registrado)",
    "HIB_0.05": "derivado(IF_0.05 OR HEUR)", "HIB_0.03": "derivado(IF_0.03 OR HEUR)",
    "HIB_0.01": "derivado(IF_0.01 OR HEUR)"}
TIEMPO_DERIVADO = "disponibilidad_del_registro(logged_at); no es latencia de emision de esta configuracion"


def senales(r: dict, U: dict) -> dict:
    """Clasificación comparativa por componente (derivada), con score null a salvo.
    U = {α: umbral score_samples}. Los tres α cortan la MISMA puntuación; HEUR no depende de α (se calcula una vez).
    'evidencia_registrada' describe lo que el registro muestra (decisión, detector, heurístico) sin convertirlo en
    procedencia de la configuración."""
    sc, pk = r.get("_score"), r.get("_pk10", 0)
    if_valida = (sc is not None) and (pk > 0)
    ifs = {a: bool(if_valida and sc < U[a]) for a in ALFAS}             # estricto: score == umbral NO es señal
    heur_field = r.get("heuristico") is not None
    det = r.get("decision") == "ALERT"
    auth_alert = det and r.get("detector_name") == AUTH_DETECTOR         # regla heredada registrada con ALERT
    heur_sig = bool(heur_field or auth_alert)                            # componente 'heurísticos' (sin duplicar)
    g = {**{f"IF_{a}": ifs[a] for a in ALFAS}, "HEUR": heur_sig,
         **{f"HIB_{a}": bool(ifs[a] or heur_sig) for a in ALFAS},
         "if_valida": if_valida, "heuristico_registrado_en_vivo": heur_field}
    g["base"] = dict(BASE_DERIVADA)
    g["evidencia_registrada"] = {
        "decision_registrada": r.get("decision"), "detector_name_registrado": r.get("detector_name"),
        "heuristico_registrado": (r.get("heuristico") or {}).get("heuristico") if heur_field else None,
        "alerta_auth_heredada_registrada": auth_alert}
    return g


# ------------------------------------------------------------------- cobertura temporal
def cobertura(ep: dict, regs_global: list, regs_kali: list, no_eval_kali=()) -> dict:
    """¿El motor registró de forma continua [inicio, fin+60] y hay ventanas de la Kali en todas las anclas del ataque?
    no_eval_kali: eventos ventana_no_evaluada vigentes de la Kali. NO cuentan como ancla observada (no hay decisión);
    solo separan, en el motivo, las anclas registradas como no evaluadas de las que no tienen ningún registro. Sin
    eventos la salida es idéntica a la anterior a #59. La continuidad del motor se sigue midiendo con decisiones."""
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
    ne = {int(round(e["_wend"])): e for e in no_eval_kali if ini < e["_wend"] <= fin}
    ne_faltan = [a for a in faltan if a in ne]
    if ne_faltan:
        motivos = sorted({str(ne[a]["motivo"]) for a in ne_faltan})
        txt_faltan = (f"faltan {len(faltan)} de {len(esperadas)} anclas de la Kali durante el ataque: "
                      f"{len(ne_faltan)} registradas como {EVENTO_NO_EVALUADA} ({', '.join(motivos)}) y "
                      f"{len(faltan) - len(ne_faltan)} sin registro (pérdida de datos)")
    else:
        txt_faltan = f"faltan {len(faltan)} de {len(esperadas)} anclas de la Kali durante el ataque (pérdida de datos)"
    mot = "ok" if suf else (
        "motor no continuo (hueco o no cubre el intervalo)" if not motor_continuo else txt_faltan)
    out = {"suficiente": suf, "motivo": mot, "motor_continuo": motor_continuo,
           "anclas_ataque_esperadas": len(esperadas), "anclas_ataque_observadas": len(esperadas) - len(faltan),
           "hueco_motor_max_s": round(hueco, 1), "cubre_inicio": cubre_ini, "cubre_fin_mas_60": cubre_fin}
    if ne_faltan:                                    # solo con eventos: sin ellos la salida no cambia
        out["anclas_no_evaluadas"] = len(ne_faltan)
        out["anclas_sin_registro"] = len(faltan) - len(ne_faltan)
    return out


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
def clasificar(ep, regs_global, origen, U, destinos, integridad_apto=None, no_eval=()):
    """integridad_apto: True/False/None. None = integridad DESCONOCIDA (no verificada) => NO evaluable.
    U = {α: umbral score_samples} (ver umbrales_de). no_eval: eventos ventana_no_evaluada vigentes (leer_no_evaluadas)."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    eid = f"{ep['escenario']}-r{ep['repeticion']}"
    kali = [r for r in regs_global if r["entity_ip"] == origen]
    ne_kali = [e for e in no_eval if e["entity_ip"] == origen]
    cob = cobertura(ep, regs_global, kali, ne_kali)
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
        res["ventanas_no_evaluadas"] = efecto_no_evaluadas(ep, res, ne_kali)
        return res
    lim = fin + HORIZONTE_S
    dentro = [r for r in kali if ini <= r["_logged"] <= lim]
    previas, observadas = [], []
    for c in CONFIGS:
        d_conf = d_obs = p_conf = p_obs = None
        for r in dentro:
            g = senales(r, U)
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
                   "detector_name": r.get("detector_name"),
                   # clasificación derivada: logged_at = cuándo quedó registrada la evidencia usada; la latencia
                   # real de emisión solo se mide con 'emisiones_observadas' (antes: tiempo_es_emision_real)
                   "tiempo_significado": TIEMPO_DERIVADO,
                   "evidencia_registrada": g["evidencia_registrada"]}
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
    for a in ALFAS_COMPARTIDAS:
        comp = {f"ambos_{a}": 0, f"solo_IF_{a}": 0, "solo_HEUR": 0, f"ninguno_{a}": 0,
                "nota": "solo ventanas con atribución confirmada" if destino_cubre else
                "evidencia de destino no cubre el intervalo: no se computa (atribución no confirmable)"}
        if destino_cubre:
            for r in dentro:
                if not (r["_wend"] > ini and r["_wend"] - HORIZONTE_S < fin and r["_logged"] <= fin):
                    continue
                inc, _, conf = atribuir(destinos, eid, r["window_end_utc"], ep.get("destino"))
                if not inc or not conf:
                    continue
                g = senales(r, U)
                k = (f"ambos_{a}" if g[f"IF_{a}"] and g["HEUR"] else f"solo_IF_{a}" if g[f"IF_{a}"]
                     else "solo_HEUR" if g["HEUR"] else f"ninguno_{a}")
                comp[k] += 1
        res[f"compartidas_durante_{a}"] = comp
    res["ventanas_no_evaluadas"] = efecto_no_evaluadas(ep, res, ne_kali)
    return res


def relacion_no_evaluada(e: dict, ini: float, fin) -> str | None:
    """Relación por el INTERVALO de la ventana (window_end-60, window_end], no por el instante de escritura."""
    if fin is None:
        return None
    w1 = e["_wend"]
    if not (w1 > ini and w1 - HORIZONTE_S < fin):
        return None                                   # no solapa el ataque: sin efecto en este episodio
    return "ventana_del_ataque" if w1 <= fin else "ventana_posterior_solapa"


EFECTO_COMPONENTE = {
    "IF": "sin score en esas ventanas: la clasificación IF no es evaluable en ellas para ningún α (0,05/0,03/0,01)",
    "HEUR": "el evento no registra el heurístico y no hay decisión para esa clave (los conflictos se resuelven "
            "aparte): no se sabe si disparó; no se supone que no",
    "HIB": "IF sin score y heurístico desconocido en esas ventanas: solo un positivo confirmado probaría detección"}


def efecto_no_evaluadas(ep: dict, res: dict, ne_kali: list) -> dict:
    """Efecto de las ventanas no evaluadas de la Kali sobre este episodio, por configuración. No toca la Tabla 8: la
    evaluabilidad ya la decide cobertura() (un ancla del ataque sin decisión falta, con o sin evento)."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    det = []
    for e in ne_kali:
        rel = relacion_no_evaluada(e, ini, fin)
        if rel is None:
            continue
        det.append({"registro_id": e["registro_id"], "window_end_utc": e["window_end_utc"],
                    "intervalo_ventana_utc": e["intervalo_ventana_utc"], "logged_at_utc": e["logged_at_utc"],
                    "motivo": e["motivo"], "relacion_ventana": rel,
                    "escrito": "durante_actividad" if e["_logged"] <= fin else "tras_fin",
                    "escrito_tras_fin_s": round(e["_logged"] - fin, 1)})
    ataque = [d for d in det if d["relacion_ventana"] == "ventana_del_ataque"]
    post = [d for d in det if d["relacion_ventana"] == "ventana_posterior_solapa"]
    out = {"n": len(det), "ventanas_del_ataque": len(ataque), "ventanas_posteriores_que_solapan": len(post),
           "detalle": det}
    if not det:
        out["efecto"] = "ninguno"
        return out
    out["efecto_en_evaluabilidad"] = (
        f"{len(ataque)} ancla(s) del ataque sin decisión constan como {EVENTO_NO_EVALUADA}: la cobertura es "
        "insuficiente y el episodio no es evaluable (antes de #59 esas anclas ya faltaban como pérdida de datos; "
        "la Tabla 8 no cambia, cambia el motivo)" if ataque else
        "ninguno sobre la evaluabilidad (la cobertura exige anclas en (inicio, fin]); solo deja incompleta la "
        "relación 'posterior', que no entra en la Tabla 8")
    por_conf = {}
    for c in CONFIGS:
        conf = bool(isinstance(res.get(c), dict) and res[c].get("deteccion_confirmada"))
        comp = "HIB" if c.startswith("HIB") else "IF" if c.startswith("IF") else "HEUR"
        if conf:
            por_conf[c] = {"estado": "deteccion_confirmada_visible", "ausencia_establecible": None,
                           "motivo": "detección confirmada durante el ataque en una ventana con decisión registrada; "
                                     "las ventanas no evaluadas no la anulan"}
        elif ataque:
            por_conf[c] = {"estado": "ausencia_no_establecible", "ausencia_establecible": False,
                           "motivo": EFECTO_COMPONENTE[comp]}
        else:
            por_conf[c] = {"estado": "posterior_incompleta", "ausencia_establecible": True,
                           "motivo": "las ventanas afectadas cierran después del fin: no pueden dar detección "
                                     "durante (logged_at > fin); solo la relación posterior queda incompleta"}
    out["por_configuracion"] = por_conf
    out["nota"] = ("ausencia_establecible se refiere solo a estas ventanas no evaluadas; si el episodio entra en la "
                   "comparación lo decide 'evaluable' (cobertura, destino e integridad)")
    return out


# ------------------------------------------------------------------- emisiones observadas (no son una configuración)
def _numero(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def emisor_de(r: dict, detector_modelo) -> tuple:
    """Componente emisor según el REGISTRO (detector_name), no según el score. Devuelve (componente, motivo)."""
    dn = r.get("detector_name")
    if r.get("decision") == "ALERT":
        if dn == AUTH_DETECTOR:
            return "heuristico_auth_heredado", None
        if detector_modelo and dn == detector_modelo:
            return "IF_desplegado", None
        return "desconocido", ("ALERT sin detector_name registrado" if not dn else
                               f"detector_name {dn!r} no identifica el IF desplegado esperado ({detector_modelo!r})")
    return "heuristico:" + str((r.get("heuristico") or {}).get("heuristico") or "sin_nombre"), None


def estado_umbral_registrado(r: dict) -> str:
    """Distingue clave ausente, null y no numérico; los tres dejan el umbral registrado desconocido."""
    if CLAVE_UMBRAL not in r:
        return "clave_ausente"
    thr = r[CLAVE_UMBRAL]
    return "null" if thr is None else "numerico" if _numero(thr) else "no_numerico"


def configuracion_emisora(r: dict, componente: str, desplegado) -> dict:
    """Configuración realmente usada, solo con lo REGISTRADO. Si falta o no cuadra: desconocida (no se rellena)."""
    est = estado_umbral_registrado(r)
    umbral = r[CLAVE_UMBRAL] if est == "numerico" else None
    out = {"umbral_registrado": umbral if umbral is not None else UMBRAL_DESCONOCIDO[est],
           "umbral_registrado_estado": est}
    if componente == "IF_desplegado":
        if umbral is None:
            out.update(estado="desconocida", motivo="el registro no trae un umbral numérico (" + est + ")")
        elif not _numero(desplegado):
            out.update(estado="desconocida", motivo="la config no declara umbrales.desplegado_referencia")
        elif umbral == desplegado:
            out.update(estado="confirmada", configuracion="IF desplegado (umbral registrado == desplegado_referencia)")
        else:
            out.update(estado="desconocida",
                       motivo=f"umbral registrado {umbral!r} != desplegado_referencia {desplegado!r}")
        sc = r.get("_score")
        out["coherencia_score_umbral"] = (None if (sc is None or umbral is None) else
                                          "coherente(score<umbral)" if sc < umbral else
                                          "incoherente(ALERT con score>=umbral registrado)")
    elif componente.startswith("heuristico"):
        out.update(estado="identificada", configuracion=componente + " (no usa umbral del IF)")
    else:
        out.update(estado="desconocida", motivo="emisor no identificado en el registro")
    return out


def _relacion_episodio(r: dict, eps: dict, origen: str, destinos) -> dict:
    """Relación de un evento real con los episodios: mismos criterios temporales y de atribución que clasificar()."""
    nada = {"episodio_id": None, "relacion_temporal": "fuera_de_episodio", "atribucion": None,
            "atribucion_confirmada": False}
    if r["entity_ip"] != origen:
        return {**nada, "relacion_temporal": "fuera_de_episodio(otra_entidad)"}
    for clave, ep in eps.items():
        ini, fin = ep["inicio_ep"], ep["fin_ep"]
        if fin is None or not (ini <= r["_logged"] <= fin + HORIZONTE_S):
            continue
        eid = f"{ep['escenario']}-r{ep['repeticion']}"
        incluir, atrib, conf = atribuir(destinos, eid, r["window_end_utc"], ep.get("destino"))
        w0, w1 = r["_wend"] - HORIZONTE_S, r["_wend"]
        solapa = w1 > ini and w0 < fin
        rel = ("durante_actividad" if (solapa and r["_logged"] <= fin)
               else "posterior" if (solapa and r["_logged"] > fin)
               else "previa" if r["_wend"] <= ini else "ambigua")
        return {"episodio_id": clave, "relacion_temporal": rel, "atribucion": atrib,
                "atribucion_confirmada": bool(incluir and conf),
                "desde_inicio_generador_s": round(r["_logged"] - ini, 1),
                "tras_fin_generador_s": round(r["_logged"] - fin, 1)}
    return nada


def emisiones_observadas(regs, eps, origen, destinos, desplegado, detector_modelo, ref_motor) -> list:
    """Eventos REALES del registro: decisiones ALERT y señales heurísticas registradas en vivo. Un score que cruza un
    umbral sin ALERT ni heurístico registrado NO es una emisión y no aparece aquí."""
    out = []
    for r in regs:
        alerta = r.get("decision") == "ALERT"
        heur = r.get("heuristico") is not None
        if not (alerta or heur):
            continue
        comp, motivo = emisor_de(r, detector_modelo)
        h = r.get("heuristico") or {}
        out.append({
            "registro_id": r.get("decision_id") or r.get("id") or f"motor:{r['_ln']}",
            "tipo": "alerta_emitida" if alerta else "senal_heuristica_registrada(sin_ALERT)",
            "componente_emisor": comp, **({"motivo_emisor_desconocido": motivo} if motivo else {}),
            "decision_emitida": r.get("decision"),
            "accion_heuristica_registrada": h.get("accion") if heur else None,
            "logged_at_utc": iso(r["_logged"]), "window_end_utc": r["window_end_utc"],
            "entity_ip": r["entity_ip"],
            "modelo_registrado": r.get("detector_name") or "desconocido (no registrado)",
            "score_registrado": r.get("_score"), "score_estado": r.get("_score_estado"),
            "configuracion_emisora": configuracion_emisora(r, comp, desplegado),
            **_relacion_episodio(r, eps, origen, destinos),
            **({"incidencias_registro": r["_incidencias"]} if r.get("_incidencias") else {}),
            "respaldo": {**ref_motor, "linea": r["_ln"]}})
    return out


def resumen_emisiones_episodio(lst: list) -> dict:
    """Por episodio: la latencia REAL solo sale de una alerta del IF desplegado confirmada, durante y atribuida."""
    ok = [e for e in lst if e["tipo"] == "alerta_emitida" and e["componente_emisor"] == "IF_desplegado"
          and e["configuracion_emisora"]["estado"] == "confirmada"
          and e["relacion_temporal"] == "durante_actividad" and e["atribucion_confirmada"]]
    p = ok[0] if ok else None
    return {"nota": "eventos reales del registro; no son una configuración de la Tabla 8",
            "registros": [e["registro_id"] for e in lst],
            "primera_alerta_IF_desplegado_confirmada_durante": (
                {k: p[k] for k in ("registro_id", "logged_at_utc", "window_end_utc", "desde_inicio_generador_s")}
                if p else None),
            "eventos_con_emisor_o_configuracion_desconocida": sum(
                1 for e in lst if e["configuracion_emisora"]["estado"] == "desconocida")}


# ------------------------------------------------------------------- control normal (FPR)
DENOMINADOR_EVALUADAS = ("ventanas con decisión registrada (evaluadas); las ventanas no evaluadas no son TN, FP ni "
                         "FN y una decisión ausente no es PERMIT: las tasas se leen junto a la cobertura")


def fpr_control(regs, desde, hasta, U, excluidas, no_eval=()):
    v = [r for r in regs if desde <= r["_logged"] <= hasta and r["entity_ip"] not in excluidas]
    n = len(v)
    out = {"ventanas": n, "denominador": n, "desde": iso(desde), "hasta": iso(hasta)}
    # no evaluadas: por el intervalo de la ventana (window_end en el control), no por el instante de escritura
    ne = [e for e in no_eval if desde <= e["_wend"] <= hasta and e["entity_ip"] not in excluidas]
    out["ventanas_no_evaluadas"] = len(ne)
    out["ventanas_no_evaluadas_por_motivo"] = {m: sum(1 for e in ne if str(e["motivo"]) == m)
                                               for m in sorted({str(e["motivo"]) for e in ne})}
    out["ventanas_no_evaluadas_criterio"] = ("window_end en [desde, hasta] (las decisiones se seleccionan por "
                                             "logged_at); excluidas las entidades NUNCA_BLOQUEAR")
    out["cobertura_evaluada"] = round(n / (n + len(ne)), 6) if n + len(ne) else None
    out["denominador_significado"] = DENOMINADOR_EVALUADAS
    if n == 0:
        out["aviso"] = "sin ventanas en el control"; return out
    for c in CONFIGS:
        fa = sum(1 for r in v if senales(r, U)[c])
        out[c] = {"falsas_alarmas": fa, "tasa": round(fa / n, 6)}
    return out


# ------------------------------------------------------------------- métricas por ventana (solo con etiquetas)
def metricas_por_ventana(regs, etiquetas, U, no_eval=()):
    pares = [(r, etiquetas[(r["entity_ip"], r["window_end_utc"])]) for r in regs
             if (r["entity_ip"], r["window_end_utc"]) in etiquetas]
    ne = {e["_clave"] for e in no_eval} & set(etiquetas)
    cob = {"etiquetadas_no_evaluadas": len(ne),
           "etiquetadas_sin_registro": len(set(etiquetas) - ne - {(r["entity_ip"], r["window_end_utc"]) for r, _ in pares}),
           "cobertura_etiquetadas": round(len(pares) / (len(pares) + len(ne)), 6) if pares or ne else None,
           "denominador_significado": "etiquetadas con decisión registrada (evaluadas); las etiquetadas no evaluadas "
                                      "no son TP, FP, TN ni FN: las métricas se leen junto a cobertura_etiquetadas"}
    if not pares:
        return {"calculadas": False, "motivo": "ninguna ventana coincide con el fichero de etiquetas", **cob}
    out = {"calculadas": True, "n_etiquetadas": len(pares), "denominador": len(pares), **cob}
    for c in CONFIGS:
        tp = fp = tn = fn = 0
        for r, y in pares:
            p = 1 if senales(r, U)[c] else 0
            y = int(y)
            tp += p and y; fp += p and not y; tn += (not p) and (not y); fn += (not p) and y
        out[c] = {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
                  "precision": round(tp / (tp + fp), 6) if tp + fp else None,
                  "recall": round(tp / (tp + fn), 6) if tp + fn else None,
                  "FPR": round(fp / (fp + tn), 6) if fp + tn else None}
    return out


# ------------------------------------------------------------------- bloque de ventanas no evaluadas (salida)
def bloque_no_evaluadas(ne: dict, eps: dict, por_ep: dict, origen: str) -> dict:
    regs = []
    for e in ne["registros"]:
        rel = []
        if e["entity_ip"] == origen:
            for eid, ep in eps.items():
                r = relacion_no_evaluada(e, ep["inicio_ep"], ep["fin_ep"])
                if r:
                    rel.append({"episodio_id": eid, "relacion_ventana": r})
        regs.append({**publico(e), "relacion_episodios": rel or (
            "otra_entidad (solo control/métricas)" if e["entity_ip"] != origen else "fuera_de_episodio")})
    vig = ne["vigentes"]
    det_fuera = []
    for eid, c in por_ep.items():
        v = c.get("ventanas_no_evaluadas") or {}
        confs = [cf for cf in CONFIGS if isinstance(c.get(cf), dict) and c[cf].get("deteccion_confirmada")]
        if v.get("ventanas_del_ataque") and not c["evaluable"] and confs:
            det_fuera.append({"episodio_id": eid, "configuraciones_con_deteccion_confirmada": confs,
                              "motivo_no_evaluable": c["motivo_no_evaluable"]})
    return {
        "definicion": "eventos ventana_no_evaluada del motor: calidad y cobertura, no decisiones. Sin score, decisión "
                      "ni etiqueta; no son TP/FP/TN/FN, ni PERMIT, ni alerta, ni emisión observada",
        "fuente": "mismo --motor que las decisiones (respaldo con archivo, sha256 y línea por registro)",
        "contadas": len(vig),
        "por_motivo": {m: sum(1 for e in vig if str(e["motivo"]) == m) for m in sorted({str(e["motivo"]) for e in vig})},
        "motivos_reconocidos": MOTIVOS_NO_EVALUADA,
        "registros": regs, "incidencias": ne["incidencias"],
        "duplicados": ne["duplicados"], "conflictos": ne["conflictos"],
        "reglas": {"duplicado": "misma clave entity_ip|window_end: se cuenta una vez (primer registro)",
                   "conflicto": "decisión y no evaluada en la misma clave: prevalece la decisión; el evento no se cuenta",
                   "relacion": "por el intervalo (window_end-60, window_end] frente a [inicio, fin]; logged_at se "
                               "informa aparte (instante de escritura)",
                   "tabla8": "no se añade columna ni se cambia el denominador: un ancla del ataque sin decisión ya "
                             "dejaba el episodio no evaluable; ahora el motivo distingue el registro"},
        "detecciones_confirmadas_en_episodios_no_evaluables": det_fuera}


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
    U = umbrales_de(cfg)
    procedencia = verificar_procedencia(cfg, Path(a.config), U)
    orden_ok = orden_umbrales(U)
    desplegado = cfg["umbrales"].get("desplegado_referencia")
    origen = cfg.get("origen") or "10.10.20.30"
    excluidas = set(cfg.get("combinacion_real", {}).get("exclusiones", {}).get("NUNCA_BLOQUEAR", []))

    eps, inc_m = leer_marcas(Path(a.marcas))
    regs, inc_r, dups = leer_motor(Path(a.motor))
    ref_motor = {"archivo": a.motor, "sha256": hashlib.sha256(Path(a.motor).read_bytes()).hexdigest()}
    ne = leer_no_evaluadas(Path(a.motor), regs, ref_motor)            # calidad/cobertura, aparte de las decisiones
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
        c = clasificar(ep, regs, origen, U, destinos, integridad.get(eid), ne["vigentes"])
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

    # emisiones REALES, aparte de las 7 configuraciones comparativas (no entran en la Tabla 8)
    detector_modelo = (cfg.get("modelo") or {}).get("detector")
    emis = emisiones_observadas(regs, eps, origen, destinos, desplegado, detector_modelo, ref_motor)
    for eid in por_ep:
        por_ep[eid]["emisiones_observadas"] = resumen_emisiones_episodio(
            [e for e in emis if e["episodio_id"] == eid])

    salida = {
        "fuentes": {"marcas": a.marcas, "motor": a.motor, "config": a.config},
        "umbrales": {"0.05_recalibrado": U["0.05"], "0.03_recalibrado": U["0.03"],
                     "0.05_desplegado_en_vivo": desplegado, "0.01_recalibrado": U["0.01"],
                     "escala": "score_samples; señal IF si score < umbral (estricto)",
                     "escala_anomalia_equivalente": {a: umbral_escala_anomalia(U[a]) for a in ALFAS},
                     "regla_escala_anomalia": "anomalia = -score; señal si anomalia > umbral_anomalia",
                     "orden_respetado": orden_ok, "procedencia": procedencia},
        "configuraciones": list(CONFIGS),
        "nota_umbral": "el motor emitió en vivo con el umbral DESPLEGADO; las 7 configuraciones (incluida IF_0.05 "
                       "recalibrada) son clasificaciones comparativas derivadas de los registros, no alertas emitidas.",
        "clasificacion_por": "logged_at (instante en que quedó registrada la evidencia usada) + solape de la ventana "
                             "con el ataque; window_end ≠ logged_at. En las configuraciones derivadas ese tiempo es "
                             "disponibilidad del registro; la latencia real de emisión está en emisiones_observadas.",
        "tiempos": {
            "clasificaciones_derivadas": TIEMPO_DERIVADO,
            "latencia_real_de_emision": "solo emisiones_observadas con componente_emisor=IF_desplegado, "
                                        "configuracion_emisora.estado=confirmada, relación durante y atribución "
                                        "confirmada: logged_at - inicio del generador",
            "cambio_de_campos": "hasta a6dc5ab: tiempo_es_emision_real (bool) y base 'emitido_por_modelo_desplegado'"
                                "/'emitido_ALERT(auth_heredada)'/'registrada_en_vivo'; desde 2026-10-28.2: "
                                "tiempo_significado, base derivada, evidencia_registrada y emisiones_observadas"},
        "emisiones_observadas": {
            "definicion": "decisiones ALERT y señales heurísticas registradas en vivo, tal como constan en el "
                          "registro; NO son una configuración ni entran en la Tabla 8; un score que cruza un umbral "
                          "sin ese registro no es una emisión",
            "detector_modelo_esperado": detector_modelo or "desconocido (la config no declara modelo.detector)",
            "umbral_desplegado_referencia": desplegado, "fuente": ref_motor,
            "resumen": {
                "eventos": len(emis),
                "por_componente": {k: sum(1 for e in emis if e["componente_emisor"] == k)
                                   for k in sorted({e["componente_emisor"] for e in emis})},
                "configuracion_desconocida": sum(1 for e in emis
                                                 if e["configuracion_emisora"]["estado"] == "desconocida")},
            "registros": emis},
        "atribucion_destino": "con --destinos" if destinos is not None else "sin evidencia de destino (incompleta)",
        "integridad_fuentes": ("de " + a.integridad) if a.integridad else "DESCONOCIDA (no se pasó --integridad); "
                               "ningún episodio se declara evaluable sin verificación de integridad",
        "calidad_datos": {"incidencias_marcas": inc_m, "incidencias_motor": inc_r, "ventanas_duplicadas": len(dups),
                          "episodios_incompletos": [e for e, v in eps.items() if v["estado"] != "completo"],
                          "ventanas_no_evaluadas": {"contadas": len(ne["vigentes"]),
                                                    "incidencias": len(ne["incidencias"]),
                                                    "duplicados": len(ne["duplicados"]),
                                                    "conflictos": len(ne["conflictos"]),
                                                    "detalle": "bloque ventanas_no_evaluadas"}},
        "ventanas_no_evaluadas": bloque_no_evaluadas(ne, eps, por_ep, origen),
        "tabla8": tabla, "episodios": por_ep}
    if not orden_ok:
        salida["calidad_datos"]["aviso_orden_umbrales"] = (
            "los umbrales no cumplen u_0.01 <= u_0.03 <= u_0.05: las señales IF no quedan anidadas por α")
    salida["control_normal_fpr"] = (fpr_control(regs, *map(como_epoch, a.control.split(",")), U, excluidas,
                                                ne["vigentes"])
                                    if a.control else {"calculado": False, "motivo": "no se pasó --control"})
    if a.etiquetas:
        et = {(r["entity_ip"], r["window_end_utc"]): r["etiqueta"]
              for r in csv.DictReader(open(a.etiquetas, encoding="utf-8"))}
        salida["metricas_por_ventana"] = metricas_por_ventana(regs, et, U, ne["vigentes"])
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
         "Umbrales (score_samples, señal si score < umbral): "
         + "; ".join(f"α {a.replace('.', ',')} = {salida['umbrales'][a + '_recalibrado']!r}" for a in ALFAS)
         + f"; desplegado en vivo = {salida['umbrales']['0.05_desplegado_en_vivo']!r}.", "",
         "| Familia | Evaluables | IF 0,05 | IF 0,03 | IF 0,01 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 "
         "| Híbrido 0,01 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for fam, t in tabla.items():
        n = len(t["evaluables"])
        L.append(f"| {fam} | {n} | " + " | ".join(f"{t[c]}/{n}" if n else "—" for c in CONFIGS) + " |")
    noev = ", ".join(e for t in tabla.values() for e in t["no_evaluables"]) or "ninguno"
    L += ["", f"No evaluables: {noev}", "",
          "Métricas por ventana: " + ("calculadas" if salida["metricas_por_ventana"].get("calculadas")
                                       else "no calculadas (" + salida["metricas_por_ventana"]["motivo"] + ")")]
    # registro aparte: lo que el sistema emitió realmente (no es una columna ni una octava configuración)
    L += ["", "## Emisiones observadas (registro aparte; no es una configuración de la tabla)", "",
          "Primera alerta del IF **desplegado** con umbral registrado = desplegado, durante el ataque y con "
          "atribución confirmada. Es la única base para una latencia real de emisión.", "",
          "| Episodio | Primera alerta real (s desde el inicio) | Registro | Eventos con emisor/configuración desconocida |",
          "|---|---|---|---|"]
    for eid, e in salida["episodios"].items():
        eo = e["emisiones_observadas"]; p = eo["primera_alerta_IF_desplegado_confirmada_durante"]
        L.append(f"| {eid} | {p['desde_inicio_generador_s'] if p else '—'} | {p['registro_id'] if p else '—'} "
                 f"| {eo['eventos_con_emisor_o_configuracion_desconocida']} |")
    # calidad y cobertura: ventanas que el motor declaró no evaluadas (no son decisiones ni negativos)
    ne = salida["ventanas_no_evaluadas"]
    L += ["", "## Ventanas no evaluadas (calidad y cobertura; no son decisiones)", "",
          f"Contadas: {ne['contadas']} · por motivo: "
          + (", ".join(f"{m} = {n}" for m, n in ne["por_motivo"].items()) or "—")
          + f" · duplicados: {len(ne['duplicados'])} · conflictos con decisión: {len(ne['conflictos'])}"
          + f" · incidencias: {len(ne['incidencias'])}", ""]
    afect = [(eid, e["ventanas_no_evaluadas"]) for eid, e in salida["episodios"].items()
             if e["ventanas_no_evaluadas"]["n"]]
    if afect:
        L += ["| Episodio | Ventanas del ataque | Posteriores que solapan | Evaluable | Efecto |", "|---|---|---|---|---|"]
        for eid, v in afect:
            L.append(f"| {eid} | {v['ventanas_del_ataque']} | {v['ventanas_posteriores_que_solapan']} | "
                     f"{'sí' if salida['episodios'][eid]['evaluable'] else 'no'} | {v['efecto_en_evaluabilidad']} |")
        L.append("")
    for d in ne["detecciones_confirmadas_en_episodios_no_evaluables"]:
        L.append(f"- Detección confirmada fuera de la comparación: {d['episodio_id']} "
                 f"({', '.join(d['configuraciones_con_deteccion_confirmada'])}).")
    for nombre, blq, k in (("Control", salida["control_normal_fpr"], "cobertura_evaluada"),
                           ("Métricas por ventana", salida["metricas_por_ventana"], "cobertura_etiquetadas")):
        if k in blq:
            n_ne = blq.get("ventanas_no_evaluadas", blq.get("etiquetadas_no_evaluadas"))
            L.append(f"- {nombre}: cobertura {blq[k]} ({n_ne} no evaluadas); tasas sobre ventanas evaluadas.")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
