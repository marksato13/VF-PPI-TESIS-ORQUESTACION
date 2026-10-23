#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""McNemar (pareado) + Holm del IF limpio vs cada candidato, con las predicciones
ACTUALES (umbral propio) sobre las mismas 65 505 ventanas. Local, desde el gz.
Unidad = ventana; se DECLARA la dependencia temporal entre ventanas (el test asume
pares discordantes independientes -> aqui es aproximado, descriptivo)."""
import json, csv, gzip, math, pathlib
D = pathlib.Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\_campana\resultados-2026-10-23\eval41\v2")
M = json.loads((D/"metricas.json").read_text(encoding="utf-8"))
thr = {r["modelo"]: r["umbral"] for r in M["tabla7"]}

with gzip.open(D/"scores-todos-candidatos.csv.gz","rt",encoding="utf-8") as f:
    rd=csv.reader(f); H=next(rd); rows=list(rd)
li=H.index("label"); y=[int(r[li]) for r in rows]
cols={h.split("::",1)[1]:i for i,h in enumerate(H) if h.startswith("score::")}
def pred(nombre):
    i=cols[nombre]; u=thr[nombre]; return [1 if float(r[i])<u else 0 for r in rows]
def correct(nombre):
    p=pred(nombre); return [int(pi==yi) for pi,yi in zip(p,y)]

def phi(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def mcnemar(cA,cB):
    b=sum(1 for a,x in zip(cA,cB) if a==1 and x==0)
    c=sum(1 for a,x in zip(cA,cB) if a==0 and x==1)
    n=b+c
    if n==0: return b,c,1.0,"sin discordantes"
    if n<=1000:
        k=min(b,c); p=2*sum(math.comb(n,i) for i in range(k+1))*(0.5**n); p=min(1.0,p); met="binomial exacta"
    else:
        z=(abs(b-c)-1)/math.sqrt(n); p=2*(1-phi(z)); p=min(1.0,max(0.0,p)); met="normal (continuidad)"
    return b,c,p,met

CL="IF limpio (desplegado)"; cCL=correct(CL)
otros=["IF recalibrado (contaminado, antecedente)","IF scaled (lab)","IF primary (lab)","IF uniform (lab)","OCSVM (lab)","LOF (lab)","Elliptic Envelope (lab)"]
res=[]
for o in otros:
    cO=correct(o); b,c,p,met=mcnemar(cCL,cO)
    # b = limpio acierta y el otro falla ; c = limpio falla y el otro acierta
    res.append({"vs":o,"b_limpio_mejor":b,"c_otro_mejor":c,"p":p,"metodo":met})
# Holm
res_sorted=sorted(res,key=lambda r:r["p"]); m=len(res_sorted)
for rank,r in enumerate(res_sorted):
    r["p_holm"]=min(1.0,(m-rank)*r["p"])
# monotonia Holm
acc=0
for r in res_sorted:
    acc=max(acc,r["p_holm"]); r["p_holm"]=acc

L=["# 4.1 - Significancia McNemar + Holm (predicciones ACTUALES, umbral propio)","",
   "IF limpio vs cada candidato sobre 65 505 ventanas. `b` = ventanas donde el limpio acierta y el otro",
   "falla; `c` = al reves. **Salvedad:** la unidad es la ventana y las ventanas son **dependientes**",
   "(series temporales); McNemar asume pares discordantes independientes, asi que esto es **descriptivo**,",
   "no una prueba inferencial estricta. Dominado por diferencias en falsos positivos sobre normales.","",
   "| vs | b (limpio mejor) | c (otro mejor) | p (McNemar) | p_Holm | método |",
   "|---|---:|---:|---:|---:|---|"]
for r in res_sorted:
    L.append("| %s | %d | %d | %.3g | %.3g | %s |"%(r["vs"],r["b_limpio_mejor"],r["c_otro_mejor"],r["p"],r["p_holm"],r["metodo"]))
L+=["","**Lectura:** frente a los candidatos de laboratorio y OCSVM/LOF/EE, el limpio difiere con p_Holm muy",
    "pequeno (comete muchisimos menos FP). Frente al **contaminado** la diferencia es minima (ver b vs c",
    "cercanos) -> coherente con que son **equivalentes**. No se afirma 'estadisticamente superior' como",
    "conclusion fuerte por la dependencia entre ventanas; se reporta como diferencia **descriptiva** pareada."]
(D/"SIGNIFICANCIA-McNemar.md").write_text("\n".join(L),encoding="utf-8")
(D/"significancia-mcnemar.json").write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding="utf-8")
print("\n".join(L))
