# Base editorial para la sección 4.1

Fecha de cierre: 2026-10-23. Este documento no sustituye la sección 4 del Word; sirve como base verificable para redactarla sin inventar resultados.

## A. Presentación de la evaluación

Se evaluó el modelo operativo `if_limpio_2026_10`, un Pipeline congelado con escalador, Isolation Forest y umbral `score_samples < -0,5693969936322356`. La unidad de análisis es la ventana temporal de 10 s por entidad, no el episodio. El conjunto evaluado contiene 65 421 ventanas normales de prueba y 84 ventanas etiquetadas como ataque, para 65 505 observaciones. La evaluación es reutilizada: el conjunto ya participó en decisiones de desarrollo el 14/10/2026 y no constituye un test ciego independiente.

La calibración se realizó sobre 65 633 ventanas de validación. Este conjunto incluye 80 ventanas de la entidad Kali, 17 con actividad observable. No se encontró evidencia independiente que permita confirmar que esas 17 ventanas correspondan a ataques; se conservan como parte de la calibración operativa, pero su normalidad no está verificada.

## B. Tabla 6: IF limpio

| Indicador | Valor |
|---|---:|
| TP | 54 |
| FP | 2961 |
| TN | 62460 |
| FN | 30 |
| Precisión | 1.7910% |
| Recall | 64.2857% |
| F1 | 0.0348 |
| FPR | 4.5261% |
| ROC-AUC | 0.9247 |
| AP | 0.1858 |

## C. Interpretación

El IF detectó 54 de 84 ventanas etiquetadas como ataque y produjo 2 961 falsas alarmas sobre 65 421 ventanas normales. La precisión fue 54/(54+2 961) = 1,79 %. La baja precisión no debe ocultarse: la prevalencia fue 84/65 505 = 0,128 %, por lo que un FPR de 4,53 % genera muchas más alarmas normales que verdaderos positivos. ROC-AUC mide la capacidad de ordenar observaciones normales y anómalas; no garantiza que el umbral operativo tenga buena precisión. Aunque el sistema traduzca una señal aislada del IF a LIMIT reversible, LIMIT también puede afectar tráfico legítimo y su costo no se resuelve con la métrica de ranking.

## D. Tabla 7: configuraciones

La comparación usa las mismas 65 505 ventanas y el umbral propio de cada configuración. Los candidatos de laboratorio y los modelos entrenados con datos de esta red tienen distinto origen; por tanto, el resultado mide transferencia al entorno objetivo, no superioridad intrínseca de Isolation Forest. IF limpio y IF contaminado detectaron ambos 54/84, pero difirieron en FP, ROC-AUC y AP. No se afirma equivalencia estadística ni superioridad. IF uniform e IF exact son variantes idénticas y deben presentarse como una única configuración con duplicación documentada.

## E. Figura ROC/PR

La figura muestra el comportamiento de ranking de las nueve configuraciones usando los scores de precisión completa. El panel (a) resume ROC-AUC y el panel (b) muestra precisión frente a recall con la prevalencia real de 0,128 % como referencia. La figura no reemplaza la decisión en el umbral congelado: una curva favorable puede coexistir con una precisión operativa baja.

## F. Sensibilidad y ventanas sin actividad

Los cortes de sensibilidad se calcularon sobre la validación original de 65 633 y se aplicaron a test; alpha = 0,05 reproduce el umbral operativo y no se presenta como óptimo. Al reducir alpha disminuyen simultáneamente FPR y recall; al aumentarlo, el recall sube con un costo mayor en FPR. La validación sin Kali, de 65 553 ventanas, es únicamente complementaria.

En la auditoría del test normal, 19 863 ventanas tuvieron paquetes en los últimos 10 s y presentaron 2 837 FP, FPR 14,28 %. Otras 12 208 no tuvieron paquetes recientes pero sí actividad retrospectiva y presentaron 124 FP. Las 33 350 restantes no mostraron actividad en los contadores revisados y presentaron 0 FP. El 4,53 % global depende de esta composición. Offline, el evaluador puntúa todas las ventanas; en vivo, una ventana sin paquetes omite el IF, pero todavía puede pasar por la evaluación de heurísticos antes de determinar la acción final. Por ello los 124 FP no son directamente el FPR operativo del sistema completo.

## G. Limitaciones

- La evaluación está reutilizada y no es un test ciego independiente.
- Las 80 ventanas Kali dentro de validación incluyen actividad observable, pero no tienen confirmación independiente de ser ataques.
- Las familias de ataque son proxies observables; no deben presentarse como ground truth confirmado.
- La evaluación de 4.1 corresponde al IF solo; el híbrido pertenece a 4.2.
- Los resultados no se extrapolan automáticamente a otra red ni a IPv6.

## Matriz de afirmaciones

| Afirmación permitida | Evidencia | Limitación |
|---|---|---|
| IF limpio detecta 54/84 y obtiene FPR 4,53 % en esta evaluación. | Tabla 6 y `metricas.json`. | Evaluación reutilizada; FPR del IF offline, no del sistema completo. |
| La precisión es 1,79 % con 2 961 FP. | Matriz de confusión de Tabla 6. | Prevalencia 0,128 %; LIMIT no elimina el costo de falsos positivos. |
| Los candidatos de laboratorio transfieren mal a esta red. | Tabla 7: FPR de 29,07 % a 99,57 %. | No demuestra superioridad intrínseca de IF. |
| Alpha = 0,05 reproduce el umbral operativo. | `p1-reconciliacion.json` y `ALFA-F6.csv`. | No demuestra que sea óptimo; no hubo meta de aceptación previa más específica. |
| El FPR global depende de ventanas con y sin actividad reciente. | `p3-ventanas-cero.json`. | Offline y motor vivo no aplican exactamente la misma ruta de decisión. |

## Correcciones necesarias en el Word

1. Sustituir en el resumen y palabras clave `One-Class SVM` por `Isolation Forest` cuando describan el modelo operativo.
2. En 3.3.3, después de `Validación: 65 633`, añadir que incluye 80 ventanas de Kali, 17 con actividad observable, sin confirmarlas como ataques.
3. En 3.3.5, conservar que el umbral no usa test ni ataque para seleccionarse, pero añadir que la composición de validación contiene esas 80 ventanas de normalidad no verificada.
4. En 3.3.7 y Tabla 5, añadir que la evaluación de 65 505 ventanas es reutilizada y que la unidad primaria es la ventana; la cobertura por episodio pertenece al análisis complementario.
5. En 3.6 y Tabla 5, cambiar `ataques identificados por familia` por `ventanas de actividad etiquetadas por familia proxy observable`.
6. Insertar la Tabla 6, Tabla 7, la figura ROC/PR y este bloque de limitaciones en la sección 4.1, que todavía no aparece en el Word revisado.

## Estado

- VERIFICADO: hash, filas, scores completos, matrices y métricas.
- CORREGIDO: sensibilidad alpha, figura y manifiesto editorial.
- CONSERVADO: modelo, escalador, umbral y despliegue sin cambios.
- PENDIENTE: incorporar estos textos y tablas al Word; test ciego independiente; confirmación externa de familias; replay ET Open no pertenece a 4.1.
