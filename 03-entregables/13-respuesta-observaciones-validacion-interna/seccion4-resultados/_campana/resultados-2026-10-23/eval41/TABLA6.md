# Tabla 6 - IF limpio sobre oro (65421 normal) + 84 ataque

| TP | FP | TN | FN | Precision | Recall | F1 | FPR | ROC-AUC | AP |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 54 | 2961 | 62460 | 30 | 0.0179 | 0.6429 | 0.0348 | 0.0453 | 0.9247 | 0.1858 |

AP = average_precision_score (area PR por suma ponderada de recalls, sklearn). Clase positiva = anomalia; score = -score_samples.