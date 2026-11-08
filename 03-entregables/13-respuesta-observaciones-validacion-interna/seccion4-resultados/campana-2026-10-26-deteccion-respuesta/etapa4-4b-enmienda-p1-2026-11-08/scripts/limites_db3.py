#!/usr/bin/env python3
"""DB-3 (PROPUESTA, sin aprobar): límites operativos de falsas alertas del IF por α, con ventanas faltantes tratadas por COTAS.

Referencia ejecutable de las definiciones de DB-3-PROPUESTA.md. No lee datos del laboratorio y no forma parte del
análisis de la 4B hasta que Mark apruebe DB-3 y se publique con su hash.

Idea central: una ventana FALTANTE (no evaluada, ausente o fuera de la población principal: C1, C2, C3) no es ni ALERT ni
PERMIT: su estado se desconoce. Marcarlas todas como ALERT sería «conservador» solo para el tiempo en alerta (L2); para
los avisos (L1) puede UNIR dos avisos separados (menos avisos), es decir, favorecer al α. Por eso cada medida se acota entre
el mejor y el peor caso, y si el límite cae dentro de la cota el α queda «no_concluyente»: ni cumple ni se descarta.
"""
from __future__ import annotations

from typing import Iterable

SEPARACION_AVISO_S = 60.0   # dos ALERT forman el mismo aviso si entre ellas hay MENOS de 60 s (propuesta)
VENTANA_S = 10.0


def _grupos(ts: list[float], sep: float) -> list[list[float]]:
    out: list[list[float]] = []
    for t in sorted(ts):
        if out and t - out[-1][-1] < sep:
            out[-1].append(t)
        else:
            out.append([t])
    return out


def avisos_observados(alertas: Iterable[float], sep: float = SEPARACION_AVISO_S) -> int:
    """Avisos con solo las ALERT conocidas; las ventanas faltantes no cuentan como ALERT ni unen nada."""
    return len(_grupos(list(alertas), sep))


def cotas_avisos(alertas: Iterable[float], faltantes: Iterable[float], sep: float = SEPARACION_AVISO_S) -> dict:
    """Mínimo y máximo de avisos según el estado (desconocido) de las ventanas faltantes.

    mínimo: todas las faltantes ALERT; solo cuentan los avisos que contienen alguna ALERT conocida (las faltantes pueden unir).
    máximo: faltantes no unen; además cada faltante a ≥ sep de toda ALERT conocida puede formar un aviso propio
            (empaquetado voraz con separación ≥ sep entre ellos)."""
    O, M = sorted(set(alertas)), sorted(set(faltantes) - set(alertas))
    obs = avisos_observados(O, sep)
    union = _grupos(O + M, sep)
    conocidas = set(O)
    minimo = sum(1 for g in union if any(t in conocidas for t in g))
    libres = [m for m in M if all(abs(m - o) >= sep for o in O)]
    extra, ultimo = 0, None
    for m in libres:
        if ultimo is None or m - ultimo >= sep:
            extra += 1
            ultimo = m
    return {"observado": obs, "minimo": minimo, "maximo": obs + extra}


def cotas_tiempo(alertas_n: int, decididas_n: int, faltantes_n: int) -> dict:
    """Fracción de ventanas en ALERT: observada sobre las decididas; cotas con las faltantes todas PERMIT / todas ALERT."""
    d, m = decididas_n, faltantes_n
    return {"observado": (alertas_n / d) if d else None,
            "minimo": (alertas_n / (d + m)) if d + m else None,
            "maximo": ((alertas_n + m) / (d + m)) if d + m else None}


def decision(minimo: float | None, maximo: float | None, limite: float) -> str:
    """cumple (maximo ≤ límite) · no_cumple (minimo > límite) · no_concluyente (el límite cae dentro de la cota) · sin_dato."""
    if minimo is None or maximo is None:
        return "sin_dato"
    if maximo <= limite:
        return "cumple"
    if minimo > limite:
        return "no_cumple"
    return "no_concluyente"


def evaluar_entidad(alertas: list[float], decididas_n: int, alertas_n: int, faltantes: list[float],
                    horas_requeridas: float, l1_por_hora: float = 1.0, l2_fraccion: float = 0.10,
                    sep: float = SEPARACION_AVISO_S) -> dict:
    """L1 y L2 de una entidad y un α. ``horas_requeridas`` = ventanas requeridas × 10 s / 3600 (no depende de los resultados)."""
    ca = cotas_avisos(alertas, faltantes, sep)
    h = horas_requeridas
    l1 = {k: (v / h if h else None) for k, v in ca.items()}
    l1["decision"] = decision(l1["minimo"], l1["maximo"], l1_por_hora)
    l2 = cotas_tiempo(alertas_n, decididas_n, len(faltantes))
    l2["decision"] = decision(l2["minimo"], l2["maximo"], l2_fraccion)
    ds = (l1["decision"], l2["decision"])
    if "no_cumple" in ds:
        glob = "no_cumple"
    elif "no_concluyente" in ds or "sin_dato" in ds:
        glob = "no_concluyente"
    else:
        glob = "cumple"
    return {"L1_avisos_por_hora": l1, "L2_fraccion_en_alerta": l2, "decision": glob}


def veredicto_alfa(por_entidad: dict) -> dict:
    """Un α es elegible solo si TODAS las entidades de la población de selección cumplen de forma concluyente."""
    dec = {ip: e["decision"] for ip, e in por_entidad.items()}
    if any(d == "no_cumple" for d in dec.values()):
        v = "no_cumple"
    elif any(d != "cumple" for d in dec.values()):
        v = "no_concluyente"
    else:
        v = "cumple"
    return {"alfa": v, "entidades": dec, "elegible": v == "cumple"}


def elegir_alfa(veredictos: dict, episodios_a_tiempo: dict) -> dict:
    """Regla de DB-3 §5. veredictos {α: veredicto_alfa}; episodios_a_tiempo {α: n} (episodios C0 de la 4C detectados a tiempo).
    Entre los elegibles, el de más episodios; empate -> el α menor. Sin elegibles: «ninguno cumple» o «no concluyente»."""
    elegibles = [a for a, v in veredictos.items() if v["elegible"]]
    if elegibles:
        mejor = max(episodios_a_tiempo[a] for a in elegibles)
        empatados = sorted(a for a in elegibles if episodios_a_tiempo[a] == mejor)
        return {"resultado": "elegido", "alfa": min(empatados, key=float), "empate_entre": empatados}
    if any(v["alfa"] == "no_concluyente" for v in veredictos.values()):
        return {"resultado": "no_concluyente", "alfa": None,
                "nota": "algún α no cumple ni se descarta por la cobertura: no se elige ninguno ni se afirma que ninguno cumple"}
    return {"resultado": "ningun_alfa_cumple", "alfa": None,
            "nota": "el α desplegado sigue sin presentarse como elegido"}
