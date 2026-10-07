# Fases de la metodología — derivadas de los 15 artículos semilla

Insumo para redactar la metodología de la tesis (revista IJIES). Se analizó la
**estructura de fases** de los 15 artículos semilla, se sintetizó un **estándar
común**, y se mapearon **las fases de CyberFlow** a ese estándar, con su estado.

## A. Estructura de fases de cada artículo semilla

| # | Artículo | Fases de su metodología (sección "Proposed method/methodology") |
|---|---|---|
| 01 | 2024043017 (voting IDS) | Preprocesamiento → Selección de características → Clasificador por votación ponderada → Ajuste de pesos → Evaluación/comparación |
| 02 | 2024063018 (FS + ML) | Preprocesamiento → Selección de características → Aprendizaje del modelo → Evaluación/comparación |
| 03 | 2024103137 (IDS 6G, CapsDA) | **Recolección de datos** → Preprocesamiento → **Extracción** de características (PCA) → **Selección** (SHO) → Detección (CapsNet-DA) → Evaluación |
| 04 | 2025043014 (PSO-LightGBM) | Recolección → Preprocesamiento → **Balanceo (ADASYN)** → **Outliers (z-score)** → Selección (VarMiRF) → Modelo (PSO-LightGBM) → Evaluación |
| 05 | 2025043016 (cuckoo) | Dataset → Preparación (missing, encoding) → Selección (cuckoo) → **Clustering (K-means)** → Clasificación → Evaluación |
| 06 | 2026033101 (DL-Protect+) | Dataset → Preprocesamiento (**dedup de flujo**, embeddings, **GAN balanceo**) → **Extracción** (ventana deslizante, **entropía de puertos**, GNN) → Selección (metaheurística + SHAP) → Clasificación → Evaluación + **calibración de umbral** |
| 07 | 2026063025 (IoMT, WOA+GNN) | Preproc. + ingeniería → Selección (WOA) → Detección multinivel (LightGBM+GNN) → **Setup experimental** (imbalance, **estrategia train/val**, métricas) → Resultados |
| 08 | 2026063027 (reglas+ML) | **Diseño del estudio** → Datos/linkage/feature construction → Modelo → **Train + comparación de modelos** → **Integración reglas+ML + implementación** → **Validación cuasi-experimental** → Resultados |
| 09 | 2026063032 (fuzzy+LSTM) | Dataset (**augmentation, anti-fuga, integridad**) → Extracción → **Lógica difusa (reglas)** → LSTM → Evaluación |
| 10 | 2026063040 (EMBER, LightGBM) | Dataset → Setup experimental → Config del modelo → **Clasificadores competidores (comparación)** → Esquema de umbral triclase → Resultados (FPR@TPR, **tiempo de inferencia**, SHAP) |
| 11 | 2026063064 (DL multi-modelo) | Adquisición → Preprocesamiento (clean/encode/norm/split) → **Balanceo (SMOTE)** → Aprendizaje de features → **Diseño de arquitectura (varios modelos)** → Entrenamiento → Evaluación |
| 12 | an efficient (BiLSTM) | Preprocesamiento → Selección (función híbrida) + clasificador BiLSTM → **Setup experimental** (datasets, entrenamiento, métricas) → Resultados |
| 13 | Anomaly IDS using ML | Preprocesamiento + selección de instancias → Clasificación (AdaBoost/RF/J48/NB) → Evaluación |
| 14 | Detecting anomalies MQMT | Recolección+anotación → Extracción/ingeniería → Preprocesamiento → **Diseño del modelo** → **Entrenamiento y validación** → **Despliegue + perfil de recursos** → Evaluación (+ **generalización a mundo real**) |
| 15 | Hybrid AI-driven | Dataset → Preprocesamiento + selección → Detección de anomalía → Clasificación → Resultados (+ **alcance y limitación**) |

## B. Estándar común (el que debes seguir)

Los 15 convergen en un **pipeline empírico de ML para IDS/anomalía** (IMRaD, con
una sección "Metodología/Framework propuesto" dividida en fases):

