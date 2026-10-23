# ¿Tiene α = 0,05 justificación empírica en CyberFlow?

## Conclusión ejecutiva

**Tiene una justificación metodológica original documentada como cola experimental del 5 % en validación y por continuidad del protocolo. No está demostrado que sea el mejor alfa ni el más estable para el IF limpio.** En este análisis posterior del test ya observado, α = 0,03 detecta exactamente las mismas 54 ventanas positivas que α = 0,05 con 1 236 falsos positivos menos (1 725 frente a 2 961). Por tanto, 0,05 está dominado respecto de TP/FP en esta rejilla y este conjunto. Esto justifica considerar 0,03 en una confirmación futura, **no cambiar ahora el despliegue ni presentar un nuevo alfa como validado independientemente**.

## 1. Evidencia original: qué estaba decidido y qué se midió

Los extractos íntegros, líneas, commits, fechas y hashes se conservan en `EVIDENCIA-ORIGINAL-ALFA.json`.

### 1.1 Elección original documentada

1. **Protocolo PM-F1-v1**, archivo `docs/fase04-modelado/01-protocolo-modelado-F1-v2.md`, sección «Regla de umbral R04», conservado en el producto en el commit `34e31cd` del **18-ago-2026**, anterior a la evaluación de la red real de septiembre. Declara literalmente: «El operating point principal se fija en alpha=0.05 de falsos positivos por ventana normal de validación. Es un objetivo experimental predeclarado, no un SLA de producción ni una garantía poblacional». Su encabezado declara congelamiento el 4-ago; el commit del 18-ago es la evidencia versionada aquí recuperada, no una certificación de que cada acción experimental ocurriera como se planificó.
2. **Hoja de ruta multilayer-v2**, en el mismo commit, declara que se mantiene α = 0,05 de PM-F1-v1 **por continuidad metodológica**. No es un resultado de comparar empíricamente diferentes alfas.
3. **Código preliminar del sensor**, `entrenar_preliminar.py` en `71a72d6` del **27-sep-2026**, ya contiene `--alpha`, valor por defecto `0.05`, descrito como «cola de validación que define el umbral (y FPR objetivo)». Calcula el cuantil con validación antes de calcular FPR en test. Es evidencia de la regla implementada previa al informe del 29-sep, no de una función de costos optimizada.
4. **Nota L**, informe del 29-sep: reporta 65 633 ventanas de validación y FPR test de 4,45 % para el **IF anterior**, con α = 0,05. Mide un resultado agregado, no estabilidad entre periodos ni comparación de alfas. La comparación 92,4 % → 4,45 % cambió modelo/datos/entorno; tampoco aísla el efecto de elegir α = 0,05.

**Qué sí y qué no:** hay objetivo experimental de cola del 5 % documentado antes de la evaluación real, y continuidad de esa elección. No se encontró un mínimo previo de detección, presupuesto operacional en alarmas/hora, capacidad de revisión, límite sobre ventanas activas ni costos FP/FN que distingan 0,05 de las alternativas. El protocolo inicial usaba un estadístico de orden, mientras el IF limpio usa cuantil NumPy lineal: la continuidad de α no implica identidad de todos los procedimientos o de los datasets.

La cronología versionada respalda que la regla existía antes del **informe** del test de la red real. No certifica por sí sola que ningún test se hubiera inspeccionado previamente, ni convierte el test reutilizado del IF limpio en independiente. Tampoco se interpreta la fecha declarada del encabezado como un registro externo de prerregistro.

### 1.2 De dónde sale «estable»

- En `84f3eb2` (**7-oct-2026**) se añadió a `F3-modelado-hibrido.md`: «además es estable (validación cruzada del umbral) y reproducible (determinismo con semillas)», dentro de la descripción del IF recalibrado. No adjunta una comparación de estabilidad entre distintos alfas.
- El experimento histórico que sí existe es `validacion_cruzada_estabilidad.py` y su JSON `validacion-cruzada-estabilidad.json`, referidos al **OCSVM de laboratorio**: 1 373 ventanas normales, 179 positivas, α fijado en 0,05. No es el IF limpio de esta red.
- **Cinco pliegues agrupados por episodio:** el script vuelve a ajustar el OCSVM por pliegue, manteniendo su configuración. El texto «no se reajusta» del informe debe entenderse como configuración no optimizada, porque el código sí ejecuta `fit` en cada pliegue. Se midieron umbral, FPR y detección. FPR medio **5,8277 %**, desviación muestral **3,2343 puntos porcentuales**; detección media **85,4749 %**, desviación **3,9700 puntos porcentuales**. Los pliegues reutilizan las mismas 179 positivas: no son cinco pruebas independientes de ataque.
- **1 000 remuestreos por episodio de validación:** se reportó variación del **umbral**, media **1,7852718945**, desviación **0,0731758865**, CV **4,098865 %**, intervalo percentil **[1,6496005791; 1,8131889308]**. El criterio CV < 5 % es otro porcentaje distinto de α = 5 %: no mide FPR. Tampoco compara alfas ni es evidencia de estabilidad temporal del desempeño.
- Se verificaron las medias, desviaciones, denominadores de los cinco pliegues y la identidad `CV = 100 × desviación / |media|` contra el JSON. No se reentrenó el OCSVM ni se reprodujeron los 1 000 bootstrap: no se conserva aquí su serie individual. La verificación es de consistencia aritmética y trazabilidad, no una nueva reproducción del ajuste.
- La frase posterior «knee razonable» aparece en `ESQUEMA-AFIRMACIONES-Y-CIERRE-4.1.md`, introducida en `d0b8e18` (23-oct). Se apoya en sensibilidad posterior sobre test ya observado; no define un criterio de curvatura, utilidad o aceptación previo. No basta para llamar 0,05 óptimo ni estable.

