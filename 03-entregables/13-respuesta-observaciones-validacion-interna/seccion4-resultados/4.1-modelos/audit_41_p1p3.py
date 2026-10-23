#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.1 re-audit P1 (validacion/umbral/alfa + 80 ventanas) y P3 (ventanas packet=0).
Corre EN EL SENSOR (lectura). Modelo congelado if_limpio_2026_10."""
import json, csv, pathlib
import numpy as np, joblib
CF=pathlib.Path("/home/m4rk/cyberflow"); ART=CF/"artifacts"
PART=ART/"aprendizaje"/"base"/"particionado-nota-L.csv"
ORO=ART/"aprendizaje"/"oro"/"oro.csv"
MANIF=ART/"preliminar"/"limpio-2026-10"/"manifest-if-limpio-2026-10.json"
MDL=ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib"
OUT=ART/"eval-4.1-2026-10-23"; OUT.mkdir(parents=True,exist_ok=True)
U_OP=-0.5693969936322356; KALI="10.10.20.30"
man=json.loads(MANIF.read_text())
def feats_(o):
    if isinstance(o,dict):
        if "features" in o and isinstance(o["features"],list): return o["features"]
        for v in o.values():
            r=feats_(v)
            if r: return r
mdl=joblib.load(MDL); feats=feats_(man)
def X(rows): return np.asarray([[float(r[c]) for c in feats] for r in rows],float)

# ===== P1 =====
val=[r for r in csv.DictReader(open(PART,newline="",encoding="utf-8")) if r.get("particion")=="validation"]
val_k=[r for r in val if r.get("entity_ip")==KALI]
val_nk=[r for r in val if r.get("entity_ip")!=KALI]
sv_all=np.asarray(mdl.score_samples(X(val)),float)
sv_nk=np.asarray(mdl.score_samples(X(val_nk)),float)
def q(a,alpha): return float(np.quantile(a,alpha))  # numpy lineal (igual que el pipeline)
p1={"n_val_total":len(val),"n_val_sin_kali":len(val_nk),"n_val_kali":len(val_k),
    "umbral_operativo":U_OP,
    "q05_val_total":q(sv_all,0.05),"q05_val_sin_kali":q(sv_nk,0.05),
    "reproduce_operativo_con":("val_total(65633)" if abs(q(sv_all,0.05)-U_OP)<abs(q(sv_nk,0.05)-U_OP) else "val_sin_kali"),
    "delta_total":q(sv_all,0.05)-U_OP,"delta_sin_kali":q(sv_nk,0.05)-U_OP,
    "definicion":"quantile numpy lineal, alerta = score_samples < umbral"}
# tabla alfa en AMBOS conjuntos
alfas=[0.01,0.025,0.05,0.10]
def oro_scores():
    oro=list(csv.DictReader(open(ORO,newline="",encoding="utf-8")))
    return oro, np.asarray(mdl.score_samples(X(oro)),float)
oro,so=oro_scores()
# ataques
ATA=ART/"aprendizaje"/"ataques"/"ataques-nota-M.csv"
ata=list(csv.DictReader(open(ATA,newline="",encoding="utf-8"))); sa=np.asarray(mdl.score_samples(X(ata)),float)
def alfa_tab(sv,etq):
    t=[]
    for a in alfas:
        thr=q(sv,a); fpr=float(np.mean(so<thr)); rec=float(np.mean(sa<thr))
        tp=int(np.sum(sa<thr)); fp=int(np.sum(so<thr)); prec=tp/(tp+fp) if tp+fp else 0.0
        f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
        t.append(dict(conjunto=etq,alfa=a,umbral=thr,fpr_obs=fpr,recall=rec,precision=prec,F1=f1))
    return t
p1["alfa_val_total"]=alfa_tab(sv_all,"val_total_65633")
p1["alfa_val_sin_kali"]=alfa_tab(sv_nk,"val_sin_kali_65553")
# enumerar las 80 kali de validacion
cols=["entity_ip","window_end_utc","particion","packet_count_10s","flow_attempt_count_30s",
      "http_request_count_60s","dns_query_count_60s","tls_observation_count_60s"]
with open(OUT/"p1-80-ventanas-kali-validacion.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(cols+["score_samples","model_alerta","clasif"])
    sk=np.asarray(mdl.score_samples(X(val_k)),float)
    for r,s in zip(val_k,sk):
        act = any(float(r.get(c,0) or 0)>0 for c in ("packet_count_10s","flow_attempt_count_30s","http_request_count_60s","dns_query_count_60s","tls_observation_count_60s"))
        clasif = "actividad_confirmada" if act else ("anomalo_sin_contadores" if s<U_OP else "incierto_benigno")
        w.writerow([r.get(c) for c in cols]+[round(float(s),6),int(s<U_OP),clasif])
p1["n_val_kali_con_actividad"]=int(sum(1 for r in val_k if any(float(r.get(c,0) or 0)>0 for c in ("packet_count_10s","flow_attempt_count_30s","http_request_count_60s","dns_query_count_60s","tls_observation_count_60s"))))

# ===== P3 ===== (oro 65421)
# campo packet_count_10s: presencia/tipo
has=0; empty=0; nonnum=0; zero=0
for r in oro:
    v=r.get("packet_count_10s", None)
    if v is None: continue
    has+=1
    if v=="" : empty+=1; continue
    try:
        fv=float(v)
        if fv==0: zero+=1
    except ValueError: nonnum+=1
def retro(r):
    return any(float(r.get(c,0) or 0)>0 for c in ("flow_attempt_count_30s","http_request_count_60s","dns_query_count_60s","tls_observation_count_60s","syn_count_10s"))
cats={"con_paquetes_10s":{"n":0,"fp":0},"cero_10s_con_retro":{"n":0,"fp":0},"cero_10s_sin_actividad":{"n":0,"fp":0}}
for r,s in zip(oro,so):
    pk=float(r.get("packet_count_10s",0) or 0); al=int(s<U_OP)
    if pk>0: k="con_paquetes_10s"
    elif retro(r): k="cero_10s_con_retro"
    else: k="cero_10s_sin_actividad"
    cats[k]["n"]+=1; cats[k]["fp"]+=al
for k,d in cats.items():
    d["tn"]=d["n"]-d["fp"]; d["fpr"]=d["fp"]/d["n"] if d["n"] else 0.0
# politica motor en vivo: ventanas sin paquetes -> PERMIT (no_live_packets), no puntua modelo
fp_total=int(np.sum(so<U_OP))
fp_en_cero=cats["cero_10s_con_retro"]["fp"]+cats["cero_10s_sin_actividad"]["fp"]
p3={"packet_count_10s_presente":has,"vacias_str":empty,"no_numericas":nonnum,"cero_real":zero,
    "categorias":cats,"fp_total_offline":fp_total,
    "fp_en_ventanas_cero_10s":fp_en_cero,
    "nota_politica":"El motor EN VIVO marca PERMIT las ventanas sin paquetes (heuristico no_live_packets) y NO puntua el modelo; "
      "el evaluador OFFLINE si las puntua. Por eso %d de los %d FP offline (%.1f%%) caen en ventanas con packet_count_10s=0 "
      "que en operacion serian PERMIT -> el FP operativo del modelo es menor que el FP offline." % (fp_en_cero,fp_total,100*fp_en_cero/fp_total if fp_total else 0)}

(OUT/"p1-reconciliacion.json").write_text(json.dumps(p1,indent=2,ensure_ascii=False),encoding="utf-8")
(OUT/"p3-ventanas-cero.json").write_text(json.dumps(p3,indent=2,ensure_ascii=False),encoding="utf-8")
print("== P1 =="); print(json.dumps({k:p1[k] for k in ("n_val_total","n_val_sin_kali","n_val_kali","umbral_operativo","q05_val_total","q05_val_sin_kali","reproduce_operativo_con","delta_total","delta_sin_kali","n_val_kali_con_actividad")},ensure_ascii=False,indent=2))
print("alfa val_total:",json.dumps(p1["alfa_val_total"],default=float))
print("== P3 =="); print(json.dumps(p3,ensure_ascii=False,default=float,indent=2))
