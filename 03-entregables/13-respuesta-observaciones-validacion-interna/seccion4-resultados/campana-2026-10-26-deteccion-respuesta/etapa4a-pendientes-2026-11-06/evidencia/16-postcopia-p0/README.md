# Post-copia repetida (comprobador r2) y comprobación ANTICIPADA de precondiciones P0 (06-nov, 20:45–21:06Z)

> **Corrección posterior (06-nov, 22:10Z).** Dos afirmaciones de esta carpeta no eran exactas. Los resultados y los
> ficheros de abajo se conservan **sin cambios**.
>
> 1. **`comprobar` sí escribió en el paquete.** `p0/bloques/sensor1_p0.sh` dice que «comprobar NO crea» nada. Es
>    cierto del DIR y de la salida en seco, pero la consulta de VERSION (`python3 -I -c`, importando
>    `evaluar_ecarga.py`) creó a las **21:05:27.80Z**
>    `~/cf-e4/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc` (27 980 B,
>    `754ec729…`). Desde entonces, el inventario de Sensor1 tiene 481 ficheros frente a 480: la post-copia r2 de las
>    21:24Z da NO_CONFORME 11/12 en Sensor1. El CONFORME 3/3 de §4 (21:02Z) era cierto en su momento.
> 2. **El rc 0 de §5 no era un agregado.** `p0/p0_anticipado.sh` termina con rc 0 aunque fallen todos sus bloques; sus
>    lecturas son válidas, pero su código no. Los 9 bloques sí terminaron con rc 0, transporte igual y stderr vacío, y
>    eso se comprobó fichero a fichero.
>
> Las dos se corrigen en [`../17-correccion-p0/`](../17-correccion-p0/): P0 r2 y producto `20dabe2`. El `.pyc` **no se
> ha borrado**; la actuación puntual está propuesta allí.

**Alcance.** Solo lecturas en el laboratorio, más el comprobador corregido y probado en banco. **E-carga NO
ejecutada y NO programada.**

No se hizo nada de lo siguiente:
- arrancar o parar generadores o muestreadores;
- cambiar servicios, permisos o sudoers;
- activar restricciones;
- volver a copiar el paquete;
- avanzar a la 4B o la 4C.

Tampoco cambian S14, el motor, IF, las 28 características, α, los heurísticos ni la política de respuesta.

La salida anterior con el error, [`../15-traslado-902991e/post-copia-3-hosts.txt`](../15-traslado-902991e/post-copia-3-hosts.txt),
y su guion `post_copia_host.sh` (r1) se conservan **sin cambios** como evidencia histórica.

**Referencias consultadas antes de trabajar:**
- docs `origin/main` = `9650701`, sin cambios posteriores;
- producto: rama `recuperacion/etapa4a-pendientes-20261106` = `902991ec077c…` (punta, sin cambios posteriores) y
  `main` = `7b275b8`.

## 0. Estado de ejecución al empezar (solo lectura, 20:45Z)

Fuente: [`estado-previo/`](estado-previo/). **Ninguna ejecución no prevista.**

- **Clientes:**
  - `cyberflow-lab.target` y las seis unidades `inactive`/`disabled`;
  - ningún proceso de perfiles;
  - sin crontab ni `at`.
- **Bastión, Sensor1 y srv-dmz:**
  - ningún muestreador, generador ni proceso de E-carga;
  - sin temporizadores, unidades transitorias ni unidades de usuario de E-carga;
  - crontab vacío; `at` no está instalado.
- **En Sensor1** solo están los temporizadores permanentes del producto, que no son de E-carga:
  `cyberflow-acumular`, `cyberflow-limpieza` y `cyberflow-aprendizaje`.

## 1. Causa comprobada del `$'\r': command not found`

Fuente: [`causa-cr/causa-cr.txt`](causa-cr/causa-cr.txt), reproducible con `causa-cr/reproducir_causa.ps1`.

