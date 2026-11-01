# Tabla 3B — campaña A repetida (3B) 2026-11-01 (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas | 1.ª (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | no | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 26.56 |
| inundacion_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.9 |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 8 | 20.19 |
| inundacion_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.2 |
| inundacion_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.43 |
| inundacion_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.36 |
| escaneo_sostenido-r4 | no | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 21.97 |
| escaneo_sostenido-r5 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 35.63 |
| escaneo_breve-r5 | no | 8 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| fuerza_bruta_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.59 |
| fuerza_bruta_http-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.68 |
| dns_inusual-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 21.88 |
| escaneo_sostenido-r3 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 22.01 |
| dns_inusual-r2 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 7 | 25.85 |
| fuerza_bruta_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.84 |
| fuerza_bruta_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.44 |
| dns_inusual-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 17.22 |
| escaneo_breve-r1 | no | 8 | oportuna | oportuna | solo_posterior | oportuna | oportuna | oportuna | oportuna | 1 | 16.4 |
| escaneo_breve-r4 | no | 8 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_breve-r3 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| dns_inusual-r4 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 6 | 23.88 |
| fuerza_bruta_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.14 |
| inundacion_http-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 29.32 |
| escaneo_breve-r2 | no | 8 | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_sostenido-r1 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 39.61 |

Motivos fuera de la población principal:

- escaneo_sostenido-r2: integridad no apta
- inundacion_http-r1: integridad no apta
- dns_inusual-r3: fuente degradada; integridad no apta
- inundacion_http-r4: fuente degradada; integridad no apta
- inundacion_http-r2: fuente degradada; integridad no apta
- inundacion_http-r3: fuente degradada; integridad no apta
- escaneo_sostenido-r4: integridad no apta
- escaneo_sostenido-r5: integridad no apta
- escaneo_breve-r5: integridad no apta
- fuerza_bruta_http-r3: fuente degradada; integridad no apta
- fuerza_bruta_http-r5: integridad no apta
- dns_inusual-r5: fuente degradada; integridad no apta
- escaneo_sostenido-r3: integridad no apta
- dns_inusual-r2: integridad no apta
- fuerza_bruta_http-r2: fuente degradada; integridad no apta
- fuerza_bruta_http-r4: integridad no apta
- dns_inusual-r1: integridad no apta
- escaneo_breve-r1: integridad no apta
- escaneo_breve-r4: fuente degradada; integridad no apta
- dns_inusual-r4: integridad no apta
- fuerza_bruta_http-r1: integridad no apta
- inundacion_http-r5: integridad no apta
- escaneo_breve-r2: integridad no apta
- escaneo_sostenido-r1: integridad no apta
