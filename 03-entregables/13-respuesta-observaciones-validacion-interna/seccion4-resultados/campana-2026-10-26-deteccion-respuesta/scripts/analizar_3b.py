#!/usr/bin/env python3
"""Analizador de la campaña A REPETIDA (paso 3B), congelado en la preparación 3A (2026-11-01).

No ejecuta nada: lee registros. Reutiliza las lecturas, umbrales y señales de analizar.py (sin cambiarlas) y añade
lo que la primera campaña A no tenía: inventario de ventanas esperadas, puntualidad, detección DURANTE el ataque
por disponibilidad del registro y calidad de fuentes por episodio.

Entradas
  --marcas        marcas.jsonl del generador
  --motor         motor_decision.log en vivo (decisiones y ventana_no_evaluada)
  --config        config-campana-3b.json (umbrales, población, protocolo_3b)
  --ciclos        ciclos.jsonl en vivo (registro_escrito_en por ciclo; ciclos sin decisiones; huecos)
  --inventario    motor_decision.log de la repetición offline (replay_motor.py) sobre el PCAP/EVE archivados
  --inventario-rango "ini,fin"  inicio del archivo PCAP y cierre de la campaña (epoch o ISO). Las ventanas esperadas
                  son las decididas por la repetición con window_end en [ini + historia, fin - 120] (bordes: el motor
                  necesita historia completa al principio; al final la repetición no ve los últimos PCAP cerrados).
  --destinos      CSV de extraer_evidencia_destino.py --formato 3b
  --integridad    integridad.json de verificar_integridad.py
  --calidad-fuentes  JSON de calidad_fuentes.py
  --control       "desde,hasta" del control normal
  --salida        directorio

Definiciones (congeladas; ver PROTOCOLO-CAMPANA-A-REPETIDA.md)
  Disponibilidad de una ventana  registro_escrito_en del ciclo que la decidió (ciclos.jsonl, enlazado por
                  inicio_ciclo). Si no se puede enlazar, logged_at, y se declara ('disponibilidad_fuente').
  Puntualidad     a tiempo si disponibilidad - window_end <= 60 s; tardía si > 60 s. Una ventana tardía está
                  DECIDIDA: cuenta en la cobertura, no en la puntualidad.
  Estado de ventana (claves entity_ip|window_end dentro del inventario):
                  decidida_a_tiempo · decidida_tardia · no_evaluada (evento explícito) · ausente (esperada sin
                  registro en vivo) · solo_en_vivo (registro en vivo que la repetición no produjo; se informa).
                  Fuera del rango del inventario o sin inventario: evidencia_insuficiente (no se puede saber si faltan).
  Ciclo sin decisiones / hueco entre escrituras > 20 s: se informan; NO prueban pérdida (la pérdida solo se
                  establece contra el inventario: 'ausente').
  Alcance del inventario: la repetición usa los MISMOS datos capturados. Detecta pérdida del motor en vivo, no
                  pérdida del SPAN, tcpdump o Suricata (eso es calidad de fuentes). Coincidir con la repetición no
                  demuestra que una fuente degradada no tuviera efecto.
  Ventanas del episodio: las de la Kali con window_end en (inicio, fin+60) (su intervalo (w-60, w] solapa [inicio,
                  fin]), tomadas del inventario.
  Observación completa del episodio = todas sus ventanas esperadas decididas en vivo + fuente 'completa' + integridad
                  apta + evidencia de destino para cada ventana decidida. Define la POBLACIÓN PRINCIPAL y no depende
                  del resultado de la detección.
  Señal atribuible: la configuración da señal en la ventana Y la evidencia de destino muestra paquetes del origen
                  hacia el destino del episodio dentro de la ventana y dentro de [inicio, fin]
                  (paquetes_en_intervalo_ataque > 0).
  Categorías por configuración y episodio:
                  oportuna          hay una señal atribuible cuya disponibilidad es <= fin.
                  solo_posterior    hay señal atribuible, pero todas disponibles después del fin.
                  ausencia_con_observacion_suficiente   ninguna señal atribuible y observación completa.
                  no_evaluable      ninguna señal atribuible y observación incompleta (la falta de datos no es FN,
                                    ni TN, ni latencia 0).
                  Las categorías oportuna/solo_posterior se informan aunque la observación sea incompleta
                  ('en_poblacion_principal' dice si el episodio entra en la tabla principal).
  Las 7 configuraciones son clasificaciones DERIVADAS de los registros; sus tiempos son la disponibilidad del
  registro usado. Las EMISIONES (ALERT y heurísticos registrados en vivo) se cuentan aparte, con su latencia real.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402
import poblacion  # noqa: E402

PUNTUALIDAD_S = 60.0
BORDE_FIN_S = 120.0
HUECO_ESCRITURA_S = 20.0
HORIZONTE_S = an.HORIZONTE_S
CONFIGS = an.CONFIGS
CATEGORIAS = ("oportuna", "solo_posterior", "ausencia_con_observacion_suficiente", "no_evaluable")
ESTADOS_VENTANA = ("decidida_a_tiempo", "decidida_tardia", "no_evaluada", "ausente", "solo_en_vivo",
                   "evidencia_insuficiente")


# ------------------------------------------------------------------- lecturas
def leer_jsonl(path: Path) -> list:
    out = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def leer_ciclos(path: Path | None) -> list:
    if path is None:
        return []
    return sorted((c for c in leer_jsonl(path) if c.get("event") == "ciclo" and an._numero(c.get("inicio_ciclo"))),
                  key=lambda c: c["inicio_ciclo"])


def disponibilidad(regs: list, ciclos: list) -> None:
    """Añade _disp y _disp_fuente a cada registro (decisión o no evaluada)."""
    por_ini = {round(c["inicio_ciclo"], 6): c for c in ciclos}
    for r in regs:
        c = por_ini.get(round(r["inicio_ciclo"], 6)) if an._numero(r.get("inicio_ciclo")) else None
        if c is not None and an._numero(c.get("registro_escrito_en")):
            r["_disp"], r["_disp_fuente"] = float(c["registro_escrito_en"]), "registro_escrito_en(ciclo)"
        else:
            r["_disp"], r["_disp_fuente"] = r["_logged"], "logged_at(sin ciclo enlazable)"


def leer_inventario(path: Path | None, rango, historia: float) -> dict | None:
    if path is None or rango is None:
        return None
    lo, hi = rango[0] + historia, rango[1] - BORDE_FIN_S
    dec, ne = {}, {}
    for r in leer_jsonl(path):
        ev = r.get("event")
        if ev not in ("decision", an.EVENTO_NO_EVALUADA) or not r.get("window_end_utc") or not r.get("entity_ip"):
            continue
        w = an.ep_iso(r["window_end_utc"])
        if not (lo <= w <= hi):
            continue
        k = (r["entity_ip"], r["window_end_utc"])
        (dec if ev == "decision" else ne).setdefault(k, r)
    for k in set(dec) & set(ne):
        ne.pop(k)
    return {"desde": lo, "hasta": hi, "esperadas": dec, "no_evaluadas_en_referencia": ne,
            "fuente": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def leer_destinos_3b(path: Path | None):
    if path is None:
        return None
    """Formato 3b. Un CSV de formato 'a' (primera campaña) se acepta SOLO para re-análisis: sin la columna de
    actividad, ninguna señal es atribuible ('actividad_no_medida') y las ventanas posteriores al fin no tienen fila."""
    d = defaultdict(list)
    for row in csv.DictReader(open(path, encoding="utf-8")):
        tiene = "paquetes_en_intervalo_ataque" in row
        d[(row["episodio_id"], row["window_end_utc"])].append(
            {"destino": row["destino"],
             "paquetes_ventana": int(row["paquetes_ventana"] or 0) if tiene else None,
             "paquetes_en_intervalo_ataque": int(row["paquetes_en_intervalo_ataque"] or 0) if tiene else None})
    return dict(d)


# ------------------------------------------------------------------- ventanas
def estado_ventana(k, vivo: dict, ne_vivo: dict, inv: dict | None) -> str:
    """Estado de una clave entity_ip|window_end. vivo/ne_vivo: dicts clave -> registro."""
    if k in vivo:
        r = vivo[k]
        if inv is not None and k not in inv["esperadas"] and inv["desde"] <= r["_wend"] <= inv["hasta"]:
            return "solo_en_vivo"
        return "decidida_a_tiempo" if r["_disp"] - r["_wend"] <= PUNTUALIDAD_S else "decidida_tardia"
    if k in ne_vivo:
        return "no_evaluada"
    if inv is None:
        return "evidencia_insuficiente"
    w = an.ep_iso(k[1])
    if not (inv["desde"] <= w <= inv["hasta"]):
        return "evidencia_insuficiente"
    return "ausente" if k in inv["esperadas"] else "evidencia_insuficiente"


def inventario_resumen(inv, vivo, ne_vivo, excluida) -> dict:
    if inv is None:
        return {"disponible": False, "motivo": "sin --inventario/--inventario-rango: no se puede afirmar que no "
                                               "falten ventanas (estado evidencia_insuficiente)"}
    esp = {k for k in inv["esperadas"] if not excluida(k[0])}
    vivo_r = {k for k, r in vivo.items() if inv["desde"] <= r["_wend"] <= inv["hasta"] and not excluida(k[0])}
    est = Counter(estado_ventana(k, vivo, ne_vivo, inv) for k in esp)
    solo = vivo_r - esp
    ret = sorted(vivo[k]["_disp"] - vivo[k]["_wend"] for k in esp & vivo_r)
    return {"disponible": True, "fuente": inv["fuente"], "sha256": inv["sha256"],
            "rango_window_end_utc": [an.iso(inv["desde"]), an.iso(inv["hasta"])],
            "esperadas": len(esp), "estados": {e: est.get(e, 0) for e in ESTADOS_VENTANA[:4]},
            "solo_en_vivo": len(solo), "no_evaluadas_en_referencia": len(inv["no_evaluadas_en_referencia"]),
            "cobertura_total": round(len(esp & vivo_r) / len(esp), 6) if esp else None,
            "puntualidad": {"limite_s": PUNTUALIDAD_S,
                            "a_tiempo": est.get("decidida_a_tiempo", 0), "tardias": est.get("decidida_tardia", 0),
                            "retraso_disponibilidad_s": {"p50": _q(ret, .5), "p95": _q(ret, .95),
                                                         "max": ret[-1] if ret else None}},
            "alcance": "la repetición offline procesa los MISMOS PCAP/EVE: detecta ventanas que el motor en vivo no "
                       "decidió, no pérdidas del SPAN/tcpdump/Suricata; coincidir con ella no prueba que una fuente "
                       "degradada no tuviera efecto",
            "ejemplos_ausentes": sorted(f"{k[0]}|{k[1]}" for k in esp if est and
                                        estado_ventana(k, vivo, ne_vivo, inv) == "ausente")[:20],
            "ejemplos_solo_en_vivo": sorted(f"{k[0]}|{k[1]}" for k in solo)[:20]}


def _q(v, p):
    if not v:
        return None
    v = sorted(v); k = (len(v) - 1) * p; i = int(k)
    return round(v[i] if i + 1 >= len(v) else v[i] + (v[i + 1] - v[i]) * (k - i), 3)


def ciclos_resumen(ciclos: list, desde=None, hasta=None) -> dict:
    cs = [c for c in ciclos if (desde is None or c["inicio_ciclo"] >= desde) and (hasta is None or c["inicio_ciclo"] <= hasta)]
    esc = sorted(c["registro_escrito_en"] for c in cs if an._numero(c.get("registro_escrito_en")))
    huecos = [(a, b) for a, b in zip(esc, esc[1:]) if b - a > HUECO_ESCRITURA_S]
    return {"ciclos": len(cs), "sin_decisiones": sum(1 for c in cs if c.get("decididas") == 0),
            "duracion_s": {"p50": _q([c["duracion_s"] for c in cs if an._numero(c.get("duracion_s"))], .5),
                           "p95": _q([c["duracion_s"] for c in cs if an._numero(c.get("duracion_s"))], .95),
                           "max": max((c["duracion_s"] for c in cs if an._numero(c.get("duracion_s"))), default=None)},
            "huecos_escritura_mayores_20s": [{"desde_utc": an.iso(a), "hasta_utc": an.iso(b), "s": round(b - a, 1)}
                                             for a, b in huecos],
            "significado": "un ciclo sin decisiones o un hueco > 20 s entre escrituras NO prueba pérdida: las "
                           "ventanas pueden decidirse en ciclos posteriores (tardías). La pérdida solo se establece "
                           "contra el inventario (estado 'ausente')."}


# ------------------------------------------------------------------- episodio
def atribuible(destinos, eid, wend_utc, ep_destino):
    """(estado, detalle). estado: 'atribuible' | 'sin_actividad_del_ataque' | 'otro_destino' | 'sin_evidencia'."""
    if destinos is None:
        return "sin_evidencia", "no se aportó --destinos"
    filas = destinos.get((eid, wend_utc))
    if filas is None:
        return "sin_evidencia", "la ventana no tiene filas de destino"
    f = [x for x in filas if x["destino"] == ep_destino]
    if not f:
        return ("otro_destino" if any(x["destino"] for x in filas) else "sin_actividad_del_ataque"), \
               "sin paquetes del origen hacia el destino del episodio en la ventana"
    if f[0]["paquetes_en_intervalo_ataque"] is None:
        return "actividad_no_medida", "evidencia de destino de formato 'a': sin paquetes_en_intervalo_ataque"
    if f[0]["paquetes_en_intervalo_ataque"] <= 0:
        return "sin_actividad_del_ataque", "paquetes hacia el destino solo fuera de [inicio, fin]"
    return "atribuible", f"{f[0]['paquetes_en_intervalo_ataque']} paquetes hacia el destino dentro de [inicio, fin]"


def ventanas_esperadas_episodio(ep, origen, inv, vivo) -> tuple:
    """Claves esperadas de la Kali en (inicio, fin+60). Del inventario; sin él, las que haya en vivo (incompleto)."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    if inv is not None:
        ks = [k for k in inv["esperadas"] if k[0] == origen and ini < an.ep_iso(k[1]) < fin + HORIZONTE_S]
        dentro = inv["desde"] <= ini and fin + HORIZONTE_S <= inv["hasta"] + HORIZONTE_S
        return sorted(ks, key=lambda k: k[1]), ("inventario" if dentro else "inventario(episodio fuera del rango)")
    ks = [k for k, r in vivo.items() if k[0] == origen and ini < r["_wend"] < fin + HORIZONTE_S]
    return sorted(ks, key=lambda k: k[1]), "sin_inventario(solo registros en vivo)"


