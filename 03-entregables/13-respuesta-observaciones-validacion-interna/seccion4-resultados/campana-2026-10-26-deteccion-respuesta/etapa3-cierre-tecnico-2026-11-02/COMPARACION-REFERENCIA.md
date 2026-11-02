# Comparación con la referencia (cierre técnico de la Etapa 3)

- **Referencia:** la candidata de la Etapa 3, `585da7b`. El banco usa `../etapa3-deteccion-temprana-2026-11-02/resultados/`; el replay, `e3-b1ee393-e5-eventos`, motor igual a `585da7b`.
- **Nuevo:** `49a29db`, el motor del cierre.

Mismas entradas y mismos criterios. `analizar_3b.py` y los comparadores no se modificaron.

> **Qué no es esto.** Ni el banco ni el replay son una confirmación independiente:
> - las «120 ejecuciones» de la Etapa 3 y las 60 de aquí reinyectan **los mismos 5 escaneos** grabados en el 3B (3 repeticiones por escaneo y condición);
> - el replay vuelve a leer el **mismo** tramo del 3B.
>
> Sirven para comparar versiones sobre entradas idénticas, no para estimar el comportamiento ante ataques nuevos. La confirmación en vivo corresponde a la Etapa 4, en sombra, con una campaña nueva.

---

## 1. Banco: vía rápida, alternativa C (5 escaneos × 3 repeticiones por condición)

Segundos desde el primer SYN del escaneo. «Margen» = desde la aplicación hasta el último SYN del escaneo.

### 1.1 Resultado por condición

| Condición | n | Aplicada p50 / p95 / máx | 1.er descarte p50 / p95 / máx | Descarte antes del último SYN | Margen mín. | Confirmadas |
|---|---|---|---|---|---|---|
| Referencia, sin carga, sin VLAN | 15 | 1,52 / 1,91 / 2,00 | 1,54 / 1,96 / 2,03 | 15/15 | 2,62 | 15/15 |
| **Nuevo, sin carga, sin VLAN** | 15 | 1,42 / 1,58 / 1,59 | 1,45 / 1,64 / 1,64 | 15/15 | 3,02 | 15/15 |
| Referencia, con carga, sin VLAN | 15 | 0,98 / 1,60 / 1,62 | 1,13 / 1,64 / 1,65 | 15/15 | 2,98 | 15/15 |
| **Nuevo, con carga, sin VLAN** | 15 | 0,80 / 1,65 / 1,72 | 1,13 / 1,67 / 1,74 | 15/15 | 2,94 | 15/15 |
| **Nuevo, sin carga, con VLAN** | 15 | 1,46 / 1,65 / 1,83 | 2,55 / 2,70 / 2,71 | 15/15 | 3,00 | 15/15 |
| **Nuevo, con carga, con VLAN** | 15 | 0,92 / 1,59 / 1,60 | 1,34 / 2,71 / 2,73 | 15/15 | 2,90 | 15/15 |

Total del cierre: 60 de 60 aplicadas antes del último SYN, y 60 de 60 confirmadas por el agente.

### 1.2 Tramos medidos por separado (p50 / p95 / máx, s)

| Tramo | Ref. sin carga | Nuevo sin carga | Ref. con carga | Nuevo con carga | Nuevo VLAN sin carga | Nuevo VLAN con carga |
|---|---|---|---|---|---|---|
| evidencia → emisión | 0,31 / 0,89 / 0,93 | 0,31 / 0,87 / 0,87 | 0,004 / 0,022 / 0,022 | 0,006 / 0,019 / 0,020 | 0,31 / 0,87 / 0,87 | 0,006 / 0,024 / 0,024 |
| disponible → emisión | 0 / 0 / 0 | 0 / 0,001 / 0,001 | 0 / 0 / 0 | 0 / 0,001 / 0,001 | 0 / 0 / 0,001 | 0 / 0 / 0,001 |
| emisión → publicación | 0,12 / 0,22 / 0,24 | 0,17 / 0,26 / 0,26 | 0,15 / 0,25 / 0,26 | 0,14 / 0,22 / 0,25 | 0,21 / 0,25 / 0,26 | 0,12 / 0,24 / 0,24 |
| publicación → entrega | 0,33 / 0,81 / 0,82 | 0,09 / 0,57 / 0,58 | 0,34 / 0,85 / 0,86 | 0,10 / 0,87 / 0,89 | 0,08 / 0,65 / 0,82 | 0,33 / 0,85 / 0,86 |
| entrega → aplicación | 0,33 / 0,45 / 0,46 | 0,27 / 0,34 / 0,38 | 0,41 / 0,47 / 0,49 | 0,37 / 0,62 / 0,62 | 0,27 / 0,37 / 0,37 | 0,38 / 0,48 / 0,51 |
| aplicación → confirmación | 0,04 / 0,05 / 0,06 | 0,05 / 0,05 / 0,05 | 0,06 / 0,07 / 0,07 | 0,06 / 0,07 / 0,08 | 0,05 / 0,06 / 0,08 | 0,07 / 0,08 / 0,08 |
| aplicación → 1.er descarte | 0,05 / 0,38 / 0,48 | 0,09 / 0,45 / 0,49 | 0,15 / 0,41 / 0,43 | 0,25 / 0,47 / 0,54 | 0,97 / 1,25 / 1,31 | 0,66 / 1,20 / 1,29 |
| 1.er descarte → último SYN | 3,32 / 3,75 / 3,81 | 3,33 / 3,84 / 3,86 | 3,43 / 3,96 / 4,09 | 3,60 / 3,94 / 4,04 | 2,31 / 3,63 / 3,65 | 3,15 / 3,72 / 3,73 |

