import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(encoding="utf-8")


def reemplazar(ini_pat, fin_pat, nuevo):
    global s
    i = s.index(ini_pat); j = s.index(fin_pat, i)
    s = s[:i] + nuevo + s[j:]


reemplazar("def estado_ventana(", "def _q(v, p):", '''def _ep(k) -> float:
    return an.ep_iso(k[1])


def estado_referencia(k, inv) -> str:
    """Estado de la clave en la repetición offline: decision | no_evaluada | sin_registro."""
    if inv is None:
        return "sin_inventario"
    if k in inv["esperadas"]:
        return "decision"
    if k in inv["no_evaluadas_en_referencia"]:
        return "no_evaluada"
    return "sin_registro"


def requeridas_inventario(inv, excluida=lambda ip: False, desde=None, hasta=None) -> set:
    """Ventanas requeridas por el inventario: TODA clave registrada por la repetición (decisión o ventana_no_evaluada)
    dentro del rango. Una ventana que la repetición no pudo evaluar sigue siendo requerida: no sale del denominador
    (corrección 3A-2, 2026-11-01)."""
    ks = set(inv["esperadas"]) | set(inv["no_evaluadas_en_referencia"])
    lo = inv["desde"] if desde is None else max(desde, inv["desde"])
    hi = inv["hasta"] if hasta is None else min(hasta, inv["hasta"])
    return {k for k in ks if lo <= _ep(k) <= hi and not excluida(k[0])}


def estado_ventana(k, vivo: dict, ne_vivo: dict, inv: dict | None, requerida: bool = False) -> str:
    """Estado de una clave entity_ip|window_end. vivo/ne_vivo: dicts clave -> registro.
    requerida=True: la clave pertenece a la rejilla del episodio aunque la repetición no la registrara."""
    ref = estado_referencia(k, inv)
    if k in vivo:
        r = vivo[k]
        if (inv is not None and not requerida and ref == "sin_registro"
                and inv["desde"] <= r["_wend"] <= inv["hasta"]):
            return "solo_en_vivo"
        return "decidida_a_tiempo" if r["_disp"] - r["_wend"] <= PUNTUALIDAD_S else "decidida_tardia"
    if k in ne_vivo:
        return "no_evaluada"
    if inv is None or not (inv["desde"] <= _ep(k) <= inv["hasta"]):
        return "evidencia_insuficiente"
    return "ausente" if (requerida or ref != "sin_registro") else "evidencia_insuficiente"


def inventario_resumen(inv, vivo, ne_vivo, excluida) -> dict:
    if inv is None:
        return {"disponible": False, "motivo": "sin --inventario/--inventario-rango: no se puede afirmar que no "
                                               "falten ventanas (estado evidencia_insuficiente)"}
    req = requeridas_inventario(inv, excluida)
    vivo_r = {k for k, r in vivo.items() if inv["desde"] <= r["_wend"] <= inv["hasta"] and not excluida(k[0])}
    est = {k: estado_ventana(k, vivo, ne_vivo, inv) for k in req}
    cnt = Counter(est.values())
    solo = vivo_r - req
    dec = [k for k in req if k in vivo]
    ret = sorted(vivo[k]["_disp"] - vivo[k]["_wend"] for k in dec)
    ne_ref = [k for k in req if estado_referencia(k, inv) == "no_evaluada"]
    return {"disponible": True, "fuente": inv["fuente"], "sha256": inv["sha256"],
            "rango_window_end_utc": [an.iso(inv["desde"]), an.iso(inv["hasta"])],
            "requeridas": len(req),
            "requeridas_definicion": "claves con decisión O ventana_no_evaluada en la repetición offline, dentro del "
                                     "rango; una no evaluada en la referencia sigue siendo requerida",
            "estados": {e: cnt.get(e, 0) for e in ("decidida_a_tiempo", "decidida_tardia", "no_evaluada", "ausente")},
            "decididas_en_vivo": len(dec),
            "cobertura_total": round(len(dec) / len(req), 6) if req else None,
            "no_evaluadas_en_referencia": {
                "total": len(ne_ref),
                "decididas_en_vivo": sum(1 for k in ne_ref if k in vivo),
                "no_evaluadas_en_vivo": sum(1 for k in ne_ref if est[k] == "no_evaluada"),
                "ausentes_en_vivo": sum(1 for k in ne_ref if est[k] == "ausente")},
            "solo_en_vivo": len(solo),
            "solo_en_vivo_nota": "decididas en vivo sin registro en la referencia: se informan, fuera del denominador",
            "puntualidad": {"limite_s": PUNTUALIDAD_S,
                            "a_tiempo": cnt.get("decidida_a_tiempo", 0), "tardias": cnt.get("decidida_tardia", 0),
                            "retraso_disponibilidad_s": {"p50": _q(ret, .5), "p95": _q(ret, .95),
                                                         "max": ret[-1] if ret else None}},
            "alcance": "la repetición offline procesa los MISMOS PCAP/EVE: detecta ventanas que el motor en vivo no "
                       "decidió, no pérdidas del SPAN/tcpdump/Suricata; coincidir con ella no prueba que una fuente "
                       "degradada no tuviera efecto",
            "ejemplos_sin_decision": sorted(f"{k[0]}|{k[1]}|{est[k]}" for k in req if k not in vivo)[:20],
            "ejemplos_solo_en_vivo": sorted(f"{k[0]}|{k[1]}" for k in solo)[:20]}


''')

