# Paso 2 — instalación y validación en vivo del motor incremental (1-nov-2026)

Identificador de la corrida: `20261101T0254Z`. Todas las horas son UTC.

**Conclusión:** **listo para preparar el paso 3.** El candidato `24f8a80` funcionó en vivo, en modo sombra, durante 75 min. Hubo tráfico legítimo de hora punta y tres inundaciones HTTP, y se cumplen los siete criterios de rendimiento fijados antes de la carga (C1–C7):

- **Ciclos:** ninguno superó 9,5 s. El máximo fue 9,38 s, con un margen de 0,62 s.
- **Inventario:** se decidieron las mismas 4058 ventanas que en la repetición offline, sin diferencias de decisión ni de puntuación.
- **Registro:** 0 duplicados y orden `decidido ≤ logged ≤ escrito` en el 100 % de las decisiones.
- **Memoria:** sin swap.

Antes de **ejecutar** la campaña A repetida hay que resolver cuatro cosas (sección 12):

1. el endpoint de fuerza bruta `:18081/auth` está inactivo;
2. el filtro `NUNCA_BLOQUEAR` del analizador no funciona;
3. la Kali tiene 3 bloqueos en el estado de escalada del publicador;
4. falta archivar la verificación del respaldo de logrotate.

Además, el margen bajo carga es estrecho: la CPU del motor llega al 100 % en la inundación.

Estas son **pruebas técnicas del motor**. No son episodios de la campaña A ni de la campaña B, y sus resultados no
se mezclan con los confirmatorios:

- no se ejecutaron los 25 episodios de la campaña A ni la campaña B;
- no se activó ninguna respuesta (motor sin `--enforce`, agente de srv-dmz parado y deshabilitado);
- no se modificó el documento Word.

## 1. Alcance y referencias

| Elemento | Valor |
|---|---|
| Código instalado | repo `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`, rama `candidato/motor-rendimiento-20261031`, commit `24f8a80e376d89b78454fd16854d2239a1b7d278` |
| `motor_decision.py` | `6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e` (sustituye a `e2b2eb53…`, 7b275b8) |
| `motor_incremental.py` (nuevo) | `a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168` |
| Procedimiento seguido | `../paso1-motor-incremental-2026-10-31/PROCEDIMIENTO-PASO2-INSTALACION-Y-REVERSION.md` (repo de documentación, `e66f436`) |
| Protocolo fijado antes de la carga | `PROTOCOLO-PASO2.md`, sha256 `3928677954932b4773b1c46525e31bfeecebb22d7566b97ee14c36601f94f73f`, fijado a las 03:17:20 |
| Criterios definitivos, fijados antes de T1 | `CRITERIOS-DEFINITIVOS-PASO2.md`, sha256 `fda6d172ab958631c7fd0ed4b5a12c4b45974f3a69085cd1a59237ce37e1056e`, fijados a las 03:42:14 |
| Directorio exclusivo en el sensor | `/home/m4rk/cf-paso2-20261101T0254Z/` (no se borró ni reutilizó ningún directorio anterior) |

**No cambió nada de lo siguiente:**

| Elemento | Detalle |
|---|---|
| Modelo | `if_limpio_2026_10_desplegable.joblib`, `df547da0…` |
| Manifiesto | `b3ad6805…` |
| Escalador | el mismo |
| Esquema desplegado | `multilayer-v2.json`, `e032a1a2…` |
| Características | las mismas |
| Heurísticos | `10deb05d…` |
| Extractores | v2 `7130edae…`, v3 `5adbfbf4…` |
| Umbral operativo | −0,5693969936322356 |
| Historia | 230 s |
| Argumentos y unidad `ppi-motor.service` | idénticos antes y después del reinicio |
| Intensidad del ataque | la del constructor aprobado |
| Relojes y zonas horarias | sin cambios |

No se ejecutó `cyberflow_config.py --escribir`.

## 2. Cronología

| Hora | Hecho |
|---|---|
| 02:54:53 | Alcance desde el bastión: 7 hosts responden; HTTP y HTTPS del servidor dan 200; el panel da 401. Relojes con desfase < 1 ms. |
| 02:55:20 | Estado inicial del sensor guardado en `estado-inicial/` |
| 03:02:52 | Arrancan el archivador del SPAN completo (`archivar_captura.sh`, 20 s) y el muestreador de recursos (5 s). Se registra el byte inicial del EVE: inodo 663679, byte 23 760 588. |
| 03:03:25 | Los seis perfiles legítimos arrancan con factor horario 1,0 (sección 5) |
| ~03:10 | Mark ejecuta `01_logrotate.sh`: la comprobación global pasa de rc=1 a rc=0 (sección 3) |
| 03:14:00 | Respaldo operativo e instalación |
| 03:14:01.039 | `systemctl restart ppi-motor` (PID 1378 → 1289322) |
| 03:15:43 | Preparación desde la Kali: HTTP, HTTPS, `/api/auth` y `:18081/auth` (sección 9) |
| 03:17:20 | Protocolo fijado |
| 03:14:01–03:17:51 | Calentamiento (230 s) |
| 03:20:00–03:50:59 | **Tráfico normal evaluado (31 min)** |
| 03:42:14 | Criterios definitivos fijados |
| 03:50:59.754–03:52:29.044 | **T1** |
| 03:56:56.136–03:58:26.063 | **T2** |
| 04:02:52.070–04:04:22.037 | **T3** |
| 04:18:29 | Cierre: se paran el archivador (barrido final) y el muestreador, y se extraen las copias |
| 04:19:05 | Se paran los envoltorios de factor 1,0 y vuelve la programación habitual (sección 5) |
| 04:19:26 | Comprobación final de srv-dmz: sigue en modo sombra |

