# Tabla 8 — campaña A (generada por analizar.py)

Celda: episodios con **detección durante** / episodios **evaluables** (cobertura suficiente).
Clasificación por `logged_at` y solape de la ventana con el ataque. Las configuraciones derivadas
offline no son alertas emitidas en vivo (el motor usó el umbral desplegado).

Umbrales (score_samples, señal si score < umbral): α 0,05 = -0.5694578968203694; α 0,03 = -0.5898535710336618; α 0,01 = -0.6223889502095352; desplegado en vivo = -0.5693969936322356.

| Familia | Evaluables | IF 0,05 | IF 0,03 | IF 0,01 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 | Híbrido 0,01 |
|---|---|---|---|---|---|---|---|---|
| Escaneo sostenido | 0 | — | — | — | — | — | — | — |
| Inundación HTTP | 0 | — | — | — | — | — | — | — |
| DNS inusual | 0 | — | — | — | — | — | — | — |
| Escaneo breve | 0 | — | — | — | — | — | — | — |
| Fuerza bruta HTTP | 0 | — | — | — | — | — | — | — |

No evaluables: escaneo_sostenido-r2, escaneo_sostenido-r4, escaneo_sostenido-r5, escaneo_sostenido-r3, escaneo_sostenido-r1, inundacion_http-r1, inundacion_http-r4, inundacion_http-r2, inundacion_http-r3, inundacion_http-r5, dns_inusual-r3, dns_inusual-r5, dns_inusual-r2, dns_inusual-r1, dns_inusual-r4, escaneo_breve-r5, escaneo_breve-r1, escaneo_breve-r4, escaneo_breve-r3, escaneo_breve-r2, fuerza_bruta_http-r3, fuerza_bruta_http-r5, fuerza_bruta_http-r2, fuerza_bruta_http-r4, fuerza_bruta_http-r1

Métricas por ventana: no calculadas (sin --etiquetas no se fabrican métricas)

## Emisiones observadas (registro aparte; no es una configuración de la tabla)

Primera alerta del IF **desplegado** con umbral registrado = desplegado, durante el ataque y con atribución confirmada. Es la única base para una latencia real de emisión.

| Episodio | Primera alerta real (s desde el inicio) | Registro | Eventos con emisor/configuración desconocida |
|---|---|---|---|
| escaneo_sostenido-r2 | 45.5 | motor:36658 | 0 |
| inundacion_http-r1 | 38.7 | motor:37009 | 0 |
| dns_inusual-r3 | — | — | 0 |
| inundacion_http-r4 | 34.7 | motor:37863 | 0 |
| inundacion_http-r2 | 46.0 | motor:38287 | 0 |
| inundacion_http-r3 | 42.5 | motor:38673 | 0 |
| escaneo_sostenido-r4 | 33.1 | motor:39101 | 0 |
| escaneo_sostenido-r5 | 44.7 | motor:39520 | 0 |
| escaneo_breve-r5 | — | — | 0 |
| fuerza_bruta_http-r3 | 35.6 | motor:40208 | 0 |
| fuerza_bruta_http-r5 | 39.7 | motor:40612 | 0 |
| dns_inusual-r5 | 34.4 | motor:41009 | 0 |
| escaneo_sostenido-r3 | 39.7 | motor:41448 | 0 |
| dns_inusual-r2 | — | — | 0 |
| fuerza_bruta_http-r2 | 26.4 | motor:42228 | 0 |
| fuerza_bruta_http-r4 | 34.7 | motor:42650 | 0 |
| dns_inusual-r1 | 28.5 | motor:43061 | 0 |
| escaneo_breve-r1 | — | — | 0 |
| escaneo_breve-r4 | — | — | 0 |
| escaneo_breve-r3 | — | — | 0 |
| dns_inusual-r4 | — | — | 0 |
| fuerza_bruta_http-r1 | 30.7 | motor:44862 | 0 |
| inundacion_http-r5 | 28.8 | motor:45252 | 0 |
| escaneo_breve-r2 | — | — | 0 |
| escaneo_sostenido-r1 | 42.4 | motor:45966 | 0 |

## Ventanas no evaluadas (calidad y cobertura; no son decisiones)

Contadas: 3 · por motivo: ventana_no_regenerada = 3 · duplicados: 0 · conflictos con decisión: 0 · incidencias: 0

- Control (window_end en [desde, hasta]): 2526 evaluadas + 0 no evaluadas explícitas; cobertura entre registradas 1.0 (sin inventario de ventanas esperadas: no garantiza que no falten registros); tasas sobre las evaluadas.
