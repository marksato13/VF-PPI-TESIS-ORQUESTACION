# Etapa 4A: cierre complementario (2026-11-04, 05:30–07:30 UTC)

> **Veredicto.** El cierre complementario **cumple sus criterios**, con dos salvedades que pasan a la 4B. **La 4B se
> puede preparar, pero no iniciar** hasta resolver el pendiente P1 (medición de I5).
>
> Lo que está cerrado:
> - **Panel:** corregido (**93f076e**) y desplegado con modo v2 explícito.
> - **Primer PCAP ilegible:** corregido y verificado en arranque y rotaciones.
> - **v1 residual:** retirada (publicador y relé), sin tocar la cadena v2.
> - **Suricata con `ring-size: 16384`:** **0 descartes en 1 193 578 paquetes** durante 60 min, con **más** carga que la
>   base de la 4A (68 ráfagas frente a 11; 79 flujos grandes frente a 63). El resultado es **compatible con la
>   hipótesis**. **No la demuestra**: es una hora, y la relación con las descargas sigue siendo una correlación.
>
> Las salvedades:
> 1. **La calidad de captura del periodo es C3 (no evaluable) con las herramientas congeladas.** Suricata 7 no escribe
>    los contadores que valen 0 en `stats.log`. Por eso `salud_captura` (ec78ca5) no encuentra `kernel_drops` cuando no
>    hay descartes y no puede certificarlo. Tampoco detecta bien un reinicio (§6.4). **Con las herramientas actuales,
>    I5 no se puede demostrar.**
> 2. **El arranque controlado de la captura reinició también el motor** (`Requires=`), cosa que no estaba prevista
>    (§3.3).
>
> No se inició la 4B, la 4C ni la campaña B. No hubo ataques ni restricciones. No se eligió α, no se reentrenó y no se
> tocó el Word. La evidencia de la 4A no se modificó: solo se añadieron notas de corrección marcadas en su README §8 y
> en su PROPUESTA (§9).

Petición: la de Mark del 04-nov, en siete partes. Base: [`../etapa4a-instalacion-2026-11-04/`](../etapa4a-instalacion-2026-11-04/README.md).
Mark ejecutó los comandos con sudo; nunca se pidió ni se registró la contraseña.

## 1. Referencias efectivas

| Qué | Referencia | Estado |
|---|---|---|
| Documentación de partida | `main` @ **82772d8** | Sin cambios posteriores al empezar (fetch 07:3x) |
| Detector instalado | **ec78ca5** en Sensor1 `~/cyberflow-e4/ec78ca5` | `SHA256SUMS` OK, 87 ficheros (07:3x) |
| Modelo / scaler / variables / umbral | `if_limpio_2026_10_desplegable.joblib` `df547da0…`; manifiesto `b3ad6805…`; 28 variables; umbral **−0,5693969936322356** | Idénticos a `../etapa4a-instalacion-2026-11-04/evidencia/00-lecturas-previas/s1-hashes.txt` |
| Panel | rama `panel/cadena-v2-20261104`: **a27889d → 93f076e** | Desplegado; no fusionado en main |
| Herramientas | rama `recuperacion/etapa4a-instalacion-20261104`: **f1a12d7 → fc55674 → 398e479 → ce353ef** | No fusionado en main |
| Configuración de Suricata | `/etc/suricata/suricata.yaml`: `8e084b7d…` → **`0962ce68…`** (una línea: `ring-size: 16384`) | Respaldo `/etc/suricata/suricata.yaml.respaldo-cierre4a-20261104T061651Z` (`8e084b7d…`) |
| Política y α | `if_senal`; comparación α 0,05 / 0,03 / 0,01 sin cambios | Sin α final |

Lo que se ejecutó en Sensor1 es `cierre4a_sensor1.sh` de **fc55674** (sha `b5f984bf…`). En 398e479 solo se corrigió un
comentario (§3.3).

**Enlaces** (las ramas y commits se comprobaron con `git ls-remote` el 04-nov a las 07:3x UTC):
- Panel: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/panel/cadena-v2-20261104>
  — commit <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/commit/93f076e48ed425bf4ed3c02bd57e061a6379ec4e>