def clasificar_3b(eid, ep, origen, U, vivo, ne_vivo, inv, destinos, integridad, calidad) -> dict:
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    if fin is None or ep["estado"] != "completo":
        return {"en_poblacion_principal": False, "observacion": {"completa": False,
                "motivos": [f"episodio {ep['estado']}"]}, **{c: {"categoria": "no_evaluable"} for c in CONFIGS}}
    esp, origen_inv = ventanas_esperadas_episodio(ep, origen, inv, vivo)
    estados = {k: estado_ventana(k, vivo, ne_vivo, inv) for k in esp}
    decididas = [k for k in esp if k in vivo]
    sin_dest = [k for k in decididas if destinos is None or (eid, k[1]) not in destinos]
    cal = (calidad or {}).get(eid, {}).get("estado") if calidad is not None else None
    motivos = []
    if origen_inv != "inventario":
        motivos.append(f"ventanas esperadas: {origen_inv}")
    if not esp:
        motivos.append("ninguna ventana esperada de la Kali")
    falt = [k for k in esp if k not in vivo]
    if falt:
        motivos.append(f"{len(falt)}/{len(esp)} ventanas esperadas sin decisión ("
                       + ", ".join(f"{e}={n}" for e, n in Counter(estados[k] for k in falt).items()) + ")")
    if sin_dest:
        motivos.append(f"{len(sin_dest)} ventanas decididas sin evidencia de destino")
    if cal != "completa":
        motivos.append(f"fuente {cal or 'sin evaluar (no se aportó --calidad-fuentes)'}")
    if integridad is not True:
        motivos.append("integridad " + ("desconocida" if integridad is None else "no apta"))
    completa = not motivos
    ventanas = []
    for k in esp:
        r = vivo.get(k)
        st, det = atribuible(destinos, eid, k[1], ep.get("destino"))
        v = {"window_end_utc": k[1], "estado": estados[k], "atribucion": st}
        if r is not None:
            g = an.senales(r, U)
            v.update(disponible_utc=an.iso(r["_disp"]), disponibilidad_fuente=r["_disp_fuente"],
                     disponible_antes_fin=r["_disp"] <= fin, retraso_s=round(r["_disp"] - r["_wend"], 1),
                     decision=r.get("decision"), score=r.get("_score"),
                     heuristico=(r.get("heuristico") or {}).get("heuristico") if r.get("heuristico") else None,
                     senales=[c for c in CONFIGS if g[c]])
        ventanas.append(v)
    res = {"ventanas_esperadas": len(esp), "origen_ventanas": origen_inv,
           "estados_ventana": dict(Counter(estados.values())),
           "observacion": {"completa": completa, "motivos": motivos, "calidad_fuente": cal,
                           "integridad_apta": integridad},
           "en_poblacion_principal": completa, "ventanas": ventanas,
           # comprobación de referencia con el criterio del paso 2 (window_end en [inicio, fin+10])
           "ventanas_wend_inicio_fin10": sum(1 for k in esp if an.ep_iso(k[1]) <= fin + 10),
           "de_ellas_disponibles_antes_fin": sum(1 for k in esp if an.ep_iso(k[1]) <= fin + 10
                                                 and k in vivo and vivo[k]["_disp"] <= fin)}
    for c in CONFIGS:
        sen = [v for v in ventanas if c in v.get("senales", [])]
        atr = [v for v in sen if v["atribucion"] == "atribuible"]
        no_atr = [{"window_end_utc": v["window_end_utc"], "atribucion": v["atribucion"]} for v in sen
                  if v["atribucion"] != "atribuible"]
        op = [v for v in atr if v["disponible_antes_fin"]]
        if op:
            cat, p = "oportuna", min(op, key=lambda v: v["disponible_utc"])
        elif atr:
            cat, p = "solo_posterior", min(atr, key=lambda v: v["disponible_utc"])
        else:
            cat, p = ("ausencia_con_observacion_suficiente" if completa else "no_evaluable"), None
        res[c] = {"categoria": cat, "senales_atribuibles": len(atr), "oportunas": len(op),
                  "senales_no_atribuibles": no_atr,
                  "primera": None if p is None else {
                      "window_end_utc": p["window_end_utc"], "disponible_utc": p["disponible_utc"],
                      "disponible_desde_inicio_s": round(an.ep_iso(p["disponible_utc"]) - ini, 1)},
                  "tiempo_significado": "disponibilidad del registro usado; no es latencia de emisión"}
    return res


