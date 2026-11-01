#!/usr/bin/env python3
"""verificar_integridad v2 — REVISIÓN POSTERIOR A CONOCER LOS RESULTADOS del paso 3B (../CRITERIOS-REVISION.md).

Igual que verificar_integridad.py (se importa sin modificarlo) salvo cobertura_previa, cobertura_durante,
cobertura_posterior y continuidad, que exigen el DESGLOSE POR COMPONENTE del respaldo v2 (pcap, eve, procesamiento y,
en durante, anclas_kali). Un respaldo sin desglose (formato v1: previa_s, continuidad_sin_huecos...) NO verifica:
el valor agregado no basta. Hashes, faltantes, captura (incluidos kernel_drops de Suricata y descartes de tcpdump),
reinicios y relojes: exactamente como en v1.
    python3 verificar_integridad_v2.py --descriptor desc.json --salida integridad.json
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
for p in (AQUI, AQUI.parent.parent / "scripts"):
    sys.path.insert(0, str(p))
import verificar_integridad as vi  # noqa: E402

R = vi.R
COMPONENTES = ("pcap", "eve", "procesamiento")
MINIMOS = {"previa": vi.HISTORIA_MIN_S, "posterior": vi.POST_MIN_S, "durante": None}


def _componentes(c: dict, extra=()) -> tuple[bool, list, str | None]:
    falta = [k for k in COMPONENTES + tuple(extra) if not isinstance(c.get(k), dict) or "ok" not in c[k]]
    if falta:
        return False, [], f"respaldo sin desglose de {falta}: no verificado"
    malos = [f"{k}: {c[k].get('motivo')}" for k in COMPONENTES + tuple(extra) if c[k]["ok"] is not True]
    return not malos, malos, None


def estado_intervalo(e, nombre) -> dict:
    doc, fallo = vi._respaldo(e, "cobertura")
    if fallo:
        return fallo
    c = (doc.get("intervalos") or {}).get(nombre)
    if not isinstance(c, dict):
        return R("ausente", "automatico", f"respaldo sin desglose por componente para '{nombre}' (formato v1): "
                                          "no verificado")
    ok, malos, err = _componentes(c, ("anclas_kali",) if nombre == "durante" else ())
    if err:
        return R("ausente", "automatico", err)
    m = MINIMOS[nombre]
    if m is not None and not (isinstance(c.get("duracion_s"), (int, float)) and c["duracion_s"] >= m):
        return R("ausente", "automatico", f"intervalo {c.get('duracion_s')} s < mínimo {m} s")
    return R("verificado" if ok else "ausente", doc.get("origen", "local"),
             f"{nombre}: pcap, eve y procesamiento verificados" if ok else f"{nombre}: " + "; ".join(malos),
             {"rango_utc": c.get("rango_utc")})


def estado_continuidad(e) -> dict:
    doc, fallo = vi._respaldo(e, "cobertura")
    if fallo:
        return fallo
    c = doc.get("continuidad")
    if not isinstance(c, dict):
        return R("ausente", "automatico", "respaldo sin desglose de continuidad (formato v1): no verificado")
    ok, malos, err = _componentes(c)
    if err:
        return R("ausente", "automatico", err)
    return R("verificado" if ok else "ausente", doc.get("origen", "local"),
             "continua: pcap, eve y procesamiento" if ok else "; ".join(malos), {"rango_utc": c.get("rango_utc")})


def evaluar_episodio(e: dict) -> dict:
    req = {
        "pcap": vi.estado_archivo("pcap", e), "eve": vi.estado_archivo("eve", e),
        "decisiones": vi.estado_archivo("decisiones", e), "caracteristicas": vi.estado_archivo("caracteristicas", e),
        "cobertura_previa": estado_intervalo(e, "previa"),
        "cobertura_durante": estado_intervalo(e, "durante"),
        "cobertura_posterior": estado_intervalo(e, "posterior"),
        "continuidad": estado_continuidad(e), "sin_faltantes": vi.estado_faltantes(e),
        "captura_sin_errores_relevantes": vi.estado_captura_errores(e),
        "reinicios": vi.estado_reinicios(e), "relojes": vi.estado_relojes(e)}
    por = {k: [c for c in vi.REQUISITOS if req[c]["estado"] == k]
           for k in ("verificado", "declarado_sin_verificar", "ausente", "desconocido")}
    return {"episodio_id": e["episodio_id"], "campana": e.get("campana"), "requisitos": req, "resumen": por,
            "apto": len(por["verificado"]) == len(vi.REQUISITOS),
            "criterio": "v2 (revisión posterior): apto solo si los 12 requisitos están 'verificado'; cobertura y "
                        "continuidad por componente (pcap, eve, procesamiento frente al inventario)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descriptor", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    desc = json.load(open(a.descriptor, encoding="utf-8"))
    eps = [evaluar_episodio(e) for e in desc.get("episodios", [])]
    rep = {"generado_por": "verificar_integridad_v2.py (revisión posterior a conocer los resultados)",
           "episodios": eps,
           "resumen": {"aptos": [e["episodio_id"] for e in eps if e["apto"]],
                       "no_aptos": [e["episodio_id"] for e in eps if not e["apto"]]}}
    Path(a.salida).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rep["resumen"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