- Herramientas: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/recuperacion/etapa4a-instalacion-20261104/deploy/etapa4/cierre>
  — commit <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/commit/ce353ef090c9f5fb4eeb0fa1c4b3e917c00cc5ae>
- Esta carpeta: <https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/tree/main/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-cierre-complementario-2026-11-04>

## 2. Observación → corrección → prueba → resultado

| # | Observación | Corrección | Prueba | Resultado |
|---|---|---|---|---|
| A | Una decisión posterior a la última publicación se mostraba como «sin señal IF» | `cadena_v2.py`: cobertura demostrada por la traza (`cubierta` / `pendiente` / `fuente_desactualizada` / `fuente_ausente` / `desconocido`); margen de 2 s; huecos > 30 s | 3 regresiones en `DecisionesPosteriores` | Fallan en a27889d y pasan en 93f076e. En vivo (§4.3): posterior a la cobertura → «pendiente»; anterior → «sin señal α» |
| B | Una medida «desconocida» acababa con la aplicación en «no aplica» | «no aplica» solo cuando la ausencia de medida está demostrada; en cualquier otro caso, «desconocido» | `FuentesAusentes::test_medida_desconocida_…` | Ídem |
| C | Arrancar sin `traza.jsonl` seleccionaba v1 | `--modo-panel v2` por defecto y fijado en el drop-in; v1 solo con `--modo-panel v1-historico`; las fuentes ausentes se muestran como incidencia | `ModoExplicito` ×2, `ServidorSinTraza` ×3 (servidor real) | Ídem; en Sensor1 la cmdline incluye `--modo-panel v2` |
| — | `decision_if` del motor mezclado con la señal α | Filas separadas: «1a · IF del motor» y «1b · Señal α publicada» | `IFDelMotorExplicito`, `JsEstados` (Node) | Visto en una ALERT real (§4.3) |
| — | Fuente ausente o ilegible mostrada como cero | Contadores `null` y KPI «—» | `FuentesAusentes` ×4 (incluye desaparición y recuperación) | Ídem |
| D | El primer PCAP de cada arranque era ilegible para el motor | `cf-primer-pcap` en `ExecStartPost` (solo `chgrp` al grupo del directorio) | Reproducción con strace en Docker; arranque controlado en Sensor1 | El primer fichero y las rotaciones son legibles y válidos; `pcaps_ilegibles=0` en 3 884 decisiones |
| E | v1 residual (publicador y relé) | `disable --now` de sus temporizadores | Estados, procesos, mtime de los feeds y srv-dmz | v1 parada; v2 con 179/179 recepciones aceptadas en la ventana |
| F | Descartes de Suricata con el anillo por defecto | `ring-size: 16384` (único cambio) | Ensayo de 60 min con criterios declarados antes | 0 descartes con carga mayor; compatible, no demostrado |
| G | Textos que daban por descartados la CPU y el disco | Notas de corrección en README §8 y en PROPUESTA de la 4A | Medida a 1 s (§6.3) | Ver §9 |
| H | Comprobaciones de calidad de los scripts | `clasificar_periodo.py`, `comparar_suricata.py`, `analizar_fino.py` | Banco P1–P6 10/10; base 4A idéntica con las dos fuentes | Ver §7 |

## 3. Primer PCAP ilegible (parte 2)

### 3.1 Causa

- **Qué hace tcpdump.** Con `-Z tcpdump`, tcpdump 4.99.4 (el mismo de Sensor1) abre el **primer** fichero como root y le
  hace `chown(tcpdump, tcpdump)` **antes** de soltar privilegios.
- **Por qué solo falla el primero.** Los ficheros siguientes los crea ya como tcpdump y heredan el grupo `m4rk` del
  directorio setgid (`2750 tcpdump:m4rk`).
- **Efecto.** Con `UMask=0027` el modo es 640, así que el motor (m4rk) no puede leer el primer fichero.
- **Reproducción.** Hecha con strace en `ubuntu:24.04`, con tcpdump 4.99.4:
  `evidencia/02-pcap/pcap_repro.sh` → `out_pcap_repro.txt`.

