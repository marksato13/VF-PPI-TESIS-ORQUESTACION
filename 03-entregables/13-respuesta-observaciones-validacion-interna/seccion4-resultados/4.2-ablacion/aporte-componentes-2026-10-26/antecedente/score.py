import os, sys, csv, json, joblib, operator
import numpy as np
from datetime import datetime
sys.path.insert(0, '/home/m4rk/cyberflow/scripts/engine')
import heuristicos as H
# Umbral DNS corregido por el doblado del espejo (nota 23/24): todo-unico ~0.5.
H.UMBRALES_POR_DEFECTO['dns_entropy']['min_unique_dns_name_ratio_60s'] = 0.45
W = os.environ['W']; T0 = os.environ['T0']; ID = os.environ['ID']
mani = json.load(open('/home/m4rk/cyberflow/artifacts/preliminar/manifest-if-recalibrado.json'))
umb = float(mani['detectors']['if_recalibrado_2026_09']['calibration']['threshold'])
feats = mani['feature_names']
pipe = joblib.load('/home/m4rk/cyberflow/artifacts/preliminar/if_recalibrado_desplegable.joblib')
rows = [r for r in csv.DictReader(open(W + '/features.csv')) if r.get('entity_ip') == '10.10.20.30']
rows.sort(key=operator.itemgetter('window_end_utc'))
t0 = datetime.fromisoformat(T0.replace('Z', '+00:00')).timestamp()
def te(r): return datetime.fromisoformat(r['window_end_utc'].replace('Z', '+00:00')).timestamp()
X = np.array([[float(r.get(c) or 0) for c in feats] for r in rows]) if rows else np.zeros((0, len(feats)))
sc = list(pipe.score_samples(X)) if rows else []
mfirst = ''
for r, s in zip(rows, sc):
    if s < umb and te(r) >= t0 and mfirst == '':
        mfirst = round(te(r) - t0, 1)
hname = ''; haction = ''; hfirst = ''
for r in rows:
    v = H.evaluar(r)
    if v and te(r) >= t0 and hname == '':
        hname = v['heuristico']; haction = v['accion']; hfirst = round(te(r) - t0, 1)
malerts = sum(1 for s in sc if s < umb)
print('RESULT %s kaliwin=%d model_alerts=%d model_first=%s heur=%s action=%s heur_first=%s'
      % (ID, len(rows), malerts, mfirst if mfirst != '' else '-', hname or '-', haction or '-', hfirst if hfirst != '' else '-'))