reemplazar("def ventanas_esperadas_episodio(", "def clasificar_3b(", '''def anclas_rejilla(desde_abierto: float, hasta_abierto: float) -> list:
    """window_end de la rejilla de PASO_S (múltiplos de 10 s en epoch) con desde < w < hasta, AMBOS abiertos."""
    a = math.floor(desde_abierto / an.PASO_S) * an.PASO_S + an.PASO_S      # > desde aunque desde esté en la rejilla
    out = []
    while a < hasta_abierto:
        out.append(float(a)); a += an.PASO_S
    return out


def ventanas_esperadas_episodio(ep, origen, inv, vivo, ne_vivo=None) -> tuple:
    """Ventanas REQUERIDAS del episodio: toda ancla de la rejilla con window_end en (inicio, fin+60), abierta en ambos
    extremos (su intervalo (w-60, w] solapa [inicio, fin]). No se toman solo de las decisiones del inventario: una
    ventana no evaluada o ausente en la referencia sigue siendo requerida. No hay exclusiones definidas.
    Devuelve (claves, cobertura_inventario).
    Corrección 3A-1 (2026-11-01): antes se comprobaba fin+60 <= hasta+60 (cierto siempre que fin <= hasta) y las
    claves salían solo de las decisiones del inventario, de modo que un inventario truncado o una ventana no evaluada
    en ambas versiones reducían el denominador sin dejar rastro."""
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    anc = anclas_rejilla(ini, fin + HORIZONTE_S)
    conocidas = set(vivo) | set(ne_vivo or {})
    if inv is not None:
        conocidas |= set(inv["esperadas"]) | set(inv["no_evaluadas_en_referencia"])
    idx = {(k[0], int(round(_ep(k)))): k for k in conocidas if k[0] == origen}
    claves = [idx.get((origen, int(a)), (origen, an.iso(a))) for a in anc]
    if inv is None:
        cob = {"cubre": False, "motivo": "sin inventario"}
    else:
        fuera = [an.iso(a) for a in anc if not (inv["desde"] <= a <= inv["hasta"])]
        cob = {"cubre": bool(anc) and not fuera, "primera_requerida_utc": an.iso(anc[0]) if anc else None,
               "ultima_requerida_utc": an.iso(anc[-1]) if anc else None,
               "inventario_utc": [an.iso(inv["desde"]), an.iso(inv["hasta"])], "fuera_del_inventario": fuera}
    return claves, cob


''')

