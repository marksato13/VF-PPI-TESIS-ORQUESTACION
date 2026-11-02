# Tabla 3B — replay cierre Etapa 2: cand-e5-eventos (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas | 1.ª (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 24.2 |
| inundacion_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.25 |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 9 | 7.56 |
| inundacion_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.02 |
| inundacion_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 11.68 |
| inundacion_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 9.98 |
| escaneo_sostenido-r4 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 19.33 |
| escaneo_sostenido-r5 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 22.54 |
| escaneo_breve-r5 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| fuerza_bruta_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.2 |
| fuerza_bruta_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.98 |
| dns_inusual-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 9.24 |
| escaneo_sostenido-r3 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 8.5 |
| dns_inusual-r2 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 8 | 13.26 |
| fuerza_bruta_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 4.25 |
| fuerza_bruta_http-r4 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 4.35 |
| dns_inusual-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 14.21 |
| escaneo_breve-r1 | sí | 8 | oportuna | oportuna | solo_posterior | oportuna | oportuna | oportuna | oportuna | 1 | 13.46 |
| escaneo_breve-r4 | no | 8 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_breve-r3 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| dns_inusual-r4 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 8 | 11.11 |
| fuerza_bruta_http-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 11.53 |
| inundacion_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 13.08 |
| escaneo_breve-r2 | sí | 8 | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None |
| escaneo_sostenido-r1 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 23.91 |

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
