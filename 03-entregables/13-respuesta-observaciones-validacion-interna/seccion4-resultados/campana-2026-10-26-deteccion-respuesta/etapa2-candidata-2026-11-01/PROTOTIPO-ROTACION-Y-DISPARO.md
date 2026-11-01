# Prototipo: rotación de PCAP de 5 s y disparo por cierre de fichero (Etapa 2, puntos 1 y 4)

## 0. Naturaleza de cada resultado

| Etiqueta | Significado | Dónde aparece |
|---|---|---|
| **MEDIDO** | Dato observado en un sistema real: el sensor (lecturas de solo lectura) o el banco Docker con procesos y nft reales. | Diagnóstico de descartes, pruebas, ensayo netns y ensayo de la cadena |
| **SIMULADO** | Replay del motor candidato sobre datos archivados del 3B, con reloj simulado. Los tiempos de ciclo son la CPU real **del portátil** (`--reloj coste`, `factor-cpu 1`), no la del Sensor1. La rotación de 5 s es **emulada** troceando el PCAP archivado. | Todo este documento, salvo la sección 4 |
| **PENDIENTE** | No hecho o no medible sin tocar el laboratorio. | Sección 6 |

**En el sensor no ha cambiado nada:** sigue `tcpdump -G 15` y el motor periódico desplegado.

## 1. Montaje

- **Datos:** PCAP archivado del 3B (`archivo-pcap`, 844 ficheros de 15 s), `eve-segmento.json` (1 087 178 líneas) y `marcas.jsonl`. Tramo 08:40–09:05 UTC del 1-nov, con 5 episodios del origen de ensayo: escaneo sostenido, escaneo breve, dos fuerzas brutas y DNS inusual. Hashes en `MANIFIESTO.sha256` y en el manifiesto del 3B.
- **Troceador** (`scripts/engine/trocear_pcap.py`): emula `tcpdump -G N -U`, que rota con el reloj del proceso **al llegar un paquete**.
  - Con 5 s salen 481 ficheros y con 15 s, 161.
  - En los dos casos hay 2 229 358 paquetes y 295 922 362 bytes, con el mismo sha256 de registros (`85f2bf17…`), verificado paquete a paquete (`resultados/trocear-e5.json` y `trocear-e15.json`).
- **Arnés** (`scripts/engine/replay_motor.py`): ejecuta el **mismo** `motor_decision.py` con un reloj y un sistema de ficheros simulados.
  - Un PCAP está disponible cuando aparece el siguiente, más `--retraso-cierre`.
  - Una línea EVE está disponible según el máximo acumulado de sus timestamps: nunca se lee EVE futuro.
  - Los ficheros abiertos no se leen.
- **Replays** (`herramientas/correr_replays.sh`; ejecución secuencial, para que la CPU medida no se contamine):

| Replay | Rotación | Disparo | Caso |
|---|---|---|---|
| r1 | 15 s **original** (los ficheros reales del sensor) | Periódico (desplegado) | Valida el emulador |
| r2 | 15 s emulada | Periódico | **Referencia** (equivale a hoy) |
| r3 | 5 s | Periódico | Solo la rotación |
| r4 | 5 s | Por eventos | **Candidato** |
| r5 | 15 s | Por eventos | Solo el disparo |
| r6 | 5 s | Por eventos | El fichero tarda 3 s más en estar disponible |
| r7 | 5 s | Por eventos | Reinicio del motor a las 08:50:02 (pierde la memoria) |

Las anclas de 10 s, el historial de 230 s y las **28 características** (`multilayer-v2.json`) no cambian en ningún replay.

## 2. Contenido (¿cambian las decisiones?) — SIMULADO

Comparación con r2, unida por (entidad, fin de ventana) (`resultados/comparacion-replays-tramo.json` → `contenido_vs_referencia`):

