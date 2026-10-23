# Sustituciones exactas del Word — cierre descriptivo 4.1

No se editó el archivo fuente ni se afirma haber recibido un adjunto nuevo. Se identifican los archivos disponibles que fueron revisados.

- Word: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\Articulo-IJIES-espanol_MARK_4.1-revisado.docx`
- SHA-256: `3f83c6d9136aedc4bd6ff44b7a154895b3dafe62d008a8e24077c78d36297edc`
- Excel: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\RESPUESTA-OBSERVACIONES-validacion-interna-CyberFlow.xlsx`
- SHA-256: `cba8c160f3a93fef983f250df281ad2df9c4d0df0b8ede02a7329a50754d64eb`

Las citas son texto de párrafo extraído del Word (las ecuaciones OMML pueden no aparecer en el texto plano). Al aplicar: sustituir únicamente el párrafo indicado, conservando su estilo y las ecuaciones adyacentes.

## 3.3.3: composición de validación

**Texto actual exacto:**

El subconjunto de entrenamiento se emplea para ajustar el escalador y el Isolation Forest; el de validación para calibrar el umbral de anomalía; y el de prueba para estimar la tasa de falsos positivos sobre tráfico normal. La validación contiene 65 633 ventanas normales, incluidas 80 ventanas de la entidad Kali, de las cuales 17 presentan actividad observable. No se encontró evidencia independiente que permita confirmar que esas 17 ventanas sean ataques; por tanto, su normalidad no está verificada. La Tabla 3 presenta la composición de la base y su distribución final.

**Sustituir por:**

El subconjunto de entrenamiento se emplea para ajustar el escalador y el Isolation Forest; el de validación, para calibrar el umbral; y el de prueba, para estimar falsos positivos. La validación contiene 65 633 ventanas nominalmente normales, incluidas 80 de la entidad Kali, 17 con actividad observable. No se confirmó independientemente su condición de ataque o normalidad; la pertenencia a Kali no basta para etiquetarlas como ataques. La Tabla 3 presenta la distribución utilizada.

## 3.3.3: separación de fuentes

**Texto actual exacto:**

Los datos de ataque se mantienen separados del ajuste del escalador, del entrenamiento del Isolation Forest y de la calibración del umbral. Se utilizan para evaluar inicialmente la capacidad de detección del IF y, posteriormente, comparar su desempeño con el de los heurísticos y el detector combinado. Los escenarios y las condiciones experimentales se detallan en la sección 3.6.

**Sustituir por:**

Las 84 ventanas etiquetadas como ataque de la evaluación no se utilizaron para ajustar el escalador, entrenar el IF limpio ni calcular su umbral. Esto no implica que toda la validación tenga normalidad confirmada: contiene las 80 ventanas de Kali descritas anteriormente. La evaluación se reutilizó durante el desarrollo y no constituye un test ciego nuevo.

## 3.3.4: StandardScaler

**Texto actual exacto:**

Las 28 características se organizan en matrices numéricas, conservando el mismo orden en entrenamiento, validación y prueba. Se aplica StandardScaler utilizando la media y la desviación estándar calculadas exclusivamente con las 203 967 observaciones normales de entrenamiento. La transformación se define como, Eq. (2):

**Sustituir por:**

Las 28 características se organizan en matrices numéricas con el mismo orden en entrenamiento, validación y prueba. El Pipeline evaluado conserva StandardScaler e Isolation Forest; el escalador se ajustó únicamente con las 203 967 observaciones de entrenamiento. Se describe como componente de la configuración congelada, no como requisito teórico de IF ni como una ventaja demostrada frente a una versión sin escalado. La transformación se define en la Eq. (2).

## 3.3.5: calibración

**Texto actual exacto:**

El modelo ajustado puntúa las 65 633 observaciones normales de validación, transformadas con el escalador obtenido en entrenamiento. Se adopta α = 0,05 como criterio de calibración y se establece el umbral en el percentil 5 de las puntuaciones, Eq. (3). La validación incluye 80 ventanas de Kali, 17 con actividad observable, sin confirmación independiente de que correspondan a ataques.

**Sustituir por:**

El IF limpio puntúa las 65 633 ventanas de validación, transformadas con el escalador de entrenamiento. La configuración congelada usa α = 0,05 y el percentil 5 de los scores para obtener el umbral. La validación incluye 80 ventanas de Kali, 17 con actividad observable, sin confirmación independiente de su condición de ataque o normalidad. El procedimiento del cuantil se expresa en la Eq. (3).