### 3.2 Corrección mínima

- **Script.** `/usr/local/sbin/cf-primer-pcap` (`b654f875…`). Solo hace `chgrp m4rk` sobre los `live-*.pcap` que
  sean `tcpdump:tcpdump` en ese directorio. Espera como máximo 10 s y nunca hace fallar la unidad.
- **Drop-in.** `etapa4-primer-pcap.conf` (`1a71f2ee…`), con `ExecStartPost=-…`.
- **Lo que no cambia.** El modo, el propietario, `-Z`, `UMask` y el usuario.
- **Alternativas rechazadas.**
  - Meter a m4rk en el grupo tcpdump: es un privilegio extra.
  - Ejecutar tcpdump como `User=tcpdump` con capacidades ambientales: es un cambio mayor.

### 3.3 Verificación (arranque controlado a las 06:12:46 UTC)

- **Journal.** 06:12:46.923: `primer_pcap: grupo corregido en …/live-20261104061246.pcap`.
- **Ficheros.** El primero del nuevo tcpdump y tres rotaciones son `tcpdump:m4rk 640`, legibles y PCAP completos
  (885 / 817 / 2 039 / 867 paquetes). En el anillo quedan 0 ficheros con grupo tcpdump.
- **Procesados de verdad.** `marca_pcap` avanza con cada fichero desde el ciclo 0.
- **En la ventana 06:26:55–07:26:55:**
  - 717 ciclos, hueco máximo entre ciclos 5,9 s, duración máxima 2,62 s;
  - 3 884 decisiones con **`pcaps_ilegibles=0`** y `historial_completo=true`;
  - 0 `PermissionError` nuevos.
- **Imprevisto.** `ppi-motor` tiene `Requires=ppi-motor-capture.service`, así que systemd **reinició también el
  motor**: PID 1707357, a las 06:12:46. Ya había pasado lo mismo en la instalación de la 4A (02:11:07).
  - El contador del proceso nuevo empieza en 0.
  - **El histórico no se ha ocultado.** El registro del motor anterior a las 06:12:46 conserva `pcaps_ilegibles=1`
    con `PermissionError … live-20261104021107.pcap`, y está copiado en
    `evidencia/06-sensor1-remoto/previo/pcaps-ilegibles-antes.txt`.
  - El intervalo de arranque (06:12:46 + horizonte de 230 s) queda fuera de la observación válida, que empieza a
    las 06:26:55.

## 4. Panel (parte 1)

### 4.1 Pruebas (Linux, Docker `debian:trixie-slim`, Python + Node)

- **93f076e:** **144 pasadas**, 7 omitidas (`evidencia/01-panel/out_pruebas_panel_2.txt`).
- **a27889d con las 17 regresiones nuevas:** **17 fallan**, como se esperaba.
- El primer intento (`out_pruebas_panel_1.txt`) tuvo 2 fallos de la propia prueba: la caché de 3 s de
  `/api/status` y una pieza JS no extraída. Se corrigieron antes del commit.

### 4.2 Despliegue

- **Ficheros.** `dashboard.py` (`6eb2a4be…`) y `cadena_v2.py` (`23403181…`) en Sensor1.
- **Respaldo de a27889d.** `~/respaldos-etapa4/panel-20261104T054553Z`.
- **Drop-in.** `ppi-dashboard.service.d/modo-panel-v2.conf` (`7faad004…`), con el ExecStart de la unidad +
  `--modo-panel v2 --cadena-v2-dir /home/m4rk/feed-v2 --modo-respuesta sombra`.
- **Journal.** «panel: modo v2, cadena desde /home/m4rk/feed-v2 (modo sombra); «Preparar demo» deshabilitado».
- **Correspondencia con datos reales.** 3 911 decisiones, 120 ALERT. Las 120 señales α son el mismo conjunto que
  `senales-if`, y todas las decisiones son PERMIT.
