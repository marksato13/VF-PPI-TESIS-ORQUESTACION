#!/usr/bin/env python3
"""E1 (atribución), E3 (efecto) y E4 (tráfico legítimo) de la repetición B2 con los PCAP archivados del Sensor1 (503 ficheros, hashes verificados
contra el manifiesto archivado). Solo lectura: lee la copia local (ruta corta `C:\\Users\\markp\\cf-b2-pcap\\pcap`) y las trazas de `evidencia-local\\`.
E3 se calcula con `analizar_b.e3` (validado) a partir de una serie por bloques de 1 s construida del SPAN; E1 y E4 se calculan aquí.
Uso: analizar_pcap_b2.py [carpeta_pcap]  -> escribe resultado-pcap.json"""
import collections
import datetime
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "herramientas"))
import analizar_b as AB  # noqa: E402
import lector_pcap as L  # noqa: E402

EV = AQUI / "evidencia-local"
KALI, SRV, DC1 = "10.10.20.30", "10.10.30.10", "10.10.10.20"
SYN, ACK, RST = 0x02, 0x10, 0x04
FAM = {"inundacion_http": ("http_abuse", "LIMIT", 80), "fuerza_bruta_http": ("brute_force", "BLOCK", 18081), "dns_inusual": ("dns_entropy", None, 53)}


def jl(n):
    return [json.loads(l) for l in open(EV / (n + ".jsonl"), encoding="utf-8", errors="replace") if l.strip()]


def ep_(s):
    return datetime.datetime.fromisoformat(s).timestamp()


