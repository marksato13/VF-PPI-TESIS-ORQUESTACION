# Trazabilidad de datos

| Conjunto | Filas | Variación | Nota |
|---|---:|---:|---|
| particionado-limpio.csv (filas totales) | 337 980 |  | entrada declarada del entrenamiento (sha 5ef83b32…) |
| descartadas por banda de guarda | 2 778 | −2 778 | 60 s al inicio de cada bloque; no pertenecen a ninguna partición |
| partición train | 204 148 |  |  |
|   excluidas del entrenamiento (eligible_training=False) | 181 | −181 | Kali 10.10.20.30, ráfaga 27-sep 21:35–22:05 UTC; única diferencia entre particionado-limpio y nota-L |
|   entrenamiento efectivo | 203 967 | 203 967 | coincide con el informe del modelo |
| partición validation (calibración original) | 65 633 | 65 633 | idéntica en nota-L |
|   ventanas Kali en validación (excluidas solo de la nueva calibración) | 80 | −80 | normalidad no confirmada; NO se etiquetan como ataque |
|   validación sin Kali (nueva calibración) | 65 553 | 65 553 |  |
| partición test = oro (prueba normal) | 65 421 | 65 421 | mismas claves y valores; incluye 74 ventanas de 10.10.20.30, sin cambios |
| ataques nota M (evaluación) | 84 | 84 | 0 solapes con train/validation/test |

Las tres exclusiones son distintas: 2 778 por banda de guarda (antes de particionar), 181 del entrenamiento (ráfaga Kali del 27-sep, ya aplicadas al entrenar el modelo vigente) y 80 de validación (solo para esta nueva calibración). Entrenamiento, prueba y ataques no cambian.
