# Paso 1 — corrección y validación offline del motor (31-oct / 1-nov-2026)

**Conclusión:** el candidato está **listo para la validación en vivo del paso 2**, con las condiciones de la
sección 10. Toma las mismas decisiones que 7b275b8 en toda la campaña A grabada, y offline ningún ciclo en régimen
estable supera 9,5 s, tampoco en la inundación HTTP. Que funcione en vivo está por comprobar y es el objeto del paso 2.

## 1. Problema que se corrige

En la campaña A del 29-oct, el motor desplegado (7b275b8) tardó hasta 43 s por ciclo con carga: p50 15,6 s y 131
huecos de más de 20 s. Ningún episodio fue evaluable (0/25), porque el criterio preregistrado exige cobertura continua
con una tolerancia de 20 s.

La causa quedó investigada en el commit 2defae7: cada ciclo recalculaba sobre los 230 s de historia la deduplicación
del espejo, la atribución de flujos, las observaciones EVE y, sobre todo, `build_rows`. El coste crecía con el tráfico
retenido, no con el tráfico nuevo. R1 lo confirma: en la inundación, `build_rows` tarda una mediana de 17,8 s y un
máximo de 26,9 s.

## 2. Qué cambia y qué no

**Repositorio del código:** `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`.

- **Rama:** `candidato/motor-rendimiento-20261031`, que parte de 7b275b8. No se fusionó a main.
- **URL:** <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/candidato/motor-rendimiento-20261031>

| Commit | Contenido |
|---|---|
| `4552d83` | Procesamiento incremental, puntuación en lote, instrumentación por ciclo, arnés de replay y pruebas |
| `9b4cf2b` | `logged_at` vuelve a ser el instante de escritura; se añaden `decidido_en` y `registro_escrito_en` (sección 6) |
| `24f8a80` | logrotate también rota `_state/ciclos.jsonl` (solo el generador de configuración; el motor no cambia) |

| Archivo (24f8a80) | sha256 |
|---|---|
| `scripts/engine/motor_decision.py` | `6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e` |
| `scripts/engine/motor_incremental.py` (nuevo) | `a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168` |
| `scripts/engine/replay_motor.py` (nuevo, solo offline) | `c93c80c8e313bc1eabfdc6024bae0381136a441d4e231a8492bb298299fc44c7` |
| `scripts/setup/cyberflow_config.py` | `6d5fcb60cb74cee21aa7bead2b520f0e2295683b4df0e4e342ddc42a54e5449f` |
| Referencia: `motor_decision.py` de 7b275b8, el desplegado | `e2b2eb535091ea0fb7aa08054aa8cc4eff295a4e678269cba5d4a5ee5d95bc73` |

Cambios en el ciclo:

1. **Deduplicación incremental.** Vuelve a ejecutar la `deduplicar_espejo` congelada solo en los grupos de claves
   que tocan los paquetes nuevos o podados. El resultado es la misma lista, con los mismos objetos y el mismo orden.
2. **Atribución incremental.** Vuelve a ejecutar la `attribute_packets` congelada solo en los flujos canónicos que
   cambiaron, incluido el cambio de iniciador cuando la poda se lleva el SYN.
3. **EVE por línea.** Las observaciones L7 se calculan una vez por línea con la `load_app_observations` congelada.
   Por eso ya no se vuelca ni se escribe `eve_window.jsonl`.
4. **Solo filas pendientes.** Por entidad, `build_rows` se ejecuta desde A_min, la primera ancla del rango aún no
   puntuada, conservando las observaciones necesarias (30 s antes para paquetes, 60 s antes para L7). No se usa la regla
   rechazada «última ventana + 10 s».
5. **Puntuación en un solo lote por ciclo.** Es bit a bit igual a una llamada por fila, y se comprueba en cada ciclo
   verificado.
6. **Registro escrito una vez por ciclo** e instrumentación en `_state/ciclos.jsonl`: inicio y fin, duración por
   etapa, marcas de disponibilidad de PCAP y EVE, y contadores (procesadas, pendientes, no evaluadas, no elegibles,
   excluidas, flujos recalculados).

