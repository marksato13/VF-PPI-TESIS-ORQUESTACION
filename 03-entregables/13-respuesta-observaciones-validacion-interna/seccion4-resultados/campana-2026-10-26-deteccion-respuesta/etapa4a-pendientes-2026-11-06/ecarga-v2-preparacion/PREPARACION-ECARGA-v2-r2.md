# Preparación de E-carga v2, revisión r2: defectos corregidos (06-nov, noche)

> **Sustituida en parte por la r3** ([`PREPARACION-ECARGA-v2-r3.md`](PREPARACION-ECARGA-v2-r3.md), protocolo r4).
> `evaluar_s14` 2026-11-06.1 de `a12deae` no contaba el hueco inmediatamente anterior a un tramo saturado. Con eso,
> un caso con datos ausentes habilitaba la condición (3). Cambia lo siguiente:
> - el paquete es `~/cf-e4/paquete-902991e`, no `paquete-a12deae`;
> - los resultados van a `evidencia/14-ecarga-ejecucion/`, no a la 13;
> - S14 sigue el protocolo r4 §3.6.1.1.
>
> El texto de abajo **no se ha modificado**: su sha256 en `b863634` es `78dfa8ca…`
> (`../evidencia/13-correccion-s14/protocolo-v2-r3.sha256`).

**Estado: preparación corregida. E-carga NO se ha ejecutado ni programado.** No se ha arrancado ningún generador, no
se ha lanzado ningún ataque, no se ha activado ninguna restricción y no se ha iniciado la 4B, la 4C ni la campaña B. El
modelo IF, las 28 características, α, los heurísticos y la política de respuesta no se han tocado. La ejecución exige una
orden posterior y explícita de Mark (§8).

**Qué sustituye.** Esta r2 sustituye, de [`PREPARACION-ECARGA-v2.md`](PREPARACION-ECARGA-v2.md) (r1, `fef1ebd`, sha256
`79a24275…`):
- §1.2 y §1.3: las herramientas;
- §3: la secuencia del día;
- §4.4: S14;
- §5: la parada.

El resto de la r1 sigue vigente: §2, §4.1–4.3 y §4.5–4.7, §6 y §7.

Las copias [`guiones-c7f24510/`](guiones-c7f24510/) y [`evaluacion-e83f4be6/`](evaluacion-e83f4be6/) se conservan
**selladas y sin cambios** como evidencia. Están **sustituidas** y no se usan. En los hosts tienen al lado un aviso
`*.SUSTITUIDO.txt`.

Protocolo: `PROTOCOLO-CARGA-v2.md` **r3** (S14 en §3.6.1, S2/S3 en §3.6.2 y P0 ampliado en §3.5, puntos 10–12).

## 1. Defectos, causa, corrección y prueba

Pruebas: [`tests/test_etapa4_ecarga_prep.py`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/a12deae/tests/test_etapa4_ecarga_prep.py),
en el banco Docker, sin red y sin acceso al laboratorio. `systemctl`, `sudo`, `ssh`, `curl`, `nft` y `pgrep` son dobles
(`tests/ecarga_banco/bin`), y `/proc` de los generadores es un directorio simulado.

Columna «anterior»: la versión de `guiones-c7f24510` / `evaluacion-e83f4be6` (salida en
`../evidencia/12-correccion-preparacion/banco-anterior-regresiones.txt`). Columna «r2»: la de `a12deae`.

