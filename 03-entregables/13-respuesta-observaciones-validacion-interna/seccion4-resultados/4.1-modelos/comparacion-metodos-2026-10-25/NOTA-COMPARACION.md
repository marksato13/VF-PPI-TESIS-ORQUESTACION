# Comparación de cinco detectores — nota técnica (25-oct-2026)

Cálculo **offline** en el laptop. El IF desplegado (`if_limpio_2026_10`) **no se reentrena**: se usan sus
puntuaciones del sensor y aquí solo se verifican. El modelo, los servicios y la configuración del sensor no se tocaron.
La tabla completa está en `TABLA7-comparacion.md` / `TABLA7-comparacion-completa.csv`, y los hashes en `MANIFIESTO-COMPARACION.json`.

## 1. Auditoría de datos (detalle en `AUDITORIA-DATOS.json`)

| Conjunto | Ventanas | Cómo se obtuvo |
|---|---:|---|
| Partición `train` | 204 148 | `particionado-limpio.csv` (SHA `5ef83b32…`, entrada declarada del IF) |
| Entrenamiento efectivo | **203 967** | `eligible_training == True`. Las 181 restantes (ráfaga de 10.10.20.30, 27-sep 21:35–22:05 UTC) se excluyen **por su bandera**; otras 368 ventanas de esa IP siguen siendo elegibles |
| Validación | 65 633 → **65 553** | Se quitan las 80 claves de `validacion-kali-80-excluidas.csv` (son todas las de 10.10.20.30 en validación). No se etiquetan como ataque |
| Prueba normal | **65 421** | `oro.csv`, idéntico a la partición `test`. **Conserva 74 ventanas de 10.10.20.30**, cuya normalidad no está confirmada |
| Ataques | **84** | `ataques-nota-M.csv`, solo para evaluar |
| Evaluación | **65 505** | 65 421 + 84 |

- Los seis archivos de entrada coinciden por SHA-256 con `sensor-procedencia.json`. Los 15 cruces de claves (`campaign_id`, `entity_ip`, `window_end_utc`) entre train, validación, prueba, ataques, las 181 y las 80 dan **0**.
- **Variables:** 28, en el orden del manifiesto del IF. Se leen como `float64`. Una celda vacía o no numérica detendría la lectura, y no ocurre. Hay 0 valores no finitos. Etiquetas, IP, fechas y partición no entran al modelo.
- **Constantes en el entrenamiento:** `fragment_ratio_10s` y `tls_handshake_failure_ratio_60s`. El escalador congelado les asigna `scale_ = 1`.
- **Duplicados:** 126 061 de 203 967 filas (62 %) están duplicadas. El vector todo ceros aparece 109 178 veces (53,5 %).
- **Ventanas sin paquetes recientes** (`packet_count_10s == 0`): 146 901 en entrenamiento, 45 826 en validación, 45 558 en prueba y 0 en ataques. **Se conservan**, como pide el encargo. En vivo, el motor no puntúa estas ventanas, así que las FPR de aquí **no equivalen** a la FPR operativa.
- **Escalador:** el `StandardScaler` del pipeline desplegado (`n_samples_seen = 203 967`). Sus `mean_` y `scale_` son idénticos a los exportados en el sensor con scikit-learn 1.9.0. El laptop usa 1.9.1, que avisa del cambio de versión al cargar. Al volver a puntuar el IF localmente, la diferencia máxima con el sensor es 1,1·10⁻¹⁶.

## 2. Configuración

Todo se registró en `config-comparacion.json` **antes** de entrenar. No hubo búsqueda de hiperparámetros, porque no hay normales etiquetados fuera de la validación, y la validación se reserva para el umbral.

