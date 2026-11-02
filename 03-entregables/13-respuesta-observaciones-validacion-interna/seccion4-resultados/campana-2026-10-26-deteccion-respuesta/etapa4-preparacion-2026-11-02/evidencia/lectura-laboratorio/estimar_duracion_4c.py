"""Estima la duración de la batería 4C con las duraciones REALES por escenario del 3B (mismos parámetros y tiempos
60/120/90). Solo lee. Uso: python -I estimar_duracion_4c.py <marcas_3b.jsonl> <escenarios-4c.json> <carpeta_campana>
El orden se recalcula con generar_campana.plan_orden (el mismo del generador)."""
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

marcas, cfg = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
sys.path.insert(0, str(Path(sys.argv[3]) / "scripts"))
import generar_campana as g  # noqa: E402
ini, dur = {}, {}
eventos = []
for ln in open(marcas, encoding="utf-8"):
    r = json.loads(ln)
    t = datetime.fromisoformat(r["reloj"]["pared_utc"]).timestamp()
    eventos.append((r["evento"], t))
    if r["evento"] == "inicio":
        ini[r["episodio_id"]] = t
    elif r["evento"] == "fin":
        dur.setdefault(r["episodio_id"].rsplit("-r", 1)[0], []).append(t - ini[r["episodio_id"]])
t0 = eventos[0][1]
t_fin = max(t for e, t in eventos if e == "fin")
por = {k: {"n": len(v), "media_s": round(statistics.mean(v), 1), "min_s": round(min(v), 1), "max_s": round(max(v), 1)}
       for k, v in sorted(dur.items())}
orden = [f"{s['id']}-r{r}" for s, r in g.plan_orden(cfg)]
est = 60 + sum(por[e.rsplit("-r", 1)[0]]["media_s"] for e in orden) + len(orden) * 120 + (len(orden) - 1) * 90
t, plan = 60.0, []
for e in orden:
    t += 120
    d = por[e.rsplit("-r", 1)[0]]["media_s"]
    plan.append({"n": len(plan) + 1, "episodio": e, "inicio_rel_s": round(t), "fin_rel_s": round(t + d)})
    t += d + 90
out = {"orden": orden, "plan_estimado": plan, "duracion_por_escenario_3b": por, "bateria_3b_real_s": round(t_fin - t0, 1),
       "bateria_4c_estimada_s": round(est, 1), "bateria_4c_estimada_h": round(est / 3600, 2),
       "nota": "60 s de calentamiento + 120 s de contexto antes de cada episodio + 90 s de observación entre episodios"}
print(json.dumps(out, ensure_ascii=False, indent=1))
