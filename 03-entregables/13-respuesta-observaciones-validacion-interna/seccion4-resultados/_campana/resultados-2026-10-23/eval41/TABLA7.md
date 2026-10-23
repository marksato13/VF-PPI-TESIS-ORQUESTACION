# Tabla 7 - Comparacion de candidatos sobre las MISMAS ventanas (84+65421)

| Modelo | Entrenamiento | ROC-AUC | AP | Det@FPR5% | FPR5 real | FPR propio | Recall propio |
|---|---|---:|---:|---:|---:|---:|---:|
| IF limpio (desplegado) | esta red | 0.9247 | 0.1858 | 0.655 | 0.050 | 0.0453 | 0.6429 |
| IF recalibrado (contaminado, respaldo) | esta red | 0.9228 | 0.2026 | 0.667 | 0.050 | 0.0445 | 0.6429 |
| IF scaled (lab) | laboratorio | 0.8250 | 0.0043 | 0.167 | 0.050 | - | - |
| IF primary (lab) | laboratorio | 0.8283 | 0.0044 | 0.167 | 0.050 | - | - |
| IF uniform (lab) | laboratorio | 0.7960 | 0.0054 | 0.167 | 0.050 | - | - |
| IF exact (lab) | laboratorio | 0.7960 | 0.0054 | 0.167 | 0.050 | - | - |
| OCSVM (lab) | laboratorio | 0.4555 | 0.0011 | 0.559 | 0.698 | - | - |
| LOF (lab) | laboratorio | 0.2991 | 0.0009 | 0.000 | 0.503 | - | - |
| Elliptic Envelope (lab) | laboratorio | 0.3443 | 0.0014 | 0.059 | 0.050 | - | - |

Candidatos de laboratorio y el IF de esta red tienen condiciones de entrenamiento distintas:
esto mide TRANSFERENCIA a la red objetivo, no superioridad intrinseca del algoritmo.