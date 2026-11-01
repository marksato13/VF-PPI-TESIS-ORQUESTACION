#!/usr/bin/env python3
"""Comprobaciones offline de presupuesto_e2e.py v3 y contrato_caracteristicas.py (solo lectura). Uso: python -I -B pruebas/test_presupuesto_e2e.py

Validación contra la realidad (bloque 3). El publicador SÍ corrió en sombra durante el 3B y dejó su feed final
(feed.json, generado 10:36:30,40 UTC) y su estado de escalada (estado.json). Se comparan EXACTAMENTE estos campos:
  feed   : conjunto de IPs y, por entrada, accion, hasta, alcance, motivo, detector, nivel, revisar_humano.
  estado : conjunto de IPs y, por IP, bloqueos y ultimo_evento_block (exactos) y ultimo_visto (tolerancia 0,2 s,
           porque el simulador fija 'ahora' en :x0,29 y el real lo toma del reloj, :x0,39-0,40).
NO se comparan: 'generado', 'umbrales' y 'version' del feed, ni la firma (feed.sig), ni ningún feed intermedio
(solo existe el final), ni nada del agente (inactivo en sombra: no hay estado nft real que comparar).
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI / "herramientas"))
import presupuesto_e2e as p  # noqa: E402

EV = AQUI.parent / "ejecucion-3b-2026-11-01" / "evidencia" / "sensor" / "copias"
FALLOS: list[str] = []


def ok(cond: bool, txt: str) -> None:
    print(("OK   " if cond else "FALLO") + "  " + txt)
    if not cond:
        FALLOS.append(txt)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cd = AQUI / "codigo-desplegado"
    verdicto, sev, nunca = p.extraer_publicador(cd / "publicar_feed.py")
    esc = p.cargar_escalada(cd / "escalada.py")
    # 1. Código desplegado
    ok(nunca == {"10.10.10.30", "10.10.60.11", "10.10.30.1", "10.10.40.1", "10.10.60.1", "10.10.20.1",
                 "10.10.10.20"}, "NUNCA_BLOQUEAR extraído del publicador desplegado (7 IPs, DNS incluido)")
    for f, h in (("publicar_feed.py", "f7bc4c7d"), ("escalada.py", "7d80ab4a"), ("agente_enforce.py", "2985c123")):
        ok(p.sha(cd / f).startswith(h), "%s = %s" % (f, h))

    dec = []
    with gzip.open(EV / "motor_decision.log.gz", "rt", encoding="utf-8") as fh:
        for l in fh:
            if '"event": "decision"' in l:
                dec.append(json.loads(l))
    dec.sort(key=lambda d: float(d["logged_at"]))

    # 2. Políticas
    act = p.construir_politica("actual", None, dec, verdicto, sev)
    ok(act is verdicto, "política actual con umbral desplegado = función _verdicto_de desplegada")
    act_u = p.construir_politica("actual", dec[0]["threshold"], dec, verdicto, sev)
    dif = sum(1 for d in dec if (act_u(d) or ("",))[0] != (verdicto(d) or ("",))[0])
    ok(dif == 0, "reimplementación con el umbral desplegado: misma acción en %d decisiones (difieren %d)"
       % (len(dec), dif))
    sen = p.construir_politica("if_senal", None, dec, verdicto, sev)
    ok(all((sen(d) or ("", "x"))[1].startswith("modelo:") is False for d in dec), "if_senal nunca propone por el IF")
    w = "2026-11-01T08:00:%02d+00:00"
    base = {"entity_ip": "1.2.3.4", "event": "decision", "decision": "ALERT", "detector_name": "if_x",
            "score": -1.0, "heuristico": None}
    s1 = [dict(base, window_end_utc=w % 0, logged_at=100.0), dict(base, window_end_utc=w % 10, logged_at=110.0)]
    ok(p.construir_politica("persist_2", None, s1, verdicto, sev)(s1[1]) is not None, "persist_2: dos ventanas seguidas -> LIMIT")
    ok(p.construir_politica("persist_3", None, s1, verdicto, sev)(s1[1]) is None, "persist_3: solo dos -> sin acción")
    s2 = [dict(base, window_end_utc=w % 0, logged_at=120.0), dict(base, window_end_utc=w % 10, logged_at=110.0)]
    ok(p.construir_politica("persist_2", None, s2, verdicto, sev)(s2[1]) is None,
       "persist_2: la ventana previa escrita DESPUÉS no cuenta (no se usa información futura)")

    # 3. Validación contra la realidad (campos enumerados en el docstring)
    feed = json.loads((EV / "feed.json").read_text(encoding="utf-8"))
    real_est = json.loads((EV / "estado.json").read_text(encoding="utf-8"))
    T_final = (feed["generado"] // 10) * 10
    cad = p.Cadena(esc, verdicto, sev, nunca)
    p.correr(cad, dec, float(dec[0]["logged_at"]), T_final)
    campos = ("ip", "accion", "hasta", "alcance", "motivo", "detector", "nivel", "revisar_humano")
    sim_f = sorted(({c: e[c] for c in campos} for e in cad.ultimo_feed), key=lambda e: e["ip"])
    real_f = sorted(({c: e[c] for c in campos} for e in feed["entradas"]), key=lambda e: e["ip"])
    ok(sim_f == real_f, "feed final: %d entradas idénticas en %s" % (len(real_f), ", ".join(campos)))
    ok(set(cad.estado) == set(real_est), "estado de escalada: mismo conjunto de %d IPs" % len(real_est))
    ok(all(cad.estado[ip].get("bloqueos") == real_est[ip].get("bloqueos")
           and cad.estado[ip].get("ultimo_evento_block") == real_est[ip].get("ultimo_evento_block")
           for ip in real_est if ip in cad.estado), "estado: bloqueos y ultimo_evento_block idénticos en todas las IPs")
    ok(all(abs(cad.estado[ip]["ultimo_visto"] - real_est[ip]["ultimo_visto"]) < 0.2 for ip in real_est if ip in cad.estado),
       "estado: ultimo_visto dentro de 0,2 s (fase :x0,29 simulada frente a reloj real)")
    ok(real_est[p.ORIGEN]["bloqueos"] == 3, "el origen 10.10.20.30 terminó en nivel 3 (real)")

    # 4. Modelo temporal: consumidor perdido y supuestos
    r = p.aplicar_desde_tick(100.0, "alto")
    ok(not r["relay_perdido"] and not r["agente_perdido"] and abs(r["t_apl_estimada"] - 107.564) < 1e-6,
       "alto con duraciones históricas: relé :x3, agente :x6 -> t_apl_estimada = tick + 7,564")
    viejo = dict(p.ESCENARIOS["alto"])
    try:
        p.ESCENARIOS["alto"]["pub_dur"] = 4.0             # termina en :x4,29, después del arranque del relé (:x3 + 1 s)
        r = p.aplicar_desde_tick(100.0, "alto")
        ok(r["relay_perdido"] and r["tick_relay"] == 113.0, "publicador lento: el relé copia el feed anterior; la entrada viaja en el siguiente (+10 s)")
        p.ESCENARIOS["alto"]["pub_dur"] = viejo["pub_dur"]
        p.ESCENARIOS["alto"]["relay_dur"] = 3.5           # el relé termina después del arranque del agente
        r = p.aplicar_desde_tick(100.0, "alto")
        ok(r["agente_perdido"] and r["tick_agente"] == 116.0, "relé lento: el agente aplica en el ciclo siguiente (+10 s)")
    finally:
        p.ESCENARIOS["alto"].update(viejo)
    ok(p.tick_para(100.10, "alto") == 100.0 and p.tick_para(100.50, "alto") == 110.0
       and p.tick_para(100.50, "favorable") == 100.0, "lectura: 'alto' al arrancar (:x0,29), 'favorable' al terminar")
    ok(p.clasificar(50, 51, 52, 53) == "deteccion_posterior", "t_det medido tras el fin -> deteccion_posterior")
    ok(p.clasificar(50, 40, 51, 53) == "despues_del_fin_bajo_supuestos", "aplicación favorable tras el fin")
    ok(p.clasificar(50, 40, 45, 49) == "antes_del_fin_bajo_supuestos" and p.clasificar(50, 40, 48, 52) == "indeterminado",
       "antes solo 'bajo supuestos'; el rango que cruza el fin -> indeterminado")
    ok({"activacion_nft_s", "efecto_s"} <= set(p.DESCONOCIDAS), "activación nft y efecto: declaradas desconocidas, no sumadas como 0")

    # 5. Resultados publicados
    res = json.loads((AQUI / "resultados" / "presupuesto-e2e.json").read_text(encoding="utf-8"))
    meta = res["episodios_meta"]
    ok(len(meta) == 25 and sum(m["admitido_v2"] for m in meta) == 15, "25 ejecutados (3B), 15 admitidos (revisión v2)")
    ok(all(m["t_apl_real"].startswith("no aplica") and m["t_efecto"].startswith("no aplica") for m in meta),
       "t_apl real y t_efecto = no aplica en sombra")
    ok(all(m["t_fin_eval_utc"] <= m["t_fin_observado_utc"] and m["t_fin_eval_utc"] <= m["t_fin_ref_utc"] for m in meta),
       "t_fin_eval = min(referencia, observado) en los 25")
    r2 = next(m for m in meta if m["episodio"] == "dns_inusual-r2")
    ok(r2["t_fin_eval_utc"] == r2["t_fin_observado_utc"], "dns_inusual-r2 terminó a 89,08 s: manda el fin observado")
    ok(all(v["resumen_por_escenario"]["escaneo_breve"]["cualquiera"]["V0_clases"]["antes_del_fin_bajo_supuestos"] == 0
           for v in res["politicas"].values()), "escaneo breve: 0/5 antes del fin en todas las políticas y α")
    ep = res["politicas"]["actual|desplegado"]["episodios"]
    ok(all(e["primera_cualquiera"] is None or e["primera_cualquiera"]["demoras_desconocidas_no_incluidas"] for e in ep),
       "cada estimación lista las demoras desconocidas no incluidas")
    br1 = next(e for e in ep if e["episodio"] == "escaneo_breve-r1")
    ok(br1["primera_cualquiera"]["motivo"].startswith("brute_force")
       and br1["primera_prevista"]["motivo"].startswith("port_scan")
       and br1["primera_prevista"]["t_det_menos_inicio_s"] > br1["primera_cualquiera"]["t_det_menos_inicio_s"],
       "escaneo_breve-r1: la primera señal es brute_force; la regla prevista (port_scan) llega después")
    sr3 = next(e for e in ep if e["episodio"] == "escaneo_sostenido-r3")
    ok(sr3["primera_prevista"]["V0"]["clase"] == "deteccion_posterior",
       "escaneo_sostenido-r3: port_scan llega tras el fin aunque otra señal (IF) llegó antes")

    # 6. D3: tres resultados separados (IF / heurístico previsto / respuesta if_senal)
    tres = {x["episodio"]: x for x in res["tres_resultados_d3"]}
    ok(len(tres) == 25 and all(set(x["1_anomalia_if"]) == {"desplegado", "IF_0.05", "IF_0.03", "IF_0.01"}
                               for x in tres.values()), "D3: los 25 episodios con la anomalía del IF a los 4 umbrales")
    ifs = res["politicas"]["if_senal|desplegado"]
    ok(all(not (e[k] and e[k]["motivo"].startswith("modelo:")) for e in ifs["episodios"]
           for k in ("primera_cualquiera", "primera_LIMIT", "primera_BLOCK")),
       "if_senal: ninguna respuesta procede de un ALERT aislado del IF (motivo 'modelo:')")
    ok(not any(k.startswith("LIMIT_modelo") for v in ifs["control"]["senales_por_entidad"].values() for k in v),
       "if_senal en el control: ningún veredicto 'modelo:' convertido en LIMIT")

    def t_if(x, u):
        a = x["1_anomalia_if"][u]
        return float("inf") if a is None else a["t_det_menos_inicio_s"]
    ok(all(t_if(x, "IF_0.05") <= t_if(x, "IF_0.03") <= t_if(x, "IF_0.01") for x in tres.values()),
       "un α menor (umbral más estricto) nunca adelanta la primera anomalía del IF")
    s3 = tres["escaneo_sostenido-r3"]
    ok(s3["1_anomalia_if"]["desplegado"]["disponible_antes_del_fin"] and
       not s3["2_heuristico_previsto"]["disponible_antes_del_fin"] and
       not s3["3_respuesta_if_senal"]["es_regla_prevista"],
       "sostenido-r3: la anomalía del IF cuenta antes del fin sin exigirle port_scan; heurístico y respuesta aparte")
    ok(all(tres["dns_inusual-r%d" % i]["1_anomalia_if"]["desplegado"] is None for i in (2, 3, 4)),
       "dns_inusual r2-r4: sin ALERT del IF; solo el heurístico dns_entropy")
    ok(all(x["punto_de_aplicacion"].startswith("DC1") == (x["escenario"] == "dns_inusual") for x in tres.values()),
       "punto de aplicación: DC1 solo en el escenario DNS (D1), srv-dmz en los demás")
    ep_s = [{"episodio": "e", "escenario": "x", "t_inicio": 0.0, "t_fin_eval": 100.0}]
    k_s = [{"window_end_utc": "w1", "decision": "ALERT", "score": -0.70, "detector_name": "if"},
           {"window_end_utc": "w0", "decision": "NORMAL", "score": -0.60, "detector_name": "if"}]
    at_s = {"e": {"w0": {"atribucion": "atribuible", "disponible_utc": "1970-01-01T00:00:10+00:00"},
                  "w1": {"atribucion": "atribuible", "disponible_utc": "1970-01-01T00:00:20+00:00"}}}
    ok(p.primera_alerta_if(ep_s, k_s, at_s, -0.55)["e"]["t_det_menos_inicio_s"] == 10.0 and
       p.primera_alerta_if(ep_s, k_s, at_s, -0.65)["e"]["t_det_menos_inicio_s"] == 20.0 and
       p.primera_alerta_if(ep_s, k_s, at_s, -0.80)["e"] is None and
       p.primera_alerta_if(ep_s, k_s, at_s, None)["e"]["t_det_menos_inicio_s"] == 20.0,
       "primera_alerta_if: score con cada umbral; con el desplegado, la decisión registrada")

    # 7. Contrato de características (28 del IF; 31 en el esquema ampliado)
    import contrato_caracteristicas as cc
    C = AQUI / "contrato"
    lee = lambda n: json.loads((C / n).read_text(encoding="utf-8"))  # noqa: E731
    src = (C / "extract_multilayer_v2.py").read_text(encoding="utf-8")
    rc = cc.comprobar(lee("multilayer-v2.json"), lee("multilayer-v3.json"), lee("manifest-if-limpio-2026-10.json"), src)
    ok(rc["todo_ok"] and rc["por_capa"] == {"L3": 9, "L4": 8, "L7": 11} and rc["por_fuente"] == {"eve": 11, "pcap": 17},
       "contrato: 28 = L3 9 + L4 8 + L7 11; 11 de EVE y 17 de PCAP; manifiesto, esquema y extractor en el mismo orden")
    ok([x["nombre"] for x in rc["ampliado_solo"]] == ["arp_request_rate_10s", "unique_src_mac_30s",
                                                       "mac_ip_binding_changes_60s"],
       "esquema ampliado: 31 = las 28 + 3 de L2 que el IF actual no usa")
    ok("dns_query_count_60s" in rc["metadatos_del_extractor_no_entradas"],
       "los contadores auxiliares (p. ej. dns_query_count_60s) son metadatos, no entradas del modelo")
    malo = lee("multilayer-v2.json")
    malo["features"][11]["layer"] = "L4"
    ok(not cc.comprobar(malo, lee("multilayer-v3.json"), lee("manifest-if-limpio-2026-10.json"), src)["todo_ok"],
       "contrato: una capa alterada se detecta (la comprobación no es tautológica)")
    print("\n%d fallos" % len(FALLOS))
    return 1 if FALLOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