reemplazar("    esp, origen_inv = ventanas_esperadas_episodio(ep, origen, inv, vivo)\n", "    completa = not motivos\n", '''    esp, cob_inv = ventanas_esperadas_episodio(ep, origen, inv, vivo, ne_vivo)
    estados = {k: estado_ventana(k, vivo, ne_vivo, inv, requerida=True) for k in esp}
    decididas = [k for k in esp if k in vivo]
    sin_dest = [k for k in decididas if destinos is None or (eid, k[1]) not in destinos]
    cal = (calidad or {}).get(eid, {}).get("estado") if calidad is not None else None
    motivos = []
    if inv is None:
        motivos.append("sin inventario: no se puede establecer que no falten ventanas")
    elif not cob_inv["cubre"]:
        motivos.append(f"el inventario no cubre {len(cob_inv['fuera_del_inventario'])}/{len(esp)} ventanas requeridas "
                       f"(requeridas {cob_inv['primera_requerida_utc']} .. {cob_inv['ultima_requerida_utc']}; "
                       f"inventario {cob_inv['inventario_utc'][0]} .. {cob_inv['inventario_utc'][1]})")
    if not esp:
        motivos.append("ninguna ventana requerida")
    falt = [k for k in esp if k not in vivo]
    if falt:
        motivos.append(f"{len(falt)}/{len(esp)} ventanas requeridas sin decisión ("
                       + ", ".join(f"{e}={n}" for e, n in sorted(Counter(estados[k] for k in falt).items())) + ")")
    if sin_dest:
        motivos.append(f"{len(sin_dest)} ventanas decididas sin evidencia de destino")
    if cal != "completa":
        motivos.append(f"fuente {cal or 'sin evaluar (no se aportó --calidad-fuentes)'}")
    if integridad is not True:
        motivos.append("integridad " + ("desconocida" if integridad is None else "no apta"))
''')
a = '''        v = {"window_end_utc": k[1], "estado": estados[k], "atribucion": st}'''
assert a in s
s = s.replace(a, '''        v = {"window_end_utc": k[1], "estado": estados[k], "estado_referencia": estado_referencia(k, inv),
             "atribucion": st}''')
a = '''    res = {"ventanas_esperadas": len(esp), "origen_ventanas": origen_inv,'''
assert a in s
s = s.replace(a, '''    res = {"ventanas_esperadas": len(esp), "ventanas_requeridas": len(esp), "cobertura_inventario": cob_inv,''')

