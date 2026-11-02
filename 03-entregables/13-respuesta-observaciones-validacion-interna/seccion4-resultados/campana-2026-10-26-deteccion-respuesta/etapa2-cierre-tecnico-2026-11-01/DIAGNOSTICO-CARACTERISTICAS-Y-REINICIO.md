# Diagnóstico de características, scores y reinicio (puntos 4 y 5 del cierre técnico)

Código: rama `candidato/etapa2-20261101`, commits `3083f60` (horizonte por ventana, reanudación) y `953a436` (regla de registro de 60 s). Entorno del modelo: venv con Python 3.14.3, scikit-learn 1.9.0 y numpy 2.5.1, sin `InconsistentVersionWarning`. El modelo, el escalador y el contrato de 28 características (9 L3, 8 L4, 11 L7) no se tocan. No se reentrena ni se recalibra.

Las cifras de este documento salen de los replays de `resultados/replays/`. Las comparaciones están en `resultados/comparaciones/` y se generan con `herramientas/comparar_cierre.py`.

## 1. Síntoma (entrega anterior)

En el tramo 08:40–09:05 del 3B, la misma ventana (entidad, `window_end`) producía vectores distintos según la configuración de captura y disparo:

- r2 (ficheros de 15 s, periódico) frente a r4 (5 s, eventos): 215 vectores distintos.
- La deriva más visible era `flow_duration_mean_30s` (P-5).

La entrega anterior lo atribuyó a la «disponibilidad». No era la causa.

## 2. Causa exacta

`attribute_packets` (congelada, compartida con el entrenamiento) recorre los paquetes que recibe y fija, sobre **esa** entrada:

1. el inicio de cada flujo (primer paquete visto del flujo);
2. su propietario (qué extremo es la entidad: la inversión depende del primer paquete);
3. si un paquete cuenta como `flow_attempt`;
4. qué secuencias TCP ya se vieron (retransmisiones).

Hasta `2be5335`, el motor podaba su anillo a `history_seconds` (230 s) **desde el paquete más nuevo leído**. Por tanto, la entrada con la que se calculaba la ventana W empezaba en `más_nuevo − 230`, y `más_nuevo` dependía de cuándo se decidía:

- de la rotación (5 o 15 s);
- del retraso de cierre;
- de si el ciclo era periódico o por eventos;
- de un reinicio.

Un flujo que empezó antes de ese corte se veía «empezar» en el primer paquete que quedaba dentro. Así cambiaban su duración, su propietario y sus intentos.

## 3. Corrección

- **Horizonte fijado por ventana.** La ventana W se calcula siempre con la entrada `[W − 230 s, …]`, con las anclas procesadas en orden ascendente (`ventanas_por_ancla` en `motor_decision.py`). `attribute_packets` es causal: los paquetes posteriores a W no cambian lo que fija sobre `(W − 60, W]`. Se mantienen el deduplicador y el atribuidor incrementales, y la fórmula de las características no cambia.
- **No se usa `flow.age`.** La duración sigue saliendo de los paquetes observados, como en el entrenamiento.
- **Verificación por ancla.** `comprobar_ancla` (en `motor_incremental.py`) recalcula cada ventana con la vía global congelada (deduplicación, atribución, EVE y `build_rows` sobre todas las observaciones del horizonte) y compara campo a campo.

### 3.1 Conjunto de registros

El horizonte por ventana obliga a decidir qué ventanas se generan sin mirar el futuro:

- **Antes:** `build_rows` generaba todas las anclas entre la primera y la última observación de la entidad en el buffer. La última dependía de paquetes posteriores a la ventana (no causal). Por eso había ventanas vacías que aparecían o no según la rotación.
- **Ahora:** una ventana (E, A) se registra si E tiene algún paquete o evento L7 en (A − 60, A] (`REGISTRO_S`).
  - Los paquetes de (A − 60, A − 30] no entran en ningún conteo de A: solo hacen que se registre la ventana vacía (PERMIT, score nulo) que sigue al último paquete, como hacía el motor en vivo.
  - Sin esta regla (versión intermedia, sin publicar como resultado), el análisis del 3B perdía las ventanas de la rejilla del origen entre fin + 30 y fin + 60. En vivo, todos los episodios tenían de 5 a 6 ventanas con 0 paquetes en 10 s después del fin: 24 episodios con 5 y 1 con 6. La población principal habría caído por un cambio de registros, no por la detección. Por eso se añadió la regla.
- **Diferencia que queda frente al motor anterior.** Las ventanas vacías dentro de huecos de más de 60 s de una entidad ya no se registran. Son todo ceros, PERMIT y sin score: no pueden dar señal en ninguna configuración. Se cuantifican en `resultados/comparaciones/`.

### 3.2 Diferencia de contrato previa (no introducida ahora)

Ver la sección 5.4: la diferencia existe, pero lo medido **no justifica reentrenar**.

