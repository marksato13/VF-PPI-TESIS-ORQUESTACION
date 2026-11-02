# Vía rápida para el escaneo breve

Objetivo: detectar el escaneo breve con margen suficiente para aplicar una respuesta **mientras sigue activo**. Este documento separa cuatro hechos, que no son equivalentes:

1. detección (existe evidencia y se emite la señal);
2. publicación y entrega;
3. aplicación confirmada en nftables;
4. efecto sobre el tráfico (primer paquete descartado).

Una alerta anterior al fin **no** es prueba de bloqueo oportuno. Un replay abierto **no** prueba que el atacante se detenga: eso se confirma en la campaña B.

## 1. Anatomía de los cinco escaneos breves (3B)

Comando: `nmap -sT -T4 --max-retries 1 -p 1-1000` desde 10.10.20.30 hacia srv-dmz (10.10.30.10). Herramienta: `scripts/etapa3/anatomia_escaneos.py`; datos en `resultados/via-rapida/anatomia-breves.json`.

| Fase | Qué hay en el cable | Cuándo |
|---|---|---|
| Descubrimiento | ICMP echo y timestamp, SYN/443 y ACK/80: 5 tramas | t0 + 0,09 s |
| Resolución inversa | 4 consultas DNS a DC1/DC2; nada al destino | ~13 s |
| **Ráfaga efectiva** | 999 puertos, ~2 SYN por puerto (`--max-retries 1`), 8–11 retransmisiones | **4,22–4,62 s** |
| Fin del proceso | último SYN 0,23 s antes de la marca de fin | 17,6–18,0 s desde el inicio |

- La ráfaga empieza con una primera oleada de 11–13 puertos en 1 ms; sigue una pausa de ~1,2 s y después la aceleración.
- srv-dmz **no contesta RST** a los puertos cerrados: descarta en silencio. Solo contesta SYN-ACK en 80 y 443 (y en 18081 en los sostenidos).
- Por eso un intento solo puede darse por fallido **por tiempo**: sin SYN-ACK tras g s.

Referencia de tiempos: los paquetes que el atacante emitió realmente (sin copias SPAN), no la señal de otra regla. En escaneo_breve-r1, la regla brute_force que disparó antes del fin no era del escaneo: eran registros tardíos de Suricata (ver `HTTP-CONFUSIONES-Y-RENOVACIONES.md` §2).

## 2. Regla temprana `port_scan_temprano`

`scripts/engine/escaneo_temprano.py` (versión 2026-11-02.1). Es un **componente heurístico adicional**: no altera las entradas del IF.

- **Por par origen → destino**, con la red y las IP de gestión excluidas.
- Cuenta **puertos distintos** con intentos fallidos: RST recibido, o sin SYN-ACK tras g s. Un SYN-ACK tardío retira el intento.
- **Ventana** (t − W, t] sobre el instante del SYN.
- **Copias SPAN**: la misma trama en menos de 5 ms cuenta una vez. **Retransmisiones**: mismo (src, sport, dst, dport, seq), no suman puertos.
- **Causal**: un vencimiento solo se resuelve cuando el reloj de datos ha pasado t_syn + g, y nunca se usa información futura.
- **Refractario** de 60 s por par.
- Cada disparo lleva un identificador (sha256 de 16 hex), la versión, los parámetros, la muestra de puertos, `t_evidencia`, `disponible_en` y `emitido_en`.

Proceso: `scripts/engine/detector_rapido.py`, con dos modos:

- `--ficheros DIR`: capturas cortas cerradas. Tras cada fichero avanza el reloj a la marca del siguiente.
- `--flujo`: lectura continua por la entrada estándar.

Equivalencia: el detector de producción y el evaluador de la rejilla dan **los mismos 10 disparos** sobre el 3B.

## 3. Elección de parámetros (rejilla y tráfico legítimo)