| # | Defecto | Causa | Corrección | Prueba | Anterior | r2 |
|---|---|---|---|---|---|---|
| 1 | `generadores.sh arrancar` da rc 0 tras un `systemctl start` fallido | Imprimía `start rc=$?` y salía con el rc de `estado` | rc inequívocos: 0 confirmado, 2 precondición, 3 error de start/stop, 4 leído y no coincide, 5 desconocido. Tras un start fallido: `ARRANQUE_FALLIDO` y rc 3 | `…arranque_fallido…` | rc 0 | rc 3 |
| 2 | Arranque parcial o con el argv equivocado aceptado | Solo contaba procesos `clientes_lab.py` | Confirma el target activo y cada unidad `active/running`, con `MainPID` cuyo argv es `--perfil <p> --origen <IP>`. Los procesos deben ser exactamente esos seis PID, y seguir iguales (PID y `NRestarts`) 5 s después | `…arranque_parcial`, `…argv…` | rc 0 | rc 4 |
| 3 | Consulta fallida leída como «inactivo» | `systemctl is-active` vacío se tomaba por «no active» | `leer_unidad` valida `LoadState`, `ActiveState`, `SubState`, `MainPID` y `NRestarts`. Si una consulta falla o llega incompleta: `consulta=ERROR` y rc 5 | `…consulta_fallida…` (estado, arranque y parada) | rc 0, «parados» | rc 5 |
| 4 | No se comprobaba la configuración real de las unidades | No se leían `PartOf` ni `ExecStart` | `configuracion`: unidad cargada, `PartOf=cyberflow-lab.target` y argv del perfil. `arrancar` lo exige, y además un estado «parado confirmado» | `…sin_partof…`, `…procesos_previos` | arranca | rc 2, sin start |
| 5 | Parada confirmada con un conteo global | `pgrep -fc` más `is-active` | `comprobar_parado`: target inactivo; las seis unidades inactivas o `failed`, con `MainPID` 0; y ningún `clientes_lab.py`, aunque esté fuera de las unidades | `…parada_detecta_proceso_huerfano` | rc 1 genérico | rc 4 y el PID |
| 6 | La parada fallida no se distinguía | `exit 1` para cualquier cosa | Error de stop: rc 3 con `confirmado=si/no`. Sin efecto: rc 4. No se puede leer: rc 5 | `…parada_fallida`, `…sin_efecto` | rc 1 | rc 3 / rc 4 |
| 7 | Hash del generador truncado | Comparaba `cut -c1-8` | Compara el sha256 completo, `ae5134a7…cdc3` | `…hash_completo…` | 8 caracteres | 64 |
| 8 | `muestreo_bastion.sh` marca `parado=1` aunque falle | Asignaba `parado=1` después de cualquier intento | Estados `solicitada`, `fallida`, `confirmada` y `agotada`, en `parada.jsonl` y `eventos.log` con la salida remota. Un intento por muestra, hasta 6. Si un rc 3 lo confirma `comprobar-parado`, cuenta como confirmada. Al agotarse: `INTERVENCIÓN NECESARIA`, `DIR/PARADA-NO-CONFIRMADA` y rc 4 | `…ssh_falla_en_parada_agota…`, `…fallida_y_recuperacion`, `…rc_remoto_4` | rc 0, 1 intento, generadores vivos | rc 4 tras 3 de 3; o recuperación y rc 0 |
| 9 | Lecturas fallidas escritas como valores válidos | `sudo nft` fallido daba el hash de la salida vacía; un PID ilegible daba «0 `--aplicar`»; sin `pipefail` | `pipefail`; `q()`; `ERROR` en cada lectura; `S/D/C ERROR rc=N` si el ssh falla; `cuenta()` numérico | `…lecturas_fallidas_se_escriben_error` | `ruleset=e3b0c442…` | `ruleset=ERROR` |
| 10 | `derivar_bastion.py` convierte `ERROR` en `false` | El estado `ERROR` contaba como «no activo» | `g()` devuelve `None` si el grupo es `ERROR` | `…bastion_lectura_error_no_es_false` (datos del 06-nov) | S1 y S10 `false` | ningún `false`, `null` |
| 11 | **Cobertura de PCAP:** con dos PCAP en T+2 s y T+7 s da S2 = S3 = true | Solo miraba los ficheros cuyo nombre caía en la ventana. S3 = salto máximo entre ellos | `derivar_pcap.py` 2026-11-06.2 (protocolo r3 §3.6.2): cadena con los ficheros de los bordes, lectura completa (primera y última pasada, huecos entre pasadas, `obs_pcap.log`), no comprobados, vacíos, duplicados y desorden. `false` = demostrado; `null` = sin evidencia, con el motivo | `…dos_ficheros…`, `…falta_el_inicio`, `…falta_el_final`, `…truncada`, `…primera_pasada_tardia`, `…fichero_ilegible…`, `…duplicado_contradictorio` | S2 = S3 = true (7 de 7 fallan) | `null`/`false` |
| 12 | **De punta a punta:** una cobertura que falta habilita la condición (3) | `construir_entrada` copiaba S2/S3 de cualquier versión y S14 era manual | `construir_entrada` 2026-11-06.2 exige `derivar_pcap 2026-11-06.2`, `derivar_bastion 2026-11-06.2` y `evaluar_s14 2026-11-06.1`; otra versión → `null`. S14 sale de `--s14` y ya no se admite como manual | `…e2e_dos_pcap_no_habilita`, `…e2e_pcap_falta_el_final…` | **`habilita_condicion_3` = true** | `false` |
| 13 | S14 sin regla | Era «manual» | `muestreo_s14.py` (1 s) y `evaluar_s14.py`, según protocolo r3 §3.6.1 | 11 casos `test_s14_*` y 2 E2E | sin herramienta | ver §3 |