- **Solo lectura.** Desde el bastión: GET sin sesión 401 y POST 409. `preparar.json` no cambió.

### 4.3 Comprobación visual con sesión iniciada (04-nov, 06:45–06:47 UTC)

Mark inició la sesión en su Chrome. Claude la leyó con la extensión, sin introducir ni ver credenciales y sin
pulsar acciones.

- **Franja.** «Cadena v2 · política if_senal · modo sombra (las medidas son propuestas; no se ejecutan) · …
  fuentes: señales IF ok, traza ok, feed ok · agente: desconocido desde el sensor · efecto: sin evidencia · panel
  de solo lectura». En `/api/status`: `estado: ok`, `incidencias: []`.
- **ALERT real de 10.10.20.24 (06:46:06 UTC).**
  - «1A · IF del motor: decision_if ALERT · score −0,5706 · umbral −0,5694»;
  - «1B · Señal α publicada: α superados 0.05»;
  - medida «sin medida publicada»; aplicación «no aplica (ausencia de medida demostrada)»;
  - agente «desconocido»; efecto «sin evidencia».
- **Decisión posterior a la cobertura** (`logged_at` 06:46:57 frente a la cobertura 06:46:47,3): 1B «pendiente ·
  posterior a la última publicación», medida «pendiente», aplicación «desconocido (sin evidencia)».
- **Decisión anterior a la cobertura:** «sin señal α (procesada por el publicador)».
- **«Preparar demo».** `hidden`, `disabled`, no visible.
- **Lo que confirmó Mark.** Su «sí» a los cuatro puntos antes de esta lectura.

**Agente.** Queda «desconocido» en el panel a propósito: el sensor no recibe su traza. La verificación directa se
hizo en srv-dmz (§5).

## 5. v1 residual (parte 3)

### 5.1 Antes de tocar nada

Se guardaron el estado, las unidades, los temporizadores, los procesos, el mtime de los feeds y el ruleset:
- Sensor1: `evidencia/06-sensor1-remoto/sudo-A-20261104T061245Z/`;
- bastión: `evidencia/07-bastion-remoto/sudo-bastion-20261104T061209Z/`.

### 5.2 Qué se retiró

| Host | Componente | Antes | Después |
|---|---|---|---|
| Sensor1 | `ppi-publicar-feed.timer` → `publicar_feed.py` → `~/feed/feed.json` | active / enabled, cada 10 s | **inactive / disabled**; `feed.json` parado en 06:12:40 (igual a las 07:28) |
| Bastión | `ppi-relay-feed.timer` → `relay-feed.sh` (`b5005113…`) → `adminsrvdmz:~/enforce` | active / enabled | **inactive / disabled**; `~/enforce` parado en 06:12:05 (igual a las 07:28) |

Los ficheros, feeds y registros se conservan.

### 5.3 Lo que no se tocó

- **Agente v1 de srv-dmz** (`ppi-enforce-agent.timer`): sigue **inactive / disabled**.
- **Cadena v2:**
  - `ppi-publicar-feed-v2` (Sensor1), `ppi-relay-eventos` (bastión) y `ppi-enforce-agent-v2-dmz` (srv-dmz,
    **sin `--aplicar`**) siguen active.
  - En la ventana, el agente v2 tuvo **179 recepciones, todas «aceptado»** (secuencias 767 → 945).

### 5.4 Sin aplicación y sin cambios de reglas

- Ningún proceso con `--aplicar` ni `--enforce` en los tres hosts.
- 0 eventos de aplicación.
- Ruleset de srv-dmz `e3b0c442…` (vacío, igual a la base); ruleset de Sensor1 `24c320e3…` (igual antes y después).

### 5.5 Un rechazo transitorio (observación nueva, no causada por estos cambios)

- **Qué pasó.** A las 06:26:26,99 UTC el agente v2 registró **1 `rechazo` por `firma_invalida`**. Es el único en
  932 líneas desde las 02:18.
- **Recuperación.** A los 0,5 s aceptó la secuencia 765, la pareja publicada a las 06:26:26,30. No se perdió
  ninguna secuencia.