### 1.3 Lectura

- **Evidencia → emisión no cambia en el banco**, y era lo esperado. En el banco siempre llegan bytes detrás de la señal, así que el defecto de lectura (§1 del informe) no se manifestaba.
  - Sin carga, el p50 de 0,31 s y el máximo de 0,87 s son la **espera causal** del paquete que cierra la ventana g = 0,1 s y demuestra que la ráfaga no sigue sola. No es espera de lectura: **disponible → emisión es 0 (≤ 1 ms)** en todas las condiciones.
  - La corrección no gana tiempo en el banco. Elimina el caso en que, con tráfico escaso, la señal quedaba en el búfer sin límite. Ese caso lo cubre la regresión de escritura única, que falla en `585da7b`.
- **Publicación → entrega y entrega → aplicación** varían entre ejecuciones por el ciclo del relé y del agente, igual que en la referencia. No forman parte de este cierre.
- **Con VLAN, el primer descarte llega ~1 s más tarde** (aplicación → primer descarte, p50 0,97 s sin carga). No es un retraso de la regla: la pila de srv-dmz solo recibe la copia de la **VLAN 30**, es decir, los SYN que el pfSense real deja pasar (6-9 por escaneo). El SYN siguiente que llega a srv-dmz tarda más en aparecer, y el margen de aplicación sigue en ≥ 2,90 s.
  - La batería sin VLAN medía el «primer descarte» sobre ≈ 2 010 SYN por escaneo de la VLAN 20 que el pfSense ya filtra. Su cifra era optimista.
  - La de VLAN es la representativa de srv-dmz; el resultado, aplicada antes del último SYN, se mantiene (15/15 y 15/15).
- **Banco:** tcpdump 4.99.5, libpcap 1.10.5 (TPACKET_V3), kernel 6.18 de WSL2. Sensor1 puede diferir (paso 0 del procedimiento).

Datos: `resultados/bateria-c/`, `resultados/bateria-c-vlan/` (JSONL por ejecución, `resumen.json`, `TABLA.md`) y `resultados/comparaciones/resumen-bateria-e3-tramos.json` (la referencia, resumida con el mismo resumidor).

---

## 2. Replay del 3B: IF puro, episodios y control

Mismo tramo, anillo, modelo, umbral, argumentos y orden de eventos que `e3-b1ee393-e5-eventos`. Replay en 912,5 s.

### 2.1 Clave a clave (`comparaciones/e3-b1ee393-vs-cierre-49a29db-e5-eventos.json`)

| | Referencia | Nuevo |
|---|---|---|
| Claves (entidad, ventana) | 12 773 | 12 773 (iguales) |
| Estados: decisión / cancelada / no elegible | 12 726 / 14 / 33 | 12 726 / 14 / 33 |
| Vectores comparables / distintos | 9 607 / — | 0 distintos |
| Scores distintos | — | **0** |
| Decisiones finales distintas | — | **36** (todas `auth_failure_heuristic`, §3) |

**IF puro idéntico:** mismas 28 características, mismos scores, mismo α. Las 36 diferencias son de la decisión final y vienen de la heurística interna. En las 36, `decision_if` = PERMIT, igual que la clasificación del IF en la referencia.

### 2.2 Los 25 episodios y la población principal

`comparar_25` frente a la referencia e3: **0 diferencias de categoría** en las 7 configuraciones derivadas.

