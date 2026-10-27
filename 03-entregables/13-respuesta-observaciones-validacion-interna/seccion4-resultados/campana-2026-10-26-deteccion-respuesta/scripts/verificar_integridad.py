#!/usr/bin/env python3
"""Verificador de integridad de fuentes por campaña/episodio (lo consulta analizar.py antes de declarar evaluable).

Distingue DECLARACIONES de VERIFICACIONES. Un booleano o número escrito en el descriptor NO es una verificación.
Cada requisito tiene un estado:
  - "verificado"              comprobado desde ficheros/registros accesibles (hash real, o lectura de un RESPALDO
                              que corresponde al episodio) o por un INFORME EXTERNO accesible y trazable
  - "declarado_sin_verificar" el descriptor afirma un valor pero SIN respaldo accesible que lo sustente
  - "ausente"                 el recurso/respaldo requerido falta, no es legible, o su contenido NO corresponde
  - "desconocido"             no hay ni afirmación ni respaldo: nada que comprobar
Solo "verificado" cuenta para 'apto'.

RESPALDO (para cobertura, continuidad, faltantes, captura, reinicios y relojes): un fichero JSON accesible,
producido localmente o en el sensor, que identifica campana/episodio/periodo y contiene los VALORES de los que se
deriva el resultado. El descriptor NO aporta el valor: lo aporta el respaldo. Si falta el respaldo pero el descriptor
declara algo, el requisito es 'declarado_sin_verificar' (no apto).

INFORME EXTERNO (para los ficheros PCAP/EVE/decisiones/caracteristicas verificados en otra máquina): su 'referencia'
debe poder abrirse y debe identificar campana/episodio/fuente/archivo/periodo, con un sha256 válido que coincida con
el declarado. Marcadores (<...>), hashes inválidos, referencias inexistentes o informes de otro episodio NO cuentan.
No se añade firma digital: se exige trazabilidad suficiente (que la referencia se abra y corresponda).

Entrada: DESCRIPTOR JSON (ver EJEMPLO-descriptor-integridad.json). No ejecuta la campaña ni toca los hosts.
    python3 verificar_integridad.py --descriptor desc.json --salida integridad.json
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

HISTORIA_MIN_S = 120
POST_MIN_S = 90
MARGEN_RELOJ_S = 3600
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MARCADOR = re.compile(r"<[^>]+>")
REQUISITOS = ("pcap", "eve", "decisiones", "caracteristicas", "cobertura_previa", "cobertura_durante",
              "cobertura_posterior", "continuidad", "sin_faltantes", "captura_sin_errores_relevantes",
              "reinicios", "relojes")


def sha256(p: Path):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def R(estado, metodo, razon, evidencia=None):
    return {"estado": estado, "metodo": metodo, "razon": razon, "evidencia": evidencia}


def _hash_valido(h) -> bool:
    return isinstance(h, str) and bool(HEX64.match(h)) and not MARCADOR.search(h)


def _abrir_json(ruta):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _corresponde(doc, e, fuente=None) -> tuple[bool, str]:
    """El respaldo/informe debe identificar la MISMA campaña, episodio, periodo (que cubra el intervalo) y fuente."""
    if not isinstance(doc, dict):
        return False, "contenido no es objeto JSON"
    if doc.get("campana") != e.get("campana"):
        return False, f"campaña no corresponde ({doc.get('campana')!r} != {e.get('campana')!r})"
    if doc.get("episodio") != e.get("episodio_id"):
        return False, f"episodio no corresponde ({doc.get('episodio')!r} != {e.get('episodio_id')!r})"
    iv, per = e.get("intervalo", {}), doc.get("periodo", {})
    if iv and per:
        if not (per.get("inicio", float("inf")) <= iv.get("inicio", 0) and
                per.get("fin", float("-inf")) >= iv.get("fin", 0)):
            return False, "el periodo del respaldo no cubre el intervalo del episodio"
    else:
        return False, "falta intervalo/periodo para comprobar correspondencia"
    if fuente is not None and doc.get("fuente") not in (fuente, None) and fuente not in (doc.get("fuentes") or []):
        return False, f"fuente del respaldo no corresponde ({doc.get('fuente')!r})"
    return True, "corresponde (campaña/episodio/periodo)"


# ----------------------------------------------------------------- ficheros (hash real o informe externo)
def estado_archivo(campo, e) -> dict:
    ruta = e.get("rutas", {}).get(campo)
    esperado = e.get("hashes_esperados", {}).get(campo)
    externo = e.get("informe_externo", {}).get(campo)
    if esperado is not None and not _hash_valido(esperado):
        return R("ausente", "automatico", f"hash esperado inválido o marcador: {esperado!r}")
    if ruta:
        p = Path(ruta)
        if not p.exists():
            return R("ausente", "automatico", f"la ruta {ruta} no existe")
        real = sha256(p)
        if real is None:
            return R("ausente", "automatico", f"{ruta} no es legible")
        if esperado and real != esperado:
            return R("ausente", "automatico", f"hash distinto: {real[:12]} != esperado {esperado[:12]}")
        return R("verificado", "automatico", "existe, legible y hash real" + (" coincide" if esperado else ""),
                 {"sha256": real})
    if externo is not None:
        return _estado_informe_externo(campo, e, externo, esperado)
    if esperado is not None:
        return R("declarado_sin_verificar", "pendiente", "hash declarado SIN ruta accesible ni informe externo")
    return R("desconocido", "pendiente", "no se aportó ni ruta ni informe externo")


def _estado_informe_externo(campo, e, info, esperado) -> dict:
    if not isinstance(info, dict) or not all(info.get(k) for k in ("maquina", "herramienta", "resultado", "referencia")):
        return R("declarado_sin_verificar", "pendiente", "informe externo incompleto (máquina/herramienta/resultado/referencia)")
    if info.get("resultado") != "ok":
        return R("ausente", "evidencia_externa", f"informe externo con resultado={info.get('resultado')!r}")
    doc = _abrir_json(info["referencia"])
    if doc is None:
        return R("declarado_sin_verificar", "pendiente",
                 f"la referencia {info['referencia']!r} no se puede abrir/resolver en el equipo de análisis")
    ok, razon = _corresponde(doc, e, fuente=campo)
    if not ok:
        return R("ausente", "evidencia_externa", f"la referencia no corresponde: {razon}")
    # el documento debe listar el archivo de esta fuente con un sha256 válido que coincida con el declarado
    archivos = doc.get("archivos", {})
    sha_doc = (archivos.get(campo) or {}).get("sha256") if isinstance(archivos.get(campo), dict) else archivos.get(campo)
    if not _hash_valido(sha_doc):
        return R("ausente", "evidencia_externa", f"la referencia no trae un sha256 válido para {campo} ({sha_doc!r})")
    if esperado and sha_doc != esperado:
        return R("ausente", "evidencia_externa", f"sha256 del informe {sha_doc[:12]} != declarado {esperado[:12]}")
    if info.get("sha256") and info["sha256"] != sha_doc:
        return R("ausente", "evidencia_externa", "el sha256 del informe no coincide con el de su propia referencia")
    return R("verificado", "evidencia_externa",
             f"referencia abierta y correspondiente en {info['maquina']}", {"sha256": sha_doc, "referencia": info["referencia"]})


# ----------------------------------------------------------------- respaldos (valor derivado de un fichero accesible)
def _respaldo(e, campo):
    """Devuelve (doc, estado_fallo). doc=None y estado_fallo!=None si no hay respaldo utilizable."""
    resp = (e.get("respaldos") or {}).get(campo)
    declarado = _hay_declaracion(e, campo)
    if not resp or not resp.get("ruta"):
        if declarado:
            return None, R("declarado_sin_verificar", "pendiente", "valor declarado sin respaldo accesible")
        return None, R("desconocido", "pendiente", "ni declaración ni respaldo")
    doc = _abrir_json(resp["ruta"])
    if doc is None:
        return None, R("ausente", "automatico", f"respaldo {resp['ruta']!r} no se puede abrir")
    ok, razon = _corresponde(doc, e)
    if not ok:
        return None, R("ausente", "automatico", f"respaldo no corresponde: {razon}")
    return doc, None


def _hay_declaracion(e, campo) -> bool:
    d = e.get("declaraciones") or {}
    return campo in d


def estado_cobertura(e, campo, clave, minimo) -> dict:
    doc, fallo = _respaldo(e, "cobertura")
    if fallo:
        return fallo
    if clave == "durante":
        v = doc.get("durante_completa")
        return R("verificado" if v is True else "ausente", doc.get("origen", "local"),
                 "durante completa (respaldo)" if v is True else "durante incompleta (respaldo)",
                 {"ruta": e["respaldos"]["cobertura"]["ruta"]})
    v = doc.get(clave)
    if not isinstance(v, (int, float)):
        return R("ausente", "automatico", f"respaldo sin valor numérico para {clave}")
    return R("verificado" if v >= minimo else "ausente", doc.get("origen", "local"),
             f"{v} s (min {minimo}) [respaldo]", {"segundos": v})


def estado_continuidad(e) -> dict:
    resp = e.get("respaldos") or {}
    ruta = (resp.get("continuidad") or resp.get("cobertura") or {}).get("ruta")
    if not ruta:
        if _hay_declaracion(e, "continuidad"):
            return R("declarado_sin_verificar", "pendiente", "continuidad declarada sin respaldo accesible")
        return R("desconocido", "pendiente", "ni declaración ni respaldo de continuidad")
    doc = _abrir_json(ruta)
    if doc is None:
        return R("ausente", "automatico", f"respaldo {ruta!r} no se puede abrir")
    ok, razon = _corresponde(doc, e)
    if not ok:
        return R("ausente", "automatico", f"respaldo no corresponde: {razon}")
    v = doc.get("continuidad_sin_huecos")
    if v is None:
        return R("ausente", "automatico", "el respaldo no trae continuidad_sin_huecos")
    return R("verificado" if v else "ausente", doc.get("origen", "local"),
             "continua (respaldo)" if v else "con huecos (respaldo)")


def estado_faltantes(e) -> dict:
    doc, fallo = _respaldo(e, "cobertura")
    if fallo:
        return fallo
    f = doc.get("faltantes")
    if f is None:
        return R("ausente", "automatico", "el respaldo no informa de ficheros faltantes")
    return R("verificado" if not f else "ausente", doc.get("origen", "local"),
             "sin faltantes (respaldo)" if not f else f"faltan {f}")


def estado_captura_errores(e) -> dict:
    doc, fallo = _respaldo(e, "captura")
    if fallo:
        return fallo
    relevantes = [x for x in (doc.get("errores") or []) if x.get("afecta_fuentes")]
    if relevantes:
        return R("ausente", doc.get("origen", "local"), "errores que afectan a las fuentes: "
                 + "; ".join(x.get("desc", "?") for x in relevantes))
    perd = doc.get("paquetes_descartados")
    if perd is None:
        return R("ausente", "automatico", "el respaldo no trae paquetes_descartados")
    if perd > 0:
        return R("ausente", doc.get("origen", "local"), f"{perd} paquetes descartados")
    return R("verificado", doc.get("origen", "local"), "sin errores relevantes ni descartes (respaldo)")


def estado_reinicios(e) -> dict:
    doc, fallo = _respaldo(e, "reinicios")
    if fallo:
        return fallo
    problemas, vistos = [], 0
    for comp, lista in (doc.get("reinicios") or {}).items():
        for r in (lista or []):
            vistos += 1
            if not r.get("recuperado"):
                problemas.append(f"{comp}: sin recuperación confirmada")
            elif r.get("historia_tras_s", 0) < HISTORIA_MIN_S or r.get("calentamiento_s", 0) <= 0:
                problemas.append(f"{comp}: historia/calentamiento insuficiente")
    if problemas:
        return R("ausente", doc.get("origen", "local"), "; ".join(problemas))
    return R("verificado", doc.get("origen", "local"),
             f"{vistos} reinicio(s) con recuperación/historia/calentamiento suficientes" if vistos else "sin reinicios")


def estado_relojes(e) -> dict:
    doc, fallo = _respaldo(e, "relojes")
    if fallo:
        return fallo
    req = doc.get("requeridos") or []
    tol = doc.get("tolerancia_s")
    med = doc.get("mediciones")
    if not req:
        return R("ausente", "automatico", "el respaldo no indica hosts requeridos")
    if not isinstance(med, list) or not med:
        return R("desconocido", "pendiente", "respaldo sin mediciones (una tolerancia no es una medición)")
    iv = e.get("intervalo", {})
    ini, fin = iv.get("inicio"), iv.get("fin")
    faltan, fuera, malas, ok = [], [], [], []
    for host in req:
        m = next((x for x in med if x.get("host") == host), None)
        if m is None:
            faltan.append(host); continue
        if not all(k in m for k in ("referencia", "momento", "desfase_s", "incertidumbre_s")):
            malas.append(host); continue
        if ini is not None and fin is not None and not (ini - MARGEN_RELOJ_S <= m["momento"] <= fin + MARGEN_RELOJ_S):
            fuera.append(host); continue
        corr = m.get("correccion_desfase")
        if corr and not (isinstance(corr, dict) and corr.get("procedimiento") and corr.get("verificado")):
            malas.append(host + "(corrección sin procedimiento verificado)"); continue
        if tol is not None and abs(m["desfase_s"]) > tol:
            malas.append(host + f"(desfase {m['desfase_s']}>tol {tol})"); continue
        ok.append(host)
    if faltan or fuera or malas:
        estado = "ausente" if (fuera or malas) else "desconocido"
        return R(estado, doc.get("origen", "local"), f"faltan={faltan} fuera_de_periodo={fuera} invalidas={malas} ok={ok}")
    return R("verificado", doc.get("origen", "local"), f"mediciones válidas para {ok}", {"hosts": ok})


def evaluar_episodio(e: dict) -> dict:
    req = {
        "pcap": estado_archivo("pcap", e), "eve": estado_archivo("eve", e),
        "decisiones": estado_archivo("decisiones", e), "caracteristicas": estado_archivo("caracteristicas", e),
        "cobertura_previa": estado_cobertura(e, "cobertura", "previa_s", HISTORIA_MIN_S),
        "cobertura_durante": estado_cobertura(e, "cobertura", "durante", None),
        "cobertura_posterior": estado_cobertura(e, "cobertura", "posterior_s", POST_MIN_S),
        "continuidad": estado_continuidad(e), "sin_faltantes": estado_faltantes(e),
        "captura_sin_errores_relevantes": estado_captura_errores(e),
        "reinicios": estado_reinicios(e), "relojes": estado_relojes(e)}
    por = {k: [c for c in REQUISITOS if req[c]["estado"] == k]
           for k in ("verificado", "declarado_sin_verificar", "ausente", "desconocido")}
    apto = len(por["verificado"]) == len(REQUISITOS)
    return {"episodio_id": e["episodio_id"], "campana": e.get("campana"), "requisitos": req, "resumen": por,
            "apto": apto,
            "criterio": "apto solo si los 12 requisitos están 'verificado' (hash real, respaldo correspondiente o "
                        "informe externo accesible). Declarado/ausente/desconocido NO cuentan."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descriptor", required=True)
    ap.add_argument("--salida", default="integridad.json")
    a = ap.parse_args()
    desc = json.load(open(a.descriptor, encoding="utf-8"))
    eps = [evaluar_episodio(e) for e in desc.get("episodios", [])]
    rep = {"generado_por": "verificar_integridad.py",
           "nota": "verificado / declarado_sin_verificar / ausente / desconocido. Solo 'verificado' => apto. "
                   "Un booleano del descriptor no es verificación; requiere respaldo accesible y correspondiente.",
           "episodios": eps,
           "resumen": {"aptos": [e["episodio_id"] for e in eps if e["apto"]],
                       "no_aptos": [e["episodio_id"] for e in eps if not e["apto"]]}}
    # salida con saltos LF (bytes que se publican)
    Path(a.salida).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rep["resumen"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