| Método | Configuración | Puntuación (mayor = más anómalo) |
|---|---|---|
| IF | Congelado: 500 árboles, `random_state=20260813` | `−score_samples` |
| OCSVM | RBF, `nu=0,05`, `gamma="scale"` → 1/26 efectivo (las 2 constantes reducen la varianza total), `tol=1e-3`. **Entrenado con las 203 967 filas**, sin submuestra; 10 235 vectores de soporte | `−score_samples` |
| LOF | `novelty=True`, k=20, euclídea (Minkowski p=2), búsqueda `brute` elegida por scikit-learn. Se evalúan solo ventanas que no se usaron al ajustar | `−score_samples` |
| Elliptic Envelope | FastMCD, `random_state=20260813`, **`support_fraction=0,75` (desviación D1)** | `−score_samples` = Mahalanobis² robusta |
| PCA | k mínimo con varianza explicada ≥ 95 % en el entrenamiento escalado: **k = 17** (95,9 %) | ‖z − ẑ‖², con ẑ = μ + (z−μ)VₖᵀVₖ en el espacio escalado |

**Desviación D1 (Elliptic Envelope).**
- **Fallo con lo registrado:** la configuración original (soporte h = 50 %) **falla** con «covariance matrix of the support data is equal to 0». El grupo de ceros (53,5 %) es mayor que h, así que el subconjunto MCD óptimo es ese único punto.
- **Regla aplicada:** se tomó el primer valor de {0,75; 0,9; 1,0} mayor que 0,535, usando solo el entrenamiento y antes de ver ninguna puntuación de EE.
- **Persiste el mal condicionamiento:** aun así, la covarianza robusta tiene **16 de 28 autovalores < 10⁻⁶** y la precisión tiene rango 15. El soporte está dominado por ventanas sin paquetes, donde muchas variables son casi constantes. De ahí los umbrales de 10⁸–10⁹.
- **Conclusión:** el supuesto del método (una sola nube elíptica gaussiana) **no se cumple** en estos datos.

**Calibración.**
- Umbral = `quantile(validación_65 553, 1−α, method="linear")`; anomalía si la puntuación es estrictamente mayor que el umbral.
- **Empates:** 0 en el umbral, en todos los métodos y con ambos α. La FPR de validación es 3,0006 % y 5,0005 %.
- **Conversión al IF:** con interpolación lineal, el cuantil 1−α de −s es −(cuantil α de s). Por eso la regla original del IF (`score_samples < umbral`) es equivalente. Para el IF, el umbral reproducido difiere del de referencia en 2,2·10⁻¹⁶ (α = 0,03) y 1,1·10⁻¹⁶ (α = 0,05), por redondeo al negar. TP, FP, TN y FN son idénticos (54/1 723/63 698/30 y 54/2 955/62 466/30), y también la ROC-AUC (0,9247265513) y la AP (0,1858068840).
- **No confundir con el despliegue:** el umbral desplegado (−0,5693969936322356, α = 0,05 sobre **65 633**) **no** es ninguno de estos.

## 3. Resultados (prueba: 65 421 normales + 84 ataques)

| Método | ROC-AUC | AP | TP / FP (α = 0,03) | FPR prueba 0,03 | TP / FP (α = 0,05) | FPR prueba 0,05 |
|---|---:|---:|---:|---:|---:|---:|
| IF | 0,9247 | 0,1858 | 54 / 1 723 | **2,63 %** | 54 / 2 955 | **4,52 %** |
| OCSVM | 0,8691 | **0,6357** | 59 / 1 958 | 2,99 % | 71 / 3 319 | 5,07 % |
| LOF | **0,9763** | 0,0291 | **77** / 2 314 | 3,54 % | **79** / 3 766 | 5,76 % |
| Elliptic Envelope | 0,9179 | 0,3811 | 44 / 1 785 | 2,73 % | 48 / 3 039 | 4,65 % |
| PCA | 0,9487 | 0,5944 | 71 / 2 116 | 3,23 % | 71 / 3 539 | 5,41 % |

Precisión, recall, F1, FN, TN y los umbrales con todos sus decimales están en la Tabla 7.

## 4. Hallazgos técnicos