Antes de cada episodio se comprobaron las cuatro condiciones del protocolo (`c01_pre_T1/T2/T3`): ≥ 230 s desde el
episodio anterior, 6 últimos ciclos < 9,5 s, pendientes sin crecer y ningún `curl` en la Kali. Las cuatro se
cumplieron siempre. Durante cada episodio se vigiló el sensor directamente (`vigilancia_Tk.txt`), sin depender solo
del aviso del monitor. El motor no se reinició durante los episodios: `NRestarts=0` y el mismo PID, 1289322, de
principio a fin.

## 3. logrotate (resuelto antes de instalar)

**Problema.** La configuración global de logrotate fallaba (`logrotate -d`, rc=1, 5 errores). Dos respaldos
redundantes dejados en `/etc/logrotate.d/` duplicaban entradas:

- `cyberflow.anterior:9 duplicate log entry for …/motor_decision.log`
- `suricata.orig-cyberflow:1 duplicate log entry for /var/log/suricata/fast.log` y `…/eve.json`

**Intervención de Mark** (necesita sudo con contraseña; yo no la tengo ni la pido). Ejecutó en el sensor:

```
ssh -t sensor1 'bash ~/cf-paso2-20261101T0254Z/mark/01_logrotate.sh'
```

El guion (sha256 `cfbb56da…`) hizo lo siguiente:

1. Tomó la línea base: rc=1.
2. Creó el respaldo exclusivo `/var/backups/cyberflow-paso2-20261101T0254Z/` (root:root 0700).
3. Copió allí la configuración activa (`logrotate.d-cyberflow.antes-paso2`).
4. **Trasladó, sin borrarlos**, los dos redundantes con `mv -n`.
5. Repitió la comprobación global sin los redundantes: rc=0.
6. Instaló la estrofa nueva (`motor_decision.log` + `_state/ciclos.jsonl`, sha256
   `183e7bc469122ed9e2d517d0561adde2afa589a97dce3365e291d9b185fce094`).
7. Repitió la comprobación global: rc=0.

En ningún momento se usó `--force` ni se provocó una rotación, porque `-d` no modifica el estado. La salida
completa y los rc de las tres comprobaciones están en `evidencia/logrotate/`. Entre la segunda y la tercera solo
cambian los PID de las líneas `switching euid` y las dos líneas de `ciclos.jsonl`.

**Incidencia del respaldo.** El guion 01 no llegó a registrar permisos ni hashes **dentro** del respaldo: el comodín
`"$K"/*` lo expandía el shell de m4rk, que no puede leer un directorio root 0700, y `stat`/`sha256sum` respondieron
«No such file». Los traslados sí se hicieron, y lo prueban dos hechos:

- `ls -la /etc/logrotate.d` ya no muestra los dos ficheros;
- la comprobación global da rc=0.

Para completarlo preparé `mark/03_verificar_respaldo.sh` (sha256 `a5b90e3d…`): solo lectura, `sudo find … -exec
stat/sha256sum {} +`, sin comodines del shell. Su resultado: **pendiente de que Mark lo ejecute** (`[BASTIÓN gadmin] ssh -t sensor1 'bash ~/cf-paso2-20261101T0254Z/mark/03_verificar_respaldo.sh'`). La salida quedará en `/home/m4rk/cf-paso2-20261101T0254Z/logrotate/mark-03-verificar-respaldo.log` y se añadirá a esta evidencia. Los valores esperados están en el respaldo operativo, que sí se pudo leer: `antes-paso2` y `cyberflow.anterior` = `7832acf2…`, y `suricata.orig-cyberflow` = `f95789a4…`.

Reversión, si hiciera falta: `mark/02_logrotate_revertir.sh` (sha256 `1b89a5e3…`). No se ha usado.

## 4. Instalación

1. **Candidato verificado.** Se partió de `candidato-24f8a80.tgz` (sha256 `5e535c9a…`) y los dos ficheros coincidían
   con los hashes aprobados. Las 48 pruebas específicas pasaron (`pruebas-especificas.txt`).
2. **Respaldo operativo exclusivo** en `respaldo-operativo/`, con `SHA256SUMS` y `STAT.txt`. Contiene:
   - `motor_decision.py.7b275b8-e2b2eb53`;
   - los dos `.toml`;
   - `multilayer-v2.json`;
   - el texto de la unidad y de `systemctl show`;
   - las copias de logrotate.
3. **Sustitución** de `motor_decision.py` y alta de `motor_incremental.py`, los dos `m4rk:m4rk 0664`, igual que el
   anterior. Hashes verificados en destino.
4. **Reinicio** a las 03:14:01.039, con `sudo -n systemctl restart ppi-motor` (NOPASSWD). Resultado:
   - servicio `active`, `NRestarts=0`;
   - argumentos **idénticos** a los iniciales y sin `--enforce`;
   - registro de arranque con `procesamiento: incremental`;
   - journal sin trazas.
5. **Comprobación posterior** a los 125 s:
   - captura, Suricata, publicador y panel activos;
   - feed generado hace 7 s;
   - `eve.json` crece;
   - `ciclos.jsonl` se escribe;
   - `eve_window.jsonl` ya no se escribe, como estaba previsto;
   - 0 claves duplicadas;
   - `decidido_en ≤ logged_at` en los 161 registros posteriores al reinicio.

**Incidencia de `__pycache__`.**
- **Qué pasó:** `python -m py_compile` sobre el directorio desplegado devolvió *Permission denied*.
  `scripts/engine/__pycache__/` es `root:root 0755`. Lo creó una ejecución con sudo el 27-sep y solo contiene
  `dashboard.cpython-312/314.pyc`, así que m4rk no puede escribir en él.
- **Por qué no afecta:**
  - la compilación se había comprobado sobre la copia preparada (`producto-24f8a80/`);
  - el servicio importa los módulos sin problema, porque Python sigue funcionando aunque no pueda escribir el `.pyc`;
  - además, el servicio corre con `ProtectSystem=strict` y solo puede escribir en `ReadWritePaths=/home/m4rk/cyberflow/logs`.
- **Coste:** el motor recompila en memoria cada vez que arranca. Es un coste menor y no afecta a los ciclos.
- **No se tocó:** cambiar el propietario necesita sudo y no es necesario.

