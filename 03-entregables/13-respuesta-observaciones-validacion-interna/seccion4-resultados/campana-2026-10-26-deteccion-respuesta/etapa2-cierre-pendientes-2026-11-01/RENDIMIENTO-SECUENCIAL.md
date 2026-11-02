# Rendimiento: comparación secuencial sin competencia entre replays

## Condiciones

El criterio se fijó **antes** de medir (`CRITERIO-ACEPTACION-RENDIMIENTO.md`, commit `baa6e92`, publicado a las 04:28 UTC). No se ha cambiado después.

| | |
|---|---|
| Máquina | el mismo portátil Windows 11 (Python 3.14.3 del venv `venv-modelo`) para las tres |
| Versiones | referencia `953a436`; candidata `862404e` (corrección de pendientes); optimizada `6b6ef82` (misma lógica, sin trabajo repetido) |
| Arnés | `replay_motor.py` de `4694e38` para las tres (CPU por ciclo, memoria privada y carga del equipo) |
| Entradas | las congeladas del cierre: anillo re-troceado de 5 s y segmento de EVE; modelo `if_limpio_2026_10` |
| Configuración | anillo de 5 s, disparo por eventos, paso 10 s, horizonte 230 s, reloj `coste` |
| Tramo | 07:24:40–10:05:40 completo, con historia previa |
| Orden | una corrida cada vez, sin otros replays ni pruebas en paralelo (`resultados/replays/secuencial-progreso.log`) |
| Perfil por etapas | corridas aparte con `--perfilar`, de 08:05 a 08:40 (inundaciones r1, r4 y r2). **No** se usan para el criterio, porque el perfilado añade coste |

## Equivalencia antes de comparar tiempos

| Comparación | Claves | Vectores distintos | Scores distintos | Decisiones distintas | Reglas o detector distintos | Transiciones de estado |
|---|---|---|---|---|---|---|
| `953a436` frente a `862404e` | 12 773 | 0 de 9607 | 0 | 0 de 12 726 | 0 | 14 `ventana_no_regenerada` → `cancelada`; 33 `sin_registro` → `no_evaluada:no_elegible` (arranque, 07:21) |
| `862404e` frente a `6b6ef82` | 12 773 | 0 de 9607 | 0 | 0 de 12 726 | 0 | ninguna |
| `953a436` frente a `6b6ef82` | 12 773 | 0 de 9607 | 0 | 0 de 12 726 | 0 | las mismas que la primera fila |

Hay además dos pruebas de equivalencia con mutación:

- `test_fila_de_ancla_igual_a_build_rows_global_del_horizonte`: 80 semillas y más de 500 anclas;
- `test_deslizar_igual_a_la_global_con_atribucion`: 40 semillas, con copias diferidas TTL 63 → 64 y ficheros tardíos.

Las dos fallan si se introduce una mutación.

**No se han cambiado** las 28 características, las anclas, el horizonte causal, el modelo, los umbrales α (0,05 / 0,03 / 0,01) ni las reglas.

## Qué se optimizó (`6b6ef82`) y por qué

El perfil de la referencia (08:05–08:40, `resultados/replays/perfil-ref-953a436`) mostraba dos cosas:

- `filas`, la construcción por ancla, ocupaba 267,7 s de 1082 s de pared;
- la deduplicación y la atribución recorrían todo el horizonte en cada ciclo para obtener las diferencias. En el cProfile intermedio: `Deduplicador.actualizar` tardaba 1,9 s por llamada y `Atribuidor.actualizar`, 1,46 s.

Los cambios:

1. **`fila_de_ancla`.** Solo pasa a `build_rows` lo que la fila A lee: paquetes de (A − 30, A], L7 de (A − 60, A], la propia ancla y `capture_start`. Antes pasaba todo el horizonte de 230 s.
2. **`Deduplicador.deslizar` y `Atribuidor.deslizar`.** Salen los presentes con marca de tiempo anterior al corte (por bisección sobre el orden mantenido) y entran solo los contextos llegados desde la llamada anterior. No se recorre el horizonte para saber qué cambió.
3. **Selección de paquetes y L7 por bisección.** Se aplica en cada ancla y en las pendientes.

**Perfil de la optimizada** (mismo tramo, `perfil-opt-6b6ef82`): `filas` baja de 267,7 s a 58,7 s; la pared total, de 1082 s a 576 s. En las tres corridas de perfil, el ciclo de pared máximo (28,1, 26,3 y 13,7 s) es el de arranque a las 08:05, que se pone al día con la historia. No es un ciclo de inundación.

