# Criterio de aceptación del rendimiento (fijado antes de medir)

Este documento se publica **antes** de ejecutar ninguna medición secuencial. El criterio no se cambiará después de ver los resultados. Si no se cumple, el rendimiento queda **pendiente**, con el perfil del cuello de botella.

## Qué se mide

| | |
|---|---|
| Referencia | motor `953a436` (cierre técnico publicado) |
| Candidata | motor `862404e` (corrección de pendientes) y, si hay optimización, el commit que la contenga |
| Arnés | `replay_motor.py` de `4694e38` para las dos (CPU por ciclo, memoria y carga del equipo) |
| Configuración | la de la candidata del cierre: anillo de 5 s, disparo por eventos, paso 10 s, horizonte 230 s, reloj `coste`, modelo `if_limpio_2026_10` (sha256 `df547da0…fd60`) |
| Entradas | las congeladas del cierre: anillo re-troceado de 5 s (2535 ficheros) y segmento de EVE (sha256 `b7bf61a2…318f`) |
| Tramo | 07:24:40–10:05:40 completo, para tener historia previa y las mismas ventanas en las dos versiones |
| Ejecución | una corrida cada vez, en el mismo portátil, sin otros replays ni pruebas en paralelo. Se registra la carga del equipo en cada ciclo |

## Segmentos

- **Normal:** control del 3B, 07:32:00–08:05:00.
- **Inundación:** cada `inundacion_http-r1…r5`, de su `inicio` a su `fin` (marcas del orquestador).
- **Recuperación:** de cada `fin` a `fin + 120 s`.

## Criterios

Los cuatro tienen que cumplirse en **todos** los segmentos para declarar resuelto el rendimiento. Se basan en la cadencia del motor: paso de 10 s y rotación de 5 s.

| # | Criterio | Umbral | Por qué |
|---|---|---|---|
| R1 | Cadencia: duración de pared de cada ciclo | p95 ≤ 10 s **y** máximo ≤ 20 s | p95 dentro de un paso. El máximo es el criterio de continuidad del 3B (≤ 20 s) |
| R2 | Sin acumulación: retraso de decisión (`logged_at − window_end`) de las ventanas del segmento | p95 ≤ 15 s **y** máximo ≤ 25 s | 5 s de rotación + ≤ 20 s de ciclo. Por encima, las ventanas se encolan detrás de otras |
| R3 | Recuperación tras cada inundación | En ≤ 60 s desde el `fin`, el retraso vuelve a ≤ p95 del normal + 5 s y no vuelve a superarlo en la recuperación. Al acabar la recuperación, las pendientes son ≤ al máximo del normal | Que la cola se vacía y no deja deuda |
| R4 | Integridad | 0 ventanas `pcap_incompleto` o `ventana_no_regenerada`, y 0 ausentes, en los segmentos | Una mejora de tiempo no puede comprarse perdiendo ventanas |

## Lo que no se hará

- No se cambiarán los umbrales después de medir.
- No se declarará resuelto el rendimiento por una mejora de la mediana si R1–R4 fallan.
- Una pausa entre escrituras no se interpretará como pérdida sin comprobar las ventanas y la actividad.
- Las cifras son del portátil (`--factor-cpu 1`). **No** son una garantía para el Sensor1, que tendrá que medirse en vivo.
- Si se optimiza, no se cambian las 28 características, las anclas, el horizonte causal, el modelo, los umbrales ni las reglas. La equivalencia se comprueba antes de medir de nuevo.