- **Causa probable, no demostrada.** El relé v2 entrega en dos `mv` (primero la firma y después el feed). Si el
  agente lee justo entre los dos, ve una pareja incoherente.
- **Relación con este cierre.** Ninguna: el relé v1 escribía en otro directorio.
- **Efecto en la 4B.** En modo activo, un rechazo así retrasaría una medida un ciclo. Queda como pendiente P4.
- Evidencia: `evidencia/03-v1/out_d_rechazo.txt` y `out_b_rechazo.txt`.

### 5.6 Reversión

`revertir_cierre4a.sh publicador-v1` (Sensor1) o `rele-v1` (bastión). Cada uno vuelve a habilitar **solo** su
temporizador. Ninguna pieza arranca el agente v1 ni carga restricciones de la demo.

## 6. Ensayo del anillo de Suricata (parte 4)

### 6.1 Antes del cambio

- **Versión.** Suricata 7.0.3.
- **af-packet de ens37:** `cluster_flow`, `cluster-id 99`, `defrag yes`, `checksum-checks no`. Sin fijar:
  `ring-size`, `use-mmap`, `tpacket-v3`, `block-size` y `threads` (4 workers).
- **Anillo real**, leído de `/proc/<pid>/maps`: **4 mapeos de socket, 3,2 MiB en total**. El mmap estaba activo,
  así que `ring-size` sí aplica.
- **Criterios.** Se declararon y fijaron **antes** de medir: `CRITERIOS-ENSAYO-ANILLO.md`, sha `6c6cbbee…`,
  registrado en Sensor1 a las 06:04:59 UTC (`evidencia/06-sensor1-remoto/previo/`).
- **Contadores previos.** 82 529 descartes acumulados (PID 1372, 4 d 10 h). De ellos, 238 entre las 05:34 y las
  06:04, ya en este cierre y sin cambios.

### 6.2 Aplicación (fase B; Mark, 06:16:51–06:17:12 UTC)

1. Comprobación de que el YAML era el medido (`8e084b7d…`). Respaldo con hash.
2. Candidato con **una sola línea añadida** (diff 615a616). `--dump-config` muestra `af-packet.0.ring-size = 16384`.
3. `suricata -T` sobre el candidato: **rc=0**. Se instaló. `-T` sobre la ruta real: **rc=0**. Código de salida real,
   sin tubería.
4. Reinicio: el motor arrancó a las 06:16:55 («Engine started», W:4). PID 1708643, NRestarts 0.
5. **Anillo real después: 4 mapeos, 102,5 MiB.**

No se tocaron los hilos, el offloading, el anillo de la NIC ni `rmem`.

### 6.3 Resultado, con el mismo método (`comparar_suricata.py`, eventos `stats` de EVE)

| | Base 4A (02:19:45–03:19:51) | Calentamiento (06:16:55–06:26:55) | **Ensayo (06:26:55–07:26:55)** |
|---|---|---|---|
| Intervalos de 8 s válidos / hueco máximo | 450 / 8 s | 73 / 8 s | **449 / 8 s** (cobertura 3 592 s) |
| Reinicios dentro | 0 | 0 | **0** |
| Paquetes | 936 761 | 173 380 | **1 193 578** |
| Descartes (por millón) | 7 (7,47) | 0 | **0 (0,00)** |
| Intervalos con descartes | 1 (03:05:47) | 0 | **0** |
| Paquetes por 8 s: p50 / p95 / máx | 1 856 / 4 306 / 7 168 | 1 467 / 5 253 / 14 169 | **1 477 / 7 437 / 19 406** |
| Máximo de pps en un intervalo | 896 | 1 771 | **2 426** |
| Ráfagas ≥ 5 000 por 8 s (umbral ≥ 9) | 11 | 5 | **68** |
| Flujos ≥ 1 000 paquetes (umbral ≥ 50) / sus paquetes | 63 / 88 747 | 20 / 37 312 | **79 / 399 823** |
| Hacia srv-dmz, principales clientes (flujos / paquetes) | .22 471/84 062 · .23 108/69 246 · .26 111/19 191 | — | .22 512/90 590 · .23 95/45 160 · .26 112/27 736 |

