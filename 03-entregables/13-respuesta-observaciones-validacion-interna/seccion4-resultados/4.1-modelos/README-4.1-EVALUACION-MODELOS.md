# 4.1 — Evaluación del modelo limpio y comparación entre modelos

> **Actualización 2026-10-25.** La comparación **entre algoritmos** vigente es
> `comparacion-metodos-2026-10-25/` (IF congelado frente a OCSVM, LOF, Elliptic Envelope y PCA entrenados con
> los mismos datos del sensor). La «Tabla 7» de este documento compara candidatos históricos congelados
> (variantes del IF y un OCSVM de laboratorio) y queda como registro. La calibración α vigente está en
> `calibracion-alfa-2026-10-24/`.

> **Re-audit endurecido (v2, 2026-10-23): ver `ESQUEMA-AFIRMACIONES-Y-CIERRE-4.1.md`** (autoritativo).
> Corrige: se **retiró Det@FPR5%** (corte sobre test = fuga), el IF limpio **no gana en todo**
> (el contaminado tiene AP 0,203 > 0,186 y FPR 4,45 % < 4,53 %; son equivalentes), `IF uniform ≡ IF exact`,
> la evaluación es **reutilizada** (no test ciego), y se añadió sensibilidad de α (F6) + figura a resolución
> completa + scores de los 9 candidatos. Resultados duros en `../_campana/resultados-2026-10-23/eval41/v2/`.
> Lo de abajo es el primer pase (valores coincidentes; el v2 manda).

**Ejecutado 2026-10-23** en el sensor (lectura), modelo **desplegado `if_limpio_2026_10`**.
Conjunto: **oro = 65 421 ventanas normales** (`artifacts/aprendizaje/oro/oro.csv`) + **84 ventanas
de ataque** (`artifacts/aprendizaje/ataques/ataques-nota-M.csv`). Cada modelo se carga congelado y
se puntúa con `score_samples` sobre los **mismos** datos (Pipelines con escalador dentro → **no hay
doble escalado**). No se reentrena nada. Clase positiva = anomalía; para ROC/PR el score se orienta
a "mayor = más anómalo" (`-score_samples`). AP = `average_precision_score` (sklearn).

Resultados crudos y figura: `../_campana/resultados-2026-10-23/eval41/` (metricas.json, curvas.json,
TABLA6.md, TABLA7.md, **figura-roc-pr.png/svg**, scores por ventana). Script reproducible:
`eval_4_1.py` (aquí) + `../_campana/figura_roc_pr.py`.

## Tabla 6 — IF limpio (umbral operativo `score_samples < −0,569397`)

| TP | FP | TN | FN | Precisión | Recall | F1 | FPR | ROC-AUC | AP |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 54 | 2 961 | 62 460 | 30 | 0,0179 | **0,6429** | 0,0348 | **0,0453** | **0,9247** | 0,1858 |

- **Recall 64,3 % (54/84)** y **FPR 4,53 %** con el umbral operativo. Precisión/F1 bajos por el
  desbalance extremo (prevalencia 0,13 %): miles de FP frente a decenas de TP — por eso el titular
  son ROC-AUC/AP/FPR, no precisión/F1. En operación un FP del modelo da **LIMIT** (reversible), no
  bloqueo.
- **Detección por familia (modelo limpio) — cerrada.** El CSV no trae etiqueta de familia, pero se
  aplica el **criterio observable de la nota M (errata)**: HTTP si `http_request_count_60s>0`; si no,
  DNS si `dns_query_count_60s>0`; en otro caso escaneo. Resultado del **IF limpio**:

  | Familia | Ventanas | Detectadas | TPR |
  |---|---:|---:|---:|
  | HTTP | 43 | 35 | 81,4 % |
  | Escaneo | 33 | 19 | 57,6 % |
  | DNS | 8 | 0 | 0,0 % |
  | **Total** | **84** | **54** | **64,3 %** |

  **Idéntico** a la reconstrucción de nota M para el contaminado (HTTP 35/43 · escaneo 19/33 · DNS 0/8)
  → limpiar tampoco cambió la detección por familia. El DNS 0/8 es del montaje de nota M (apuntó al
  DMZ, no al resolver); lo cubre el heurístico `dns_entropy` (ver 4.2). Detalle:
  `../_campana/resultados-2026-10-23/eval41/DETECCION-POR-FAMILIA-limpio.md`.

## Tabla 7 — Candidatos sobre las MISMAS 84 + 65 421 ventanas

