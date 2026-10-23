"""Lectura remota: no escribe en las VMs, no entrena ni altera servicios.

--inventory lista posibles scores conservados. Sin esa opción recupera scores
de validación con inferencia del IF limpio congelado y metadatos del test.
Los scores de test se toman exclusivamente del respaldo canónico local.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent

INVENTORY = r'''
from pathlib import Path
import json
a=Path('/home/m4rk/cyberflow/artifacts')
files=[]
for root in (a/'eval-4.1-2026-10-23',a/'preliminar/limpio-2026-10'):
    if root.exists():
        files.extend({'path':str(p),'bytes':p.stat().st_size} for p in root.rglob('*') if p.is_file())
print(json.dumps(files))
'''

EXPORT = r'''
from pathlib import Path
import csv, gzip, hashlib, json, sys
import numpy as np, joblib
base=Path('/home/m4rk/cyberflow/artifacts')
model=base/'preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib'
manifest=base/'preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json'
part=base/'aprendizaje/base/particionado-nota-L.csv'
normal=base/'aprendizaje/oro/oro.csv'
attack=base/'aprendizaje/ataques/ataques-nota-M.csv'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
assert sha(model)=='df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60'
def features(o):
    if isinstance(o,dict):
        if isinstance(o.get('features'),list):return o['features']
        for v in o.values():
            ans=features(v)
            if ans:return ans
feats=features(json.loads(manifest.read_text()))
val=[r for r in csv.DictReader(part.open(newline='',encoding='utf-8')) if r.get('particion')=='validation']
assert len(val)==65633
assert sum(r['entity_ip']=='10.10.20.30' for r in val)==80
pipeline=joblib.load(model)
scores=pipeline.score_samples(np.asarray([[float(r[f]) for f in feats] for r in val],float))
assert float(np.quantile(scores,.05,method='linear'))==-0.5693969936322356
keys=['campaign_id','entity_ip','window_end_utc','packet_count_10s']
validation=[dict({k:r.get(k,'') for k in keys},score_samples=float(s)) for r,s in zip(val,scores)]
test=[]
for path,label,n in [(normal,0,65421),(attack,1,84)]:
    records=list(csv.DictReader(path.open(newline='',encoding='utf-8')))
    assert len(records)==n
    test.extend(dict({k:r.get(k,'') for k in keys},label=label) for r in records)
payload={'provenance':{'model_sha256':sha(model),'files':{str(p):sha(p) for p in [model,manifest,part,normal,attack]},
          'validation_scores_method':'Inferencia score_samples del IF limpio congelado; solo validation; sin fit/reentrenamiento',
          'numpy':np.__version__},'validation':validation,'test_metadata':test}
sys.stdout.buffer.write(gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', action='store_true')
    args=parser.parse_args()
    command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','gadmin@10.10.10.30',
             'ssh -o BatchMode=yes -o ConnectTimeout=8 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 /home/m4rk/cyberflow/.venv/bin/python -']
    result=subprocess.run(command,input=(INVENTORY if args.inventory else EXPORT).encode(),capture_output=True,check=True,timeout=180)
    if args.inventory:
        obj=json.loads(result.stdout)
        print(json.dumps(obj,ensure_ascii=False,indent=2))
    else:
        obj=json.loads(gzip.decompress(result.stdout))
        assert len(obj['validation'])==65633 and len(obj['test_metadata'])==65505
        dest=HERE/'entradas-alfa-if-limpio.json.gz'
        dest.write_bytes(result.stdout)
        print(json.dumps({'file':str(dest),'sha256':hashlib.sha256(result.stdout).hexdigest(),
                          'validation':len(obj['validation']),'test_metadata':len(obj['test_metadata'])},indent=2))


if __name__=='__main__':main()
