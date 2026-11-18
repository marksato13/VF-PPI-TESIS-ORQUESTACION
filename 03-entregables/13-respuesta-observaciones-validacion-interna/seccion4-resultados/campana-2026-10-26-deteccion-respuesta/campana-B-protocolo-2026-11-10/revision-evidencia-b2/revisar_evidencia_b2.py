#!/usr/bin/env python3
"""Revisión OFFLINE de la evidencia ya capturada de la repetición cancelada de la Campaña B (B2, 10-nov-2026). Lee SOLO las copias locales de
`evidencia-local\\` (traza del publicador, traza del agente de srv-dmz, marcas del generador, pasos de la puerta D5); no accede a Sensor1, al
bastión ni a srv-dmz. Reutiliza `analizar_b` (solo lectura) para E2 y E5; E1 se calcula aquí; E3 y E4 se declaran «no evaluado» porque faltan sus
fuentes (serie del espejo y transacciones de control). NO reclasifica nada: los seis episodios siguen C3.
Uso: revisar_evidencia_b2.py -> imprime y guarda resultado-revision.json"""
import datetime
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "herramientas"))
import analizar_b as AB  # noqa: E402

EV = AQUI / "evidencia-local"
K = "10.10.20.30"
REGLA = {"inundacion_http": "http_abuse", "fuerza_bruta_http": "brute_force", "dns_inusual": "dns_entropy"}
ACCION = {"inundacion_http": "LIMIT", "fuerza_bruta_http": "BLOCK", "dns_inusual": None}


def jl(n):
    return [json.loads(l) for l in open(EV / (n + ".jsonl"), encoding="utf-8", errors="replace") if l.strip()]


def epoch(s):
    return datetime.datetime.fromisoformat(s).timestamp()