## 4. Reinicio (r7 de la entrega anterior)

**Síntoma.** Tras el reinicio a las 08:50:00, 16 decisiones cambiaban durante unos 50 s.

**Causa exacta** (doble):

1. `EveTail` arrancaba al final de `eve.json`. Las ventanas posteriores al arranque no tenían las L7 de sus 60 s previos.
2. El buffer de PCAP se reconstruía con el horizonte del instante del arranque, no con el de la siguiente ventana por decidir.

**Corrección.**

- El motor lee la última ventana registrada (`ancla_reanudada`, sacada de `scored_windows`). Si el hueco no supera `history_seconds + --recuperacion-max-segundos` (600 s), reanuda desde la ventana siguiente.
- `EveTail(desde=…)` rebobina `eve.json` por bloques hasta la primera línea con marca ≥ `desde − 30 s`: `recuperacion_eve` registra el offset, los bytes y si la recuperación fue completa.
- El anillo se relee desde `ancla_siguiente − 230 s`, limitado por la retención.
- Cada decisión lleva `historial_completo`. Vale false si su horizonte empieza antes del primer dato disponible tras el arranque.
- Si el hueco es mayor que el límite, se registra `hueco_arranque` y las ventanas del hueco no se inventan.

**Sin duplicados ni información futura:**

- `scored_windows` se recarga del registro y las anclas posteriores a `ancla_hecha` se tratan una sola vez.
- El ancla solo se procesa si el PCAP cerrado la cubre más el margen de deduplicación (`marca_pcap − 0,005 ≥ A`).

## 5. Resultados

Comparador: `herramientas/comparar_cierre.py`, con tolerancia 0 (el extractor es determinista: cualquier diferencia de bits cuenta). Se compara sobre las claves (entidad, ventana) del rango indicado.

### 5.1 Tramo 08:41–09:04: siete configuraciones de captura y disparo

Referencia: r2 (anillo de 15 s, periódico).

| Replay | Código nuevo: claves comunes / solo en uno | Código nuevo: vectores distintos | Código nuevo: scores, reglas y clases distintos | Latencia p50 / p90 (s) | Código anterior (`tramo-*`): vectores distintos / reglas distintas / clase α 0,05 distinta |
|---|---|---|---|---|---|
| r1 archivo original 15 s, periódico | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 16,7 / 26,4 | 11 / 0 / 0 |
| r3 5 s, periódico | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 9,5 / 11,8 | 147 / 0 / 1 |
| r4 5 s, eventos | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 4,3 / 6,1 | 162 / 0 / 0 |
| r5 15 s, eventos | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 9,3 / 16,0 | 0 / 0 / 0 |
| r6 5 s, eventos, retraso de cierre 3 s | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 7,3 / 8,9 | 162 / 0 / 0 |
| r7 5 s, eventos, reinicio a las 08:50:00 | 1842 / 0 | 0 de 1400 | 0 / 0 / 0 | 4,3 / 5,8 | 198 / 4 / 7 |

Ficheros: `resultados/comparaciones/tramo-cierre.json` y `tramo-anterior.json`. Las latencias son del replay en el portátil, con varios replays en paralelo.

**Código nuevo frente a la entrega anterior, en r2** (`r2-vs-r3-y-anterior.json`):

- 170 vectores distintos de 1400 y 152 scores distintos;
- 0 reglas, 0 clases α y 0 decisiones ALERT/PERMIT distintas.

La única ventana con detector distinto es 10.10.30.10 a las 08:44:00. El código anterior le atribuía 5 paquetes por la inversión de propietario; ahora queda vacía. Es PERMIT en los dos casos.

**Claves que no coinciden con la entrega anterior:**

- 96 solo en el anterior: 85 vacías (score nulo) y 11 con paquetes de 10.10.30.10 por la misma inversión.
- 34 solo en el nuevo: todas vacías y PERMIT.

### 5.2 Reinicios durante cada tipo de tráfico (r8)

r8 frente a r8ref, ambos con anillo de 5 s y disparo por eventos, en 08:34–09:04. Hay 6 reinicios: 08:34:12 (inundación HTTP r3), 08:38:47 (escaneo sostenido r4), 08:45:05 (tráfico normal), 08:47:41 (escaneo breve r5), 08:52:03 (fuerza bruta HTTP r3) y 09:02:01 (DNS inusual r5).

- **Claves:** 2378/2378 comunes, con 0 duplicados, 0 perdidas y 0 no evaluadas.
- **Contenido:** 0 de 1822 vectores distintos, y 0 scores, reglas o clases distintos.
- **Reanudación:** cada arranque reanudó desde la ventana siguiente a la última registrada (`ancla_reanudada`). La recuperación de EVE fue completa en los 6, con entre 14 771 y 73 444 líneas releídas, y no hubo ningún `hueco_arranque`.
- **Historial:** todas las decisiones desde 08:34 llevan `historial_completo = true`.