1. **El IF no es el mejor en detección.**
   - A igual α, PCA, LOF y OCSVM detectan más ataques que el IF (71, 77 y 59 frente a 54 con α = 0,03).
   - LOF tiene la mayor ROC-AUC, y OCSVM y PCA la mayor AP.
   - F1 con α = 0,03: PCA 0,0625, LOF 0,0622, **IF 0,0580**, OCSVM 0,0562 y EE 0,0460. Con α = 0,05, el IF queda cuarto (0,0349).
2. **El IF tiene la menor FPR de prueba con ambos α** (2,63 % y 4,52 %). Junto con Elliptic Envelope (2,73 % y 4,65 %), es de los que quedan **por debajo** de la FPR calibrada en validación. LOF (+0,54 y +0,76 pp) y PCA (+0,23 y +0,41 pp) la superan. OCSVM queda igual con α = 0,03 (2,99 %) y la supera en +0,07 pp con α = 0,05. El compromiso observado con α = 0,03, frente al IF:
   - PCA: +17 TP a cambio de +393 FP.
   - LOF: +23 TP a cambio de +591 FP.
   - OCSVM: +5 TP a cambio de +235 FP.
3. **Las detecciones están anidadas.**
   - Los 54 ataques que detecta el IF también los detectan OCSVM, LOF y PCA. Los 44 (y 48) de EE también los detectan todos los demás.
   - El IF no detecta ningún ataque en exclusiva. OCSVM detecta 2 (α = 0,03) y LOF 6 (α = 0,03) que no detecta nadie más.
   - Ningún método detecta 5 ataques con α = 0,03, ni 4 con α = 0,05.
4. **LOF: ROC-AUC alta y AP mínima.** 97 ventanas normales puntúan por encima del ataque más alto. Las ventanas sin paquetes llegan a 3,5·10¹⁰ por la densidad local degenerada que provocan los duplicados. 1 079 de sus 2 314 FP (α = 0,03) son ventanas sin paquetes, frente a 34 del IF, 342 de PCA, 358 de OCSVM y 0 de EE. En operación, LOF además guarda las 203 967 ventanas y su inferencia es unas 10–15 veces más lenta que la del IF, aun usando todos los hilos frente a uno solo del IF.
5. **OCSVM: AP alta y ROC-AUC baja.** Los ataques que mejor puntúa están muy arriba, pero el ataque peor puntuado queda por debajo de 64 441 de las 65 421 normales. Su entrenamiento es el más caro: unos 10–12 min.
6. **Elliptic Envelope** solo funciona con la desviación D1 y tiene la covarianza degenerada. Es el método con menor recall.
7. **Tiempos indicativos.** Se tomaron en un Intel Core Ultra 7 155U (14 hilos, 31,5 GB, Windows 11, Python 3.14.3, scikit-learn 1.9.1), con `time.perf_counter`, una ejecución por método. La inferencia cubre las 131 058 ventanas.

   | Método | Ajuste (s) | Inferencia (s) |
   |---|---|---|
   | PCA | 0,2–0,3 | < 0,1 |
   | Elliptic Envelope | 17–18 | < 0,1 |
   | LOF (`n_jobs=-1`) | 62–71 | 44–55 |
   | OCSVM (un hilo) | 586–746 | 136–147 |
   | IF | congelado, no se entrenó aquí | 3,1–4,4 (volver a puntuar, un hilo) |

   Los rangos reflejan ejecuciones repetidas. La última del OCSVM coincidió en parte con las pruebas del repo del producto, y la primera con consolidaciones ligeras. No son tiempos del sensor ni de operación.

## 5. Alcance que se debe declarar