| Hipótesis | Comprobación | Resultado |
|---|---|---|
| El fichero `post_copia_host.sh` tenía CR | Bytes del fichero publicado | **No**: 1 896 bytes, 0 CR, 18 LF y último byte LF |
| La preparación de la entrada (`-replace "\r",""`) dejó un CR | Bytes recibidos por bash con esa preparación | **No es la causa**: el `-replace` actuó sobre el texto, que no tenía CR |
| **El transporte desde Windows** | Bytes recibidos al canalizar la cadena desde PowerShell 7.6 a un programa nativo | **Sí.** PowerShell añade `[Environment]::NewLine` (`\r\n`) al final: llegan 1 898 bytes, con la cola `l s - 1 A \n \r \n` |

La línea 19 que ejecuta bash es solo `\r`. Con la redirección de bash (`< fichero`) llegan los 1 896 bytes exactos.

**Consecuencia.** El error ocurrió **después** de la última orden de la r1 (`ls -1A`). Las lecturas de la r1 no
quedaron alteradas, pero el código de salida de cada host fue 127 en lugar de un resultado. Por eso la r1 no servía para
decidir. El banco también demuestra un segundo defecto de la r1: con una marca distinta termina con **rc 0**, porque su
código lo fija `ls`.

## 2. Comprobador r2: corrección

Ficheros en [`comprobador-r2/`](comprobador-r2/):

| Requisito | Cómo lo cumple la r2 |
|---|---|
| LF y bytes realmente enviados | Desde el portátil (Git Bash, nunca una tubería de PowerShell), antes de enviar se cuentan los CR del guion: con 1 o más, **rc 2 y no se conecta**. El guion viaja en base64 dentro del argumento de ssh. El host imprime primero el sha256 de los bytes decodificados y ejecuta esos mismos bytes; el portátil exige que coincida con el del fichero local (si no, `TRANSPORTE_DISTINTO`) |
| Cada operación crítica comprobada | 12 comprobaciones por host, cada una `OK`, `FALLO` o `ERROR`: paquete, marca (exactamente una línea `SUMAS=` y la esperada), `SHA256SUMS` interno, `sha256sum -c --strict`, inventario exacto de 480 ficheros, evaluador, `ecarga/SHA256SUMS` y su `-c`, dos `VERSION`, aviso y restos `.parcial` |
| Consultas fallidas ≠ vacío, cero o éxito | Una lectura imposible es `ERROR` (rc 3), nunca «0» ni «ninguno». Un `find` o `grep` que falla no se interpreta como resultado |
| Completa solo con todos los requisitos | `CONFORME` solo si las 12 están en OK. Global rc 0 solo con los 3 hosts `CONFORME` |
| Códigos locales y remotos propagados | El host termina con `exit` explícito y su código: 0, 1, 2 o 3. El portátil guarda el rc de ssh (255 = `SSH_FALLIDO`) y exige que coincida con la línea `RESULTADO`. Si no, `INCOHERENTE` |
| Conservar stdout, stderr y rc | `<host>.stdout`, `<host>.stderr`, `<host>.rc` y `resumen.txt`. La carpeta de salida debe ser nueva: nunca se sobrescribe |

**Códigos del comprobador:**
- **Global:**
  - 0: CONFORME 3/3;
  - 2: precondición (uso, salida existente, CR en el guion, herramientas);
  - 4: algún host no conforme (se listan).
- **Por host:** `CONFORME`, `NO_CONFORME` (rc 1), `ERROR_LECTURA` (rc 3), `SSH_FALLIDO` (255),
  `TRANSPORTE_DISTINTO`, `SIN_RESULTADO` e `INCOHERENTE`.

## 3. Pruebas aisladas (sin conexión al laboratorio)

Banco Docker `--network none`, ssh doble. El paquete de prueba es el **real** de `902991e`, extraído del bundle con
`git archive`: 480 ficheros, `SUMAS` `8480f0e0…`.

En los hosts simulados, `rm`, `mv`, `cp`, `chmod`, `mkdir`, `touch`, `tee`, `systemctl`, `sudo`, `nft` y otras son
dobles que fallan. En cada prueba se exige además que **ningún byte, modo ni fichero** de los hosts cambie.

| Ejecución | Resultado |
|---|---|
| Usuario 65534 | **27 pasan** ([`banco-65534.txt`](comprobador-r2/banco/banco-65534.txt)) |
| root | **26 pasan, 1 omitida** ([`banco-root.txt`](comprobador-r2/banco/banco-root.txt)). La omitida es la de permisos, porque root lee sin permisos; ese caso lo cubre la prueba del directorio |

