B=~/cf-e4/4c
python3 - <<'PY'
import json,os,time,subprocess
B=os.path.expanduser("~/cf-e4/4c"); a=[]; w=[]
def last(p):
    try: return json.loads(open(p).read().strip().splitlines()[-1])
    except Exception as e: return None
ps=subprocess.run("ps -eo args",shell=True,capture_output=True,text=True).stdout
vig="vigia_4c_b.py bucle" in ps; pue="lanzador_puerta_banco.py ejecutar" in ps
v=last(B+"/vigia/vigia.jsonl") or {}
ev=v.get("evento"); est=(v.get("permiso") or {}).get("estado")
causas=(v.get("permiso") or {}).get("causas")
marcas=[json.loads(l) for l in open(B+"/compuerta/marcas-vistas.jsonl") if l.strip()]
ini=[m for m in marcas if m.get("evento")=="inicio"]; fin=[m for m in marcas if m.get("evento")=="fin"]
cf=[m for m in marcas if m.get("evento") in("campana_fin","cancelacion")]
g=json.load(open(B+"/compuerta/gate.json"))
bloq=os.path.exists(B+"/compuerta/puerta-bloqueo.json")
if ev=="vigia_fin" : a.append("vigia_fin")
elif not vig and not cf: a.append("VIGIA CAIDO")
if not pue and not cf: a.append("PUERTA D5 CAIDA")
if est=="cancelar" or ev in("cancelacion",): a.append("vigia cancelar: %s"%causas)
if est=="pausa": w.append("pausa: %s"%causas)
if bloq: a.append("PUERTA BLOQUEADA")
if v.get("reversion_necesaria") or any("reversion_necesaria" in str(x) for x in [v]) : a.append("reversion_necesaria (X2)")
if cf: a.append("FIN/CANCEL generador: "+json.dumps(cf[-1])[:200])
ult=ini[-1].get("episodio_id") if ini else None
print(time.strftime("%FT%TZ",time.gmtime()),"inicios",len(ini),"fines",len(fin),"ultimo",ult,"estados_fin",[m.get("estado") for m in fin][-3:],"vigia",ev,est,"gate en_ep",g["en_episodio"],"pend",g["pendiente"],"WARN",w,"ALARMA",a)
PY
