"""Rendimiento secuencial por segmento y criterio R1-R4 (CRITERIO-ACEPTACION-RENDIMIENTO.md, fijado antes de medir).
Uso: python rendimiento_secuencial.py marcas.jsonl dir_replay salida.json [inventario_ausentes.json]
Segmentos: normal 07:32:00-08:05:00; inundacion_http-rN [inicio, fin]; recuperacion (fin, fin+120].
Retraso de decision = logged_at - window_end (ventanas con fin en el segmento)."""
import json, sys, datetime as dt, collections
ts = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
marcas, rep, salida = sys.argv[1], sys.argv[2], sys.argv[3]
ausentes = json.load(open(sys.argv[4], encoding="utf-8")) if len(sys.argv) > 4 else None

ep = {}
for l in open(marcas, encoding="utf-8"):
    r = json.loads(l)
    if r.get("evento") in ("inicio", "fin") and str(r.get("episodio_id", "")).startswith("inundacion_http"):
        ep.setdefault(r["episodio_id"], {})[r["evento"]] = ts(r["reloj"]["pared_utc"])
seg = {"normal": (ts("2026-11-01T07:32:00Z"), ts("2026-11-01T08:05:00Z"))}
for e, m in sorted(ep.items()):
    seg[e] = (m["inicio"], m["fin"])
    seg[e.replace("inundacion_http", "recuperacion")] = (m["fin"], m["fin"] + 120)

arnes = [json.loads(l) for l in open(rep + "/ciclos-arnes.jsonl", encoding="utf-8")]
motor = [json.loads(l) for l in open(rep + "/_state/ciclos.jsonl", encoding="utf-8")]
dec, noev, canc = [], [], []
for l in open(rep + "/motor_decision.log", encoding="utf-8"):
    r = json.loads(l)
    if r.get("event") == "decision":
        dec.append((ts(r["window_end_utc"]), r["logged_at"] - ts(r["window_end_utc"])))
    elif r.get("event") == "ventana_no_evaluada":
        noev.append((ts(r["window_end_utc"]), r["motivo"]))
    elif r.get("event") == "pendiente_cancelada":
        canc.append(ts(r["window_end_utc"]))


def q(v, p):
    v = sorted(v)
    return round(v[min(len(v) - 1, int(p * len(v)))], 3) if v else None


def mx(v):
    return round(max(v), 3) if v else None


def resumen(a, b):
    cs = [c for c in arnes if a <= c["t"] <= b]
    ms = [c for c in motor if a <= c["inicio_ciclo"] <= b]
    lat = [x for w, x in dec if a < w <= b]
    dur = [c["dur_s"] for c in cs]
    cpu = [c["cpu_s"] for c in cs if "cpu_s" in c]
    etapas = collections.defaultdict(list)
    for c in ms:
        for k, v in c.get("etapas_s", {}).items():
            etapas[k].append(v)
    return {
        "ciclos": len(cs),
        "pared_s": {"p50": q(dur, .5), "p95": q(dur, .95), "max": mx(dur),
                    "n_gt_10": sum(x > 10 for x in dur), "n_gt_20": sum(x > 20 for x in dur)},
        "cpu_s": {"p50": q(cpu, .5), "p95": q(cpu, .95), "max": mx(cpu)},
        "etapas_motor_s": {k: {"p50": q(v, .5), "p95": q(v, .95), "max": mx(v), "suma": round(sum(v), 2)}
                           for k, v in sorted(etapas.items())},
        "decididas_por_ciclo_max": max((c.get("decididas", 0) for c in ms), default=None),
        "retraso_decision_s": {"n": len(lat), "p50": q(lat, .5), "p95": q(lat, .95), "max": mx(lat)},
        "pendientes": {"max": max((c["ventanas_pendientes"] for c in ms), default=None),
                       "al_final": ms[-1]["ventanas_pendientes"] if ms else None},
        "memoria_mb": {"rss_max": mx([c.get("rss_mb", 0) for c in cs]), "pico": mx([c.get("pico_mb", 0) for c in cs]),
                       "privada_max": mx([c.get("privada_mb", 0) for c in cs])},
        "equipo": {"cpu_sistema_pct_p50": q([c["cpu_sistema_pct"] for c in cs if "cpu_sistema_pct" in c], .5),
                   "cpu_sistema_pct_max": mx([c["cpu_sistema_pct"] for c in cs if "cpu_sistema_pct" in c]),
                   "mem_carga_pct_max": mx([c["mem_carga_pct"] for c in cs if "mem_carga_pct" in c]),
                   "mem_disponible_mb_min": min((c["mem_disponible_mb"] for c in cs if "mem_disponible_mb" in c), default=None),
                   "confirmada_mb_max": mx([c["confirmada_mb"] for c in cs if "confirmada_mb" in c]),
                   "limite_confirmacion_mb": max((c.get("limite_confirmacion_mb", 0) for c in cs), default=None)},
        "no_evaluadas": dict(collections.Counter(m for w, m in noev if a < w <= b)),
        "canceladas": sum(1 for w in canc if a < w <= b),
    }


