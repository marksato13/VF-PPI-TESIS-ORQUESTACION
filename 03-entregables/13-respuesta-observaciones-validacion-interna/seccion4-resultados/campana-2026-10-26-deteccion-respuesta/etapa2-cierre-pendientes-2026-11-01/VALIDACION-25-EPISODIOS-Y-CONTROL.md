# 25 episodios y control, con la versión corregida

## Qué se ejecutó

- **Analizador.** `analizar_3b.py` **sin modificar**, con los mismos argumentos que en el cierre técnico: inventario 07:24:40–10:05:30, control 07:32–08:05, mismas marcas, configuración, destinos, integridad v2 y calidad de fuentes. Guion: `guiones/analizar_pendientes.sh`.
- **Corridas analizadas.** Las corridas secuenciales completas `sec-ref-953a436` (referencia) y `sec-opt-6b6ef82` (versión corregida y optimizada). Las entradas son las congeladas.
- **Antecedente.** El análisis del cierre técnico se conserva sin tocar en `../etapa2-cierre-tecnico-2026-11-01/resultados/analisis-3b-cand-e5-eventos/`.
- **Criterios.** No se cambian los criterios de admisión. No se recupera ningún episodio excluido por pérdidas originales de Suricata.

## Ventanas

| | `953a436` (ref) | `6b6ef82` (corregida) | Cambio |
|---|---|---|---|
| Requeridas (inventario del analizador, 07:28:30–10:03:30) | 12 223 | 12 209 | −14 |
| Decididas a tiempo | 12 209 | 12 209 | 0 |
| No evaluadas | 14 (`ventana_no_regenerada`) | 0 | −14 |
| Canceladas justificadamente (`pendiente_cancelada`, fuera del inventario del analizador) | 0 | 14 | +14 |
| Ausentes | 0 | 0 | 0 |
| Retraso de disponibilidad p50 / p95 / máx (s) | 2,54 / 6,42 / 12,64 | 2,23 / 4,45 / 7,27 | efecto del rendimiento |
| `no_evaluada:no_elegible` de arranque (07:21:xx, fuera del rango del inventario) | sin registro | 33 | +33 explícitas |

**Por qué bajan las requeridas.** Las 14 ventanas que desaparecen del denominador son las del `DIAGNOSTICO-14-VENTANAS.md`: no son registrables por la regla causal en su propio horizonte. No se ocultan: cada una tiene su evento `pendiente_cancelada`, con la evidencia, en `resultados/replays/sec-opt-6b6ef82/motor_decision.log.gz`.

**Ventanas de arranque.** Las 33 `no_elegible` son ventanas de arranque sin historia suficiente (`history_coverage < 60`). Antes se omitían en silencio; ahora se registran. Están fuera del rango del inventario y del control, y no cambian ningún denominador.

## Vectores, scores y decisiones

Comparación clave a clave: `resultados/comparaciones/sec-ref-953a436-vs-sec-opt-6b6ef82.json`.

- 0 vectores distintos de 9607.
- 0 scores distintos.
- 0 decisiones distintas de 12 726.
- 0 diferencias de detector o de reglas.

## Categorías de los 25 episodios

Con las 7 configuraciones (IF y HIB a α = 0,05 / 0,03 / 0,01, y HEUR). Los tres valores de α se conservan; no se elige ninguno.

- **`953a436` secuencial frente a `6b6ef82` secuencial:** 0 diferencias de categoría en los 25 episodios (`resultados/comparaciones/25-publicado-vs-ref-vs-opt.json`, par `ref_vs_cand`).
- **Población principal:** 15/25 en las dos, con las mismas exclusiones.
- **Análisis publicado del cierre técnico frente a las corridas secuenciales:** 4 diferencias, todas en `escaneo_breve-r3`. En HEUR, HIB_0.05, HIB_0.03 y HIB_0.01 la categoría pasa de `solo_posterior` a `oportuna`. **No se debe al cambio de código**, porque la referencia `953a436` ejecutada sola da lo mismo que la optimizada. Se debe al reloj de coste del replay:

| Corrida | Ventana de la 1.ª señal HEUR | Disponible (UTC) | Fin del episodio (marca) | Categoría |
|---|---|---|---|---|
| Publicada (953a436, replays en paralelo) | 09:38:40 | 09:38:42,798 | 09:38:42,566 | solo_posterior (+0,23 s) |
| `953a436` secuencial | 09:38:40 | 09:38:42,399 | 09:38:42,566 | oportuna (−0,17 s) |
| `6b6ef82` secuencial | 09:38:40 | 09:38:41,915 | 09:38:42,566 | oportuna (−0,65 s) |

La señal, la ventana y la regla son las mismas. Lo que cambia, en menos de un segundo, es cuándo queda disponible el registro, y eso depende de la velocidad del equipo que ejecuta el replay.

**Esto no demuestra que el escaneo breve se detecte y se pueda responder a tiempo.** Es un margen de décimas de segundo en un portátil y no se traslada al Sensor1. La categoría del 3B en vivo revisado sigue siendo `solo_posterior`. La detección del escaneo breve y una respuesta efectiva durante su actividad siguen siendo el **objetivo de la Etapa 3**. No se declara imposible en general, y no se ha alargado ningún ataque.

## Control (07:32–08:05)

| | `953a436` | `6b6ef82` |
|---|---|---|
| Ventanas / denominador | 2622 / 2622 | 2622 / 2622 |
| No evaluadas | 0 | 0 |
| Falsas alarmas IF α = 0,05 / 0,03 / 0,01 | 395 / 254 / 83 | 395 / 254 / 83 |
| HEUR | 92 | 92 |
| HIB α = 0,05 / 0,03 / 0,01 | 466 / 336 / 171 | 466 / 336 / 171 |

El bloque `control_normal` completo coincide campo a campo en las dos versiones (0 diferencias), también por entidad.

## Salidas

- `resultados/analisis-3b-sec-ref-953a436/` y `resultados/analisis-3b-sec-opt-6b6ef82/`: `analisis-3b.json` y `TABLA-3B.md`, con su `.stdout` y su `.stderr`.
- `resultados/comparaciones/`.
