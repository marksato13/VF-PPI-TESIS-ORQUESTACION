#!/usr/bin/env python3
"""Verificador de integridad de fuentes por campaña/episodio (lo consulta analizar.py antes de declarar evaluable).

Distingue DECLARACIONES de VERIFICACIONES. Cada requisito tiene un estado:
  - "verificado"              comprobado automáticamente aquí (p.ej. hash real del fichero disponible) o por un
                              INFORME EXTERNO TRAZABLE (máquina, herramienta, resultado, referencia de evidencia)
  - "declarado_sin_verificar" el descriptor lo afirma pero sin respaldo comprobable (p.ej. solo un hash escrito)
  - "ausente"                 el recurso requerido no está / no es legible
  - "desconocido"             no hay información suficiente para afirmar nada
Solo "verificado" cuenta para 'apto'. Un hash escrito en el descriptor NO prueba que el fichero exista ni que se
haya verificado. Una tolerancia de reloj NO es una medición. 'desconocido'/'ausente'/'declarado_sin_verificar' NO
son 'correcto'.

Entrada: DESCRIPTOR JSON (ver EJEMPLO-descriptor-integridad.json). No ejecuta la campaña ni toca los hosts.
    python3 verificar_integridad.py --descriptor desc.json --salida integridad.json
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

HISTORIA_MIN_S = 120
POST_MIN_S = 90
MARGEN_RELOJ_S = 3600          # una medición de reloj vale si su momento cae dentro de ±1 h del intervalo del episodio
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


def _informe_externo_valido(info: dict) -> bool:
    """Un informe externo es trazable solo si identifica máquina, herramienta, resultado y referencia de evidencia."""
    return isinstance(info, dict) and all(info.get(k) for k in ("maquina", "herramienta", "resultado", "referencia")) \
        and info.get("resultado") == "ok"


def estado_archivo(campo, e) -> dict:
    ruta = e.get("rutas", {}).get(campo)
    esperado = e.get("hashes_esperados", {}).get(campo)
    externo = e.get("informe_externo", {}).get(campo)
    if ruta:
        p = Path(ruta)
        if not p.exists():
            return R("ausente", "automatico", f"la ruta {ruta} no existe")
        real = sha256(p)
        if real is None:
            return R("ausente", "automatico", f"{ruta} no es legible")
        if esperado and real != esperado:
            return R("ausente", "automatico", f"hash distinto: calculado {real[:12]} != esperado {esperado[:12]}",
                     {"sha256_calculado": real, "sha256_esperado": esperado})
        return R("verificado", "automatico", "existe, legible y hash real" + (" coincide" if esperado else " calculado"),
                 {"sha256": real})
    # sin ruta local: solo vale un informe externo trazable
    if _informe_externo_valido(externo):
        return R("verificado", "evidencia_externa",
                 f"verificado en {externo['maquina']} con {externo['herramienta']}", externo)
    if esperado or (externo is not None):
        return R("declarado_sin_verificar", "pendiente",
                 "hash/afirmación en el descriptor SIN ruta accesible ni informe externo trazable")
    return R("desconocido", "pendiente", "no se aportó ni ruta ni informe externo")


def estado_cobertura(e, clave, minimo) -> dict:
    cov = e.get("cobertura_s", {})
    if clave not in cov:
        return R("desconocido", "pendiente", f"falta cobertura_s.{clave}")
    v = cov[clave]
    if clave == "durante":
        return R("verificado" if v is True else "ausente", "automatico",
                 "durante completa" if v is True else "durante incompleta")
    return R("verificado" if v >= minimo else "ausente", "automatico",
             f"{v} s (min {minimo})", {"segundos": v})


def estado_relojes(e) -> dict:
    rel = e.get("relojes", {})
    req = rel.get("requeridos") or []
    tol = rel.get("tolerancia_s")
    med = rel.get("mediciones")
    if not req:
        return R("desconocido", "pendiente", "no se indicaron hosts requeridos")
    if not isinstance(med, list) or not med:
        return R("desconocido", "pendiente",
                 "solo hay tolerancia configurada, SIN mediciones (una tolerancia no es una medición)")
    intervalo = e.get("intervalo", {})
    ini, fin = intervalo.get("inicio"), intervalo.get("fin")
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
            malas.append(host + "(correccion sin procedimiento verificado)"); continue
        if tol is not None and abs(m["desfase_s"]) > tol:
            malas.append(host + f"(desfase {m['desfase_s']}>tol {tol})"); continue
        ok.append(host)
    if faltan or fuera or malas:
        estado = "ausente" if (fuera or malas) else "desconocido"
        return R(estado, "automatico",
                 f"faltan={faltan} fuera_de_periodo={fuera} invalidas={malas} ok={ok}")
    return R("verificado", "automatico", f"mediciones válidas para {ok}", {"hosts": ok})


def estado_reinicios(e) -> dict:
    """Un reinicio no invalida todo el ensayo, pero debe tener recuperación e historia/calentamiento suficientes."""
    reinicios = e.get("reinicios", {})
    problemas = []
    vistos = 0
    for comp, lista in reinicios.items():
        for r in (lista or []):
            vistos += 1
            if not r.get("recuperado"):
                problemas.append(f"{comp}: reinicio sin recuperación confirmada")
            elif r.get("historia_tras_s", 0) < HISTORIA_MIN_S or r.get("calentamiento_s", 0) <= 0:
                problemas.append(f"{comp}: historia/calentamiento insuficiente tras el reinicio")
    if "reinicios" not in e:
        return R("desconocido", "pendiente", "no se informó sobre reinicios")
    if problemas:
        return R("ausente", "automatico", "; ".join(problemas))
    return R("verificado", "automatico", f"{vistos} reinicio(s) con recuperación e historia/calentamiento suficientes"
             if vistos else "sin reinicios en el intervalo")


def estado_captura_errores(e) -> dict:
    cap = e.get("captura")
    if cap is None:
        return R("desconocido", "pendiente", "no se informó de estadísticas de captura")
    perd = cap.get("paquetes_descartados")
    errores = cap.get("errores", [])
    relevantes = [x for x in errores if x.get("afecta_fuentes")]
    if relevantes:
        return R("ausente", "automatico", "errores de captura que afectan a las fuentes: "
                 + "; ".join(x.get("desc", "?") for x in relevantes))
    if perd is None:
        return R("desconocido", "pendiente", "no se informó de paquetes descartados")
    if perd > 0:
        return R("ausente", "automatico", f"{perd} paquetes descartados por el kernel")
    return R("verificado", "automatico", "sin errores relevantes ni descartes")


def estado_continuidad(e) -> dict:
    if "continuidad_sin_huecos" not in e:
        return R("desconocido", "pendiente", "no se informó de continuidad de captura")
    return R("verificado" if e["continuidad_sin_huecos"] else "ausente", "automatico",
             "continua" if e["continuidad_sin_huecos"] else "con huecos")


def estado_faltantes(e) -> dict:
    if "faltantes" not in e:
        return R("desconocido", "pendiente", "no se informó de ficheros faltantes")
    return R("verificado" if not e["faltantes"] else "ausente", "automatico",
             "sin faltantes" if not e["faltantes"] else f"faltan {e['faltantes']}")


def evaluar_episodio(e: dict) -> dict:
    req = {
        "pcap": estado_archivo("pcap", e), "eve": estado_archivo("eve", e),
        "decisiones": estado_archivo("decisiones", e), "caracteristicas": estado_archivo("caracteristicas", e),
        "cobertura_previa": estado_cobertura(e, "previa", HISTORIA_MIN_S),
        "cobertura_durante": estado_cobertura(e, "durante", None),
        "cobertura_posterior": estado_cobertura(e, "posterior", POST_MIN_S),
        "continuidad": estado_continuidad(e), "sin_faltantes": estado_faltantes(e),
        "captura_sin_errores_relevantes": estado_captura_errores(e),
        "reinicios": estado_reinicios(e), "relojes": estado_relojes(e)}
    verificados = [k for k in REQUISITOS if req[k]["estado"] == "verificado"]
    desconocidos = [k for k in REQUISITOS if req[k]["estado"] == "desconocido"]
    declarados = [k for k in REQUISITOS if req[k]["estado"] == "declarado_sin_verificar"]
    ausentes = [k for k in REQUISITOS if req[k]["estado"] == "ausente"]
    apto = len(verificados) == len(REQUISITOS)
    return {"episodio_id": e["episodio_id"], "campana": e.get("campana"), "requisitos": req,
            "resumen": {"verificado": verificados, "declarado_sin_verificar": declarados,
                        "ausente": ausentes, "desconocido": desconocidos},
            "apto": apto,
            "criterio": "apto solo si los 12 requisitos están 'verificado' (automático o informe externo trazable). "
                        "declarado_sin_verificar / ausente / desconocido NO cuentan como correcto."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descriptor", required=True)
    ap.add_argument("--salida", default="integridad.json")
    a = ap.parse_args()
    desc = json.load(open(a.descriptor, encoding="utf-8"))
    eps = [evaluar_episodio(e) for e in desc.get("episodios", [])]
    rep = {"generado_por": "verificar_integridad.py",
           "nota": "Distingue verificado / declarado_sin_verificar / ausente / desconocido. Solo 'verificado' => apto.",
           "episodios": eps,
           "resumen": {"aptos": [e["episodio_id"] for e in eps if e["apto"]],
                       "no_aptos": [e["episodio_id"] for e in eps if not e["apto"]]}}
    Path(a.salida).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep["resumen"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