def emisiones_episodio(eid, ep, origen, vivo, destinos, desplegado, detector_modelo) -> dict:
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    if fin is None:
        return {"emisiones": 0, "oportunas": 0}
    lst = []
    for k, r in vivo.items():
        if k[0] != origen or not (ini < r["_wend"] < fin + HORIZONTE_S):
            continue
        if not (r.get("decision") == "ALERT" or r.get("heuristico") is not None):
            continue
        comp, _ = an.emisor_de(r, detector_modelo)
        st, _ = atribuible(destinos, eid, k[1], ep.get("destino"))
        lst.append({"window_end_utc": k[1], "componente_emisor": comp, "decision": r.get("decision"),
                    "configuracion_emisora": an.configuracion_emisora(r, comp, desplegado)["estado"],
                    "atribucion": st, "disponible_utc": an.iso(r["_disp"]), "logged_at_utc": an.iso(r["_logged"]),
                    "oportuna": r["_disp"] <= fin and st == "atribuible",
                    "latencia_disponible_s": round(r["_disp"] - ini, 2),
                    "latencia_logged_s": round(r["_logged"] - ini, 2)})
    lst.sort(key=lambda e: e["disponible_utc"])
    op = [e for e in lst if e["oportuna"]]
    return {"emisiones": len(lst), "atribuibles": sum(e["atribucion"] == "atribuible" for e in lst),
            "oportunas": len(op),
            "primera_oportuna": op[0] if op else None,
            "latencia_primera_oportuna_s": op[0]["latencia_disponible_s"] if op else None,
            "nota": "sin emisión oportuna la latencia es None (no 0)", "detalle": lst}


