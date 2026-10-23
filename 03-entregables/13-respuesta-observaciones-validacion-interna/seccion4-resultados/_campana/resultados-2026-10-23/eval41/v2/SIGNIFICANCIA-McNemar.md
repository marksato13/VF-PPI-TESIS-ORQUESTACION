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

**Lectura:** frente a los candidatos de laboratorio y OCSVM/LOF/EE, el limpio difiere con p_Holm muy
pequeno (comete muchisimos menos FP). Frente al **contaminado** la diferencia es minima (ver b vs c
cercanos) -> coherente con que son **equivalentes**. No se afirma 'estadisticamente superior' como
conclusion fuerte por la dependencia entre ventanas; se reporta como diferencia **descriptiva** pareada.