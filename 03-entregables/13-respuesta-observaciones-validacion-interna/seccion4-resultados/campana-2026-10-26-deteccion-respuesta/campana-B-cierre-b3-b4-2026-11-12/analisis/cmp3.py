import json, pickle, bisect, datetime, collections
W = r"C:\Users\markp\cf-b4"; K = "10.10.20.30"
D = pickle.load(open(W + r"\span-kali-srv.pkl", "rb")); k2s = sorted(D["k2s"]); s2k = sorted(D["s2k"]); tk = [x[0] for x in k2s]; ts_ = [x[0] for x in s2k]
R = json.load(open(W + r"\resultado-b4.json", encoding="utf8"))
for r in R["episodios"]:
    f = r["familia"]
    if f.startswith("dns") or f.startswith("inund"): continue
    t0, t1 = r["t_inicio"], r["t_fin"]; e1 = r["E1"]; e2 = r["E2"]; e3 = r["E3"]
    ta = t0 + e2["t_apl_menos_t_inicio"]
    ev = e1.get("ventana_evidencia_vs_inicio_s"); a, b = max(t0, t0 + ev[0]), min(t1, t0 + ev[1])
    pk = bisect.bisect_right(tk, b) - bisect.bisect_left(tk, a)
    # bloques de 1 s tras t_apl: SYN y respuestas
    n = int(t1 - ta); bl_syn = 0; bl_resp = 0
    for s in range(int(ta) + 1, int(t1)):
        c = bisect.bisect_left(tk, s + 1) - bisect.bisect_left(tk, s); bl_syn += c >= 1
        rr = bisect.bisect_left(ts_, s + 1) - bisect.bisect_left(ts_, s); bl_resp += rr
    tot = max(1, int(t1) - int(ta) - 1)
    # primeros 3 bloques tras t_apl
    k3 = [(bisect.bisect_left(tk, s + 1) - bisect.bisect_left(tk, s), bisect.bisect_left(ts_, s + 1) - bisect.bisect_left(ts_, s)) for s in range(int(ta) + 1, int(ta) + 4)]
    print("%-22s E1 senal=%s (%s) paquetes Kali->srv en ventana evidenciayepisodio=%d | tras t_apl: bloques 1s con >=1 SYN %d/%d, respuestas srv->Kali tras t_apl=%d, primeros 3 bloques (syn,resp)=%s | E3=%s | primer_descarte=%s" % (r["episodio"], e1.get("resultado_senal"), e1.get("t_det_menos_t_inicio"), pk, bl_syn, tot, bl_resp, k3, e3["resultado"], e3.get("primer_descarte_host_menos_t_inicio")))
    if f.startswith("fuerza"): print("      E3 motivo:", e3["motivo"][:160], "| huecos", e3.get("huecos_del_espejo"))
for r in R["episodios"]:
    if r["familia"].startswith("escaneo"): print(r["episodio"], "E3 motivo:", r["E3"]["motivo"][:140], "| huecos", r["E3"].get("huecos_del_espejo"), "| E1 resultado:", r["E1"]["resultado"], "|", r["E1"].get("motivo")); 