**Carga.** Es **comparable, y mayor** que la base: se cumplen los dos umbrales declarados. Los perfiles legítimos de
fondo eran los mismos y no hubo ataques. La intensidad se registró, no se eligió.

**Recursos** (`analizar_fino.py`; 3 599 muestras a 1 s; hueco máximo 1,01 s; 0 errores; un solo PID):

| | Anillo viejo (06:05–06:12) | **Ensayo** |
|---|---|---|
| CPU del hilo de Suricata más cargado: p95 / máx | 1 / 2 % | 2 / **5 %** |
| softirq del host: p95 / máx | 0,5 / 1,0 % | 0,5 / 2,3 % |
| iowait: máx | 0,3 % | 0,5 % |
| Disco, ms en E/S por s: p95 / máx | 3 / 17 | 2 / 13 |
| softnet dropped / time_squeeze | 0 / 18 | **0** / 169 |
| NIC `rx_missed` / `rx_fifo` | 0 / 0 | **0 / 0** |
| NIC `rx_dropped` | 6 345 | 50 505 (≈14/s, constante; tramas sin manejador, ya en la 4A) |
| `MemAvailable` mínima | 5,7 GB | **5,2 GB** |
| RSS de Suricata | 121 MB | 168 → 173 MB (+≈100 MB: el anillo mayor) |
| Parada máxima de eve.json | 3 s | 5 s |

**Interpretación.**
- **Sin saturación.** No hay ninguna de CPU, softirq, disco ni memoria. `time_squeeze` sube con el tráfico, pero
  sin `dropped`.
- **El ensayo no deja ver qué recurso se saturaba antes.** Con el anillo viejo y el muestreo a 1 s no se registró
  ningún descarte, así que la causa de los descartes antiguos sigue sin demostrarse.

**Estabilidad y continuidad.**
- **EVE.** Hueco del reinicio ≈ 1,75 s (último evento 06:16:51,40; primero 06:16:53,15). Sin paradas de más de 5 s
  después.
- **Captura.** La de tcpdump no se tocó: 0 descartes del kernel y 122 lecturas SIGUSR1 en la ventana, tanto en el
  anillo como en la vía rápida.
- **Motor y vía rápida** en la ventana: §3.3.
- **Reversión.** No se cumplió ningún criterio, ni en el control de mitad (07:01) ni al final. No se revirtió.

**Veredicto del ensayo: compatible con la hipótesis.**
- Con carga comparable, y de hecho mayor, hubo 0 descartes frente a 7,47 por millón.
- No se cumplió ningún criterio de reversión y no apareció saturación nueva.
- **No demuestra la causa ni refuta otras.**
  - Con la tasa de fondo del 04-nov (≈1,2 episodios por hora), una hora sin episodios tendría una probabilidad
    del ≈30 % por azar.
  - Si los episodios se deben a las ráfagas (base del 04-nov: 7 episodios en 73 ráfagas), esa probabilidad bajaría
    al ≈0,15 %. Pero eso supone precisamente la hipótesis.
- **No se repitió el intervalo.** Se mantiene el cambio, y las dos medidas se conservan.

### 6.4 Lo que el ensayo destapó sobre la medición (afecta a I5 y a la 4C)

1. **`stats.log` omite los ceros.** Con `null-values` por defecto, Suricata 7 no escribe los contadores que valen 0.
   Desde el reinicio, **ninguno de los 106 primeros bloques trae `capture.kernel_drops`**
   (`evidencia/04-suricata/out_stats_ceros.txt`). `salud_captura` (ec78ca5) busca ese contador, así que cuando no
   hay descartes **no puede certificarlo** y la ventana sale **C3: «Suricata sin medida completa»**. No inventa un
   cero, lo cual es correcto, pero **con la herramienta congelada I5 no se puede cumplir nunca**.
   - Los eventos `stats` de EVE sí escriben `"kernel_drops": 0`. Leída desde EVE, la base de la 4A es idéntica a la
     de `stats.log` (`out_base_eve.txt`).
