#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4.3 por REPLAY (corre en el sensor). Suricata y CyberFlow (modelo limpio + heuristicos)
sobre el MISMO PCAP de la pasada limpia; atribucion por timestamp a cada episodio
(DNS/flood/escaneo, bien separados). Reloj del paquete para ambos. No reentrena."""
import subprocess, json, csv, os, pathlib, importlib.util
from datetime import datetime
CF="/home/m4rk/cyberflow"; PY=CF+"/.venv/bin/python3"
PCAP="/tmp/campana-pcap/pass.pcap"; OUT="/tmp/pass-replay"; pathlib.Path(OUT).mkdir(parents=True,exist_ok=True)
EVE=OUT+"/eve.json"; FEAT=OUT+"/features.csv"; ATAC="10.10.20.30"; U=-0.5693969936322356
EPIS=[("DNS",1792775890.746,1792775908.688),("flood",1792775988.694,1792776008.415),("escaneo",1792776088.422,1792776090.579)]
MARGEN=150.0

def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True); return r.returncode,(r.stderr or r.stdout or "")[-500:]
def ts(v):
    if v is None: return None
    try: return float(v)
    except (TypeError,ValueError): pass
    s=str(v).strip().replace("Z","+00:00")
    import re; s=re.sub(r"([+-]\d{2})(\d{2})$",r"\1:\2",s)
    try: return datetime.fromisoformat(s).timestamp()
    except ValueError: return None

# Suricata version + HOME_NET
sv=subprocess.run(["suricata","-V"],capture_output=True,text=True).stdout.strip()
home=subprocess.run(["bash","-lc","grep -m1 'HOME_NET' /etc/suricata/suricata.yaml"],capture_output=True,text=True).stdout.strip()
rules_sha=subprocess.run(["bash","-lc","sha256sum /var/lib/suricata/rules/suricata.rules 2>/dev/null | cut -c1-16"],capture_output=True,text=True).stdout.strip()

if not os.path.exists(EVE):
    rc,e=run(["suricata","-r",PCAP,"-l",OUT,"-k","none"]); print("suricata rc",rc,"|",e[-200:])
rc,e=run([PY,CF+"/scripts/features/extract_multilayer_v2.py","--pcap",PCAP,"--eve",EVE,
    "--campaign-id","pass","--output",FEAT,"--schema",CF+"/configs/features/multilayer-v2.json",
    "--entity-network","10.10.0.0/16","--capture-start","2026-10-23T17:17:20Z"])
print("extractor rc",rc,"|",e[-300:])

# CyberFlow: modelo limpio + heuristicos sobre las ventanas del extractor
import numpy as np, joblib
man=json.load(open(CF+"/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json"))
def findfeats(o):
    if isinstance(o,dict):
        if "features" in o and isinstance(o["features"],list): return o["features"]
        for v in o.values():
            r=findfeats(v)
            if r: return r
    return None
feats=findfeats(man)
mdl=joblib.load(CF+"/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib")
# heuristicos del sensor
H=None
for p in (CF+"/scripts/engine/heuristicos.py",):
    if os.path.exists(p):
        spec=importlib.util.spec_from_file_location("heuristicos",p); H=importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
frows=list(csv.DictReader(open(FEAT,newline="",encoding="utf-8"))) if os.path.exists(FEAT) else []
cf_ev=[]  # (epoch, model_alert, heur_rule)
for r in frows:
    we=ts(r.get("window_end_utc"))
    if we is None: continue
    try: x=np.asarray([[float(r[c]) for c in feats]],float); sc=float(mdl.score_samples(x)[0]); ma=sc<U
    except Exception: ma=False
    hv=H.evaluar(r) if H else None
    cf_ev.append((we,ma,(hv or {}).get("heuristico")))

# Suricata alertas del atacante
sur=[]
if os.path.exists(EVE):
    for ln in open(EVE,encoding="utf-8",errors="ignore"):
        if '"alert"' not in ln or ATAC not in ln: continue
        try: e=json.loads(ln)
        except ValueError: continue
        if e.get("event_type")!="alert": continue
        if e.get("src_ip")!=ATAC and e.get("dest_ip")!=ATAC: continue
        te=ts(e.get("timestamp"))
        if te is not None: sur.append((te,(e.get("alert") or {}).get("signature","?")))

filas=[]
for fam,t0,tf in EPIS:
    hi=tf+MARGEN
    cf_m=sorted(e[0] for e in cf_ev if e[1] and t0<=e[0]<=hi)
    cf_h=sorted(e[0] for e in cf_ev if e[2] and t0<=e[0]<=hi)
    cf_any=sorted(e[0] for e in cf_ev if (e[1] or e[2]) and t0<=e[0]<=hi)
    reglas=sorted({e[2] for e in cf_ev if e[2] and t0<=e[0]<=hi})
    su=sorted(s[0] for s in sur if t0<=s[0]<=hi)
    filas.append(dict(familia=fam,
        cf_detecta=bool(cf_any), cf_componente=("modelo+heuristico" if cf_m and cf_h else ("modelo" if cf_m else ("heuristico" if cf_h else "-"))),
        cf_reglas="|".join(reglas),
        t_cf_s=(round(cf_any[0]-t0,1) if cf_any else None),
        t_cf_modelo_s=(round(cf_m[0]-t0,1) if cf_m else None),
        sur_detecta=bool(su), t_sur_s=(round(su[0]-t0,1) if su else None)))

meta=dict(suricata=sv, home_net=home, rules_sha16=rules_sha, pcap=PCAP,
          n_ventanas_cf=len(cf_ev), n_alertas_suricata_atacante=len(sur))
print("META",json.dumps(meta,ensure_ascii=False))
print("TABLA9")
for f in filas: print(json.dumps(f,ensure_ascii=False))
pathlib.Path(OUT+"/tabla9.json").write_text(json.dumps({"meta":meta,"filas":filas},indent=2,ensure_ascii=False),encoding="utf-8")