**Veredicto:** la evidencia histórica demuestra que hubo mediciones de variación de umbral y de resultados por pliegue para **otro modelo y otro dataset**, a un único α. **La mayor estabilidad de α = 0,05 respecto de otros alfas y la estabilidad del desempeño del IF limpio no están demostradas.** Mantener fijo el umbral y reproducir sus scores son propiedades de congelamiento/repetibilidad, no estabilidad del desempeño ante cambios de distribución.

## 2. Procedimiento del análisis posterior

- Modelo limpio congelado, SHA-256 `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60`.
- Cortes: `numpy.quantile(scores_validation, α, method="linear")`, **solo sobre las 65 633 ventanas originales de validación**. No se excluyen las 80 ventanas Kali; 17 tienen actividad observable y no tienen condición de ataque/normalidad confirmada independientemente.
- No había un vector completo de scores de validación entre los artefactos de evaluación inspeccionados. Se recuperó mediante **inferencia** del Pipeline limpio congelado sobre esa partición original, sin entrenamiento ni escritura remota; se conserva completo en `entradas-alfa-if-limpio.json.gz`, junto con metadatos para alinear el test. Los hashes del modelo, manifiesto y datasets originales están en la procedencia de esa exportación.
- Test: los **mismos scores completos conservados**, 65 421 normales y 84 etiquetadas como ataque; archivo SHA-256 `6e98219fb79a187b7256e664a4791a0619be70a68d9a23eee1e61c45de98ffc8`. No se recalcularon los scores de test ni se cargó otro modelo para ellos.
- Regla estricta: alerta si `score_samples < umbral`; empates no alertan. El corte de 0,05 reproduce exactamente **−0,5693969936322356** y TP 54, FN 30, FP 2 961, TN 62 460.
- Test y metadatos se emparejan por campaña, entidad, marca temporal y etiqueta, verificando unicidad e igualdad de las 65 505 claves. Cada positivo es una **ventana**, no un ataque/episodio independiente confirmado.
- El test ya fue observado: este análisis es exploratorio, sin declaración de selección confirmatoria.

## 3. Sensibilidad global

| Alfa | Umbral (score_samples) | TP | FN | FP | TN | Recall | FPR | Precisión | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0,005 | −0,6378394420989123 | 26 | 58 | 280 | 65 141 | 30,95 % | 0,43 % | 8,50 % | 0,13333 |
| 0,01 | −0,6223738394125686 | 50 | 34 | 567 | 64 854 | 59,52 % | 0,87 % | 8,10 % | 0,14265 |
| 0,02 | −0,6028234334119111 | 52 | 32 | 1 130 | 64 291 | 61,90 % | 1,73 % | 4,40 % | 0,08215 |
| 0,025 | −0,5952528323894616 | 53 | 31 | 1 423 | 63 998 | 63,10 % | 2,18 % | 3,59 % | 0,06795 |
| 0,03 | −0,5898052872761252 | 54 | 30 | 1 725 | 63 696 | 64,29 % | 2,64 % | 3,04 % | 0,05797 |
| 0,04 | −0,5800582408391518 | 54 | 30 | 2 301 | 63 120 | 64,29 % | 3,52 % | 2,29 % | 0,04428 |
| **0,05** | **−0,5693969936322356** | **54** | **30** | **2 961** | **62 460** | **64,29 %** | **4,53 %** | **1,79 %** | **0,03485** |
| 0,10 | −0,5369318991910549 | 59 | 25 | 6 107 | 59 314 | 70,24 % | 9,33 % | 0,96 % | 0,01888 |

La precisión no se confunde con recall: incluso los cortes restrictivos producen más FP que TP. La mayor F1 observada en esta rejilla corresponde a 0,01; eso no convierte F1 en un criterio original ni demuestra un óptimo operativo.