## 3.3.5: evitar justificación retrospectiva

**Texto actual exacto:**

Donde θ es el umbral; qα es el cuantil de orden α; sᵢ es la puntuación de normalidad asignada por el IF a la observación estandarizada i; i es su índice y n el número de observaciones de validación. Este criterio sitúa aproximadamente el 5% de las observaciones normales de validación por debajo del corte, sin utilizar datos de prueba ni etiquetas de ataque para seleccionarlo. La composición de validación contiene actividad de Kali cuya normalidad no está verificada, por lo que α = 0,05 reproduce el criterio operativo, pero no prueba una tasa futura ni un óptimo.

**Sustituir por:**

Donde θ es el umbral, qα el cuantil de orden α, sᵢ el score de normalidad de la observación estandarizada i y n el número de ventanas de validación. El corte se calcula con validación; α = 0,05 se conserva como configuración operativa congelada. No se presenta como óptimo ni como respuesta a una meta de aceptación fijada de antemano que no quedó documentada. La sensibilidad posterior es descriptiva y no selecciona un nuevo corte.

## 3.3.5: precisión completa del corte

**Texto actual exacto:**

El percentil 5 produce un umbral de −0,069397 en la función de decisión del IF. Con la configuración automática del parámetro de contaminación, este valor equivale a −0,569397 en la escala de puntuación de normalidad, mediante la resta de 0,5. Ambas escalas generan la misma clasificación; la conversión corresponde al desplazamiento de salida del modelo y no a la estandarización de las características. Eq (4),

**Sustituir por:**

El percentil 5 de validación produce θ = −0,5693969936322356 en la escala score_samples. La regla es score_samples < θ. Con offset_ = −0,5 equivale a −0,06939699363223562 en decision_function; ambas escalas conservan la clasificación. Esta conversión corresponde al desplazamiento de salida del IF, no al escalado de características. La Eq. (4) relaciona ambas escalas.

## 3.3.6: ventanas sin paquetes

**Texto actual exacto:**

La integración conserva la puntuación y el umbral del IF y registra el origen de las señales para evaluar cada componente por separado.

**Sustituir por:**

La integración conserva el umbral congelado y registra el origen de cada señal. En el motor en vivo, sin paquetes recientes se omite el IF, pero todavía pueden activarse reglas sobre información retrospectiva. Por tanto, una ventana sin paquetes recientes no implica automáticamente PERMIT. En la evaluación offline de 4.1 se puntúan todas las ventanas; sus resultados no equivalen a los del motor con heurísticos.

## 3.3.7: unidad y alcance

**Texto actual exacto:**

La evaluación mantiene fijos el escalador, el IF y el umbral calibrado. Se utilizan las 65 421 observaciones de prueba normal y 84 ventanas etiquetadas como actividad de ataque para estimar el desempeño. La evaluación es reutilizada: el conjunto ya participó en decisiones de desarrollo y no constituye un test ciego independiente. La unidad primaria es la ventana temporal de 10 s; la cobertura por episodio se presenta por separado. Se comparan el IF, los heurísticos y su combinación sobre los mismos datos de cada ensayo, mediante Eq. (7).

**Sustituir por:**

La evaluación de 4.1 mantiene fijos el escalador, el IF limpio if_limpio_2026_10 y el umbral −0,5693969936322356. Comprende 65 421 ventanas normales de prueba y 84 etiquetadas como ataque, para 65 505 observaciones. La unidad primaria es la ventana de 10 s por entidad. El conjunto se reutilizó durante el desarrollo, por lo que no es un test ciego nuevo. Estos resultados corresponden al IF offline; la comparación con heurísticos y el híbrido se reporta separadamente.

## 3.3.7: interpretación de métricas

**Texto actual exacto:**

Donde  son los ataques detectados;  los ataques no detectados;  las observaciones normales señaladas como anómalas y  las normales correctamente identificadas. Se distingue la detección por ventana de la cobertura por episodio y se declara el denominador de cada resultado. Para el IF también se calcula ROC-AUC utilizando el negativo de su puntuación de normalidad, de modo que los valores mayores representen mayor anomalía.

**Sustituir por:**