reemplazar("def control_3b(", "# ------------------------------------------------------------------- principal", '''def _fa(regs, U) -> dict:
    return {c: sum(1 for r in regs if an.senales(r, U)[c]) for c in CONFIGS}


def _tramos_fuera(desde, hasta, lo, hi) -> list:
    """Partes de [desde, hasta] fuera de [lo, hi] (en la rejilla de 10 s, sin solaparse con el tramo cubierto)."""
    t = []
    if desde < lo:
        t.append((desde, min(hasta, lo - an.PASO_S)))
    if hasta > hi:
        t.append((max(desde, hi + an.PASO_S), hasta))
    return [(a, b) for a, b in t if a <= b]


def control_3b(vivo, ne_vivo, inv, desde, hasta, U, pob) -> dict:
    """Control normal. Corrección 3A-2 (2026-11-01): población e intervalo coherentes.
    - tramo_cubierto = [desde, hasta] ∩ rango del inventario. Población = ventanas REQUERIDAS por el inventario
      (decisión o no evaluada en la referencia) salvo exclusiones de población justificadas. Falsas alarmas y tasa
      sobre las requeridas decididas en vivo; cotas sobre TODAS las requeridas (sin decisión: todas negativas / todas
      positivas). Las decididas solo en vivo se informan fuera del denominador.
    - tramos_sin_inventario: parte declarada fuera del rango del inventario. Se informa lo decidido en vivo, con
      cobertura NO determinable; no recibe la cobertura del tramo cubierto ni entra en sus cotas.
    - historico_fpr_control: analizar.fpr_control sobre todo [desde, hasta] (solo ventanas decididas), únicamente
      para comparar con la primera campaña A."""
    exc = lambda ip: poblacion.excluida(ip, pob)  # noqa: E731
    regs = list(vivo.values())
    out = {"intervalo_declarado_utc": [an.iso(desde), an.iso(hasta)],
           "historico_fpr_control": an.fpr_control(regs, desde, hasta, U, pob, list(ne_vivo.values())),
           "umbral_cobertura": "no se adopta un umbral automático (p. ej. 90 %): la tasa se publica con su "
                               "cobertura y sus cotas"}

    def bloque_vivo(a, b):
        v = [r for r in regs if a <= r["_wend"] <= b and not exc(r["entity_ip"])]
        n = len(v); fa = _fa(v, U)
        return {"intervalo_utc": [an.iso(a), an.iso(b)], "decididas_en_vivo": n,
                "no_evaluadas_en_vivo": sum(1 for e in ne_vivo.values() if a <= e["_wend"] <= b
                                            and not exc(e["entity_ip"])),
                "cobertura": "no determinable (fuera del inventario)",
                **{c: {"falsas_alarmas": fa[c], "tasa_entre_decididas": round(fa[c] / n, 6) if n else None}
                   for c in CONFIGS}}
    if inv is None:
        out["tramo_cubierto"] = None
        out["tramos_sin_inventario"] = [bloque_vivo(desde, hasta)]
    else:
        lo, hi = max(desde, inv["desde"]), min(hasta, inv["hasta"])
        if lo > hi:
            out["tramo_cubierto"] = None
        else:
            req = requeridas_inventario(inv, exc, lo, hi)
            dec = [vivo[k] for k in req if k in vivo]
            n, N = len(dec), len(req)
            falt = N - n
            fa = _fa(dec, U)
            est = Counter(estado_ventana(k, vivo, ne_vivo, inv) for k in req if k not in vivo)
            solo = [k for k, r in vivo.items() if lo <= r["_wend"] <= hi and not exc(k[0]) and k not in req]
            out["tramo_cubierto"] = {
                "intervalo_utc": [an.iso(lo), an.iso(hi)], "requeridas": N, "decididas": n,
                "sin_decision": falt, "sin_decision_por_estado": dict(est),
                "no_evaluadas_en_referencia": sum(1 for k in req if estado_referencia(k, inv) == "no_evaluada"),
                "cobertura_total": round(n / N, 6) if N else None,
                "solo_en_vivo_fuera_del_denominador": len(solo),
                **{c: {"falsas_alarmas": fa[c], "tasa_entre_decididas": round(fa[c] / n, 6) if n else None,
                       "cotas_sobre_requeridas": {"min": round(fa[c] / N, 6) if N else None,
                                                  "max": round((fa[c] + falt) / N, 6) if N else None}}
                   for c in CONFIGS},
                "regla": "denominador de las cotas = requeridas del tramo; las sin decisión no se suponen "
                         "negativas ni positivas"}
        out["tramos_sin_inventario"] = [bloque_vivo(a, b) for a, b in
                                        _tramos_fuera(desde, hasta, inv["desde"], inv["hasta"])]
    out["control_dentro_del_inventario"] = bool(out["tramo_cubierto"]) and not out["tramos_sin_inventario"]
    por_ent = defaultdict(lambda: {"ventanas": 0, **{c: 0 for c in CONFIGS}})
    for r in regs:
        if desde <= r["_wend"] <= hasta and not exc(r["entity_ip"]):
            e = por_ent[r["entity_ip"]]; e["ventanas"] += 1
            g = an.senales(r, U)
            for c in CONFIGS:
                e[c] += bool(g[c])
    out["por_entidad"] = {ip: {**v, "excepcion_respuesta": poblacion.excepcion_respuesta(ip, pob)}
                          for ip, v in sorted(por_ent.items())}
    out["por_entidad_nota"] = "ventanas decididas en vivo en todo el intervalo declarado"
    return out


''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