Casos y resultado (rc global y estado del host):
- **Entrada correcta:** 0, con los 3 hosts `CONFORME` 12/12 y el sha recibido igual al local.
- **CR en el guion:** CRLF, un CR residual al final y un CR dentro del guion dan **2 sin abrir ninguna conexión**.
- **Transporte que añade `\r\n`:** 4, con ese host `TRANSPORTE_DISTINTO` y los demás `CONFORME`.
- **Regresión r1 con el transporte de PowerShell:** reproduce `line 19: $'\r'` y rc 127.
- **La r2 ignora la basura tras el resultado:** el `exit` explícito hace que no la ejecute.
- **Fallo de SSH:** al bastión, los 3 hosts `SSH_FALLIDO`; a srv-dmz, solo ese host. Se guarda el stderr.
- **Fallo de lectura:** un fichero convertido en directorio da `ERROR_LECTURA` (rc 3); un `SHA256SUMS` sin permiso
  da `ERROR` en las tres comprobaciones que dependen de él.
- **Hash incorrecto:** `NO_CONFORME`.
- **Fichero ausente:** fallan los hashes y el inventario, y se nombra el fichero.
- **Fichero inesperado:** los hashes dan OK y el inventario, FALLO.
- **Marca:** ausente, con otro `SUMAS`, con dos líneas `SUMAS=`, con un espacio final o sin línea `SUMAS=`: siempre
  FALLO.
- **Versión incorrecta:** FALLO.
- **Aviso** ausente o que no nombra el paquete: FALLO.
- **Resto `.parcial`:** FALLO.
- **Un host correcto y otro fallido:** «NO_CONFORME 2/3; sin conformidad en: sensor1».
- **Regresión de ocultación:** con la marca distinta, la r1 da rc 0 y la r2, rc 1.
- **Salida existente:** 2, intacta y sin ninguna conexión.
- **Por host** quedan stdout, stderr y rc.
- **Guiones** sin CR y sin órdenes de escritura en el host.

## 4. Comprobación posterior repetida con la r2 (21:02Z), solo lectura

Fuente: [`post-copia-r2-20261106T210203Z/`](post-copia-r2-20261106T210203Z/). **RESULTADO_GLOBAL rc=0, CONFORME 3/3**,
stderr vacío en los tres hosts y sha recibido `07063091…` igual al local.

| Comprobación | Bastión | Sensor1 | srv-dmz |
|---|---|---|---|
| `~/cf-e4/paquete-902991e` existe | OK | OK | OK |
| Marca `VERIFICADO` con `SUMAS=8480f0e0…` (una sola línea) | OK | OK | OK |
| `SHA256SUMS` interno = `8480f0e0…` | OK | OK | OK |
| Inventario exacto (480) y hashes correctos | OK | OK | OK |
| Evaluador `53e9f7bd…` | OK | OK | OK |
| `ecarga/SHA256SUMS` `e001352c…` y su `-c` | OK | OK | OK |
| `evaluar_s14` 2026-11-06.2 y `construir_entrada` 2026-11-06.3 | OK | OK | OK |
| Aviso junto a `paquete-a12deae` que nombra `paquete-902991e` | OK | OK | OK |
| Sin restos `.paquete-902991e.parcial.*` | OK | OK | OK |

**Informativo (no decide):**
- los registros del traslado siguen en `ESTADO_FINAL=VERIFICADO rc=0`;
- `paquete-a12deae` verifica (`9ff24889`), con 481 ficheros en el bastión y srv-dmz y 482 en Sensor1.

El fichero de más en Sensor1 es el `.pyc` histórico de las 16:35Z, que no se tocó (`../15-traslado-902991e/README.md`).

## 5. Precondiciones de P0: comprobación ANTICIPADA (21:05Z del viernes 06-nov)

Fuente: [`p0-anticipado-20261106T210504Z/`](p0-anticipado-20261106T210504Z/), generada con [`p0/p0_anticipado.sh`](p0/p0_anticipado.sh)
y [`p0/bloques/`](p0/bloques/).

Todos los bloques terminaron con rc 0, con el transporte verificado y stderr vacío. El guion de S11 es el publicado
sin cambios: `precheck.sh` `b3127edd…`. Los verificadores se ejecutaron desde `paquete-902991e` y son byte a byte los
de `a1cea5e`.