**Hallado al escribir las pruebas, antes de publicar** (no estaba en ninguna versión publicada): en `evaluar_s14.py`, un
dato ausente en mitad de una saturación partía el episodio en dos tramos de menos de 8 s, y la componente salía `true`.
Ahora queda `null` («dudoso») y nunca `true`. Prueba: `test_s14_lectura_fallida_dentro_de_una_saturacion_no_da_true`.

## 2. Referencias exactas

**Producto `a12deae`**, rama `recuperacion/etapa4a-pendientes-20261106`. **No se ha fusionado en `main`.** Ubicación
canónica: `deploy/etapa4/ecarga/`.
- `SHA256SUMS`: sha256 `9ff24889…a8a9fb`.
- Evaluador: `deploy/etapa4/sensor1/evaluar_ecarga.py` **2026-11-06.4**, sha256 `53e9f7bd…c5d23f`, sin cambios.

| Fichero | Versión | sha256 |
|---|---|---|
| `generadores.sh` | 2026-11-06.2 | `0badeac51ccf2339122412a7607b01176b22f97413e927134bb11ab208a3f662` |
| `muestreo_bastion.sh` | 2026-11-06.2 | `35c3248fd9157b0cc9c12d9c1d6aec3ea1112233a99bfa6cea1582ead26d459f` |
| `guardia.py` | 2026-11-06.2 | `37581e901103353fc27d15958d0601948c6da88b2625c3be8959fd2536a8dc0d` |
| `sensor1_muestreadores.sh` | 2026-11-06.2 | `25fb732ddc15bc83f1f1a79e6e9ccb7ca0cd867a2dfd48270a26dd9ba03c915b` |
| `muestreo_s14.py` | 2026-11-06.1 | `c4ef7c845df49c1c63e16b2e92d8a71c1f517fab007359864122131eff88e67f` |
| `sensor1_post.sh` | 2026-11-06.2 | `9be5ed13ef7e781a268326f0708e46af30caf0af8a35252ead3d43b42d6ec13b` |
| `derivar_pcap.py` | 2026-11-06.2 | `64b51deaad50c2fa8751248d24313f7b9af1d3fb975e085b783475505ba0c7fc` |
| `evaluar_s14.py` | 2026-11-06.1 | `ba2ba3b99fcc92daa1192f3af0090d712e7cd7d2f0ec9d8f8da087f4aef03cee` |
| `derivar_bastion.py` | 2026-11-06.2 | `09c4a0dfd8610be719719f4fe1fa06c501d7e68a45c8f64e16bb7ff4e1f3ec38` |
| `construir_entrada.py` | 2026-11-06.2 | `9fa51ea5ccee3bc79481e4cd4618346ec8a058fdfbb68fe8b1bbc1fbc4836167` |

