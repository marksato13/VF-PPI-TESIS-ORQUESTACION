# Tabla 3B — re-análisis de la primera campaña A (2026-10-29) con el analizador CORREGIDO (3A-1/3A-2); NO sustituye la Tabla 8 histórica ni el re-análisis anterior (analizar_3b.py)

Población principal = episodios con observación completa (inventario, fuente completa, integridad y destino),
independiente del resultado. Categorías: oportuna / solo_posterior / ausencia_con_observacion_suficiente /
no_evaluable. Las 7 configuraciones son derivadas; las emisiones reales van en su columna.

| Episodio | Principal | Ventanas esp. | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones oportunas | 1.ª (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | no | 12 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| inundacion_http-r1 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| dns_inusual-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| inundacion_http-r4 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| inundacion_http-r2 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| inundacion_http-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_sostenido-r4 | no | 13 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_sostenido-r5 | no | 12 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_breve-r5 | no | 8 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| fuerza_bruta_http-r3 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| fuerza_bruta_http-r5 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| dns_inusual-r5 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_sostenido-r3 | no | 13 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| dns_inusual-r2 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| fuerza_bruta_http-r2 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| fuerza_bruta_http-r4 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| dns_inusual-r1 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_breve-r1 | no | 7 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_breve-r4 | no | 8 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_breve-r3 | no | 8 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| dns_inusual-r4 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| fuerza_bruta_http-r1 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| inundacion_http-r5 | no | 15 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_breve-r2 | no | 8 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |
| escaneo_sostenido-r1 | no | 12 | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | no_evaluable | 0 | None |

Motivos fuera de la población principal:

- escaneo_sostenido-r2: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- inundacion_http-r1: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- dns_inusual-r3: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- inundacion_http-r4: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- inundacion_http-r2: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- inundacion_http-r3: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_sostenido-r4: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_sostenido-r5: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_breve-r5: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- fuerza_bruta_http-r3: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- fuerza_bruta_http-r5: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- dns_inusual-r5: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_sostenido-r3: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- dns_inusual-r2: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- fuerza_bruta_http-r2: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- fuerza_bruta_http-r4: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- dns_inusual-r1: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_breve-r1: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_breve-r4: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_breve-r3: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- dns_inusual-r4: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- fuerza_bruta_http-r1: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- inundacion_http-r5: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_breve-r2: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
- escaneo_sostenido-r1: sin inventario: no se puede establecer que no falten ventanas; 6 ventanas decididas sin evidencia de destino; fuente sin evaluar (no se aportó --calidad-fuentes); integridad no apta
