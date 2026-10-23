# F6 - Sensibilidad a alfa (cortes calculados en VALIDACION, aplicados a TEST; sin reentrenar)

alfa=0,05 es la configuracion CONGELADA (reproduce el umbral operativo). Los demas son analisis de sensibilidad, no una re-seleccion.

| alfa | Umbral (score_samples) | FPR observado (test) | Recall | Precision | F1 |
|---:|---:|---:|---:|---:|---:|
| 0.01 | -0.622389 | 0.87 % | 59.52 % | 8.10 % | 0.1427 |
| 0.025 | -0.595282 | 2.17 % | 63.10 % | 3.60 % | 0.0680 |
| 0.05 | -0.569458 | 4.52 % | 64.29 % | 1.79 % | 0.0349 |
| 0.1 | -0.537022 | 9.31 % | 70.24 % | 0.96 % | 0.0189 |

- n validacion = 65553. El umbral de alfa=0,05 (-0,56946) reproduce el operativo (-0,56940); FPR test 4,52 %.
- Bajar alfa recorta FPR **y** recall; subirlo gana poco recall a gran costo de FPR. La literatura puede sustentar el **procedimiento** de calibracion por percentil, no que 0,05 sea optimo para esta red.
- No habia una **meta de aceptacion** de FPR/recall definida de antemano mas alla del objetivo de ~5 % de FPR fijado en validacion; no se inventa una post-hoc.