## 5. Carga legítima con factor 1,0

**Estado al empezar.** A las 02:55, que en el reloj de clientes es domingo a las 02:55, `cyberflow-lab.target`
estaba **inactivo** y deshabilitado, y los seis perfiles estaban parados. A esa hora la curva horaria original
(`factor_horario`) habría dado 0,036.

**Mecanismo reversible.** Para probar con la carga de hora punta de un día laborable no se cambió ni el reloj ni la
zona horaria. Se usó el envoltorio `clientes_factor1.py` (sha256 `69d79937…`):

- importa `clientes_lab.py` sin modificarlo (sha256 `ae5134a7…`, comprobado al arrancar y al parar);
- sustituye `factor_horario` por una función que devuelve 1,0;
- lanza los seis perfiles con los mismos argumentos que sus unidades systemd.

Funcionó de 03:03:25 a 04:19:05: 8600 acciones, 0 fallidas, por perfil:

| Perfil | Acciones |
|---|---|
| ofimatica | 1400 |
| navegacion | 3000 |
| descargas | 400 |
| aplicacion | 2000 |
| ligero | 200 |
| erratico | 1600 |

**Estado al cerrar.** Se pararon los envoltorios (quedan 0) y se arrancó `cyberflow-lab.target` con la curva horaria
original, que es la programación habitual. El target queda **activo y deshabilitado** al arranque, como antes. Los
seis servicios están `active` con `NRestarts=0`.

**Diferencia con el estado inicial.** El target estaba inactivo y se deja activo. Si se prefiere el estado exacto de
las 02:55:

```
[CLIENTES adminclientes] → lo ejecuto yo (NOPASSWD) si se pide
sudo -n systemctl stop cyberflow-lab.target
```

## 6. Estado inicial y final

| Comprobación | Inicial (02:55) | Final (04:19) |
|---|---|---|
| Hosts alcanzables desde el bastión | 7/7 | — |
| Relojes frente al bastión (NTP a.ntp.br) | sensor +0,1 ms, Kali −0,5 ms, srv-dmz 0,0 ms, clientes −0,9 ms | sin cambios (no se tocaron) |
| `ppi-motor` | active, PID 1378, NR=0, 7b275b8 | active, PID 1289322, NR=0, `6c274d9e…` + `a403307a…` |
| `--enforce` | no está (ni en la unidad ni en argv) | no está |
| Captura (tcpdump 4.99.4, ens37) / Suricata 7.0.3 | active, NR=0 | active, NR=0, mismos PID (1375 / 1372) |
| `ppi-dashboard` / publicador | active / OK | active (panel 401) / OK |
| `ppi-enforce-agent.timer` en srv-dmz | inactive / disabled; última ejecución 2026-10-28 07:33:41 | igual |
| Conjuntos `inet cyberflow` en srv-dmz | consulta correcta: la tabla no existe desde la restauración del 30-oct, así que no hay restricciones | igual |
| Feed y estado de escalada | copiados sin modificar (`estado-inicial/`) | copiados (`copias/feed.json`, `feed.sig`, `estado.json`). No los modifiqué, pero el publicador los actualizó, como hace en sombra: **10.10.20.30 tiene `bloqueos: 3`** (último BLOCK a las 04:04:58) y aparecen entradas nuevas `bloqueos: 0` de los perfiles. El feed final solo lleva LIMIT de .22 y .24, que caducan a las 04:23:50. |
| Procesos de replay o carga en la Kali | ninguno | ninguno |
| Memoria del sensor | 7,1 GB disponibles, swap 0 | 5,1 GB disponibles, swap 0 |
| Perfiles legítimos | target inactivo | target activo con curva habitual (sección 5) |
| logrotate global | rc=1 | rc=0 |

## 7. Resultados de rendimiento por condición

**Fuentes.** Las condiciones se asignan por `inicio_ciclo`, según el protocolo. Los datos salen de:
- `_state/ciclos.jsonl`;
- `motor_decision.log`;
- el muestreador de 5 s (902 muestras);
- `stats.log` de Suricata;
- el EVE del intervalo.

El análisis lo hace `herramientas/analizar_p2.py` y el resultado completo está en `evidencia/copias/resultados.json`.

### 7.1 Duración del ciclo (s)

| Condición | Ciclos | p50 | p95 | Máx. | > 9,5 s | > 10 s |
|---|---|---|---|---|---|---|
| Calentamiento (informativo) | 23 | 0,95 | 1,63 | 6,40 (primer ciclo) | 0 | 0 |
| **Normal** | 186 | 1,16 | 1,88 | 2,54 | 0 | 0 |
| **Inundación T1** | 9 | 5,15 | 6,97 | 7,20 | 0 | 0 |
| **Recuperación T1** | 23 | 2,73 | 4,07 | 7,33 | 0 | 0 |
| **Inundación T2** | 9 | 6,82 | 7,71 | 7,79 | 0 | 0 |
| **Recuperación T2** | 23 | 3,18 | 4,69 | 6,77 | 0 | 0 |
| **Inundación T3** | 9 | 4,41 | 8,46 | 8,47 | 0 | 0 |
| **Recuperación T3** | 23 | 3,03 | 7,44 | **9,38** | 0 | 0 |
| Entre episodios y cierre | 81 | 1,10 | 1,80 | 2,66 | 0 | 0 |

**Margen mínimo frente a 10 s: 0,62 s**, en recuperación T3. En la campaña A del 29-oct, con 7b275b8, el p50 era
15,6 s y el máximo 43 s.

### 7.2 Tiempo por etapa

p50 / máximo en segundos de las siete etapas que más pesan (`etapas_s` de `ciclos.jsonl`). El resto (`decision_y_registro`, `expiracion_y_escritura`, `eve_observaciones`, `eve_poda`, `filtro_plano_control`, `seleccion`) no supera 0,07 s en ninguna condición.

