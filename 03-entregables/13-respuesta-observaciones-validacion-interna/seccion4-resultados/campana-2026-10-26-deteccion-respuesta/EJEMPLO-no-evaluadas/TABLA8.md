# Tabla 8 — campaña A (generada por analizar.py)

Celda: episodios con **detección durante** / episodios **evaluables** (cobertura suficiente).
Clasificación por `logged_at` y solape de la ventana con el ataque. Las configuraciones derivadas
offline no son alertas emitidas en vivo (el motor usó el umbral desplegado).

Umbrales (score_samples, señal si score < umbral): α 0,05 = -0.5694578968203694; α 0,03 = -0.5898535710336618; α 0,01 = -0.6223889502095352; desplegado en vivo = -0.5693969936322356.

| Familia | Evaluables | IF 0,05 | IF 0,03 | IF 0,01 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 | Híbrido 0,01 |
|---|---|---|---|---|---|---|---|---|
| Inundación HTTP | 0 | — | — | — | — | — | — | — |

No evaluables: inundacion_http-r1

Métricas por ventana: calculadas

## Emisiones observadas (registro aparte; no es una configuración de la tabla)

Primera alerta del IF **desplegado** con umbral registrado = desplegado, durante el ataque y con atribución confirmada. Es la única base para una latencia real de emisión.

| Episodio | Primera alerta real (s desde el inicio) | Registro | Eventos con emisor/configuración desconocida |
|---|---|---|---|
| inundacion_http-r1 | 41.0 | motor:5 | 0 |

## Ventanas no evaluadas (calidad y cobertura; no son decisiones)

Contadas: 3 · por motivo: pcap_incompleto = 2, ventana_no_regenerada = 1 · duplicados: 0 · conflictos con decisión: 0 · incidencias: 0

| Episodio | Ventanas del ataque | Posteriores que solapan | Evaluable | Efecto |
|---|---|---|---|---|
| inundacion_http-r1 | 1 | 0 | no | 1 ancla(s) del ataque sin decisión constan como ventana_no_evaluada: la cobertura es insuficiente y el episodio no es evaluable (antes de #59 esas anclas ya faltaban como pérdida de datos; la Tabla 8 no cambia, cambia el motivo) |

- Detección confirmada fuera de la comparación: inundacion_http-r1 (IF_0.05, IF_0.03, IF_0.01, HIB_0.05, HIB_0.03, HIB_0.01).
- Control (window_end en [desde, hasta]): 8 evaluadas + 2 no evaluadas explícitas; cobertura entre registradas 0.8 (sin inventario de ventanas esperadas: no garantiza que no falten registros); tasas sobre las evaluadas.
- Conjunto etiquetado: 3 claves esperadas = 2 con decisión + 1 no evaluadas + 0 sin registro; cobertura total 0.666667; métricas solo sobre las claves con decisión.
