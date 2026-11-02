# Validación offline de los 25 episodios del 3B (punto 6 del cierre técnico)

## 1. Qué se ejecutó

Dos replays completos del 3B (07:24:40–10:05:40 UTC) con el motor de la rama candidata (`953a436`). El modelo es `if_limpio_2026_10` (sha256 `df547da0…`) y el contrato de 28 características no cambia. Los dos replays son:

| Replay | Captura | Disparo | Qué representa |
|---|---|---|---|
| `completo-ref-orig15-periodico` | archivo PCAP original del 3B (ficheros de 15 s) | periódico, 10 s | la configuración del 3B en vivo con el motor nuevo |
| `completo-cand-e5-eventos` | el mismo PCAP re-troceado a 5 s (`trocear_pcap.py`: 2535 ficheros, 9 579 930 paquetes, registros idénticos al original) | por eventos (cierre de PCAP) | la candidata de la Etapa 2 |

El análisis usa `analizar_3b.py` **sin modificar**, con los mismos insumos que la revisión 3B:

- marcas;
- `config-campana-3b.json`;
- `destinos-3b.csv`;
- `calidad-fuentes.json`;
- `integridad-v2.json`;
- control de 07:32 a 08:05;
- rango del inventario de 07:24:40 a 10:05:30.

El propio replay hace de registro «en vivo» y de inventario, y su `ciclos.jsonl` da la disponibilidad de cada registro (reloj simulado por coste).

**No se cambia ningún criterio.** Se informan los 25 episodios planificados, se conservan las exclusiones por pérdidas de Suricata (fuente degradada) y por integridad, y no se extrapola nada fuera de estos datos.

**Qué no mide un replay.** Los tiempos de disponibilidad salen del coste medido en el portátil, con 4 replays en paralelo; no son tiempos del Sensor1. Un replay tampoco mide la entrega por SSH, la aplicación en el destino ni el efecto: eso se separa en el README (§4).

## 2. Resultado global

| | 3B en vivo (revisado) | Replay ref (15 s, periódico) | Replay cand (5 s, eventos) |
|---|---|---|---|
| Población principal | 15/25 | 15/25 | 15/25 |
| Episodios fuera, con el mismo motivo | 10 | 10 (idénticos) | 10 (idénticos) |
| Inventario: requeridas / a tiempo / no evaluadas / ausentes | — | 12 223 / 12 209 / 14 / 0 | 12 223 / 12 209 / 14 / 0 |
| Diferencias de categoría con el vivo (25 episodios × 7 configuraciones) | — | 6 (todas de `escaneo_breve-r1`) | **0** |
| Vectores distintos entre ref y cand (07:29–10:04) | — | referencia | **0 de 9244** (y 0 scores, reglas o clases α distintos en 12 226 claves) |

**Fuera de la población principal (10):**

- integridad no apta: inundacion_http-r1 y escaneo_sostenido-r1;
- fuente degradada e integridad no apta: dns_inusual-r3, inundacion_http-r2, r3 y r4, fuerza_bruta_http-r2 y r3, dns_inusual-r5 y escaneo_breve-r4.

Son los mismos que en `revision-3b-2026-11-01/TABLA-3B.md`. La integridad v2 incluye la continuidad del motor en vivo: se conserva tal cual porque así lo exige el encargo, aunque el replay no tenga esa limitación.

**Las 14 no evaluadas** (`ventana_no_regenerada`) son iguales en ref y cand. Ninguna es del origen de ensayo ni cae en el control. Ver el README, §6.3.

## 3. Por episodio (replay candidato; categorías idénticas al 3B en vivo revisado)

Tiempos: «1.ª» es la disponibilidad del primer registro con señal atribuible, en segundos desde el inicio del episodio. En vivo: `ciclos.jsonl` del sensor. En cand: el reloj simulado del replay.