| Etapa | Normal | Inund. T1 | Recup. T1 | Inund. T2 | Recup. T2 | Inund. T3 | Recup. T3 |
|---|---|---|---|---|---|---|---|
| `filas` | 0,28 / 0,68 | 1,10 / 2,05 | 0,50 / 1,97 | 1,60 / 2,30 | 0,62 / 2,03 | 2,24 / 3,25 | 0,61 / 3,52 |
| `pcap_parseo` | 0,16 / 0,66 | 1,77 / 2,31 | 0,21 / 2,06 | 1,76 / 2,16 | 0,23 / 1,43 | 1,05 / 2,13 | 0,20 / 2,12 |
| `deduplicacion` | 0,32 / 0,59 | 0,98 / 1,41 | 0,99 / 1,44 | 1,23 / 2,09 | 1,11 / 1,48 | 0,92 / 1,58 | 1,11 / 1,60 |
| `atribucion` | 0,22 / 0,55 | 0,88 / 1,17 | 0,54 / 1,24 | 1,09 / 1,61 | 0,63 / 1,26 | 0,63 / 1,61 | 0,60 / 1,82 |
| `eve_lectura` | 0,01 / 0,02 | 0,27 / 0,39 | 0,01 / 0,67 | 0,29 / 0,41 | 0,01 / 0,19 | 0,29 / 0,54 | 0,01 / 0,35 |
| `pcap_poda` | 0,08 / 0,14 | 0,12 / 0,19 | 0,20 / 0,25 | 0,14 / 0,23 | 0,23 / 0,30 | 0,14 / 0,22 | 0,25 / 0,29 |
| `puntuacion` | 0,06 / 0,08 | 0,07 / 0,07 | 0,06 / 0,07 | 0,06 / 0,07 | 0,06 / 0,06 | 0,07 / 0,07 | 0,06 / 0,07 |

**Lectura.** Bajo carga, el coste se reparte entre la construcción de filas, el análisis del PCAP, la deduplicación y la atribución, y ninguna etapa domina. En el paso 1, con 7b275b8, `build_rows` llegaba a tardar 26,9 s; aquí tarda como mucho 3,5 s. En las recuperaciones, `deduplicacion`, `atribucion` y `pcap_poda` siguen por encima del normal mientras quedan en la historia de 230 s los paquetes de la inundación, y vuelven a bajar cuando salen de ella.

**Disponibilidad de datos.** La edad de la marca de PCAP al empezar el ciclo es de unos 10 s de mediana y 16,2 s como máximo. Corresponde a los ficheros de 15 s de tcpdump. La marca de EVE tiene menos de 0,9 s de edad en todas las condiciones.

### 7.3 Pendientes, retraso y orden de registro

| Condición | Pendientes p95 / máx. | Media 1.er → último tercio | `decidido_en − window_end` p50 / p95 / máx. (s) | `registro_escrito_en − decidido_en` máx. |
|---|---|---|---|---|
| Normal | 22,75 / 26 | 13,6 → 16,4 | 15,0 / 25,8 / 240,5 | 1,6 ms |
| Inundación T1 | 23,8 / 25 | 16,7 → 17,0 | 20,5 / 30,5 / 106,4 | 1,8 ms |
| Recuperación T1 | 22,8 / 23 | 16,7 → 16,6 | 16,8 / 62,6 / 240,1 | 1,7 ms |
| Inundación T2 | 25 / 25 | 18,3 → 18,7 | 20,9 / 30,9 / 226,5 | 1,6 ms |
| Recuperación T2 | 24 / 25 | 18,7 → 18,6 | 17,1 / 28,0 / 239,3 | 1,6 ms |
| Inundación T3 | 27 / 27 | 19,0 → 18,7 | 22,7 / 173,3 / 236,8 | 1,7 ms |
| Recuperación T3 | 26 / 27 | 17,4 → 16,9 | 17,0 / 86,3 / 234,9 | 1,7 ms |
| Entre episodios y cierre | 24 / 26 | 15,1 → 12,7 | 14,8 / 25,1 / 236,7 | 1,9 ms |

- **Orden de registro.** Se cumple `decidido_en ≤ logged_at ≤ registro_escrito_en` en **todas** las decisiones:
  - calentamiento: 323/323;
  - normal: 2322/2322;
  - inundaciones: 126 + 123 + 128;
  - recuperaciones: 309 + 302 + 321;
  - entre episodios y cierre: 995/995.
- **Ventanas no evaluadas.** No hubo ninguna `ventana_no_evaluada` en ninguna condición.
- **Por qué hay retrasos de ~240 s.** No son una acumulación. Son ventanas sin paquetes (`packet_count_10s = 0`)
  dentro del rango de entidades con tráfico esporádico (10.10.10.1, .25, 10.10.30.10). Esas ventanas solo se
  deciden cuando un paquete posterior amplía el rango de la entidad. Es el mismo diseño de `build_rows` que en
  7b275b8 y ya se vio en el normal antes de T1 (p99 114,6 s, máximo 234,6 s).
- **Ciclos sin decisiones nuevas.** Hubo ciclos que no decidieron ninguna ventana nueva: 52 en normal y 2 a 8 por
  inundación o recuperación. No es un fallo: el ciclo terminó, pero ninguna ventana completó todavía su rango.

### 7.4 Recursos

| Condición | CPU del motor p95 | RSS máx. | Memoria disponible mín. | Swap usado | `pswpout` |
|---|---|---|---|---|---|
| Calentamiento | 100 % (arranque) | 424 MB | 5980 MB | 0 | 0 |
| Normal | 34 % | 496 MB | 5503 MB | 0 | 0 |
| Inundación T1 | 68 % | 912 MB | 5509 MB | 0 | 0 |
| Recuperación T1 | 72 % | 1015 MB | 4874 MB | 0 | 0 |
| Inundación T2 | 100 % | 953 MB | 6165 MB | 0 | 0 |
| Recuperación T2 | 76 % | 1187 MB | 4678 MB | 0 | 0 |
| Inundación T3 | 100 % | 1124 MB | 4762 MB | 0 | 0 |
| Recuperación T3 | 84 % | 1124 MB | 4078 MB | 0 | 0 |
| Entre episodios y cierre | 31 % | 1131 MB | 4054 MB | 0 | 0 |

