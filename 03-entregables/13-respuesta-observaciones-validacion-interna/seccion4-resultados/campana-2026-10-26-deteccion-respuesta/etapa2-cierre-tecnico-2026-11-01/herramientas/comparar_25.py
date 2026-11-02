"""Compara por episodio y configuracion las categorias de analizar_3b.py en: revision en vivo, replay de
referencia (archivo 15 s periodico) y replay candidato (5 s eventos). Tambien el control normal.
Uso: python comparar_25.py vivo.json ref.json cand.json salida.json"""
import json, sys
nombres = ("vivo_revisado", "replay_ref", "replay_cand")
A = dict(zip(nombres, (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:4])))
CONF = ["IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01"]
filas, dif = [], {"vivo_vs_cand": [], "ref_vs_cand": []}
for e in A["replay_cand"]["episodios"]:
    f = {"episodio": e}
    for n in nombres:
        x = A[n]["episodios"].get(e, {})
        f[n] = {"principal": x.get("en_poblacion_principal"),
                **{c: (x.get(c) or {}).get("categoria") for c in CONF},
                "primera_IF_0.05_s": ((x.get("IF_0.05") or {}).get("primera") or {}).get("disponible_desde_inicio_s"),
                "primera_HEUR_s": ((x.get("HEUR") or {}).get("primera") or {}).get("disponible_desde_inicio_s")}
    for par, (p, q) in (("vivo_vs_cand", ("vivo_revisado", "replay_cand")), ("ref_vs_cand", ("replay_ref", "replay_cand"))):
        for k in ["principal"] + CONF:
            if f[p][k] != f[q][k]:
                dif[par].append([e, k, f[p][k], f[q][k]])
    filas.append(f)
res = {"episodios": filas, "diferencias": dif,
       "poblacion": {n: A[n].get("poblacion") for n in nombres},
       "control_normal": {n: A[n].get("control_normal") for n in nombres}}
json.dump(res, open(sys.argv[4], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for par, d in dif.items():
    print(par, len(d))
    for x in d: print("  ", x)
for n in nombres:
    p = A[n].get("poblacion") or {}
    print(n, "poblacion:", {k: v for k, v in p.items() if not isinstance(v, (list, dict))})
