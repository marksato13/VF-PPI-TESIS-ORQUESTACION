"""Análisis exploratorio local de α. No modifica artefactos canónicos ni despliegue.

python analizar_alfa.py
Entradas: scores completos del test y exportación de validación original.
No se ajusta ningún modelo; los ocho cortes proceden solo de validation.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from bisect import bisect_left
import csv
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import urllib.parse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'PENDIENTES.md').exists())
PRODUCT = ROOT.parent/'producto-as-deployed'
V2 = ROOT/'03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/_campana/resultados-2026-10-23/eval41/v2'
ALPHAS = [.005,.01,.02,.025,.03,.04,.05,.10]
U = -.5693969936322356


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save_json(path, obj):path.write_bytes((json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def save_text(path, value):path.write_bytes(value.encode())
def save_csv(path, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def source(repo, revision, path, first=None, last=None):
    commit=subprocess.check_output(['git','rev-parse',revision],cwd=repo,text=True).strip()
    data=subprocess.check_output(['git','show',f'{revision}:{path}'],cwd=repo)
    lines=data.decode().splitlines()
    return {'repository':repo.name,'commit':commit,'path':path,
            'blob_sha256':hashlib.sha256(data).hexdigest(),
            'commit_date':subprocess.check_output(['git','show','-s','--format=%aI',commit],cwd=repo,text=True).strip(),
            'lines': [{'line':i+1,'text':line} for i,line in enumerate(lines)
                      if (first is None or i+1>=first) and (last is None or i+1<=last)]}


def audit():
    s=[source(PRODUCT,'34e31cd','docs/fase04-modelado/01-protocolo-modelado-F1-v2.md',62,78),
       source(PRODUCT,'34e31cd','docs/fase04-modelado/04-protocolo-modelado-multilayer-v2-y-hoja-de-ruta.md',20,75),
       source(PRODUCT,'71a72d6','scripts/modeling/entrenar_preliminar.py',76,145),
       source(ROOT,'84f3eb2','02-metodologia/metodologia-7-fases/F3-modelado-hibrido.md',64,105),
       source(ROOT,'37fb2e2','04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md',28,64),
       source(ROOT,'37fb2e2','02-metodologia/historico-laboratorio/fase04-modelado/09-validacion-cruzada-y-estabilidad.md'),
       source(ROOT,'d0b8e18','03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/ESQUEMA-AFIRMACIONES-Y-CIERRE-4.1.md',1,25)]
    s.append(source(PRODUCT,'b204f59','scripts/modeling/experiments/validacion_cruzada_estabilidad.py',81,161))
    s.append(source(PRODUCT,'b204f59','results/ablacion/validacion-cruzada-estabilidad.json'))
    history=json.loads(subprocess.check_output(['git','show','b204f59:results/ablacion/validacion-cruzada-estabilidad.json'],cwd=PRODUCT))
    folds=history['validacion_cruzada']['pliegues'];saved=history['validacion_cruzada']
    recomputed={
        'deteccion_media':statistics.mean(100*f['det']/179 for f in folds),
        'deteccion_desv':statistics.stdev(100*f['det']/179 for f in folds),
        'fpr_media':statistics.mean(100*f['fp']/f['n_prueba'] for f in folds),
        'fpr_desv':statistics.stdev(100*f['fp']/f['n_prueba'] for f in folds),
    }
    for k,v in recomputed.items():assert math.isclose(v,saved[k],abs_tol=1e-12)
    boot=history['estabilidad_umbral']
    cv=abs(boot['desv']/boot['media'])*100
    assert math.isclose(cv,boot['cv_pct'],abs_tol=1e-12)
    out={'sources':s,'historical_model':'OCSVM de laboratorio, no IF limpio',
         'historical_alpha_compared':[.05], 'historical_summaries_arithmetic_verified':recomputed,
         'historical_bootstrap_cv_recomputed_pct':cv,
         'bootstrap_summary':boot,
         'verification_limit':'Se verifican aritmética y correspondencia código/documento/JSON; no se reentrena y no se reproducen los 1000 remuestreos sin su serie original.',
         'clean_IF_stability_demonstrated':False,
         'alpha_005_more_stable_than_other_alphas_demonstrated':False}
    save_json(HERE/'EVIDENCIA-ORIGINAL-ALFA.json',out)
    return out


def metrics(alpha, threshold, scores, labels, mask):
    pred=scores[mask]<threshold;y=labels[mask]
    tp=int(np.sum(pred&(y==1)));fp=int(np.sum(pred&(y==0)))
    fn=int(np.sum(~pred&(y==1)));tn=int(np.sum(~pred&(y==0)))
    def ratio(a,b):return a/b if b else None
    return {'alfa':alpha,'umbral':float(threshold),'TP':tp,'FN':fn,'FP':fp,'TN':tn,
            'recall':ratio(tp,tp+fn),'FPR':ratio(fp,fp+tn),'precision':ratio(tp,tp+fp),
            'F1':ratio(2*tp,2*tp+fp+fn),'n_positivas':tp+fn,'n_normales':fp+tn}


def table(rows):
    lines=['| Alfa | Umbral (score_samples) | TP | FN | FP | TN | Recall | FPR | Precisión | F1 |',
           '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        a=f"{r['alfa']:g}".replace('.',',')
        u=repr(r['umbral']).replace('.',',')
        lines.append(f"| {a} | {u} | {r['TP']} | {r['FN']} | {r['FP']} | {r['TN']} | {r['recall']:.2%} | {r['FPR']:.2%} | {r['precision']:.2%} | {r['F1']:.5f} |")
    return '\n'.join(lines)


def main():
    history=audit()
    testfile=V2/'scores-todos-candidatos-full.csv.gz'
    assert sha(testfile)=='6e98219fb79a187b7256e664a4791a0619be70a68d9a23eee1e61c45de98ffc8'
    inputs=HERE/'entradas-alfa-if-limpio.json.gz'
    payload=json.loads(gzip.decompress(inputs.read_bytes()))
    rows=list(csv.DictReader(gzip.open(testfile,'rt',encoding='utf-8')))
    val=payload['validation'];meta=payload['test_metadata']
    assert len(val)==65633 and len(rows)==65505
    assert len({(r['campaign_id'],r['entity_ip'],r['window_end_utc']) for r in val})==65633
    key=lambda r:(r['campaign_id'],r['entity_ip'],r['window_end_utc'],int(r['label']))
    assert len({key(r) for r in rows})==len(rows)
    bykey={key(r):r for r in meta};assert len(bykey)==len(rows)
    assert set(bykey)=={key(r) for r in rows}
    aligned=[bykey[key(r)] for r in rows]
    labels=np.array([int(r['label']) for r in rows])
    scores=np.array([float(r['score::IF limpio (desplegado)']) for r in rows])
    recent=np.array([float(r['packet_count_10s'])>0 for r in aligned])
    sv=np.array([r['score_samples'] for r in val]);assert np.isfinite(sv).all()
    assert sum(r['entity_ip']=='10.10.20.30' for r in val)==80
    thresholds=np.quantile(sv,ALPHAS,method='linear')
    assert float(thresholds[ALPHAS.index(.05)])==U
    global_rows=[metrics(a,t,scores,labels,np.ones(len(rows),dtype=bool)) for a,t in zip(ALPHAS,thresholds)]
    recent_rows=[metrics(a,t,scores,labels,recent) for a,t in zip(ALPHAS,thresholds)]
    assert recent_rows[0]['n_normales']==19863 and recent_rows[0]['n_positivas']==84
    r05=global_rows[ALPHAS.index(.05)]
    assert (r05['TP'],r05['FN'],r05['FP'],r05['TN'])==(54,30,2961,62460)
    assert recent_rows[ALPHAS.index(.05)]['FP']==2837
    previous=json.loads((V2/'p1-reconciliacion.json').read_bytes())
    for old in previous['alfa_val_total']:
        new=global_rows[ALPHAS.index(old['alfa'])]
        for oldkey,newkey in [('umbral','umbral'),('fpr_obs','FPR'),('recall','recall'),('precision','precision'),('F1','F1')]:
            assert math.isclose(old[oldkey],new[newkey],abs_tol=1e-12,rel_tol=1e-12)
    save_csv(HERE/'sensibilidad-alfa-global.csv',global_rows)
    save_csv(HERE/'sensibilidad-alfa-paquetes-recientes.csv',recent_rows)
    for name,items in [('TABLA-ALFA-GLOBAL.md',global_rows),('TABLA-ALFA-PAQUETES-RECIENTES.md',recent_rows)]:
        save_text(HERE/name,table(items)+'\n')
    validation=[{'alfa':a,'umbral':float(t),'n_validacion':len(sv),
                 'alertas_estrictas_validacion':int(np.sum(sv<t)),
                 'empates_en_umbral':int(np.sum(sv==t))} for a,t in zip(ALPHAS,thresholds)]
    save_csv(HERE/'cortes-solo-validacion.csv',validation)
    exchanges=[]
    for low,high in zip(global_rows,global_rows[1:]):
        dt=high['TP']-low['TP'];df=high['FP']-low['FP']
        exchanges.append({'alfa_desde':low['alfa'],'alfa_hasta':high['alfa'],
                          'ventanas_positivas_adicionales':dt,'FP_adicionales':df,
                          'FP_por_positiva_adicional':df/dt if dt else None,
                          'sin_ganancia_deteccion':dt==0})
    save_csv(HERE/'intercambios-adyacentes.csv',exchanges)
    relative=[]
    for r in global_rows:
        relative.append({'alfa':r['alfa'],'referencia':.05,'delta_TP':r['TP']-r05['TP'],
                         'delta_FN':r['FN']-r05['FN'],'delta_FP':r['FP']-r05['FP'],
                         'delta_TN':r['TN']-r05['TN'],
                         'mismas_positivas_detectadas_que_005':bool(np.array_equal((scores<r['umbral'])&(labels==1),(scores<U)&(labels==1)))})
    save_csv(HERE/'intercambios-respecto-005.csv',relative)
    dominance=[]
    for r in global_rows:
        for other in global_rows:
            if other['TP']>=r['TP'] and other['FP']<=r['FP'] and (other['TP']>r['TP'] or other['FP']<r['FP']):
                dominance.append({'alfa_dominada':r['alfa'],'alfa_dominante':other['alfa'],
                                  'positivas_adicionales':other['TP']-r['TP'],
                                  'FP_evitados':r['FP']-other['FP']})
    save_csv(HERE/'dominancia-observada.csv',dominance)
    scenarios=[]
    # Costos exclusivamente hipotéticos por ventana, no costos operativos medidos.
    for ratio in [1,100,290,300,400,1000]:
        costs=[r['FP']+ratio*r['FN'] for r in global_rows]
        best=min(costs)
        scenarios.append({'escenario':'HIPOTETICO: C_FP=1; C_FN='+str(ratio),
                          'mejores_en_rejilla':[r['alfa'] for r,c in zip(global_rows,costs) if c==best],
                          'coste_minimo':best,'coste_alfa_005':r05['FP']+ratio*r05['FN']})
    for metric,limit in [('FPR',.01),('FPR',.02),('recall',.64),('recall',.70)]:
        allowed=[r for r in global_rows if r[metric]<=limit] if metric=='FPR' else [r for r in global_rows if r[metric]>=limit]
        choice=max(allowed,key=lambda r:(r['TP'],-r['FP'])) if metric=='FPR' else min(allowed,key=lambda r:(r['FP'],-r['TP']))
        scenarios.append({'escenario':f'HIPOTETICO: {metric} '+('<=' if metric=='FPR' else '>=')+str(limit),
                          'mejores_en_rejilla':[choice['alfa']]})
    save_json(HERE/'escenarios-hipoteticos.json',scenarios)
    # Descripción por día UTC con cortes fijos; no es CV, bootstrap ni test nuevo.
    days=sorted({datetime.fromisoformat(r['window_end_utc']).date().isoformat() for r in rows})
    dates=np.array([datetime.fromisoformat(r['window_end_utc']).date().isoformat() for r in rows])
    temporal=[]
    for day in days:
        for a,t in zip(ALPHAS,thresholds):
            for name,mask in [('global',dates==day),('paquetes_recientes',(dates==day)&recent)]:
                item=metrics(a,t,scores,labels,mask)
                # No presentar precisión=100 % por construcción en un día solo positivo.
                item.pop('precision');item.pop('F1')
                temporal.append({'dia_utc':day,'grupo':name,**item})
    save_csv(HERE/'descriptivo-por-dia-utc.csv',temporal)
    plt.rcParams.update({'font.size':10,'axes.titlesize':11,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(10,4.7),layout='constrained',sharey=True)
    offsets=[(5,-17),(5,-17),(0,-18),(-15,9),(-12,20),(-7,-22),(3,8),(-42,9)]
    for ax,items,title in zip(axes,[global_rows,recent_rows],['(a) Global: 65 421 normales + 84 positivas','(b) Con paquetes: 19 863 normales + 84 positivas']):
        ax.plot([100*r['FPR'] for r in items],[100*r['recall'] for r in items],color='#7a7a7a',lw=1,zorder=1)
        for r,offset in zip(items,offsets):
            ax.scatter(100*r['FPR'],100*r['recall'],s=70 if r['alfa']==.05 else 32,
                       marker='D' if r['alfa']==.05 else 'o',color='#d55e00' if r['alfa']==.05 else '#0072b2',zorder=3)
            ax.annotate(f"α={r['alfa']:g}".replace('.',','),(100*r['FPR'],100*r['recall']),xytext=offset,textcoords='offset points',fontsize=9,
                        arrowprops={'arrowstyle':'-','color':'#888','lw':.5})
        ax.set_title(title);ax.set_xlabel('FPR (%)');ax.grid(alpha=.25)
        ax.set_xlim(0,max(r['FPR'] for r in items)*108);ax.set_ylim(0,100)
    axes[0].set_ylabel('Recall de ventanas etiquetadas (%)')
    fig.suptitle('Sensibilidad exploratoria: cortes solo en validación (n = 65 633)\nDiamante naranja: α=0,05 congelado; no se cambia el despliegue',fontsize=12)
    for ext in ['png','svg','pdf']:fig.savefig(HERE/f'recall-frente-fpr-alfa.{ext}',dpi=400)
    plt.close(fig)
    svg=HERE/'recall-frente-fpr-alfa.svg'
    save_text(svg,'\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n')
    summary={'validation_n':len(sv),'quantile_method':'numpy.quantile(method=linear)',
             'comparison':'score_samples < threshold','validation_Kali':80,'validation_Kali_active_unconfirmed':17,
             'test_source_sha256':sha(testfile),'inputs_sha256':sha(inputs),
             'provenance':payload['provenance'],'global':global_rows,'recent':recent_rows,
             'dominance':dominance,'exchanges':exchanges,'hypothetical_scenarios':scenarios,
             'temporal_rows':len(temporal),'test_already_observed':True,'model_or_deployment_change':False,
             'historical_arithmetic_verified':True,'clean_IF_performance_stability_demonstrated':False}
    save_json(HERE/'resultados-alfa.json',summary)
    # Comprobación independiente de conteos con búsqueda binaria, sin reutilizar
    # las máscaras booleanas de metrics(). Cuantil contrastado por interpolación.
    sorted_val=sorted(float(v) for v in sv)
    checks=[]
    for group,items,mask in [('global',global_rows,np.ones(len(rows),dtype=bool)),('recientes',recent_rows,recent)]:
        positives=sorted(float(s) for s,y,m in zip(scores,labels,mask) if m and y==1)
        normals=sorted(float(s) for s,y,m in zip(scores,labels,mask) if m and y==0)
        for r in items:
            rank=(len(sorted_val)-1)*r['alfa'];lo=math.floor(rank);hi=math.ceil(rank)
            q=sorted_val[lo]+(rank-lo)*(sorted_val[hi]-sorted_val[lo])
            assert math.isclose(q,r['umbral'],abs_tol=1e-15,rel_tol=0)
            assert bisect_left(positives,r['umbral'])==r['TP']
            assert bisect_left(normals,r['umbral'])==r['FP']
            checks.append({'grupo':group,'alfa':r['alfa'],'cuantil_independiente':True,'conteos_bisect_left':True})
    assert global_rows[ALPHAS.index(.03)]['TP']==r05['TP']
    assert global_rows[ALPHAS.index(.03)]['FP']==1725
    assert all(global_rows[i]['TP']<=global_rows[i+1]['TP'] and global_rows[i]['FP']<=global_rows[i+1]['FP'] for i in range(7))
    save_json(HERE/'COMPROBACION-ALFA.json',{'checks':checks,'discrepancies':0,
              'model_sha256':payload['provenance']['model_sha256'],
              'score_test_hash_confirmed':True,'metadata_alignment_unique_rows':65505,
              'operational_threshold_reproduced_exactly':True,'operational_TP_FN_FP_TN_confirmed':True,
              'positive_sets_003_004_005_identical':all(r['mismas_positivas_detectadas_que_005'] for r in relative if r['alfa'] in [.03,.04,.05]),
              'monotonic_TP_FP':True,'new_training':False,'new_campaigns':False,'deployment_changes':False})
    index=HERE/'ARCHIVOS-ALFA.md'
    files=sorted(p for p in HERE.iterdir() if p.is_file() and p.name not in ['MANIFIESTO-ALFA.json','ARCHIVOS-ALFA.md'])
    save_text(index,'# Archivos del análisis exploratorio de α\n\n'+'\n'.join(
        f"- `{p}` — [GitHub](https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/blob/main/{urllib.parse.quote(p.relative_to(ROOT).as_posix(),safe='/')})"
        for p in files+[index,HERE/'MANIFIESTO-ALFA.json'])+'\n')
    files.append(index)
    save_json(HERE/'MANIFIESTO-ALFA.json',{'scope':'Exploratorio; test ya observado; no selección independiente',
        'files':{p.name:sha(p) for p in files},'source_test_sha256':sha(testfile),
        'validation_input_sha256':sha(inputs),'serialization':'UTF-8/LF, hashes sobre bytes finales',
        'model_or_deployment_changes':False})
    print(table(global_rows));print('\nRECIENTES\n'+table(recent_rows))
    print('\nDOMINANCIA',json.dumps(dominance))
    print('\nTEMPORAL 0.05',json.dumps([r for r in temporal if r['alfa']==.05]))
    print('\nESCENARIOS',json.dumps(scenarios))


if __name__=='__main__':main()