# ------------------------------------------------------------------- control
def control_3b(vivo, ne_vivo, inv, desde, hasta, U, pob) -> dict:
    exc = lambda ip: poblacion.excluida(ip, pob)  # noqa: E731
    regs = [r for r in vivo.values()]
    base = an.fpr_control(regs, desde, hasta, U, pob, list(ne_vivo.values()))
    if inv is not None:
        esp = {k for k in inv["esperadas"] if desde <= an.ep_iso(k[1]) <= hasta and not exc(k[0])}
        dec = {k for k in esp if k in vivo}
        n_falt = len(esp) - len(dec)
        base["inventario"] = {"esperadas": len(esp), "decididas": len(dec), "sin_decision": n_falt,
                              "cobertura_total": round(len(dec) / len(esp), 6) if esp else None,
                              "rango_inventario_utc": [an.iso(inv["desde"]), an.iso(inv["hasta"])],
                              "nota": "control fuera del rango del inventario: solo cuenta la parte cubierta"
                              if desde < inv["desde"] or hasta > inv["hasta"] else ""}
        base["inventario_esperado"] = "ver 'inventario'"
        for c in CONFIGS:
            if c in base:
                fa, n = base[c]["falsas_alarmas"], base["ventanas"]
                base[c]["cotas_si_faltan"] = {
                    "min": round(fa / (n + n_falt), 6) if n + n_falt else None,
                    "max": round((fa + n_falt) / (n + n_falt), 6) if n + n_falt else None,
                    "regla": "las ventanas sin decisión no se suponen negativas ni positivas: se dan las cotas"}
    base["umbral_cobertura"] = ("no se adopta un umbral automático (p. ej. 90 %): la tasa se publica con su "
                                "cobertura y sus cotas")
    por_ent = defaultdict(lambda: {"ventanas": 0, **{c: 0 for c in CONFIGS}})
    for r in regs:
        if desde <= r["_wend"] <= hasta and not exc(r["entity_ip"]):
            e = por_ent[r["entity_ip"]]; e["ventanas"] += 1
            g = an.senales(r, U)
            for c in CONFIGS:
                e[c] += bool(g[c])
    base["por_entidad"] = {ip: {**v, "excepcion_respuesta": poblacion.excepcion_respuesta(ip, pob)}
                           for ip, v in sorted(por_ent.items())}
    return base


