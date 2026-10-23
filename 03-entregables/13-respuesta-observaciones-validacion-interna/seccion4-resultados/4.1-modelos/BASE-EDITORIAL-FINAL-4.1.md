# Base editorial final — evaluación descriptiva 4.1

## Resultado (texto utilizable)

Se evaluó el IF limpio `if_limpio_2026_10`, con escalador, modelo y umbral congelados, sobre 65 505 ventanas de 10 s por entidad: 65 421 normales de prueba y 84 etiquetadas como ataque. La calibración utilizó 65 633 ventanas de validación y fijó la regla `score_samples < −0,5693969936322356`, con α = 0,05. La validación incluye 80 ventanas de Kali, 17 con actividad observable; no se confirmó independientemente su condición de ataque o normalidad. No se las clasifica como ataques por pertenecer a Kali. El conjunto evaluado se reutilizó durante el desarrollo y no constituye un test ciego nuevo.

| Indicador | Resultado | Definición |
|---|---:|---|
| TP | 54 | Ventanas etiquetadas como ataque marcadas por el IF |
| FP | 2 961 | Ventanas normales marcadas por el IF |
| TN | 62 460 | Ventanas normales no marcadas |
| FN | 30 | Ventanas etiquetadas como ataque no marcadas |
| Precisión | 1,79 % | 54 / (54 + 2 961) |
| Recall | 64,29 % | 54 / 84 |
| F1 | 0,03485 | 2TP / (2TP + FP + FN) |
| FPR | 4,53 % | 2 961 / 65 421 |
| ROC-AUC | 0,92473 | Ranking por −score_samples |
| AP | 0,18581 | `average_precision_score`, sin integración trapezoidal |

Los valores son redondeos de los números de precisión completa de `eval41/v2/metricas.json`. No se modificó ningún score, umbral ni recuento. Las tablas 6 y 7 se contrastaron contra las nueve series de scores; IF uniform e IF exact son idénticos: nueve filas, ocho configuraciones distintas.

## Interpretación breve

**Recall y precisión responden preguntas distintas.** El recall pregunta qué fracción de las ventanas etiquetadas como ataque fue detectada: 54 de 84 (64,29 %). La precisión pregunta qué fracción de las ventanas marcadas corresponde a esa etiqueta: 54 de 3 015 (1,79 %). De las ventanas marcadas, 2 961 son falsas alarmas respecto del etiquetado utilizado, aproximadamente el 98,21 %. Detectar una parte importante de las positivas no implica que la mayoría de las alarmas sea correcta.

**Costo de falsas alarmas.** La prevalencia de 84/65 505 = 0,128 % explica por qué un FPR de 4,53 % puede coexistir con precisión baja, pero no reduce el costo de las 2 961 falsas alarmas. Estas pueden exigir revisión y, en un sistema que derive una respuesta, afectar tráfico legítimo. Que una señal del IF se traduzca a LIMIT reversible no demuestra que sea inocua. Esta evaluación no mide ese costo operativo ni el efecto completo del enforcement.

**Composición del conjunto.** Como análisis complementario, 19 863 ventanas normales tuvieron paquetes recientes y acumularon 2 837 FP (14,28 %). Las 12 208 sin paquetes recientes pero con actividad retrospectiva tuvieron 124 FP (1,02 %); las 33 350 restantes, sin actividad en los contadores revisados, tuvieron 0 FP. Los recuentos suman 65 421 ventanas y 2 961 FP. El 14,28 % no reemplaza el 4,53 % global: explica su dependencia de la composición y no debe omitirse al interpretar el conjunto.

**Transferencia entre configuraciones.** Los candidatos del laboratorio y los modelos ajustados en esta red tienen distinto origen de entrenamiento. La Tabla 7 describe su transferencia a esta evaluación, no superioridad intrínseca de Isolation Forest. IF limpio y anterior detectaron ambos 54/84, pero el limpio tiene ROC-AUC 0,92473 frente a 0,92283, mientras el anterior tiene AP 0,20263 frente a 0,18581 y FPR 4,45 % frente a 4,53 %. La coincidencia de recall no demuestra equivalencia estadística ni superioridad general del limpio.

**Configuración congelada.** α = 0,05 se conserva porque es la configuración evaluada. Su análisis de sensibilidad describe el compromiso recall/FPR con cortes calculados en validación; no identifica un óptimo ni justifica retrospectivamente decisiones previas o metas de aceptación no documentadas. StandardScaler se describe como parte del Pipeline congelado, no como una necesidad teórica de IF ni como una ablación con/sin escalado que no se ejecutó.

## Alcance que debe declararse

- Esta sección mide **IF offline**, puntuando todas las ventanas. No atribuir estos resultados al híbrido.
- En el motor con heurísticos, sin paquetes recientes se omite el IF, pero aún pueden activarse reglas retrospectivas. Ausencia de paquetes recientes no significa automáticamente PERMIT.
- Las etiquetas de familia son aproximadas. El código asigna HTTP si hay solicitudes HTTP, luego DNS si hay consultas DNS y, por descarte, la clave histórica `escaneo`. Esa última categoría es **residual sin HTTP/DNS, no escaneo confirmado**. Se conservan sus recuentos (33 ventanas, 19 detectadas) y las claves históricas en los archivos de datos para trazabilidad.
- La reutilización del conjunto limita inferencias confirmatorias. No impide redactar esta evaluación descriptiva; un nuevo test independiente y la generalización a otras redes no son condiciones de cierre de estos ajustes.

## Figura y trazabilidad

Figura definitiva: `eval41/v2/figura-roc-pr-v2.{png,svg,pdf}`. Panel (a) ROC con diagonal de referencia; panel (b) PR escalonada `steps-post` con prevalencia real. Se usan todos los umbrales de los scores de precisión completa, sin selección ni suavizado. IF limpio destacado por grosor y leyenda; tamaño diseñado de 7,2 pulgadas de ancho (~183 mm), tipografía de leyenda 8,5 pt, PNG a 600 DPI. AP procede de `average_precision_score`; la suma de incrementos de recall por precisión coincide numéricamente con AP y se usa solo como comprobación.

`COMPROBACION-METRICAS-4.1.json` confirma métricas y tablas. `MANIFIESTO-4.1-CANONICO.json` contiene hashes de bytes finales; `VERIFICACION-GITHUB-4.1.json` registra la comprobación por descarga HTTP de un commit fijo, sin normalizar los bytes recibidos. El informe de verificación no se incluye en su propio manifiesto para evitar una referencia circular.

## Ajustes resueltos y condiciones declaradas

**Resueltos:** representación PR escalonada; legibilidad a ancho de publicación indicado; cálculo AP correcto; confirmación de tablas; serialización UTF-8/LF; hashes de figuras y textos finales; propuestas exactas para el Word disponible. La integridad remota solo se considera resuelta si el informe descargado registra cero discrepancias.

**Se declaran, no se fabrican soluciones:** incertidumbre de las ventanas de Kali; familias proxy y residual no confirmado; evaluación reutilizada; FPR dependiente de composición; costo de falsas alarmas; origen distinto de entrenamiento; ausencia de óptimo demostrado o equivalencia estadística. Ninguna requiere repetir campañas, reentrenar o cambiar el despliegue para esta redacción descriptiva.