Rejilla completa: W ∈ {0,5; 1; 2; 5; 10} s, K ∈ {5…30}, g ∈ {0,05; 0,1; 0,2; 0,5; 1} s (`resultados/via-rapida/rejilla-temprana.json`). Extracto para los 5 breves (los 5 sostenidos se detectan en todas las filas listadas):

| W | g | K | Breves detectados | Desde el inicio de la ráfaga | Hasta el último SYN |
|---|---|---|---|---|---|
| 2 | 0,1 | 5 | 5/5 | 0,10 s | 4,12–4,52 s |
| **2** | **0,1** | **8** | **5/5** | **0,10 s** | **4,12–4,52 s** |
| 2 | 0,1 | 10 | 5/5 | 0,10 s | 4,12–4,52 s |
| 2 | 0,1 | 12 | 5/5 | 0,10–1,31 s (irregular) | 3,31–4,51 s |
| 2 | 0,1 | 15 | 5/5 | 1,31 s | 2,91–3,31 s |
| 2 | 1,0 | 8 | 5/5 | 1,00 s | 3,22–3,62 s |
| 1 | 1,0 | 8 | **0/5** (efecto del borde: con W = g el intento vence fuera de la ventana) | — | — |

Con K = 12 el resultado es irregular porque dos escaneos tienen solo 11 puertos en la primera oleada. Con K ≥ 15 hay que esperar a la aceleración.

**Tráfico legítimo** (`scripts/etapa3/margen_legitimo.py`; `resultados/via-rapida/margen-legitimo.json`). Cuatro capturas, ~7,2 h:

| Captura | Horas |
|---|---|
| 3B (sin la Kali) | 3,52 |
| preparación 3A | 1,78 |
| preflight | 0,33 |
| paso 2 | 1,56 |

- Con W = 2 y g = 0,1, el máximo de puertos fallidos de un par legítimo es **3** (10.10.20.26 → srv-dmz).
- El bastión (10.10.10.30), ya excluido, llega a **4** al comprobar puertos de 8 hosts en el preflight.
- Con K = 4 habría falsas alarmas sobre el bastión (8 pares); con K ≥ 5, 0 en todas.

**Elegido: K = 8, W = 2 s, g = 0,1 s.** No se elige solo porque separe los cinco ejemplos:

- K = 8 es el doble del peor legítimo (4);
- queda 1,4 veces por debajo de la oleada más pequeña observada (11);
- g = 0,1 s es unas 100 veces el RTT del laboratorio (< 1 ms) y deja un SYN-ACK legítimo lento fuera del recuento con margen.

**Limitación:** datos del mismo laboratorio y de pocos hosts. Un servidor que conteste RST, o un cliente con muchas conexiones fallidas (balanceador o comprobaciones de salud), requiere revisar K.

Con K = 8 sobre todo el archivo del 3B: **10 disparos**, todos Kali → srv-dmz, uno por escaneo; 0 sobre otros pares. Evidencia de los breves (tiempo de datos):

| Escaneo | Evidencia − 10.º puerto | Evidencia → último SYN | Evidencia → fin del proceso |
|---|---|---|---|
| r1 | 0,100 s | 4,119 s | 4,359 s |
| r2 | 0,101 s | 4,516 s | 4,737 s |
| r3 | 0,101 s | 4,120 s | 4,357 s |
| r4 | 0,101 s | 4,516 s | 4,744 s |
| r5 | 0,100 s | 4,518 s | 4,746 s |

## 4. Integración en el feed

- `publicar_feed_v2.py --senales-rapidas FICHERO` sigue el fichero de señales.
- **Destino:** el punto de aplicación que protege al host escaneado (`DESTINO_DE_OBJETIVO = {"10.10.30.10": ("srv-dmz", "todo")}`). Si el host escaneado no tiene agente, se registra `sin_punto_de_aplicacion`; no se inventa un destino.
- **Sin duplicar:** si la regla por ventanas `port_scan` dispara después sobre el mismo (IP, destino, alcance), la restricción queda **mantenida** (misma severidad, sin evidencia nueva) o **renovada** si la evidencia es posterior. Nunca hay dos restricciones ni dos peldaños de escalada.
- Política de renovación: ver `HTTP-CONFUSIONES-Y-RENOVACIONES.md` §6. Pruebas: `tests/test_etapa3_publicador.py` (8).