## Resultados frente al criterio (corridas completas secuenciales)

Los segmentos son: normal (07:32–08:05), cada inundación (inicio–fin) y su recuperación (fin a fin + 120 s). En la tabla:

- **R1:** pared p95 ≤ 10 s y máximo ≤ 20 s.
- **R2:** retraso p95 ≤ 15 s y máximo ≤ 25 s.
- **R3:** recuperación.
- **R4:** integridad, sin `pcap_incompleto` ni `ventana_no_regenerada`. Los ausentes se comprueban con el inventario de `analizar_3b.py` (0 en las tres; ver `VALIDACION-25-EPISODIOS-Y-CONTROL.md`).

| Segmento | Version | Ciclos | Pared p50/p95/max (s) | CPU p95/max (s) | >10 s | >20 s | Retraso p95/max (s) | Pendientes max/fin | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| normal | 953a436 (ref) | 396 | 0.562/1.301/1.74 | 1.281/1.641 | 0 | 0 | 2.509/2.842 | 96/67 | si | si | - | si |
| normal | 862404e (cand) | 396 | 0.782/2.049/3.744 | 1.953/2.844 | 0 | 0 | 3.323/4.935 | 96/67 | si | si | - | si |
| normal | 6b6ef82 (opt) | 396 | 0.546/1.153/1.597 | 1.125/1.594 | 0 | 0 | 2.383/2.733 | 96/67 | si | si | - | si |
| inundacion_http-r1 | 953a436 (ref) | 18 | 2.65/6.545/6.545 | 6.047/6.047 | 0 | 0 | 7.584/7.584 | 77/66 | si | si | - | si |
| inundacion_http-r1 | 862404e (cand) | 18 | 3.607/8.191/8.191 | 7.906/7.906 | 0 | 0 | 10.355/10.355 | 77/70 | si | si | - | si |
| inundacion_http-r1 | 6b6ef82 (opt) | 18 | 2.798/5.412/5.412 | 5.344/5.344 | 0 | 0 | 6.612/6.612 | 77/68 | si | si | - | si |
| recuperacion-r1 | 953a436 (ref) | 24 | 2.364/6.28/6.639 | 4.781/4.859 | 0 | 0 | 7.851/7.851 | 71/62 | si | si | si | si |
| recuperacion-r1 | 862404e (cand) | 24 | 3.428/5.349/6.048 | 5.25/5.891 | 0 | 0 | 7.214/7.214 | 72/62 | si | si | si | si |
| recuperacion-r1 | 6b6ef82 (opt) | 24 | 1.738/3.37/3.855 | 3.297/3.438 | 0 | 0 | 4.998/4.998 | 71/62 | si | si | si | si |
| inundacion_http-r2 | 953a436 (ref) | 15 | 3.58/11.397/11.397 | 9.5/9.5 | 1 | 0 | 12.639/12.639 | 81/70 | **NO** | si | - | si |
| inundacion_http-r2 | 862404e (cand) | 18 | 4.408/6.989/6.989 | 6.719/6.719 | 0 | 0 | 8.211/8.211 | 77/69 | si | si | - | si |
| inundacion_http-r2 | 6b6ef82 (opt) | 18 | 2.942/5.545/5.545 | 5.359/5.359 | 0 | 0 | 6.552/6.552 | 76/69 | si | si | - | si |
| recuperacion-r2 | 953a436 (ref) | 23 | 3.085/7.239/7.394 | 6.234/6.438 | 0 | 0 | 8.756/8.756 | 74/64 | si | si | si | si |
| recuperacion-r2 | 862404e (cand) | 24 | 1.937/3.986/6.881 | 3.766/6.797 | 0 | 0 | 7.917/7.917 | 74/64 | si | si | si | si |
| recuperacion-r2 | 6b6ef82 (opt) | 24 | 1.734/2.916/3.973 | 2.828/3.891 | 0 | 0 | 5.064/5.064 | 74/64 | si | si | si | si |
| inundacion_http-r3 | 953a436 (ref) | 18 | 2.92/7.65/7.65 | 7.438/7.438 | 0 | 0 | 8.739/8.739 | 73/67 | si | si | - | si |
| inundacion_http-r3 | 862404e (cand) | 13 | 3.967/14.425/14.425 | 13.875/13.875 | 4 | 0 | 30.854/30.854 | 72/72 | **NO** | **NO** | - | si |
| inundacion_http-r3 | 6b6ef82 (opt) | 18 | 2.687/6.151/6.151 | 6.031/6.031 | 0 | 0 | 7.268/7.268 | 72/67 | si | si | - | si |
| recuperacion-r3 | 953a436 (ref) | 24 | 2.432/4.067/4.495 | 3.969/4.391 | 0 | 0 | 5.615/5.615 | 71/60 | si | si | si | si |
| recuperacion-r3 | 862404e (cand) | 18 | 4.329/17.79/17.79 | 17.5/17.5 | 2 | 0 | 25.04/25.04 | 71/60 | **NO** | **NO** | si | si |
| recuperacion-r3 | 6b6ef82 (opt) | 24 | 1.843/3.231/3.97 | 3.172/3.891 | 0 | 0 | 5.119/5.119 | 71/60 | si | si | si | si |
| inundacion_http-r4 | 953a436 (ref) | 18 | 2.377/5.573/5.573 | 5.406/5.406 | 0 | 0 | 6.805/6.805 | 71/65 | si | si | - | si |
| inundacion_http-r4 | 862404e (cand) | 18 | 2.826/8.185/8.185 | 8.125/8.125 | 0 | 0 | 9.246/9.246 | 71/64 | si | si | - | si |
| inundacion_http-r4 | 6b6ef82 (opt) | 18 | 2.32/5.595/5.595 | 5.5/5.5 | 0 | 0 | 6.835/6.835 | 71/65 | si | si | - | si |
| recuperacion-r4 | 953a436 (ref) | 24 | 2.648/4.595/4.681 | 4.438/4.547 | 0 | 0 | 5.781/5.781 | 76/58 | si | si | si | si |
| recuperacion-r4 | 862404e (cand) | 24 | 3.195/6.217/6.825 | 6.078/6.734 | 0 | 0 | 7.861/7.861 | 78/58 | si | si | si | si |
| recuperacion-r4 | 6b6ef82 (opt) | 24 | 1.573/2.946/3.723 | 2.828/3.672 | 0 | 0 | 4.881/4.881 | 76/58 | si | si | si | si |
| inundacion_http-r5 | 953a436 (ref) | 16 | 3.495/9.836/9.836 | 9.391/9.391 | 0 | 0 | 12.475/12.475 | 77/76 | si | si | - | si |
| inundacion_http-r5 | 862404e (cand) | 13 | 5.623/12.274/12.274 | 12.109/12.109 | 4 | 0 | 18.96/18.96 | 75/75 | **NO** | **NO** | - | si |
| inundacion_http-r5 | 6b6ef82 (opt) | 18 | 2.53/6.085/6.085 | 5.984/5.984 | 0 | 0 | 7.194/7.194 | 76/76 | si | si | - | si |
| recuperacion-r5 | 953a436 (ref) | 24 | 2.006/3.892/3.993 | 3.734/3.781 | 0 | 0 | 5.17/5.17 | 80/60 | si | si | si | si |
| recuperacion-r5 | 862404e (cand) | 22 | 4.196/7.167/10.797 | 6.969/10.391 | 1 | 0 | 16.376/16.376 | 82/60 | si | **NO** | si | si |
| recuperacion-r5 | 6b6ef82 (opt) | 24 | 1.617/2.795/3.217 | 2.75/3.141 | 0 | 0 | 4.326/4.326 | 80/60 | si | si | si | si |