1. **Datos / Línea base** — fuente, descripción, integridad, anti-fuga.
2. **Preprocesamiento** — limpieza, missing, encoding, normalización, (balanceo, outliers).
3. **Extracción de características** — ventanas, entropía, embeddings, PCA.
4. **Selección de características** — híbrida / metaheurística / estadística.
5. **Diseño y selección del modelo** — (varios candidatos → comparación → elegido).
6. **Entrenamiento y validación** — hiperparámetros, estrategia train/val, congelado.
7. **Montaje experimental** — entorno, métodos competidores (baseline).
8. **Evaluación y comparación** — métricas (acc/prec/recall/F1/ROC-AUC/FPR), vs baselines/prior, (tiempo/recursos, despliegue, explicabilidad).

**Los más parecidos a tu tesis** (sistema real + comparación + despliegue): **06**
(dedup de flujo, ventana deslizante, entropía de puertos, edge, calibración de
umbral), **08** (integración **reglas+ML** + implementación + **validación**), **10**
(comparación de **clasificadores competidores**, FPR@TPR, inferencia), **14**
(**despliegue + recursos + generalización a mundo real**).

## C. TUS fases (CyberFlow) mapeadas al estándar — con estado

| Fase (estándar) | Cómo se concreta en CyberFlow | Estado |
|---|---|---|
| 1. Datos / Línea base | Captura real por espejo SPAN; dataset `multilayer-v3` (712 450 ventanas); FPR 92,4→4,45 % tras recalibrar | ✅ (nota 24, L-recalibracion) |
| 2. Preprocesamiento | **Dedup del espejo** (VLAN/ip_id), ventaneo; alcance (exclusiones con cifra) | ✅ |
| 3. Extracción de características | **28 features multicapa L3/L4/L7** (ventanas 10–60 s, entropía DNS, ratios de puertos) | ✅ (esquema v2) |
| 4. Selección de características | Esquema congelado de 28 features (v2); L2 queda para v3 | ✅ / ◐ (L2 futuro) |
| 5. Diseño y **selección del modelo** | **7 modelos comparados** (OCSVM, IsolationForest, …) → **elegido IsolationForest** recalibrado | ✅ corrido; **falta la TABLA escrita** |
| 6. Entrenamiento y validación | Modelo **congelado** (umbral −0,568892), reproducible; runbook + rollback | ✅ (RUNBOOK-CONGELAR) |
| 6-bis. **Detección híbrida** (modelo + reglas) | IsolationForest + **heurísticos** deterministas (brute/scan/http/dns) | ✅ **ablación 6/7/9** (nota 31) |
| 6-ter. **Respuesta/enforcement** (tu aporte) | PERMIT/LIMIT/BLOCK con feed firmado (ed25519), escalada | ✅ (no está en los 15 → diferenciador) |
| 7. Montaje experimental / comparación | **Replay del mismo PCAP** a CyberFlow y Suricata (ET Open), reloj del paquete | ✅ (nota 19, 22) |
| 8. Evaluación y comparación | **9/9 vs 0/9**; Nikto (tiempo 3,4 vs 12 s); **4 familias** (incl. brute); métricas TPR/FPR/latencia (`30-metricas.py`) | ✅ (notas 26–32); ◐ falta N mayor y Suricata-vs-brute |
| 9. **Despliegue / operación real** (como art. 06/14) | Desplegado en el sensor; enforcement en vivo; tiempos det 2–40 s, resp 1–2,5 min | ✅ |
| 10. **Validación** (como art. 08) | **Interna** (demo técnica + grabar expertos, jueves); **externa** (TAM + juicio de expertos) | ⏳ interna el jueves; externa futura |

## D. Lo que FALTA para cerrar la metodología (resumen)

- **Fase 5:** escribir la **tabla de comparación de los 7 modelos** (métricas → por qué
  IsolationForest). El script existe (`compare_frozen_models_metrics.py`); los
  artefactos están en el store de modelado (localizarlos).
- **Fase 8:** N mayor (rangos) y comparación **Suricata-vs-fuerza-bruta** por replay.
- **Fase 10:** ejecutar la **validación interna** (jueves) y planificar la **externa** (TAM).
- **Fase 4:** capa 2 en el scoring = **v3** (plan de reentrenamiento, post-validación).

> Tu tesis es **más completa que el artículo semilla típico**: añade respuesta
> (enforcement) y despliegue real + validación, como solo los artículos 06/08/14
> insinúan. Ese es el ángulo diferenciador a resaltar en la redacción.