**Esto NO es el P0 del ensayo.** El protocolo (r4 §3.2) fija P0 en 1794191400, el lunes 09-nov a las 02:30:00Z
(domingo 08-nov, 21:30 en Perú). Lo leído hoy describe el estado de hoy y **no garantiza** el de ese momento.

| # (§3.5) | Precondición | Hoy | Evidencia | ¿Repetir en P0? |
|---|---|---|---|---|
| 1 | Los tres verificadores con rc 0 | **CUMPLE**: bastión, Sensor1 y srv-dmz OK; srv-dmz en sombra demostrada, `con_aplicar=0`, `tablas_cyberflow=0`, `eventos_aplicacion=0` | `01`–`03` | Sí |
| 2 | Hashes congelados de O11 | **CUMPLE**: modelo `df547da0…`, manifiesto `b3ad6805…`, esquema `e032a1a2…`, `ec78ca5` `SHA256SUMS` OK y `suricata.yaml` `0962ce68…` | `04` | Sí |
| 3 | Sin `--aplicar`/`--enforce`; rulesets de Sensor1 `24c320e3…` y de srv-dmz `e3b0c442…` | **CUMPLE**: 0 procesos en los tres hosts, rulesets iguales, srv-dmz sin tablas y 0 eventos de aplicación | `00`, `03`, `04` | Sí |
| 4 | Generador `ae5134a7…`; seis servicios inactivos y sin procesos de perfiles | **CUMPLE**: hash igual, target y unidades `inactive`, `PARADO_CONFIRMADO` y `procesos=0` (lectura de `/proc` de `generadores.sh`) | `05` | Sí |
| 5a | Zona `Etc/UTC` en clientes y Sensor1 | **CUMPLE** | `05`, `06`, `00` | Sí |
| 5b | `date -u` dentro de la franja | **NO EVALUABLE hoy**: hoy es 06-nov 21:05Z y la franja es 09-nov 02:30–05:00Z | — | **Sí, decisivo** |
| 5c | `weekday()` UTC de 0 a 4 | **CUMPLE** para la fecha publicada: 2026-11-09 es lunes | cálculo de los epochs | — |
| 6 | `/home` de Sensor1 ≥ 2 GB y `MemAvailable` ≥ 1 GiB | **CUMPLE**: 12 015 MiB y 6 634 MiB | `06` | Sí |
| 7 | `obs_pcap --en-seco` con los dos fines | **CUMPLE**: rc 0, `fin_utc` 2026-11-09T04:16:00Z y sin salida | `06` | Sí |
| 8 | Ventana fijada en epoch y publicada antes de T_g | **CUMPLE**: protocolo r4 §3.2, publicado | docs | Solo si cambia la franja |
| 9 | `paquete-ae2900e` en Sensor1: `SHA256SUMS`, evaluador `53e9f7bd…` y VERSION 2026-11-06.4 | **CUMPLE** | `06` | Sí |
| 10 | `generadores.sh configuracion` rc 0: seis unidades cargadas con `PartOf` y argv de su perfil e IP | **CUMPLE**: 6 OK, `.21`–`.26` | `05` | Sí |
| 11 | `sensor1_muestreadores.sh comprobar` rc 0: anillo ≥ 900 s; PSI, `vmstat`, `diskstats` y `USER_HZ` legibles | **CUMPLE**, con **margen escaso**: retención **929 s** (29 s sobre el mínimo), medida sin carga | `06` | **Sí, decisivo** |
| 12 | Muestreadores (S14 incluido) arrancados antes de T_g − 300 s | **NO EVALUABLE hoy**: es un acto de la ejecución y hoy no se arranca ninguno | — | Sí, en la ejecución |
| 13 | El paquete de los puntos 10–12 es el de `902991e` | **CUMPLE**: post-copia r2 3/3 (§4); `comprobar` verifica `paquete-902991e` | §4, `06` | Sí |

**Comprobaciones adicionales del encargo:**

