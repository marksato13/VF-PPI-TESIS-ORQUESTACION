#!/usr/bin/env python3
"""Paso 1: compara los registros de decision de referencia y candidato y resume tiempos por condicion.

Uso: analizar_p1.py --base ~/cf-p1 --marcas marcas.jsonl --salida resumen.json
Lee r1-ref-perfil, r2-cand-verif, r3-cand, r4-ref-reinicio, r4-cand-reinicio (los que existan).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import statistics
from pathlib import Path

CLAVE_EVENTOS = ("decision", "ventana_no_evaluada")
CAMPOS_SOLO_CANDIDATO = {"procesamiento", "ciclos_path"}  # anadidos al registro de arranque
# Unico campo excluido de la comparacion de decisiones: no existe en 7b275b8 (9b4cf2b lo anade). Se comprueba
# aparte que decidido_en <= logged_at. logged_at SI se compara (en el replay es la hora simulada del ciclo).
CAMPOS_EXCLUIDOS_DECISION = {"decidido_en"}
CALENTAMIENTO_S = 230  # tras arrancar o reiniciar, la historia de 230 s aun no esta llena


def leer_jsonl(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def clave(r: dict) -> tuple:
    return (r.get("event"), r.get("entity_ip"), r.get("window_end_utc"))


def comparar(dir_a: Path, dir_b: Path) -> dict:
    a = leer_jsonl(dir_a / "motor_decision.log")
    b = leer_jsonl(dir_b / "motor_decision.log")
    res: dict = {"a": dir_a.name, "b": dir_b.name, "registros_a": len(a), "registros_b": len(b),
                 "eventos_a": dict(collections.Counter(r.get("event") for r in a)),
                 "eventos_b": dict(collections.Counter(r.get("event") for r in b))}
    for nombre, regs in (("a", a), ("b", b)):
        c = collections.Counter(clave(r) for r in regs if r.get("event") in CLAVE_EVENTOS)
        res[f"duplicados_{nombre}"] = sum(n - 1 for n in c.values() if n > 1)
    da = {clave(r): r for r in a if r.get("event") in CLAVE_EVENTOS}
    db = {clave(r): r for r in b if r.get("event") in CLAVE_EVENTOS}
    res["solo_a"] = sorted(map(list, set(da) - set(db)))[:10]
    res["solo_b"] = sorted(map(list, set(db) - set(da)))[:10]
    res["n_solo_a"] = len(set(da) - set(db))
    res["n_solo_b"] = len(set(db) - set(da))
    campos = collections.Counter()
    ejemplos = []
    for k in sorted(set(da) & set(db), key=str):
        ra, rb = da[k], db[k]
        dif = sorted(c for c in set(ra) | set(rb) if c not in CAMPOS_EXCLUIDOS_DECISION
                     and ra.get(c, "<ausente>") != rb.get(c, "<ausente>"))
        for c in dif:
            campos[c] += 1
        if dif and len(ejemplos) < 5:
            ejemplos.append({"clave": list(k), "campos": {c: [ra.get(c), rb.get(c)] for c in dif}})
    res["comunes"] = len(set(da) & set(db))
    res["campos_distintos"] = dict(campos)
    res["ejemplos_distintos"] = ejemplos
    # orden de emision
    oa = [clave(r) for r in a if r.get("event") in CLAVE_EVENTOS]
    ob = [clave(r) for r in b if r.get("event") in CLAVE_EVENTOS]
    res["mismo_orden"] = oa == ob
    # registros de arranque
    sa = [r for r in a if r.get("event") not in CLAVE_EVENTOS]
    sb = [r for r in b if r.get("event") not in CLAVE_EVENTOS]
    dif_arr = []
    for ra, rb in zip(sa, sb):
        d = sorted(c for c in set(ra) | set(rb) if c not in CAMPOS_SOLO_CANDIDATO and c not in ("logged_at",)
                   and ra.get(c) != rb.get(c))
        if d:
            dif_arr.append({c: [ra.get(c), rb.get(c)] for c in d})
    res["otros_registros"] = [len(sa), len(sb)]
    res["otros_registros_distintos"] = dif_arr[:5]
    # resumen de decisiones de b
    dec = [r for r in b if r.get("event") == "decision"]
    res["decisiones_b"] = dict(collections.Counter(r.get("decision") for r in dec))
    res["heuristico_b"] = dict(collections.Counter(str(r.get("heuristico")) for r in dec))
    res["score_none_b"] = sum(1 for r in dec if r.get("score") is None)
    res["con_pendiente_desde_b"] = sum(1 for r in dec if r.get("pendiente_desde") is not None)
    res["no_evaluadas_b"] = dict(collections.Counter(r.get("motivo") for r in b if r.get("event") == "ventana_no_evaluada"))
    res["campos_excluidos"] = sorted(CAMPOS_EXCLUIDOS_DECISION)
    con_dec = [r for r in b if r.get("event") in CLAVE_EVENTOS and "decidido_en" in r]
    res["decidido_en_b"] = {"registros": len(con_dec),
                            "posterior_a_logged_at": sum(1 for r in con_dec if r["decidido_en"] > r["logged_at"])}
    res["arranques"] = [sum(1 for r in a if r.get("event") == "motor_startup"),
                        sum(1 for r in b if r.get("event") == "motor_startup")]
    res["equivalente"] = (res["n_solo_a"] == 0 and res["n_solo_b"] == 0 and not campos
                          and res["duplicados_a"] == 0 and res["duplicados_b"] == 0 and not dif_arr)
    return res


def episodios(ruta: Path) -> list[tuple[str, float, float]]:
    ini, out = {}, []
    for r in leer_jsonl(ruta):
        t = dt.datetime.fromisoformat(r["reloj"]["pared_utc"]).timestamp() if "reloj" in r else None
        if r.get("evento") == "inicio":
            ini[r["episodio_id"]] = t
        elif r.get("evento") == "fin" and r.get("episodio_id") in ini:
            out.append((r["episodio_id"], ini[r["episodio_id"]], t))
    return out


def condicion(t: float, eps: list, control: tuple[float, float]) -> str:
    # Los datos llegan con retraso (PCAP rota cada 15 s) y la historia retiene 230 s: la carga dura mas que el episodio.
    for nombre, i, f in eps:
        if nombre.startswith("inundacion_http") and i <= t < f + 30:
            return "inundacion"
    for nombre, i, f in eps:
        if nombre.startswith("inundacion_http") and f + 30 <= t < f + 30 + 230:
            return "recuperacion"
    for nombre, i, f in eps:
        if i <= t < f + 30:
            return "otros_ataques"
    if control[0] <= t < control[1]:
        return "control"
    return "normal"


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def resumir(xs: list[float]) -> dict:
    return {"n": len(xs), "p50": round(pct(xs, .5), 3), "p90": round(pct(xs, .9), 3), "p95": round(pct(xs, .95), 3),
            "max": round(max(xs), 3) if xs else None, "media": round(statistics.fmean(xs), 3) if xs else None,
            "sobre_9_5": sum(x > 9.5 for x in xs), "sobre_10": sum(x > 10 for x in xs)}


def estad(v: list[float]) -> dict:
    return {"p50": round(pct(v, .5), 4), "p95": round(pct(v, .95), 4), "max": round(max(v), 4)}


def tiempos(directorio: Path, eps: list, control: tuple) -> dict:
    ciclos = leer_jsonl(directorio / "ciclos-arnes.jsonl")
    # arranques (primer ciclo de cada main(), incluido el de un reinicio) y su calentamiento
    arranques = [c["t"] for c in ciclos if c.get("arranque")]

    def cond_de(t: float, es_arranque: bool) -> str:
        if es_arranque:
            return "arranque"
        if any(0 < t - a < CALENTAMIENTO_S for a in arranques):
            return "calentamiento"
        return condicion(t, eps, control)

    por = collections.defaultdict(list)
    etapas_por = collections.defaultdict(lambda: collections.defaultdict(list))
    for c in ciclos:
        cond = cond_de(c["t"], c.get("arranque"))
        por[cond].append(c["dur_s"])
        por["todos"].append(c["dur_s"])
        if cond not in ("arranque", "calentamiento"):
            por["estable_total"].append(c["dur_s"])
        for k, v in (c.get("etapas") or {}).items():
            etapas_por[cond][k].append(v)
    # etapas internas del candidato (ciclos.jsonl del propio motor)
    internos = [r for r in leer_jsonl(directorio / "_state" / "ciclos.jsonl") if r.get("event") == "ciclo"]
    etapas_int = collections.defaultdict(lambda: collections.defaultdict(list))
    contadores = collections.defaultdict(lambda: collections.defaultdict(list))
    t_arranques = set(arranques)
    for r in internos:
        cond = cond_de(r["inicio_ciclo"], r["inicio_ciclo"] in t_arranques)
        etapas_int[cond]["ciclo_completo_motor"].append(r.get("duracion_s", 0.0))
        for k, v in (r.get("etapas_s") or {}).items():
            etapas_int[cond][k].append(v)
        for k in ("ventanas_pendientes", "filas_construidas", "decididas", "puntuadas", "no_evaluadas",
                  "paquetes_anillo", "entidades", "flujos_recalculados"):
            if isinstance(r.get(k), (int, float)):
                contadores[cond][k].append(r[k])
    return {
        "ciclos": len(ciclos),
        "por_condicion": {k: resumir(v) for k, v in sorted(por.items())},
        "etapas_arnes": {cond: {k: estad(v) for k, v in sorted(d.items())} for cond, d in sorted(etapas_por.items())},
        "registros_ciclo_motor": len(internos),
        "etapas_motor": {cond: {k: estad(v) for k, v in sorted(d.items())} for cond, d in sorted(etapas_int.items())},
        "contadores_motor_max": {cond: {k: max(v) for k, v in sorted(d.items())} for cond, d in sorted(contadores.items())},
        "lentos": sorted(({"hora": c.get("hora"), "dur_s": c["dur_s"]} for c in ciclos if c["dur_s"] > 9.5),
                         key=lambda x: -x["dur_s"])[:15],
    }


def verificacion(ruta: Path) -> dict:
    v = leer_jsonl(ruta)
    malos = [r for r in v if not r.get("ok")]
    tot = collections.Counter()
    for r in v:
        for k, x in r.items():
            if k.startswith("ok_") and not x:
                tot[k] += 1
    return {"ciclos": len(v), "no_ok": len(malos), "fallos_por_comprobacion": dict(tot),
            "ejemplos": malos[:5],
            "filas_necesarias": sum(r.get("filas_necesarias", 0) for r in v),
            "filas_candidatas": sum(r.get("filas_candidatas", 0) for r in v),
            "puntuadas": sum(r.get("puntuadas", 0) for r in v)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--marcas", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    eps = episodios(a.marcas)
    control = (dt.datetime(2026, 10, 29, 8, 1, tzinfo=dt.timezone.utc).timestamp(),
               dt.datetime(2026, 10, 29, 8, 35, 10, tzinfo=dt.timezone.utc).timestamp())
    B = a.base
    out: dict = {"episodios": len(eps), "inundaciones": [(n, i, f) for n, i, f in eps if n.startswith("inundacion")]}
    pares = [("r1-ref-perfil", "r2-cand-verif"), ("r1-ref-perfil", "r3-cand"), ("r2-cand-verif", "r3-cand"),
             ("r4-ref-reinicio", "r4-cand-reinicio"), ("r4-ref-reinicio", "r4-cand-reinicio-9b4cf2b"),
             ("r4-ref-reinicio", "r5-cand-reinicio-tiempos")]
    out["comparaciones"] = [comparar(B / x, B / y) for x, y in pares if (B / x / "motor_decision.log").exists()
                            and (B / y / "motor_decision.log").exists()]
    out["verificacion"] = {d: verificacion(B / d / "verificacion.jsonl")
                           for d in ("r2-cand-verif", "r4-cand-reinicio", "r4-cand-reinicio-9b4cf2b")
                           if (B / d / "verificacion.jsonl").exists()}
    out["tiempos"] = {d: tiempos(B / d, eps, control)
                      for d in ("r1-ref-perfil", "r3-cand", "r2-cand-verif", "r4-ref-reinicio", "r4-cand-reinicio-9b4cf2b",
                                "r5-cand-reinicio-tiempos")
                      if (B / d / "ciclos-arnes.jsonl").exists()}
    a.salida.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for c in out["comparaciones"]:
        print(c["a"], "vs", c["b"], "equivalente=", c["equivalente"], "comunes=", c["comunes"],
              "solo=", c["n_solo_a"], c["n_solo_b"], "dup=", c["duplicados_a"], c["duplicados_b"],
              "campos=", c["campos_distintos"], "orden=", c["mismo_orden"])
    for d, v in out["verificacion"].items():
        print("verif", d, {k: v[k] for k in ("ciclos", "no_ok", "fallos_por_comprobacion")})
    for d, t in out["tiempos"].items():
        print("tiempos", d, json.dumps(t["por_condicion"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
