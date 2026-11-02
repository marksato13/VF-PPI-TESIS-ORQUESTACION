"""Efecto del horizonte (230 s frente a 900 s) en flow_duration_mean_30s, score y clase IF por alfa.
Uso: python sens_clases.py dir230 dir900 esquema.json umbrales.json desde hasta salida.json"""
import json,sys,collections
a,b,esq,umb,d,h,out=sys.argv[1:8]
E=json.load(open(esq,encoding="utf-8")); names=[x if isinstance(x,str) else x.get("name") for x in (E.get("feature_names") or E.get("features"))]
i=names.index("flow_duration_mean_30s")
U=json.load(open(umb,encoding="utf-8"))
def carga(p):
    o={}
    for l in open(p+"/caracteristicas.jsonl",encoding="utf-8"):
        r=json.loads(l)
        if d<=r["window_end_utc"][11:16]<=h: o[(r["entity_ip"],r["window_end_utc"])]=r
    return o
A,B=carga(a),carga(b)
res={"comparables":0,"vector_distinto":0,"solo_flow_duration":0,"otras_caracteristicas":collections.Counter(),
     "cambio_clase":{},"por_entidad":collections.Counter(),"dur230_dur900_ejemplos":[]}
cc={k:collections.Counter() for k in U}
for k in sorted(set(A)&set(B)):
    xa,xb=A[k]["x"],B[k]["x"]; res["comparables"]+=1
    if xa==xb: continue
    res["vector_distinto"]+=1
    dif=[j for j in range(len(xa)) if xa[j]!=xb[j]]
    if dif==[i]: res["solo_flow_duration"]+=1
    for j in dif:
        if j!=i: res["otras_caracteristicas"][names[j]]+=1
    res["por_entidad"][k[0]]+=1
    if len(res["dur230_dur900_ejemplos"])<8: res["dur230_dur900_ejemplos"].append([k[0],k[1][11:19],round(xa[i],1),round(xb[i],1),round(A[k]["score"],4),round(B[k]["score"],4)])
    for al,t in U.items():
        ca,cb=A[k]["score"]<t,B[k]["score"]<t
        if ca!=cb: cc[al][("ALERT->PERMIT" if ca else "PERMIT->ALERT")+" "+k[0]]+=1
res["cambio_clase"]={al:dict(c) for al,c in cc.items()}
res["otras_caracteristicas"]=dict(res["otras_caracteristicas"]); res["por_entidad"]=dict(res["por_entidad"])
json.dump(res,open(out,"w",encoding="utf-8"),indent=1); print(json.dumps(res,indent=1))