Cumple todo: 953a436 (ref) = NO, 862404e (cand) = NO, 6b6ef82 (opt) = SI

### Etapas del motor (suma en s sobre todos los segmentos medidos)

| Etapa | 953a436 (ref) | 862404e (cand) | 6b6ef82 (opt) |
|---|---|---|---|
| decision_y_registro | 0.0 | 0.1 | 0.1 |
| eve_lectura | 15.8 | 19.1 | 23.2 |
| eve_poda | 0.1 | 0.1 | 0.1 |
| expiracion_y_escritura | 0.5 | 0.6 | 0.7 |
| filtro_plano_control | 16.3 | 21.1 | 30.9 |
| pcap_parseo | 66.9 | 85.0 | 100.1 |
| pcap_poda | 67.0 | 101.9 | 85.8 |
| pendientes | 50.2 | 70.5 | 44.4 |
| puntuacion | 14.6 | 18.8 | 22.0 |
| ventanas_por_ancla | 545.3 | 743.3 | 373.0 |

### Memoria y carga del equipo (maximos sobre los segmentos)

| Version | RSS max (MB) | Privada max (MB) | CPU sistema p50 (%) | CPU sistema max (%) | Memoria del equipo max (%) | Disponible min (MB) | Confirmada max / limite (MB) |
|---|---|---|---|---|---|---|---|
| 953a436 (ref) | 1168.3 | 1981.4 | 32.6 (normal) | 83.5 | 97 | 647 | 59850 / 68471 |
| 862404e (cand) | 1167.1 | 1981.0 | 31.5 (normal) | 79.3 | 89 | 3504 | 59227 / 68471 |
| 6b6ef82 (opt) | 1136.2 | 1951.1 | 36.2 (normal) | 66.9 | 84 | 5152 | 61048 / 68471 |

