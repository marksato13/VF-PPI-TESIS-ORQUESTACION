#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 - Re-exporta los scores de los 9 candidatos a PRECISION COMPLETA (%.17g),
backup sin perdida. Corre en el sensor."""
import json, csv, gzip, hashlib, pathlib
import numpy as np, joblib
ART=pathlib.Path("/home/m4rk/cyberflow/artifacts")
ORO=ART/"aprendizaje"/"oro"/"oro.csv"; ATA=ART/"aprendizaje"/"ataques"/"ataques-nota-M.csv"
MANIF=ART/"preliminar"/"limpio-2026-10"/"manifest-if-limpio-2026-10.json"
OUT=ART/"eval-4.1-2026-10-23"
man=json.loads(MANIF.read_text())
def ff(o):
    if isinstance(o,dict):
        if "features" in o and isinstance(o["features"],list): return o["features"]
        for v in o.values():
            r=ff(v)
            if r: return r
feats=ff(man)
def leer(p,lab):
    rows=list(csv.DictReader(open(p,newline="",encoding="utf-8")))
    return rows, np.asarray([[float(r[c]) for c in feats] for r in rows],float), lab
rn,Xn,_=leer(ORO,0); ra,Xa,_=leer(ATA,1)
import numpy as np
X=np.vstack([Xn,Xa]); y=[0]*len(rn)+[1]*len(ra)
rows=rn+ra; famc=lambda r:("HTTP" if float(r.get("http_request_count_60s",0) or 0)>0 else ("DNS" if float(r.get("dns_query_count_60s",0) or 0)>0 else "escaneo"))
fam=[""]*len(rn)+[famc(r) for r in ra]
MOD=[("IF limpio (desplegado)",ART/"preliminar"/"limpio-2026-10"/"if_limpio_2026_10_desplegable.joblib"),
 ("IF recalibrado (contaminado, antecedente)",ART/"preliminar"/"if_recalibrado_desplegable.joblib"),
 ("IF scaled (lab)",ART/"model"/"candidates"/"if_scaled_weighted.joblib"),
 ("IF primary (lab)",ART/"model"/"candidates"/"if_primary_weighted.joblib"),
 ("IF uniform (lab)",ART/"model"/"candidates"/"if_uniform.joblib"),
 ("IF exact (lab)",ART/"model"/"candidates"/"if_exact_collapsed.joblib"),
 ("OCSVM (lab)",ART/"model"/"candidates"/"ocsvm_scaled.joblib"),
 ("LOF (lab)",ART/"model"/"candidates"/"lof_scaled.joblib"),
 ("Elliptic Envelope (lab)",ART/"model"/"candidates"/"elliptic_envelope_scaled.joblib")]
sc={}
for n,p in MOD:
    m=joblib.load(p); sc[n]=np.asarray(m.score_samples(X),float)
names=[n for n,_ in MOD]
outp=OUT/"scores-todos-candidatos-full.csv.gz"
with gzip.open(outp,"wt",encoding="utf-8",newline="") as f:
    w=csv.writer(f); w.writerow(["idx","campaign_id","entity_ip","window_end_utc","label","familia_proxy"]+["score::"+n for n in names])
    for i in range(len(rows)):
        r=rows[i]
        w.writerow([i,r.get("campaign_id"),r.get("entity_ip"),r.get("window_end_utc"),y[i],fam[i]]+["%.17g"%sc[n][i] for n in names])
sha=hashlib.sha256(outp.read_bytes()).hexdigest()
print("escrito",outp,"sha256",sha,"bytes",outp.stat().st_size)
