# Tabla 6 - IF limpio `if_limpio_2026_10` (umbral score_samples < -0,5693969936322356)

Clase positiva = 84 ventanas etiquetadas como ataque (nota M) vs 65 421 normales (oro=test). **Anomalia estadistica, no ataque confirmado por paquete.** Sumas verificadas: TP+FN=84, TN+FP=65421, total=65505.

| Indicador | Valor | Numerador/denominador |
|---|---|---|
| TP | 54 | ventanas etiquetadas como ataque detectadas / 84 |
| FP | 2961 | ventanas normales marcadas / 65 421 |
| TN | 62460 | - / 65 421 |
| FN | 30 | - / 84 |
| Precision | 0.0179 (1.79 %) | TP/(TP+FP) = 54/3015 |
| Recall (TPR) | 0.6429 (64.29 %) | TP/(TP+FN) = 54/84 |
| F1 | 0.03485 | 2PR/(P+R) |
| FPR | 0.0453 (4.53 %) | FP/(FP+TN) = 2961/65421 |
| Especificidad | 0.9547 (95.47 %) | TN/(TN+FP) |
| ROC-AUC | 0.92473 | ranking (anomalia = -score_samples) |
| Average Precision (AP) | 0.18581 | sklearn average_precision_score |

## Deteccion por familia (etiqueta PROXY observable de nota M; no ground-truth)

| Familia | Ventanas | Detectadas | TPR |
|---|---:|---:|---:|
| HTTP | 43 | 35 | 81.40 % |
| Residual sin HTTP/DNS (antes «escaneo») | 33 | 19 | 57.58 % |
| DNS | 8 | 0 | 0.00 % |
| **Total** | **84** | **54** | **64,29 %** |
La categoría residual se asignó por ausencia de HTTP/DNS; no confirma escaneo. Las claves históricas de metricas.json y del CSV de scores se conservan como trazabilidad, sin convertirlas en ground truth.
