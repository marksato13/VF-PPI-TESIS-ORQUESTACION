# Tabla 6 - IF limpio `if_limpio_2026_10` (umbral score_samples < -0,5693969936322356)

Clase positiva = ataque (84 ventanas Kali, nota M) vs 65 421 normales (oro=test). **Anomalia estadistica, no ataque confirmado por paquete.** Sumas verificadas: TP+FN=84, TN+FP=65421, total=65505.

| Indicador | Valor | Numerador/denominador |
|---|---|---|
| TP | 54 | ventanas de ataque detectadas / 84 |
| FP | 2961 | ventanas normales marcadas / 65 421 |
| TN | 62460 | - / 65 421 |
| FN | 30 | - / 84 |
| Precision | 0.0179 (1.79 %) | TP/(TP+FP) = 54/3015 |
| Recall (TPR) | 0.6429 (64.29 %) | TP/(TP+FN) = 54/84 |
| F1 | 0.0348 | 2PR/(P+R) |
| FPR | 0.0453 (4.53 %) | FP/(FP+TN) = 2961/65421 |
| Especificidad | 0.9547 (95.47 %) | TN/(TN+FP) |
| ROC-AUC | 0.9247 | ranking (anomalia = -score_samples) |
| Average Precision (AP) | 0.1858 | sklearn average_precision_score |

## Deteccion por familia (etiqueta PROXY observable de nota M; no ground-truth)

| Familia | Ventanas | Detectadas | TPR |
|---|---:|---:|---:|
| HTTP | 43 | 35 | 81.40 % |
| escaneo | 33 | 19 | 57.58 % |
| DNS | 8 | 0 | 0.00 % |
| **Total** | **84** | **54** | **64,29 %** |