| Replay | Comunes | Misma decisión | Misma clase α | Mismo score | Mismos heurísticos | Vectores distintos | Características que cambian |
|---|---|---|---|---|---|---|---|
| r1 (original 15 s) | 2229 | 2229 | 2227 | 2187 | 2229 | 55 | `flow_duration_mean_30s` (55), `unique_dst_*` (3) y 1 en otras |
| r3 (5 s, periódico) | 2226 | 2225 | 2222 | 2053 | 2226 | 196 | `flow_duration_mean_30s` (196), `unique_dst_*` (5), `flow_attempt_rate_10s` (4) |
| r4 (5 s, eventos) | 2231 | 2231 | 2229 | 2041 | 2231 | 215 | `flow_duration_mean_30s` (215), `unique_dst_*` (6), `flow_attempt_rate_10s` (3) |
| r5 (15 s, eventos) | 2232 | 2232 | 2230 | 2195 | 2232 | 44 | `flow_duration_mean_30s` (44) |
| r6 (5 s, retraso 3 s) | 2243 | 2243 | 2243 | 2084 | 2243 | 177 | Como r4 |
| r7 (5 s, reinicio) | 2226 | 2219 | 2214 | 1982 | **2222** | 268 | Además, 11 características de 60 s (`dns_query_rate`, `unique_dns_name_ratio`, `http_request_rate`, `tls_session_rate`…), por la pérdida de memoria (sección 5) |

**Lectura:**

- **Las claves y la atribución se conservan:** los mismos pares entidad-ventana, salvo en los bordes del tramo (08:37:10 al principio y 09:04:50 al final; las diferencias `solo_ref`/`solo_otro` son de borde). En las rotaciones de 5 s aparecen además ventanas de 10.10.10.1, que se deciden antes del corte final del replay.
- **La rotación de 5 s no cambia ninguna detección ni ninguna regla.** Cambia la **clase α** en 2 de 2231 ventanas (r4) y desplaza alertas IF por α en ±1–3 de un total de 101/240/331.
- **La característica sensible es `flow_duration_mean_30s`.** Depende de cómo cortan los ficheros los flujos largos:
  - cambia incluso entre los ficheros **originales** y los **emulados** de 15 s (r1 frente a r2: 55 vectores), porque la fase de rotación es distinta;
  - con 5 s hay más cortes y más vectores distintos (196–215), con diferencias de hasta 225 s en ventanas de flujos largos.
  - Hipótesis, **no demostrada**: el extractor incremental cierra la duración del flujo en el borde del fichero.
  - Requisito para la Etapa 3: medir la diferencia en todo el 3B y decidir si se calcula a partir del EVE (`flow.age`) en vez del PCAP.
- **Deduplicación:** la misma decisión releída no genera eventos nuevos. Medido en el banco: `ensayo-cadena-eventos.json`, `decision_repetida_genero_nuevos = 0`.

## 3. Disponibilidad (¿cuándo se decide?) — SIMULADO con CPU del portátil

| Replay | Disparos | Espera desde el cierre del PCAP al ciclo (p50 / p90 / máx.) | Ciclo (p50 / p90 / máx.) | Latencia ventana → decisión, **ventanas con score** (p50 / p90) | Ídem, ventanas sin score (p50 / p90) | Pendientes por ciclo (p50 / máx.) | Pico de memoria |
|---|---|---|---|---|---|---|---|
| r1 original 15 s, periódico | 148 periodo | 8,9 / 14,2 / 15,4 s | 2,3 / 4,2 / 6,6 s | 15,5 / 30,8 s | 24,8 / 123,8 s | 12 / 28 | 867,6 MB |
| **r2 15 s, periódico (hoy)** | 149 periodo | 10,2 / 15,2 / 15,4 s | 0,9 / 2,1 / 3,5 s | **13,7 / 28,5 s** | 23,1 / 118,5 s | 12 / 28 | 863,5 MB |
| r3 5 s, periódico | 149 periodo | 1,9 / 2,0 / 2,1 s | 1,4 / 2,7 / 6,9 s | 10,0 / 27,8 s | 19,7 / 120,0 s | 8 / 12 | 863,4 MB |
| **r4 5 s, eventos** | 297 pcap_cerrado | **0,68 / 0,81 / 2,4 s** | 1,6 / 3,0 / 5,9 s | **3,9 / 38,6 s** | 14,0 / 128,6 s | 6 / 11 | 860,8 MB |
| r5 15 s, eventos | 98 pcap_cerrado + 99 plazo | 3,5 / 10,9 / 11,5 s | 2,3 / 4,5 / 10,1 s | 11,1 / 36,3 s | 20,6 / 121,0 s | 9 / 19 | 866,7 MB |
| r6 5 s, eventos, retraso 3 s | 295 pcap_cerrado | 3,7 / 3,8 / 7,9 s | 2,0 / 3,9 / 7,1 s | 7,4 / 48,7 s | 17,2 / 128,6 s | 8 / 14 | 860,8 MB |
| r7 5 s, eventos, reinicio | 291 pcap_cerrado + 2 arranques | 0,68 / 0,80 / 5,1 s | 1,9 / 3,3 / 8,6 s | 4,2 / 37,1 s | 14,5 / 123,6 s | 6 / 11 | 859,0 MB |

