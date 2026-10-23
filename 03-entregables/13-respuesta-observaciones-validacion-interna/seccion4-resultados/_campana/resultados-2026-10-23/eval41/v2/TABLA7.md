# Tabla 7 - Comparacion de configuraciones (mismas 84 + 65 421 ventanas, mismo etiquetado)

Precision/Recall/FPR en %; F1/ROC-AUC/AP en [0,1]. Umbral propio de cada modelo (de su manifiesto, precision completa).

| Configuracion | Entrenamiento | Precision | Recall | F1 | FPR | ROC-AUC | AP |
|---|---|---:|---:|---:|---:|---:|---:|
| IF limpio (desplegado) | esta red | 1.79 % | 64.29 % | 0.03485 | 4.53 % | 0.92473 | 0.18581 |
| IF recalibrado (contaminado, antecedente) | esta red | 1.82 % | 64.29 % | 0.0354 | 4.45 % | 0.9228 | 0.2026 |
| IF scaled (lab) | laboratorio | 0.39 % | 91.67 % | 0.0077 | 30.34 % | 0.8250 | 0.0043 |
| IF primary (lab) | laboratorio | 0.36 % | 82.14 % | 0.0072 | 29.07 % | 0.8283 | 0.0044 |
| IF uniform (lab) | laboratorio | 0.32 % | 85.71 % | 0.0064 | 34.13 % | 0.7960 | 0.0054 |
| IF exact (lab) _(= IF uniform, identico)_ | laboratorio | 0.32 % | 85.71 % | 0.0064 | 34.13 % | 0.7960 | 0.0054 |
| OCSVM (lab) | laboratorio | 0.13 % | 100.00 % | 0.0026 | 99.57 % | 0.4555 | 0.0011 |
| LOF (lab) | laboratorio | 0.12 % | 70.24 % | 0.0023 | 76.80 % | 0.2991 | 0.0009 |
| Elliptic Envelope (lab) | laboratorio | 0.06 % | 42.86 % | 0.0013 | 86.90 % | 0.3443 | 0.0014 |

**Lecturas honestas:**
- **El IF limpio NO gana en todas las metricas:** ROC-AUC limpio 0,9247 > contaminado 0,9228, pero **AP contaminado 0,2026 > limpio 0,1858** y FPR contaminado 4,45 % < limpio 4,53 %. Ambos detectaron 54/84 y difirieron en FP, ROC-AUC y AP. Esta coincidencia de recall no demuestra equivalencia estadistica ni superioridad.
- `IF uniform` e `IF exact` son **identicos** (mismo vector de scores): hay 8 configuraciones distintas, no 9.
- Candidatos de **laboratorio**: recall alto pero **FPR 29-99,6 %** (inservibles en esta red); OCSVM marca el 99,6 % del normal (ROC-AUC 0,455, bajo el azar); LOF ROC-AUC 0,299.
- Es una comparacion de **transferencia** al entorno objetivo (los datos de entrenamiento difieren), **no** una prueba aislada de superioridad del algoritmo IF.
- **Det@FPR5% retirada**: el calculo anterior fijaba el corte sobre los negativos de TEST (fuga); ademas OCSVM/LOF no alcanzan el 5 % por empates. La sensibilidad correcta (corte en validacion) esta en `ALFA-F6`.
