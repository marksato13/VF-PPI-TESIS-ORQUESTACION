#!/usr/bin/env python3
"""Población evaluada y excepciones de respuesta (preparación 3A, 2026-11-01).

Corrige la discrepancia de NUNCA_BLOQUEAR. Hasta ahora config-campana.json guardaba en
combinacion_real.exclusiones.NUNCA_BLOQUEAR cadenas con anotación ("10.10.10.20 (DNS/AD)"). analizar.py las usaba tal
cual como conjunto de exclusión del control y las comparaba con entity_ip exacto: ninguna coincidía, de modo que
nada se excluía (el DNS siempre estuvo en la población) y el fallo era silencioso. Además mezclaba dos conceptos:

  excepciones_respuesta   equipos que NO deben recibir restricciones (LIMIT/BLOCK). Es política de RESPUESTA: no
                          quita a la entidad de la población evaluada ni borra las señales del detector sobre ella.
  exclusiones_poblacion   entidades FUERA del alcance de una evaluación (no entran en el denominador). Cada una exige
                          una justificación explícita.

Formato nuevo (config["poblacion"]):
  {"excepciones_respuesta": [{"ip": "10.10.10.20", "nota": "DNS/AD"}, ...],
   "exclusiones_poblacion": [{"ip": "10.10.60.11", "justificacion": "..."}, ...]}
  - "ip": dirección IPv4/IPv6 o red CIDR estricta; sin anotaciones dentro del campo.
  - "nota" (excepciones) es opcional; "justificacion" (exclusiones) es obligatoria y no vacía.

Formato anterior (combinacion_real.exclusiones.NUNCA_BLOQUEAR, lista de cadenas "IP (anotación)"): se CONVIERTE de
forma explícita y documentada, en `conversion`:
  - cada cadena se separa en IP y anotación; la IP se valida;
  - todas pasan a excepciones_respuesta (era su significado: "nunca bloquear");
  - exclusiones_poblacion queda vacía (ninguna tiene justificación de exclusión), que es exactamente lo que el
    analizador hacía de hecho: los conteos del control NO cambian por esta corrección.
Una entrada mal formada aborta (ErrorPoblacion); nunca se ignora en silencio. Declarar los dos formatos a la vez
también aborta (ambigüedad).

Este módulo NO cambia la política del publicador (publicar_feed.py en el sensor tiene su propia lista y no lee
config-campana.json): solo define cómo el ANÁLISIS selecciona la población y anota las excepciones.
"""
from __future__ import annotations
import ipaddress
import re

LEGADO = ("combinacion_real", "exclusiones", "NUNCA_BLOQUEAR")
_CADENA_LEGADO = re.compile(r"^\s*([^\s()]+)\s*(?:\((.*)\))?\s*$")


class ErrorPoblacion(ValueError):
    pass


def _red(valor, donde: str):
    if not isinstance(valor, str) or not valor.strip() or valor != valor.strip():
        raise ErrorPoblacion(f"{donde}: 'ip' debe ser una cadena sin espacios ni anotaciones (es {valor!r})")
    try:
        return ipaddress.ip_network(valor, strict=True)
    except ValueError as ex:
        raise ErrorPoblacion(f"{donde}: dirección o red inválida {valor!r} ({ex})") from None