out = {k: resumen(*v) for k, v in seg.items()}
normal = out["normal"]
umbral_r3 = (normal["retraso_decision_s"]["p95"] or 0) + 5
crit = {}
for k, v in seg.items():
    r = out[k]
    c = {}
    c["R1"] = (r["pared_s"]["p95"] is not None and r["pared_s"]["p95"] <= 10 and r["pared_s"]["max"] <= 20)
    c["R2"] = (r["retraso_decision_s"]["p95"] is not None and r["retraso_decision_s"]["p95"] <= 15
               and r["retraso_decision_s"]["max"] <= 25)
    malas = sum(n for m, n in r["no_evaluadas"].items() if m in ("pcap_incompleto", "ventana_no_regenerada"))
    aus = None
    if ausentes is not None:
        aus = sum(1 for w in ausentes if v[0] < w <= v[1])
    c["R4"] = malas == 0 and (aus in (0, None))
    c["R4_detalle"] = {"no_evaluadas_rendimiento": malas, "ausentes": aus}
    if k.startswith("recuperacion"):
        fin = v[0]
        lat = sorted((w, x) for w, x in dec if fin < w <= v[1])
        # primer instante desde el que TODA ventana de la recuperacion queda <= umbral
        ultimo_malo = max((w for w, x in lat if x > umbral_r3), default=None)
        t_rec = 0.0 if ultimo_malo is None else ultimo_malo - fin
        pend_fin = r["pendientes"]["al_final"]
        c["R3"] = t_rec <= 60 and pend_fin is not None and pend_fin <= normal["pendientes"]["max"]
        c["R3_detalle"] = {"umbral_retraso_s": round(umbral_r3, 3), "vuelve_en_s": round(t_rec, 3),
                           "pendientes_al_final": pend_fin, "pendientes_max_normal": normal["pendientes"]["max"]}
        # la recuperacion se juzga con R2 tambien (retraso), y R1
    crit[k] = c
todos = all(c["R1"] and c["R2"] and c["R4"] and c.get("R3", True) for c in crit.values())
res = {"replay": rep, "segmentos": out, "criterio": crit, "cumple_todo": todos}
json.dump(res, open(salida, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k in seg:
    r, c = out[k], crit[k]
    print(f"{k:22s} ciclos={r['ciclos']:4d} pared p50/p95/max={r['pared_s']['p50']}/{r['pared_s']['p95']}/{r['pared_s']['max']}"
          f" >10={r['pared_s']['n_gt_10']} >20={r['pared_s']['n_gt_20']} cpu_max={r['cpu_s']['max']}"
          f" retraso p95/max={r['retraso_decision_s']['p95']}/{r['retraso_decision_s']['max']}"
          f" pend max/fin={r['pendientes']['max']}/{r['pendientes']['al_final']}"
          f" R1={c['R1']} R2={c['R2']} R3={c.get('R3', '-')} R4={c['R4']}")
print("CUMPLE TODO:", todos)