**No cambian:**
- el modelo IF, el escalador, las 28 características, los heurísticos, el umbral y los parámetros de ataque;
- la historia de 230 s, las ventanas de 10/30/60 s, las reglas de deduplicación y la atribución de flujos;
- las reglas de elegibilidad y el criterio del analizador.

`extract_multilayer_v2.py` (`7130edae…`), `extract_multilayer_v3.py` (`5adbfbf4…`) y `heuristicos.py` (`10deb05d…`)
son idénticos byte a byte en 7b275b8, en el candidato y en el sensor.

## 3. Método

- **Arnés `scripts/engine/replay_motor.py`.** Ejecuta el `main()` real de cada versión, sin modificarlo, sobre la
  evidencia congelada de la campaña A.
  - **Entradas:** `/home/m4rk/cf-campana-A-20261029`, con `eve.json` de 1 175 076 líneas (sha256 `54e1882f…`) y 816
    PCAP (sha256 de su concatenación `8fa86de6…`).
  - **Reloj:** simulado, con una retícula fija de 10 s, la misma para las dos versiones. Cada ciclo ve exactamente los
    mismos datos aunque una versión tarde más que la otra.
  - **PCAP:** un fichero existe desde la hora de su nombre y se considera cerrado cuando existe el siguiente.
  - **EVE:** se lee en el orden del fichero; una línea cuenta como escrita cuando el reloj alcanza el máximo acumulado
    de los timestamps.
- **Tramo.** De 2026-10-29 07:15:10 a 10:39:20 UTC, todo el tramo con PCAP archivado: 1225 ciclos más el de
  arranque.
- **Argumentos.** Los del servicio `ppi-motor`, con el modelo, el manifiesto y el esquema desplegados
  (`evidencia/herramientas/args-motor.txt`).
- **Dónde y cómo.** En el Sensor1 (4 vCPU, 8 GB, Python 3.14.4, scikit-learn 1.9.0), con `nice -n 15` y el motor
  desplegado en sombra activo. Comandos: `evidencia/herramientas/corridas.sh`, `fase_c.sh` y `r5.sh`.

| Corrida | Motor | Qué mide | Concurrencia | Duración real | RSS máx. | rc |
|---|---|---|---|---|---|---|
| R1 | 7b275b8 (`--perfilar`) | referencia de registros y tiempos | sola | 3 h 47 min | 0,86 GB | 0 |
| R2 | 4552d83 + `--verificar-equivalencia` | equivalencia etapa por etapa en los 1225 ciclos | con R4 | 3 h 59 min | 1,42 GB | 0 |
| R3 | 9b4cf2b, sin verificación | tiempos del candidato y registros frente a R1 | sola | 29 min | 1,34 GB | 0 |
| R4 ref / R4 cand | 7b275b8 / 4552d83 (+ verificación) | reinicio a las 09:05, a mitad de la inundación (08:55–09:20) | con R2 | 54 / 58 min | 0,80 / 1,23 GB | 0 |
| R4-9b4cf2b | 9b4cf2b + verificación | el mismo reinicio sobre el código final | sola | 55 min | 1,24 GB | 0 |
| R5 | 9b4cf2b, sin verificación | tiempos limpios del reinicio | sola | 7 min | 1,18 GB | 0 |

Ninguna corrida se interrumpió ni se repitió. Las duraciones de R2 y R4 no se usan como medida de rendimiento: en R2
y R4-cand la verificación recalcula cada ciclo también por la vía global, y la referencia de R4 corrió en paralelo con
R2. Los tiempos del candidato salen de R3 y R5.

## 4. Equivalencia

Detalle completo en `RESULTADOS.md` y `evidencia/resumen.json`.