## Totales de las corridas completas

| Versión | Pared total (s) | CPU total (s) | `ventanas_por_ancla` (s) | Ciclos > 10 s en inundación o recuperación | Ciclos > 20 s |
|---|---|---|---|---|---|
| `953a436` | 2286 | 2169 | 1577 | 1 (r2) | 0 |
| `862404e` | 3122 | 3018 | 2141 | 11 (r3, r5 y sus recuperaciones) | 0 |
| `6b6ef82` | 1825 | 1777 | 996 | 0 | 0 |

## Lectura

- **La referencia `953a436` no cumplía el criterio.** Ejecutada sola, falla R1 en `inundacion_http-r2`: un ciclo de 11,4 s; con 15 ciclos en el segmento, el p95 coincide con el máximo. En la medición en paralelo del cierre técnico, el máximo había llegado a 23,1 s. La diferencia muestra cuánto pesaba la competencia entre replays.
- **La candidata `862404e` tampoco lo cumplía** (R1 y R2 en r3 y r5). Hace el mismo trabajo que la referencia: sus vectores son idénticos y no añade etapas caras. Aun así, gasta un 37 % más de CPU, y **todas** las etapas, incluidas las que no se tocaron (`pcap_parseo`, `pcap_poda`), van entre un 27 y un 52 % más lentas. Eso indica un cambio del entorno del portátil durante esa corrida (frecuencia o temperatura, aplicaciones abiertas), no un coste de la corrección. Se informa tal cual y no se descarta la corrida.
- **La optimizada `6b6ef82` cumple R1–R4 en los 11 segmentos.**
  - El peor ciclo en inundación es de 6,15 s (r3), y ningún ciclo supera 10 s.
  - El retraso máximo de decisión es 7,27 s.
  - Tras cada inundación, el retraso vuelve de inmediato a ≤ p95 del normal + 5 s (7,38 s), y las pendientes acaban por debajo del máximo del normal (96).
- **Ruido del portátil.** Las etapas que no se tocaron sirven de testigo: en `6b6ef82`, `pcap_parseo` y `filtro_plano_control` van entre un 50 y un 90 % **más lentas** que en la referencia. Es decir, la optimizada no se midió en un entorno más favorable. La mejora viene de `ventanas_por_ancla` (545 s → 373 s en los segmentos medidos) y de `pendientes` (50 s → 44 s).
- **Memoria y carga del equipo.**
  - El RSS máximo del replay fue similar en las tres (1136–1168 MB) y la memoria privada no superó 2,0 GB.
  - La carga de memoria del equipo llegó al 97 % (647 MB disponibles) durante r5 en la corrida de la referencia, y al 84 % en la optimizada. La memoria confirmada no llegó al límite en ninguna (máx. 61 048 de 68 471 MB).
  - La CPU del sistema (todos los procesos) tuvo una mediana del 31–36 % en el tramo normal en las tres. Hubo otras aplicaciones abiertas durante toda la medición, y eso se registra ciclo a ciclo en `ciclos-arnes.jsonl.gz` (`cpu_sistema_pct`, `mem_carga_pct`, `mem_disponible_mb`, `confirmada_mb`).
- **Pausas.** Ninguna pausa entre escrituras se trató como pérdida. R4 y el inventario (0 ausentes, 0 `ventana_no_regenerada`) se comprobaron por ventana.

## Alcance

**Resuelto offline** (portátil, `--factor-cpu 1`): con la optimizada, el motor cumple el criterio fijado de antemano en las 5 inundaciones HTTP y sus recuperaciones, con resultados idénticos.

**Pendiente en el Sensor1:** estas cifras **no** son una garantía para el Sensor1. El sensor tiene otra CPU y otra memoria, y además ejecuta Suricata y tcpdump. El mismo criterio R1–R4 tendrá que medirse allí, en vivo, cuando se autorice instalar la versión. Esa instalación no se ha hecho en este encargo.