**Lectura del RSS.** El RSS sube con cada inundación (de ~0,5 a ~1,1 GB) y no vuelve a bajar en el cierre. Puede
ser el comportamiento normal del asignador de Python, que retiene memoria liberada, o una retención de estado.
Con 75 min de datos no se puede distinguir. Queda como observación para la sesión larga de la campaña A (sección 12).

**Journal.** El journal del motor desde el reinicio tiene 5 líneas, todas de arranque, y 0 trazas. El journal del
sistema tiene un único aviso.

### 7.5 Captura, archivado y descartes

**Archivador.** `vistos=374 archivados=374, sin fallos`, de 03:02 a 04:18, con 514 MB en total. Los PCAP se quedan
en el sensor, en `archivo-pcap/`. Sus sha256 por fichero están en `archivar.log` y no se suben al repositorio.

**Segmento EVE.** Es del mismo inodo (663679) y va desde el byte 23 760 588. Son 169 040 034 bytes.

| Condición | Suricata `capture.kernel_drops` / paquetes | `rx_drop` de ens37 |
|---|---|---|
| Calentamiento | 250 / 110 169 | 12 550 |
| Normal | 559 / 1 157 942 (0,05 %) | 26 031 |
| Inundación T1 | 0 / 351 881 | 1 286 |
| Recuperación T1 | 0 / 135 624 | 3 178 |
| Inundación T2 | 91 / 400 384 (0,02 %) | 1 206 |
| Recuperación T2 | 70 / 168 404 (0,04 %) | 3 258 |
| Inundación T3 | 0 / 380 846 | 1 270 |
| Recuperación T3 | 68 / 164 051 (0,04 %) | 3 195 |
| Entre episodios y cierre | 788 / 3 283 486 (0,02 %) | 11 390 |

**Descartes del calentamiento.** Los descartes de Suricata del calentamiento (250) **no** son de un intervalo
evaluado. También hubo descartes, pequeños, en intervalos evaluados (normal, T2 y las recuperaciones de T2 y T3), y
se señalan como degradación de la fuente.

**`rx_drop` de ens37.** Este contador aumenta en todas las condiciones, también en el tráfico normal, y no sigue a
la carga: en las inundaciones crece menos por minuto que en el normal. No coincide con los descartes de Suricata, y
el archivador no perdió ningún fichero. En este paso no se determinó qué tramas cuenta. Queda como característica de
la interfaz SPAN que hay que vigilar, y no se atribuye al motor.

**Efecto en la Kali.** En T1 y T3, Suricata no descartó nada durante la inundación. En T2 descartó 91 paquetes de
400 384. Las 10 ventanas de la Kali se decidieron en los tres episodios (sección 8), así que no hay indicio de que
estos descartes les afectaran.

### 7.6 Tráfico observado (EVE, 10.10.20.30 → 10.10.30.10:80)

Cuento las peticiones del EVE con estos criterios, porque el SPAN ve cada petición **dos veces**: en la VLAN 20 (Kali → pfSense) y en la VLAN 30 (pfSense → servidor), como flujos con `flow_id` distinto.

- **Comprobado en T1:** hay 26 403 eventos `http`, de los que 13 415 son de la VLAN 20 y 12 988 de la VLAN 30 (`evidencia/salidas/out_a06_http_doble.txt`).
- **Criterio:** se cuenta solo la observación de la VLAN de origen, por `(flow_id, tx_id)`.
- **Por qué no se usa el puerto de origen:** se reutiliza dentro de un mismo episodio.

El análisis sin inventario (`resultados-sin-inventario.json`) contaba las dos VLAN y por eso daba ~26 000. Esas cifras quedan **sustituidas** por las de esta tabla.

| Episodio | Intentos del generador (iteraciones de `curl`) | Peticiones HTTP en el EVE (VLAN 20) | Con respuesta 200 | Sin respuesta registrada |
|---|---|---|---|---|
| T1 | 13 968 | 13 415 | 13 254 | 161 |
| T2 | 14 213 | 13 923 | 13 687 | 236 |
| T3 | 14 192 | 13 589 | 13 282 | 307 |

**Intentos frente a peticiones.** Hay entre un 2 y un 4 % menos de peticiones que intentos. Encaja con iteraciones de `curl` que no llegaron a enviar la petición antes de `--max-time 2`; no se investigó más. En las dos VLAN, 424 transacciones de T1 aparecen como `request_uri_not_seen`, sin método ni URL: libhtp no llegó a ver la petición.

**Recuperaciones.** Hay algunas decenas de transacciones sin respuesta: 47, 50 y 74. El generador ya había terminado y no quedaba ningún `curl`, así que se atribuyen a cierres de conexiones del episodio anterior que Suricata registra con retraso.

### 7.7 Duplicados

**No hay ninguna clave `(entity_ip, window_end_utc)` duplicada** en ninguna combinación:

- registro rotado (`motor_decision.log.1`, 52 688 registros);
- registro vigente (12 464);
- registros posteriores a la instalación (4973);
- rotado y vigente juntos.

### 7.8 Inventario de ventanas frente a la repetición offline

**Referencia.** La repetición offline (`replay_motor.py`) se hizo con el **mismo motor instalado** sobre:

- el archivo PCAP del SPAN, 374 ficheros;
- el segmento EVE conservado.

Cubrió de 03:19:50 a 04:18:10 en 351 ciclos y terminó con rc=0. El inventario se compara para `window_end` entre 03:23:50 y 04:16:15, desde el normal + 230 s hasta el cierre − 120 s.

| Medida | Valor |
|---|---|
| Ventanas esperadas (decididas por la repetición) | 4058 |
| Decididas en vivo | 4058 |
| **Ausentes en vivo** | **0** |
| Solo en vivo | 0 |
| Decisión distinta | 0 |
| Puntuación distinta (igualdad exacta) | 0 |
| `ventana_no_evaluada` (en vivo y en la repetición) | 0 |