2. **Bloque viejo tras un reinicio.** Durante unos 20 min, el «último bloque con kernel_drops» de la cola de 1 MiB
   fue el del **proceso anterior** (PID 1372, uptime de días). `salud_captura` lo siguió devolviendo, y por eso
   `clasificar_periodo` muestra un segmento hasta las 06:36 con los contadores viejos. Esas lecturas no generan
   incrementos válidos («mismo bloque»), pero **el reinicio no se detecta por esa vía**.

Ninguna de las dos se corrigió aquí: habría que modificar la herramienta congelada o hacer un segundo cambio de
configuración en mitad del ensayo. Pasan a P1.

## 7. Calidad de captura y clasificación (parte 5)

- **Herramientas nuevas** (rama de herramientas), probadas en banco:
  - `clasificar_periodo.py`: envuelve `salud_captura` sin modificarlo. Reporta el anillo y la vía rápida por
    separado. Cuenta como `no_evaluable` las lecturas SIGUSR1 sin margen, la falta de continuidad de PID o un periodo
    fuera de las muestras. Segmenta Suricata por reinicio y no recorta los límites. Banco P1–P6 **10/10**.
  - `comparar_suricata.py`: segmentado por uptime. El incremento que cruza un reinicio no se usa. Admite `stats.log`
    o EVE `stats`.
  - `analizar_fino.py`: un dato que falta cuenta como «no legible», nunca como 0.
- **Clase de la ventana del ensayo, con los criterios congelados: C3 para el anillo y para la vía rápida.**
  - El único motivo es «Suricata sin medida completa» (§6.4).
  - La parte de tcpdump está bien: `cobertura_tcpdump_ok`, 0 descartes, 122 lecturas, un PID por captura.
  - **No se reclasifica.** Por los EVE `stats`, la ventana tiene 0 descartes de Suricata, pero la clase oficial
    sigue siendo C3 mientras no se resuelva P1.
- **I5 y C0 no cambian.** I5 sigue exigiendo 0 descartes en los 30 min previos a la 4C, y la población principal
  sigue siendo C0.

## 8. Validaciones por separado

| Validación | Resultado |
|---|---|
| Instalación (hashes, versiones, v2 activa, v1 apagada, sin `--aplicar`/`--enforce`, 0 aplicaciones, ruleset de base) | **OK** |
| Panel (pruebas, despliegue y comprobación visual con sesión) | **OK**; el agente queda «desconocido» a propósito |
| Calidad de captura (tcpdump) | **OK**: 0 descartes y cobertura completa |
| Calidad de captura (Suricata, herramienta congelada) | **C3, no evaluable** (§6.4) |
| Ensayo del anillo | **Compatible con la hipótesis**; no demostrada |

## 9. Correcciones de texto en la 4A

En `../etapa4a-instalacion-2026-11-04/` se añadieron notas marcadas como «**Corrección (cierre complementario,
04-nov)**»:
- **README §8:** `ps %CPU` es la media de toda la vida del proceso, y el porcentaje de disco usado no es latencia,
  así que ni la CPU ni el disco quedaban descartados. La coincidencia con las descargas es una correlación.
- **PROPUESTA §1:** se corrige la frase «La CPU, el disco y la rotación están descartados como causa».
- **PROPUESTA (estado):** se anota que se ensayó.
- **README (veredicto):** se añade el enlace a este cierre.

El texto original y la evidencia se conservan. Su `MANIFIESTO.sha256` se regeneró, porque cambian dos `.md`; las
líneas de `evidencia/` no cambiaron.

## 10. Respaldos y reversión