Frente al replay de seguridad optimizado (`sec-opt-6b6ef82`) hay 2 diferencias: `escaneo_breve-r1`, HEUR y HIB_0.01, oportuna → solo_posterior. Son **las mismas que ya tenía e3** y no son del cierre.

**Población principal: 15 de 25**, sin cambios. Los 10 excluidos y sus motivos son los mismos, producidos por el mismo criterio, aplicado antes del resultado:

| Excluido | Motivo |
|---|---|
| escaneo_sostenido-r1 | integridad no apta |
| inundacion_http-r1 | integridad no apta |
| inundacion_http-r2, -r3, -r4 | fuente degradada; integridad no apta |
| dns_inusual-r3, -r5 | fuente degradada; integridad no apta |
| escaneo_breve-r4 | fuente degradada; integridad no apta |
| fuerza_bruta_http-r2, -r3 | fuente degradada; integridad no apta |

**Diferencias por campo dentro de los episodios** (`comparaciones/clasificacion-e3-vs-cierre.json`):

- Sin contar instantes, solo `dns_inusual-r1` cambia: en HEUR y en las tres HIB pierde **una** señal atribuible (13 → 12 y 14 → 13). Es la ventana 09:28:10, un `auth_failure_heuristic` sin evidencia HTTP válida que caía 51 s después del fin del episodio (§3). Las oportunas y la categoría («oportuna») no cambian.
- El resto son marcas de tiempo del reloj «coste» (p. ej., `disponible_utc` 08:09:01.95 → 08:09:02.30 en `escaneo_sostenido-r2`), que mide el tiempo de cómputo del replay en el portátil y varía entre ejecuciones. Ninguna categoría cambia por ello.

### 2.3 Control normal

Idéntico a la referencia:

- **IF:** 395 / 254 / 83 ventanas con señal (α 0,05 / 0,03 / 0,01);
- **HEUR:** 0;
- **HIB:** 395 / 254 / 83;
- **inventario:** 12 209 ventanas requeridas, todas decididas a tiempo; cobertura 1,0.

---

## 3. Cambios de `auth_failure_heuristic` (`comparaciones/cambios-auth-failure-e3-vs-cierre.json`)

### 3.1 En el motor

| | Referencia e3 | Nuevo |
|---|---|---|
| Ventanas con `auth_failure_heuristic` como decisión final | 61 | **25** |
| De ellas, sin ninguna petición HTTP válida en la vista | 36 | 0 |
| Señal histórica (`auth_failure.historico`) no autorizada | — | 91, registradas, sin efecto |

Las **36** que desaparecen son todas de **10.10.20.30** (el atacante). En las 36: ALERT → PERMIT, `no_live_packets_heuristic`, `decision_if` = PERMIT. Todas tienen **0 peticiones válidas** en la vista HTTP y entre 6 y 392 transacciones tardías. Ubicación:

- la mayoría caen **61-118 s después del fin** de `fuerza_bruta_http` r1-r5: son el registro tardío de Suricata de un ataque ya terminado;
- 08:54:50, 09:19:20, 09:24:20 y 09:33:20, en la misma cola;
- 09:28:10: 51 s después del fin de `dns_inusual-r1`;
- 09:08:40: 80 s después del fin de `escaneo_sostenido-r3`;
- 09:57:50: 20 s después del fin de `escaneo_breve-r2`.

Ninguna cae dentro de un episodio activo. Las 25 que se conservan tienen evidencia HTTP válida en la ventana.

### 3.2 En el feed (cada registro, por su propio publicador)

| | Referencia | Nuevo |
|---|---|---|
| Restricciones creadas o renovadas (total) | 66 | **58** |
| Renovaciones por `auth_failure_heuristic` | 13 | **5** |

- **Se eliminan 8 renovaciones** sobre 10.10.20.30, a las 08:54:20, 08:59:20, 09:08:40, 09:18:50, 09:23:50, 09:28:10, 09:33:20 y 09:50:20. Prolongaban un BLOCK con HTTP tardío después de terminar el ataque.
- **Se conservan 5**, a 31-38 s del fin de cada fuerza bruta, con evidencia válida (≥ 5 peticiones y ratio ≥ 0,8) en la ventana.
- Ninguna IP legítima cambia: ni antes ni ahora hubo restricciones `auth_failure` sobre legítimos en este tramo.

El efecto práctico es que el bloqueo deja de alargarse sin evidencia. La respuesta durante el ataque no cambia: §2.2, 0 diferencias de categoría.