**Paquete en los hosts.** `~/cf-e4/paquete-a12deae`, en el bastión, en Sensor1 y en srv-dmz (06-nov, 16:33Z), sin
instalar nada y sin sobrescribir:
- tgz `4463b2f9…`;
- `SHA256SUMS` interno `7b35ec72…` (480 ficheros);
- `sha256sum -c --strict` rc 0 en los tres;
- evaluador = publicado en los tres;
- `ecarga/SHA256SUMS` = publicado en los tres.

Clientes no lo necesita: `generadores.sh` le llega por stdin desde el bastión. Transcripción:
`../evidencia/12-correccion-preparacion/paquete-a12deae.txt`.

## 3. S14

La definición está en `PROTOCOLO-CARGA-v2.md` r3 **§3.6.1**. Se publica antes de cualquier ensayo y no se aplica a
ninguna observación anterior. Para cada componente fija:
- métrica, unidad y fuente;
- muestreo a 1 s;
- límite inclusivo, y duración ≥ 8 s;
- justificación;
- cobertura ≥ 99 %, sin huecos > 4 s;
- tratamiento de lecturas fallidas, datos ausentes y reinicios;
- condiciones de `true`, `false` y `null`.

Utilización alta **no** es saturación: se exige capacidad agotada **y** espera (PSI), o un hilo o CPU no repartible al
95 %. «Nueva» se mide contra la línea base [T_g − 300 s, T_g).

**Recomendación de alcance: adoptar la r3 tal cual.** Con ella S14 deja de ser manual. Si la medida falta o no cubre la
ventana, S14 queda `null` y el veredicto es «no demostrable»: no habilita nada. La alternativa, mantener S14 manual sin
regla, dejaría S14 en `null` para siempre y E-carga nunca podría habilitar la condición (3). No se pide a Mark ningún
umbral técnico. Lo que necesita es aprobar la r3 como parte de la orden de ejecución (§8).

Pruebas (`test_s14_*`): por debajo, en y por encima del límite; utilización sin espera; 7 s frente a 8 s; hilo, softirq,
disco y memoria; `softnet`, `oom_kill` y reinicio de contador; datos ausentes y cobertura incompleta; lectura fallida
dentro de una saturación; reinicio de Suricata; línea base saturada o ausente.

## 4. Pruebas y regresiones

| Ejecución | Resultado | Evidencia (`../evidencia/12-correccion-preparacion/`) |
|---|---|---|
| Banco nuevo, usuario 65534 | **56 pasan**, 0 fallan, 0 omitidas | `banco-nuevo-65534.txt` |
| Banco nuevo, root | **56 pasan**, 0 fallan, 0 omitidas | `banco-nuevo-root.txt` |
| Versión anterior, `-k regresion` | **26 de 26 fallan**, cada una en la aserción del defecto. Las 30 restantes no se seleccionan; las de S14 y la comprobación de versiones no existen en la versión anterior | `banco-anterior-regresiones.txt` |
| Suite completa del producto, usuario 65534 | 978 pasan, 0 fallan, 53 omitidas | `suite-completa-nuevo.txt` |
| Suite completa, root + `NET_ADMIN` (red aislada) + repo de documentación | **1 028 pasan**, 0 fallan, 3 omitidas | `suite-completa-root.txt` |
| `test_dashboard_gui_contract.py` en el portátil (con node) | 5 pasan | `gui-node-portatil.txt` |

**Fallos previos:** ninguno.

**Omisiones, comprobadas una a una (no se atribuyen al entorno sin verificarlo):**
- Las 53 de la pasada sin root piden root, `nft` o el repo de documentación (`CAMPANA_DIR`). Con los tres, en la pasada
  root, corren y pasan.
- De las 3 que quedan como root:
  - las 2 de `chmod 000` no tienen sentido como root, y en la pasada 65534 corren y pasan;
  - la de `node` se omite porque la imagen no tiene `node` (`command -v node` vacío, comprobado), y en el portátil
    pasa.

## 5. Comprobaciones en vivo hechas hoy (solo lectura, 06-nov 16:35Z; se repiten en P0)

