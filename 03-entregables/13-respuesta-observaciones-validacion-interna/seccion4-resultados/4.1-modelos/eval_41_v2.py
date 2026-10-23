#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.1 v2 - Evaluacion endurecida y auditable. Corre EN EL SENSOR (solo lectura).
Sin fallback silencioso de score; verifica hashes; umbral del manifiesto a precision
completa; Tabla 6 (con especificidad + chequeos de suma, sin redondear en JSON);
Tabla 7 a umbral propio (sin Det@FPR5%); marca variantes identicas; sensibilidad de
alfa sobre validacion; scores completos de los 9; run-manifest. Respaldo durable en
artifacts/eval-4.1-2026-10-23/.
"""
import sys, json, csv, hashlib, pathlib, gzip
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
import sklearn, joblib, numpy
try: import scipy
except Exception: scipy=None

ART = pathlib.Path("/home/m4rk/cyberflow/artifacts")
ORO = ART/"aprendizaje"/"oro"/"oro.csv"
ATA = ART/"aprendizaje"/"ataques"/"ataques-nota-M.csv"
PART = ART/"aprendizaje"/"base"/"particionado-nota-L.csv"
MANIF_L = ART/"preliminar"/"limpio-2026-10"/"manifest-if-limpio-2026-10.json"
MANIF_R = ART/"preliminar"/"manifest-if-recalibrado.json"
MANIF_C = ART/"model"/"manifest.json"
OUT = ART/"eval-4.1-2026-10-23"; OUT.mkdir(parents=True, exist_ok=True)

def sha(p):
    try: return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    except OSError: return None
def jload(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def buscar(o,k):
    if isinstance(o,dict):
        if k in o and isinstance(o[k],list): return o[k]
        for v in o.values():
            r=buscar(v,k)
            if r: return r
    return None
def buscar_num(o,k):
    if isinstance(o,dict):
        for kk,v in o.items():
            if kk==k and isinstance(v,(int,float)): return float(v)
            r=buscar_num(v,k)
            if r is not None: return r
    return None

man_l=jload(MANIF_L); feats=buscar(man_l,"features")
U_L = buscar_num(man_l,"threshold")  # score_samples threshold del limpio
man_c=jload(MANIF_C)
THR={k:v["threshold_used"] for k,v in man_c.get("evaluation",{}).items() if isinstance(v,dict) and "threshold_used" in v}
MH=man_c.get("model_hashes",{})
man_r=jload(MANIF_R); U_R=-0.568892  # umbral del recalibrado contaminado (manifest comparte estructura multi-detector; se fija al conocido)

def leer(p,label):
    rows=list(csv.DictReader(open(p,newline="",encoding="utf-8")))
    bad=[]
    M=np.empty((len(rows),len(feats)),float)
    for i,r in enumerate(rows):
        for j,c in enumerate(feats):
            try:
                v=float(r[c]); M[i,j]=v
                if not np.isfinite(v): bad.append((i,c))
            except (TypeError,ValueError): bad.append((i,c)); M[i,j]=np.nan
    return rows,M,np.full(len(rows),label,int),bad

rn,Xn,yn,badn = leer(ORO,0)
ra,Xa,ya,bada = leer(ATA,1)
X=np.vstack([Xn,Xa]); y=np.concatenate([yn,ya])
ids=[(r.get("campaign_id"),r.get("window_end_utc")) for r in rn]+[(r.get("campaign_id"),r.get("window_end_utc")) for r in ra]
N_POS=int((y==1).sum()); N_NEG=int((y==0).sum())

# Auditoria del conjunto
def dups(rows):
    k=[(r.get("entity_ip"),r.get("window_end_utc")) for r in rows]; return len(k)-len(set(k))
auditoria={
 "oro":{"n":len(rn),"dup_por_entidad_ventana":dups(rn),
        "vacias_pkt0":int(sum(1 for r in rn if float(r.get("packet_count_10s",0) or 0)==0)),
        "features_invalidas":len(badn),"particion":"test (held-out, nota L)","sha256":sha(ORO)},
 "ataques":{"n":len(ra),"dup_por_entidad_ventana":dups(ra),
        "vacias_pkt0":int(sum(1 for r in ra if float(r.get("packet_count_10s",0) or 0)==0)),
        "features_invalidas":len(bada),
        "procedencia":"Kali 10.10.20.30, 30-sep 00:10-01:52 UTC (nota M); packet_count>0","sha256":sha(ATA)},
 "reutilizacion":"Este conjunto (84+65421) YA se uso el 14-oct para la comparacion de modelos "
                 "(COMPARACION-MODELOS.md): es una EVALUACION REUTILIZADA, no una confirmacion "
                 "independiente. No hay test ciego nuevo para el limpio.",
 "181_excluidas":"Distintas de estas 84: son la rafaga Kali del 27-sep excluida del ENTRENAMIENTO "
                 "(eligible_training=False); no entran a esta evaluacion.",
 "etiquetas_familia":"PROXY observable (nota M, errata): HTTP si http_request_count_60s>0; si no DNS "
                 "si dns_query_count_60s>0; resto escaneo. NO es ground-truth por ataque.",
}

def familia(r):
    if float(r.get("http_request_count_60s",0) or 0)>0: return "HTTP"
    if float(r.get("dns_query_count_60s",0) or 0)>0: return "DNS"
    return "escaneo"
fam_ata=[familia(r) for r in ra]

def expected_hash_for(path):
    s=sha(path)
    # buscar el sha en model_hashes (valores) o en manifests limpio/recal
    found = any(s==v for v in MH.values()) if isinstance(MH,dict) else False
    return s, found

MODELOS=[
 ("IF limpio (desplegado)","esta red", ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib", U_L),
 ("IF recalibrado (contaminado, antecedente)","esta red", ART/"preliminar"/"if_recalibrado_desplegable.joblib", U_R),
 ("IF scaled (lab)","laboratorio", ART/"model"/"candidates"/"if_scaled_weighted.joblib", THR.get("if_scaled_weighted")),
 ("IF primary (lab)","laboratorio", ART/"model"/"candidates"/"if_primary_weighted.joblib", THR.get("if_primary_weighted")),
 ("IF uniform (lab)","laboratorio", ART/"model"/"candidates"/"if_uniform.joblib", THR.get("if_uniform")),
 ("IF exact (lab)","laboratorio", ART/"model"/"candidates"/"if_exact_collapsed.joblib", THR.get("if_exact_collapsed")),
 ("OCSVM (lab)","laboratorio", ART/"model"/"candidates"/"ocsvm_scaled.joblib", THR.get("ocsvm_scaled")),
 ("LOF (lab)","laboratorio", ART/"model"/"candidates"/"lof_scaled.joblib", THR.get("lof_scaled")),
 ("Elliptic Envelope (lab)","laboratorio", ART/"model"/"candidates"/"elliptic_envelope_scaled.joblib", THR.get("elliptic_envelope_scaled")),
]

def metr_clasif(scores, umbral):
    yp=(scores<umbral).astype(int)
    tp=int(((y==1)&(yp==1)).sum()); fp=int(((y==0)&(yp==1)).sum())
    tn=int(((y==0)&(yp==0)).sum()); fn=int(((y==1)&(yp==0)).sum())
    prec=tp/(tp+fp) if tp+fp else 0.0; rec=tp/(tp+fn) if tp+fn else 0.0
    f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
    spec=tn/(tn+fp) if tn+fp else 0.0; fpr=fp/(fp+tn) if fp+tn else 0.0
    return dict(TP=tp,FP=fp,TN=tn,FN=fn,precision=prec,recall=rec,F1=f1,specificity=spec,FPR=fpr)

resultados=[]; scores_all={}; fallidos=[]; firmas={}
for nombre,origen,ruta,umbral in MODELOS:
    if not ruta.exists(): fallidos.append((nombre,"no existe el joblib")); continue
    s_hash,found=expected_hash_for(ruta)
    m=joblib.load(ruta)
    if not hasattr(m,"score_samples"):
        fallidos.append((nombre,"sin score_samples; tipo %s"%type(m).__name__)); continue
    ss=np.asarray(m.score_samples(X),float)
    scores_all[nombre]=ss
    # variante identica
    fp_key=hashlib.sha256(np.round(ss,8).tobytes()).hexdigest()[:16]
    firmas.setdefault(fp_key,[]).append(nombre)
    anom=-ss
    roc=float(roc_auc_score(y,anom)); ap=float(average_precision_score(y,anom))
    fila=dict(modelo=nombre,origen=origen,sha256=s_hash,sha_en_manifest=found,
              umbral=umbral,roc_auc=roc,average_precision=ap)
    if umbral is not None: fila.update(metr_clasif(ss,umbral))
    resultados.append(fila)
# marcar duplicados
dupes={k:v for k,v in firmas.items() if len(v)>1}

# ---- Tabla 6 (clean) ----
cl=[f for f in resultados if f["modelo"].startswith("IF limpio")][0]
assert cl["TP"]+cl["FN"]==N_POS and cl["TN"]+cl["FP"]==N_NEG and cl["TP"]+cl["TN"]+cl["FP"]+cl["FN"]==len(y)
# per familia (proxy) para el limpio
ss_l=scores_all["IF limpio (desplegado)"]; ss_la=ss_l[len(Xn):]
famdet={}
for f,sc in zip(fam_ata, ss_la):
    famdet.setdefault(f,{"n":0,"det":0}); famdet[f]["n"]+=1; famdet[f]["det"]+=int(sc<U_L)

# ---- Sensibilidad de alfa (F6) sobre VALIDACION ----
alfa_tab=None
try:
    val_rows=[];
    with open(PART,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("particion")=="validation" and r.get("entity_ip")!="10.10.20.30":
                val_rows.append(r)
    Xv=np.asarray([[float(r[c]) for c in feats] for r in val_rows],float)
    m_l=joblib.load(ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib")
    sv=np.asarray(m_l.score_samples(Xv),float)
    sa_test=ss_l  # scores del limpio sobre test (oro+ataques)
    alfa_tab=[]
    for a in (0.01,0.025,0.05,0.10):
        thr=float(np.quantile(sv,a))
        fpr=float(np.mean(ss_l[:len(Xn)]<thr))
        rec=float(np.mean(ss_la<thr))
        tp=int(np.sum(ss_la<thr)); fp=int(np.sum(ss_l[:len(Xn)]<thr))
        prec=tp/(tp+fp) if tp+fp else 0.0; f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
        alfa_tab.append(dict(alfa=a,umbral=thr,fpr_obs=fpr,recall=rec,precision=prec,F1=f1,n_val=len(val_rows)))
except Exception as e:
    alfa_tab=[{"error":"%s: %s"%(type(e).__name__,e)}]

# ---- escribir respaldo durable ----
# scores completos (ancho) + gzip
modelos_ok=[f["modelo"] for f in resultados]
with gzip.open(OUT/"scores-todos-candidatos.csv.gz","wt",encoding="utf-8",newline="") as f:
    w=csv.writer(f)
    w.writerow(["idx","campaign_id","window_end_utc","label","familia_proxy"]+["score::"+n for n in modelos_ok])
    fam_all=[""]*len(Xn)+fam_ata
    for i in range(len(y)):
        w.writerow([i,ids[i][0],ids[i][1],int(y[i]),fam_all[i]]+["%.6f"%scores_all[n][i] for n in modelos_ok])

versiones=dict(python=sys.version.split()[0],numpy=numpy.__version__,sklearn=sklearn.__version__,
               joblib=joblib.__version__,scipy=(scipy.__version__ if scipy else None))
metricas=dict(tabla6_clean=cl, n_pos=N_POS, n_neg=N_NEG, n_total=len(y),
              per_familia_proxy=famdet, tabla7=resultados, variantes_identicas=dupes,
              candidatos_fallidos=fallidos, umbral_limpio=U_L, umbral_recal=U_R,
              alfa_sensibilidad=alfa_tab, auditoria=auditoria, versiones=versiones)
(OUT/"metricas.json").write_text(json.dumps(metricas,indent=2,ensure_ascii=False,default=float),encoding="utf-8")

runman=dict(fecha="2026-10-23",versiones=versiones,
  datos={"oro":{"sha256":sha(ORO),"n":len(rn)},"ataques":{"sha256":sha(ATA),"n":len(ra)},
         "particionado":{"sha256":sha(PART)},"manifiesto_limpio":{"sha256":sha(MANIF_L)},
         "manifiesto_candidatos":{"sha256":sha(MANIF_C)}},
  hashes_modelos={f["modelo"]:{"sha256":f["sha256"],"en_model_hashes_manifest":f["sha_en_manifest"],"umbral":f["umbral"]} for f in resultados},
  model_hashes_manifest=MH, umbrales=THR, features_orden=feats,
  comando="python3 eval_41_v2.py (sensor, venv py3.14.4/sklearn1.9.0)")
(OUT/"run-manifest.json").write_text(json.dumps(runman,indent=2,ensure_ascii=False),encoding="utf-8")

print("U_L(manifiesto)=",U_L," U_R=",U_R)
print("Tabla6 clean:",{k:cl[k] for k in ("TP","FP","TN","FN","precision","recall","F1","specificity","FPR","roc_auc","average_precision")})
print("sumas ok: TP+FN=%d(=%d) TN+FP=%d(=%d) total=%d(=%d)"%(cl["TP"]+cl["FN"],N_POS,cl["TN"]+cl["FP"],N_NEG,len(y),len(y)))
print("familia(limpio):",famdet)
print("variantes_identicas:",dupes)
print("fallidos:",fallidos)
print("alfa:",json.dumps(alfa_tab,default=float))
print("scores gz:",sha(OUT/"scores-todos-candidatos.csv.gz")[:16], (OUT/"scores-todos-candidatos.csv.gz").stat().st_size)
print("OUT:",OUT)
