#!/usr/bin/env python3
"""Análisis OFFLINE de la corrida parcial (6 episodios) de la nueva Campaña B, 11-nov-2026. Lee solo copias locales en C:\\Users\\markp\\cf-b3.
E1: señal del publicador + paquetes Kali->destino en el SPAN. E2: analizar_b.e2 con la traza del agente. E3: e3_v2 (LIMIT: SPAN o salida con hora;
BLOCK: SPAN única, BLOCK_ADMITE_SALIDA=False). E4: transacciones por perfil (analizar_b.e4). E5: lecturas del set (muestreador + puerta D5).
Criterios: los de analizar_b.py sin cambios; E3 fijado en CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md."""
import bisect, collections, datetime, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path(r"C:\Users\markp\desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10")
sys.path.insert(0, str(BASE / "herramientas")); sys.path.insert(0, str(BASE / "instrumentacion")); sys.path.insert(0, str(BASE / "revision-evidencia-b2"))
import analizar_b as AB, analizar_b_instrumentado as V2, analizar_intentos as AI, lector_pcap as L  # noqa
W = Path(r"C:\Users\markp\cf-b3")
K, SRV, DC1 = "10.10.20.30", "10.10.30.10", "10.10.10.20"
SYN, ACK, RST = 2, 16, 4
FAM = {"inundacion_http": ("http_abuse", "LIMIT", 80), "fuerza_bruta_http": ("brute_force", "BLOCK", 18081), "dns_inusual": ("dns_entropy", None, 53),
       "escaneo_breve": ("port_scan", "BLOCK", None), "escaneo_sostenido": ("port_scan", "BLOCK", None)}
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8", errors="replace") if l.strip()]
def epo(s): return datetime.datetime.fromisoformat(s).timestamp()
def main():
    mar = jl(W / "bastion/corrida/marcas.jsonl"); ag = jl(W / "cf-b3-agente.jsonl"); pub = jl(W / "evid/traza.jsonl")
    pu = jl(W / "bastion/compuerta/puertas-D5.jsonl"); lectset = jl(W / "cf-b3-set-lecturas.jsonl")
    orden = [m for m in mar if m["evento"] == "campana_inicio"][0]["orden"]
    ini = {m["episodio_id"]: epo(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
    fin = {m["episodio_id"]: epo(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
    est = {m["episodio_id"]: m for m in mar if m["evento"] == "fin"}
    eps = [e for e in orden if e in ini and e in fin]
    nuevos = [n for p in pub for n in p.get("nuevos", [])]
    lo, hi = min(ini.values()) - 130, max(fin.values()) + 130
    pres = collections.Counter(); ser = collections.defaultdict(collections.Counter); tsl = collections.defaultdict(list)
    for f in sorted((W / "pcap").glob("*.pcap")):
        for ts, s, d, pr, sp, dp, fl, pl, pre in L.paquetes(f):
            if ts < lo or ts > hi: continue
            sec = int(ts); pres[sec] += 1
            if pr == 6 and s == K and d == SRV:
                for puerto, tag in ((80, "80"), (18081, "18")):
                    if dp == puerto:
                        tsl["k" + tag].append(ts); ser["syn" + tag][sec] += bool(fl & SYN and not fl & ACK)
            elif pr == 6 and s == SRV and d == K:
                for puerto, tag in ((80, "80"), (18081, "18")):
                    if sp == puerto:
                        ser["resp" + tag][sec] += 1; ser["acc" + tag][sec] += bool(fl & SYN and fl & ACK)
            elif (s == K and d == DC1) or (s == DC1 and d == K):
                tsl["dc1"].append(ts)
            if pr == 6 and s == K and d == SRV and dp not in (80, 18081):
                tsl["kotros"].append(ts); ser["synotros"][sec] += bool(fl & SYN and not fl & ACK)
    # transacciones de clientes (E4)
    filas = []
    for t in sorted((W / "cf-b3-clientes").glob("transacciones-*.tsv")): filas += V2.leer_transacciones(t)
    aplic = [x for x in ag if x.get("evento") == "aplicacion"]
    restr = [{"ip": n["ip"], "desde": a["aplicado_en"], "hasta": n.get("hasta", a["aplicado_en"] + 300)} for a in aplic for n in a.get("nuevos", [])]
    ctrl = V2.control_desde_transacciones(filas, restr)
    out = []
    for k, e in enumerate(eps):
        fam = e.rsplit("-", 1)[0]; regla, acc, puerto = FAM[fam]; t0, t1 = ini[e], fin[e]
        sig = ini[eps[k + 1]] if k + 1 < len(eps) else None
        tope = sig if sig else t1 + 400
        r = {"episodio": e, "familia": fam, "estado_generador": est[e]["estado"], "t_inicio": t0, "t_fin": t1, "duracion_s": round(t1 - t0, 1), "intentos_generador": est[e].get("intentos_generador")}
        # E1
        cand = sorted((n for n in nuevos if n["ip"] == K and n["regla"] == regla and t0 <= n["decidido_en"] <= t1), key=lambda n: n["decidido_en"])
        otras = sorted({n["regla"] for n in nuevos if n["ip"] == K and t0 <= n["decidido_en"] <= t1 and n["regla"] != regla})
        nm = {80: "k80", 18081: "k18", 53: "dc1"}.get(puerto)
        cu = (lambda a, b: bisect.bisect_right(tsl[nm], b) - bisect.bisect_left(tsl[nm], a)) if nm else None
        if cand:
            td = cand[0]["decidido_en"]; ev = cand[0]["evidencia"]
            e1 = {"señal_publicador": regla, "t_det_menos_t_inicio": round(td - t0, 2), "margen_antes_del_fin_s": round(t1 - td, 2), "otras_reglas_en_ventana": otras,
                  "ventana_evidencia_vs_inicio_s": [round(ev[0] - t0, 1), round(ev[1] - t0, 1)], "ventana_toca_episodio_anterior": bool(k > 0 and ev[0] < fin[eps[k - 1]]),
                  "resultado_senal": {"cumple": "verificado", "fallo": "fallido", "indeterminado": "indeterminado"}[AB.comparar(td, td, t1, AB.EPS)]}
            if cu:
                dentro = cu(max(t0, ev[0]), min(t1, ev[1])); e1["paquetes_kali_en_ventana_evidencia_y_episodio"] = dentro
                e1["resultado"] = ("verificado" if dentro and e1["resultado_senal"] == "verificado" else "indeterminado" if puerto == 53 else e1["resultado_senal"] if not dentro else e1["resultado_senal"])
                if puerto == 53 and cu(t0, t1) == 0: e1["resultado"] = "indeterminado"; e1["motivo"] = "el SPAN no contiene paquetes Kali<->DC1: no se puede atribuir con paquetes"
            else:
                e1["resultado"] = "indeterminado"; e1["motivo"] = "sin lector de paquetes para este servicio"
        else:
            e1 = {"resultado": "fallido", "motivo": "sin señal de la regla prevista en [inicio, fin]", "otras_reglas_en_ventana": otras}
        r["E1"] = e1
        # E2/E3/E5
        trz = [x for x in ag if t0 - 2 <= x.get("t", x.get("recibido_en", 0)) <= tope]
        ep = {"episodio_id": e, "escenario": fam, "origen": K, "accion_prevista": acc, "t_inicio": t0, "t_fin_ref": t1, "traza_agente": trz}
        r2 = AB.e2(ep)
        if acc is None:
            r["E2"] = {"resultado": "no_aplica", "motivo": "DNS: DC1 no tiene punto de aplicación; el agente de srv-dmz ignora las entradas de DC1 (`ajenas`)"}
            r["E3"] = {"resultado": "no_aplica", "motivo": "sin punto de aplicación"}; r["E5"] = {"resultado": "no_aplica", "motivo": "no hubo regla que retirar"}
        else:
            r["E2"] = {"resultado": r2["resultado"], "confirmacion": r2.get("confirmacion"), "t_apl_menos_t_inicio": round(r2["t_apl_sup"] - t0, 2) if "t_apl_sup" in r2 else None,
                       "margen_antes_del_fin_s": round(r2["margen_s"], 2) if "margen_s" in r2 else None, "violaciones": r2["violaciones"], "id_regla": r2.get("id"), "motivo": r2["motivo"]}
            tag = "80" if acc == "LIMIT" else "18"
            serie = [{"t": s, "aceptadas": ser["acc" + tag][s], "resp": ser["resp" + tag][s], "syn": ser["syn" + tag][s]} for s in range(int(math.floor(t0)) - 30, int(math.ceil(t1)) + 1) if pres[s]]
            ep["serie"] = serie
            if fam == "inundacion_http":
                ts = AI.series(AI.leer(W / ("cf-b3-kali/intentos/intentos-%s.tsv" % e)))
                ep["intentos_salida"] = [{"t": t, "intentos": v["intentos"]} for t, v in ts.items()]
            r3 = V2.e3_v2(ep, r2)
            esperados = max(1, int(t1 - t0)); huecos = round(1 - len({x["t"] for x in serie if t0 <= x["t"] < t1}) / esperados, 3)
            r["E3"] = {"resultado": r3["resultado"], "motivo": r3["motivo"], "via_continuidad": r3.get("via_continuidad"), "continuidad": r3.get("continuidad"), "b0": r3.get("b0"),
                       "t_efecto_menos_t_inicio": round(r3["t_efecto"] - t0, 1) if "t_efecto" in r3 else None, "huecos_del_espejo": huecos,
                       "primer_descarte_host_menos_t_inicio": round(r3["primer_descarte_host"] - t0, 2) if r3.get("primer_descarte_host") else None}
            if "t_apl_sup" in r2:
                a = r2["t_apl_sup"]; r["E3"]["serie"] = {"previo10_aceptadas_media": round(sum(ser["acc" + tag][s] for s in range(int(a) - 10, int(a))) / 10, 1),
                      "posterior_aceptadas_media": round(sum(ser["acc" + tag][s] for s in range(int(math.ceil(a)), int(t1))) / max(1, int(t1) - int(math.ceil(a))), 1),
                      "syn_posterior_media": round(sum(ser["syn" + tag][s] for s in range(int(math.ceil(a)), int(t1))) / max(1, int(t1) - int(math.ceil(a))), 1),
                      "resp_posterior_media": round(sum(ser["resp" + tag][s] for s in range(int(math.ceil(a)), int(t1))) / max(1, int(t1) - int(math.ceil(a))), 1)}
            lect, retiro = [], None
            for x in lectset:
                if t1 <= x["t"] <= tope and x.get("ok"):
                    lect.append({"t": x["t"], "bloqueados": list(x["sets"].get("bloqueados", {})), "limitados": list(x["sets"].get("limitados", {}))})
            for p in pu:
                for s in p.get("pasos", []):
                    if t1 <= s.get("t", 0) <= tope and s.get("paso") == "retirar" and s.get("retirado") and retiro is None: retiro = s["t"]
            r5 = AB.e5(dict(ep, t_siguiente=sig, lecturas_set=lect, d5_retirada_en=retiro), r2)
            r["E5"] = {"resultado": r5["resultado"], "via": r5.get("via"), "motivo": r5["motivo"], "lecturas_del_set": len(lect), "retirada_d5_menos_fin_s": round(retiro - t1, 1) if retiro else None}
        # E4
        r["E4"] = dict(AB.e4(dict(ep, control=ctrl)), perfiles=sorted({f["perfil"] for f in filas if t0 - 60 <= float(f["t_fin"]) <= t1 + 90}))
        out.append(r)
    (W / "resultado-b3.json").write_text(json.dumps({"episodios": out, "cobertura_segundos_con_captura": len(pres), "transacciones_total": len(filas)}, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    for r in out:
        print(r["episodio"], "| E1", r["E1"].get("resultado"), r["E1"].get("t_det_menos_t_inicio"), "| E2", r["E2"]["resultado"], r["E2"].get("confirmacion"), "| E3", r["E3"]["resultado"], r["E3"].get("via_continuidad"), r["E3"]["motivo"][:70],
              "| E4", r["E4"]["resultado"], r["E4"].get("n"), "| E5", r["E5"]["resultado"], r["E5"].get("via"))
if __name__ == "__main__": main()
