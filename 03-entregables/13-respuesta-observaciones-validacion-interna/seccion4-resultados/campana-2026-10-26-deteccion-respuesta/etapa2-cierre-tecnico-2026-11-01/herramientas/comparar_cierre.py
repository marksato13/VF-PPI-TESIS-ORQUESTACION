#!/usr/bin/env python3
"""Comparador del cierre tecnico de la Etapa 2 (contenido completo + disponibilidad).

Para cada replay frente a la referencia, sobre las claves (entidad, ventana) de [desde, hasta]:
  claves      comunes / solo_ref / solo_otro, y duplicados dentro de cada replay
  vectores    iguales bit a bit / distintos, y por cada una de las 28 caracteristicas el numero
              de ventanas en que difiere (tolerancia 0: el extractor es determinista; cualquier
              diferencia se cuenta)
  scores      iguales / distintos (y |diferencia| maxima)
  decision    ALERT/PERMIT y detector iguales
  reglas      lista de heuristicos iguales
  clases      clase IF por alfa (0,05 / 0,03 / 0,01) iguales
  historial   ventanas con historial_completo = false
Disponibilidad: latencia logged_at - fin de ventana, memoria pico, coste de ciclo.
Episodios (marcas.jsonl): para el origen de ensayo, primera ventana con la regla prevista y con
IF a cada alfa: durante [ini, fin], despues (fin, fin+60] o ausente; con la hora de registro.

Uso: comparar_cierre.py --referencia DIR --otros DIR... --marcas marcas.jsonl --esquema esquema.json
     --desde ISO --hasta ISO --salida comparacion.json
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import statistics
from pathlib import Path

ALFA = {"0.05": -0.5694578968203694, "0.03": -0.5898535710336618, "0.01": -0.6223889502095352}
ORIGEN = "10.10.20.30"
REGLA_PREVISTA = {"dns_inusual": "dns_entropy", "inundacion_http": "http_abuse", "escaneo_breve": "port_scan",
                  "escaneo_sostenido": "port_scan", "fuerza_bruta_http": "brute_force"}


def ts(x: str) -> float:
    return dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()


def cuantiles(v):
    if not v:
        return {"n": 0}
    v = sorted(v)
    q = lambda p: v[min(len(v) - 1, int(round(p * (len(v) - 1))))]  # noqa: E731
    return {"n": len(v), "p50": round(q(0.5), 3), "p90": round(q(0.9), 3), "max": round(v[-1], 3),
            "media": round(statistics.fmean(v), 3)}


def clase(score):
    if score is None:
        return "sin_score"
    for a in ("0.01", "0.03", "0.05"):
        if score < ALFA[a]:
            return a
    return "normal"


def reglas(r):
    h = r.get("heuristicos")
    if isinstance(h, list):
        return sorted(str(x.get("heuristico")) + ":" + str(x.get("accion")) if isinstance(x, dict) else str(x)
                      for x in h)
    return []


def tiene_regla(r, regla):
    return any(x.startswith(regla + ":") for x in reglas(r))


def cargar(d: Path, desde: float, hasta: float) -> dict:
    dec, noev, dup = {}, {}, 0
    arranques = []
    for linea in (d / "motor_decision.log").open(encoding="utf-8"):
        r = json.loads(linea)
        if r.get("event") == "motor_startup":
            arranques.append(r)
            continue
        if "window_end_utc" not in r:
            continue
        w = ts(r["window_end_utc"])
        if not desde <= w <= hasta:
            continue
        k = (r["entity_ip"], r["window_end_utc"])
        if k in dec or k in noev:
            dup += 1
        (dec if r.get("event") == "decision" else noev)[k] = r
    x = {}
    p = d / "caracteristicas.jsonl"
    if p.exists():
        for linea in p.open(encoding="utf-8"):
            r = json.loads(linea)
            x[(r["entity_ip"], r["window_end_utc"])] = r
    mem, dur = [], []
    p = d / "ciclos-arnes.jsonl"
    if p.exists():
        for linea in p.open(encoding="utf-8"):
            c = json.loads(linea)
            dur.append(c.get("dur_s", 0.0))
            for k in ("rss_mb", "pico_mb", "vmhwm_mb", "peak_mb"):
                if k in c:
                    mem.append(c[k])
    return {"dec": dec, "noev": noev, "dup": dup, "x": x, "mem_pico_mb": max(mem) if mem else None,
            "ciclo_s": cuantiles(dur), "arranques": len(arranques)}


def comparar(ref: dict, otro: dict, nombres: list[str]) -> dict:
    kr = set(ref["dec"]) | set(ref["noev"])
    ko = set(otro["dec"]) | set(otro["noev"])
    com = sorted(kr & ko)
    out = {"comunes": len(com), "solo_ref": len(kr - ko), "solo_otro": len(ko - kr),
           "duplicados_ref": ref["dup"], "duplicados_otro": otro["dup"],
           "ejemplos_solo_ref": sorted(kr - ko)[:8], "ejemplos_solo_otro": sorted(ko - kr)[:8]}
    n_x = n_xd = n_s = n_sd = n_dec = n_reg = 0
    por_car = collections.Counter()
    clases = {a: 0 for a in ALFA}
    dmax = 0.0
    ejemplos = []
    hist_dif = collections.Counter()
    for k in com:
        a, b = ref["dec"].get(k), otro["dec"].get(k)
        if a is None or b is None:
            n_dec += (a is None) != (b is None)
            continue
        if (a["decision"], a["detector_name"]) != (b["decision"], b["detector_name"]):
            n_dec += 1
        if reglas(a) != reglas(b):
            n_reg += 1
        sa, sb = a.get("score"), b.get("score")
        n_s += 1
        if sa != sb:
            n_sd += 1
            if sa is not None and sb is not None:
                dmax = max(dmax, abs(sa - sb))
        for al, um in ALFA.items():
            ca = sa is not None and sa < um
            cb = sb is not None and sb < um
            clases[al] += ca == cb
        xa, xb = ref["x"].get(k), otro["x"].get(k)
        if xa is not None and xb is not None:
            n_x += 1
            if xa["x"] != xb["x"]:
                n_xd += 1
                dif = [nombres[i] for i, (u, v) in enumerate(zip(xa["x"], xb["x"])) if u != v]
                por_car.update(dif)
                hist_dif[(a.get("historial_completo"), b.get("historial_completo"))] += 1
                if len(ejemplos) < 10:
                    ejemplos.append({"clave": k, "caracteristicas": dif[:8],
                                     "historial_ref": a.get("historial_completo"),
                                     "historial_otro": b.get("historial_completo")})
    out.update({"vectores_comparados": n_x, "vectores_distintos": n_xd,
                "por_caracteristica": dict(por_car.most_common()),
                "scores_comparados": n_s, "scores_distintos": n_sd, "score_dif_max": dmax,
                "decision_o_detector_distintos": n_dec, "reglas_distintas": n_reg,
                "clases_iguales_por_alfa": clases, "ejemplos_vectores_distintos": ejemplos,
                "historial_en_vectores_distintos": {"%s/%s" % k: v for k, v in hist_dif.items()}})
    return out


def episodios(marcas: Path) -> list[dict]:
    ini, out = {}, []
    for linea in marcas.open(encoding="utf-8"):
        r = json.loads(linea)
        if r.get("evento") == "inicio":
            ini[r["episodio_id"]] = (r["escenario"], ts(r["reloj"]["pared_utc"]))
        elif r.get("evento") == "fin" and r.get("episodio_id") in ini:
            esc, t0 = ini[r["episodio_id"]]
            out.append({"id": r["episodio_id"], "escenario": esc, "ini": t0, "fin": ts(r["reloj"]["pared_utc"]),
                        "estado": r.get("estado")})
    return out


def deteccion(run: dict, ep: dict) -> dict:
    regla = REGLA_PREVISTA[ep["escenario"]]
    filas = sorted((ts(k[1]), r) for k, r in run["dec"].items() if k[0] == ORIGEN
                   and ep["ini"] < ts(k[1]) < ep["fin"] + 60)
    res = {}
    for nombre, cond in [("regla_" + regla, lambda r: tiene_regla(r, regla))] + \
            [("IF_" + a, (lambda um: lambda r: r.get("score") is not None and r["score"] < um)(um))
             for a, um in ALFA.items()]:
        prim = next(((w, r) for w, r in filas if cond(r)), None)
        if prim is None:
            res[nombre] = {"estado": "ausente" if filas else "no_evaluable"}
            continue
        w, r = prim
        disp = r.get("logged_at")
        res[nombre] = {"estado": "durante" if disp is not None and disp <= ep["fin"] else "despues",
                       "ventana_desde_inicio_s": round(w - ep["ini"], 1),
                       "registro_desde_inicio_s": round(disp - ep["ini"], 1) if disp else None,
                       "historial_completo": r.get("historial_completo")}
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--referencia", type=Path, required=True)
    ap.add_argument("--otros", type=Path, nargs="+", required=True)
    ap.add_argument("--marcas", type=Path, required=True)
    ap.add_argument("--esquema", type=Path, required=True)
    ap.add_argument("--desde", type=ts, required=True)
    ap.add_argument("--hasta", type=ts, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    esquema = json.loads(a.esquema.read_text(encoding="utf-8"))
    nombres = [f["name"] for f in sorted(esquema["features"], key=lambda f: f["order"])]
    eps = [e for e in episodios(a.marcas) if a.desde <= e["ini"] and e["fin"] + 60 <= a.hasta]
    ref = cargar(a.referencia, a.desde, a.hasta)
    salida = {"desde": a.desde, "hasta": a.hasta, "referencia": a.referencia.name, "tolerancia": "0 (bit a bit)",
              "runs": {}}

    def resumen(run, nombre):
        lat = [r["logged_at"] - ts(r["window_end_utc"]) for r in run["dec"].values() if r.get("logged_at")]
        hist = collections.Counter(str(r.get("historial_completo")) for r in run["dec"].values())
        return {"decisiones": len(run["dec"]), "no_evaluadas": len(run["noev"]), "duplicados": run["dup"],
                "arranques": run["arranques"], "latencia_s": cuantiles(lat), "historial_completo": dict(hist),
                "memoria_pico_mb": run["mem_pico_mb"], "ciclo_s": run["ciclo_s"],
                "episodios": {e["id"]: deteccion(run, e) for e in eps}}

    salida["runs"][a.referencia.name] = resumen(ref, a.referencia.name)
    for d in a.otros:
        o = cargar(d, a.desde, a.hasta)
        salida["runs"][d.name] = dict(resumen(o, d.name), frente_a_referencia=comparar(ref, o, nombres))
    a.salida.write_text(json.dumps(salida, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    for n, r in salida["runs"].items():
        c = r.get("frente_a_referencia", {})
        print("%s | dec %d noev %d dup %d | comunes %s solo_ref %s solo_otro %s | x_dist %s/%s | score_dist %s | "
              "reglas_dist %s | clases %s | lat p50/p90 %s/%s | mem %s" % (
                  n, r["decisiones"], r["no_evaluadas"], r["duplicados"], c.get("comunes"), c.get("solo_ref"),
                  c.get("solo_otro"), c.get("vectores_distintos"), c.get("vectores_comparados"),
                  c.get("scores_distintos"), c.get("reglas_distintas"), c.get("clases_iguales_por_alfa"),
                  r["latencia_s"].get("p50"), r["latencia_s"].get("p90"), r["memoria_pico_mb"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
