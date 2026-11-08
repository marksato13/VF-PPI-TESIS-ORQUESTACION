#!/usr/bin/env python3
"""Control normal de la Etapa 4 (4B): métricas SEPARADAS por componente y por clase de salud de la ventana.

ENMIENDA P1 (2026-11-08, VERSION 2026-11-08.1). Sobre la 2026-11-02.1, solo cambia CÓMO se mide Suricata en la clase
de cada ventana y del periodo completo: con ``--suricata-eve`` (eventos ``stats`` de EVE, ``salud_captura``
2026-11-06.1) en lugar de ``stats.log``, que Suricata 7 escribe sin los contadores a cero. Cada ventana y el periodo
completo quedan en UNA de tres categorías de Suricata, que se publican por separado:
    cero_descartes   estado ``cero_explicito`` (cobertura completa, un proceso, kernel_drops presente, Δ = 0)
    descartes        estado ``descartes`` (Δ kernel_drops > 0)  -> clase C1 (como en SALUD-CAPTURA §3)
    datos_faltantes  cualquier otro estado (``ausente``, ``desactualizada``, ``error_lectura``,
                     ``cobertura_insuficiente``)                -> clase C3; el estado concreto se conserva
Una ausencia NUNCA se convierte en cero. Sin ``--suricata-eve`` el comportamiento es el de la 2026-11-02.1 (reproduce
el control publicado del 3B). No cambia ningún criterio, umbral, α ni la definición de las clases.

Solo lee. Complementa a analizar_3b.py (que da la cobertura contra el inventario y las cotas del control) con lo
que el 3B no separaba (PROTOCOLO-4B-CONTROL.md §5):

  1. clase de cada ventana: C0/C1/C2/C3 de [w − 60, w] con salud_captura.clasificar (SALUD-CAPTURA.md §3),
     usando SOLO el journal del tcpdump del anillo; sin datos de salud la clase es "sin_medida";
  2. IF por α (0,05 / 0,03 / 0,01), misma puntuación y mismos umbrales que analizar.py (score < umbral, estricto,
     IF válido solo con paquetes en 10 s), por clase, con desglose por entidad;
  3. heurísticos POR REGLA (campo heuristico.heuristico del registro) y la regla heredada auth_failure_heuristic
     registrada como ALERT, por clase;
  4. emisiones reales del motor (decision == ALERT) por detector, por clase;
  5. vía rápida: señales de senales-rapidas.jsonl con t_evidencia en [desde, hasta] (sin ataques, toda señal es
     falsa alarma), por origen y destino, y la clase de la vía rápida por hora (journal de SU tcpdump);
  6. propuestas del publicador v2 (traza.jsonl, eventos 'nuevos' con publicado_en en [desde, hasta]) por tipo,
     regla, acción y entidad; las 'rechazada' aparte (no son propuestas).
Las ventanas C3 no entran en ninguna tasa; C1 y C2 se publican aparte de C0. Nada se suma entre clases.

Uso:
  python3 control_4b.py --motor motor_decision.log --config config-campana-3b.json \
     --desde ISO --hasta ISO [--salud-captura .../herramientas-20261106/salud_captura.py \
     --incrementos incrementos.jsonl --tcpdump-anillo tcpdump-anillo.log --tcpdump-via tcpdump-via.log \
     --suricata-eve eve-segmento.json [--suricata-eve eve.json.1 ...] [--ahora EPOCH]] \
     [--senales-rapidas senales-rapidas.jsonl] [--traza-publicador traza.jsonl] --salida control-4b.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402
import poblacion  # noqa: E402

VERSION = "2026-11-08.1"   # .1 (08-nov): Suricata por EVE stats, tres categorías por ventana y por periodo. 2026-11-02.1: base
HORIZONTE_S = 60.0
CLASES = ("C0", "C1", "C2", "C3", "insuficiente", "sin_medida")
CAT_CERO, CAT_DESC, CAT_FALTA = "cero_descartes", "descartes", "datos_faltantes"
CATEGORIAS = (CAT_CERO, CAT_DESC, CAT_FALTA)
MAX_TRAMOS = 50


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cargar_salud(path: Path):
    spec = importlib.util.spec_from_file_location("salud_captura", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def categoria_suricata(estado: str | None) -> str:
    """cero_explicito -> cero_descartes; descartes -> descartes; todo lo demás (incluido None) -> datos_faltantes."""
    if estado == "cero_explicito":
        return CAT_CERO
    if estado == "descartes":
        return CAT_DESC
    return CAT_FALTA


def _jsonl(path: Path) -> list:
    out = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


class Clasificador:
    """Clase de [w − 60, w] por valor de window_end (cacheada: todas las entidades comparten la rejilla).

    Con ``eve`` (lectura de ``salud_captura.leer_eve_stats``) la parte de Suricata de CADA periodo se decide con
    ``medida_suricata_eve`` sobre ese mismo periodo, y el resultado lleva ``suricata_categoria`` y ``suricata_estado``."""

    def __init__(self, sc=None, incs=None, td=None, rotacion=5.0, eve=None, ahora=None):
        self.sc, self.incs, self.td = sc, incs or [], td or []
        self.crit = dict(sc.CRITERIOS, rotacion_s=rotacion) if sc else None
        self.eve, self.ahora = eve, ahora
        if eve is not None and (sc is None or not hasattr(sc, "medida_suricata_eve")):
            raise SystemExit("--suricata-eve exige una salud_captura con medida_suricata_eve (2026-11-06.1 o posterior)")
        self.cache: dict = {}

    def clase(self, w: float, ancho: float = HORIZONTE_S) -> dict:
        k = (round(w, 3), ancho)
        if k not in self.cache:
            if self.sc is None:
                self.cache[k] = {"clase": "sin_medida", "motivos": ["sin datos de salud"]}
            elif self.eve is None:
                self.cache[k] = self.sc.clasificar(self.incs, self.td, w - ancho, w, self.crit)
            else:
                med = self.sc.medida_suricata_eve(self.eve, w - ancho, w, self.ahora)
                r = dict(self.sc.clasificar(self.incs, self.td, w - ancho, w, self.crit, suricata_eve=med))
                r["suricata_estado"] = med.get("estado")
                r["suricata_categoria"] = categoria_suricata(med.get("estado"))
                r["suricata"] = {"estado": med.get("estado"), "paquetes": med.get("paquetes"),
                                 "descartes": med.get("descartes"), "descartes_parciales": med.get("descartes_parciales"),
                                 "motivos": med.get("motivos")}
                self.cache[k] = r
        return self.cache[k]

    def categoria(self, w: float, ancho: float = HORIZONTE_S) -> str | None:
        return self.clase(w, ancho).get("suricata_categoria")


def tasas(regs, U) -> dict:
    n = len(regs)
    out = {"ventanas": n}
    for c in an.CONFIGS:
        fa = sum(1 for r in regs if an.senales(r, U)[c])
        out[c] = {"falsas_alarmas": fa, "tasa": round(fa / n, 6) if n else None}
    return out


def por_entidad(regs, U) -> dict:
    g = defaultdict(list)
    for r in regs:
        g[r["entity_ip"]].append(r)
    return {ip: {"ventanas": len(v), **{c: sum(1 for r in v if an.senales(r, U)[c]) for c in an.CONFIGS}}
            for ip, v in sorted(g.items())}


def heuristicos(regs) -> dict:
    reglas, auth = Counter(), 0
    for r in regs:
        h = r.get("heuristico")
        if h is not None:
            reglas[(h or {}).get("heuristico") or "desconocido"] += 1
        if r.get("decision") == "ALERT" and r.get("detector_name") == an.AUTH_DETECTOR:
            auth += 1
    return {"por_regla": dict(sorted(reglas.items())), "auth_failure_heuristic_alert_heredada": auth}


def emisiones(regs) -> dict:
    c = Counter(str(r.get("detector_name")) for r in regs if r.get("decision") == "ALERT")
    return {"alert_por_detector": dict(sorted(c.items())), "alert_total": sum(c.values())}


def _resumen_clase(c: dict) -> dict:
    out = {"clase": c["clase"], "motivos": c.get("motivos", [])}
    if "suricata_categoria" in c:
        out["suricata_categoria"] = c["suricata_categoria"]
        out["suricata_estado"] = c.get("suricata_estado")
        out["suricata"] = c.get("suricata")
    return out


def por_horas(clasif: Clasificador, desde: float, hasta: float) -> list:
    horas, t = [], desde
    while t < hasta:
        f = min(t + 3600, hasta)
        horas.append({"desde_utc": an.iso(t), "hasta_utc": an.iso(f), **_resumen_clase(clasif.clase(f, f - t))})
        t = f
    return horas


def via_rapida(path: Path, desde, hasta, clasif_via: Clasificador | None) -> dict:
    s = [x for x in _jsonl(path) if x.get("event") == "senal_rapida"
         and desde <= float(x.get("t_evidencia") or 0) <= hasta]
    out = {"senales": len(s), "significado": "sin ataques en el control: toda señal es falsa alarma",
           "por_regla": dict(Counter(str(x.get("regla")) for x in s)),
           "por_origen_destino": dict(Counter(f"{x.get('origen')}->{x.get('destino')}" for x in s)),
           "retraso_emision_s": sorted(round(float(x["emitido_en"]) - float(x["t_evidencia"]), 3)
                                       for x in s if x.get("emitido_en") is not None)[:50]}
    if clasif_via is not None:
        out["clase_por_hora"] = [{k: v for k, v in h.items() if k != "suricata"}
                                 for h in por_horas(clasif_via, desde, hasta)]
    return out


def propuestas(path: Path, desde, hasta) -> dict:
    nuevos = []
    for x in _jsonl(path):
        if x.get("evento") == "publicacion" and desde <= float(x.get("publicado_en") or 0) <= hasta:
            nuevos += x.get("nuevos") or []
    rech = [n for n in nuevos if n.get("tipo") == "rechazada"]
    prop = [n for n in nuevos if n.get("tipo") != "rechazada"]
    return {"propuestas": len(prop),
            "significado": "propuestas en SOMBRA del publicador v2: nadie las aplica; no son detecciones",
            "por_tipo": dict(Counter(str(n.get("tipo")) for n in prop)),
            "por_regla": dict(Counter(str(n.get("regla")) for n in prop)),
            "por_accion": dict(Counter(str(n.get("accion")) for n in prop)),
            "por_entidad": dict(Counter(str(n.get("ip")) for n in prop)),
            "rechazadas": len(rech),
            "rechazadas_por_motivo": dict(Counter(str(n.get("motivo_rechazo")) for n in rech))}


def _tramos(ws: list, paso: float = 10.0) -> list:
    """Une los valores de window_end consecutivos (≤ paso + 0,5 s) en tramos [w_primero − 60, w_último]."""
    out, ini, ant = [], None, None
    for w in sorted(set(ws)):
        if ini is None:
            ini = ant = w
        elif w - ant <= paso + 0.5:
            ant = w
        else:
            out.append([an.iso(ini - HORIZONTE_S), an.iso(ant)])
            ini = ant = w
    if ini is not None:
        out.append([an.iso(ini - HORIZONTE_S), an.iso(ant)])
    return out


def suricata_por_ventana(v: list, nev: list, clasif: Clasificador) -> dict:
    """Tres categorías por ventana (decididas y no evaluadas), con el estado concreto de los datos faltantes."""
    dec, nov = Counter(), Counter()
    estados = Counter()
    faltan_ws = []
    for r in v:
        c = clasif.clase(r["_wend"])
        dec[c["suricata_categoria"]] += 1
        if c["suricata_categoria"] == CAT_FALTA:
            estados[str(c.get("suricata_estado"))] += 1
            faltan_ws.append(r["_wend"])
    for e in nev:
        c = clasif.clase(e["_wend"])
        nov[c["suricata_categoria"]] += 1
        if c["suricata_categoria"] == CAT_FALTA:
            faltan_ws.append(e["_wend"])
    tr = _tramos(faltan_ws)
    return {"fuente": "eve_stats",
            "significado": "categoría de Suricata de [w − 60, w] por ventana; independiente de las demás causas de C3",
            "ventanas_decididas_por_categoria": {k: dec.get(k, 0) for k in CATEGORIAS},
            "ventanas_no_evaluadas_por_categoria": {k: nov.get(k, 0) for k in CATEGORIAS},
            "datos_faltantes_decididas_por_estado": dict(sorted(estados.items())),
            "tramos_con_datos_faltantes": tr[:MAX_TRAMOS], "tramos_con_datos_faltantes_total": len(tr)}


def analizar(regs, ne, desde, hasta, U, pob, clasif: Clasificador) -> dict:
    v = [r for r in regs if desde <= r["_wend"] <= hasta and not poblacion.excluida(r["entity_ip"], pob)]
    nev = [e for e in ne if desde <= e["_wend"] <= hasta and not poblacion.excluida(e["entity_ip"], pob)]
    grupos, motivos = defaultdict(list), defaultdict(Counter)
    for r in v:
        c = clasif.clase(r["_wend"])
        grupos[c["clase"]].append(r)
        for m in c.get("motivos", []):
            motivos[c["clase"]][m.split(":")[0]] += 1
    ne_por = Counter(clasif.clase(e["_wend"])["clase"] for e in nev)
    out = {"ventanas_decididas": len(v), "ventanas_no_evaluadas": len(nev),
           "ventanas_por_clase": {k: len(grupos.get(k, [])) for k in CLASES},
           "no_evaluadas_por_clase": {k: ne_por.get(k, 0) for k in CLASES},
           "motivos_por_clase": {k: dict(m) for k, m in motivos.items()},
           "por_clase": {}}
    if clasif.eve is not None:
        out["suricata_por_ventana"] = suricata_por_ventana(v, nev, clasif)
    for k in CLASES:
        g = grupos.get(k, [])
        if not g:
            continue
        if k in ("C3", "insuficiente"):
            out["por_clase"][k] = {"ventanas": len(g), "nota": "excluida de toda tasa (SALUD-CAPTURA §4.3)"}
            continue
        out["por_clase"][k] = {"if_y_configuraciones": tasas(g, U), "heuristicos": heuristicos(g),
                               "emisiones_reales": emisiones(g), "por_entidad": por_entidad(g, U)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--salud-captura", type=Path)
    ap.add_argument("--incrementos", type=Path)
    ap.add_argument("--tcpdump-anillo", type=Path)
    ap.add_argument("--tcpdump-via", type=Path)
    ap.add_argument("--suricata-eve", type=Path, action="append", default=[],
                    help="eve.json (segmento del control) y rotados: Suricata se mide por EVE stats")
    ap.add_argument("--ahora", type=float, default=None, help="epoch de referencia para 'desactualizada' (por omisión, ahora)")
    ap.add_argument("--rotacion", type=float, default=5.0)
    ap.add_argument("--senales-rapidas", type=Path)
    ap.add_argument("--traza-publicador", type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)

    cfg = json.load(open(a.config, encoding="utf-8"))
    U = an.umbrales_de(cfg)
    pob = poblacion.cargar_poblacion(cfg)
    desde, hasta = an.como_epoch(a.desde), an.como_epoch(a.hasta)
    regs, inc_r, dups = an.leer_motor(a.motor)
    ref = {"archivo": str(a.motor), "sha256": _sha(a.motor)}
    ne = an.leer_no_evaluadas(a.motor, regs, ref)["vigentes"]

    sc = cargar_salud(a.salud_captura) if a.salud_captura else None
    if sc is not None and not (a.incrementos and a.tcpdump_anillo):
        raise SystemExit("--salud-captura exige --incrementos y --tcpdump-anillo")
    if a.suricata_eve and sc is None:
        raise SystemExit("--suricata-eve exige --salud-captura")
    if a.suricata_eve and not all(hasattr(sc, n) for n in ("leer_eve_stats", "medida_suricata_eve")):
        raise SystemExit("--suricata-eve exige una salud_captura con medida_suricata_eve y leer_eve_stats "
                         "(2026-11-06.1 o posterior)")
    for f in a.suricata_eve:
        if not Path(f).is_file():           # un EVE que no se pudo copiar no es «cero datos»: se para
            raise SystemExit(f"error: --suricata-eve no legible: {f}")
    incs = _jsonl(a.incrementos) if a.incrementos else []
    ahora = a.ahora if a.ahora is not None else time.time()
    lect = None
    if a.suricata_eve:
        lect = sc.leer_eve_stats([Path(f) for f in a.suricata_eve], desde=desde - 2 * HORIZONTE_S)
    clasif = Clasificador(sc, incs, sc.leer_tcpdump_log(a.tcpdump_anillo) if sc else [], a.rotacion, lect, ahora)
    clasif_via = (Clasificador(sc, incs, sc.leer_tcpdump_log(a.tcpdump_via), a.rotacion, lect, ahora)
                  if sc is not None and a.tcpdump_via else None)

    fuentes = {"motor": ref, "config": {"archivo": str(a.config), "sha256": _sha(a.config)},
               "salud_captura": ({"archivo": str(a.salud_captura), "sha256": _sha(a.salud_captura),
                                  "version": getattr(sc, "VERSION", None)} if sc else None),
               "incrementos": str(a.incrementos) if a.incrementos else None,
               "tcpdump_anillo": str(a.tcpdump_anillo) if a.tcpdump_anillo else None,
               "tcpdump_via": str(a.tcpdump_via) if a.tcpdump_via else None}
    if lect is not None:
        fuentes["suricata_eve"] = {"ficheros": [{"archivo": str(f), "sha256": _sha(Path(f))} for f in a.suricata_eve],
                                   "muestras_leidas": len(lect.get("muestras", [])), "parciales": lect.get("parciales"),
                                   "invalidas": len(lect.get("invalidas", [])), "repetidas": lect.get("repetidas"),
                                   "conflictos": len(lect.get("conflictos", [])), "errores": lect.get("errores", []),
                                   "ahora_epoch": ahora}
    res = {"version": VERSION, "intervalo_utc": [an.iso(desde), an.iso(hasta)], "fuentes": fuentes,
           "umbrales": U, "poblacion": poblacion.publico(pob),
           "seleccion": "ventanas con window_end_utc en [desde, hasta] (ambos incluidos), deduplicadas como "
                        "analizar.py; clase de la ventana = clase de [w − 60, w]",
           "incidencias_motor": inc_r[:50], "duplicados": len(dups),
           "detector": analizar(regs, ne, desde, hasta, U, pob, clasif)}
    if lect is not None:
        res["periodo_completo"] = {"intervalo_utc": [an.iso(desde), an.iso(hasta)],
                                   "anillo_if_heur": _resumen_clase(clasif.clase(hasta, hasta - desde)),
                                   "por_hora": por_horas(clasif, desde, hasta)}
        if clasif_via is not None:
            res["periodo_completo"]["via_rapida"] = _resumen_clase(clasif_via.clase(hasta, hasta - desde))
    if a.senales_rapidas:
        res["via_rapida"] = via_rapida(a.senales_rapidas, desde, hasta, clasif_via)
    if a.traza_publicador:
        res["propuestas_publicador_v2"] = propuestas(a.traza_publicador, desde, hasta)
    a.salida.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    d = res["detector"]
    resumen = {"ventanas_por_clase": d["ventanas_por_clase"],
               "C0": (d["por_clase"].get("C0") or {}).get("if_y_configuraciones"),
               "sin_medida": (d["por_clase"].get("sin_medida") or {}).get("if_y_configuraciones")}
    if "suricata_por_ventana" in d:
        resumen["suricata_decididas"] = d["suricata_por_ventana"]["ventanas_decididas_por_categoria"]
        resumen["periodo_completo"] = {k: res["periodo_completo"]["anillo_if_heur"].get(k)
                                       for k in ("clase", "suricata_categoria", "suricata_estado")}
    print(json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
