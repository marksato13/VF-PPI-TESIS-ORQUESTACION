#!/usr/bin/env python3
"""Extensión de `analizar_b` (NO lo modifica; se importa de `herramientas\\`) para la validación futura:
  - `e3_v2(ep, r2)`: E3 con la continuidad «SPAN o salida» (regla en CRITERIO-E3-SPAN-O-SALIDA.md). Sin `ep["intentos_salida"]` devuelve EXACTAMENTE lo que
    devuelve `analizar_b.e3` (así los resultados históricos de B2 no cambian). Con la serie de la salida, el criterio de «siguió intentando» se cumple si lo
    cumple el SPAN (SYN >= 50 % de B0) O la salida (intentos >= 50 % de su B0) en una racha de K bloques; el efecto se evalúa igual que en `analizar_b`.
  - `control_desde_transacciones(filas, restricciones)`: construye `ep["control"] = [{t, ok, atribuible}]` para E4 a partir del registro de transacciones.
Entrada `intentos_salida`: [{"t": segundo, "intentos": n}] (de analizar_intentos.series)."""
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "herramientas"))
import analizar_b as AB  # noqa: E402


BLOCK_ADMITE_SALIDA = False    # DECISIÓN DE MARK (11-nov): en los episodios BLOCK de esta corrida la ÚNICA fuente de continuidad es SPAN; la vía salida con hora solo rige en LIMIT.
                               # Con False, un episodio BLOCK se evalúa EXACTAMENTE con `analizar_b.e3` (SYN ≥ 1 por bloque, K=3, 0 respuestas) aunque haya `intentos_salida`;
                               # si SPAN no permite verificar la continuidad, el resultado es `indeterminado` (I2). La rama BLOCK+salida queda implementada pero desactivada.


