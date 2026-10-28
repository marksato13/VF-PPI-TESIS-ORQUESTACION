#!/usr/bin/env python3
"""Compara, por la MISMA clave (entidad, window_end), el motor de produccion y el candidato corregido (solo lectura).

Referencias por clave:
  * COMPLETO : la ventana recalculada con el codigo del motor sobre las fuentes completas (PCAP archivados + eve.json),
               como diag_ventanas.py. Da el packet_count_10s real y todas las features.
  * EMULADO  : para cada decision del CANDIDATO, la entrada exacta que tenia al decidir, reconstruida con lo que el
               propio candidato registra (inicio_ciclo, marca_pcap, marca_eve): paquetes en [marca_pcap-230, marca_pcap],
               EVE en [inicio_ciclo-230, marca_eve]. Si pk10 y score coinciden, las features del score son las mismas.
Informa: ceros con trafico, conteos distintos, pendientes recuperadas, no evaluadas, duplicados, claves que faltan,
diferencias de features EMULADO vs COMPLETO (las que pueden mover el score) y logged_at - window_end de cada motor.
"""
from __future__ import annotations
import argparse, bisect, collections, ipaddress, json, statistics, sys
from pathlib import Path

RAIZ = Path.home() / "cyberflow"
sys.path.insert(0, str(RAIZ / "scripts" / "features"))
import extract_multilayer_v2 as v2  # noqa: E402
import extract_multilayer_v3 as v3  # noqa: E402
import joblib  # noqa: E402

HIST = 230.0
EXCL = "10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32"
MODELO = RAIZ / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"


def ts(iso: str) -> float:
    return v2.parse_eve_timestamp(iso)


def cuantiles(xs):
    if len(xs) < 3:
        return "n<3"
    q = statistics.quantiles(xs, n=20)
    return f"n={len(xs)} min {min(xs):.2f} p5 {q[0]:.2f} mediana {statistics.median(xs):.2f} p95 {q[-1]:.2f} max {max(xs):.2f} s"