def main():
    ag, pub, mar, pu = jl("agente"), jl("publicador"), jl("marcas"), jl("puertas")
    orden = [m for m in mar if m["evento"] == "campana_inicio"][0]["orden"]
    ini = {m["episodio_id"]: epoch(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
    fin = {m["episodio_id"]: epoch(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
    estado = {m["episodio_id"]: m["estado"] for m in mar if m["evento"] == "fin"}
    eps = [e for e in orden if e in ini]
    nuevos = [n for p in pub for n in p.get("nuevos", [])]
    out = []
    for k, e in enumerate(eps):
        fam = e.rsplit("-", 1)[0]
        t0, t1 = ini[e], fin[e]
        sig = ini[eps[k + 1]] if k + 1 < len(eps) else None
        tope = sig if sig is not None else t1 + 400
        acc = ACCION[fam]
        r = {"episodio": e, "familia": fam, "estado_generador": estado[e], "clase_salud": "C3 (se conserva)", "t_inicio": t0, "t_fin": t1}
        # ---- E1: señal de la regla prevista, atribuida al origen, con t_det + u < t_fin
        cand = sorted((n for n in nuevos if n["ip"] == K and n["regla"] == REGLA[fam] and t0 <= n["decidido_en"] <= t1), key=lambda n: n["decidido_en"])
        otras = sorted({n["regla"] for n in nuevos if n["ip"] == K and t0 <= n["decidido_en"] <= t1 and n["regla"] != REGLA[fam]})
        if cand:
            td = cand[0]["decidido_en"]
            r["E1"] = {"resultado": {"cumple": "verificado", "fallo": "fallido", "indeterminado": "indeterminado"}[AB.comparar(td, td, t1, AB.EPS)],
                       "regla": REGLA[fam], "t_det_menos_t_inicio": round(td - t0, 2), "margen_antes_del_fin_s": round(t1 - td, 2),
                       "destino": cand[0].get("destino"), "otras_reglas_en_ventana": otras,
                       "ventana_evidencia_vs_inicio_s": [round(cand[0]["evidencia"][0] - t0, 1), round(cand[0]["evidencia"][1] - t0, 1)],
                       "ventana_toca_episodio_anterior": bool(k > 0 and cand[0]["evidencia"][0] < fin[eps[k - 1]])}
        else:
            r["E1"] = {"resultado": "fallido", "motivo": "sin señal de la regla prevista en [inicio, fin]", "otras_reglas_en_ventana": otras}
        # ---- E2 (analizar_b.e2) con la traza del agente acotada al episodio
        trz = [x for x in ag if t0 - 2 <= x.get("t", x.get("recibido_en", 0)) <= tope]
        ep = {"episodio_id": e, "escenario": fam, "origen": K, "accion_prevista": acc, "t_inicio": t0, "t_fin_ref": t1, "traza_agente": trz}
        r2 = AB.e2(ep)
        if acc is None:
            r["E2"] = {"resultado": "no evaluado", "motivo": "DNS: DC1 no tiene punto de aplicación; el agente de srv-dmz ignora las entradas de DC1 por diseño (`ajenas`)"}
        else:
            r["E2"] = {"resultado": {"cumple": "verificado", "fallo": "fallido", "indeterminado": "indeterminado", "fallo_experimento": "indeterminado"}[r2["resultado"]],
                       "analizador": r2["resultado"], "confirmacion": r2.get("confirmacion"), "t_apl_menos_t_inicio": round(r2["t_apl_sup"] - t0, 2) if "t_apl_sup" in r2 else None,
                       "margen_antes_del_fin_s": round(r2["margen_s"], 2) if "margen_s" in r2 else None, "violaciones_fuera_de_alcance": r2["violaciones"],
                       "id_regla": r2.get("id"), "motivo": r2["motivo"]}
        # ---- E3 y E4: sin fuente
        desc = None
        if acc and "id" in r2:
            ds = [x["t"] for x in trz if x.get("evento") == "primer_descarte" and x.get("id") == r2["id"] and x.get("ip") == K]
            desc = round(min(ds) - t0, 2) if ds else None
        r["E3"] = {"resultado": "no evaluado", "motivo": "falta la serie SPAN por bloques de 1 s (espejo) y la prueba de que el generador siguió intentando",
                   "indicio_host_no_es_E3": ("primer descarte del host a +%s s de inicio (contador nft de la regla)" % desc) if desc is not None else None}
        r["E4"] = {"resultado": "no evaluado", "motivo": "la evidencia local no incluye transacciones de control de los clientes en [inicio-60 s, fin+90 s]"}
        # ---- E5: lecturas del set hechas por la puerta D5 entre el fin y el siguiente episodio (nft_antes / nft_despues)
        if acc is None:
            r["E5"] = {"resultado": "no evaluado", "motivo": "sin punto de aplicación: no hubo regla que retirar"}
        else:
            lect, retiro = [], None
            for p in pu:
                for s in p["pasos"]:
                    if t1 <= s.get("t", 0) <= tope and s.get("paso") in ("nft_antes", "nft_despues"):
                        lect.append({"t": s["t"], "bloqueados": [K] if "bloqueados" in s.get("donde", []) else [], "limitados": [K] if "limitados" in s.get("donde", []) else []})
                    if t1 <= s.get("t", 0) <= tope and s.get("paso") == "retirar" and s.get("retirado") and retiro is None:
                        retiro = s["t"]
            ep5 = dict(ep, t_siguiente=sig, lecturas_set=lect, d5_retirada_en=retiro)
            r5 = AB.e5(ep5, r2)
            res = {"cumple": "verificado", "fallo": "fallido", "indeterminado": "indeterminado"}.get(r5["resultado"], "no evaluado")
            r["E5"] = {"resultado": res, "analizador": r5["resultado"], "via": r5.get("via"), "lecturas": len(lect), "t_ultima_lectura_menos_t_fin": round(r5["t"] - t1, 2) if "t" in r5 else None,
                       "hay_siguiente_episodio": sig is not None, "motivo": r5["motivo"]}
        out.append(r)
    res = {"fuente": "evidencia-local/ (copias; hashes en SHA256.txt)", "episodios": out}
    (AQUI / "resultado-revision.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True))
    for r in out:
        print(r["episodio"], "| E1", r["E1"]["resultado"], r["E1"].get("t_det_menos_t_inicio"), "| E2", r["E2"]["resultado"], r["E2"].get("confirmacion"), r["E2"].get("t_apl_menos_t_inicio"),
              "| E3", r["E3"]["resultado"], "| E4", r["E4"]["resultado"], "| E5", r["E5"]["resultado"], r["E5"].get("via"), r["E5"].get("t_ultima_lectura_menos_t_fin"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