**Registro completo, R1 (7b275b8) frente a R3 (9b4cf2b):**
- Los **16 069 registros son iguales**: 16 068 de decisión o ventana no evaluada, más el de arranque.
- Mismas claves (`entity_ip`, `window_end_utc`), mismo orden de emisión y los mismos valores en todos los campos:
  `score`, `decision`, `detector_name`, `heuristico`, `threshold`, `packet_count_10s`, `history_coverage_s`,
  `pendiente_desde`, `inicio_ciclo`, `marca_pcap`, `marca_eve`, contadores y `logged_at`.
- 0 duplicados en cada lado.
- Contenido: 14 081 PERMIT, 1 986 ALERT, 4 965 sin `score` (ventanas sin paquetes, que decide el heurístico), 9 089
  con `pendiente_desde`, y 1 `ventana_no_evaluada` (`ventana_no_regenerada`) idéntica en los dos.
- R2 (4552d83) da el mismo resultado frente a R1 y frente a R3.

**Campo excluido de la comparación:** solo `decidido_en`, que no existe en 7b275b8. Se comprobó aparte que
`decidido_en` ≤ `logged_at` en los 16 068 registros.

**Características.** El registro de decisión no contiene las 28 características. Su igualdad se comprueba en la
verificación etapa por etapa, que compara las filas completas.

**Verificación etapa por etapa (`--verificar-equivalencia`):** en cada ciclo se recalcula por la vía global de
7b275b8 y se compara deduplicación (mismos objetos y orden), atribución, observaciones EVE, filas completas, cobertura
de las ventanas que 7b275b8 habría decidido y puntuación en lote frente a una llamada por fila.

| Corrida | Ciclos verificados | Con alguna diferencia | Filas necesarias cubiertas | Filas puntuadas en lote |
|---|---:|---:|---:|---:|
| R2 (4552d83, campaña completa) | 1225 | **0** | 36 248 | 20 297 |
| R4 (4552d83, reinicio) | 151 | **0** | 5 431 | 3 020 |
| R4-9b4cf2b (código final, reinicio) | 151 | **0** | 5 431 | 3 020 |

**Reinicio a mitad de la inundación (09:05):** los 2300 registros de 7b275b8 coinciden con los de 4552d83, con los
de 9b4cf2b con verificación y con los de 9b4cf2b sin ella (R5). Mismo orden, dos arranques en cada lado y 0
duplicados, también a través del reinicio.

**Casos que el replay no cubre**, probados en `tests/test_motor_incremental.py` (sección 7):
- duplicados del espejo que cruzan el borde de un fichero;
- cambio de propietario de un flujo al podar el SYN;
- huecos y ventanas no elegibles;
- entidades excluidas;
- EVE por línea;
- puntuación en lote;
- tiempos de registro;
- escenario sintético con reinicio, hueco de PCAP (`pcap_incompleto`), entidad solo L7, entidad excluida o fuera de la
  red y servidor que pasa a ser entidad.

## 5. Tiempos por condición (offline)

> Son mediciones **offline** de tiempo de procesamiento en el Sensor1 con entradas congeladas. **No son latencias de
> detección en vivo** ni garantizan el funcionamiento en vivo. Esa medida es el paso 2.

**Cómo se mide:**
- **Duración del ciclo:** tiempo real desde el inicio del ciclo hasta su `sleep`.
- **Presupuesto:** 10 s, el paso del motor; se informa también > 9,5 s.
- **Condición:** se asigna por la hora simulada del ciclo con las marcas de la campaña.
  - Inundación: [inicio, fin + 30 s) de cada `inundacion_http`.
  - Recuperación: los 230 s siguientes.
  - Otros escenarios: escaneos, DNS y fuerza bruta.
- **Fuera del régimen estable:** el primer ciclo tras arrancar y el calentamiento (230 s) se informan aparte.