## 5. Alternativas comparadas

| Alternativa | Qué es | Disponibilidad de la evidencia | Coste y riesgo |
|---|---|---|---|
| A1 | capturas de 1 s (`tcpdump -G 1`) + detector sobre ficheros cerrados | al cerrar el fichero que contiene la evidencia: 0–1 s más (según la fase) | un tcpdump más en el sensor; muchos ficheros pequeños; tcpdump solo rota al llegar un paquete |
| A2 | capturas de 2 s | 0–2 s más | igual, con menos ficheros |
| C | flujo continuo (`tcpdump -U -w - \| detector_rapido --flujo`) | al leer el paquete (ms) | un proceso de larga duración que hay que vigilar; si se cae, no hay vía rápida |
| B | Suricata con reglas `threshold` (solo banco) | al registrar la alerta (ms) | Suricata cuenta SYN, no puertos distintos ni intentos sin respuesta; la lista de puertos servidos es configuración por host; activar reglas en Sensor1 es un cambio de la Etapa 4 |

Las cuatro alimentan **la misma** cadena: publicador → relé → agente → helper → nft.

## 6. Presupuesto temporal

### 6.1 Tres clases de cifra

| Clase | Qué es | De dónde sale |
|---|---|---|
| **Datos** | tiempos medidos sobre las marcas del PCAP del 3B: evidencia, último SYN, fin | §3 (rejilla, detector sobre el archivo) |
| **Simulado (banco)** | la cadena real (detector, publicador, relé local, agente, helper, nft) sobre un par veth, con el segmento del 3B reinyectado a su velocidad original | `deploy/pruebas-aisladas/ensayo_via_rapida.py` |
| **Desconocido** | lo que el banco no reproduce | §6.4 |

Ninguna mediana se suma a otra: cada fila del banco es una **ejecución completa** de la cadena y los tiempos son instantes sobre el mismo reloj, medidos desde el primer SYN de la ráfaga.

### 6.2 Banco

- Contenedor `cyberflow-etapa3-banco:1` con `--privileged --network none`. No toca el laboratorio.
- Par veth vA → vB; vB tiene 10.10.30.10 (srv-dmz). `tcpreplay-edit --enet-vlan=del` (las tramas del espejo llevan 802.1Q) y `--enet-dmac` de vB.
- El kernel de vB no contesta (descarte en `output`): el atacante reinyectado no depende de respuestas, como en el cable.
- El perfil `dmz` del helper crea la tabla `inet cyberflow_dmz` con su conjunto `bloqueados` y contadores. Un proceso aparte lee el contador del elemento del atacante cada 20 ms: «primer descarte visto».
- **Fase:** el replay arranca tras una espera aleatoria en [0, R) para A1/A2, de modo que la ráfaga no caiga siempre al principio del fichero.
- **Carga:** inundación HTTP del 3B en bucle, con la IP reasignada a 10.10.20.99 (para no confundirla con el atacante), más 4 procesos que ocupan CPU.
- Sondeos de la cadena, iguales a los de producción: relé 1 s, agente 0,5 s.

### 6.3 Prueba de humo (escaneo_breve-r3, una ejecución por celda)

`resultados/via-rapida/humo/ensayo-via-rapida.jsonl`. Segundos desde el primer SYN de la ráfaga.

