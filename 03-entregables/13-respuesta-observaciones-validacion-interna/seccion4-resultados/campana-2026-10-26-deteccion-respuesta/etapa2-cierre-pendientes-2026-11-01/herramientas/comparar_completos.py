"""Compara dos replays completos clave a clave: registros, vectores, scores, reglas y decisiones.
Uso: python comparar_completos.py dir_a dir_b salida.json [desde_iso hasta_iso]
Clave = (entidad, window_end_utc). Estado de una clave en cada replay: decision | no_evaluada:<motivo>
| cancelada | sin_registro."""
import collections, json, sys
a_dir, b_dir, salida = sys.argv[1:4]
desde = sys.argv[4] if len(sys.argv) > 4 else ""
hasta = sys.argv[5] if len(sys.argv) > 5 else "9999"


def cargar(d):
    est, dec, x = {}, {}, {}
    for l in open(d + "/motor_decision.log", encoding="utf-8"):
        r = json.loads(l)
        ev = r.get("event")
        if ev not in ("decision", "ventana_no_evaluada", "pendiente_cancelada"):
            continue
        k = (r["entity_ip"], r["window_end_utc"])
        if not (desde <= k[1] < hasta):
            continue
        if ev == "decision":
            est[k] = "decision"
            dec[k] = (r["decision"], r["detector_name"], r["score"], r.get("heuristico"),
                      json.dumps(r.get("heuristicos"), sort_keys=True))
        elif ev == "ventana_no_evaluada":
            est[k] = "no_evaluada:" + r["motivo"]
        else:
            est[k] = "cancelada"
    for l in open(d + "/caracteristicas.jsonl", encoding="utf-8"):
        r = json.loads(l)
        k = (r["entity_ip"], r["window_end_utc"])
        if desde <= k[1] < hasta:
            x[k] = (r["x"], r["score"])
    return est, dec, x


ea, da, xa = cargar(a_dir)
eb, db, xb = cargar(b_dir)
claves = set(ea) | set(eb)
trans = collections.Counter((ea.get(k, "sin_registro"), eb.get(k, "sin_registro")) for k in claves)
comunes_dec = set(da) & set(db)
comunes_x = set(xa) & set(xb)
dif_x = sorted(k for k in comunes_x if xa[k][0] != xb[k][0])
dif_score = sorted(k for k in comunes_x if xa[k][1] != xb[k][1])
dif_dec = sorted(k for k in comunes_dec if da[k][0] != db[k][0])
dif_regla = sorted(k for k in comunes_dec if da[k][1:] != db[k][1:])
res = {
    "a": a_dir, "b": b_dir, "rango": [desde, hasta],
    "claves": {"a": len(ea), "b": len(eb), "union": len(claves)},
    "estados_a": dict(collections.Counter(ea.values())),
    "estados_b": dict(collections.Counter(eb.values())),
    "transiciones_a_b": {f"{x} -> {y}": n for (x, y), n in sorted(trans.items()) if x != y},
    "iguales": sum(n for (x, y), n in trans.items() if x == y),
    "vectores_comparables": len(comunes_x), "vectores_distintos": len(dif_x), "scores_distintos": len(dif_score),
    "decisiones_comparables": len(comunes_dec), "decisiones_distintas": len(dif_dec),
    "detector_o_reglas_distintos": len(dif_regla),
    "ejemplos": {"vectores": dif_x[:5], "decisiones": dif_dec[:5], "reglas": dif_regla[:5],
                 "transiciones": sorted((k for k in claves if ea.get(k) != eb.get(k)))[:40]},
}
json.dump(res, open(salida, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "ejemplos"}, indent=1, ensure_ascii=False))