Transcripción: `../evidencia/12-correccion-preparacion/lecturas-previas.txt`.

| Comprobación | Resultado |
|---|---|
| `generadores.sh configuracion` (a12deae) | **rc 0**: las seis unidades cargadas, con `PartOf=cyberflow-lab.target` y el argv de su perfil e IP |
| `generadores.sh estado` | target inactivo y deshabilitado; hash `ae5134a7`; 0 procesos; seis unidades `inactive/dead`, `MainPID` 0; `consulta=ok` |
| `sensor1_muestreadores.sh comprobar` | **rc 0**, sin ningún FALLO:<br>- retención del anillo 936 s (≥ 900);<br>- PSI, `vmstat`, `diskstats` y `USER_HZ` legibles;<br>- `obs_pcap --en-seco` rc 0, `fin_utc` 2026-11-09T04:16:00Z;<br>- `/home` 12 098 MiB;<br>- `MemAvailable` 6 644 MiB |

En la primera pasada del guion de lecturas, un `ssh` sin `< /dev/null` consumió la entrada y cortó el resto de las
lecturas. Era un error del guion de evidencia, no del producto. Se corrigió y se repitió entero, también solo de
lectura.

## 6. Secuencia del día (SOLO TRAS ORDEN EXPLÍCITA DE MARK; sustituye a la r1 §3)

La franja es la misma, **sin programar**:

| Paso | Epoch | Hora UTC |
|---|---|---|
| P0 | 1794191400 | 02:30Z |
| Línea base de S14 | 1794192900–1794193200 | 02:55–03:00Z |
| T_g | 1794193200 | 03:00Z |
| Ventana | 1794194100–1794197700 | 03:15–04:15Z |
| Fin de `obs_pcap` | 1794197760 | 04:16Z |
| Parada | 1794197820 | 04:17Z |
| Análisis, no antes de | 1794198600 | 04:30Z |

Abreviaturas:
- P = `~/cf-e4/paquete-a12deae`
- E = `$P/deploy/etapa4/ecarga`
- X = `~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z`
- CLI = `ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20`

**Quién ejecuta.** Lo ejecuto yo desde el portátil, por ssh al bastión y desde ahí a cada host. Ningún paso necesita la
contraseña de sudo de Mark. La excepción es la intervención de §7, si la parada no se confirma.

**Paso 0.** Igual que la r1: la franja sigue siendo viable y no se desplaza en silencio.

**Paso 1: P0, 02:30Z.** Solo lecturas. Si algo no da 0, no se arranca nada.

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
P=~/cf-e4/paquete-a12deae; E=$P/deploy/etapa4/ecarga; X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z
CLI="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
mkdir "$X" "$X/manual" || exit 2
(cd $P && sha256sum -c --strict --quiet SHA256SUMS) && (cd $E && sha256sum -c --strict --quiet SHA256SUMS) || exit 2
$CLI 'bash -s configuracion'    < $E/generadores.sh || exit 2   # rc 0: PartOf y argv de las seis unidades
$CLI 'bash -s permisos'         < $E/generadores.sh
$CLI 'bash -s comprobar-parado' < $E/generadores.sh || exit 2   # PARADO_CONFIRMADO
# relojes, los 3 verificadores con rc 0 y S11 «antes»: igual que la r1 §3, paso 1
```

```bash
# [SENSOR1 m4rk] → lo ejecuto yo (desde el bastión)
bash ~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga/sensor1_muestreadores.sh comprobar \
  ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1-comprobar 1794197760 2026-11-09T04:16:00Z   # rc 0; anillo >= 900 s, PSI
```

**Paso 2: 02:50Z, muestreadores.** Tienen que estar arrancados antes de 02:55Z, que es el inicio de la línea base de
S14.

```bash
# [SENSOR1 m4rk] → lo ejecuto yo. rc 3 = algún muestreador no quedó vivo -> parar y no seguir
bash ~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga/sensor1_muestreadores.sh arrancar \
  ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 1794197760 2026-11-09T04:16:00Z