| Condición | 7b275b8 (R1): mediana / p95 / máx (s) | > 9,5 s | > 10 s | Candidato (R3): mediana / p95 / máx (s) | > 9,5 s | > 10 s |
|---|---|---:|---:|---|---:|---:|
| Control normal 08:01–08:35 (n = 205) | 7,74 / 9,69 / 10,13 | 13 | 6 | **1,07 / 1,70 / 2,35** | 0 | 0 |
| Normal fuera de episodios (n = 657) | 8,26 / 18,98 / 20,80 | 242 | 218 | **0,88 / 2,01 / 2,88** | 0 | 0 |
| Otros escenarios (n = 176) | 10,61 / 17,96 / 20,60 | 117 | 104 | **1,57 / 3,90 / 5,23** | 0 | 0 |
| Inundación HTTP (n = 60) | 24,10 / 33,38 / 34,46 | 60 | 60 | **4,92 / 8,26 / 9,20** | 0 | 0 |
| Recuperación tras la inundación (n = 105) | 33,67 / 36,77 / 37,98 | 103 | 102 | **2,45 / 3,42 / 4,22** | 0 | 0 |
| **Todo el régimen estable (n = 1203)** | 9,00 / 33,40 / 37,98 | 535 | 490 | **1,23 / 3,55 / 9,20** | **0** | **0** |
| Calentamiento (n = 22) | 0,57 / 1,40 / 1,51 | 0 | 0 | 0,15 / 0,31 / 0,42 | 0 | 0 |
| Primer ciclo tras arrancar (07:15, tráfico normal) | 1,60 | — | — | 1,61 | — | — |

**Etapas en la inundación HTTP**, mediana / p95 / máx en s:

| Etapa | 7b275b8 (R1, funciones envueltas) | Candidato (R3, etapas del motor) |
|---|---|---|
| `build_rows` / `filas` | 17,78 / 25,91 / 26,93 | 1,78 / 3,34 / 3,54 |
| atribución | 2,51 / 3,59 / 3,87 | 0,78 / 1,32 / 1,92 |
| parseo de PCAP | 1,66 / 1,99 / 2,05 | 1,12 / 2,14 / 2,31 |
| deduplicación | 0,50 / 0,71 / 0,73 | 1,01 / 1,41 / 1,56 |
| observaciones EVE | 1,05 / 1,38 / 1,42 | 0,02 / 0,03 / 0,03 |
| puntuación | 0,93 / 1,48 / 1,67 | 0,06 / 0,06 / 0,07 |
| ciclo completo | 24,10 / 33,38 / 34,46 | 4,92 / 8,26 / 9,20 |

En el candidato, el ciclo de inundación queda repartido entre `filas`, parseo de PCAP, deduplicación y atribución. No
hay una etapa que lo domine: el parseo de PCAP de los ficheros nuevos ya es trabajo proporcional al tráfico entrante.

La deduplicación incremental del candidato mide más que la global de R1, porque las dos herramientas acotan la etapa
de forma distinta: el arnés envuelve solo la función, mientras que la etapa del motor incluye mantener el anillo y los
mapas de llegada. El ciclo completo es la cifra comparable.

**Reinicio a las 09:05, en plena inundación (R5, candidato solo):**

| Tramo | Mediana / p95 / máx (s) |
|---|---|
| Primer ciclo tras arrancar | 28,32 s (08:55) y 23,33 s (09:05) |
| Calentamiento (n = 44, duración medida por el arnés) | 2,37 / 5,40 / 7,28 |
| Inundación (duración que registra el motor) | 5,18 / 8,20 / 8,50 |
| Recuperación (duración que registra el motor) | 2,63 / 3,31 / 3,64 |

El primer ciclo tras arrancar con la historia cargada de inundación es la **única** excepción al presupuesto. Tiene que
parsear los 230 s de PCAP ya presentes en el anillo (13 s), además de atribuirlos (5 s) y deduplicarlos (4,5 s). La
referencia paga el mismo coste y tarda más: 34 y 45 s en R4, aunque esa referencia corrió en paralelo con R2. Con
tráfico normal, ese primer ciclo tarda 1,6 s.

## 6. Instrumentación temporal: decidir frente a quedar disponible

