# Tabla 6-a — Comparación de los valores de α (IF limpio `if_limpio_2026_10`, validación sin Kali n=65 553)

Umbral = cuantil lineal de `score_samples` en validación sin Kali; alerta si `score_samples < umbral`.
Evaluación: 65 421 ventanas normales + 84 de ataque = 65 505. Clasificación con el **umbral de precisión completa**
(columna Umbral en `TABLA6a-comparacion-alfa.csv` / `umbrales-alfa-precision-completa.json`), no con el redondeado.
Verificado por fila: TP+FN=84 y FP+TN=65 421. Filas nuevas (2026-10-27): α=0,005 y α=0,008.

| α | Umbral | TP | FP | TN | FN | Precisión (%) | Recall (%) | F1 | FPR (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0,005 (nuevo) | -0.6378693863 | 26 | 279 | 65142 | 58 | 8.52 | 30.95 | 0.1337 | 0.43 |
| 0,008 (nuevo) | -0.6276028054 | 32 | 461 | 64960 | 52 | 6.49 | 38.10 | 0.1109 | 0.70 |
| 0,01 | -0.6223889502 | 50 | 567 | 64854 | 34 | 8.10 | 59.52 | 0.1427 | 0.87 |
| 0,02 | -0.6028434329 | 52 | 1130 | 64291 | 32 | 4.40 | 61.90 | 0.0821 | 1.73 |
| 0,025 | -0.5952824057 | 53 | 1421 | 64000 | 31 | 3.60 | 63.10 | 0.0680 | 2.17 |
| 0,03 | -0.5898535710 | 54 | 1723 | 63698 | 30 | 3.04 | 64.29 | 0.0580 | 2.63 |
| 0,04 | -0.5800997272 | 54 | 2299 | 63122 | 30 | 2.29 | 64.29 | 0.0443 | 3.51 |
| 0,05 | -0.5694578968 | 54 | 2955 | 62466 | 30 | 1.79 | 64.29 | 0.0349 | 4.52 |
| 0,1 | -0.5370224765 | 59 | 6092 | 59329 | 25 | 0.96 | 70.24 | 0.0189 | 9.31 |

Referencias reproducidas (sin Kali): α=0,01 → TP=50, FP=567, TN=64 854, FN=34; α=0,03 → 54/1 723/63 698/30; α=0,05 → 54/2 955/62 466/30.
El umbral desplegado operativo (−0,5693969936322356) proviene de α=0,05 sobre la validación **completa** (65 633); aquí la calibración es **sin Kali**. No se cambia el α desplegado.