| Alt. | Carga | Evidencia | Disponible | Publicada | Entregada | Recibida | **Aplicada** | **1.er descarte** | Último SYN | Margen aplicada → último SYN |
|---|---|---|---|---|---|---|---|---|---|---|
| C | no | 0,101 | 0,121 | 0,383 | 1,229 | 1,640 | **1,805** | **1,867** | 4,562 | 2,76 |
| A1 | no | 0,100 | 0,647 | 0,880 | 1,717 | 2,054 | **2,241** | **2,294** | 4,556 | 2,31 |
| A2 | no | 0,101 | 0,985 | 1,192 | 1,289 | 1,331 | **1,489** | **1,562** | 4,495 | 3,01 |
| B | no | 0,003 | 0,014 | 0,128 | 0,675 | 0,828 | **0,987** | **1,048** | 4,530 | 3,54 |
| C | sí | 0,101 | 0,120 | 0,350 | 0,561 | 0,944 | **1,374** | **1,470** | 4,911 | 3,54 |
| A1 | sí | 0,101 | 0,669 | 0,797 | 1,210 | 1,383 | **1,606** | **1,681** | 4,794 | 3,19 |
| A2 | sí | 0,101 | 0,200 | 0,361 | 0,858 | 0,970 | **1,242** | **1,315** | 5,033 | 3,79 |
| B | sí | 0,005 | 0,016 | 0,233 | 0,287 | 0,583 | **0,895** | **1,099** | 4,997 | 4,10 |

En las 8 ejecuciones, la restricción quedó aplicada y descartando paquetes **antes del último SYN**, con 2,3–4,1 s de escaneo restante. Entre 1 505 y 2 001 de los 2 017 SYN del escaneo llegaron a vB después de la aplicación.

Lectura:

- **El término dominante no es la detección** sino los sondeos de la cadena: publicada → entregada (relé, 1 s) toma 0,05–0,85 s, y entregada → recibida (agente, 0,5 s) toma 0,04–0,41 s. Dependen de la **fase** del sondeo, no de la carga: por eso una fila con carga puede salir antes que la misma sin carga.
- A1/A2 añaden la espera al cierre del fichero (disponible − evidencia: 0,10–0,88 s), que también depende de la fase.
- B (Suricata) adelanta la evidencia unos 0,1 s porque cuenta SYN, no intentos vencidos sin respuesta. Emite 3 alertas por escaneo. La 1.ª se publicó como `nueva`; el tipo de las otras dos no se conservó en la prueba de humo (el directorio temporal se borra). Por diseño, sobre el mismo (IP, destino, alcance) no crean una segunda restricción: quedan `mantenida` o `renovada` (§4).
- Aplicada → primer descarte visto: 0,05–0,20 s (incluye el sondeo de 20 ms del contador).

**Esto es una prueba de humo, no el presupuesto.** Una sola ejecución por celda y un solo escaneo no sostienen percentiles. Corrección hecha tras la prueba: el campo `paquetes_descartados_contador` guarda el contador **en el primer sondeo** con descartes (11–57 paquetes), no el total. Se añadió `paquetes_descartados_final`.

### 6.4 Batería completa (120 ejecuciones)

5 escaneos breves × 4 alternativas × con y sin carga × 3 repeticiones; n = 15 por celda. Datos en `resultados/via-rapida/bateria/ensayo-via-rapida.jsonl`, resumen con `deploy/pruebas-aisladas/resumir_ensayo_via_rapida.py` (`resultados/via-rapida/bateria/resumen.json`). Los percentiles se calculan **sobre ejecuciones completas**, no sumando tramos. Segundos desde el primer SYN de la ráfaga.

