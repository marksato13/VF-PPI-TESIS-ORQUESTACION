#!/usr/bin/env python3
"""Presupuesto temporal y simulación de la cadena de respuesta sobre registros de SOMBRA (solo lee). Versión 2.

Etapa 1. No despliega, no ejecuta ataques y no toca ningún host. Reutiliza los registros del paso 3B (campaña A
en sombra: 25 episodios ejecutados; 15 admitidos por la revisión v2) y SIMULA qué habría hecho la cadena
publicador -> relé -> agente con el código desplegado.

LO QUE ESTA HERRAMIENTA NO ES
  * No es una campaña de respuesta. Reutiliza tráfico registrado sin bloqueo: no modela cómo una restricción
    habría cambiado el ataque, las decisiones posteriores ni el tráfico legítimo. Muestra riesgos bajo supuestos.
  * Sus tiempos de aplicación son ESTIMACIONES (t_apl_estimada). t_apl real y t_efecto valen "no aplica".
  * Los dos escenarios temporales ("favorable" y "alto") NO son intervalos de confianza ni límites garantizados:
      favorable = duraciones p50/mínimas medidas y offsets desconocidos supuestos en 0 (supuesto declarado);
      alto      = máximos HISTÓRICOS medidos + cotas configuradas (AccuracySec=1s) para los offsets.
    El comportamiento futuro puede quedar fuera de ambos.
  * Las demoras DESCONOCIDAS (activación nft, efecto en el tráfico) no se sustituyen por cero para certificar
    oportunidad: se listan y la clase lleva el sufijo "_bajo_supuestos". Solo "deteccion_posterior" (t_det medido
    después del fin) es una conclusión que no depende de supuestos de la cadena.

Componentes simulados con el código DESPLEGADO extraído literalmente: `_verdicto_de`, `_SEVERIDAD` y
NUNCA_BLOQUEAR del publicador (f7bc4c7d) y `escalada.procesar` (7d80ab4a). El agente se modela según 2985c123
(sets que nunca acortan; LIMIT no degrada un BLOCK vivo; BLOCK saca al origen del set LIMIT).

Políticas para la decisión D3 (acción del IF), evaluadas con varios umbrales α:
  actual        ALERT del IF -> LIMIT (publicador desplegado)
  if_senal      el IF solo señala; restringen únicamente los heurísticos
  persist_k     el IF propone LIMIT solo si hay ALERT del IF en las k ventanas consecutivas (paso 10 s) que
                terminan en la actual, todas ya escritas cuando se escribe la actual (k = 2, 3)
(Corroboración IF + heurístico en la misma ventana: la acción la da el heurístico, así que en acciones coincide
con if_senal; se documenta en DECISIONES.md, no se simula aparte.)
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

ORIGEN = "10.10.20.30"
# Regla prevista por escenario (escenarios.json / FICHAS). Una señal de otra regla no valida la prevista.
REGLA_PREVISTA = {"dns_inusual": "dns_entropy", "inundacion_http": "http_abuse", "escaneo_breve": "port_scan",
                  "escaneo_sostenido": "port_scan", "fuerza_bruta_http": "brute_force"}
PERIODO = 10.0
FASE = {"pub": 0.0, "relay": 3.0, "agente": 6.0}

# Cada parámetro: (valor, clase, fuente). Clases: medido | configurado | supuesto | desconocido.
PARAM = {
    "pub_inicio_offset_s": (0.29, "medido", "journal 3B: 972 ejecuciones arrancan en :x0,29"),
    "pub_duracion_p50_s": (0.598, "medido", "3B, 972 ejecuciones (p50)"),
    "pub_duracion_max_s": (0.773, "medido", "3B, 972 ejecuciones (máximo histórico, no garantizado)"),
    "relay_inicio_offset_favorable_s": (0.0, "supuesto", "offset real desconocido; supuesto 0 en 'favorable'"),
    "relay_inicio_offset_alto_s": (1.0, "configurado", "AccuracySec=1s del timer (cota de systemd)"),
    "relay_duracion_min_s": (1.065, "medido", "systemctl show en el bastión (pocas muestras)"),
    "relay_duracion_max_s": (1.612, "medido", "systemctl show en el bastión (pocas muestras; no garantizado)"),
    "agente_inicio_offset_favorable_s": (0.0, "supuesto", "offset real desconocido; supuesto 0 en 'favorable'"),
    "agente_inicio_offset_alto_s": (1.0, "configurado", "AccuracySec=1s del timer"),
    "agente_duracion_p50_s": (0.173, "medido", "octubre, 76 201 ejecuciones (p50)"),
    "agente_duracion_max_s": (0.564, "medido", "octubre, 76 201 ejecuciones (máximo histórico)"),
    "reloj_incertidumbre_s": (0.01, "medido", "relojes-3b.log: |desfase| <= 0,0036 +- 0,0006 s en 4 hosts"),
}
P = {k: v[0] for k, v in PARAM.items()}
DESCONOCIDAS = {
    "activacion_nft_s": "del commit nft al primer paquete descartado; las reglas no tienen `counter`",
    "efecto_s": "de la aplicación al cese del efecto del ataque (conexiones abiertas, retransmisiones, tasa)",
    "lectura_publicador": "punto exacto de lectura del registro dentro de la ejecución del publicador",
}
ESCENARIOS = {
    "favorable": {"lee_al_final": True, "pub_dur": P["pub_duracion_p50_s"],
                  "relay_off": P["relay_inicio_offset_favorable_s"], "relay_dur": P["relay_duracion_min_s"],
                  "ag_off": P["agente_inicio_offset_favorable_s"], "ag_dur": P["agente_duracion_p50_s"]},
    "alto": {"lee_al_final": False, "pub_dur": P["pub_duracion_max_s"],
             "relay_off": P["relay_inicio_offset_alto_s"], "relay_dur": P["relay_duracion_max_s"],
             "ag_off": P["agente_inicio_offset_alto_s"], "ag_dur": P["agente_duracion_max_s"]},
}


def iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def abrir(p: Path):
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else p.open(encoding="utf-8")


# --- Código desplegado ---------------------------------------------------------------------------------------
def extraer_publicador(path: Path) -> tuple:
    """(_verdicto_de, _SEVERIDAD, NUNCA) ejecutando SOLO esos nodos del fuente desplegado."""
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    nodos = [n for n in arbol.body
             if (isinstance(n, ast.FunctionDef) and n.name == "_verdicto_de")
             or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("_SEVERIDAD", "NUNCA_BLOQUEAR_POR_DEFECTO")
                                                   for t in n.targets))]
    ns: dict = {"__builtins__": __builtins__}
    exec(compile(ast.Module(body=nodos, type_ignores=[]), str(path), "exec"), ns)  # noqa: S102 (código del repo)
    return ns["_verdicto_de"], ns["_SEVERIDAD"], set(ns["NUNCA_BLOQUEAR_POR_DEFECTO"])


def cargar_escalada(path: Path):
    spec = importlib.util.spec_from_file_location("escalada_desplegada", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- Políticas (D3) ------------------------------------------------------------------------------------------
def es_heuristico_legacy(d: dict) -> bool:
    return d.get("decision") == "ALERT" and str(d.get("detector_name", "")).endswith("_heuristic")


def alerta_if(d: dict, umbral: float | None) -> bool:
    """ALERT del IF. umbral None = la decisión registrada del motor (umbral desplegado)."""
    if es_heuristico_legacy(d):
        return False
    if umbral is None:
        return d.get("decision") == "ALERT"
    sc = d.get("score")
    return sc is not None and sc < umbral


def construir_politica(nombre: str, umbral: float | None, decisiones: list[dict], verdicto_desplegado, sev):
    """Devuelve vfun(d) -> (accion, motivo, detector) | None."""
    if nombre == "actual" and umbral is None:
        return verdicto_desplegado
    k = {"persist_2": 2, "persist_3": 3}.get(nombre)
    alertas = {}
    if k:
        for d in decisiones:
            if alerta_if(d, umbral):
                clave = (d["entity_ip"], d["window_end_utc"][:19])
                la = float(d["logged_at"])
                alertas[clave] = min(la, alertas.get(clave, la))

    def persistente(d: dict) -> bool:
        w = ts(d["window_end_utc"])
        la = float(d["logged_at"])
        for i in range(k):
            clave = (d["entity_ip"], iso(w - PERIODO * i)[:19])
            if clave not in alertas or alertas[clave] > la + 1e-6:
                return False
        return True

    def vfun(d: dict):
        cand = []
        det = str(d.get("detector_name", ""))
        if es_heuristico_legacy(d):
            cand.append(("BLOCK", det, det))
        if alerta_if(d, umbral):
            if nombre == "actual" or (k and persistente(d)):
                cand.append(("LIMIT", "modelo:" + det, det))
        h = d.get("heuristico")
        if isinstance(h, dict) and h.get("accion") in sev:
            cand.append((h["accion"], "%s: %s" % (h.get("heuristico", "?"), h.get("motivo", "")),
                         str(h.get("heuristico", "heuristico"))))
        return max(cand, key=lambda c: sev[c[0]]) if cand else None
    return vfun


# --- Modelo temporal de la cadena por timers -----------------------------------------------------------------
def siguiente(t: float, fase: float) -> float:
    """Primer instante de la rejilla (fase mod 10) que es >= t."""
    return math.ceil(round((t - fase) / PERIODO, 9)) * PERIODO + fase


def aplicar_desde_tick(T: float, esc: str) -> dict:
    """Desde el tick T del publicador: fin de publicación, relé y agente, con la regla de consumidor perdido:
    si el publicador termina después de que arranque el relé, el relé copia el feed ANTERIOR y la entrada nueva
    viaja en el relé siguiente (+10 s); igual entre relé y agente."""
    e = ESCENARIOS[esc]
    pub_fin = T + P["pub_inicio_offset_s"] + e["pub_dur"]
    R = siguiente(pub_fin - e["relay_off"], FASE["relay"])
    relay_fin = R + e["relay_off"] + e["relay_dur"]
    A = siguiente(relay_fin - e["ag_off"], FASE["agente"])
    t_apl = A + e["ag_off"] + e["ag_dur"]
    return {"tick_pub": T, "pub_fin": pub_fin, "tick_relay": R, "relay_fin": relay_fin, "tick_agente": A,
            "t_apl_estimada": t_apl,
            "relay_perdido": R - T > FASE["relay"] + 1e-6, "agente_perdido": A - R > FASE["agente"] - FASE["relay"] + 1e-6}


def tick_para(t_det: float, esc: str) -> float:
    """Tick del publicador que incluye un registro escrito en t_det. favorable: lee al final de su ejecución;
    alto: lee al arrancar (el punto real de lectura es desconocido)."""
    e = ESCENARIOS[esc]
    lectura = P["pub_inicio_offset_s"] + (e["pub_dur"] if e["lee_al_final"] else 0.0)
    return siguiente(t_det - lectura, FASE["pub"])


def cadena_timers(t_det: float, esc: str) -> dict:
    return aplicar_desde_tick(tick_para(t_det, esc), esc)


def cadena_eventos(t_det: float, esc: str) -> float:
    """V1: publicador, relé y agente encadenados por eventos (sin esperar timers); mismas duraciones."""
    e = ESCENARIOS[esc]
    return t_det + e["pub_dur"] + e["relay_dur"] + e["ag_dur"]


def clasificar(t_fin: float, t_det: float, t_fav: float, t_alto: float) -> str:
    eps = P["reloj_incertidumbre_s"]
    if t_det - eps > t_fin:
        return "deteccion_posterior"                 # medido: no depende de supuestos de la cadena
    if t_fav - eps > t_fin:
        return "despues_del_fin_bajo_supuestos"
    if t_alto + eps < t_fin:
        return "antes_del_fin_bajo_supuestos"        # además deben caber las demoras DESCONOCIDAS
    return "indeterminado"


# --- Simulación de la cadena ---------------------------------------------------------------------------------
class Cadena:
    """Publicador (ventana 120 s, más severo por IP, escalada) + agente (sets nft que nunca acortan)."""

    def __init__(self, escalada, verdicto, sev, nunca):
        self.esc, self.verdicto, self.sev, self.nunca = escalada, verdicto, sev, nunca
        self.estado: dict = {}
        self.kernel: dict = {}
        self.aplicaciones: list = []
        self.ultimo_feed: list = []

    def tick(self, T: float, decisiones: list[dict]):
        ahora = T + P["pub_inicio_offset_s"]
        por_ip: dict = {}
        for d in decisiones:
            la = float(d.get("logged_at", 0))
            if la > ahora:
                break
            if la < ahora - 120:
                continue
            ip = str(d.get("entity_ip", ""))
            if not ip or ip in self.nunca:
                continue
            v = self.verdicto(d)
            if v is None:
                continue
            prev = por_ip.get(ip)
            if (prev is None or self.sev[v[0]] > self.sev[prev[0]]
                    or (self.sev[v[0]] == self.sev[prev[0]] and la > prev[3])):
                por_ip[ip] = (v[0], v[1], v[2], la)
        fav = aplicar_desde_tick(T, "favorable")["t_apl_estimada"]
        alto = aplicar_desde_tick(T, "alto")["t_apl_estimada"]
        feed = []
        for ip, (acc, mot, det, la) in sorted(por_ip.items()):
            e = self.esc.procesar(self.estado, ip, acc, ahora, evento_ts=la)
            hasta = round(ahora + e["timeout_s"])
            feed.append({"ip": ip, "accion": e["accion"], "hasta": hasta, "alcance": "all", "motivo": mot,
                         "detector": det, "nivel": e["nivel"], "revisar_humano": e["revisar_humano"]})
            k = self.kernel.setdefault(ip, {"BLOCK": 0.0, "LIMIT": 0.0})
            if acc == "LIMIT" and k["BLOCK"] > fav:
                continue
            if acc == "BLOCK":
                k["LIMIT"] = 0.0
            if hasta <= k[acc] + 1:
                continue
            nueva = k[acc] <= fav
            k[acc] = hasta
            self.aplicaciones.append({"ip": ip, "accion": acc, "t_apl_favorable": fav, "t_apl_alto": alto,
                                      "hasta": hasta, "nivel": e["nivel"], "nueva": nueva, "tick": T,
                                      "revisar_humano": e["revisar_humano"]})
        self.ultimo_feed = feed


def correr(cadena: Cadena, decisiones: list[dict], desde: float, hasta: float):
    i0 = 0
    T = math.floor(desde / PERIODO) * PERIODO
    while T <= hasta:
        ahora = T + P["pub_inicio_offset_s"]
        while i0 < len(decisiones) and float(decisiones[i0]["logged_at"]) < ahora - 120:
            i0 += 1
        cadena.tick(T, decisiones[i0:])
        T += PERIODO


def dist(v: list) -> dict | None:
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    return {"n": len(v), "min": round(v[0], 2), "mediana": round(statistics.median(v), 2),
            "max": round(v[-1], 2), "valores": [round(x, 2) for x in v]}


CLASES = ("antes_del_fin_bajo_supuestos", "indeterminado", "despues_del_fin_bajo_supuestos", "deteccion_posterior")


# --- Evaluación por episodio ---------------------------------------------------------------------------------
def evaluar_episodios(eps, kali, atrib_por_ep, ciclos, vfun) -> list[dict]:
    out = []
    for ep in eps:
        t0, t_fin = ep["t_inicio"], ep["t_fin_eval"]
        atrib = atrib_por_ep[ep["episodio"]]
        primeras: dict = {}
        for d in kali:
            w = atrib.get(d["window_end_utc"])
            if not w or w.get("atribucion") != "atribuible":
                continue
            v = vfun(d)
            if v is None:
                continue
            disp = ts(w["disponible_utc"])
            claves = ["cualquiera", v[0]]
            h = d.get("heuristico")
            if isinstance(h, dict) and h.get("heuristico") == REGLA_PREVISTA.get(ep["escenario"])                     and h.get("accion") in ("LIMIT", "BLOCK"):
                claves.append("prevista")
            for clave in claves:
                if clave not in primeras or disp < primeras[clave][0]:
                    primeras[clave] = (disp, d, v, w)
        res = {"episodio": ep["episodio"], "escenario": ep["escenario"]}
        for clave in ("cualquiera", "prevista", "LIMIT", "BLOCK"):
            if clave not in primeras:
                res["primera_" + clave] = None
                continue
            td, d, v, w = primeras[clave]
            cyc = ciclos.get(round(d["inicio_ciclo"], 4))
            w_end = ts(d["window_end_utc"])
            v0 = {e: cadena_timers(td, e) for e in ESCENARIOS}
            v1 = {e: cadena_eventos(td, e) for e in ESCENARIOS}
            td2 = w_end + (cyc["duracion_s"] if cyc else 0.0)
            v2 = {e: cadena_eventos(td2, e) for e in ESCENARIOS}
            rel = lambda x: round(x - t0, 2)  # noqa: E731
            res["primera_" + clave] = {
                "window_end_utc": d["window_end_utc"], "accion": v[0], "motivo": v[1],
                "t_det_utc": iso(td), "disponibilidad_fuente": w.get("disponibilidad_fuente"),
                "t_det_menos_inicio_s": rel(td), "duracion_ciclo_s": cyc["duracion_s"] if cyc else None,
                "ventana_cierra_menos_inicio_s": rel(w_end),
                "deteccion_disponible_antes_del_fin": td + P["reloj_incertidumbre_s"] < t_fin,
                "V0": {"t_apl_estimada_menos_inicio_s": {"favorable": rel(v0["favorable"]["t_apl_estimada"]),
                                                         "alto": rel(v0["alto"]["t_apl_estimada"])},
                       "t_apl_estimada_menos_t_det_s": {e: round(v0[e]["t_apl_estimada"] - td, 2) for e in v0},
                       "margen_s": {e: round(t_fin - v0[e]["t_apl_estimada"], 2) for e in v0},
                       "consumidor_perdido_alto": v0["alto"]["relay_perdido"] or v0["alto"]["agente_perdido"],
                       "clase": clasificar(t_fin, td, v0["favorable"]["t_apl_estimada"],
                                           v0["alto"]["t_apl_estimada"])},
                "V1": {"t_apl_estimada_menos_inicio_s": {e: rel(v1[e]) for e in v1},
                       "clase": clasificar(t_fin, td, v1["favorable"], v1["alto"])},
                "V2": {"t_det_menos_inicio_s": rel(td2),
                       "t_apl_estimada_menos_inicio_s": {e: rel(v2[e]) for e in v2},
                       "clase": clasificar(t_fin, td2, v2["favorable"], v2["alto"])},
                "demoras_desconocidas_no_incluidas": sorted(DESCONOCIDAS)}
        out.append(res)
    return out


def resumir(evs: list[dict], eps_meta: dict) -> dict:
    resumen = {}
    for esc in sorted({x["escenario"] for x in evs}):
        xs = [x for x in evs if x["escenario"] == esc]
        r = {"episodios": len(xs), "admitidos_v2": sum(eps_meta[x["episodio"]]["admitido_v2"] for x in xs)}
        for clave in ("cualquiera", "prevista", "BLOCK"):
            ok = [x["primera_" + clave] for x in xs if x["primera_" + clave]]
            r[clave] = {
                "con_senal_atribuible": len(ok),
                "deteccion_disponible_antes_del_fin": sum(p["deteccion_disponible_antes_del_fin"] for p in ok),
                "t_det_menos_inicio_s": dist([p["t_det_menos_inicio_s"] for p in ok]),
                "V0_t_apl_estimada_alto_menos_inicio_s": dist([p["V0"]["t_apl_estimada_menos_inicio_s"]["alto"]
                                                              for p in ok]),
                "V0_margen_alto_s": dist([p["V0"]["margen_s"]["alto"] for p in ok]),
                **{v + "_clases": {c: sum(p[v]["clase"] == c for p in ok) for c in CLASES}
                   for v in ("V0", "V1", "V2")}}
        resumen[esc] = r
    return resumen


# --- Control normal ------------------------------------------------------------------------------------------
def evaluar_control(dec, en_ctl, claves_ctl, c0, c1, vfun, escalada, sev, nunca) -> dict:
    vistos, senal_ts = set(), {}
    n_veredicto, por_ent_senal = 0, {}
    for d in en_ctl:
        k = (d["entity_ip"], d["window_end_utc"])
        if k in vistos:
            continue
        vistos.add(k)
        v = vfun(d)
        if v is None:
            continue
        n_veredicto += 1
        senal_ts.setdefault(d["entity_ip"], []).append(ts(d["window_end_utc"]))
        t = "LIMIT_modelo" if v[1].startswith("modelo:") else "%s_%s" % (v[0], v[2])
        por_ent_senal.setdefault(d["entity_ip"], {}).setdefault(t, 0)
        por_ent_senal[d["entity_ip"]][t] += 1
    inc_senal = {}
    for ip, lst in senal_ts.items():
        lst.sort()
        inc_senal[ip] = 1 + sum(1 for x, y in zip(lst, lst[1:]) if y - x > 120)
    cad = Cadena(escalada, vfun, sev, nunca)
    sub = [d for d in dec if c0 - 130 <= float(d["logged_at"]) and ts(d["window_end_utc"]) <= c1]
    correr(cad, sub, c0, c1)
    por_ent: dict = {}
    for x in cad.aplicaciones:
        pe = por_ent.setdefault(x["ip"], {"aplicaciones_nuevas": 0, "renovaciones": 0, "BLOCK": 0, "_iv": []})
        pe["aplicaciones_nuevas" if x["nueva"] else "renovaciones"] += 1
        pe["BLOCK"] += x["accion"] == "BLOCK"
        a_, b_ = max(x["t_apl_favorable"], c0), min(x["hasta"], c1)
        if b_ > a_:
            iv = pe["_iv"]
            if iv and a_ <= iv[-1][1]:
                iv[-1][1] = max(iv[-1][1], b_)
            else:
                iv.append([a_, b_])
    for pe in por_ent.values():
        iv = pe.pop("_iv")
        pe["intervalos_restriccion"] = len(iv)
        pe["segundos_restringida_hipotetica"] = round(sum(b - a for a, b in iv), 1)
        pe["fraccion_control_restringida_hipotetica"] = round(pe["segundos_restringida_hipotetica"] / (c1 - c0), 3)
    return {
        "ventanas_con_veredicto": n_veredicto,
        "tasa_ventanas_con_veredicto": round(n_veredicto / len(claves_ctl), 4),
        "senales_por_entidad": por_ent_senal,
        "incidentes_senal_por_entidad": inc_senal,
        "incidentes_senal_total": sum(inc_senal.values()),
        "incidentes_senal_sin_nunca_bloquear": sum(v for k, v in inc_senal.items() if k not in nunca),
        "entidades_con_restriccion_hipotetica": sorted(por_ent),
        "restricciones_hipoteticas_por_entidad": por_ent,
        "intervalos_restriccion_total": sum(p["intervalos_restriccion"] for p in por_ent.values()),
        "renovaciones_total": sum(p["renovaciones"] for p in por_ent.values()),
        "block_a_entidades": sum(p["BLOCK"] for p in por_ent.values()),
        "nota": "restricciones HIPOTÉTICAS (simuladas sobre tráfico de sombra); no se aplicaron. El tiempo "
                "restringido se mide sobre la unión de intervalos con renovaciones, no se deduce del número de "
                "intervalos."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for n in ("marcas", "decisiones", "ciclos", "analisis", "control", "publicador", "escalada", "salida"):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()

    verdicto, sev, nunca = extraer_publicador(a.publicador)
    escalada = cargar_escalada(a.escalada)
    an = json.loads(a.analisis.read_text(encoding="utf-8"))
    umbrales = {"desplegado": None, **{k: an["umbrales"][k] for k in ("IF_0.05", "IF_0.03", "IF_0.01")}}

    ciclos = {}
    with abrir(a.ciclos) as fh:
        for l in fh:
            r = json.loads(l)
            if r.get("event") == "ciclo":
                ciclos[round(r["inicio_ciclo"], 4)] = r
    dec = []
    with abrir(a.decisiones) as fh:
        for l in fh:
            if '"event": "decision"' in l:
                dec.append(json.loads(l))
    dec.sort(key=lambda d: float(d["logged_at"]))
    kali = sorted((d for d in dec if d.get("entity_ip") == ORIGEN), key=lambda d: d["window_end_utc"])

    ini, fin = {}, {}
    with abrir(a.marcas) as fh:
        for l in fh:
            r = json.loads(l)
            if r.get("evento") in ("inicio", "fin"):
                (ini if r["evento"] == "inicio" else fin)[r["episodio_id"]] = r
    orden = sorted(ini, key=lambda e: ts(ini[e]["reloj"]["pared_utc"]))

    # D8: horizonte. Bucles: t_inicio + 90 s. nmap: D_ref = duración natural MÍNIMA de la familia en esta
    # campaña A. En todos los casos t_fin_eval = min(t_fin_ref, t_fin_observado): una referencia fija no convierte
    # en oportuna una actuación posterior al final real.
    nat: dict = {}
    for e in orden:
        if ini[e]["escenario"].startswith("escaneo"):
            nat.setdefault(ini[e]["escenario"], []).append(
                ts(fin[e]["reloj"]["pared_utc"]) - ts(ini[e]["reloj"]["pared_utc"]))
    d_ref = {k: min(v) for k, v in nat.items()}
    eps, meta = [], {}
    for e in orden:
        esc = ini[e]["escenario"]
        t0 = ts(ini[e]["reloj"]["pared_utc"])
        t_obs = ts(fin[e]["reloj"]["pared_utc"])
        t_ref = t0 + d_ref.get(esc, 90.0)
        eps.append({"episodio": e, "escenario": esc, "t_inicio": t0, "t_fin_eval": min(t_ref, t_obs)})
        meta[e] = {"episodio": e, "escenario": esc, "admitido_v2": an["episodios"][e]["en_poblacion_principal"],
                   "motivos_exclusion_v2": an["episodios"][e]["observacion"]["motivos"],
                   "calidad_fuente_v2": an["episodios"][e]["observacion"]["calidad_fuente"],
                   "t_inicio_utc": iso(t0), "t_fin_ref_utc": iso(t_ref),
                   "fuente_fin_ref": ("D_ref mínima de la familia (3B)" if esc.startswith("escaneo")
                                      else "programado: bucle de 90 s"),
                   "t_fin_observado_utc": iso(t_obs), "t_fin_eval_utc": iso(min(t_ref, t_obs)),
                   "duracion_observada_s": round(t_obs - t0, 2),
                   "t_apl_real": "no aplica (sombra: agente inactivo)", "t_efecto": "no aplica (sombra)"}
    atrib_por_ep = {e: {w["window_end_utc"]: w for w in an["episodios"][e]["ventanas"]} for e in orden}

    # Políticas × umbral
    ctl = json.loads(a.control.read_text(encoding="utf-8"))["control_normal"]
    c0, c1 = ts(ctl["desde"]), ts(ctl["hasta"])
    en_ctl = [d for d in dec if c0 <= ts(d["window_end_utc"]) <= c1]
    claves_ctl = {(d["entity_ip"], d["window_end_utc"]) for d in en_ctl}
    politicas = {}
    for pol in ("actual", "if_senal", "persist_2", "persist_3"):
        for un_nombre, un in umbrales.items():
            if pol == "if_senal" and un_nombre != "desplegado":
                continue                                    # sin IF en la acción, α no cambia las acciones
            vfun = construir_politica(pol, un, dec, verdicto, sev)
            evs = evaluar_episodios(eps, kali, atrib_por_ep, ciclos, vfun)
            politicas["%s|%s" % (pol, un_nombre)] = {
                "politica": pol, "umbral_if": un_nombre,
                "resumen_por_escenario": resumir(evs, meta),
                "control": evaluar_control(dec, en_ctl, claves_ctl, c0, c1, vfun, escalada, sev, nunca),
                "episodios": evs if (pol == "actual" and un_nombre == "desplegado") else None}

    # Secuencial con la política actual (riesgo de contaminación bajo supuestos)
    cad_s = Cadena(escalada, verdicto, sev, nunca)
    correr(cad_s, dec, float(dec[0]["logged_at"]), float(dec[-1]["logged_at"]))
    estado_por_ep = []
    for ep in eps:
        t0 = ep["t_inicio"]
        prev = [x for x in cad_s.aplicaciones if x["ip"] == ORIGEN and x["t_apl_alto"] <= t0]
        vb = max((x["hasta"] for x in prev if x["accion"] == "BLOCK"), default=0)
        vl = max((x["hasta"] for x in prev if x["accion"] == "LIMIT"), default=0)
        estado_por_ep.append({"episodio": ep["episodio"], "block_hipotetico_vigente_al_inicio": vb > t0,
                              "block_restante_s": round(vb - t0, 1) if vb > t0 else 0,
                              "limit_hipotetico_vigente_al_inicio": vl > t0 and vb <= t0,
                              "nivel_escalada_previo": max((x["nivel"] for x in prev), default=0)})

    out = {"herramienta": "presupuesto_e2e.py v2", "solo_lectura": True,
           "advertencia": ("Simulación sobre tráfico registrado en sombra. No es una campaña de respuesta: no "
                           "modela cómo una restricción habría cambiado ataques, decisiones ni tráfico legítimo. "
                           "Los tiempos de aplicación son estimaciones bajo supuestos; t_apl real y t_efecto: no "
                           "aplica."),
           "poblaciones": {"campana_3b_ejecutados": len(orden),
                           "revision_3b_admitidos_v2": sum(m["admitido_v2"] for m in meta.values()),
                           "nota": "la simulación se calcula para los 25 ejecutados; cada fila lleva admitido_v2"},
           "entradas_sha256": {k: sha(getattr(a, k)) for k in
                               ("marcas", "decisiones", "ciclos", "analisis", "control", "publicador", "escalada")},
           "parametros": {k: {"valor": v[0], "clase": v[1], "fuente": v[2]} for k, v in PARAM.items()},
           "demoras_desconocidas": DESCONOCIDAS,
           "escenarios_temporales": {k: {**v, "significado": ("p50/mínimos medidos + offsets supuestos 0" if
                                                             k == "favorable" else
                                                             "máximos históricos + cotas configuradas")}
                                     for k, v in ESCENARIOS.items()},
           "d_ref_nmap_s": {k: round(v, 2) for k, v in d_ref.items()},
           "duraciones_naturales_nmap_s": {k: [round(x, 2) for x in v] for k, v in nat.items()},
           "episodios_meta": [meta[e] for e in orden],
           "politicas": politicas,
           "secuencial": {"politica": "actual|desplegado", "estado_al_inicio_de_cada_episodio": estado_por_ep,
                          "estado_escalada_final_origen": cad_s.estado.get(ORIGEN),
                          "nota": "riesgo bajo supuestos: con bloqueo real, los ataques y decisiones posteriores "
                                  "habrían sido otros"},
           "control": {"intervalo_utc": [ctl["desde"], ctl["hasta"]], "duracion_s": c1 - c0,
                       "ventanas_decididas": len(claves_ctl),
                       "entidades_en_control": len({d["entity_ip"] for d in en_ctl})}}
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in politicas.items():
        c = v["control"]
        print(k, "entidades", len(c["entidades_con_restriccion_hipotetica"]), "intervalos",
              c["intervalos_restriccion_total"], "|", {e: r["cualquiera"]["V0_clases"]["antes_del_fin_bajo_supuestos"]
                                                       for e, r in v["resumen_por_escenario"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