| Modelo | Entrenamiento | ROC-AUC | AP | Det@FPR5% | FPR propio | Recall propio |
|---|---|---:|---:|---:|---:|---:|
| **IF limpio (desplegado)** | esta red | **0,9247** | **0,1858** | **65,5 %** | 4,53 % | 64,3 % |
| IF recalibrado (contaminado, respaldo) | esta red | 0,9228 | 0,2026 | 66,7 % | ~4,5 % | ~64 % |
| IF scaled (lab) | laboratorio | 0,8250 | 0,0043 | 16,7 % | — | — |
| IF primary (lab) | laboratorio | 0,8283 | 0,0044 | 16,7 % | — | — |
| IF uniform (lab) | laboratorio | 0,7960 | 0,0054 | 16,7 % | — | — |
| IF exact (lab) | laboratorio | 0,7960 | 0,0054 | 16,7 % | — | — |
| OCSVM (lab) | laboratorio | 0,4555 | 0,0011 | n/a* | — | — |
| LOF (lab) | laboratorio | 0,2991 | 0,0009 | 0,0 % | — | — |
| Elliptic Envelope (lab) | laboratorio | 0,3443 | 0,0014 | 5,9 % | — | — |

\* OCSVM/LOF no alcanzan un corte real al 5 % de FPR (scores degenerados: marcan casi todo el normal
como anómalo en esta red; su FPR al percentil 95 sale 0,70/0,50). Consistente con ROC-AUC ≤ azar.

**Tabla 7 completa (cada modelo a su umbral propio): `../_campana/resultados-2026-10-23/eval41/TABLA7-completa.md`**
(Precisión/Recall/F1/FPR además de ROC-AUC/AP). Lo esencial: el **IF limpio** (FPR 4,53 %, recall 64,3 %)
≈ **contaminado** (FPR 4,45 %, recall 64,3 %); los candidatos de laboratorio tienen recall alto pero
**FPR 29–99 %** (inservibles aquí); OCSVM recall 100 % con **FPR 99,57 %** (marca todo). Hashes de cada
joblib, umbrales y versiones (sklearn 1.9.0) en `hashes-deps-aux.json`.

**Lectura:**
- El **IF limpio gana** (ROC-AUC 0,925, Det@FPR5% 65,5 %) y es el único con un **FPR usable** (4,53 %)
  con su umbral. **Limpiar la contaminación NO degradó la detección**: recall **54/84 idéntico** al
  contaminado (ROC-AUC 0,925 vs 0,923, equivalente; la diferencia es ruido de muestra).
- Los candidatos de **laboratorio transfieren mal** (ROC 0,80–0,83, Det@FPR5% 16,7 %); el **OCSVM**
  —ganador en el banco— cae a ROC-AUC 0,456 (bajo el azar) aquí.
- **Honestidad:** los candidatos de laboratorio y el IF de esta red tienen **condiciones de
  entrenamiento distintas**; esta comparación mide **transferencia** a la red objetivo, no
  superioridad intrínseca del algoritmo. Para aislar la arquitectura haría falta un protocolo
  aparte (ajuste en train, selección en validation, evaluación única en test).

## Reproducibilidad

- Script: `eval_4_1.py` (corre en el sensor con el venv) → `figura_roc_pr.py` (local, lee `curvas.json`).
- SHA-256 de entradas: oro `08604ae3…`, ataques `4affd07f…`.
- Scores por ventana del modelo limpio (84+65 421): SHA-256 del CSV completo
  `53cdfb3b5b94f99e76b03f8cfa789c6e2b92e5f536f79be0224af6768567aaac`
  (regenerable con `eval_4_1.py`; las 84 filas de ataque están en
  `../_campana/resultados-2026-10-23/eval41/scores-clean-ataque-84.csv`).
- Umbrales: limpio `−0,569397` (score_samples); contaminado `−0,568892`.

## Cierre (flecos resueltos 2026-10-23, `cerrar_41.py`)

- ✅ **Detección por familia del modelo limpio** (criterio observable de nota M) — tabla arriba;
  idéntica al contaminado.
- ✅ **Tabla 7 completa** con Precisión/Recall/F1/FPR por modelo (`TABLA7-completa.md` / `.csv`).
- ✅ **Hashes + versiones + umbrales** (`hashes-deps-aux.json`).

## Pendiente (opcional)

- Significancia McNemar+Holm del limpio vs candidatos sobre estas predicciones
  (`producto-main/scripts/modeling/experiments/significancia_modelos.py`).
</content>