```

```bash
# [BASTIÓN gadmin] → lo ejecuto yo. FIN 04:18Z (muestra <= 60 s después de HASTA); PARADA 04:17Z
setsid nohup bash $E/muestreo_bastion.sh "$X/bastion" 1794197880 1794197820 real > "$X/bastion.out" 2>&1 < /dev/null &
```

**Paso 3: T_g = 1794193200, arranque.** En primer plano, y solo tras la orden; no es una tarea programada.

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
while [ "$(date +%s)" -lt 1794193200 ]; do sleep 0.2; done
$CLI 'bash -s arrancar' < $E/generadores.sh; rc=$?; echo "arrancar rc=$rc" | tee "$X/manual/arranque.rc"
if [ $rc != 0 ]; then                       # 3 fallido · 4 parcial/inestable · 5 desconocido
  $CLI 'bash -s parar' < $E/generadores.sh; echo "parar rc=$?" | tee -a "$X/manual/arranque.rc"
  echo "E-carga ABORTADA en el arranque: no hay ventana que evaluar" | tee -a "$X/manual/arranque.rc"
fi
```

Si `arrancar` no da 0, **no hay ensayo**:
- se para;
- se conserva la evidencia;
- el resultado se publica como «no ejecutado por fallo de arranque»;
- no se reintenta sin una orden nueva.

`ARRANQUE_CONFIRMADO` exige seis PID estables durante 5 s.

**Vigilancia durante la ventana.** Solo se leen `tail` de `$X/bastion/eventos.log`, de `guardia.jsonl` y de
`parada.jsonl`, y `sensor1_muestreadores.sh estado`.

**Paso 4: fin y parada.**
- **04:16Z.** Los muestreadores de Sensor1 terminan solos.
- **04:17Z.** `muestreo_bastion.sh` pide la parada:
  - `PARADA confirmada`: `generadores.sh parar` rc 0, o rc 3 confirmado por `comprobar-parado`;
  - `PARADA FALLIDA`: se reintenta en cada muestra, hasta 6 intentos.
- **Al terminar.** `muestreo_bastion.sh` sale con **rc 0** si la parada se confirmó y con **rc 4** si no. Su rc queda
  al final de `$X/bastion.out` y en `eventos.log`.
- **Comprobación independiente**, siempre:

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
$CLI 'bash -s comprobar-parado' < $E/generadores.sh; echo "rc=$?"   # 0 = PARADO_CONFIRMADO
tail -3 "$X/bastion/parada.jsonl"; ls "$X/bastion/PARADA-NO-CONFIRMADA" 2>/dev/null && echo "INTERVENCIÓN (§7)"
```

**Paso 5: análisis, no antes de 04:30Z.** Solo lecturas.

```bash
# [SENSOR1 m4rk] → lo ejecuto yo. Ventana y línea base de S14
bash ~/cf-e4/paquete-a12deae/deploy/etapa4/ecarga/sensor1_post.sh ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 \
  1794194100 1794197700 1794192900 1794193200
```

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
scp -r -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 "$X/post-sensor1"
(cd "$X/post-sensor1/post" && sha256sum -c --strict --quiet SHA256SUMS)
python3 -I $E/derivar_bastion.py "$X/bastion/muestras.txt" 1794194100 1794197700 > "$X/bastion_s.json"
python3 -I $E/construir_entrada.py --desde 1794194100 --hasta 1794197700 \
  --clasificacion "$X/post-sensor1/post/clasificacion/clasificacion.json" --comparar "$X/post-sensor1/post/comparar.json" \
  --perfiles "$X/post-sensor1/post/perfiles.json" --perfiles-rc "$(cat "$X/post-sensor1/post/perfiles.rc")" \
  --bastion "$X/bastion_s.json" --pcap "$X/post-sensor1/post/pcap_s.json" --s14 "$X/post-sensor1/post/s14.json" \
  --manual S7=<v>:"$X/manual/s7-obs_p4_post.txt" --manual S11=<v>:"$X/manual/s11-comparacion.txt" \
  --manual S15=<v>:"$X/manual/s15-verificadores-despues.txt" \
  --salida-entrada "$X/entrada-veredicto.json" --salida-traza "$X/trazabilidad.json"
python3 -I $P/deploy/etapa4/sensor1/evaluar_ecarga.py veredicto --entrada "$X/entrada-veredicto.json" > "$X/veredicto.json"; echo $? > "$X/veredicto.rc"
(cd "$X" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS)
```

