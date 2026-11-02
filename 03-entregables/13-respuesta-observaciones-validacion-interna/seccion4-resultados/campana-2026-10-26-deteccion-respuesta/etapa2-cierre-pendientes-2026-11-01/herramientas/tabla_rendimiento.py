"""Tablas Markdown de la comparacion secuencial (ref / cand / opt) a partir de rendimiento_secuencial.py.
Uso: python tabla_rendimiento.py salida.md ref.json cand.json opt.json"""
import json, sys
sal = sys.argv[1]
nombres = ["953a436 (ref)", "862404e (cand)", "6b6ef82 (opt)"]
D = [json.load(open(p, encoding="utf-8")) for p in sys.argv[2:5]]
segs = list(D[0]["segmentos"].keys())
L = []
L.append("| Segmento | Version | Ciclos | Pared p50/p95/max (s) | CPU p95/max (s) | >10 s | >20 s | Retraso p95/max (s) | Pendientes max/fin | R1 | R2 | R3 | R4 |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for s in segs:
    for n, d in zip(nombres, D):
        x = d["segmentos"][s]; c = d["criterio"][s]
        p = x["pared_s"]; cp = x["cpu_s"]; r = x["retraso_decision_s"]; pe = x["pendientes"]
        ok = lambda k: "-" if k not in c else ("si" if c[k] else "**NO**")
        L.append(f"| {s} | {n} | {x['ciclos']} | {p['p50']}/{p['p95']}/{p['max']} | {cp['p95']}/{cp['max']} | {p['n_gt_10']} | {p['n_gt_20']} | {r['p95']}/{r['max']} | {pe['max']}/{pe['al_final']} | {ok('R1')} | {ok('R2')} | {ok('R3')} | {ok('R4')} |")
L.append("")
L.append("Cumple todo: " + ", ".join(f"{n} = {'SI' if d['cumple_todo'] else 'NO'}" for n, d in zip(nombres, D)))
L.append("")
L.append("### Etapas del motor (suma en s sobre todos los segmentos medidos)")
L.append("")
etapas = sorted({e for d in D for s in segs for e in d["segmentos"][s]["etapas_motor_s"]})
L.append("| Etapa | " + " | ".join(nombres) + " |")
L.append("|---|" + "---|" * len(nombres))
for e in etapas:
    L.append(f"| {e} | " + " | ".join(str(round(sum(d['segmentos'][s]['etapas_motor_s'].get(e, {}).get('suma', 0) for s in segs), 1)) for d in D) + " |")
L.append("")
L.append("### Memoria y carga del equipo (maximos sobre los segmentos)")
L.append("")
L.append("| Version | RSS max (MB) | Privada max (MB) | CPU sistema p50 (%) | CPU sistema max (%) | Memoria del equipo max (%) | Disponible min (MB) | Confirmada max / limite (MB) |")
L.append("|---|---|---|---|---|---|---|---|")
for n, d in zip(nombres, D):
    m = [d["segmentos"][s]["memoria_mb"] for s in segs]; q = [d["segmentos"][s]["equipo"] for s in segs]
    L.append(f"| {n} | {max(x['rss_max'] for x in m)} | {max(x['privada_max'] for x in m)} | {q[0]['cpu_sistema_pct_p50']} (normal) | {max(x['cpu_sistema_pct_max'] for x in q)} | {max(x['mem_carga_pct_max'] for x in q)} | {min(x['mem_disponible_mb_min'] for x in q)} | {max(x['confirmada_mb_max'] for x in q)} / {q[0]['limite_confirmacion_mb']} |")
open(sal, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
