#!/usr/bin/env python3
"""Calidad de las fuentes por episodio con Suricata medido por EVE (4C, s50 v2, 2026-11-10).

`calidad_fuentes.py` (fijado por hash, NO se modifica) mide Suricata con `capture.kernel_drops` de `stats.log`, y Suricata 7
no escribe esa línea cuando vale 0: con él todos los episodios de la 4C salían «insuficiente: suricata: sin stats.log». Este
envoltorio reutiliza TAL CUAL la clasificación de `calidad_fuentes.calidad_episodio` (archivo, interfaz, criterios) y solo
sustituye la medida de Suricata por la de `salud_captura.medida_suricata_eve` (2026-11-06.1) sobre los eventos `stats` del
segmento EVE, la misma que ya usan los pasos 3 y 7 de s50 y el vigía.

Una medida de Suricata solo cuenta como CERO si el estado es `cero_explicito` (cobertura completa, un solo proceso,
`kernel_drops` presente en todas las muestras del tramo y Δ = 0). Cualquier otro estado (`ausente`, `desactualizada`,
`error_lectura`, `cobertura_insuficiente`) es «no medido» y deja el episodio `insuficiente`; nunca se convierte en cero.

Uso:
  python3 calidad_fuentes_eve.py --herramientas ~/cf-e4/herramientas --salud-captura <salud_captura.py> --eve eve-segmento.json \
      --marcas marcas.jsonl --archivador archivar.log [--muestras muestras.jsonl] --duracion-pcap 5 --salida calidad-fuentes.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

VERSION = "2026-11-10.1"


def _cargar(ruta: Path, nombre: str):
    espec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(mod)
    return mod


def mapear_medida(med: dict, iso) -> dict:
    """Medida EVE -> el diccionario que espera `calidad_fuentes.calidad_episodio` (`medido`, `kernel_drops`, ...).
    Defensivo: un estado «cero_explicito» sin cifras coherentes se trata como NO medido."""
    est = med.get("estado")
    desc, paq, acot = med.get("descartes"), med.get("paquetes"), med.get("acotado_por")
    coherente = isinstance(desc, int) and not isinstance(desc, bool) and desc >= 0 and isinstance(paq, int) and acot
    if est == "cero_explicito" and coherente and desc == 0:
        ok = True
    elif est == "descartes" and coherente and desc > 0:
        ok = True
    else:
        ok = False
    if ok:
        return {"medido": True, "fuente": "eve_stats", "estado": est, "muestra_desde_utc": iso(acot[0]),
                "muestra_hasta_utc": iso(acot[1]), "kernel_packets": paq, "kernel_drops": desc,
                "muestras_eve": med.get("muestras")}
    motivos = "; ".join(med.get("motivos") or []) or "medida incoherente"
    return {"medido": False, "fuente": "eve_stats", "estado": est if est not in ("cero_explicito", "descartes") else "incoherente",
            "motivo": f"EVE stats {est}: {motivos}", "descartes_parciales": med.get("descartes_parciales")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--herramientas", required=True, type=Path, help="directorio con calidad_fuentes.py y analizar.py (fijados)")
    ap.add_argument("--salud-captura", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--archivador", type=Path)
    ap.add_argument("--muestras", type=Path)
    ap.add_argument("--margen", type=float, default=60.0)
    ap.add_argument("--duracion-pcap", type=float, default=15.0)
    ap.add_argument("--ahora", type=float, help="solo pruebas: instante de referencia para «desactualizada»")
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)
    sys.path.insert(0, str(a.herramientas))
    import calidad_fuentes as cf           # noqa: E402  (fijado por hash)
    an = cf.an
    sc = _cargar(a.salud_captura, "salud_captura")
    eps, inc = an.leer_marcas(a.marcas)
    lect = sc.leer_eve_stats([a.eve])
    ahora = a.ahora if a.ahora is not None else time.time()
    arch = cf.leer_archivador(a.archivador) if a.archivador else None
    mu = cf.leer_muestras(a.muestras) if a.muestras else []
    cf.delta_stats = lambda serie, desde, hasta: mapear_medida(sc.medida_suricata_eve(lect, desde, hasta, ahora), an.iso)
    res = {eid: cf.calidad_episodio(ep, ["eve"], arch, mu, a.margen, a.duracion_pcap) for eid, ep in eps.items()}
    doc = cf.__doc__.split("Uso (")[0].strip()
    a.salida.write_text(json.dumps({
        "definicion": doc + "\n\nENMIENDA 4C s50 v2 (calidad_fuentes_eve.py " + VERSION + "): la medida de Suricata (punto 3) sale de los eventos "
                      "`stats` de EVE con salud_captura " + sc.VERSION + "; solo `cero_explicito` cuenta como cero descartes.",
        "margen_s": a.margen, "duracion_pcap_s": a.duracion_pcap,
        "fuentes": {"suricata": "eve_stats", "eve": str(a.eve), "salud_captura": sc.VERSION,
                    "archivador": str(a.archivador) if a.archivador else None,
                    "muestras": str(a.muestras) if a.muestras else None, "muestras_eve": len(lect.get("muestras", [])),
                    "eve_ok": bool(lect.get("ok")), "eve_errores": lect.get("errores", [])},
        "incidencias_marcas": inc, "episodios": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: (v["estado"], v["motivos"]) for k, v in res.items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
