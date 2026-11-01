#!/usr/bin/env python3
"""PASO2 (20261101T0254Z): analisis de la validacion en vivo del motor incremental. Solo biblioteca estandar.

Lee las copias conservadas (ciclos, registro de decisiones, marcas del generador, muestras de recursos, segmento EVE,
stats.log de Suricata, estado del archivador y, si existe, el registro de la repeticion offline) y escribe
resultados.json. No toca nada operativo.
"""
from __future__ import annotations
import argparse, collections, json, re, statistics
from datetime import datetime, timezone
from pathlib import Path

KALI, SRV = "10.10.20.30", "10.10.30.10"
U = {"desplegado": -0.5693969936322356, "0.05": -0.5694578968203694, "0.03": -0.5898535710336618,
     "0.01": -0.6223889502095352}
HIST = 230.0


def ep(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def q(v: list[float], p: float) -> float | None:
    if not v:
        return None
    v = sorted(v)
    k = (len(v) - 1) * p
    i = int(k)
    return v[i] if i + 1 >= len(v) else v[i] + (v[i + 1] - v[i]) * (k - i)


def resumen(v: list[float]) -> dict:
    return {"n": len(v), "p50": q(v, .5), "p95": q(v, .95), "max": max(v) if v else None,
            "min": min(v) if v else None}


def jl(p: Path):
    out = []
    for x in p.open(encoding="utf-8", errors="replace"):
        x = x.strip()
        if x:
            try:
                out.append(json.loads(x))
            except json.JSONDecodeError:
                pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--t-normal", required=True, type=ep)
    ap.add_argument("--t-fin", required=True, type=ep)
    ap.add_argument("--replay", type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    ap.add_argument("--copias", default="copias")
    a = ap.parse_args()
    B = a.base
    T0 = float((B / "reinicio.t").read_text().split()[0])
    ciclos = [c for c in jl(B / a.copias / "ciclos.jsonl") if c.get("event") == "ciclo" and c["inicio_ciclo"] >= T0 - 1]
    regs_all = jl(B / a.copias / "motor_decision.log")
    marcas = jl(B / a.copias / "marcas-episodios.jsonl")
    eps = {}
    for m in marcas:
        if m.get("evento") == "inicio":
            eps.setdefault(m["episodio_id"], {})["ini"] = ep(m["reloj"]["pared_utc"])
        elif m.get("evento") == "fin":
            e = eps.setdefault(m["episodio_id"], {})
            e.update(fin=ep(m["reloj"]["pared_utc"]), estado=m["estado"], rc=m.get("codigo_salida"),
                     intentos=m.get("intentos_generador"))
    orden = sorted(eps, key=lambda k: eps[k]["ini"])

    def condicion(t: float) -> str:
        if t < T0 + HIST:
            return "calentamiento"
        if a.t_normal <= t < (eps[orden[0]]["ini"] if orden else a.t_fin):
            return "normal"
        for k in orden:
            e = eps[k]
            if e["ini"] <= t <= e["fin"]:
                return "inundacion_" + k.split("-r")[-1]
            if e["fin"] < t <= e["fin"] + HIST:
                return "recuperacion_" + k.split("-r")[-1]
        return "entre_o_cierre" if t <= a.t_fin else "posterior"

    conds = ["calentamiento", "normal"] + [f"{p}_{k.split('-r')[-1]}" for k in orden for p in ("inundacion", "recuperacion")] \
        + ["entre_o_cierre"]
    R = {"T_reinicio": T0, "t_normal": a.t_normal, "t_fin": a.t_fin,
         "episodios": {k: {**eps[k], "ini_utc": iso(eps[k]["ini"]), "fin_utc": iso(eps[k].get("fin")),
                           "duracion_s": eps[k].get("fin", 0) - eps[k]["ini"]} for k in orden},
         "condiciones": {}}
    porc = collections.defaultdict(list)
    for c in ciclos:
        porc[condicion(c["inicio_ciclo"])].append(c)
    cic_por_inicio = {round(c["inicio_ciclo"], 6): c for c in ciclos}

    # registros posteriores al reinicio
    regs = [r for r in regs_all if r.get("event") in ("decision", "ventana_no_evaluada") and r.get("logged_at", 0) >= T0]
    for r in regs:
        r["_wend"] = ep(r["window_end_utc"])
        c = cic_por_inicio.get(round(r.get("inicio_ciclo", -1), 6))
        r["_escrito"] = c.get("registro_escrito_en") if c else None
    porw = collections.defaultdict(list)
    for r in regs:
        porw[condicion(r["_wend"])].append(r)

    # recursos
    mu = jl(B / a.copias / "muestras.jsonl")
    for i in range(1, len(mu)):
        p, m = mu[i - 1], mu[i]
        dt = m["t"] - p["t"]
        m["_cpu_motor"] = (100.0 * ((m["utime"] + m["stime"]) - (p["utime"] + p["stime"])) / m["hz"] / dt) \
            if m["pid"] == p["pid"] and dt > 0 else None
        tp, ip = map(int, p["cpu_total_idle"].split()); tm, im = map(int, m["cpu_total_idle"].split())
        m["_cpu_sistema"] = 100.0 * (1 - (im - ip) / (tm - tp)) if tm > tp else None
        m["_rxdrop"] = int(m["ens37_rx_drop"].split()[1]) - int(p["ens37_rx_drop"].split()[1])
        m["_pswpout"] = m["pswpout"] - p["pswpout"]
        m["_pswpin"] = m["pswpin"] - p["pswpin"]
    porm = collections.defaultdict(list)
    for m in mu[1:]:
        porm[condicion(m["t"])].append(m)

    # suricata kernel drops (stats.log)
    sur = []
    for f in (a.copias + "/stats-inicio.log", a.copias + "/stats-fin.log"):
        p = B / f
        if not p.exists():
            continue
        t = None; vals = {}
        for line in p.open(errors="replace"):
            mm = re.match(r"Date: (\d+)/(\d+)/(\d+) -- (\d+):(\d+):(\d+)", line)
            if mm:
                if t and vals:
                    sur.append((t, dict(vals)))
                mo, d, y, h, mi, s = map(int, mm.groups())   # stats.log: M/D/YYYY, hora del sensor (UTC)
                t = datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp(); vals = {}
                continue
            mm = re.match(r"(capture\.kernel_packets|capture\.kernel_drops)\s*\|\s*Total\s*\|\s*(\d+)", line)
            if mm:
                vals[mm.group(1)] = vals.get(mm.group(1), 0) + int(mm.group(2))
        if t and vals:
            sur.append((t, dict(vals)))
    sur = sorted({t: v for t, v in sur}.items())

    def sur_delta(t1, t2):
        a1 = [v for t, v in sur if t <= t1]; a2 = [v for t, v in sur if t <= t2]
        if not a1 or not a2:
            return None
        return {k: a2[-1].get(k, 0) - a1[-1].get(k, 0) for k in ("capture.kernel_packets", "capture.kernel_drops")}

    # EVE: http de la Kali al servidor
    http = collections.defaultdict(dict)
    evp = B / a.copias / "eve-segmento.json"
    if evp.exists():
        for line in evp.open(errors="replace"):
            if '"10.10.20.30"' not in line or '"http"' not in line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("event_type") != "http" or e.get("src_ip") != KALI or e.get("dest_ip") != SRV:
                continue
            t = ep(e["timestamp"].replace("+0000", "+00:00"))
            # El SPAN ve cada peticion dos veces: en la VLAN 20 (Kali -> pfSense) y en la VLAN 30 (pfSense -> servidor),
            # como flujos distintos (flow_id distinto). Se cuenta solo la observacion de la VLAN de origen (20), por
            # (flow_id, tx_id). El puerto de origen NO sirve de clave: se reutiliza en ~28 000 conexiones por episodio.
            if e.get("vlan") != [20]:
                continue
            key = (e.get("flow_id"), e.get("tx_id"))
            http[condicion(t)][key] = (t, (e.get("http") or {}).get("status"), (e.get("http") or {}).get("http_user_agent"))

    for cond in conds:
        cs = porc.get(cond, [])
        if not cs and not porw.get(cond):
            continue
        t_ini = min((c["inicio_ciclo"] for c in cs), default=None)
        t_fin = max((c["fin_ciclo"] for c in cs), default=None)
        d = [c["duracion_s"] for c in cs]
        et = collections.defaultdict(list)
        for c in cs:
            for k, v in c["etapas_s"].items():
                et[k].append(v)
        pend = [c["ventanas_pendientes"] for c in cs]
        n3 = max(1, len(pend) // 3)
        ws = porw.get(cond, [])
        dec = [r for r in ws if r["event"] == "decision"]
        ne = [r for r in ws if r["event"] == "ventana_no_evaluada"]
        ms = porm.get(cond, [])
        hx = http.get(cond, {})
        R["condiciones"][cond] = {
            "intervalo_ciclos": [iso(t_ini), iso(t_fin)],
            "ciclos": resumen(d),
            "ciclos_mas_9_5": sum(x > 9.5 for x in d), "ciclos_mas_10": sum(x > 10 for x in d),
            "lista_mas_9_5": [(iso(c["inicio_ciclo"]), c["duracion_s"]) for c in cs if c["duracion_s"] > 9.5],
            "margen_10s_min": (10 - max(d)) if d else None,
            "etapas": {k: resumen(v) for k, v in sorted(et.items())},
            "edad_marca_pcap": resumen([c["inicio_ciclo"] - c["marca_pcap"] for c in cs if c.get("marca_pcap")]),
            "edad_marca_eve": resumen([c["inicio_ciclo"] - c["marca_eve"] for c in cs if c.get("marca_eve")]),
            "marca_pcap_no_avanzo": sum(not c.get("marca_pcap_avanzo", True) for c in cs),
            "ciclos_sin_decisiones_nuevas": sum(c["decididas"] == 0 for c in cs),
            "pendientes": {**resumen(pend), "media_primer_tercio": statistics.mean(pend[:n3]) if pend else None,
                           "media_ultimo_tercio": statistics.mean(pend[-n3:]) if pend else None},
            "ventanas_por_window_end": {"decisiones": len(dec), "no_evaluadas": len(ne),
                                        "no_evaluadas_motivos": dict(collections.Counter(r.get("motivo") for r in ne)),
                                        "entidades": len({r["entity_ip"] for r in ws})},
            "retraso_decidido_menos_wend": resumen([r["decidido_en"] - r["_wend"] for r in dec if "decidido_en" in r]),
            "retraso_logged_menos_wend": resumen([r["logged_at"] - r["_wend"] for r in dec]),
            "retraso_escrito_menos_wend": resumen([r["_escrito"] - r["_wend"] for r in dec if r["_escrito"]]),
            "escrito_menos_decidido": resumen([r["_escrito"] - r["decidido_en"] for r in dec if r["_escrito"] and "decidido_en" in r]),
            "orden_decidido_logged_escrito_ok": sum(1 for r in dec if r["_escrito"] and r["decidido_en"] <= r["logged_at"] <= r["_escrito"]),
            "orden_sin_ciclo": sum(1 for r in dec if not r["_escrito"]),
            "recursos": {
                "cpu_motor_pct": resumen([m["_cpu_motor"] for m in ms if m.get("_cpu_motor") is not None]),
                "cpu_sistema_pct": resumen([m["_cpu_sistema"] for m in ms if m.get("_cpu_sistema") is not None]),
                "rss_mb_max": max((m["rss_kb"] for m in ms), default=0) / 1024,
                "hwm_mb_max": max((m["hwm_kb"] for m in ms), default=0) / 1024,
                "memavail_mb_min": min((m["memavail_kb"] for m in ms), default=0) / 1024,
                "swap_usado_mb_max": max((m["swaptotal_kb"] - m["swapfree_kb"] for m in ms), default=0) / 1024,
                "pswpin": sum(m["_pswpin"] for m in ms), "pswpout": sum(m["_pswpout"] for m in ms),
                "psi_mem_some10_max": max((m["psi_mem_some10"] for m in ms), default=0),
                "load1_max": max((m["load1"] for m in ms), default=0),
                "ens37_rx_drop": sum(m["_rxdrop"] for m in ms), "muestras": len(ms)},
            "suricata": sur_delta(t_ini, t_fin) if t_ini else None,
            "http_kali_servidor": {"transacciones_unicas": len(hx),
                                   "con_respuesta": sum(1 for v in hx.values() if v[1] is not None),
                                   "estados": dict(collections.Counter(str(v[1]) for v in hx.values())),
                                   "agente_preparacion": sum(1 for v in hx.values() if (v[2] or "").startswith("cf-preparacion"))},
        }

    # duplicados
    def dup(rs):
        k = collections.Counter((r["entity_ip"], r["window_end_utc"]) for r in rs if r.get("event") in ("decision", "ventana_no_evaluada"))
        return sum(n - 1 for n in k.values() if n > 1), [x for x, n in k.items() if n > 1][:10]
    rot = jl(B / a.copias / "motor_decision.log.1") if (B / a.copias / "motor_decision.log.1").exists() else []
    antes = [r for r in regs_all if r.get("logged_at", 0) < T0]
    R["duplicados"] = {"vigente_total": dup(regs_all), "solo_antes_instalacion_rotado_y_vigente": dup(rot + antes),
                       "solo_despues_instalacion": dup(regs), "rotado_mas_vigente": dup(rot + regs_all),
                       "registros_rotado": len(rot), "registros_vigente": len(regs_all),
                       "registros_despues": len(regs)}

    # deteccion: Kali
    kal = sorted([r for r in regs if r["entity_ip"] == KALI and r["event"] == "decision"], key=lambda r: r["_wend"])
    det = {}
    for k in orden:
        e = eps[k]
        rel = [r for r in kal if e["ini"] - 30 <= r["_wend"] <= e["fin"] + 60 + HIST]
        filas = []
        for r in rel:
            s = r.get("score")
            h = r.get("heuristico")
            der = {f"IF_{x}": (s is not None and r.get("packet_count_10s", 0) > 0 and s < U[x]) for x in ("0.05", "0.03", "0.01")}
            der["HEUR"] = h is not None
            for x in ("0.05", "0.03", "0.01"):
                der[f"HIB_{x}"] = der[f"IF_{x}"] or der["HEUR"]
            filas.append({"window_end": iso(r["_wend"]), "decidido_en": iso(r.get("decidido_en")),
                          "logged_at": iso(r["logged_at"]), "escrito": iso(r["_escrito"]),
                          "rel_inicio_s": round(r["_wend"] - e["ini"], 1), "decision": r.get("decision"),
                          "score": s, "threshold_registrado": r.get("threshold"), "heuristico": h,
                          "packet_count_10s": r.get("packet_count_10s"), "derivadas": der,
                          "fase": ("antes" if r["_wend"] < e["ini"] else "durante" if r["_wend"] <= e["fin"] + 10
                                   else "posterior_60" if r["_wend"] <= e["fin"] + 60 else "cola")})
        emit = [f for f in filas if f["decision"] == "ALERT" or f["heuristico"]]
        dur = [f for f in emit if f["fase"] == "durante"]
        primera = min((r for r in rel if (r.get("decision") == "ALERT" or r.get("heuristico")) and e["ini"] <= r["_wend"] <= e["fin"] + 10),
                      key=lambda r: r["logged_at"], default=None)
        det[k] = {"filas": filas, "emitidas": len(emit), "emitidas_durante": len(dur),
                  "primera_emision_durante": None if not primera else {
                      "window_end": iso(primera["_wend"]), "logged_at": iso(primera["logged_at"]),
                      "escrito": iso(primera["_escrito"]),
                      "latencia_logged_desde_inicio_s": primera["logged_at"] - e["ini"],
                      "latencia_escrito_desde_inicio_s": (primera["_escrito"] - e["ini"]) if primera["_escrito"] else None,
                      "decision": primera.get("decision"), "heuristico": primera.get("heuristico")},
                  "derivadas_durante": {c: sum(f["derivadas"][c] for f in filas if f["fase"] == "durante")
                                        for c in ("IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01")},
                  "ventanas_kali_durante": sum(f["fase"] == "durante" for f in filas)}
    R["deteccion"] = det
    R["alertas_no_kali_por_condicion"] = {c: dict(collections.Counter((r["entity_ip"], r.get("decision"), (r.get("heuristico") or {}).get("heuristico") if isinstance(r.get("heuristico"), dict) else r.get("heuristico"))
                                                                   for r in porw.get(c, []) if r["event"] == "decision" and r["entity_ip"] != KALI and (r.get("decision") == "ALERT" or r.get("heuristico"))))
                                          for c in R["condiciones"]}
    R["alertas_no_kali_por_condicion"] = {c: {str(k): v for k, v in d.items()} for c, d in R["alertas_no_kali_por_condicion"].items()}

    # inventario contra la repeticion offline
    if a.replay and a.replay.exists():
        rp = [r for r in jl(a.replay) if r.get("event") in ("decision", "ventana_no_evaluada")]
        lim_ini, lim_fin = a.t_normal + HIST, a.t_fin - 120
        ref = {(r["entity_ip"], r["window_end_utc"]): r for r in rp if lim_ini <= ep(r["window_end_utc"]) <= lim_fin}
        viv = {(r["entity_ip"], r["window_end_utc"]): r for r in regs if lim_ini <= r["_wend"] <= lim_fin}
        aus = sorted(set(ref) - set(viv), key=lambda k: k[1])
        sobr = sorted(set(viv) - set(ref), key=lambda k: k[1])
        comunes = set(ref) & set(viv)
        dif_dec = [k for k in comunes if ref[k].get("decision") != viv[k].get("decision") or ref[k]["event"] != viv[k]["event"]]
        dif_score = [k for k in comunes if ref[k].get("score") != viv[k].get("score")]
        porcond = collections.defaultdict(lambda: collections.Counter())
        for k in ref:
            porcond[condicion(ep(k[1]))]["esperadas"] += 1
        for k in aus:
            porcond[condicion(ep(k[1]))]["ausentes"] += 1
        for k in sobr:
            porcond[condicion(ep(k[1]))]["solo_en_vivo"] += 1
        R["inventario_replay"] = {"rango_window_end": [iso(lim_ini), iso(lim_fin)], "esperadas_replay": len(ref),
                                  "vivo": len(viv), "comunes": len(comunes), "ausentes_en_vivo": len(aus),
                                  "solo_en_vivo": len(sobr), "decision_distinta": len(dif_dec),
                                  "score_distinto": len(dif_score),
                                  "ejemplos_ausentes": aus[:20], "ejemplos_solo_vivo": sobr[:20],
                                  "ejemplos_score_distinto": [(k, ref[k].get("score"), viv[k].get("score"),
                                                               ref[k].get("packet_count_10s"), viv[k].get("packet_count_10s")) for k in dif_score[:15]],
                                  "por_condicion": {c: dict(v) for c, v in porcond.items()}}
    a.salida.write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("escrito", a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
