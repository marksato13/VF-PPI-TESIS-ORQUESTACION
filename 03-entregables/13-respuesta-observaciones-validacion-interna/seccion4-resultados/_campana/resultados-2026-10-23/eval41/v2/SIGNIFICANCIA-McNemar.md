# 4.1 - Significancia McNemar + Holm (predicciones ACTUALES, umbral propio)

IF limpio vs cada candidato sobre 65 505 ventanas. `b` = ventanas donde el limpio acierta y el otro
falla; `c` = al reves. **Salvedad:** la unidad es la ventana y las ventanas son **dependientes**
(series temporales); McNemar asume pares discordantes independientes, asi que esto es **descriptivo**,
no una prueba inferencial estricta. Dominado por diferencias en falsos positivos sobre normales.

| vs | b (limpio mejor) | c (otro mejor) | p (McNemar) | p_Holm | método |
|---|---:|---:|---:|---:|---|
| IF scaled (lab) | 16939 | 74 | 0 | 0 | normal (continuidad) |
| IF primary (lab) | 16140 | 101 | 0 | 0 | normal (continuidad) |
| IF uniform (lab) | 19398 | 49 | 0 | 0 | normal (continuidad) |
| OCSVM (lab) | 62180 | 30 | 0 | 0 | normal (continuidad) |
| LOF (lab) | 49706 | 2431 | 0 | 0 | normal (continuidad) |
| Elliptic Envelope (lab) | 56281 | 2372 | 0 | 0 | normal (continuidad) |
| IF recalibrado (contaminado, antecedente) | 179 | 227 | 0.0196 | 0.0196 | binomial exacta |

**Lectura (descriptiva; NO inferencia estricta):** los `p=0` de la tabla son del formato `%.3g`; el valor
real es **p < 1e-16** (no cero literal). Frente a los candidatos de laboratorio/OCSVM/LOF/EE el limpio
comete muchisimos menos FP (b >> c). Frente al **contaminado**: discordantes **b=179 (limpio mejor) /
c=227 (contaminado mejor)**, p ≈ 0,02 → **no se afirma superioridad de ninguno**. La afirmación
respaldada es solo: **"ambos detectaron 54/84; difirieron en FP, ROC-AUC y AP"**. **El mismo recall NO
demuestra equivalencia estadistica**, y como las ventanas son **dependientes** (series temporales) McNemar
aqui es **descriptivo**, no una prueba inferencial valida; no se usan los terminos "equivalentes" ni
"ruido de muestra" ni "estadisticamente superior".