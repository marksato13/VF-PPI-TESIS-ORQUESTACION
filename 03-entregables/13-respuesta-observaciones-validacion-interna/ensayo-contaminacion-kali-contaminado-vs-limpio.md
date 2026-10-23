# Ensayo: ¿afecta la contaminación Kali al modelo? (contaminado vs limpio)

**Fecha:** 2026-10-18 · **Motivo:** observación del compañero — la ficha del modelo
vigente declara una ráfaga de la Kali dentro del entrenamiento; ¿declararlo en
limitaciones o reentrenar?

**Respuesta corta: declararlo. Reentrenar no cambia nada medible (lo demostramos abajo).**

---

## Qué se hizo

Se entrenaron **dos Isolation Forest idénticos** sobre el **mismo dataset particionado
del modelo vigente** (`particionado-nota-L.csv`: train 204 148 / validation 65 633 /
test 65 421), con los **parámetros exactos del vigente** (α=0.05, 500 árboles, semilla
20260813, `n_jobs=1`, `contamination="auto"`, umbral = percentil 0.05 de validación sobre
`decision_function`):

- **CONTAMINADO** = dataset tal cual (las ventanas de la Kali marcadas como tráfico
  normal, igual que el modelo desplegado).
- **LIMPIO** = se excluyen del entrenamiento las **181 ventanas** de la Kali
  (`10.10.20.30`) que caen en la banda de guarda `excluir_ventanas` del 27-sep
  (21:35–22:05 UTC); de ellas ~51 son el pico activo del ataque (nota S). Todas estaban
  en la partición **train**; test y validation no se tocan.

Ambos modelos se puntúan sobre **los mismos conjuntos** (test normal idéntico; el mismo
set de anomalías; y las propias ventanas del pico 27-sep), de modo que la diferencia
aislada es **solo** la contaminación.

> **Validación de la reproducción:** el modelo CONTAMINADO reproduce el vigente de forma
> exacta — umbral `decision_function = −0.068892` (idéntico al model card, equiv.
> `score_samples = −0.568892`) y **FPR test = 4.453 %** (publicado 4.4527 %). El "antes"
> de esta tabla **es** el modelo desplegado, reproducido, no una aproximación.

## Resultado

| Métrica | CONTAMINADO (vigente) | LIMPIO (181 fuera) | Δ (limpio − contaminado) |
|---|---|---|---|
| nº ventanas de entrenamiento | 204 148 | 203 967 (−181) | — |
| umbral (`decision_function`) | −0.068892 | −0.069397 | ≈ 0 |
| **FPR sobre test normal (65 421)** | **4.453 %** | **4.526 %** | **+0.073 pp** (ruido; no mejora) |
| TPR sobre anomalías de laboratorio (179, red 10.20.0.x, ago-2026) | 45.3 % | 45.3 % | **0.0 pp** |
| Detección del propio pico Kali 27-sep (181 ventanas) | 27.6 % | 27.6 % | **0.0 pp** |

**Lectura:** excluir la contaminación **no cambia nada medible**. El FPR se mueve +0.07 pp
(ni siquiera a mejor), y la capacidad de detección queda idéntica hasta la décima. La
magnitud lo explica: 181 / 204 148 = **0,089 %** del entrenamiento (y el pico activo, ~51,
es 0,025 %), muy por debajo del propio α=0.05. Un Isolation Forest es robusto a una
fracción así de pequeña por diseño.

**Conclusión:** el modelo congelado se mantiene; la contaminación se **declara** (no se
reentrena). Reentrenar produciría un modelo nuevo (otro hash, reevaluar todo) para un
cambio nulo y, si acaso, desfavorable. El mecanismo de exclusión ya está configurado en
`cyberflow.local.toml` (`excluir_ventanas`) para todos los candidatos futuros.

---

## Texto listo para la metodología (3.3.3 / construcción del conjunto)

> El conjunto de entrenamiento se construyó a partir de **tráfico de referencia
> predominantemente legítimo** capturado en la propia red. Durante la ventana de captura
> se registró una ráfaga de tráfico de la estación de pruebas (Kali, `10.10.20.30`) el
> 27-sep-2026 (21:35–22:05 UTC) que quedó incorporada a la línea base como si fuera
> normal: 181 ventanas en la partición de entrenamiento (≈51 corresponden al pico activo
> del ataque). La incidencia está documentada (nota S) y los candidatos posteriores la
> excluyen mediante la política `excluir_ventanas`. Un ensayo controlado, entrenando el
> mismo modelo con y sin esas ventanas, mostró un efecto **inapreciable** sobre el
> desempeño (ΔFPR = +0,07 pp sobre el test normal; detección sin cambio), coherente con
> que la fracción contaminada (0,089 % del entrenamiento) está muy por debajo del nivel
> de calibración α = 0,05.

## Texto listo para limitaciones

> El conjunto de entrenamiento **no es 100 % limpio**: contiene 181 ventanas de tráfico
> de la estación de pruebas (27-sep-2026) que no fueron excluidas en la versión evaluada.
> El conjunto de prueba, en cambio, no contiene ataques, por lo que el FPR reportado
> (4,45 %) no se ve afectado por esta contaminación. Un ensayo de reentrenamiento
> excluyendo esas ventanas confirmó que su efecto sobre las métricas es inapreciable.
> No se presenta el entrenamiento como realizado exclusivamente con tráfico normal.

---

## Reproducibilidad

- Entorno: Python 3.14.3 / scikit-learn 1.9.1 (sensor: 3.14.4 / 1.9.0; IsolationForest
  determinista por semilla — reproduce el vigente al 6.º decimal).
- Dataset fuente (solo lectura, del Sensor):
  `/home/m4rk/cyberflow/artifacts/linea-base/.../particionado-nota-L.csv`
  (337 980 filas; SHA/bytes = 149 543 704).
- Esquema: `multilayer-v2.json` (28 variables L3/L4/L7).
- Anomalías: `recongelar/artifacts/dataset/multilayer-v2-anomalies.csv` (179, laboratorio ago-2026).
- Script del ensayo:
  `C:\Users\markp\AppData\Local\Temp\claude\...\scratchpad\exp\experiment.py`
  (resultados en `resultados.json`).
- **El modelo de producción `if_recalibrado_2026_09` no se tocó.** Respaldo byte-idéntico:
  hash `d27f68711fcb0f6657611bd7feb17759bc4fae36b9e61fbd5ca8d1190128125a`.