## 4. Intercambio entre cortes y alternativas dominadas

| Cambio | Ventanas positivas adicionales | FP adicionales | FP adicionales / positiva adicional |
|---|---:|---:|---:|
| 0,005 → 0,01 | 24 | 287 | 11,96 |
| 0,01 → 0,02 | 2 | 563 | 281,50 |
| 0,02 → 0,025 | 1 | 293 | 293,00 |
| 0,025 → 0,03 | 1 | 302 | 302,00 |
| 0,03 → 0,04 | 0 | 576 | No hay ganancia |
| 0,04 → 0,05 | 0 | 660 | No hay ganancia |
| 0,05 → 0,10 | 5 | 3 146 | 629,20 |

Una alternativa domina a otra si obtiene al menos tantos TP y como máximo tantos FP, con alguna mejora estricta. **0,03 domina a 0,04 y a 0,05; 0,04 también domina a 0,05.** No es solo igualdad del recuento: se verifican las mismas ventanas positivas detectadas. Los 1 236 FP evitables observados de 0,05 a 0,03 representan aproximadamente **41,74 %** de los FP de 0,05. Los demás puntos no están dominados bajo estos dos objetivos en la rejilla ensayada. Esto no prueba dominancia fuera de esta muestra ni de la rejilla.

Comparaciones con 0,05: bajar a 0,01 evita **2 394 FP** y deja de detectar **4 ventanas positivas**; subir a 0,10 detecta **5 positivas más** con **3 146 FP más**. No convertir estas cantidades en episodios o incidentes independientes.

## 5. Complementario: ventanas con paquetes recientes

Se filtra `packet_count_10s > 0`: **19 863 normales y las mismas 84 positivas** (todas ellas tienen paquetes recientes). Por eso recall no cambia, pero FPR, precisión y F1 sí. Este resultado condicionado no se mezcla con el global ni se presenta como FPR del híbrido.

| Alfa | FP en normales con paquetes | FPR condicionado | Recall |
|---:|---:|---:|---:|
| 0,005 | 280 | 1,41 % | 30,95 % |
| 0,01 | 564 | 2,84 % | 59,52 % |
| 0,02 | 1 118 | 5,63 % | 61,90 % |
| 0,025 | 1 399 | 7,04 % | 63,10 % |
| 0,03 | 1 691 | 8,51 % | 64,29 % |
| 0,04 | 2 225 | 11,20 % | 64,29 % |
| 0,05 | 2 837 | 14,28 % | 64,29 % |
| 0,10 | 5 614 | 28,26 % | 70,24 % |

La tabla complementaria completa (incluyendo TP/FN/TN/precisión/F1) se entrega por separado. El gráfico `recall-frente-fpr-alfa` usa panel (a) global y panel (b) condicionado, cada alfa identificado y 0,05 destacado sin alterar sus coordenadas.

### Variación temporal descriptiva nueva, no validación de estabilidad

Para no equiparar congelamiento con estabilidad se desagregó el mismo test por **día UTC** con el corte fijo de 0,05:

| Día UTC | Normales de test | FP | FPR global del día | Normales con paquetes | FP con paquetes | FPR condicionado |
|---|---:|---:|---:|---:|---:|---:|
| 27-sep | 19 285 | 337 | 1,75 % | 4 430 | 295 | 6,66 % |
| 28-sep | 21 089 | 1 252 | 5,94 % | 6 664 | 1 211 | 18,17 % |
| 29-sep | 25 047 | 1 372 | 5,48 % | 8 769 | 1 331 | 15,18 % |

Las 84 positivas están en el **30-sep**, sin normales de test ese día: no hay una serie de recall diario en varios días para demostrar estabilidad de detección. Los días tienen composición/exposición distinta y ventanas dependientes; no se tratan como réplicas intercambiables ni se decide significancia con tres días. Los FPR distintos muestran que el mismo umbral puede producir resultados distintos; no establecen por sí solos deriva, inestabilidad estadística ni que otro alfa sea más estable. `descriptivo-por-dia-utc.csv` conserva los ocho alfas y ambos grupos; FPR/recall sin denominador se dejan vacíos.

## 6. Prioridades y escenarios exclusivamente hipotéticos

No se encontraron costos operativos ni mínimos previos de detección. Por ello los siguientes escenarios son ilustraciones, **no el protocolo original**:

