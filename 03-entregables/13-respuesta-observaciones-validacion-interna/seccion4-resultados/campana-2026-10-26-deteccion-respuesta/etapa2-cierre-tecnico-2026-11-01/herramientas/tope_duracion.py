"""Ventanas con flow_duration_mean_30s cerca del tope de history_seconds (230 s), por entidad.
Uso: python tope_duracion.py esquema.json caracteristicas.jsonl desde_HH:MM hasta_HH:MM salida.json"""
import json,sys,collections
esq=json.load(open(sys.argv[1],encoding="utf-8"))
names=[x if isinstance(x,str) else x.get("name") for x in (esq.get("feature_names") or esq.get("features"))]
i=names.index("flow_duration_mean_30s"); d,h=sys.argv[3],sys.argv[4]
n=0; umb={60:0,120:0,180:0,200:0,220:0,229:0}; mx=0; ent=collections.Counter(); tot=collections.Counter()
for l in open(sys.argv[2],encoding="utf-8"):
    r=json.loads(l); t=r["window_end_utc"][11:16]
    if not d<=t<=h: continue
    v=r["x"][i]; n+=1; mx=max(mx,v); tot[r["entity_ip"]]+=1
    for k in umb: umb[k]+=v>=k
    if v>=200: ent[r["entity_ip"]]+=1
o={"ventanas":n,"maximo_s":mx,"ventanas_con_duracion_media_ge":umb,"por_entidad_ge_200":{e:[c,tot[e]] for e,c in ent.most_common()}}
json.dump(o,open(sys.argv[5],"w",encoding="utf-8"),indent=1); print(json.dumps(o))
