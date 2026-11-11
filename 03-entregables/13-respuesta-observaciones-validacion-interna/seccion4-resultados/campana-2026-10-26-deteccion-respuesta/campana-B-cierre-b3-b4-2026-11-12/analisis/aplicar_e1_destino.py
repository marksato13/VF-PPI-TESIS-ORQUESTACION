import json, pickle, bisect, sys
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\Users\markp\cf-b4")
from e1_por_destino import e1_por_destino
W = r"C:\Users\markp\cf-b4"
D = pickle.load(open(W + r"\span-kali-srv.pkl", "rb")); k2s = sorted(D["k2s"])
todos = [x[0] for x in k2s]
p80 = [x[0] for x in k2s if x[2] in (80,) and x[1] == 6]; p18 = [x[0] for x in k2s if x[2] == 18081 and x[1] == 6]
R = json.load(open(W + r"\resultado-b4.json", encoding="utf8"))
out = []
for r in R["episodios"]:
    f = r["familia"]
    if f.startswith("dns"): continue
    e1 = r["E1"]; t0, t1 = r["t_inicio"], r["t_fin"]
    ev = e1.get("ventana_evidencia_vs_inicio_s")
    if not ev: continue
    es, ee = t0 + ev[0], t0 + ev[1]
    senal = e1.get("resultado_senal")
    n = e1_por_destino(todos, t0, t1, es, ee, senal)
    hist = e1.get("paquetes_kali_en_ventana_y_episodio")
    # control: mismo lector restringido al puerto del lector historico (debe reproducir su conteo)
    pt = p80 if f.startswith("inund") else p18 if f.startswith("fuerza") else None
    ctrl = e1_por_destino(pt, t0, t1, es, ee, senal)["paquetes_en_ventana_y_episodio"] if pt is not None else None
    fila = {"episodio": r["episodio"], "familia": f, "resultado_historico": e1["resultado"], "resultado_senal": senal, "t_det_menos_t_inicio": e1.get("t_det_menos_t_inicio"),
            "ventana_evidencia_vs_inicio_s": ev, "toca_episodio_anterior": e1.get("ventana_toca_episodio_anterior"), "otras_reglas_en_ventana": e1.get("otras_reglas_en_ventana"),
            "paquetes_historico_por_puerto": hist, "paquetes_control_por_puerto_nuevo_lector": ctrl, "paquetes_por_destino": n["paquetes_en_ventana_y_episodio"],
            "paquetes_previos_al_inicio_en_ventana": n["paquetes_previos_al_inicio_en_ventana"], "resultado_por_destino": n["resultado"]}
    out.append(fila)
    print("%-22s hist=%-9s %-12s | por puerto(nuevo lector)=%-6s hist_n=%-6s | POR DESTINO=%-6d previos=%-4d -> %-11s | toca_anterior=%s otras=%s" % (r["episodio"], e1["resultado"], senal, ctrl, hist, n["paquetes_en_ventana_y_episodio"], n["paquetes_previos_al_inicio_en_ventana"], n["resultado"], fila["toca_episodio_anterior"], fila["otras_reglas_en_ventana"]))
json.dump(out, open(W + r"\resultado-b4-e1-por-destino.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)