Por condición se esperaban:

| Condición | Ventanas |
|---|---|
| Normal | 2043 |
| T1 | 126 |
| Recuperación T1 | 309 |
| T2 | 123 |
| Recuperación T2 | 302 |
| T3 | 128 |
| Recuperación T3 | 321 |
| Entre episodios y cierre | 706 |

En todas, todas las ventanas coinciden, con la misma decisión y la misma puntuación.

**Qué demuestra.** Funcionando en vivo, con carga, el motor no perdió ni añadió ninguna ventana respecto a procesar los mismos datos sin presión de tiempo.

**Qué no demuestra.** La repetición usa los mismos datos capturados. Si el SPAN o Suricata hubieran perdido algo, lo habrían perdido los dos, así que esos descartes se tratan aparte (sección 7.5).

## 8. Detección (separada de la aceptación)

La entidad es 10.10.20.30. Una ventana cuenta como «durante» si su `window_end` está entre el inicio y el fin + 10 s.

| Episodio | Ventanas durante / decididas | Primera emisión durante | Latencia `logged_at − inicio` | Latencia `registro_escrito_en − inicio` | Emisiones totales (antes, durante, posterior y cola) |
|---|---|---|---|---|---|
| T1 | 10 / 10 | `ALERT` del modelo (IF), ventana 03:51:00 | 28,66 s | 28,66 s | 17 |
| T2 | 10 / 10 | `ALERT` + heurístico `http_abuse` (LIMIT, 1152 req/60 s), ventana 03:57:00 | 34,45 s | 34,45 s | 17 |
| T3 | 10 / 10 | `ALERT` + heurístico `http_abuse` (LIMIT, 2388 req/60 s), ventana 04:03:00 | 37,21 s | 37,21 s | 15 |

**Clasificaciones derivadas.** No las emitió el motor: se calculan sobre las mismas puntuaciones con los umbrales
de `config-campana.json`. Cada celda es el número de ventanas «durante» con señal, sobre 10.

| Episodio | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 |
|---|---|---|---|---|---|---|---|
| T1 | 10 | 9 | 9 | 9 | 10 | 9 | 9 |
| T2 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| T3 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

- **No se elige α** y el umbral no cambia.
- **Latencia.** La primera emisión llega 28–37 s después del inicio. Se explica así:
  - la primera ventana completa del episodio termina a los 0–10 s;
  - el retraso típico de decisión es de 15–23 s;
  - el ciclo dura 5–8 s bajo carga.
  La duración del ciclo no es la latencia: la latencia la marca sobre todo el retraso `decidido_en − window_end`.
- **Atribución.** El origen 10.10.20.30 y el destino 10.10.30.10:80 están confirmados en el EVE dentro de cada
  intervalo. La Kali no tuvo otra actividad en esos tramos: lo único fuera de los episodios fue la preparación de
  las 03:15:43, que queda excluida.
- **Cola de T1.** Tras el fin de T1, en las ventanas de `window_end` fin + 100 s y fin + 110 s, el motor registró un
  heurístico `port_scan` (acción BLOCK) con `decision=PERMIT` del modelo. En modo sombra no tiene efecto. La causa
  probable es la cola de cierre de conexiones del flood: muchas conexiones cortas a un mismo puerto, que terminan
  con RST o FIN tras `--max-time 2`. El heurístico las lee como un barrido. Es una clasificación errónea a vigilar
  en la campaña A: en esa fase la ventana cuenta como «cola», no como detección del episodio.

## 9. Incidencias

1. **logrotate.**
   - **Qué pasó:** fallaba la configuración global por los dos respaldos redundantes en `/etc/logrotate.d/`.
   - **Estado:** resuelto, con los ficheros trasladados y no borrados (sección 3).
   - **Pendiente:** la verificación con root del contenido del respaldo (sección 3).
2. **Comodín sobre el respaldo root 0700.**
   - **Qué pasó:** el guion 01 no registró permisos ni hashes dentro del respaldo.
   - **Estado:** se corrige con el guion 03 (solo lectura).
3. **`__pycache__` root:root** en el directorio del motor.
   - **Qué pasó:** `py_compile` falla sobre el directorio desplegado.
   - **Estado:** sin efecto sobre el servicio (sección 4). No se tocó.
4. **Endpoint `/auth` en `:18081` inactivo.**
   - **Qué pasó:** en la preparación, `http://10.10.30.10:18081/auth` respondió `000`: la conexión fue rechazada y
     no se recibió respuesta. `ppi-brute-lab` no está activo en srv-dmz desde la restauración del 30-oct. Solo
     escuchan :80 y :443 (`lab-web-http/https`); `/api/auth` sí responde 401 en :80 y :443.
   - **Efecto aquí:** no afecta al paso 2, que solo usa la inundación HTTP.
   - **Efecto en la campaña A:** **es un bloqueo para repetirla**, porque sus episodios de fuerza bruta apuntan a ese
     endpoint. Hay que restaurarlo y comprobarlo antes del paso 3.
5. **Descartes de Suricata.**
   - **Qué pasó:** 250 descartes en el calentamiento (no evaluado), y entre 0 y 0,05 % en los intervalos evaluados
     (sección 7.5).
   - **Efecto:** no hay indicio de que afectaran a las ventanas de la Kali.
6. **`rx_drop` de ens37.**
   - **Qué pasó:** el contador aumenta de forma constante, también sin carga.
   - **Efecto:** es una propiedad de la interfaz SPAN. No se atribuye al motor.
7. **Preparación.** Hubo un `ALERT` de la Kali por las tres peticiones de 03:15:43. Por el criterio 3 de los
   criterios definitivos, no cuenta en ninguna condición.