Con la escritura en lote de 4552d83, `logged_at` se asignaba al decidir y la línea se escribía al final del ciclo.
`publicar_feed.py` y el analizador de campaña leen `logged_at` como instante de escritura o emisión. Se corrigió en
9b4cf2b:

| Campo | Dónde | Significado |
|---|---|---|
| `decidido_en` | `decision` y `ventana_no_evaluada` | momento en que el motor toma la decisión o expira la ventana |
| `logged_at` | `decision` y `ventana_no_evaluada` | instante de escritura: se asigna a todo el lote justo antes del `write`, igual que en 7b275b8, que escribía cada registro al decidirlo. Es una cota inferior de la disponibilidad, no una prueba de ella. |
| `registro_escrito_en` | `ciclos.jsonl`, una vez por ciclo | tomado al cerrar el fichero: el registro ya es visible para los consumidores. Es la marca de disponibilidad efectiva y se cruza con las decisiones por `inicio_ciclo`. |
| `registros_escritos` | `ciclos.jsonl` | número de líneas escritas en ese ciclo |

Las alertas se imprimen en stdout después de escribirse en el registro. El analizador no necesita cambios: `logged_at`
conserva su significado y los campos nuevos los ignora.

**Pruebas:**
- `TiemposDeRegistro` usa un reloj que mira el fichero en cada lectura. Comprueba que `logged_at` se toma con la línea
  aún no visible y `registro_escrito_en` con la línea ya visible.
- El escenario de extremo a extremo comprueba `decidido_en` ≤ `logged_at` ≤ `registro_escrito_en` y el conteo de
  líneas por ciclo.

**Efecto en las comparaciones:** en el replay, `time.time()` es la hora simulada del ciclo, así que `logged_at`
coincide con 7b275b8. Solo se excluye `decidido_en`. R2 y R4 (4552d83) se repitieron donde el cambio podía afectar:
R3 frente a R1 completo, R4-9b4cf2b con verificación y R5.

**Efecto en los tiempos:** solo cambia de sitio la serialización JSON. R3 y R5 se midieron ya con 9b4cf2b.

## 7. Pruebas

| Dónde | Código | Resultado |
|---|---|---|
| Sensor1, `unittest` completo | 7b275b8 | 449 OK (1 omitida) |
| Sensor1 | 4552d83 | 458 OK (1 omitida) |
| Sensor1 | **24f8a80** | **460 OK (1 omitida)** — `evidencia/pruebas-unittest-24f8a80-sensor.txt` |
| Portátil (Windows, pytest) | 24f8a80 | `test_motor_incremental`, `test_motor_completitud`, `test_publicar_feed` y `test_cyberflow_config`: OK. Fuera del motor, 4 pruebas fallan solo en Windows (`bash -n`, firma con claves, socket y discos) y pasan en Linux. |

## 8. Incidencias

- **Comillas en la terminal de Windows.** Varios comandos remotos se rompieron por el escape de PowerShell y no
  llegaron a ejecutarse; se resolvió subiendo scripts. Uno dejó sin subir `r5.sh`, y su sesión de tmux terminó al
  instante sin hacer nada; se subió y se relanzó. Ninguna corrida se vio afectada.
- **Esperas cerradas por memoria.** El sistema cerró por falta de memoria las esperas en segundo plano del portátil.
  Las corridas en el sensor, en tmux, siguieron sin interrupción.
- **Primer commit sin mensaje.** El primer intento de commit falló porque el mensaje no llegó, y solo se publicó la
  rama apuntando a 7b275b8. Quedó superado por 4552d83.
- **Prueba nueva que fallaba en Windows.** `test_motor_incremental` fallaba en Windows porque el EVE sintético se
  escribía con `\r\n`. Se corrigió la prueba, que ahora escribe `\n` como Suricata; el motor no cambió.

## 9. Limitaciones

- **Tiempos offline.** No son latencias en vivo. En vivo compiten Suricata, tcpdump, el panel y la E/S real de disco;
  la medida en vivo es el paso 2.