def leer_log(p: Path, d0: float, d1: float, excl):
    dec, noev, arranques = collections.defaultdict(list), collections.defaultdict(list), []
    with p.open(encoding="utf-8") as fh:
        for l in fh:
            try:
                r = json.loads(l)
            except json.JSONDecodeError:
                continue
            ev = r.get("event")
            if ev == "motor_startup":
                arranques.append(r)
            if ev not in ("decision", "ventana_no_evaluada"):
                continue
            if not (d0 <= ts(r["window_end_utc"]) <= d1) or excl(r["entity_ip"]):
                continue
            (dec if ev == "decision" else noev)[(r["entity_ip"], r["window_end_utc"])].append(r)
    return dec, noev, arranques


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", action="append", required=True, type=Path)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--prod", type=Path, default=RAIZ / "logs/motor_decision.log")
    ap.add_argument("--cand", type=Path, required=True)
    ap.add_argument("--eve", type=Path, default=Path("/var/log/suricata/eve.json"))
    ap.add_argument("--ejemplos", type=int, default=5)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    d0, d1 = ts(a.desde), ts(a.hasta)
    red = ipaddress.ip_network("10.10.0.0/16")
    fuera = [ipaddress.ip_network(t, strict=False) for t in EXCL.split(",")]
    excl = lambda ip: any(ipaddress.ip_address(ip) in r for r in fuera)
    pipe = joblib.load(MODELO); nombres = v2.FEATURE_NAMES

    def sc(f):
        return float(pipe.score_samples([[float(f[n]) for n in nombres]])[0]) if f and int(f["packet_count_10s"]) else None

    # --- PCAP archivados (codigo del motor)
    ficheros = sorted({p for d in a.archivo for p in d.glob("live-*.pcap")}, key=lambda p: p.name)
    ctx, tramas, vlan, rotaciones = [], 0, 0, 0
    for f in ficheros:
        hay = False
        for t, tr in v2.iter_pcap_frames(f):
            if not (d0 - 600 <= t <= d1 + 120):
                continue
            hay = True; tramas += 1
            c = v3.parse_con_contexto(t, tr)
            if c is None:
                continue
            vlan += int(bool(c.vlan))
            if c.packet.protocol not in (112, 240):
                ctx.append(c)
        rotaciones += int(hay)
    ctx.sort(key=lambda c: c.packet.timestamp); ctx_t = [c.packet.timestamp for c in ctx]

    # --- EVE
    eve = []
    with a.eve.open("r", encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            i = linea.find('"timestamp":"')
            if i < 0:
                continue
            try:
                t = ts(linea[i + 13:i + 44].split('"')[0])
            except ValueError:
                continue
            if d0 - 600 <= t <= d1 + 120:
                eve.append((t, linea))
    eve.sort(key=lambda x: x[0]); eve_t = [x[0] for x in eve]
    tmp = Path("/tmp/comparar_eve.jsonl")

    def apps_en(lo_t, hi_t):
        lo, hi = bisect.bisect_left(eve_t, lo_t), bisect.bisect_right(eve_t, hi_t)
        with tmp.open("w", encoding="utf-8") as out:
            for _, l in eve[lo:hi]:
                out.write(l)
        return v2.load_app_observations(tmp, red)

    def filas(paq_ctx, apps, ents, capture_epoch):
        paq, _ = v3.deduplicar_espejo(paq_ctx)
        at = v2.attribute_packets(paq, red)
        out = {}
        for e in ents:
            pe = [p for p in at if p.entity_ip == e]; ae = [x for x in apps if x.entity_ip == e]
            obs = [p.timestamp for p in pe] + [x.timestamp for x in ae]
            if obs:
                for r in v2.build_rows("cmp", pe, ae, step_seconds=10, capture_start=min(capture_epoch, min(obs))):
                    out[(e, r["window_end_utc"])] = r
        return out

    # --- COMPLETO
    paq, _ = v3.deduplicar_espejo(ctx)
    at = v2.attribute_packets(paq, red)
    apps_all = apps_en(d0 - 600, d1 + 120)
    inicio = min([p.timestamp for p in at] + [x.timestamp for x in apps_all])
    completo = {(r["entity_ip"], r["window_end_utc"]): r
                for r in v2.build_rows("completo", at, apps_all, step_seconds=10, capture_start=inicio)
                if d0 <= ts(r["window_end_utc"]) <= d1 and not excl(r["entity_ip"])}

    # --- registros
    p_dec, _, _ = leer_log(a.prod, d0, d1, excl)
    c_dec, c_noev, c_arr = leer_log(a.cand, d0, d1, excl)
    epoch_cand = float(c_arr[-1].get("timestamp", c_arr[-1].get("logged_at", 0))) if c_arr else d0 - 600

    # --- EMULADO del candidato por ciclo (inicio_ciclo, marca_pcap, marca_eve exactos)
    por_ciclo = collections.defaultdict(list)
    for k, regs in c_dec.items():
        r = regs[0]
        por_ciclo[(r["inicio_ciclo"], r["marca_pcap"], r["marca_eve"])].append(k)
    emulado = {}
    for (ini, mp, me), claves in por_ciclo.items():
        lo, hi = bisect.bisect_left(ctx_t, mp - HIST), bisect.bisect_right(ctx_t, mp)
        fil = filas(ctx[lo:hi], apps_en(ini - HIST, me), {k[0] for k in claves}, epoch_cand)
        for k in claves:
            emulado[k] = fil.get(k)

    # --- comparacion
    claves = sorted(set(completo) | set(p_dec) | set(c_dec) | set(c_noev), key=lambda k: (k[1], k[0]))
    cnt = collections.Counter(); ej = collections.defaultdict(list); dump = []
    feat_dif = collections.Counter(); ret_p, ret_c, ret_marca, espera = [], [], [], []
    for k in claves:
        c = completo.get(k); pk_c = int(c["packet_count_10s"]) if c else None
        pr = p_dec.get(k, []); cr = c_dec.get(k, []); ne = c_noev.get(k, [])
        we = ts(k[1])
        cnt["prod_duplicadas"] += int(len(pr) > 1); cnt["cand_duplicadas"] += int(len(cr) + len(ne) > 1)
        fila = {"clave": k, "completo_pk10": pk_c}
        if pr:
            r = pr[0]; ret_p.append(float(r["logged_at"]) - we)
            pk = int(r["packet_count_10s"]); fila["prod"] = [pk, r.get("score")]
            cnt["prod_decisiones"] += 1
            if pk_c is None:
                cnt["prod_sin_referencia"] += 1
            elif pk == 0 and pk_c > 0:
                cnt["prod_cero_con_trafico"] += 1; ej["prod_cero_con_trafico"].append(fila)
            elif pk != pk_c:
                cnt["prod_conteo_distinto"] += 1; ej["prod_conteo_distinto"].append(fila)
            else:
                cnt["prod_pk10_igual_completo"] += 1
        if cr:
            r = cr[0]; ret_c.append(float(r["logged_at"]) - we); ret_marca.append(r["marca_pcap"] - we)
            if r.get("pendiente_desde") is not None:
                espera.append(float(r["logged_at"]) - float(r["pendiente_desde"]))
                cnt["cand_pendientes_recuperadas"] += 1
            pk = int(r["packet_count_10s"]); fila["cand"] = [pk, r.get("score"), r.get("pendiente_desde") is not None]
            cnt["cand_decisiones"] += 1
            if pk_c is None:
                cnt["cand_sin_referencia"] += 1
            elif pk == 0 and pk_c > 0:
                cnt["cand_cero_con_trafico"] += 1; ej["cand_cero_con_trafico"].append(fila)
            elif pk != pk_c:
                cnt["cand_conteo_distinto"] += 1; ej["cand_conteo_distinto"].append(fila)
            else:
                cnt["cand_pk10_igual_completo"] += 1
            e = emulado.get(k); s = sc(e)
            ok = e is not None and int(e["packet_count_10s"]) == pk and \
                ((s is None and r.get("score") is None) or (s is not None and r.get("score") is not None and abs(s - r["score"]) < 1e-9))
            cnt["cand_reproducida_exacta"] += int(ok)
            if not ok:
                fila["emulado"] = [e["packet_count_10s"] if e else None, s]; ej["cand_no_reproducida"].append(fila)
            if e is not None and c is not None:
                dif = {n: (round(float(e[n]), 6), round(float(c[n]), 6)) for n in nombres if abs(float(e[n]) - float(c[n])) > 1e-6}
                for n in dif:
                    feat_dif[n] += 1
                if dif:
                    fila["features_emulado_vs_completo"] = dif
                    fila["score_completo"] = sc(c)
                cnt["cand_features_iguales_completo"] += int(not dif)
        if ne:
            cnt["cand_no_evaluadas"] += 1; fila["no_evaluada"] = ne[0].get("motivo"); ej["cand_no_evaluada"].append(fila)
        if pk_c and pk_c > 0:
            cnt["completo_con_trafico"] += 1
            if not pr:
                cnt["prod_falta_con_trafico"] += 1
            if not cr and not ne:
                cnt["cand_falta_con_trafico"] += 1; ej["cand_falta_con_trafico"].append(fila)
        if pr and cr and int(pr[0]["packet_count_10s"]) == int(cr[0]["packet_count_10s"]):
            cnt["ambos_mismo_pk10"] += 1
            sp, scd = pr[0].get("score"), cr[0].get("score")
            cnt["ambos_mismo_pk10_mismo_score"] += int((sp is None and scd is None) or (sp is not None and scd is not None and abs(sp - scd) < 1e-9))
        if pr and cr and pr[0].get("decision") != cr[0].get("decision"):
            cnt["decision_distinta_prod_cand"] += 1; ej["decision_distinta"].append(
                {**fila, "dec": [pr[0].get("decision"), cr[0].get("decision")], "det": [pr[0].get("detector_name"), cr[0].get("detector_name")]})
        dump.append(fila)

    print(f"## ventanas [{a.desde}, {a.hasta}] | ficheros PCAP con datos en rango {rotaciones} | tramas {tramas} (802.1Q {100*vlan/max(tramas,1):.1f} %)")
    print(f"   arranque candidato registrado {epoch_cand} | claves totales {len(claves)} | filas completas {len(completo)}")
    for k in sorted(cnt):
        print(f"   {k:42s} {cnt[k]}")
    print(f"## logged_at - window_end  produccion: {cuantiles(ret_p)}")
    print(f"## logged_at - window_end  candidato : {cuantiles(ret_c)}")
    print(f"## marca_pcap - window_end candidato : {cuantiles(ret_marca)}")
    print(f"## espera de pendientes (logged_at - pendiente_desde): {cuantiles(espera)}")
    print("## features EMULADO(candidato) distintas de COMPLETO, por feature (claves)")
    for n, v in feat_dif.most_common():
        print(f"   {n:42s} {v}")
    print("## ejemplos")
    for k, lst in ej.items():
        for f in lst[:a.ejemplos]:
            print(f"   [{k}] {json.dumps(f, default=str)[:700]}")
    if a.json:
        a.json.write_text("\n".join(json.dumps(f, default=str) for f in dump) + "\n", encoding="utf-8")
        print(f"## por clave -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