8. **Falsos positivos de perfiles legítimos y del DNS.**
   - **Qué pasó:** con factor 1,0, el modelo emite `ALERT` sobre perfiles legítimos durante todo el normal:
     .22 (161), .24 (106) y .26 (41), además de .21, .23 y 10.10.50.51/52.
   - **DNS/AD 10.10.10.20.** En el normal tiene 29 `ALERT`: 5 del modelo y 24 con el heurístico `dns_entropy`.
     Además, 73 ventanas registran `dns_entropy` con decisión `PERMIT`. Los seis perfiles usan este servidor como
     DNS (`--dns 10.10.10.20`). En este paso no se analizó qué consultas disparan el heurístico.
   - **Efecto:** no afecta al rendimiento. Sí afecta a la tasa de falsas alarmas del control de la campaña A, y está
     relacionado con la discrepancia de `NUNCA_BLOQUEAR` (sección 10). Las cifras por condición están en
     `resultados.json → alertas_no_kali_por_condicion`.

## 10. Discrepancia de `NUNCA_BLOQUEAR`

**Qué hace hoy el analizador.**
- `config-campana.json` (`combinacion_real.exclusiones.NUNCA_BLOQUEAR`) guarda las IP **con anotaciones**: por
  ejemplo, `"10.10.10.20 (DNS/AD)"` y `"10.10.10.30 (bastion)"`.
- `scripts/analizar.py:880` crea el conjunto con esas cadenas tal cual.
- `scripts/analizar.py:748` las compara con el `entity_ip` exacto.

**Consecuencia.** Solo coinciden las entradas sin anotación, y además ninguna de ellas es una entidad del registro.
Por eso **el DNS 10.10.10.20 nunca se excluyó** de la población del control, ni de ningún análisis anterior.

**Problema conceptual.** La lista es una **excepción de respuesta**: esas IP no deben bloquearse ni limitarse aunque
el motor las marque. No es una **exclusión de población**. Si se quitan de la población de falsas alarmas, se ocultan
los `ALERT` del modelo sobre el DNS, que este paso muestra que existen.

**Propuesta para el paso 3**, sin aplicarla aquí:

1. Separar las dos listas en la configuración:
   - `excepciones_respuesta`: las IP limpias, sin anotaciones (las anotaciones van a un campo aparte);
   - `exclusiones_poblacion`: vacía, salvo que se justifique por qué una entidad no pertenece a la población.
2. En el control, contar los `ALERT` del DNS como falsas alarmas **del detector**. Aparte, informar de que la
   respuesta las habría suprimido por la excepción.
3. Normalizar las IP al cargar la configuración (quedarse con el primer token, que debe ser una IP válida) y fallar
   si una entrada no lo es, para que una anotación no vuelva a desactivar un filtro sin avisar.
4. Volver a calcular, en el informe de la campaña A repetida, la tasa de falsas alarmas con y sin el DNS, y dejar
   constancia de que los análisis anteriores ya lo incluían.

## 11. Criterios: evaluación

| # | Criterio | Resultado |
|---|---|---|
| C1 | Todos los ciclos evaluados < 10 s; listar los > 9,5 s | **Cumple.** 0 ciclos > 9,5 s en todas las condiciones; el máximo es 9,38 s (recuperación T3), con un margen de 0,62 s. |
| C2 | Sin fallos | **Cumple.** Motor, captura y Suricata activos, `NRestarts=0`, 0 trazas; archivador 374/374 sin pérdidas. |
| C3 | 0 duplicados nuevos | **Cumple.** 0 en el rotado, el vigente y los posteriores a la instalación. |
| C4 | 0 ausentes sin explicar frente a la repetición offline | **Cumple.** 4058/4058 ventanas iguales a la repetición offline: 0 ausentes, 0 solo en vivo, 0 decisiones distintas y 0 puntuaciones distintas. |
| C5 | Sin acumulación; recuperación | **Cumple** en las tres recuperaciones: (a) la media del último tercio es 16,6 / 18,6 / 16,9 ≤ 22,75 (p95 del normal); (b) el p50 del retraso es 16,8 / 17,1 / 17,0 ≤ 25,0; (c) los 6 últimos ciclos antes del siguiente episodio duran < 9,5 s (comprobado en `c01_pre_T2/T3` y `c01_post_T3`). |
| C6 | Memoria | **Cumple.** Memoria disponible mínima 4054 MB, swap 0 y `pswpout` 0 en todas las condiciones. |
| C7 | Evidencia y tiempo | **Cumple.** PCAP continuo de 03:02 a 04:18 (374/374), segmento EVE del mismo inodo, marcas de inicio y fin de T1–T3, y el orden `decidido ≤ logged ≤ escrito` en el 100 % de las decisiones. |

**Reglas de parada.** No se activó ninguna regla de parada: no hubo motor caído, ni ciclos > 30 s, ni memoria
disponible < 500 MB, ni swap. No se redujo la intensidad ni se repitió ningún episodio.

## 12. Propuesta de protocolo para la campaña A repetida (paso 3)

1. **Requisitos previos.**
   - `ppi-brute-lab` (`:18081/auth`) activo y comprobado desde la Kali.
   - Discrepancia de `NUNCA_BLOQUEAR` corregida en el analizador (sección 10), con un test.
   - Verificación del respaldo de logrotate (guion 03) archivada.
   - **Estado de escalada de la Kali.** Tras este paso, `~/feed/estado.json` registra `bloqueos: 3` para
     10.10.20.30, con el último a las 2026-11-01 04:04:58. Con la escalera 300 → 1800 → 3600 s y revisión humana en
     la tercera reincidencia en menos de 24 h, el primer episodio de la campaña A empezaría en el nivel alto en
     lugar de en 300 s. Hay dos opciones, y hay que decidir cuál y registrarla:
     - empezar la campaña A después del **2026-11-02 04:05 UTC**, cuando la ventana de 24 h ya no cuenta esos
       bloqueos;
     - restablecer esa entrada con un procedimiento documentado, con copia previa.
     No lo cambié en este paso.
2. **Motor.** El candidato `24f8a80` tal como queda instalado, sin reinicios durante la campaña. Calentamiento
   ≥ 230 s y control normal ≥ 30 min antes del primer episodio.
