#!/usr/bin/env python3
"""Control normal de la Etapa 4 (4B): métricas SEPARADAS por componente y por clase de salud de la ventana.

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
     --desde ISO --hasta ISO [--salud-captura .../scripts/etapa4/salud_captura.py \
     --incrementos incrementos.jsonl --tcpdump-anillo tcpdump-anillo.log --tcpdump-via tcpdump-via.log] \
     [--senales-rapidas senales-rapidas.jsonl] [--traza-publicador traza.jsonl] --salida control-4b.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402
import poblacion  # noqa: E402

VERSION = "2026-11-02.1"
HORIZONTE_S = 60.0
CLASES = ("C0", "C1", "C2", "C3", "insuficiente", "sin_medida")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cargar_salud(path: Path):
    spec = importlib.util.spec_from_file_location("salud_captura", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    """Clase de [w − 60, w] por valor de window_end (cacheada: todas las entidades comparten la rejilla)."""

    def __init__(self, sc=None, incs=None, td=None, rotacion=5.0):
        self.sc, self.incs, self.td = sc, incs or [], td or []
        self.crit = dict(sc.CRITERIOS, rotacion_s=rotacion) if sc else None
        self.cache: dict = {}

    def clase(self, w: float, ancho: float = HORIZONTE_S) -> dict:
        k = (round(w, 3), ancho)
        if k not in self.cache:
            if self.sc is None:
                self.cache[k] = {"clase": "sin_medida", "motivos": ["sin datos de salud"]}
            else:
                self.cache[k] = self.sc.clasificar(self.incs, self.td, w - ancho, w, self.crit)
        return self.cache[k]


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


def via_rapida(path: Path, desde, hasta, clasif_via: Clasificador | None) -> dict:
    s = [x for x in _jsonl(path) if x.get("event") == "senal_rapida"
         and desde <= float(x.get("t_evidencia") or 0) <= hasta]
    out = {"senales": len(s), "significado": "sin ataques en el control: toda señal es falsa alarma",
           "por_regla": dict(Counter(str(x.get("regla")) for x in s)),
           "por_origen_destino": dict(Counter(f"{x.get('origen')}->{x.get('destino')}" for x in s)),
           "retraso_emision_s": sorted(round(float(x["emitido_en"]) - float(x["t_evidencia"]), 3)
                                       for x in s if x.get("emitido_en") is not None)[:50]}
    if clasif_via is not None:
        horas, t = [], desde
        while t < hasta:
            f = min(t + 3600, hasta)
            c = clasif_via.clase(f, f - t)
            horas.append({"desde_utc": an.iso(t), "hasta_utc": an.iso(f), "clase": c["clase"],
                          "motivos": c.get("motivos", [])})
            t = f
        out["clase_por_hora"] = horas
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
    incs = _jsonl(a.incrementos) if a.incrementos else []
    clasif = Clasificador(sc, incs, sc.leer_tcpdump_log(a.tcpdump_anillo) if sc else [], a.rotacion)
    clasif_via = (Clasificador(sc, incs, sc.leer_tcpdump_log(a.tcpdump_via), a.rotacion)
                  if sc is not None and a.tcpdump_via else None)

    res = {"version": VERSION, "intervalo_utc": [an.iso(desde), an.iso(hasta)],
           "fuentes": {"motor": ref, "config": {"archivo": str(a.config), "sha256": _sha(a.config)},
                       "salud_captura": ({"archivo": str(a.salud_captura), "sha256": _sha(a.salud_captura),
                                          "version": getattr(sc, "VERSION", None)} if sc else None),
                       "incrementos": str(a.incrementos) if a.incrementos else None,
                       "tcpdump_anillo": str(a.tcpdump_anillo) if a.tcpdump_anillo else None,
                       "tcpdump_via": str(a.tcpdump_via) if a.tcpdump_via else None},
           "umbrales": U, "poblacion": poblacion.publico(pob),
           "seleccion": "ventanas con window_end_utc en [desde, hasta] (ambos incluidos), deduplicadas como "
                        "analizar.py; clase de la ventana = clase de [w − 60, w]",
           "incidencias_motor": inc_r[:50], "duplicados": len(dups),
           "detector": analizar(regs, ne, desde, hasta, U, pob, clasif)}
    if a.senales_rapidas:
        res["via_rapida"] = via_rapida(a.senales_rapidas, desde, hasta, clasif_via)
    if a.traza_publicador:
        res["propuestas_publicador_v2"] = propuestas(a.traza_publicador, desde, hasta)
    a.salida.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    d = res["detector"]
    print(json.dumps({"ventanas_por_clase": d["ventanas_por_clase"],
                      "C0": (d["por_clase"].get("C0") or {}).get("if_y_configuraciones"),
                      "sin_medida": (d["por_clase"].get("sin_medida") or {}).get("if_y_configuraciones")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