| Episodio | Principal | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 | 1.ª IF 0,05 vivo / cand (s) | 1.ª HEUR vivo / cand (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 26.6 / 24.2 | 26.6 / 24.2 |
| inundacion_http-r1 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 24.9 / 9.2 | 24.9 / 9.2 |
| dns_inusual-r3 | no | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | — / — | 20.2 / 7.6 |
| inundacion_http-r4 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 24.2 / 9.0 | 24.2 / 9.0 |
| inundacion_http-r2 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 25.4 / 11.7 | 25.4 / 11.7 |
| inundacion_http-r3 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 25.4 / 10.0 | 25.4 / 10.0 |
| escaneo_sostenido-r4 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 22.0 / 19.3 | 22.0 / 19.3 |
| escaneo_sostenido-r5 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 35.6 / 22.5 | 35.6 / 22.5 |
| escaneo_breve-r5 | sí | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 39.5 / 26.1 | 39.5 / 26.1 |
| fuerza_bruta_http-r3 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 23.6 / 9.2 | 23.6 / 9.2 |
| fuerza_bruta_http-r5 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 23.7 / 10.0 | 23.7 / 10.0 |
| dns_inusual-r5 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 21.9 / 19.0 | 21.9 / 9.2 |
| escaneo_sostenido-r3 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 22.0 / 8.5 | 22.0 / 17.9 |
| dns_inusual-r2 | sí | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | — / — | 25.8 / 13.3 |
| fuerza_bruta_http-r2 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 18.8 / 4.2 | 18.8 / 4.2 |
| fuerza_bruta_http-r4 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 18.4 / 4.4 | 18.4 / 4.4 |
| dns_inusual-r1 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 17.2 / 14.2 | 17.2 / 14.2 |
| escaneo_breve-r1 | sí | oportuna* | oportuna* | solo_posterior | oportuna* | oportuna* | oportuna* | oportuna* | 16.4 / 13.5 | 16.4 / 13.5 |
| escaneo_breve-r4 | no | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 28.8 / 25.6 | 28.8 / 25.6 |
| escaneo_breve-r3 | sí | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 40.9 / 27.7 | 30.7 / 17.8 |
| dns_inusual-r4 | sí | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | ausencia_con_observacion_suficiente | oportuna | oportuna | oportuna | oportuna | — / — | 23.9 / 11.1 |
| fuerza_bruta_http-r1 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 25.1 / 11.5 | 25.1 / 11.5 |
| inundacion_http-r5 | sí | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 29.3 / 13.1 | 29.3 / 13.1 |
| escaneo_breve-r2 | sí | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 26.2 / 22.8 | 26.2 / 22.8 |
| escaneo_sostenido-r1 | no | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 39.6 / 23.9 | 39.6 / 23.9 |

\* `escaneo_breve-r1` es «oportuna» con los criterios congelados, pero **la señal no es del escaneo**. Lo explica la §4.

La tabla se genera con `herramientas/tablas_cierre.py`, que falla si alguna categoría difiere del 3B en vivo revisado.

**En la población principal (15 episodios, candidata):**

- **Detección durante el ataque** (oportuna, IF 0,05 / HEUR): escaneo_sostenido-r2, r3, r4 y r5; fuerza_bruta_http-r1, r4 y r5; dns_inusual-r1; inundacion_http-r5. En dns_inusual-r2 y r4 solo HEUR (`dns_entropy`); el IF a los tres α da `ausencia_con_observacion_suficiente`.
- **Después del ataque** (solo_posterior): escaneo_breve-r2, r3 y r5.
- **Ausencia con observación suficiente:** IF en dns_inusual-r2 y r4 (los tres α), e IF 0,01 en escaneo_breve-r3 y r5.
- **No evaluable** dentro de la población principal: ninguno.
- **escaneo_breve-r1:** ver la §4.

## 4. Los 5 escaneos breves (desglose)

Origen 10.10.20.30, destino 10.10.30.10, comando `nmap -sT -T4 --max-retries 1 -p 1-1000`. Ráfaga medida en el PCAP archivado (`herramientas/desglose_breves.py`); primera ventana con `port_scan` en el replay candidato:

| Escaneo | Ráfaga principal (UTC) | Fin (marca) | 1.ª ventana port_scan | Disponible (cand) | Respecto al fin | Otras señales disponibles antes del fin |
|---|---|---|---|---|---|---|
| escaneo_breve-r1 | 09:31:02.521–09:31:06.841 (4,319 s, 2014 SYN) | 09:31:06.98 | 09:31:10 | 09:31:12.89 | +5,9 s | brute_force (ver abajo) |
| escaneo_breve-r2 | 09:57:25.203–09:57:29.920 (4,717 s, 2014 SYN) | 09:57:30.04 | 09:57:30 | 09:57:34.86 | +4,8 s | — |
| escaneo_breve-r3 | 09:38:38.108–09:38:42.429 (4,321 s, 2017 SYN) | 09:38:42.56 | 09:38:40 | 09:38:42.79 | +0,2 s | — |
| escaneo_breve-r4 | 09:34:50.127–09:34:54.844 (4,717 s, 2013 SYN) | 09:34:54.97 | 09:35:00 | 09:35:02.62 | +7,6 s | — |
| escaneo_breve-r5 | 08:47:40.070–08:47:44.789 (4,719 s, 2014 SYN) | 08:47:44.91 | 08:47:50 | 08:47:53.07 | +8,2 s | — |

**Estructura de cada escaneo:** unos 13 s antes de la ráfaga hay 2 SYN de descubrimiento de host. La ráfaga útil dura de 4,3 a 4,7 s, con unos 2014 SYN a 1000 puertos y un pico de 728 a 760 SYN/s.

**Primera señal del escaneo.** En los 5 llega después del fin: entre +0,2 s (r3) y +8,2 s (r5), en el reloj del replay. En r3, la ventana de 09:38:40 cierra con la ráfaga aún en curso; el registro queda disponible 0,2 s después del fin. Es el caso más cercano a «durante», pero no lo es.

**escaneo_breve-r1.** La señal que el analizador cuenta como oportuna es la regla `brute_force`, en la ventana de 09:31:00, que termina **antes** de la ráfaga. Su motivo: «5 req HTTP/60s con 100% de fallo de auth». En el EVE archivado, el origen envió 40 peticiones `curl/8.17.0 GET /auth` (401) al puerto 18081 entre 09:30:53 y 09:31:10, en paralelo al escaneo.

Esa ventana es «atribuible» con el criterio congelado porque contiene los 2 SYN de descubrimiento hacia el destino. Se mantiene la categoría (no se cambian criterios), pero la conclusión correcta es que **el escaneo r1 tampoco se detectó durante el ataque**.

La procedencia de ese curl no consta en `marcas.jsonl` y no se determina con la evidencia archivada. En r2 hay 15 peticiones HTTP del origen en la misma franja relativa, sin efecto en las categorías. Esto corrige la lectura del informe del 3B («hay señal antes del fin (16,4 s)»): ver `CONCLUSIONES-CORREGIDAS.md`, C10.

**Conclusión.** Se limita a esta candidata (ficheros de 5 s, ventanas de 10 s, disparo por eventos) y a estos 5 episodios: ninguna ráfaga de unos 4,5 s se señala como escaneo antes de terminar. Las alternativas de la Etapa 3 siguen en `CONCLUSIONES-CORREGIDAS.md`, §2.

## 5. Control normal y alarmas sobre otras entidades

### 5.1 Control (07:32–08:05), según `analizar_3b.py`

| Configuración | Vivo (2644 ventanas) | Replay ref (2622) | Replay cand (2622) |
|---|---|---|---|
| IF 0,05 | 395 (14,9 %) | 395 (15,1 %) | 395 (15,1 %) |
| IF 0,03 | 254 (9,6 %) | 254 (9,7 %) | 254 (9,7 %) |
| IF 0,01 | 83 (3,1 %) | 83 (3,2 %) | 83 (3,2 %) |
| HEUR | 92 (3,5 %) | 92 (3,5 %) | 92 (3,5 %) |
| HIB 0,05 / 0,03 / 0,01 | 466 / 336 / 171 | 466 / 336 / 171 | 466 / 336 / 171 |

Las falsas alarmas son **idénticas** en número. El denominador baja de 2644 a 2622 porque la candidata no registra 22 ventanas vacías dentro de huecos de más de 60 s; son todo ceros, PERMIT y sin score.

**Reparto de las alarmas del control** (`resultados/comparaciones/alarmas-otras-entidades-cand.json`):

- HEUR: 88 `dns_entropy` sobre DC1 (10.10.10.20) y 4 `http_abuse` sobre 10.10.20.26.
- IF 0,05: sobre todo 10.10.20.22 (171), 10.10.20.24 (124) y 10.10.20.26 (46).

### 5.2 Durante los episodios

Se cuentan las señales sobre entidades distintas del origen de ensayo, con `window_end` en (inicio, fin + 60) y sumadas sobre los 25 episodios:

- 4127 ventanas;
- IF 0,05: 602; IF 0,01: 127;
- HEUR: 132.

El desglose por episodio y por entidad está en el mismo fichero. Estas alarmas no se atribuyen al ataque y no cuentan como detección.

## 6. Rendimiento y memoria en la inundación HTTP

Replays en el portátil (Python 3.14.3, sklearn 1.9.0), con 4 replays en paralelo; no son cifras del Sensor1. Ciclos con inicio en [inicio, fin + 60] (`resultados/comparaciones/rendimiento-*.json`):

| Episodio | Ciclo p50 / máx (s), ref | Ciclo p50 / máx (s), cand | Latencia de decisión p50 / p90 / máx (s), ref | Latencia p50 / p90 / máx (s), cand | Pico de memoria (MB), cand |
|---|---|---|---|---|---|
| control | 1,92 / 6,43 | 0,80 / 3,70 | 14,9 / 16,5 / 19,4 | 2,8 / 3,6 / 4,8 | 536 |
| inundacion_http-r1 | 5,17 / 11,46 | 3,62 / 8,18 | 19,4 / 23,7 / 24,5 | 6,2 / 8,6 / 9,2 | 1213 |
| inundacion_http-r2 | 8,05 / 17,73 | 5,78 / 13,70 | 27,8 / 37,5 / 38,2 | 8,6 / 16,1 / 17,0 | 1218 |
| inundacion_http-r3 | 14,80 / 24,51 | 5,96 / 18,18 | 34,3 / 49,2 / 54,3 | 12,4 / 21,5 / 29,9 | 1218 |
| inundacion_http-r4 | 6,06 / 12,52 | 2,92 / 6,70 | 19,6 / 29,1 / 29,2 | 5,6 / 7,5 / 7,9 | 1218 |
| inundacion_http-r5 | 9,10 / 23,72 | 6,32 / 23,14 | 32,0 / 49,1 / 51,7 | 14,8 / 32,6 / 37,8 | 1218 |

- **Memoria.** El pico de todo el replay es de 1218–1223 MB (ref y cand) y se alcanza en la inundación. En el control es de unos 536 MB.
- **Continuidad.** Durante las inundaciones hay ciclos de más de 20 s: en la referencia, en r3 (24,5 s) y r5 (23,7 s); en la candidata, en r5 (23,1 s). Es la continuidad ≤ 20 s que el 3B ya había señalado. **No queda resuelta** con esta candidata; se informa, no se oculta.
- **El coste por ventana es mayor que en `2be5335`.** El horizonte fijado por ventana obliga a atribuir por ancla. Medido en 08:31–08:37, `ventanas_por_ancla` suma unos 124 s de 165 s de coste total. El margen en el Sensor1 queda **pendiente en vivo**.

## 7. Qué cierra y qué no

- **Cerrado (replay).**
  - Con el motor candidato, el replay reproduce las 25 × 7 categorías del 3B en vivo revisado y las falsas alarmas del control.
  - La captura de 5 s con disparo por eventos y la de 15 s periódica dan contenido idéntico: vectores, scores, reglas y clases.
- **No cerrado.**
  - La continuidad ≤ 20 s durante las inundaciones (r5 en la candidata; r3 y r5 en la referencia).
  - La detección del escaneo breve durante el ataque (Etapa 3).
  - Cualquier cifra del Sensor1: latencia real, SSH y efecto en el destino.