# ------------------------------------------------------------------- principal
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--ciclos", type=Path)
    ap.add_argument("--inventario", type=Path)
    ap.add_argument("--inventario-rango")
    ap.add_argument("--destinos", type=Path)
    ap.add_argument("--integridad", type=Path)
    ap.add_argument("--calidad-fuentes", type=Path)
    ap.add_argument("--control")
    ap.add_argument("--etiqueta", default="", help="texto que identifica el análisis (p. ej. 'nuevo análisis de "
                                                   "evidencia del paso 2')")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)

    cfg = json.load(open(a.config, encoding="utf-8"))
    U = an.umbrales_de(cfg)
    proc = an.verificar_procedencia(cfg, a.config, U)
    try:
        pob = poblacion.cargar_poblacion(cfg)
    except poblacion.ErrorPoblacion as ex:
        raise SystemExit(f"config: población mal definida: {ex}")
    origen = cfg.get("origen") or "10.10.20.30"
    historia = float((cfg.get("protocolo_3b") or {}).get("historia_s", 230))
    desplegado = cfg["umbrales"].get("desplegado_referencia")
    detector_modelo = (cfg.get("modelo") or {}).get("detector")

    eps, inc_m = an.leer_marcas(a.marcas)
    regs, inc_r, dups = an.leer_motor(a.motor)
    ref = {"archivo": str(a.motor), "sha256": hashlib.sha256(a.motor.read_bytes()).hexdigest()}
    ne = an.leer_no_evaluadas(a.motor, regs, ref)
    ciclos = leer_ciclos(a.ciclos)
    disponibilidad(regs, ciclos)
    for e in ne["vigentes"]:
        e["_disp"], e["_disp_fuente"] = e["_logged"], "logged_at"
    vivo = {(r["entity_ip"], r["window_end_utc"]): r for r in regs}
    ne_vivo = {e["_clave"]: e for e in ne["vigentes"]}
    rango = tuple(map(an.como_epoch, a.inventario_rango.split(","))) if a.inventario_rango else None
    inv = leer_inventario(a.inventario, rango, historia)
    destinos = leer_destinos_3b(a.destinos)
    integ = {}
    if a.integridad:
        for e in json.load(open(a.integridad, encoding="utf-8")).get("episodios", []):
            integ[e["episodio_id"]] = bool(e.get("apto"))
    calidad = json.load(open(a.calidad_fuentes, encoding="utf-8"))["episodios"] if a.calidad_fuentes else None

    por_ep, tabla = {}, {}
    for eid, ep in sorted(eps.items(), key=lambda kv: kv[1]["inicio_ep"]):
        c = clasificar_3b(eid, ep, origen, U, vivo, ne_vivo, inv, destinos, integ.get(eid), calidad)
        c["emisiones_reales"] = emisiones_episodio(eid, ep, origen, vivo, destinos, desplegado, detector_modelo)
        por_ep[eid] = c
        t = tabla.setdefault(an.familia(ep["escenario"]), {
            "poblacion_principal": [], "fuera_de_poblacion": [],
            **{cf: Counter() for cf in CONFIGS}, "emisiones_oportunas_episodios": 0})
        (t["poblacion_principal"] if c["en_poblacion_principal"] else t["fuera_de_poblacion"]).append(eid)
        for cf in CONFIGS:
            t[cf][c[cf]["categoria"] if c["en_poblacion_principal"] else "fuera:" + c[cf]["categoria"]] += 1
        if c["en_poblacion_principal"] and c["emisiones_reales"]["oportunas"] > 0:
            t["emisiones_oportunas_episodios"] += 1
    for t in tabla.values():
        for cf in CONFIGS:
            t[cf] = dict(t[cf])

    exc = lambda ip: poblacion.excluida(ip, pob)  # noqa: E731
    salida = {
        "etiqueta": a.etiqueta, "analizador": "analizar_3b.py",
        "fuentes": {"marcas": str(a.marcas), "motor": ref, "ciclos": str(a.ciclos) if a.ciclos else None,
                    "destinos": str(a.destinos) if a.destinos else None,
                    "calidad_fuentes": str(a.calidad_fuentes) if a.calidad_fuentes else None,
                    "integridad": str(a.integridad) if a.integridad else None, "config": str(a.config)},
        "umbrales": {**{f"IF_{k}": v for k, v in U.items()}, "desplegado": desplegado, "procedencia": proc,
                     "orden_respetado": an.orden_umbrales(U)},
        "definiciones": __doc__.split("Definiciones (congeladas")[1].split("\"\"\"")[0].strip(),
        "poblacion": poblacion.publico(pob),
        "inventario": inventario_resumen(inv, vivo, ne_vivo, exc),
        "ciclos": ciclos_resumen(ciclos) if ciclos else {"disponible": False},
        "calidad_datos": {"incidencias_marcas": inc_m, "incidencias_motor": inc_r, "duplicados": len(dups),
                          "no_evaluadas_vivo": len(ne["vigentes"])},
        "tabla_principal": tabla,
        "tabla_principal_lectura": ("por familia: episodios en la población principal (observación completa) y, por "
                                    "configuración, conteo de categorías; los episodios fuera de la población se "
                                    "cuentan con prefijo 'fuera:' y sus detecciones siguen visibles"),
        "episodios": por_ep}
    if a.control:
        d, h = map(an.como_epoch, a.control.split(","))
        salida["control_normal"] = control_3b(vivo, ne_vivo, inv, d, h, U, pob)
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "analisis-3b.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=str),
                                               encoding="utf-8")
    (a.salida / "TABLA-3B.md").write_text(tabla_md(salida), encoding="utf-8")
    print(json.dumps({"tabla_principal": tabla, "inventario": {k: salida["inventario"].get(k) for k in
                      ("esperadas", "estados", "solo_en_vivo", "cobertura_total")}}, ensure_ascii=False, indent=1))
    return 0


def tabla_md(s: dict) -> str:
    L = [f"# Tabla 3B — {s['etiqueta'] or 'campaña A repetida'} (analizar_3b.py)", "",
         "Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),",
         "independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /",
         "no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.", "",
         "| Episodio | Principal | Ventanas esp. | " + " | ".join(CONFIGS) + " | Emisiones oportunas | 1.ª (s) |",
         "|" + "---|" * (len(CONFIGS) + 5)]
    for eid, c in s["episodios"].items():
        er = c.get("emisiones_reales", {})
        L.append(f"| {eid} | {'sí' if c['en_poblacion_principal'] else 'no'} | {c.get('ventanas_esperadas', '-')} | "
                 + " | ".join(c[cf]["categoria"] for cf in CONFIGS)
                 + f" | {er.get('oportunas', 0)} | {er.get('latencia_primera_oportuna_s')} |")
    L += ["", "Motivos fuera de la población principal:", ""]
    for eid, c in s["episodios"].items():
        if not c["en_poblacion_principal"]:
            L.append(f"- {eid}: " + "; ".join(c["observacion"]["motivos"]))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