`<v>` se fija según la regla de la r1 §4.3, después de leer el fichero. S14 ya no se pasa con `--manual`
(`construir_entrada` lo rechaza con rc 2). Los resultados se publican en `evidencia/13-ecarga-ejecucion/` **sea cual
sea el resultado**.

## 7. Parada (sustituye a la r1 §5; las condiciones de §3.7 del protocolo no cambian)

| Situación | Qué se hace | Quién |
|---|---|---|
| Fin previsto o guardia | `muestreo_bastion.sh` lanza `generadores.sh parar` y anota el estado (§6, paso 4) | yo (automático, en el bastión) |
| Parada manual en cualquier momento | `[BASTIÓN gadmin] → lo ejecuto yo`: `$CLI 'bash -s parar' < $E/generadores.sh`. rc 0 = confirmada. rc 3 = error del stop: ejecutar `comprobar-parado`, que confirma con rc 0. rc 4 o 5 = no confirmada: repetir | yo |
| `PARADA-NO-CONFIRMADA` o `muestreo_bastion.sh` rc 4 | **Intervención**: se deja de esperar y se avisa de inmediato. Si `parar` sigue sin confirmar, la vía que queda es `sudo systemctl stop 'cyberflow-lab-*'` en clientes, o la consola | **Mark**: hace falta su contraseña de sudo o la consola física, que yo no tengo |
| Generadores arrancados sin ensayo (arranque ≠ 0) | `parar` de inmediato (§6, paso 3) y abortar | yo |

Un `parar` o un `comprobar-parado` no confirmados **nunca** se registran como «parado».

## 8. Estado y orden necesaria

| Veredicto | Estado | Fundamento |
|---|---|---|
| **Corregido en banco** | **Sí** | 13 defectos con regresión: 26 de 26 fallan con la versión anterior y 56 de 56 pasan con `a12deae`. Suite completa sin fallos (§4) |
| **Preparación lista** | **Sí, a falta de la orden** | Paquete `a12deae` en los hosts y verificado. `configuracion` rc 0 (`PartOf` confirmado). `comprobar` rc 0 (anillo 936 s, PSI). S14 definido en la r3. Todo se repite en P0 |
| **Pendiente de medir en vivo** | Ver la lista | Lo que el banco no puede demostrar |

Pendiente de medir en vivo:
- `arrancar` y `parar` contra el systemd real, con confirmación de PID estables. Hasta ahora solo con dobles; la r1
  probó `parar` con el target ya parado.
- El coste de `muestreo_s14.py` a 1 s en Sensor1, y su cobertura real.
- La retención del anillo **con carga**. Hoy hay 936 s sin carga: 36 s de margen sobre los 900 que supone
  `derivar_pcap`. Si la rotación también fuera por tamaño, la carga la acortaría. `obs_pcap` lee cada 30 s, pero si se
  detuviera más que la retención real se perderían ficheros.
- PSI y softirq por CPU con carga real: la línea base y la ventana de S14.

**Orden necesaria para ejecutar** (ninguna está dada):
1. Autorizo ejecutar E-carga v2 en la franja publicada (lun 09-nov, P0 02:30Z, T_g 03:00Z, ventana 03:15–04:15Z).
2. Esa autorización incluye arrancar `cyberflow-lab.target` con `generadores.sh arrancar` en T_g y pararlo a las 04:17Z o
   por la guardia.
3. Apruebo `PROTOCOLO-CARGA-v2` r3 (S14 según §3.6.1). Es la recomendación de §3.
4. Los resultados se publican en `evidencia/13-ecarga-ejecucion/` sea cual sea el resultado.
