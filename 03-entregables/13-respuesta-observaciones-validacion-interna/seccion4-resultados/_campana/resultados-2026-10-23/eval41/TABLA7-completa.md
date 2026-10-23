# 4.1 (fleco 2) - Tabla 7 completa (cada modelo a su umbral propio; mismas 84+65421)

| Modelo | Entrenamiento | Precision | Recall | F1 | FPR | ROC-AUC | AP |
|---|---|---:|---:|---:|---:|---:|---:|
| IF limpio (desplegado) | esta red | 0.0179 | 0.6429 | 0.0348 | 0.0453 | 0.9247 | 0.1858 |
| IF recalibrado (contaminado) | esta red | 0.0182 | 0.6429 | 0.0354 | 0.0445 | 0.9228 | 0.2026 |
| IF scaled (lab) | laboratorio | 0.0039 | 0.9167 | 0.0077 | 0.3034 | 0.8250 | 0.0043 |
| IF primary (lab) | laboratorio | 0.0036 | 0.8214 | 0.0072 | 0.2907 | 0.8283 | 0.0044 |
| IF uniform (lab) | laboratorio | 0.0032 | 0.8571 | 0.0064 | 0.3413 | 0.7960 | 0.0054 |
| IF exact (lab) | laboratorio | 0.0032 | 0.8571 | 0.0064 | 0.3413 | 0.7960 | 0.0054 |
| OCSVM (lab) | laboratorio | 0.0013 | 1.0000 | 0.0026 | 0.9957 | 0.4555 | 0.0011 |
| LOF (lab) | laboratorio | 0.0012 | 0.7024 | 0.0023 | 0.7680 | 0.2991 | 0.0009 |
| Elliptic Envelope (lab) | laboratorio | 0.0006 | 0.4286 | 0.0013 | 0.8690 | 0.3443 | 0.0014 |

Nota: precision/F1 bajos por el desbalance extremo (84 vs 65421). Candidatos de lab vs IF de esta red = transferencia, no superioridad intrinseca.