def e3_v2(ep, r2):
    """LIMIT: «SPAN o salida». BLOCK: solo SPAN (delegado en `analizar_b.e3`) mientras BLOCK_ADMITE_SALIDA sea False. Sin `intentos_salida` (o sin punto de aplicación,
    o con E2 en fallo) delega EXACTAMENTE en `analizar_b.e3`."""
    acc = ep.get("accion_prevista")
    if acc not in ("LIMIT", "BLOCK") or "intentos_salida" not in ep or r2["resultado"] in ("fallo", "fallo_experimento"):
        return AB.e3(ep, r2)
    if acc == "BLOCK" and not BLOCK_ADMITE_SALIDA:
        return AB.e3(ep, r2)
    limit = acc == "LIMIT"
    t_fin, u, serie = AB.t_fin_eval(ep), AB._u(ep), ep.get("serie", [])
    t_apl, k = r2["t_apl_sup"], (AB.K_LIMIT if limit else AB.K_BLOCK)
    blq = [b for b in AB._bloques_desde(serie, math.ceil(t_apl)) if b["t"] + AB.BLOQUE <= t_fin]
    if AB._huecos(serie, ep["t_inicio"], t_fin) > AB.HUECOS_MAX:
        return AB._tope(r2, {"resultado": "indeterminado", "motivo": "I3 serie degradada (huecos > 10 %)"})
    b0 = b0_sal = None
    if limit:                                                                # LIMIT: referencia = media de los 10 bloques previos (≥ 5/s)
        previos = sorted((b for b in serie if b["t"] + AB.BLOQUE <= t_apl), key=lambda b: b["t"])[-AB.N_BASE:]
        if len(previos) < AB.N_BASE:
            return AB._tope(r2, {"resultado": "indeterminado", "motivo": "I5 sin línea base de 10 bloques"})
        b0 = sum(b["aceptadas"] for b in previos) / AB.N_BASE
        if b0 < AB.BASE_MIN:
            return AB._tope(r2, {"resultado": "indeterminado", "motivo": "I5 línea base demasiado baja", "b0": b0})
    if len(blq) < k:
        return AB._tope(r2, {"resultado": "indeterminado", "motivo": "I1 menos de %d bloques tras t_apl" % k})
    sal = {c["t"]: c["intentos"] for c in ep["intentos_salida"]}
    if limit:
        pre_sal = [sal.get(int(math.floor(t_apl)) - i, 0) for i in range(1, AB.N_BASE + 1)]
        b0_sal = sum(pre_sal) / AB.N_BASE
        umbral_syn, umbral_sal, lim, campo = AB.INTENTO_MIN * b0, AB.INTENTO_MIN * b0_sal, (1 - AB.THETA) * b0, "aceptadas"
    else:                                                                    # BLOCK: igual que `analizar_b.e3`: ≥ 1 intento por bloque (SPAN: SYN; salida: iteraciones con hora) y 0 respuestas
        umbral_syn, umbral_sal, lim, campo = 1, 1, 0, "resp"
    t_efecto, via, span_ok, sal_ok = None, None, False, False
    for i in range(len(blq) - k + 1):
        run = blq[i:i + k]
        i_span = all(b["syn"] >= umbral_syn for b in run)
        i_sal = (b0_sal > 0 if limit else True) and all(sal.get(int(b["t"]), 0) >= umbral_sal for b in run)
        span_ok, sal_ok = span_ok or i_span, sal_ok or i_sal                 # AMBAS vías se registran siempre, aunque el efecto ya se haya encontrado
        if t_efecto is None and (i_span or i_sal) and all(b[campo] <= lim for b in run):
            t_efecto, via = run[0]["t"], ("ambas" if i_span and i_sal else "span" if i_span else "salida")
    cont = {"span": span_ok, "salida": sal_ok, "b0_syn": b0, "b0_intentos_salida": b0_sal}
    if t_efecto is None and not (span_ok or sal_ok):
        return AB._tope(r2, {"resultado": "indeterminado", "motivo": "I2 el generador no siguió intentando %d bloques tras t_apl (ni SPAN ni salida)" % k, "continuidad": cont})
    if t_efecto is None:
        return {"resultado": "fallo", "motivo": "el generador siguió intentando y no se sostuvo el efecto", "b0": b0, "continuidad": cont}
    res = AB.comparar(t_efecto, t_efecto + AB.BLOQUE, t_fin, u)
    r3 = {"resultado": res, "motivo": "efecto sostenido %d bloques; continuidad por %s" % (k, via), "t_efecto": t_efecto, "b0": b0, "continuidad": cont, "via_continuidad": via}
    desc = AB.primer_descarte(ep, r2)
    r3["primer_descarte_host"] = desc
    if res == "cumple" and desc is None:
        r3.update(resultado="indeterminado", motivo="efecto en el SPAN sin contador de descartes de la regla en el host")
    return AB._tope(r2, r3)


def _restringida(restricciones, ip, t):
    return any(r["ip"] == ip and r["desde"] <= t <= r["hasta"] for r in restricciones)


def control_desde_transacciones(filas, restricciones):
    """filas: dicts con t_fin, origen, resultado, codigo, esperado. ok = sin excepción y sin 5xx no previsto; atribuible = fallo mientras el ORIGEN del
    cliente figuraba en un set restringido (restricciones: [{ip, desde, hasta}] de la traza del agente y las lecturas del set)."""
    out = []
    for f in filas:
        cod = f.get("codigo", "-")
        prevista = cod in str(f.get("esperado", "-")).split("|")
        inesperado = cod.isdigit() and int(cod) >= 500 and not prevista
        ok = not str(f.get("resultado", "ok")).startswith("excepcion") and not inesperado
        out.append({"t": float(f["t_fin"]), "ok": ok, "atribuible": (not ok) and _restringida(restricciones, f["origen"], float(f["t_fin"]))})
    return out


def leer_transacciones(ruta):
    cols = ["t_inicio", "t_fin", "perfil", "origen", "accion", "metodo", "ruta", "codigo", "resultado", "esperado", "latencia_ms"]
    out = []
    for l in open(ruta, encoding="utf-8"):
        if l.strip() and not l.startswith("#"):
            p = l.rstrip("\n").split("\t")
            if len(p) >= len(cols):
                out.append(dict(zip(cols, p)))
    return out
