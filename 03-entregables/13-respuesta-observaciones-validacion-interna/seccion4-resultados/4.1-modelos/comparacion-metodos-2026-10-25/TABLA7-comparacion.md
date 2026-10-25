# Tabla 7 — Comparación de detectores de novedad (evaluación por ventana)

Entrenamiento: 203 967 ventanas normales elegibles. Umbral: cuantil 1−α (interpolación lineal) de la puntuación de anomalía en las 65 553 ventanas de validación; anomalía si puntuación > umbral. Evaluación: 65 421 normales + 84 ataques. ROC-AUC y AP con puntuaciones continuas (no dependen de α). FPR val. = 65 553 ventanas; FPR prueba = 65 421.

## α = 0,03

| Método | TP | FP | TN | FN | Precisión | Recall | F1 | FPR val. | FPR prueba | ROC-AUC | AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IF | 54 | 1 723 | 63 698 | 30 | 3,04 % | 64,29 % | 0,0580 | 3,00 % | 2,63 % | 0,9247 | 0,1858 |
| OCSVM | 59 | 1 958 | 63 463 | 25 | 2,93 % | 70,24 % | 0,0562 | 3,00 % | 2,99 % | 0,8691 | 0,6357 |
| LOF | 77 | 2 314 | 63 107 | 7 | 3,22 % | 91,67 % | 0,0622 | 3,00 % | 3,54 % | 0,9763 | 0,0291 |
| EllipticEnvelope | 44 | 1 785 | 63 636 | 40 | 2,41 % | 52,38 % | 0,0460 | 3,00 % | 2,73 % | 0,9179 | 0,3811 |
| PCA | 71 | 2 116 | 63 305 | 13 | 3,25 % | 84,52 % | 0,0625 | 3,00 % | 3,23 % | 0,9487 | 0,5944 |

## α = 0,05

| Método | TP | FP | TN | FN | Precisión | Recall | F1 | FPR val. | FPR prueba | ROC-AUC | AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IF | 54 | 2 955 | 62 466 | 30 | 1,79 % | 64,29 % | 0,0349 | 5,00 % | 4,52 % | 0,9247 | 0,1858 |
| OCSVM | 71 | 3 319 | 62 102 | 13 | 2,09 % | 84,52 % | 0,0409 | 5,00 % | 5,07 % | 0,8691 | 0,6357 |
| LOF | 79 | 3 766 | 61 655 | 5 | 2,05 % | 94,05 % | 0,0402 | 5,00 % | 5,76 % | 0,9763 | 0,0291 |
| EllipticEnvelope | 48 | 3 039 | 62 382 | 36 | 1,55 % | 57,14 % | 0,0303 | 5,00 % | 4,65 % | 0,9179 | 0,3811 |
| PCA | 71 | 3 539 | 61 882 | 13 | 1,97 % | 84,52 % | 0,0384 | 5,00 % | 5,41 % | 0,9487 | 0,5944 |

## Umbrales y tiempos

| Método | α | Umbral (anomalía, >) | Umbral en escala original | t ajuste (s) | t inferencia 131 058 (s) |
|---|---:|---:|---:|---:|---:|
| IF | 0,03 | 0.5898535710336615 | -0.5898535710336615 (score_samples <) | congelado | 3,1 |
| IF | 0,05 | 0.5694578968203693 | -0.5694578968203693 (score_samples <) | congelado | 3,1 |
| OCSVM | 0,03 | -263.3060306010344 | 263.3060306010344 (score_samples <) | 586,2 | 146,9 |
| OCSVM | 0,05 | -297.17116473859403 | 297.17116473859403 (score_samples <) | 586,2 | 146,9 |
| LOF | 0,03 | 2.189323719487029 | -2.189323719487029 (score_samples <) | 69,0 | 49,2 |
| LOF | 0,05 | 1.5094663238037738 | -1.5094663238037738 (score_samples <) | 69,0 | 49,2 |
| EllipticEnvelope | 0,03 | 989355962.2513443 | -989355962.2513443 (score_samples <) | 17,4 | 0,0 |
| EllipticEnvelope | 0,05 | 247480102.42436323 | -247480102.42436323 (score_samples <) | 17,4 | 0,0 |
| PCA | 0,03 | 5.745082955563664 | — | 0,2 | 0,0 |
| PCA | 0,05 | 4.233583332682266 | — | 0,2 | 0,0 |
