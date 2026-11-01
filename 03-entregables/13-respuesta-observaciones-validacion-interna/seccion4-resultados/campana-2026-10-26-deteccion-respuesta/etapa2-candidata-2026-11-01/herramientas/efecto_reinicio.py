#!/usr/bin/env python3
"""Etapa 2: ventanas cuyo contenido cambia tras reiniciar el motor (r7) frente a la referencia (r2).

Une por (entidad, fin de ventana); informa, en segundos desde el reinicio, las
ventanas con distinta regla, distinta clase alfa o vector distinto, y las que
faltan en un lado. Uso: efecto_reinicio.py <ref_dir> <reinicio_dir> <t_reinicio_epoch> <salida.json>
"""
import datetime as dt, json, sys
from pathlib import Path
ts = lambda x: dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()  # noqa: E731
A = {"0.05": -0.5694578968203694, "0.03": -0.5898535710336618, "0.01": -0.6223889502095352}
def clase(s):
    if s is None: return "sin_score"
    k = [a for a, u in sorted(A.items(), reverse=True) if s < u]
    return k[-1] if k else "normal"
def cargar(d):
    out = {}
    for l in (Path(d) / "motor_decision.log").open(encoding="utf-8"):
        x = json.loads(l)
        if x.get("event") == "decision":
            out[(x["entity_ip"], x["window_end_utc"])] = x
    return out
ref, rei, t_r, sal = cargar(sys.argv[1]), cargar(sys.argv[2]), float(sys.argv[3]), Path(sys.argv[4])
regla = lambda x: sorted(h["heuristico"] for h in x.get("heuristicos", []))  # noqa: E731
dif = []
for k in sorted(set(ref) & set(rei), key=lambda k: ts(k[1])):
    a, b = ref[k], rei[k]
    if regla(a) != regla(b) or clase(a.get("score")) != clase(b.get("score")):
        dif.append({"ip": k[0], "ventana": k[1], "t_desde_reinicio_s": round(ts(k[1]) - t_r, 1),
                    "reglas_ref": regla(a), "reglas_reinicio": regla(b),
                    "clase_ref": clase(a.get("score")), "clase_reinicio": clase(b.get("score"))})
antes = [d for d in dif if d["t_desde_reinicio_s"] < 0]
despues = [d["t_desde_reinicio_s"] for d in dif if d["t_desde_reinicio_s"] >= 0]
res = {"t_reinicio": t_r, "decisiones_con_cambio": len(dif), "antes_del_reinicio": len(antes),
       "despues_max_s": max(despues) if despues else None, "cambios": dif,
       "solo_ref_tras_reinicio": sorted(k[1] + " " + k[0] for k in set(ref) - set(rei) if ts(k[1]) >= t_r - 60),
       "solo_reinicio_tras_reinicio": sorted(k[1] + " " + k[0] for k in set(rei) - set(ref) if ts(k[1]) >= t_r - 60)}
sal.write_text(json.dumps(res, indent=1), encoding="utf-8")
print("cambios", len(dif), "antes", len(antes), "despues_max_s", res["despues_max_s"])
for d in dif: print(" ", d["t_desde_reinicio_s"], d["ip"], d["reglas_ref"], "->", d["reglas_reinicio"], d["clase_ref"], "->", d["clase_reinicio"])
print("solo_ref", len(res["solo_ref_tras_reinicio"]), "solo_reinicio", len(res["solo_reinicio_tras_reinicio"]))
