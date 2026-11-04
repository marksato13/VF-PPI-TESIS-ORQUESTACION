# Tabla 3B — 3B revisado, etiquetas separadas (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.
Emisiones oportunas separadas por componente (reconciliación 2026-11-03): señal del IF, regla prevista
para la familia y otra regla. «Respuesta aplicada» no se mide aquí (sombra: nadie aplica).

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas (cualquiera) | 1.ª (s) | Señal IF | 1.ª IF (s) | Regla prevista | 1.ª regla (s) | Otra regla | Respuesta aplicada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 26.56 | 4 | 26.56 | 4 | 26.56 | 0 | no_medida |
| inundacion_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.9 | 8 | 24.9 | 8 | 24.9 | 0 | no_medida |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 8 | 20.19 | 0 | None | 8 | 20.19 | 0 | no_medida |
| inundacion_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.2 | 8 | 24.2 | 8 | 24.2 | 0 | no_medida |
| inundacion_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.43 | 8 | 25.43 | 8 | 25.43 | 0 | no_medida |
| inundacion_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.36 | 8 | 25.36 | 8 | 25.36 | 0 | no_medida |
| escaneo_sostenido-r4 | sí | 13 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 21.97 | 4 | 21.97 | 4 | 21.97 | 0 | no_medida |
| escaneo_sostenido-r5 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 35.63 | 3 | 35.63 | 3 | 35.63 | 0 | no_medida |
| escaneo_breve-r5 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| fuerza_bruta_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.59 | 8 | 23.59 | 8 | 23.59 | 0 | no_medida |
| fuerza_bruta_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.68 | 8 | 23.68 | 8 | 23.68 | 0 | no_medida |
| dns_inusual-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 21.88 | 7 | 21.88 | 6 | 21.88 | 2 | no_medida |
| escaneo_sostenido-r3 | sí | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 22.01 | 5 | 22.01 | 0 | None | 4 | no_medida |
| dns_inusual-r2 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 7 | 25.85 | 0 | None | 7 | 25.85 | 0 | no_medida |
| fuerza_bruta_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.84 | 8 | 18.84 | 8 | 18.84 | 0 | no_medida |
| fuerza_bruta_http-r4 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.44 | 8 | 18.44 | 8 | 18.44 | 0 | no_medida |
| dns_inusual-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 17.22 | 7 | 17.22 | 7 | 17.22 | 0 | no_medida |
| escaneo_breve-r1 | sí | 8 | oportuna | oportuna | solo_posterior | oportuna | oportuna | oportuna | oportuna | 1 | 16.4 | 1 | 16.4 | 0 | None | 1 | no_medida |
| escaneo_breve-r4 | no | 8 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| escaneo_breve-r3 | sí | 8 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| dns_inusual-r4 | sí | 15 | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | 6 | 23.88 | 0 | None | 6 | 23.88 | 0 | no_medida |
| fuerza_bruta_http-r1 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.14 | 8 | 25.14 | 8 | 25.14 | 0 | no_medida |
| inundacion_http-r5 | sí | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 29.32 | 6 | 29.32 | 6 | 29.32 | 0 | no_medida |
| escaneo_breve-r2 | sí | 8 | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| escaneo_sostenido-r1 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 39.61 | 3 | 39.61 | 3 | 39.61 | 0 | no_medida |

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