TP y FN cuentan ventanas etiquetadas como ataque detectadas y no detectadas; FP y TN cuentan ventanas normales marcadas y no marcadas. Recall = TP/(TP+FN) y precisión = TP/(TP+FP). Se reportan también F1, FPR, ROC-AUC y AP. Las métricas de ranking usan −score_samples; AP se calcula con average_precision_score, no con integración trapezoidal. La cobertura por episodio utiliza otro denominador y se presenta por separado.

## 3.6: familias aproximadas

**Texto actual exacto:**

La evaluación distingue el desempeño del detector y la aplicación de la respuesta. Cada ensayo registra el escenario, origen, destino, periodo de ejecución, capturas y decisiones generadas. Las comparaciones utilizan los mismos datos por ensayo y conservan la identificación del modelo, umbral y versión de los heurísticos.

**Sustituir por:**

La evaluación distingue el IF offline, el detector combinado y la aplicación de respuestas. En 4.1 las etiquetas por familia son aproximadas: HTTP identifica actividad HTTP observable y DNS actividad DNS observable; la categoría residual sin HTTP/DNS se guardó históricamente como «escaneo». Ese criterio de descarte no confirma un escaneo y no se utiliza como ground truth de familia. Cada resultado conserva el modelo, umbral, unidad de análisis y denominador.

## Tabla 3

Conservar los recuentos: 337 799 antes de guarda; 2 778 descartadas; entrenamiento 203 967; validación 65 633; prueba 65 421; total 335 021.

**Celda actual (Validación / Propósito):** Calibrar el umbral; incluye 80 ventanas Kali, 17 con actividad observable y normalidad no verificada

**Sustituir por:** Calibrar el umbral con 65 633 ventanas nominalmente normales; incluye 80 de Kali, 17 con actividad observable, sin confirmación independiente de ataque o normalidad.

## Tabla 5 — fila «Detección del IF»

- Columna 1, actual: Detección del IF
  - Sustituir por: Evaluación del IF limpio offline
- Columna 2, actual: Ventanas de actividad etiquetadas por familia proxy observable
  - Sustituir por: 65 421 ventanas normales y 84 etiquetadas como ataque; familias proxy
- Columna 3, actual: 65 505 ventanas; evaluación reutilizada, no test ciego independiente
  - Sustituir por: 65 505 ventanas de 10 s por entidad; conjunto reutilizado, no test ciego nuevo
- Columna 4, actual: Precisión, recall, F1, FPR, ROC-AUC y AP
  - Sustituir por: Precisión, recall, F1, FPR, ROC-AUC y AP (average_precision_score)

**Nota exacta para añadir bajo Tabla 5:** Los resultados de 4.1 corresponden únicamente al IF offline. Las familias son etiquetas proxy: la categoría residual sin HTTP/DNS no confirma escaneo. Las filas de comparación híbrida y respuesta tienen protocolos y denominadores propios; no heredan las métricas de 4.1.

## Tabla 6 y pie de figura

Presentar F1 = 0,03485; ROC-AUC = 0,92473; AP = 0,18581 (solo aumenta la precisión de presentación, sin cambiar el valor almacenado).

**Pie propuesto:** Figura 4. (a) ROC y (b) precisión-recall escalonada del IF limpio actual y las configuraciones de comparación, sobre 65 505 ventanas. Ranking con −score_samples y precisión completa; diagonal ROC y prevalencia PR = 84/65 505. AP se calcula con average_precision_score. IF uniform e IF exact tienen scores idénticos. La evaluación es reutilizada y describe el IF offline, no el híbrido.

## Excel: trazabilidad, sin modificar respuestas históricas

- CF-VI-02 — Uso de StandardScaler (estado registrado: En propuesta).
- CF-VI-05 — Comparación de modelos (estado registrado: En propuesta).
- CF-VI-06 — Justificación de alpha = 0,05 (estado registrado: En propuesta).
- CF-VI-07 — Deduplicación (estado registrado: En propuesta).
- CF-VI-11 — PERMIT / LIMIT / BLOCK (estado registrado: En propuesta).

La evidencia de transferencia y α no demuestra una ablación escalado/sin escalado ni valida retrospectivamente una meta de riesgo previa. No cambiar las respuestas de sesión como si esa evidencia hubiera existido entonces. F7 no se cierra con el mero cambio de nombre de la categoría residual.