**Detección por episodio** (segundos desde el inicio del episodio hasta la decisión que dispara la regla prevista; HEUR):

| Episodio (duración) | r2 hoy | r3 | **r4** | r5 | r6 | r7 |
|---|---|---|---|---|---|---|
| escaneo_sostenido-r5 (65,7 s) | 31,7 | 28,1 | **22,6** | 28,5 | 26,4 | 23,4 |
| escaneo_breve-r5 (18,0 s; ráfaga de unos 5 s) | 45,5 | 32,1 | **26,4** | 37,7 | 29,1 | 26,1 |
| fuerza_bruta_http-r3 (89,1 s) | 28,8 | 14,8 | **10,3** | 23,9 | 12,6 | 9,1 |
| fuerza_bruta_http-r5 (90,0 s) | 29,6 | 15,6 | **10,9** | 23,8 | 14,1 | 10,0 |
| dns_inusual-r5 (90,4 s) | 28,6 | 15,3 | **10,3** | 20,1 | 13,4 | 9,4 |

**Lectura:**

- **Lo que más pesa es la rotación.** El disparo por eventos solo rinde con ficheros cortos:
  - r5 (15 s con eventos) mejora poco sobre r2;
  - r4 (5 s con eventos) reduce la latencia mediana de las ventanas con score de 13,7 a 3,9 s y la detección de las fuerzas brutas y del DNS de unos 29 a unos 10 s.
- **La cola p90 no mejora, e incluso sube** (28,5 → 38,6 s). La dominan las ventanas que esperan al EVE: los registros de flujo y HTTP se escriben al cerrar el flujo o por timeout. Es el límite de la fuente EVE, no de la captura.
- **Las ventanas sin score** (entidades sin tráfico propio en esos 10 s) se deciden tarde, con una p90 de unos 120 s. No afectan a la detección, pero sí a las renovaciones (sección 4 de `PRESUPUESTO-ESCANEO-Y-REGLAS-E3.md`).
- **Retraso de 3 s en el fichero** (r6): suma unos 3,5 s a la latencia y a la detección, sin perder ninguna.
- **Coste:**
  - la memoria no cambia: unos 860 MB de pico en todos los replays (el dominante es el índice EVE del arnés, no el motor);
  - con 5 s y eventos se hacen el doble de ciclos (297 frente a 149);
  - cada ciclo procesa menos (6 pendientes de mediana frente a 12), pero el ciclo dura más (1,6 frente a 0,9 s de mediana).
  - **En el Sensor1 la duración del ciclo no está medida con este motor** (pendiente P-1).
- **No hay acumulación:** las pendientes por ciclo están acotadas (máx. 11 en r4) y no crecen a lo largo del tramo.

## 4. Cadena completa por eventos — MEDIDO en el banco (sin ssh)

`deploy/pruebas-aisladas/ensayo_cadena_eventos.py` → `resultados/ensayo-cadena-eventos.json`. Procesos reales, nft real y 20 decisiones sintéticas. Tiempos desde `logged_at` de la decisión:

