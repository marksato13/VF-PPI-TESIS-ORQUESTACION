import json, pickle, sys, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\Users\markp\cf-b4")
from e1_por_destino import e1_por_destino
W = r"C:\Users\markp\cf-b4"
P = {"B3": pickle.load(open(W + r"\span-origen-b3.pkl", "rb")), "B4": pickle.load(open(W + r"\span-origen-b4.pkl", "rb"))}
R = {"B3": json.load(open(r"C:\Users\markp\cf-b3\resultado-b3.json", encoding="utf8"))["episodios"], "B4": json.load(open(W + r"\resultado-b4.json", encoding="utf8"))["episodios"]}
PUERTO = {"inundacion_http": ("srv", 80), "fuerza_bruta_http": ("srv", 18081), "dns_inusual": ("dc1", 53), "escaneo_breve": ("srv", None), "escaneo_sostenido": ("srv", None)}
out = []
for tr in ("B3", "B4"):
    for r in R[tr]:
        f = r["familia"]; dest, puerto = PUERTO[f]; pk = P[tr][dest]
        todos = [x[0] for x in pk]
        e1 = r["E1"]; t0, t1 = r["t_inicio"], r["t_fin"]; ev = e1["ventana_evidencia_vs_inicio_s"]
        es, ee = t0 + ev[0], t0 + ev[1]
        n = e1_por_destino(todos, t0, t1, es, ee, e1.get("resultado_senal"))
        ctrl = None
        if puerto:
            ctrl = e1_por_destino([x[0] for x in pk if x[2] == puerto], t0, t1, es, ee, e1.get("resultado_senal"))["paquetes_en_ventana_y_episodio"]
        out.append({"tramo": tr, "episodio": r["episodio"], "familia": f, "destino": "10.10.30.10" if dest == "srv" else "10.10.10.20", "regla_senal": e1.get("señal_publicador"), "resultado_senal": e1.get("resultado_senal"), "t_det_menos_t_inicio": e1.get("t_det_menos_t_inicio"),
                    "ventana_evidencia_vs_inicio_s": ev, "toca_episodio_anterior": e1.get("ventana_toca_episodio_anterior"), "otras_reglas_en_ventana": e1.get("otras_reglas_en_ventana"),
                    "resultado_original": e1["resultado"], "paquetes_original": e1.get("paquetes_kali_en_ventana_evidencia_y_episodio"), "paquetes_control_mismo_puerto": ctrl,
                    "paquetes_por_destino": n["paquetes_en_ventana_y_episodio"], "paquetes_previos_al_inicio_en_ventana": n["paquetes_previos_al_inicio_en_ventana"], "resultado_por_destino": n["resultado"]})
        print("%s %-22s orig=%-13s (n=%s) ctrl=%s | destino=%-6d previos=%d -> %s" % (tr, r["episodio"], e1["resultado"], e1.get("paquetes_kali_en_ventana_evidencia_y_episodio"), ctrl, n["paquetes_en_ventana_y_episodio"], n["paquetes_previos_al_inicio_en_ventana"], n["resultado"]))
json.dump(out, open(W + r"\resultado-e1-por-destino-25.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
import collections; print(collections.Counter(x["resultado_por_destino"] for x in out), collections.Counter(x["resultado_original"] for x in out))