3. **Cobertura**, por episodio y por ventana esperada de la Kali (`window_end` en [inicio, fin + 10 s]):
   - **cobertura de decisión** = ventanas con decisión / ventanas esperadas. Es evaluable si es ≥ 0,9 y no hay dos
     esperadas consecutivas sin decisión;
   - el inventario de esperadas sale de la repetición offline del mismo motor sobre el PCAP y el EVE archivados
     (como en la sección 7.8), no del propio registro en vivo;
   - una ventana `no_evaluada` cuenta como **no cubierta**, nunca como PERMIT.
4. **Puntualidad.**
   - Hay que separar la duración del ciclo de la latencia.
   - Criterio de servicio: el p95 de `decidido_en − window_end` de las ventanas de la Kali con paquetes ≤ 40 s.
     Una ventana decidida más de 60 s después de su `window_end` se informa como **tardía**, no como omitida.
   - Las ventanas sin paquetes de entidades esporádicas (retrasos de ~230 s) se excluyen de la puntualidad, pero
     se cuentan en la cobertura.
   - Este umbral se fija **antes** de la campaña. La propuesta sale del normal medido aquí, cuyo p95 es 25,8 s.
5. **Estados de una ventana.** Hay que distinguir:
   - un ciclo sin decisiones nuevas, que es normal;
   - una ventana retrasada, que se decide tarde pero se decide;
   - una ventana `no_evaluada`, que es explícita;
   - una ventana esperada sin registro, que es ausente. Solo esta última es un fallo de cobertura.
6. **Margen de rendimiento.** Durante la campaña se mantienen las comprobaciones previas de este paso: 6 últimos
   ciclos < 9,5 s, pendientes ≤ p95 del normal y ≥ 230 s entre episodios. Si un ciclo supera 9,5 s, se registra.
   Si se superan 10 s, el episodio se marca y se sigue el criterio preregistrado de la campaña.
7. **Recursos.** Hay que vigilar el RSS a lo largo de las ~4 h de la campaña. Si crece de forma monótona más de
   1 GB respecto al inicio, se para antes del siguiente episodio y se informa.
8. **Clasificaciones.** Se mantienen las siete configuraciones y los tres α, sin cambiar el umbral. La cola
   `port_scan` posterior a una inundación cuenta como «cola», no como detección.

## 13. Limitaciones

- **Margen estrecho.** Bajo inundación y en recuperación, el margen mínimo es de 0,62 s, en recuperación T3. La
  inundación usa 100 % de CPU del motor en T2 y T3, así que con un ataque más intenso o con más carga legítima
  simultánea se podría superar 10 s. Solo se probó la inundación HTTP del constructor aprobado, tres veces y con
  una sola entidad atacante.
- **RSS ~1,1 GB tras tres inundaciones**, sin vuelta atrás observada en 15 min. La memoria sigue holgada (> 4 GB
  disponibles), pero falta una observación más larga.
- **No se probó** un reinicio del motor en vivo a mitad de un ciclo ni la reversión cruzada en vivo (instalar 7b275b8
  y volver al candidato). El procedimiento de reversión está documentado y el respaldo está verificado, pero no se
  ejecutó.
- **Duración.** La sesión duró 75 min, con 31 min de normal. Es más corta que una campaña.
- **Perfiles legítimos.** Funcionaron con factor 1,0 mediante un envoltorio. La carga es la de hora punta, pero no
  su variación a lo largo del día.

## 14. Evidencia

| Ruta en este directorio | Contenido |
|---|---|
| `PROTOCOLO-PASO2.md`, `CRITERIOS-DEFINITIVOS-PASO2.md` | Copias idénticas a las de solo lectura del sensor (sha256 en la sección 1) |
| `evidencia/estado-inicial/` | Estado inicial del sensor (servicios, argv, versiones, hashes, feed, escalada) |
| `evidencia/salidas/` | Salidas de cada paso ejecutado desde el bastión (`out_*.txt`) y vigilancia T1–T3 |
| `evidencia/logrotate/` | Las tres comprobaciones globales completas con su rc, stat/sha, diff, `mark-01.log` (y `mark-03-verificar-respaldo.log` cuando Mark ejecute el guion 03) |
| `evidencia/respaldo-operativo/` | `SHA256SUMS` y `STAT.txt` del respaldo, y unidad. El `.py` anterior se conserva en el sensor. |
| `evidencia/copias/` | `ciclos.jsonl`, `motor_decision.log` (+`.1`), muestras, `stats.log` inicio y fin, marcas, estado del archivador, journal, feed final, `resultados.json` y `resultados-sin-inventario.json` |
| `evidencia/kali/episodios/` | Configuración técnica, marcas y salidas del generador de T1–T3 |
| `evidencia/replay/` | Argumentos, huellas, ciclos y `stderr` de la repetición offline; su registro de decisiones está en `p2_replay_motor_decision.log.gz` |
| `evidencia/herramientas/`, `evidencia/mark/` | Las copias exactas que se ejecutaron en el sensor |
| `herramientas/` | Todos los guiones locales (bastión, sensor, Kali, clientes, Mark), `run.ps1`/`subir.ps1` y `analizar_p2.py` en su versión final (sha256 `0abff0a9…`) |
| `MANIFIESTO.sha256` | sha256 de todos los ficheros de este directorio |

**Se quedan en el sensor** por su tamaño, en `/home/m4rk/cf-paso2-20261101T0254Z/`:
- `archivo-pcap/`: 374 PCAP, 514 MB, con el sha256 de cada uno en `archivar.log`;
- `copias/eve-segmento.json`: 169 MB (sha256 `96ce20b96fbb39f1c8ec6bf44d3cb438c6ffe62aea71ac0f027b0f5b0586124a`). Los sha256 de todo lo que se queda en el sensor están en `evidencia/p2_hashes_en_sensor.txt`. Los registros de decisiones en vivo y de la repetición se incluyen comprimidos (`evidencia/p2_motor_decision.log.gz` y `evidencia/p2_replay_motor_decision.log.gz`).
