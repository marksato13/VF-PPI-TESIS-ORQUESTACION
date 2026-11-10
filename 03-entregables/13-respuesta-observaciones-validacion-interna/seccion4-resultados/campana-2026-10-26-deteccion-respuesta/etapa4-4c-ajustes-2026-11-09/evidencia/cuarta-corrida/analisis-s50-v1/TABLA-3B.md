# Tabla 3B — Etapa 4 4c 2026-11-10 (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.
Emisiones oportunas separadas por componente (reconciliación 2026-11-03): señal del IF, regla prevista
para la familia y otra regla. «Respuesta aplicada» no se mide aquí (sombra: nadie aplica).

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas (cualquiera) | 1.ª (s) | Señal IF | 1.ª IF (s) | Regla prevista | 1.ª regla (s) | Otra regla | Respuesta aplicada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| inundacion_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.76 | 8 | 9.76 | 8 | 9.76 | 0 | no_medida |
| fuerza_bruta_http-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 11.35 | 8 | 11.35 | 8 | 11.35 | 0 | no_medida |
| dns_inusual-r1 | no | 15 | oportuna | oportuna | no_evaluable | oportuna | oportuna | oportuna | oportuna | 8 | 16.94 | 7 | 26.9 | 8 | 16.94 | 0 | no_medida |
| fuerza_bruta_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 9.51 | 8 | 9.51 | 8 | 9.51 | 0 | no_medida |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 7 | 19.69 | 0 | None | 7 | 19.69 | 0 | no_medida |
| inundacion_http-r3 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 7.35 | 9 | 7.35 | 9 | 7.35 | 0 | no_medida |
| fuerza_bruta_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 9 | 8.25 | 9 | 8.25 | 9 | 8.25 | 0 | no_medida |
| escaneo_breve-r4 | no | 7 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| escaneo_sostenido-r5 | no | 11 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 13.14 | 4 | 13.14 | 4 | 13.14 | 0 | no_medida |
| fuerza_bruta_http-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 12.27 | 8 | 12.27 | 8 | 12.27 | 0 | no_medida |
| escaneo_breve-r2 | no | 6 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| fuerza_bruta_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.47 | 8 | 8.47 | 8 | 8.47 | 0 | no_medida |
| escaneo_sostenido-r2 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 5.11 | 5 | 5.11 | 5 | 5.11 | 0 | no_medida |
| dns_inusual-r4 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 25.64 | 4 | 55.87 | 7 | 25.64 | 0 | no_medida |
| escaneo_breve-r5 | no | 6 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| inundacion_http-r2 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 12.78 | 8 | 12.78 | 8 | 12.78 | 0 | no_medida |
| inundacion_http-r1 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 15.16 | 7 | 15.16 | 7 | 15.16 | 0 | no_medida |
| escaneo_sostenido-r3 | no | 11 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 9.15 | 5 | 9.15 | 5 | 9.15 | 0 | no_medida |
| escaneo_sostenido-r1 | no | 11 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 5.97 | 5 | 5.97 | 5 | 5.97 | 0 | no_medida |
| dns_inusual-r2 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 7 | 25.76 | 0 | None | 7 | 25.76 | 0 | no_medida |
| inundacion_http-r5 | no | 15 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 8.29 | 8 | 8.29 | 7 | 19.33 | 0 | no_medida |
| dns_inusual-r5 | no | 15 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 7 | 23.72 | 0 | None | 7 | 23.72 | 0 | no_medida |
| escaneo_breve-r3 | no | 7 | oportuna | solo_posterior | solo_posterior | solo_posterior | oportuna | solo_posterior | solo_posterior | 1 | 3.13 | 1 | 3.13 | 0 | None | 0 | no_medida |
| escaneo_breve-r1 | no | 6 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 | None | 0 | None | 0 | None | 0 | no_medida |
| escaneo_sostenido-r4 | no | 12 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 5.13 | 5 | 5.13 | 5 | 5.13 | 0 | no_medida |

Motivos fuera de la población principal:

- inundacion_http-r4: fuente insuficiente; integridad no apta
- fuerza_bruta_http-r4: fuente insuficiente; integridad no apta
- dns_inusual-r1: fuente insuficiente; integridad no apta
- fuerza_bruta_http-r3: fuente insuficiente; integridad no apta
- dns_inusual-r3: fuente insuficiente; integridad no apta
- inundacion_http-r3: fuente insuficiente; integridad no apta
- fuerza_bruta_http-r1: fuente insuficiente; integridad no apta
- escaneo_breve-r4: fuente insuficiente; integridad no apta
- escaneo_sostenido-r5: fuente insuficiente; integridad no apta
- fuerza_bruta_http-r5: fuente insuficiente; integridad no apta
- escaneo_breve-r2: fuente insuficiente; integridad no apta
- fuerza_bruta_http-r2: fuente insuficiente; integridad no apta
- escaneo_sostenido-r2: fuente insuficiente; integridad no apta
- dns_inusual-r4: fuente insuficiente; integridad no apta
- escaneo_breve-r5: fuente insuficiente; integridad no apta
- inundacion_http-r2: fuente insuficiente; integridad no apta
- inundacion_http-r1: fuente insuficiente; integridad no apta
- escaneo_sostenido-r3: fuente insuficiente; integridad no apta
- escaneo_sostenido-r1: fuente insuficiente; integridad no apta
- dns_inusual-r2: fuente insuficiente; integridad no apta
- inundacion_http-r5: fuente insuficiente; integridad no apta
- dns_inusual-r5: fuente insuficiente; integridad no apta
- escaneo_breve-r3: fuente insuficiente; integridad no apta
- escaneo_breve-r1: fuente insuficiente; integridad no apta
- escaneo_sostenido-r4: fuente insuficiente; integridad no apta