Fichero: `r8-vs-r8ref.json`.

### 5.3 Replay completo del 3B

`completo-cand-e5-eventos` frente a `completo-ref-orig15-periodico`, en 07:29–10:04:

- 12 226/12 226 claves comunes;
- 0 de 9244 vectores distintos;
- 0 scores, reglas o clases α distintos;
- 14 no evaluadas en cada uno, iguales en los dos.

Fichero: `completo-cand-vs-ref.json`. El análisis de los 25 episodios está en `VALIDACION-3B-25-EPISODIOS.md`.

### 5.4 `flow_duration_mean_30s` frente al entrenamiento: ¿hay que reentrenar?

**1. La diferencia existe.**

- **Entrenamiento.** `acumular_v3.py` extrae en pasadas periódicas sobre el anillo de captura (`retener_minutos = 15`, con poda cada 5 min). Cada pasada solo escribe las ventanas nuevas: las del final del anillo, con casi todo el anillo detrás (hasta unos 15–20 min). Por tanto, en el entrenamiento la duración de un flujo largo se observa con un horizonte de hasta unos 15–20 min.
- **Motor.** Usa 230 s; ya lo hacía en vivo en el 3B, así que no es un cambio de este cierre.
- **Medida en el tramo** (`tope-duracion-tramo.json`): 279 de 1442 ventanas con contenido (19 %) tienen `flow_duration_mean_30s` ≥ 200 s, con un máximo de 228,1 s. Se concentran en entidades con flujos largos:

  | Entidad | Ventanas ≥ 200 s |
  |---|---|
  | 10.10.50.52 | 80 de 89 |
  | 10.10.50.51 | 70 de 84 |
  | 10.10.10.21 | 67 de 87 |
  | 10.10.40.10 | 58 de 93 |

**2. El modelo es sensible a esa zona.** El escalador del pipeline da para esta característica una media de 10,1 s y una desviación de 74,4 s. El bosque (500 árboles) tiene 2183 cortes sobre ella, en `cortes-flow-duration.json`:

- 522 por encima de 200 s;
- 498 por encima de 230 s;
- el máximo, en 957,6 s.

Así que el entrenamiento vio duraciones medias muy por encima de 230 s, y truncar puede cambiar el recorrido de una fila por los árboles.

**3. Efecto medido: replay de sensibilidad con `--history-seconds 900`.** Mismo anillo de 15 s y disparo periódico, desde 08:45:30, comparado con r2 (230 s) en 08:46–09:04 (`sens900-vs-r2.json` y `sens900-clases.json`).

- **Vectores.** De 676 ventanas comparables con vector, 279 cambian de vector y de score. En 225 solo cambia `flow_duration_mean_30s`. En el resto cambian también `unique_dst_ip_ratio_30s`, `unique_dst_port_ratio_30s`, `flow_attempt_rate_10s` y otras, porque el propietario y el inicio de cada flujo dependen del horizonte.
- **Clases α.** Todos los cambios van en la misma dirección, **PERMIT → ALERT**: 54 a α 0,05, 18 a α 0,03 y 15 a α 0,01. Caen sobre entidades legítimas: DC1 (10.10.10.20) 28, 10.10.50.51 11, 10.10.50.52 8, y clientes.
- **Origen de ensayo (10.10.20.30).** 7 vectores distintos y 0 cambios de clase.
- **Reglas.** 0 distintas.
- **Coste.** El replay de 900 s no llegó a decidir 547 ventanas del rango antes del final: su latencia p50 fue de 1016 s y su pico de memoria de 3343 MB, frente a 839 MB con 230 s.

**4. Conclusión.** Con lo medido, **no se concluye que haya que reentrenar.**

- Llevar el horizonte del motor al del entrenamiento no mejora nada observable en este tramo: no recupera ninguna detección y añade falsas alarmas sobre entidades legítimas. Además multiplica por 4 la memoria y hace inviable la latencia.
- La diferencia de contrato es real y afecta al 19 % de las ventanas con contenido del tramo. Lo que falta para decidir es la **distribución de esta característica en el dataset de entrenamiento**, que está en el Sensor1 y este encargo no permitía leer.
- Queda como requisito de la Etapa 3: medir en el dataset de entrenamiento (lectura, sin reentrenar) qué fracción de filas tiene `flow_duration_mean_30s` > 230 s y en qué entidades. Con ese dato se podrá elegir con evidencia entre:
  - (a) documentar la truncación como parte del contrato del motor;
  - (b) extraer el entrenamiento con el mismo horizonte de 230 s y recalibrar;
  - (c) cambiar la definición de la característica.

  Ninguna se aplica ahora.

**Límites de esta prueba:**

- un solo tramo de 18 min;
- 676 ventanas comparables;
- un replay periódico con 15 s;
- no cubre el control normal.
