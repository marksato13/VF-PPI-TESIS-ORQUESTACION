# Tabla 3B — replay pendientes Etapa 2: sec-opt-6b6ef82 (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas | 1.ª (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 23.92 |
| inundacion_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.41 |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 9 | 7.47 |
| inundacion_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.12 |
| inundacion_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.92 |
| inundacion_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.71 |
| escaneo_sostenido-r4 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 17.37 |
| escaneo_sostenido-r5 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 21.61 |
| escaneo_breve-r5 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| fuerza_bruta_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 7.78 |
| fuerza_bruta_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.9 |
| dns_inusual-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 8.21 |
| escaneo_sostenido-r3 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 7.58 |
| dns_inusual-r2 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 8 | 12.15 |
| fuerza_bruta_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 3.27 |
| fuerza_bruta_http-r4 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 3.29 |
| dns_inusual-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 13.15 |
| escaneo_breve-r1 | sí | 8 | oportuna | oportuna | solo_posterior | oportuna | oportuna | oportuna | oportuna | 1 | 12.57 |
| escaneo_breve-r4 | no | 8 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_breve-r3 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 1 | 16.94 |
| dns_inusual-r4 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 9 | 9.8 |
| fuerza_bruta_http-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 10.9 |
| inundacion_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 11.69 |
| escaneo_breve-r2 | sí | 8 | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_sostenido-r1 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 22.54 |

Motivos fuera de la población principal:

- inundacion_http-r1: integridad no apta
- dns_inusual-r3: fuente degradada; integridad no apta
- inundacion_http-r4: fuente degradada; integridad no apta
- inundacion_http-r2: fuente degradada; integridad no apta
- inundacion_http-r3: fuente degradada; integridad no apta
- fuerza_bruta_http-r3: fuente degradada; integridad no apta
- dns_inusual-r5: fuente degradada; integridad no apta
- fuerza_bruta_http-r2: fuente degradada; integridad no apta
- escaneo_breve-r4: fuente degradada; integridad no apta
- escaneo_sostenido-r1: integridad no apta