- Prioridad fuerte a reducir FP: 0,005 produce el mínimo FP de la rejilla (280), pero pierde 58/84 positivas. Con un límite hipotético de **FPR global ≤ 1 %** y preferencia por mayor recall dentro del límite, 0,01 sería la alternativa de esta rejilla.
- Con **FPR global ≤ 2 %**, 0,02 alcanza mayor recall entre las opciones admisibles. Ninguno de esos presupuestos controla el FPR condicionado a tráfico activo: por ejemplo 0,01 tiene 2,84 % condicionado.
- Prioridad a conservar al menos el recall observado de 0,05: 0,03 es el candidato con menos FP entre los que alcanzan 54/84. 0,04 y 0,05 no ofrecen mejora agregada de detección en esta muestra.
- Prioridad a **recall ≥ 70 %**: solo 0,10 lo alcanza entre los ocho cortes, con FPR 9,33 % global y 28,26 % condicionado. Eso puede ser inaceptable si la revisión o la afectación a tráfico legítimo es costosa.
- Para ilustrar prioridades continuas se calcula `L = C_FP × FP + C_FN × FN`, con C_FP = 1. Si C_FN es 1, 100, 290, 300, 400 o 1 000, las alternativas de menor costo observado en la rejilla son respectivamente **0,005; 0,01; 0,02; 0,025; 0,03; 0,10**. Los números son hipotéticos por ventana, dependientes de esta composición; no son costos medidos por incidente ni una estimación del costo del enforcement. Los 0,04 y 0,05 dominados no minimizan esta pérdida para costos FP/FN positivos.

**No se propone un «óptimo» por estar en el medio.** Antes de recomendar un cambio deben fijarse prioridades y denominadores operativos (por ejemplo alarmas por hora/entidad y afectación legítima), validar etiquetas y confirmarse el candidato en datos nuevos con periodos/escenarios representativos y criterio de aceptación previo. Para hablar de estabilidad hacen falta medidas repetidas comparables del IF limpio y de sus cortes, con dependencia temporal tratada explícitamente. El despliegue y su umbral se conservan.

## 7. Párrafos técnicos listos para el artículo

### Metodología: elección original y análisis posterior

El Pipeline Isolation Forest limpio se evaluó con α = 0,05 y umbral score_samples < −0,5693969936322356, conservados sin cambios. La elección de la cola del 5 % está documentada como objetivo experimental de validación y por continuidad metodológica; no se identificó una función de costos, un mínimo de detección o una comparación previa de alfas que demostrara optimalidad o mayor estabilidad. Como análisis exploratorio posterior, con el test ya observado, se calcularon ocho umbrales exclusivamente sobre las 65 633 ventanas originales de validación mediante cuantil lineal y se aplicaron a los scores de precisión completa de las mismas 65 421 ventanas normales y 84 etiquetadas como ataque. La validación conserva 80 ventanas de Kali, 17 con actividad observable y sin condición de ataque/normalidad confirmada independientemente. Se reportaron métricas globales y, por separado, el subconjunto con paquetes recientes. Este análisis no selecciona un nuevo alfa validado independientemente ni modifica el despliegue.

### Resultados: compromiso observado y límites

Con α = 0,05, el IF limpio detectó 54/84 ventanas etiquetadas como ataque y produjo 2 961 FP sobre 65 421 normales (recall 64,29 %, FPR 4,53 %, precisión 1,79 % y F1 0,03485). En el análisis exploratorio, α = 0,03 conservó exactamente esas 54 detecciones con 1 725 FP (FPR 2,64 %), por lo que dominó a 0,04 y 0,05 en TP/FP dentro de la rejilla y muestra observadas. Reducir α a 0,01 evitó 2 394 FP respecto de 0,05, a costa de cuatro ventanas positivas menos; aumentarlo a 0,10 añadió cinco detecciones y 3 146 FP. Entre las normales con paquetes recientes, el FPR de 0,05 fue 14,28 %, frente a 8,51 % para 0,03. Las cifras describen el IF offline, no el híbrido ni su costo operativo. La evidencia histórica de estabilidad corresponde al OCSVM de laboratorio, no demuestra mayor estabilidad de 0,05 para el IF limpio y no sustituye una confirmación posterior de cualquier cambio sobre datos nuevos.

## 8. Reproducción y alcance de la verificación

Ejecutar `python analizar_alfa.py` en esta carpeta con NumPy, Matplotlib, los dos repositorios locales y los dos archivos de scores conservados. No necesita acceso a las VMs una vez recuperadas las entradas. `recuperar_entradas.py` documenta el acceso original en solo lectura; no volver a ejecutarlo para reproducir las tablas.

Entradas, outputs, scripts y hashes se listan en `MANIFIESTO-ALFA.json`; `ARCHIVOS-ALFA.md` enumera rutas absolutas y enlaces de publicación. Los artefactos canónicos previos de 4.1, el modelo y el despliegue no se modifican. Las fuentes históricas se conservan como evidencia; este informe corrige su interpretación, no reescribe retrospectivamente sus decisiones.