| Alternativa | Carga | n | Aplicada p50 / p95 / máx | 1.er descarte p50 / p95 / máx | Descarte antes del último SYN | Margen aplicada → último SYN mín / p50 | SYN del escaneo tras aplicar (mín / p50) |
|---|---|---|---|---|---|---|---|
| A1 | no | 15 | 1,45 / 2,03 / 2,08 | 1,53 / 2,10 / 2,11 | 15/15 | 2,43 / 3,12 | 80 % / 95 % |
| A1 | sí | 15 | 1,66 / 2,08 / 2,22 | 1,74 / 2,15 / 2,32 | 15/15 | 2,30 / 3,25 | 75 % / 92 % |
| A2 | no | 15 | 1,94 / 2,70 / 2,70 | 2,05 / 2,77 / 2,77 | 15/15 | 1,77 / 3,02 | 61 % / 90 % |
| A2 | sí | 15 | 2,09 / 2,60 / 2,68 | 2,17 / 2,67 / 2,77 | 15/15 | 2,12 / 2,55 | 72 % / 84 % |
| B | no | 15 | 0,82 / 1,43 / 1,47 | 1,05 / 1,70 / 1,97 | 15/15 | 3,20 / 4,08 | 95 % / 99 % |
| B | sí | 15 | 0,93 / 1,69 / 1,72 | 1,06 / 1,77 / 1,78 | 15/15 | 2,90 / 3,93 | 87 % / 99 % |
| **C** | no | 15 | 1,52 / 1,91 / 2,00 | 1,54 / 1,96 / 2,03 | 15/15 | 2,62 / 3,33 | 82 % / 94 % |
| **C** | **sí** | 15 | **0,98 / 1,59 / 1,62** | **1,13 / 1,64 / 1,65** | **15/15** | **2,98 / 3,74** | **92 % / 99 %** |

**En las 120 ejecuciones la restricción quedó aplicada y descartando antes del último SYN del escaneo.** El margen mínimo fue de 1,77 s (A2).

Tramos por ejecución (p50 / máx, s):

| | Evidencia → disponible | Publicada → entregada (relé, 1 s) | Entregada → recibida (agente, 0,5 s) |
|---|---|---|---|
| A1 | 0,46–0,55 / 0,91 | 0,35–0,58 / 0,88 | 0,26–0,30 / 0,38 |
| A2 | 0,93–1,04 / 1,65 | 0,34–0,35 / 0,87 | 0,27–0,30 / 0,35 |
| B | 0,01 / 0,03 | 0,31–0,33 / 1,02 | 0,24–0,29 / 0,56 |
| C sin carga | 0,31 / 0,93 | 0,33 / 0,82 | 0,24 / 0,36 |
| C con carga | **0,004–0,022** | 0,34 / 0,86 | 0,29 / 0,35 |

**Hallazgo: la alternativa C depende del tráfico ajeno.** El detector avanza su reloj solo con paquetes. Así no inventa ausencias y es causal. Sin carga, el vencimiento de un intento (SYN + g) espera al siguiente paquete, y tras la primera oleada de nmap hay una pausa de ~1,2 s: la disponibilidad se retrasa hasta 0,93 s. Con la carga, el tráfico de otro host avanza el reloj y la espera baja a milisegundos. En el sensor, el espejo siempre tiene tráfico TCP de otros hosts, así que la fila **con carga** es la representativa. Esto debe confirmarse en vivo (`PROCEDIMIENTO-ETAPA4.md` §1).

**Elección: C.** Junto con B es la más rápida con carga y no requiere activar reglas nuevas en el Suricata de Sensor1, lo que B sí exige y que además cuenta SYN y no intentos fallidos. A1/A2 añaden la espera del cierre del fichero. En todas las alternativas, el **término dominante es la cadena** (relé de 1 s + agente de 0,5 s: hasta ~1,4 s en el peor caso), no la detección. Bajar esos sondeos es la mejora más directa si hiciera falta más margen; no se ha cambiado.

**Límites de la batería.** Un replay no reacciona al bloqueo: los paquetes descartados son grabados. Hay un único destino (srv-dmz), la carga es sintética y el transporte, local.

### 6.5 Lo que el banco no mide (desconocido)

- **Retardo del espejo SPAN** del conmutador y del búfer de captura en Sensor1.
- **Transporte real** del relé al agente de srv-dmz (SSH entre VLAN). En el banco, el transporte es `local`.
- **CPU de Sensor1** con el motor, Suricata y el detector a la vez: el banco usa 4 procesos de CPU como sustituto.
- **Comportamiento del atacante ante el descarte.** Un replay abierto sigue enviando; nmap real con `--max-retries 1` y sin respuestas puede acabar antes o reducir velocidad. **Se confirma solo en la campaña B.**
- Hosts protegidos distintos de srv-dmz: hoy no tienen punto de aplicación (§4).
