#!/usr/bin/env python3
"""Presupuesto temporal de extremo a extremo y simulación de la cadena de respuesta (SOLO LEE).

Etapa 1. No despliega, no ejecuta ataques y no toca ningún host. Reconstruye con los registros del paso 3B
(campaña A, en sombra) qué habría pasado si la cadena publicador -> relé -> agente hubiera estado activa:

  * t_det  : disponibilidad (registro_escrito_en del ciclo) de la PRIMERA ventana atribuible del episodio cuyo
             registro produce un veredicto según `_verdicto_de` del publicador DESPLEGADO (código extraído
             literalmente del fichero, no reescrito).
  * t_apl  : ESTIMADO. En el 3B el agente estaba inactivo (sombra): t_apl real = "no aplica". Se estima con las
             cadencias configuradas de los timers y las duraciones medidas, como intervalo [inferior, superior].
  * margen : t_fin_programado - t_apl. Antes / después / indeterminado (si el intervalo cruza el fin, o la
             diferencia cae dentro de la incertidumbre de relojes).

Simulaciones (todas con el código desplegado de `_verdicto_de` y `escalada.procesar`):
  * aislada  : por episodio, estado de escalada y kernel vacíos al inicio; solo decisiones del origen con
               window_end > inicio. Responde a "¿llega a tiempo la cadena si nada previo interfiere?".
  * secuencial: toda la sesión 3B tal cual, con el estado de escalada acumulado. Responde a "¿qué restricción
               estaría ya vigente al empezar cada episodio?" (contaminación entre episodios en la campaña B).
  * control  : intervalo de control normal declarado; restricciones que se habrían aplicado a cada entidad,
               por candidato α (umbral del IF) y por componente.

Variantes del presupuesto (todas ESTIMADAS, no medidas):
  V0  cadencias actuales (publicador :x0, relé :x3, agente :x6, cada 10 s, AccuracySec=1s).
  V1  cadena por eventos: publicador, relé y agente encadenados al escribirse el ciclo (sin esperar timers).
  V2  V1 + detección en el límite de la rejilla de 10 s: la ventana se decide nada más cerrarse, con la
      duración medida del ciclo que la decidió (sin espera de PCAP ni de ciclo). Cota inferior con las MISMAS
      ventanas y heurísticos: muestra lo que NO puede arreglar ninguna mejora de cadencia.
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

# --- Parámetros de cadencia. Cada valor lleva su clase: medido | configurado | estimado | desconocido ---
PARAM = {
    "pub_periodo_s": (10.0, "configurado", "ppi-publicar-feed.timer OnCalendar *:*:00/10"),
    "pub_fase_s": (0.0, "configurado", "ppi-publicar-feed.timer :00"),
    "pub_inicio_offset_s": (0.29, "medido", "journal 3B: 972 ejecuciones arrancan en :x0,29"),
    "pub_duracion_p50_s": (0.598, "medido", "3B, 972 ejecuciones"),
    "pub_duracion_max_s": (0.773, "medido", "3B, 972 ejecuciones"),
    "relay_fase_s": (3.0, "configurado", "ppi-relay-feed.timer *:*:03/10 (bastión)"),
    "relay_duracion_min_s": (1.065, "medido", "systemctl show en el bastión (muestras pocas)"),
    "relay_duracion_max_s": (1.612, "medido", "systemctl show en el bastión (muestras pocas)"),
    "agente_fase_s": (6.0, "configurado", "ppi-enforce-agent.timer *:*:06/10 (srv-dmz; INACTIVO en sombra)"),
    "agente_inicio_offset_max_s": (1.0, "configurado", "AccuracySec=1s; offset real del agente desconocido"),
    "agente_duracion_p50_s": (0.173, "medido", "octubre, 76 201 ejecuciones"),
    "agente_duracion_max_s": (0.564, "medido", "octubre, 76 201 ejecuciones"),
    "nft_activacion_s": (0.0, "desconocido", "tiempo entre el commit nft y el primer paquete descartado; "
                         "sin `counter` en las reglas no se puede medir"),
    "reloj_incertidumbre_s": (0.01, "medido", "relojes-3b.log: |desfase| <= 0,0036 s +- 0,0006 en los 4 hosts"),
}
P = {k: v[0] for k, v in PARAM.items()}


def iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds")


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def abrir(p: Path):
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else p.open(encoding="utf-8")


# --- Código desplegado, extraído literalmente -------------------------------------------------------------
def extraer_publicador(path: Path) -> tuple:
    """Devuelve (_verdicto_de, _SEVERIDAD, NUNCA) ejecutando SOLO esos nodos del fuente desplegado."""
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


def verdicto_alfa(d: dict, umbral: float | None, verdicto_desplegado, sev) -> tuple | None:
    """Veredicto con el IF a otro umbral α. umbral None = el desplegado tal cual."""
    if umbral is None:
        return verdicto_desplegado(d)
    cand = []
    det = str(d.get("detector_name", ""))
    if d.get("decision") == "ALERT" and det.endswith("_heuristic"):
        cand.append(("BLOCK", det, det))
    sc = d.get("score")
    if sc is not None and not det.endswith("_heuristic") and sc < umbral:
        cand.append(("LIMIT", "modelo:" + det, det))
    h = d.get("heuristico")
    if isinstance(h, dict) and h.get("accion") in sev:
        cand.append((h["accion"], "%s: %s" % (h.get("heuristico", "?"), h.get("motivo", "")),
                     str(h.get("heuristico", "heuristico"))))
    return max(cand, key=lambda c: sev[c[0]]) if cand else None


# --- Simulación de la cadena --------------------------------------------------------------------------------
class Cadena:
    """Publicador (ventana 120 s, más severo por IP, escalada) + agente (sets nft que nunca acortan)."""

    def __init__(self, escalada, verdicto, sev, nunca):
        self.esc, self.verdicto, self.sev, self.nunca = escalada, verdicto, sev, nunca
        self.estado: dict = {}
        self.kernel: dict = {}          # ip -> {"BLOCK": hasta, "LIMIT": hasta}
        self.aplicaciones: list = []    # (ip, accion, t_apl_inf, t_apl_sup, hasta, nivel, tick)

    def tick(self, T: float, decisiones: list[dict]):
        """T = instante :x0 del publicador. `decisiones` ordenadas por logged_at."""
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
        # El agente aplica en T + 6 (+ offset 0..1) + duración; el feed lleva hasta = ahora + timeout.
        t_inf = T + P["agente_fase_s"] + P["agente_duracion_p50_s"]
        t_sup = T + P["agente_fase_s"] + P["agente_inicio_offset_max_s"] + P["agente_duracion_max_s"]
        for ip, (acc, _mot, _det, la) in sorted(por_ip.items()):
            e = self.esc.procesar(self.estado, ip, acc, ahora, evento_ts=la)
            hasta = round(ahora + e["timeout_s"])
            k = self.kernel.setdefault(ip, {"BLOCK": 0.0, "LIMIT": 0.0})
            if acc == "LIMIT" and k["BLOCK"] > t_inf:
                continue                                     # LIMIT no degrada un BLOCK vivo
            if acc == "BLOCK":
                k["LIMIT"] = 0.0                             # el agente lo saca del set opuesto
            if hasta <= k[acc] + 1:
                continue                                     # no amplía: no hay aplicación nueva
            nueva = k[acc] <= t_inf                          # nueva restricción (no ampliación)
            k[acc] = hasta
            self.aplicaciones.append({"ip": ip, "accion": acc, "t_apl_inf": t_inf, "t_apl_sup": t_sup,
                                      "hasta": hasta, "nivel": e["nivel"], "nueva": nueva, "tick": T,
                                      "revisar_humano": e["revisar_humano"]})

    def vigente(self, ip: str, t: float) -> dict:
        k = self.kernel.get(ip, {"BLOCK": 0.0, "LIMIT": 0.0})
        return {a: (k[a] if k[a] > t else None) for a in ("BLOCK", "LIMIT")}


def ticks(desde: float, hasta: float):
    T = math.floor(desde / P["pub_periodo_s"]) * P["pub_periodo_s"] + P["pub_fase_s"]
    while T <= hasta:
        yield T
        T += P["pub_periodo_s"]


def correr(cadena: Cadena, decisiones: list[dict], desde: float, hasta: float, cortar=None):
    """Recorre los ticks. `decisiones` ordenadas por logged_at; se pasa solo el tramo útil."""
    i0 = 0
    for T in ticks(desde, hasta):
        ahora = T + P["pub_inicio_offset_s"]
        while i0 < len(decisiones) and float(decisiones[i0]["logged_at"]) < ahora - 120:
            i0 += 1
        cadena.tick(T, decisiones[i0:])
        if cortar and cortar(cadena):
            return


# --- Tick del publicador para un t_det dado (V0) ---------------------------------------------------------
def tick_publicador(t: float) -> tuple[float, float]:
    """(tick inferior, tick superior). Inferior: el publicador aún lee en su ejecución (hasta inicio+dur.max).
    Superior: el registro debe existir antes de que arranque (inicio medido)."""
    per, f = P["pub_periodo_s"], P["pub_fase_s"]
    base = math.floor((t - f) / per) * per + f
    inf = base if t <= base + P["pub_inicio_offset_s"] + P["pub_duracion_max_s"] else base + per
    sup = base if t <= base + P["pub_inicio_offset_s"] else base + per
    return inf, sup


def t_apl_v0(t_det: float) -> tuple[float, float]:
    inf, sup = tick_publicador(t_det)
    return (inf + P["agente_fase_s"] + P["agente_duracion_p50_s"],
            sup + P["agente_fase_s"] + P["agente_inicio_offset_max_s"] + P["agente_duracion_max_s"])


def t_apl_v1(t_det: float) -> tuple[float, float]:
    return (t_det + P["pub_duracion_p50_s"] + P["relay_duracion_min_s"] + P["agente_duracion_p50_s"],
            t_det + P["pub_duracion_max_s"] + P["relay_duracion_max_s"] + P["agente_duracion_max_s"])


def clasificar(fin: float, inf: float, sup: float) -> str:
    eps = P["reloj_incertidumbre_s"]
    if sup + eps < fin:
        return "antes_del_fin"
    if inf - eps > fin:
        return "despues_del_fin"
    return "indeterminado"


def dist(v: list[float]) -> dict | None:
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    return {"n": len(v), "min": round(v[0], 2), "mediana": round(statistics.median(v), 2),
            "max": round(v[-1], 2), "valores": [round(x, 2) for x in v]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", type=Path, required=True)
    ap.add_argument("--decisiones", type=Path, required=True, help="motor_decision.log(.gz) del 3B")
    ap.add_argument("--ciclos", type=Path, required=True)
    ap.add_argument("--analisis", type=Path, required=True, help="analisis-3b.json REVISADO (cadena v2)")
    ap.add_argument("--control", type=Path, required=True, help="control-declarado.json")
    ap.add_argument("--publicador", type=Path, required=True, help="publicar_feed.py DESPLEGADO")
    ap.add_argument("--escalada", type=Path, required=True, help="escalada.py DESPLEGADO")
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()

    verdicto, sev, nunca = extraer_publicador(a.publicador)
    escalada = cargar_escalada(a.escalada)
    an = json.loads(a.analisis.read_text(encoding="utf-8"))
    umbrales = {k: an["umbrales"][k] for k in ("IF_0.05", "IF_0.03", "IF_0.01")}

    ciclos = {}
    with abrir(a.ciclos) as fh:
        for l in fh:
            r = json.loads(l)
            if r.get("event") == "ciclo":
                ciclos[round(r["inicio_ciclo"], 4)] = r

    dec: list[dict] = []
    with abrir(a.decisiones) as fh:
        for l in fh:
            if '"event": "decision"' in l:
                dec.append(json.loads(l))
    dec.sort(key=lambda d: float(d["logged_at"]))
    kali = [d for d in dec if d.get("entity_ip") == ORIGEN]

    eps, ini, fin = {}, {}, {}
    with abrir(a.marcas) as fh:
        for l in fh:
            r = json.loads(l)
            if r.get("evento") == "inicio":
                ini[r["episodio_id"]] = r
            elif r.get("evento") == "fin":
                fin[r["episodio_id"]] = r
    orden = sorted(ini, key=lambda e: ts(ini[e]["reloj"]["pared_utc"]))

    # Horizonte programado: bucles de 90 s (bash SECONDS+90). nmap: duración natural; en la campaña A es la
    # observada; para la B se fija como referencia la MÍNIMA natural de la familia en A (ver PRESUPUESTO-TEMPORAL).
    durs_nat: dict[str, list[float]] = {}
    for e in orden:
        if ini[e]["escenario"].startswith("escaneo"):
            durs_nat.setdefault(ini[e]["escenario"], []).append(
                ts(fin[e]["reloj"]["pared_utc"]) - ts(ini[e]["reloj"]["pared_utc"]))

    # ---- Episodios ----
    sal_eps = []
    for e in orden:
        esc = ini[e]["escenario"]
        t0 = ts(ini[e]["reloj"]["pared_utc"])
        t_fin_obs = ts(fin[e]["reloj"]["pared_utc"])
        if esc.startswith("escaneo"):
            t_fin_prog, fuente_fin = t_fin_obs, "natural observado (sombra: no hubo corte)"
        else:
            t_fin_prog, fuente_fin = t0 + 90.0, "programado: bucle de 90 s"
        ve = an["episodios"][e]
        atrib = {w["window_end_utc"]: w for w in ve["ventanas"]}
        primeras = {}
        for d in sorted(kali, key=lambda d: d["window_end_utc"]):
            w = atrib.get(d["window_end_utc"])
            if not w or w.get("atribucion") != "atribuible":
                continue
            v = verdicto(d)
            if v is None:
                continue
            disp = ts(w["disponible_utc"])
            cyc = ciclos.get(round(d["inicio_ciclo"], 4))
            reg = {"window_end_utc": d["window_end_utc"], "accion": v[0], "motivo": v[1],
                   "t_det_utc": iso(disp), "logged_at_utc": iso(float(d["logged_at"])),
                   "disponibilidad_fuente": w.get("disponibilidad_fuente"),
                   "t_det_menos_inicio_s": round(disp - t0, 2),
                   "duracion_ciclo_s": cyc["duracion_s"] if cyc else None}
            for clave in ("cualquiera", v[0]):
                if clave not in primeras or disp < ts(primeras[clave]["t_det_utc"]):
                    primeras[clave] = reg
        res = {"episodio": e, "escenario": esc, "en_poblacion_principal_v2": ve["en_poblacion_principal"],
               "t_inicio_utc": iso(t0), "t_fin_programado_utc": iso(t_fin_prog), "fuente_fin": fuente_fin,
               "t_fin_observado_utc": iso(t_fin_obs), "duracion_observada_s": round(t_fin_obs - t0, 2),
               "t_apl_real": "no aplica (sombra: agente inactivo)", "t_efecto_real": "no aplica (sombra)"}
        for clave in ("cualquiera", "LIMIT", "BLOCK"):
            p = primeras.get(clave)
            if not p:
                res["primera_" + clave] = None
                continue
            td = ts(p["t_det_utc"])
            v0 = t_apl_v0(td)
            v1 = t_apl_v1(td)
            w_end = ts(p["window_end_utc"])
            v2_det = w_end + (p["duracion_ciclo_s"] or 0)
            v2 = t_apl_v1(v2_det)
            res["primera_" + clave] = dict(p, **{
                "V0": {"t_apl_inf_utc": iso(v0[0]), "t_apl_sup_utc": iso(v0[1]),
                       "t_apl_menos_t_det_s": [round(v0[0] - td, 2), round(v0[1] - td, 2)],
                       "t_apl_menos_inicio_s": [round(v0[0] - t0, 2), round(v0[1] - t0, 2)],
                       "margen_s": [round(t_fin_prog - v0[1], 2), round(t_fin_prog - v0[0], 2)],
                       "clase": clasificar(t_fin_prog, *v0)},
                "V1": {"t_apl_menos_inicio_s": [round(v1[0] - t0, 2), round(v1[1] - t0, 2)],
                       "margen_s": [round(t_fin_prog - v1[1], 2), round(t_fin_prog - v1[0], 2)],
                       "clase": clasificar(t_fin_prog, *v1)},
                "V2": {"t_det_menos_inicio_s": round(v2_det - t0, 2),
                       "t_apl_menos_inicio_s": [round(v2[0] - t0, 2), round(v2[1] - t0, 2)],
                       "margen_s": [round(t_fin_prog - v2[1], 2), round(t_fin_prog - v2[0], 2)],
                       "clase": clasificar(t_fin_prog, *v2)},
                "senal_antes_del_fin_programado": td < t_fin_prog,
                "ventana_cierra_antes_del_fin": w_end < t_fin_prog})
        # Simulación aislada (código desplegado, decisiones del origen con window_end > inicio)
        sub = [d for d in kali if ts(d["window_end_utc"]) > t0 and float(d["logged_at"]) >= t0]
        cad = Cadena(escalada, verdicto, sev, nunca)
        correr(cad, sub, t0, t0 + 400)
        ap_ = [x for x in cad.aplicaciones if x["ip"] == ORIGEN]
        prim = ap_[0] if ap_ else None
        prim_b = next((x for x in ap_ if x["accion"] == "BLOCK"), None)
        res["simulacion_aislada"] = {
            "primera_aplicacion": None if not prim else {
                "accion": prim["accion"], "t_apl_inf_utc": iso(prim["t_apl_inf"]),
                "t_apl_sup_utc": iso(prim["t_apl_sup"]),
                "t_apl_menos_inicio_s": [round(prim["t_apl_inf"] - t0, 2), round(prim["t_apl_sup"] - t0, 2)],
                "clase": clasificar(t_fin_prog, prim["t_apl_inf"], prim["t_apl_sup"])},
            "primer_block": None if not prim_b else {
                "t_apl_menos_inicio_s": [round(prim_b["t_apl_inf"] - t0, 2), round(prim_b["t_apl_sup"] - t0, 2)],
                "nivel": prim_b["nivel"], "hasta_menos_inicio_s": round(prim_b["hasta"] - t0, 1),
                "clase": clasificar(t_fin_prog, prim_b["t_apl_inf"], prim_b["t_apl_sup"])},
            "nota": "decisiones del origen con window_end > inicio, incluidas las NO atribuibles: el publicador "
                    "no conoce la atribución; la comparación con 'primera_*' muestra si la acción la provoca el ataque"}
        sal_eps.append(res)

    # ---- Simulación secuencial de la sesión completa (contaminación entre episodios) ----
    cad_s = Cadena(escalada, verdicto, sev, nunca)
    t_ini_ses = float(dec[0]["logged_at"])
    t_fin_ses = float(dec[-1]["logged_at"])
    correr(cad_s, dec, t_ini_ses, t_fin_ses)
    estado_por_ep = []
    for e in orden:
        t0 = ts(ini[e]["reloj"]["pared_utc"])
        prev = [x for x in cad_s.aplicaciones if x["ip"] == ORIGEN and x["t_apl_sup"] <= t0]
        vig_block = max((x["hasta"] for x in prev if x["accion"] == "BLOCK"), default=0)
        vig_limit = max((x["hasta"] for x in prev if x["accion"] == "LIMIT"), default=0)
        nivel = max((x["nivel"] for x in prev), default=0)
        estado_por_ep.append({"episodio": e, "t_inicio_utc": iso(t0),
                              "block_vigente_al_inicio": vig_block > t0,
                              "block_restante_s": round(vig_block - t0, 1) if vig_block > t0 else 0,
                              "limit_vigente_al_inicio": vig_limit > t0 and vig_block <= t0,
                              "nivel_escalada_previo": nivel})
    estado_final_kali = cad_s.estado.get(ORIGEN)

    # ---- Control normal: restricciones que se habrían aplicado, por α ----
    ctl = json.loads(a.control.read_text(encoding="utf-8"))["control_normal"]
    c0, c1 = ts(ctl["desde"]), ts(ctl["hasta"])
    en_ctl = [d for d in dec if c0 <= ts(d["window_end_utc"]) <= c1]
    claves_ctl = {(d["entity_ip"], d["window_end_utc"]) for d in en_ctl}
    sal_ctl = {"intervalo_utc": [ctl["desde"], ctl["hasta"]], "duracion_s": c1 - c0,
               "ventanas_decididas": len(claves_ctl),
               "nota": "las señales cuentan TODAS las entidades (el DNS 10.10.10.20 incluido); las propuestas y "
                       "restricciones excluyen NUNCA_BLOQUEAR porque el publicador no las emite"}
    for nombre, umbral in [("desplegado", None)] + list(umbrales.items()):
        vfun = (lambda d, u=umbral: verdicto_alfa(d, u, verdicto, sev))
        vistos = set()
        senales = {"ventanas_con_veredicto": 0}
        senal_por_ent: dict = {}
        senal_ts: dict = {}
        for d in en_ctl:
            k = (d["entity_ip"], d["window_end_utc"])
            if k in vistos:
                continue
            vistos.add(k)
            v = vfun(d)
            if v is None:
                continue
            senales["ventanas_con_veredicto"] += 1
            # Componentes por separado (una ventana puede tener modelo Y heurístico)
            det = str(d.get("detector_name", ""))
            sc = d.get("score")
            comp = []
            if umbral is None:
                if d.get("decision") == "ALERT":
                    comp.append("BLOCK_legacy" if det.endswith("_heuristic") else "LIMIT_modelo")
            else:
                if d.get("decision") == "ALERT" and det.endswith("_heuristic"):
                    comp.append("BLOCK_legacy")
                if sc is not None and not det.endswith("_heuristic") and sc < umbral:
                    comp.append("LIMIT_modelo")
            h = d.get("heuristico")
            if isinstance(h, dict) and h.get("accion") in sev:
                comp.append("%s_heuristico:%s" % (h["accion"], h.get("heuristico", "?")))
            senal_ts.setdefault(d["entity_ip"], []).append(ts(d["window_end_utc"]))
            for tipo in comp:
                senales[tipo] = senales.get(tipo, 0) + 1
                senal_por_ent.setdefault(d["entity_ip"], {}).setdefault(tipo, 0)
                senal_por_ent[d["entity_ip"]][tipo] += 1
        # Incidentes de SEÑAL: ventanas con veredicto de la misma entidad separadas <= 120 s (la separación de
        # episodio de la escalada) forman un incidente; así se distinguen ventanas repetidas de incidentes.
        inc_senal = {}
        for ip, lst in senal_ts.items():
            lst.sort()
            inc_senal[ip] = 1 + sum(1 for x, y in zip(lst, lst[1:]) if y - x > 120)
        cad_c = Cadena(escalada, vfun, sev, nunca)
        sub = [d for d in dec if c0 - 130 <= float(d["logged_at"])
               and ts(d["window_end_utc"]) <= c1 + 0]     # decisiones del control (y su historia de 120 s)
        correr(cad_c, sub, c0, c1)
        por_ent: dict = {}
        for x in cad_c.aplicaciones:
            pe = por_ent.setdefault(x["ip"], {"aplicaciones_nuevas": 0, "ampliaciones": 0, "BLOCK": 0,
                                              "intervalos": []})
            pe["aplicaciones_nuevas" if x["nueva"] else "ampliaciones"] += 1
            pe["BLOCK"] += x["accion"] == "BLOCK"
            ini_r = max(x["t_apl_inf"], c0)
            fin_r = min(x["hasta"], c1)
            if fin_r > ini_r:
                iv = pe["intervalos"]
                if iv and ini_r <= iv[-1][1]:
                    iv[-1][1] = max(iv[-1][1], fin_r)
                else:
                    iv.append([ini_r, fin_r])
        for ip, pe in por_ent.items():
            pe["incidentes_restriccion"] = len(pe["intervalos"])
            pe["segundos_restringida"] = round(sum(b - a for a, b in pe["intervalos"]), 1)
            pe["fraccion_control_restringida"] = round(pe["segundos_restringida"] / (c1 - c0), 3)
            pe["intervalos"] = [[iso(a_), iso(b_)] for a_, b_ in pe["intervalos"]]
        n_ent = len({d["entity_ip"] for d in en_ctl})
        sal_ctl[nombre] = {
            "umbral": umbral if umbral is not None else an["umbrales"]["desplegado"],
            "senales_ventanas": senales,
            "tasa_ventanas_con_veredicto": round(senales["ventanas_con_veredicto"] / len(claves_ctl), 4),
            "senales_por_entidad": senal_por_ent,
            "incidentes_senal_por_entidad": inc_senal,
            "incidentes_senal_total": sum(inc_senal.values()),
            "incidentes_senal_sin_nunca_bloquear": sum(v for k, v in inc_senal.items() if k not in nunca),
            "entidades_en_control": n_ent,
            "entidades_restringidas": sorted(por_ent),
            "restricciones_por_entidad": por_ent,
            "aplicaciones_nuevas_total": sum(p["aplicaciones_nuevas"] for p in por_ent.values()),
            "incidentes_total": sum(p["incidentes_restriccion"] for p in por_ent.values()),
            "incidentes_por_hora": round(sum(p["incidentes_restriccion"] for p in por_ent.values())
                                         / ((c1 - c0) / 3600), 2),
            "fallos_transacciones_legitimas": "no medible en sombra (agente inactivo): requiere activación "
                                              "controlada con medición en los clientes"}

    # ---- Resumen por escenario (distribuciones de valores POR EPISODIO; nunca suma de medianas) ----
    resumen = {}
    for esc in sorted({x["escenario"] for x in sal_eps}):
        xs = [x for x in sal_eps if x["escenario"] == esc]
        r = {"episodios": len(xs), "en_poblacion_v2": sum(x["en_poblacion_principal_v2"] for x in xs),
             "duracion_observada_s": dist([x["duracion_observada_s"] for x in xs])}
        for clave in ("cualquiera", "BLOCK"):
            ok = [x["primera_" + clave] for x in xs if x["primera_" + clave]]
            r[clave] = {
                "con_senal_atribuible": len(ok),
                "t_det_menos_inicio_s": dist([p["t_det_menos_inicio_s"] for p in ok]),
                "V0_t_apl_menos_inicio_sup_s": dist([p["V0"]["t_apl_menos_inicio_s"][1] for p in ok]),
                "V0_margen_inf_s": dist([p["V0"]["margen_s"][0] for p in ok]),
                "V0_clases": {c: sum(p["V0"]["clase"] == c for p in ok)
                              for c in ("antes_del_fin", "indeterminado", "despues_del_fin")},
                "V1_clases": {c: sum(p["V1"]["clase"] == c for p in ok)
                              for c in ("antes_del_fin", "indeterminado", "despues_del_fin")},
                "V2_clases": {c: sum(p["V2"]["clase"] == c for p in ok)
                              for c in ("antes_del_fin", "indeterminado", "despues_del_fin")},
                "ventana_cierra_antes_del_fin": sum(p["ventana_cierra_antes_del_fin"] for p in ok)}
        resumen[esc] = r

    out = {"herramienta": "presupuesto_e2e.py", "solo_lectura": True,
           "entradas_sha256": {k: sha(getattr(a, k)) for k in
                               ("marcas", "decisiones", "ciclos", "analisis", "control", "publicador", "escalada")},
           "parametros": {k: {"valor": v[0], "clase": v[1], "fuente": v[2]} for k, v in PARAM.items()},
           "duraciones_naturales_nmap_s": {k: [round(x, 2) for x in v] for k, v in durs_nat.items()},
           "resumen_por_escenario": resumen, "episodios": sal_eps,
           "secuencial": {"estado_al_inicio_de_cada_episodio": estado_por_ep,
                          "estado_escalada_final_origen": estado_final_kali,
                          "aplicaciones_origen": len([x for x in cad_s.aplicaciones if x["ip"] == ORIGEN])},
           "control": sal_ctl}
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