def _legado(cfg: dict):
    d = cfg
    for k in LEGADO:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def cargar_poblacion(cfg: dict) -> dict:
    """Devuelve {'formato', 'excepciones_respuesta', 'exclusiones_poblacion', 'conversion', '_redes_excluidas',
    '_redes_excepcion'}. Lanza ErrorPoblacion ante cualquier entrada mal formada."""
    nuevo, viejo = cfg.get("poblacion"), _legado(cfg)
    if nuevo is not None and viejo is not None:
        raise ErrorPoblacion("la config declara 'poblacion' y el formato anterior NUNCA_BLOQUEAR a la vez: ambiguo; "
                             "deja solo 'poblacion'")
    exc, excl, conv = [], [], []
    if nuevo is not None:
        if not isinstance(nuevo, dict):
            raise ErrorPoblacion("'poblacion' debe ser un objeto")
        desconocidas = set(nuevo) - {"excepciones_respuesta", "exclusiones_poblacion", "_nota"}
        if desconocidas:
            raise ErrorPoblacion(f"'poblacion' tiene claves desconocidas {sorted(desconocidas)}")
        for i, e in enumerate(nuevo.get("excepciones_respuesta", [])):
            donde = f"poblacion.excepciones_respuesta[{i}]"
            if not isinstance(e, dict):
                raise ErrorPoblacion(f"{donde}: debe ser objeto {{ip, nota}} (es {e!r}); las anotaciones van en 'nota'")
            exc.append({"ip": str(_red(e.get("ip"), donde)), "nota": e.get("nota")})
        for i, e in enumerate(nuevo.get("exclusiones_poblacion", [])):
            donde = f"poblacion.exclusiones_poblacion[{i}]"
            if not isinstance(e, dict):
                raise ErrorPoblacion(f"{donde}: debe ser objeto {{ip, justificacion}} (es {e!r})")
            j = e.get("justificacion")
            if not isinstance(j, str) or not j.strip():
                raise ErrorPoblacion(f"{donde}: exclusión de población sin justificación explícita")
            excl.append({"ip": str(_red(e.get("ip"), donde)), "justificacion": j.strip()})
        formato = "nuevo(poblacion)"
    elif viejo is not None:
        if not isinstance(viejo, list):
            raise ErrorPoblacion("NUNCA_BLOQUEAR (formato anterior) debe ser una lista")
        for i, s in enumerate(viejo):
            donde = f"NUNCA_BLOQUEAR[{i}]"
            m = _CADENA_LEGADO.match(s) if isinstance(s, str) else None
            if not m:
                raise ErrorPoblacion(f"{donde}: entrada mal formada {s!r}")
            red = _red(m.group(1), donde)
            nota = (m.group(2) or "").strip() or None
            exc.append({"ip": str(red), "nota": nota})
            conv.append({"entrada_original": s, "ip": str(red), "nota": nota, "destino": "excepciones_respuesta"})
        formato = "anterior(NUNCA_BLOQUEAR) convertido"
    else:
        formato = "ninguno (sin excepciones ni exclusiones)"
    dup = sorted({e["ip"] for e in exc} & {e["ip"] for e in excl})
    out = {"formato": formato, "excepciones_respuesta": exc, "exclusiones_poblacion": excl,
           "conversion": conv,
           "significado": {
               "excepciones_respuesta": "no reciben restricciones; SIGUEN en la población evaluada y sus señales "
                                        "del detector cuentan (una excepción de bloqueo no borra una señal)",
               "exclusiones_poblacion": "fuera del denominador de la evaluación, cada una con justificación"},
           "en_ambas_listas": dup,
           "_redes_excluidas": [ipaddress.ip_network(e["ip"]) for e in excl],
           "_redes_excepcion": [ipaddress.ip_network(e["ip"]) for e in exc]}
    if conv:
        out["conversion_regla"] = ("formato anterior: cada cadena 'IP (anotación)' -> excepciones_respuesta con la IP "
                                   "validada y la anotación en 'nota'; exclusiones_poblacion vacía (ninguna entrada "
                                   "traía justificación). Equivale a lo que el analizador hacía de hecho: no excluía "
                                   "a nadie.")
    return out


def _dentro(ip: str, redes) -> bool:
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(a in r for r in redes)


def excluida(ip: str, pob: dict) -> bool:
    """¿La entidad está fuera de la población evaluada? Solo por exclusiones_poblacion justificadas."""
    return _dentro(ip, pob["_redes_excluidas"])


def excepcion_respuesta(ip: str, pob: dict) -> bool:
    """¿La entidad tiene excepción de respuesta? (anotación; no la saca de la población)."""
    return _dentro(ip, pob["_redes_excepcion"])


def publico(pob: dict) -> dict:
    return {k: v for k, v in pob.items() if not k.startswith("_")}
