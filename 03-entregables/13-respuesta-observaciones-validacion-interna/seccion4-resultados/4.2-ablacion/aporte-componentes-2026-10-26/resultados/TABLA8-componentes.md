# Tabla 8 — Aporte de los componentes por episodio (recalculado offline)

Bateria del 05-oct-2026 (N = 3 por familia), re-procesada desde los PCAP originales con el procesamiento
del motor vigente, el IF congelado `if_limpio_2026_10` y los heuristicos `2026-10-06.2`. Un episodio cuenta
como detectado si hay al menos una senal atribuible (ventana de 10.10.20.30 con fin en [T0, ultimo paquete
de ataque + 60 s]). Es una reproduccion offline, no una prueba nueva en vivo.

| Familia | Episodios evaluados | IF 0,05 | IF 0,03 | Heuristicos | Hibrido 0,05 | Hibrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual (alta entropia) | 3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| Inundacion HTTP | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Escaneo de puertos | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Total | 9 | 6/9 | 6/9 | 9/9 | 9/9 | 9/9 |
| Fuerza bruta HTTP | 0 | no evaluado | no evaluado | no evaluado | no evaluado | no evaluado |

Umbrales del IF (score_samples, cuantil 1-alfa sobre 65 553 ventanas de validacion): alfa 0,05 -> -0.5694578968; alfa 0,03 -> -0.5898535710.

## Complementariedad por episodio

| alfa | ambos | solo IF | solo heuristicos | ninguno |
|---|---|---|---|---|
| 0,05 | 6: e4-r1, e4-r2, e4-r3, e1-r1, e1-r2, e1-r3 | 0 | 3: e3-r1, e3-r2, e3-r3 | 0 |
| 0,03 | 6: e4-r1, e4-r2, e4-r3, e1-r1, e1-r2, e1-r3 | 0 | 3: e3-r1, e3-r2, e3-r3 | 0 |

## Resultado historico (no recalculado, 05-oct, modelo contaminado `if_recalibrado_2026_09`)

Modelo 6/9 · heuristicos 7/9 · combinado 9/9 — reproducido offline en 9/9 episodios a partir de los `features.csv` guardados. No es comparable
con las columnas de arriba: otro modelo, otra version de heuristicos y otro procesamiento (PCAP sin deduplicar).

## Metricas por ventana sobre la poblacion de la Tabla 7 (65 421 normales + 84 ataques)

| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 54 | 2955 | 62466 | 30 | 0.0179 | 0.6429 | 0.0349 | 4.52 % |
| IF_0.03 | 54 | 1723 | 63698 | 30 | 0.0304 | 0.6429 | 0.0580 | 2.63 % |
| HEUR | 47 | 472 | 64949 | 37 | 0.0906 | 0.5595 | 0.1559 | 0.72 % |
| HIB_0.05 | 54 | 3417 | 62004 | 30 | 0.0156 | 0.6429 | 0.0304 | 5.22 % |
| HIB_0.03 | 54 | 2192 | 63229 | 30 | 0.0240 | 0.6429 | 0.0464 | 3.35 % |

ROC-AUC y AP solo existen para el IF (Tabla 7); el hibrido es una regla OR sin puntuacion continua.

