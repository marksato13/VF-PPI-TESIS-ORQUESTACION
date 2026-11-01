# Tabla 3B — nuevo análisis del paso 2 con el analizador CORREGIDO (3A-1/3A-2); no sustituye reanalisis-paso2/analisis/ (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas | 1.ª (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inundacion_http-rT1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 28.66 |
| inundacion_http-rT2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 34.45 |
| inundacion_http-rT3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 37.21 |

Motivos fuera de la población principal:

- inundacion_http-rT1: integridad desconocida
- inundacion_http-rT2: fuente degradada; integridad desconocida
- inundacion_http-rT3: fuente degradada; integridad desconocida