- **Arnés de replay.**
  - Aproxima cuándo existen los datos: máximo acumulado de timestamps para EVE y fichero siguiente para PCAP.
  - Usa una retícula fija de 10 s. Compara el trabajo por ciclo con entradas idénticas, no la cadencia en vivo.
- **Margen en la inundación.** El máximo offline es 9,2 s, con p95 de 8,3 s: cabe en el presupuesto, pero con poco
  margen. Con más carga en vivo o un ataque más intenso podría superarlo; el paso 2 debe medirlo.
- **Reinicio con carga.** El primer ciclo tras arrancar con la historia de inundación tarda unos 23–28 s: es un hueco
  mayor que la tolerancia de cobertura de 20 s. No es una regresión, porque 7b275b8 tarda más, pero condiciona el
  paso 2.
- **Memoria.** El candidato conserva más estado (mapas de llegada y caché de observaciones): su RSS máximo en el replay
  completo es de 1,34 GB, frente a 0,86 GB de 7b275b8. El sensor tiene 8 GB.
- **Reinicio cruzado.** La reversión candidato → 7b275b8 no se probó offline.
- **`ciclos.jsonl`.** Crece unos 8 MB al día; su rotación se instala en el paso 2.
- **Esquema desplegado.** `configs/features/multilayer-v2.json` desplegado (`e032a1a2…`) no es el de 7b275b8
  (`1445ccd4…`). Todas las corridas usaron el desplegado, igual que el servicio, y la instalación no lo toca.

## 10. Conclusión y condiciones para el paso 2

**El candidato está listo para la validación en vivo del paso 2.**

- **Mismas decisiones.** Es equivalente a 7b275b8 en registros y decisiones a lo largo de toda la campaña A, y
  también a través de un reinicio a mitad de la inundación.
- **Tiempos offline.** No tiene ciclos por encima de 9,5 s en régimen estable, inundación HTTP incluida; 7b275b8
  tenía 535.

Condiciones:

1. **Instalación.** Instalar siguiendo `PROCEDIMIENTO-PASO2-INSTALACION-Y-REVERSION.md` y aplicar la rotación de
   `ciclos.jsonl`. Lo que necesita sudo lo ejecuta Mark.
2. **Sin reinicios durante los episodios.** No reiniciar `ppi-motor` durante una campaña: el primer ciclo con
   historia de inundación tarda unos 25 s. Hay que dejar al menos 230 s de calentamiento antes del primer episodio.
3. **Rendimiento en vivo, sobre todo en la inundación.** Medirlo con `ciclos.jsonl` (`duracion_s` y
   `registro_escrito_en`) antes de repetir la campaña A. Offline el máximo es 9,2 s, sin margen holgado. Si en vivo
   supera el presupuesto, habrá que volver a optimizar dentro del alcance autorizado.
4. **Memoria.** Vigilar el RSS de `ppi-motor` con carga; offline llega a unos 1,3 GB.

## 11. Evidencia

- **En el repositorio de documentación** (esta carpeta), 6,6 MB:
  - `evidencia/corridas/*/` (R0–R5): registros comprimidos, `ciclos.jsonl`, verificaciones, stdout y stderr con
    `/usr/bin/time -v`, `rc`, inicio, fin y huellas;
  - `evidencia/resumen.json`, `RESULTADOS.md` y `evidencia/herramientas/` (arnés, analizador, tablas y todos los
    comandos de lanzamiento);
  - las huellas de entradas y código, y las salidas de las pruebas;
  - `MANIFIESTO.sha256`: sha256 de todos los archivos de la carpeta. Se verifica con
    `python evidencia/herramientas/manifiesto.py . --verificar`.
- **Evidencia voluminosa, conservada en el Sensor1:**
  - corridas completas sin comprimir, con los árboles `referencia/` (7b275b8) y `candidato/` (24f8a80):
    `/home/m4rk/cf-p1/` (150 MB);
  - entradas congeladas: `/home/m4rk/cf-campana-A-20261029/` (PCAP 1,2 GB y `eve.json` 641 MB).