| Comprobación | Hoy | Evidencia |
|---|---|---|
| Cadena v2 en sombra | **CUMPLE**: relé v2 activo, solo hacia srv-dmz y en modo `--entrega paquete`; feed v2 < 60 s con firma válida; agente v2 en sombra | `01`–`04` |
| Cadena v1 desactivada | **CUMPLE**: `ppi-publicar-feed.timer` y `ppi-relay-feed.timer` en `disabled/inactive`, sin procesos v1; `ppi-enforce-agent.timer` en `disabled/inactive` | `01`, `02`, `04` |
| Relojes y sincronización | **CUMPLE**: `NTPSynchronized=yes` en los cuatro hosts. Bastión: chrony a 0,24 ms. Sensor1: timesyncd con 10.10.60.1, +1,99 ms. srv-dmz: +171 µs. Clientes: sí | `00`, `05` |
| Legibilidad de anillo, EVE, journal y fuentes de S14 | **CUMPLE**: 186 ficheros en el anillo; EVE con `stats` a las 21:05:25Z; 20 lecturas SIGUSR1 en 10 min por unidad; `/proc/pressure/*` legibles | `06` |
| Recursos | **CUMPLE**: Sensor1 con 6,6 GiB libres de RAM y 12 GiB en `/home`; `NRestarts` 0 en los servicios | `00`, `02`, `04` |
| Argumentos temporales y modo seco | **CUMPLE** con `obs_pcap --en-seco` (fin en epoch e ISO). `muestreo_bastion.sh … seco` **no se ejecutó**: es un muestreador que corre hasta FIN, y lanzarlo está fuera del encargo | `06` |
| Permiso de arranque y parada | **INFORMATIVO**: en clientes, `sudo -n` NOPASSWD solo para `systemctl start/stop cyberflow-lab.target` (`generadores.sh permisos`, solo lectura) | `05` |

**Observaciones sin efecto en el resultado:**
- La zona del bastión es `America/Lima`. El protocolo exige UTC solo en clientes y Sensor1, y el muestreo del bastión
  trabaja en epoch.
- `verificar_bastion` informa de «errores 1» en la última hora del relé, como INFO. Es la misma clase de evento que los
  14 `firma_invalida` históricos de srv-dmz (P4, ya explicados).
- La lectura auxiliar `pgrep -af clientes_lab.py` del bloque 05 encontró **su propia orden** (PID 6662, `bash -c …`),
  no un generador. El conteo válido es el de `generadores.sh` (`procesos=0`), que recorre `/proc` filtrando el argv.

## 6. Pendientes antes de una futura ejecución (no resueltos aquí)

1. **Orden expresa de Mark** para ejecutar E-carga, que incluye aprobar el protocolo r4. Este encargo no la da.
2. **P0 completo** en 1794191400 (09-nov 02:30Z), con `p0/p0_anticipado.sh` o su equivalente.
   - Repetir todos los puntos marcados «Sí».
   - Son decisivos el 5b (dentro de la franja) y el 11 (retención ≥ 900 s en ese momento).
   - El punto 12 se cumple durante la ejecución.
3. **Calendario.** La franja publicada sigue siendo viable: faltan ~53 h para P0. Exige operar el domingo 08-nov de
   21:30 a 00:00, hora de Perú.
   - Si no hay orden y operador a esa hora, no se desplaza en silencio: se publica una franja nueva, con los mismos
     desfases, en otra madrugada laborable UTC (§3.2).
   - Pendiente para la futura orden de ejecución.
4. **Retención del anillo con carga.** Hoy hay 929 s sin carga, solo 29 s de margen.
   - El protocolo la exige en P0, sin carga, y ya figuraba como «pendiente de medir en vivo» la retención con carga.
   - Si con los generadores activos el anillo rota más rápido, `derivar_pcap` (900 s) podría quedarse sin ficheros.
   - Corrección mínima propuesta, si Mark lo autoriza: medirla al inicio de la ejecución (ya lo hace
     `salud_captura`) y declararla. No cambia ningún umbral.
5. **Pendientes de medida en vivo** heredados de la preparación r2: arranque y parada con el systemd real, coste de
   `muestreo_s14` y retención con carga. Solo se pueden medir en la ejecución.
6. **Menor (traslado r2).** El mensaje «no es un repositorio git» oculta el error de ruta larga de Windows. Su r3
   necesita autorización. No afecta al paquete ya verificado.