| Qué | Respaldo | Revertir |
|---|---|---|
| Panel a27889d | Sensor1 `~/respaldos-etapa4/panel-20261104T054553Z` (+ SHA256SUMS) | Copiar los dos `.py` y reiniciar `ppi-dashboard` |
| Drop-in del panel | — | `sudo bash …/revertir_cierre4a.sh panel` (el defecto del código sigue siendo v2) |
| Primer PCAP | — | `… pcap` (vuelve el primer fichero ilegible; reinicia captura y motor) |
| Suricata | `/etc/suricata/suricata.yaml.respaldo-cierre4a-20261104T061651Z` (`8e084b7d…`) y `evidencia/06-sensor1-remoto/sudo-B-*/suricata.yaml.antes` | `… suricata /etc/suricata/suricata.yaml.respaldo-cierre4a-20261104T061651Z` (verifica el hash y `-T` con rc real antes de reiniciar) |
| Publicador v1 | Unidades en `sudo-A-*/etc/` | `… publicador-v1` |
| Relé v1 | Unidades en `sudo-bastion-*/etc/` | `… rele-v1` (bastión) |

La reversión **nunca** arranca `ppi-enforce-agent` (v1, con `--aplicar`) ni carga restricciones de la demo.
`revertir_cierre4a.sh` está en Sensor1 en `~/cf-e4/cierre4a/herr/` y en el bastión en `~/cierre4a/`.

## 11. Pendientes y efecto en la siguiente fase

| # | Pendiente | Efecto |
|---|---|---|
| **P1** | **Medición de I5 y C0 con Suricata 7.** Elegir entre activar `null-values: yes` en `stats.log` (otro cambio de configuración, con su propio respaldo y prueba) o una nueva versión de `salud_captura` que lea EVE `stats` y detecte el reinicio por uptime o PID, no por «último bloque». Hay que congelarla y probarla antes | **Bloquea el inicio de la 4C.** Sin esto, ninguna ventana puede ser C0 por Suricata e I5 no se puede demostrar. No flexibiliza I5 |
| P2 | El ensayo del anillo duró 1 h: hace falta más observación con carga real | La 4B puede prepararse con el anillo en 16384, vigilando los descartes con EVE `stats` |
| P3 | `Requires=` del motor: cualquier reinicio de la captura reinicia el motor | Planificarlo en la 4B: cada reinicio abre un intervalo de arranque, que se excluye |
| P4 | Rechazo transitorio de firma en el agente v2 (§5.5) | En modo activo retrasaría una medida un ciclo; revisar la entrega de la pareja antes de activar |
| P5 | En `cierre4a_*.sh`, el `SHA256SUMS` de `salida.txt` se calcula antes de la última línea (falla solo ese fichero en las 3 carpetas) | Solo documental. El MANIFIESTO de esta carpeta usa los bytes finales |
| P6 | El panel no ve al agente | Conocido; se verifica en srv-dmz |

**¿Se puede preparar la 4B?** **Sí**, con estas limitaciones: el anillo en 16384, la vigilancia con EVE `stats` y la
planificación de reinicios (P3). **No se puede iniciar la 4C** hasta cerrar P1.

## 12. Evidencia

```
README.md                         este informe
MANIFIESTO.sha256                 sha256 de cada fichero (bytes publicados), dos espacios, orden LC_ALL=C sort -f
evidencia/
  00-referencias/                 hashes congelados y motor_startup (s1_hashes.sh → out_hashes.txt)
  01-panel/                       pruebas, despliegue, correspondencia con datos reales, acceso desde el bastión
  02-pcap/                        diagnóstico, reproducción con strace, verificación del arranque y de las rotaciones
  03-v1/                          estado v1/v2 antes, después y al final; rechazo del agente
  04-suricata/                    configuración, bases, ceros de stats.log, muestreo, controles y análisis final
    ensayo-sensor1/               salida del análisis en Sensor1 (con su SHA256SUMS verificado)
  05-herramientas/                banco de clasificar_periodo, lint y copias verificadas
  06-sensor1-remoto/              previo/, sudo-A-*/, sudo-B-*/ y bases JSON tal como se generaron en Sensor1
  07-bastion-remoto/              sudo-bastion-*/
```

Los guiones de las herramientas están versionados en la rama de herramientas; aquí van los de verificación. Las
copias completas del muestreo (`muestras.jsonl`, `fino.jsonl`) son las de `ensayo-sensor1/` (`*-copia.jsonl`, hechas
a las 07:28).
