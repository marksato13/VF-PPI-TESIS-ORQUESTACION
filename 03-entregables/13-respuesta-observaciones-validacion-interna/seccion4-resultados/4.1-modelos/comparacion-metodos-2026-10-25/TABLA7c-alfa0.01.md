# Tabla 7-c — Comparación de detectores con α = 0,01 (evaluación por ventana)

Mismos artefactos y protocolo que las Tablas 7-a (α=0,05) y 7-b (α=0,03): entrenamiento 203 967 ventanas elegibles (181 excluidas), validación 65 553 para calibrar, evaluación 65 421 normales + 84 ataques = 65 505, mismas 28 características y escalador congelado. Umbral **propio por modelo** = cuantil 1−α (interpolación lineal) de SUS puntuaciones de validación; anomalía si puntuación > umbral. Se reutilizan las puntuaciones ya publicadas (`salidas/puntuaciones-*.csv.gz`, hashes verificados); **no** se reentrena ni se re-puntúa. ROC-AUC y AP se calculan con las puntuaciones continuas orientadas a anomalía y **no dependen de α** (coinciden con 7-a/7-b). Precisión/recall/FPR en %; F1, ROC-AUC y AP en escala 0–1.

| Método | TP | FP | TN | FN | Precisión | Recall | F1 | FPR val. | FPR prueba | ROC-AUC | AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IF | 50 | 567 | 64 854 | 34 | 8,10 % | 59,52 % | 0,1427 | 1,00 % | 0,87 % | 0,9247 | 0,1858 |
| OCSVM | 57 | 708 | 64 713 | 27 | 7,45 % | 67,86 % | 0,1343 | 1,00 % | 1,08 % | 0,8691 | 0,6357 |
| LOF | 36 | 975 | 64 446 | 48 | 3,56 % | 42,86 % | 0,0658 | 1,00 % | 1,49 % | 0,9763 | 0,0291 |
| EllipticEnvelope | 40 | 570 | 64 851 | 44 | 6,56 % | 47,62 % | 0,1153 | 1,00 % | 0,87 % | 0,9179 | 0,3811 |
| PCA | 67 | 825 | 64 596 | 17 | 7,51 % | 79,76 % | 0,1373 | 1,00 % | 1,26 % | 0,9487 | 0,5944 |

Verificado por fila: TP+FN=84, FP+TN=65 421, Precisión=TP/(TP+FP), Recall=TP/84, F1=2TP/(2TP+FP+FN), FPR prueba=FP/65 421. FPR val. = FP_validación/65 553 (≈ α por construcción).
IF reproduce la comprobación previa: umbral (escala `score_samples`) = −0,622388950209535 (coincide con −0,6223889502095352 hasta 1e−12; la diferencia de último dígito viene de negar la escala de anomalía), TP=50, FP=567, TN=64 854, FN=34 (exactos).
ROC-AUC/AP idénticos a 7-a/7-b (mismas puntuaciones, solo cambia el umbral).

## Umbrales (precisión completa en `umbrales-7c-precision-completa.json`)

| Método | Umbral (anomalía, >) | Umbral escala original (`score_samples <`) |
|---|---:|---:|
| IF | `0.6223889502095351` | `-0.6223889502095351` |
| OCSVM | `-177.5154311522422` | `177.5154311522422` |
| LOF | `278.2690726140263` | `-278.2690726140263` |
| EllipticEnvelope | `5566829575.714513` | `-5566829575.714513` |
| PCA | `11.259068388450087` | — |