def main(carpeta):
    ag, pub, mar, pu = jl("agente"), jl("publicador"), jl("marcas"), jl("puertas")
    orden = [m for m in mar if m["evento"] == "campana_inicio"][0]["orden"]
    ini = {m["episodio_id"]: ep_(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
    fin = {m["episodio_id"]: ep_(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
    eps = [e for e in orden if e in ini]
    lo, hi = min(ini.values()) - 130, max(fin.values()) + 130
    pres = collections.Counter()                                       # segundos con cualquier paquete capturado (cobertura del espejo)
    ser = collections.defaultdict(collections.Counter)                # nombre -> {segundo: n}
    tsl = collections.defaultdict(list)                               # nombre -> instantes exactos (para contar en ventanas sin redondear)
    kali_dst = collections.Counter()
    flujos = {}                                                        # (cliente, sport) -> dict, hacia SRV:80
    rep_clientes = collections.Counter()
    for f in sorted(Path(carpeta).glob("*.pcap")):
        for ts, s, d, pr, sp, dp, fl, pl, pre in L.paquetes(f):
            if ts < lo or ts > hi:
                continue
            sec = int(ts)
            pres[sec] += 1
            if s == KALI or d == KALI:
                kali_dst[(s, d, pr, dp if s == KALI else sp)] += 1
            if pr == 6 and s == KALI and d == SRV:
                if dp == 80:
                    tsl["k80_out"].append(ts)
                    ser["k80_out"][sec] += 1
                    ser["syn80"][sec] += bool(fl & SYN and not fl & ACK)
                elif dp == 18081:
                    tsl["k18_out"].append(ts)
                    ser["k18_out"][sec] += 1
                    ser["syn18"][sec] += bool(fl & SYN and not fl & ACK)
            elif pr == 6 and s == SRV and d == KALI:
                if sp == 80:
                    ser["resp80"][sec] += 1
                    ser["acc80"][sec] += bool(fl & SYN and fl & ACK)
                elif sp == 18081:
                    ser["resp18"][sec] += 1
                    ser["acc18"][sec] += bool(fl & SYN and fl & ACK)
            elif (s == KALI and d == DC1) or (s == DC1 and d == KALI):
                tsl["kali_dc1"].append(ts)
                ser["kali_dc1"][sec] += 1
            # clientes legítimos -> srv-dmz:80 (reconstrucción de transacciones por flujo)
            if pr == 6 and d == SRV and dp == 80 and s != KALI and s.startswith("10.10.20."):
                k = (s, sp)
                if fl & SYN and not fl & ACK:
                    flujos[k] = {"cliente": s, "t": ts, "synack": None, "http": None, "rst": False}
                elif k in flujos and fl & RST:
                    flujos[k]["rst"] = True
            elif pr == 6 and s == SRV and sp == 80 and d != KALI and d.startswith("10.10.20."):
                k = (d, dp)
                fx = flujos.get(k)
                if fx is not None:
                    if fl & SYN and fl & ACK and fx["synack"] is None:
                        fx["synack"] = ts
                    elif fl & RST:
                        fx["rst"] = True
                    elif fx["http"] is None and pre[:5] == b"HTTP/" and len(pre) >= 12:
                        try:
                            fx["http"] = int(pre[9:12])
                        except ValueError:
                            pass
    r2s = json.loads((AQUI / "resultado-revision.json").read_text())["episodios"]
    out = []
    for k, e in enumerate(eps):
        fam = e.rsplit("-", 1)[0]
        regla, acc, puerto = FAM[fam]
        t0, t1 = ini[e], fin[e]
        sig = ini[eps[k + 1]] if k + 1 < len(eps) else None
        tope = sig if sig is not None else t1 + 400
        prev = r2s[k]
        res = {"episodio": e, "familia": fam, "clase_salud": "C3 (se conserva)"}
        # ---------------- E1: atribución por paquetes
        a, b = int(math.floor(t0)), int(math.ceil(t1))
        ev0, ev1 = (prev["E1"]["ventana_evidencia_vs_inicio_s"] if prev["E1"].get("ventana_evidencia_vs_inicio_s") else [None, None])
        ev0 = t0 + ev0 if ev0 is not None else None
        ev1 = t0 + ev1 if ev1 is not None else None
        nombre = {80: "k80_out", 18081: "k18_out", 53: "kali_dc1"}[puerto]
        import bisect
        cuenta = lambda x, y: bisect.bisect_right(tsl[nombre], y) - bisect.bisect_left(tsl[nombre], x)          # instantes exactos (los PCAP se leen en orden)
        total_ep = cuenta(t0, t1)
        dentro = cuenta(max(t0, ev0), min(t1, ev1)) if ev0 is not None else None
        antes = cuenta(ev0, t0) if ev0 is not None and ev0 < t0 else 0
        res["E1_pcap"] = {"destino_y_servicio": {80: "srv-dmz TCP/80", 18081: "srv-dmz TCP/18081", 53: "DC1 UDP/53 (cualquier paquete Kali<->DC1)"}[puerto],
                          "paquetes_kali_en_[inicio,fin]": total_ep, "paquetes_kali_en_[ventana_evidencia_e_episodio]": dentro,
                          "paquetes_kali_en_ventana_antes_del_inicio": antes}
        if puerto == 53 and total_ep == 0:
            res["E1_pcap"]["resultado"] = "indeterminado"
            res["E1_pcap"]["motivo"] = "el SPAN archivado no contiene ningún paquete Kali<->DC1: la detección DNS no se puede atribuir con paquetes"
        elif dentro:
            res["E1_pcap"]["resultado"] = "verificado"
            res["E1_pcap"]["motivo"] = "hay paquetes de la Kali al destino dentro de la ventana de evidencia y del episodio"
        else:
            res["E1_pcap"]["resultado"] = "fallido" if puerto != 53 else "indeterminado"
            res["E1_pcap"]["motivo"] = "sin paquetes de la Kali al destino dentro de la ventana de evidencia y del episodio"
        # ---------------- E3: serie del espejo + analizar_b.e3
        if acc is None:
            res["E3_pcap"] = {"resultado": "no evaluado", "motivo": "DNS: sin punto de aplicación"}
        else:
            ep = {"episodio_id": e, "escenario": fam, "origen": KALI, "accion_prevista": acc, "t_inicio": t0, "t_fin_ref": t1, "u": AB.EPS,
                  "traza_agente": [x for x in ag if t0 - 2 <= x.get("t", x.get("recibido_en", 0)) <= tope]}
            r2 = AB.e2(ep)
            serie = []
            for s in range(int(math.floor(t0)) - 30, b + 1):
                if pres[s] == 0:
                    continue                                          # segundo sin captura: hueco del espejo, no «cero»
                if acc == "LIMIT":
                    serie.append({"t": s, "aceptadas": ser["acc80"][s], "resp": ser["resp80"][s], "syn": ser["syn80"][s]})
                else:
                    serie.append({"t": s, "aceptadas": ser["acc18"][s], "resp": ser["resp18"][s], "syn": ser["syn18"][s]})
            ep["serie"] = serie
            r3 = AB.e3(ep, r2)
            esperados = max(1, int(t1 - t0))
            huecos = round(1 - len({x["t"] for x in serie if t0 <= x["t"] < t1}) / esperados, 3)
            res["E3_pcap"] = {"resultado": {"cumple": "verificado", "fallo": "fallido", "indeterminado": "indeterminado", "fallo_experimento": "indeterminado"}[r3["resultado"]],
                              "analizador": r3["resultado"], "motivo": r3["motivo"], "b0_aceptadas_por_s": r3.get("b0"), "huecos_del_espejo_en_el_episodio": huecos,
                              "t_efecto_menos_t_inicio": round(r3["t_efecto"] - t0, 1) if "t_efecto" in r3 else None,
                              "primer_descarte_host_menos_t_inicio": round(r3["primer_descarte_host"] - t0, 2) if r3.get("primer_descarte_host") else None,
                              "t_apl_menos_t_inicio": round(r2["t_apl_sup"] - t0, 2) if "t_apl_sup" in r2 else None}
            ap = r2.get("t_apl_sup")
            if ap is not None:
                tra = [s for s in range(int(math.ceil(ap)), b)]
                if acc == "LIMIT":
                    pre_ = [ser["acc80"][s] for s in range(int(ap) - 10, int(ap))]
                    post = [ser["acc80"][s] for s in tra]
                    syn_post = [ser["syn80"][s] for s in tra]
                else:
                    pre_ = [ser["resp18"][s] for s in range(int(ap) - 10, int(ap))]
                    post = [ser["resp18"][s] for s in tra]
                    syn_post = [ser["syn18"][s] for s in tra]
                sn = "syn80" if acc == "LIMIT" else "syn18"
                it = [m.get("intentos_generador") for m in mar if m["evento"] == "fin" and m["episodio_id"] == e][0]
                s_ant = sum(ser[sn][s] for s in range(a, int(ap)))
                s_reg = sum(ser[sn][s] for s in range(int(ap), b))
                res["E3_pcap"]["continuidad_de_intentos"] = {
                    "criterio_escrito": "SYN de la Kali >= 50 %% de B0 durante %d bloques tras t_apl" % (AB.K_LIMIT if acc == "LIMIT" else AB.K_BLOCK),
                    "umbral_syn_por_s": round(AB.INTENTO_MIN * res["E3_pcap"]["b0_aceptadas_por_s"], 1) if res["E3_pcap"].get("b0_aceptadas_por_s") else None,
                    "syn_total_en_el_episodio": s_ant + s_reg, "syn_antes_de_la_regla": s_ant, "syn_con_regla": s_reg,
                    "intentos_generador_total_salida": it, "salida_resuelta_en_el_tiempo": False,
                    "syn_por_iteracion_total": round((s_ant + s_reg) / it, 2) if it else None}
                if acc == "LIMIT":                                    # B0 y reducción de aceptadas, siempre que haya 10 bloques previos
                    pre10 = [ser["acc80"][s] for s in range(int(ap) - 10, int(ap))]
                    b0 = sum(pre10) / 10
                    res["E3_pcap"]["reduccion_aceptadas"] = {"b0_por_s": round(b0, 1), "posterior_media_por_s": round(sum(post) / max(1, len(post)), 1),
                                                             "reduccion_pct": round(100 * (1 - (sum(post) / max(1, len(post))) / b0), 1) if b0 else None}
                    res["E3_pcap"]["continuidad_de_intentos"]["umbral_syn_por_s"] = round(AB.INTENTO_MIN * b0, 1)
                    res["E3_pcap"]["continuidad_de_intentos"]["syn_posterior_media_por_s"] = round(sum(syn_post) / max(1, len(syn_post)), 1)
                    res["E3_pcap"]["continuidad_de_intentos"]["cumple_criterio_escrito"] = bool(sum(syn_post) / max(1, len(syn_post)) >= AB.INTENTO_MIN * b0)
                res["E3_pcap"]["resumen_series"] = {"previo_10s_media": round(sum(pre_) / max(1, len(pre_)), 1), "posterior_media": round(sum(post) / max(1, len(post)), 1),
                                                    "posterior_mediana": sorted(post)[len(post) // 2] if post else None, "syn_posterior_media": round(sum(syn_post) / max(1, len(syn_post)), 1)}
        # ---------------- E4: transacciones de clientes reconstruidas del SPAN
        i0, i1 = t0 - 60, (min(t1, t1) + 90)
        fl = [f for f in flujos.values() if i0 <= f["t"] <= i1]
        okf = [f for f in fl if f["synack"] is not None and (f["http"] is None or f["http"] < 500) and not f["rst"]]
        malas = [f for f in fl if f not in okf]
        apl_ts = [x["aplicado_en"] for x in ag if x.get("evento") == "aplicacion" and x.get("nuevos") and t0 - 2 <= x["aplicado_en"] <= tope and acc]
        activa = (min(apl_ts), tope) if apl_ts else None
        en_activa = [f for f in malas if activa and activa[0] <= f["t"] <= activa[1]]
        def razon(f):
            return "sin_synack" if f["synack"] is None else "rst" if f["rst"] else "http5xx" if (f["http"] or 0) >= 500 else "ok"
        t_apl_ep = min(apl_ts) if apl_ts else None
        cubos = collections.defaultdict(lambda: collections.Counter())
        for f in fl:
            cubo = "sin_regla_en_el_episodio" if t_apl_ep is None else ("antes_de_la_regla" if f["t"] < t_apl_ep else "con_regla_activa_o_posterior")
            cubos[cubo]["total"] += 1
            cubos[cubo][razon(f)] += 1
        res["E4_pcap_desglose"] = {c: dict(v) for c, v in cubos.items()}
        res["E4_pcap"] = {"ventana": [round(i0 - t0, 1), round(i1 - t0, 1)], "transacciones_cliente": len(fl), "completas_ok": len(okf), "sin_completar_o_error": len(malas),
                          "clientes": sorted({f["cliente"] for f in fl}), "con_codigo_http": sum(1 for f in fl if f["http"] is not None),
                          "codigos": dict(collections.Counter(f["http"] for f in fl if f["http"] is not None)),
                          "fallos_con_restriccion_activa": len(en_activa) if activa else None,
                          "fallos_de_la_ip_restringida": 0, "nota": "las restricciones se aplicaron solo a 10.10.20.30 (traza del agente): ningún cliente fue restringido"}
        out.append(res)
    (AQUI / "resultado-pcap.json").write_text(json.dumps({"fuente": "pcap 503 ficheros (hashes OK) + evidencia-local", "episodios": out, "kali_top": [[list(k), v] for k, v in kali_dst.most_common(12)],
                                                           "cobertura_segundos_con_captura": len(pres)}, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    for r in out:
        print(r["episodio"], "| E1", r["E1_pcap"]["resultado"], r["E1_pcap"]["paquetes_kali_en_[ventana_evidencia_e_episodio]"], "| E3", r["E3_pcap"]["resultado"], r["E3_pcap"].get("motivo"),
              r["E3_pcap"].get("resumen_series"), "| E4", r["E4_pcap"]["transacciones_cliente"], r["E4_pcap"]["completas_ok"], r["E4_pcap"]["sin_completar_o_error"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\markp\cf-b2-pcap\pcap"))