| Tramo | p50 | Media | Máx. |
|---|---|---|---|
| Leído por el publicador | 0,13 s | 0,13 s | 0,25 s |
| Publicado (firmado y renombrado) | 0,15 s | 0,15 s | 0,27 s |
| Entregado por el relé (sondeo 1 s, copia local) | 1,08 s | 1,35 s | 12,1 s |
| Recibido por el agente | 1,17 s | 1,61 s | 12,4 s |
| Aplicado en nft | 1,35 s | 1,80 s | 12,6 s |
| Confirmado (set releído) | **1,43 s** | 1,89 s | 12,7 s |

El máximo de 12,7 s es el evento que esperó al reintento del relé, con el destino dc1 ausente a propósito. Se reinició el agente dmz a mitad de la prueba y no se perdió ninguna confirmación. **No incluye ssh:** en el laboratorio hay que medirlo (P-2).

**Presupuesto extremo a extremo del candidato.** Es una suma de piezas, no una medición conjunta:

- detección: la de r4 (unos 10 s desde el inicio en fuerza bruta y DNS);
- cadena hasta la confirmación: unos 1,4 s;
- ssh: sin medir.

## 5. Reinicio, retraso, vacíos y truncados

- **Reinicio** (r7, `resultados/efecto-reinicio-r7.json`, `herramientas/efecto_reinicio.py`):
  - 16 ventanas cambian de regla o de clase respecto a r2. Todas son de 10.10.10.20, 10.10.20.22 y 10.10.20.24, entre 2 s antes y **48 s después** del reinicio.
  - 2 de ellas (a −712 s) también cambian en r4 sin reinicio: es el efecto de la rotación.
  - Todos los cambios **reducen** alarmas (pierden `dns_entropy` o bajan de clase), porque el motor reinicia sin historial de 60 s.
  - Ningún episodio caía en ese minuto, así que la detección no se ve afectada **en este tramo**.
  - Requisito para la Etapa 3: o persistir el historial, o marcar como «historial incompleto» las ventanas del primer minuto tras un arranque.
- **Fichero vacío, truncado o abierto:**
  - `test_trocear_vacio_e_incompleto`, `test_motor_lee_pcap_vacio_y_truncado` y `test_fichero_abierto_no_dispara`;
  - el extractor congelado lanza `ValueError` ante un PCAP truncado;
  - el motor candidato solo lee ficheros **cerrados** (el siguiente ya existe), así que en operación no debería ver ninguno truncado. Queda documentado en la prueba.
- **Rotación solo con paquete:** `test_trocear_rotacion_solo_al_llegar_paquete`. Sin tráfico no se cierra el fichero, y el plazo (`plazo`, igual al paso de 10 s) garantiza el ciclo (r5: 99 disparos por plazo).

## 6. Pendiente (no se puede afirmar)

| # | Pendiente | Por qué |
|---|---|---|
| P-1 | Duración del ciclo del motor candidato **en el Sensor1** con 5 s y eventos | Exige ejecutarlo allí (aunque sea en sombra). No autorizado en la Etapa 2. |
| P-2 | Latencia del relé por ssh (sensor → bastión → srv-dmz y DC1) | Ídem |
| P-3 | Efecto de `tcpdump -G 5` en los descartes de Suricata y en el disco | El diagnóstico de descartes (`DIAGNOSTICO-DESCARTES-SURICATA.md`) se hizo con 15 s |
| P-4 | Replays del 3B completo (25 episodios) | Aquí solo se usó un tramo de 25 min con 5 episodios. Las proporciones de alarmas no se pueden extrapolar. |
| P-5 | Diferencia de `flow_duration_mean_30s` en todo el 3B y su causa | Sección 2 |

**Aviso de entorno.** Los replays se ejecutaron en el portátil con scikit-learn 1.9.1. El modelo se serializó con 1.9.0 (`InconsistentVersionWarning` en `stderr.txt`). La referencia r2 y los demás replays usan el mismo entorno, así que la comparación es consistente. Los scores absolutos frente al sensor no se han verificado aquí.