- **α = 0,03 del IF** se eligió **después** de examinar este conjunto de evaluación, en la calibración del 24-oct. Aquí se aplica el mismo α a todos los métodos, pero la elección no es ciega.
- **No es una prueba ciega:** la prueba normal y los 84 ataques ya se habían usado antes. Esta comparación no es una prueba independiente.
- **Alcance de los resultados:** valen solo para **estas configuraciones** (una por método, fijada de antemano y sin búsqueda) y **estos datos**. Con solo 84 ataques, diferencias de pocos TP no son robustas.
- **Unidad de evaluación:** **por ventana**, no por episodio.
- **Fuera de alcance:** **no** se evalúan los heurísticos, el híbrido, Suricata ni la aplicación de respuestas (LIMIT/BLOCK).
- **Ventanas sin paquetes:** como se conservan, la FPR offline no es la operativa. La prueba normal mantiene además las 74 ventanas de 10.10.20.30.

## 6. Documentos que esta comparación supera (no se borran: están en manifiestos con hash)

- `../../F5-tabla-comparacion-7-modelos.md` y la Tabla 7 de `../_campana/resultados-2026-10-23/eval41/v2/` comparan **7 candidatos históricos congelados**: variantes del IF, el modelo contaminado y un OCSVM entrenado con datos de **laboratorio**. Ese OCSVM no es el OCSVM de aquí, entrenado con los mismos datos del sensor. Para el artículo, la comparación entre algoritmos es esta.
- `../calibracion-alfa-2026-10-24/NOTA-CALIBRACION-ALFA.md` dice que las demás filas de la Tabla 7 «no se recalibraron». Queda resuelto aquí: los cinco métodos se calibran con el mismo criterio sobre las 65 553 ventanas.
- Respuesta a las observaciones: la versión vigente es `RESPUESTA-OBSERVACIONES-validacion-interna.xlsx`. La versión `…-CyberFlow.xlsx` es la anterior; se mantiene porque la cita un manifiesto.

## 7. Propuesta concisa para continuar 4.1 (insumo, no texto del manuscrito)

> Para situar el IF, se entrenaron con las mismas 203 967 ventanas normales, las mismas 28 variables escaladas y el mismo criterio de umbral (cuantil 1−α sobre 65 553 ventanas de validación) cuatro detectores de enfoque distinto: OCSVM, LOF, Elliptic Envelope y PCA por error de reconstrucción (Tabla 7). PCA, LOF y OCSVM detectan más ventanas de ataque que el IF, a costa de más falsas alarmas. El IF obtiene la menor FPR de prueba con ambos α (2,63 % y 4,52 %), con la detección incluida en la de esos tres métodos. La comparación es por ventana, reutiliza el conjunto de evaluación y usa una configuración fija por método.

## 8. Pendientes

1. **Prueba independiente:** tráfico normal nuevo y una campaña de ataques nueva, no usados antes, para confirmar el orden entre métodos sin selección posterior.
2. **Evaluación por episodio** y con N ≥ 3 por familia.
3. **Repetir la comparación excluyendo las ventanas sin paquetes**, declarándolo **antes** de mirar los resultados. Aquí solo se describe su efecto en los FP.
4. **Normalidad de las 74 ventanas de 10.10.20.30** en la prueba: confirmarla o reportar las métricas con y sin ellas, también como criterio previo.
5. **Incertidumbre:** intervalos (Wilson o bootstrap) y pruebas pareadas (McNemar sobre los 84 ataques) entre métodos. No se calcularon aquí.
6. **Sensibilidad a hiperparámetros** (`nu` y `gamma` de OCSVM, k de LOF, umbral de varianza de PCA): no se exploró. Requiere datos etiquetados distintos de la prueba.
7. **Elliptic Envelope:** cualquier variante (quitar constantes, otra `support_fraction`) sería un análisis nuevo, declarado como tal.
8. **Tiempos en el sensor** con el hardware de operación, si se van a citar como coste operativo.
9. **Bibliografía:** pendientes P1–P4 de `REFERENCIAS-VERIFICADAS.md`.
10. **Artículo:** sustituir la Tabla 7 antigua de 7 candidatos y su texto. Se hará en la redacción, por separado.
