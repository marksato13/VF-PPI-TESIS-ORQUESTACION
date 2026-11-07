# Procedimiento final de E-carga v2 (07-nov)

**Estado: instrucciones consolidadas. E-carga NO se ha ejecutado ni programado.** Este documento no autoriza nada: no
se ha arrancado ningún generador ni muestreador, no se ha modificado ningún servicio, no se ha desplegado ningún paquete
y no se ha activado ninguna restricción. Para redactarlo no se contactó con ningún host.

**Qué sustituye.** Esta es la única secuencia de ejecución vigente. Sustituye a las secuencias de
[`PREPARACION-ECARGA-v2.md`](PREPARACION-ECARGA-v2.md) §3 y [`PREPARACION-ECARGA-v2-r2.md`](PREPARACION-ECARGA-v2-r2.md)
§6, y a la lista de órdenes de la r2 §8 y la r3 §8. Esos documentos se conservan sin cambios y siguen vigentes como
definición de:
- la fuente de cada K y S (r1 §4.1 y §4.2);
- la regla de S7, S11 y S15 (r1 §4.3), con la adaptación de la fase D;
- la parada (r2 §7).

Los criterios son los del [protocolo r4](../PROTOCOLO-CARGA-v2.md): aquí no cambia ningún K, S, umbral ni franja. Tampoco
cambian el detector, el modelo IF, las características, α, los heurísticos ni la política de respuesta.

## 1. Referencias confirmadas (07-nov, 02:03Z)

Consulta a los remotos sin ningún cambio posterior a las referencias revisadas.

| Qué | Referencia exacta |
|---|---|
| Documentación | `VF-PPI-TESIS-ORQUESTACION`, main, última revisada `999bce698d508cbb51f7ae0a1bcb792367ff165d`, más el commit que publica este procedimiento |
| Producto | rama `recuperacion/etapa4a-pendientes-20261106` en `975e715808f3ad454055712660414f2e8fd50878`. main del producto sigue en `7b275b8` |
| Paquete en los hosts | `~/cf-e4/paquete-902991e`, SHA256SUMS interno `8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c`; `ecarga/SHA256SUMS` `e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80`. **No se modifica** |
| Protocolo vigente | `PROTOCOLO-CARGA-v2.md` r4, commit `034d57d` |
| Evaluador | `evaluar_ecarga.py` 2026-11-06.4, `53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f` |

### Herramientas vigentes

| Uso | Herramienta | Versión o sha256 | Dónde corre |
|---|---|---|---|
| Referencias e integridad | `evidencia/20-procedimiento-final/herramientas/00_referencias.sh` | 2026-11-07.1 | laptop |
| Procesos del ensayo | `evidencia/19-correccion-p11/laboratorio/previa.sh` + `previa_host.sh` | `4e1dd442…` | laptop → 4 hosts |
| Post-copia | **r3**: `evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh` | host `799af8f1…` | laptop → 3 hosts |
| P0 | **r3**: `evidencia/19-correccion-p11/p0-r3/p0_r3.sh` | 2026-11-06.r3; bloque Sensor1 `5ef3372a…` | laptop → 3 hosts + clientes |
| P8 | `evidencia/20-procedimiento-final/herramientas/comprobar_p8.sh` | 2026-11-07.1 | laptop + GitHub |
| P12 | `evidencia/20-procedimiento-final/herramientas/comprobar_p12.sh` + `comprobar_p12_host.sh` | host `b45e950b…` | laptop → Sensor1 |
| Instantáneas | `evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh` | la publicada | laptop → 3 hosts |
| Muestreo y generadores | paquete: `generadores.sh`, `muestreo_bastion.sh`, `guardia.py`, `sensor1_muestreadores.sh` | 2026-11-06.2 | hosts |
| Análisis | paquete: `sensor1_post.sh`, `derivar_bastion.py` (.2), `construir_entrada.py` (.3), `evaluar_s14.py` (.2) | r3 §6 | hosts |

**Mecanismo sin escritura de P0 r3.** El paquete sigue con `sensor1_muestreadores.sh` 2026-11-06.2. El bloque
`sensor1_r3.sh` deriva en memoria la versión .4, sin escribir nada:
1. .2 con sha `25fb732d…`;
2. .3 con sha `4ed4385674e9f731c7d50f12b132d86a0a3625355df24ebaf4fa9fa0c8342b6e`;
3. .4 con sha `63f7495714bf43c750748a1a6aad1e0506d10478b67034e41bd395490c05f823` (producto `975e715`).

Si un hash no coincide, no ejecuta nada y da ERROR. Lo deja registrado en `REQ X.mecanismo_sin_escritura`.

### Lo que NO se usa

| No usar | Motivo |
|---|---|
| `sensor1_muestreadores.sh comprobar` lanzado desde el paquete | La .2 escribe caché en el paquete. **Solo se comprueba a través de P0 r3**. `arrancar`, `estado` y `parar` del paquete sí valen: las versiones .3 y .4 solo cambian `comprobar` |
| P0 r2 y `p0_anticipado.sh` | P11 con falso positivo; el primero de todos daba rc 0 con los ssh fallidos |
| Comprobadores post-copia r1 y r2 | Sustituidos por la r3 |
| `paquete-a12deae`, `paquete-ae2900e`, `paquete-f6dc685` | No son el paquete vigente (protocolo r4 §3.5, punto 13) |
| `guiones-c7f24510/`, `evaluacion-e83f4be6/` | Sellados como evidencia; no se usan |
| `--manual S14` | `construir_entrada.py` lo rechaza |
| Carpeta `evidencia/12-…` o `13-ecarga-ejecucion/` | Los resultados van a `evidencia/14-ecarga-ejecucion/` |

**Texto antiguo que este procedimiento aclara.** El protocolo r4 §3.3 y §3.5, puntos 9 y 10, siguen citando `ae2900e` y
`a12deae`. El punto 13 los resuelve: el paquete es `902991e`. El evaluador tiene el mismo sha en ese paquete, y los
verificadores son los mismos bytes de `a1cea5e`. El protocolo no se ha editado.

## 2. Los tres requisitos que no decide el P0 anticipado

El P0 anticipado publicado dio 9/9 bloques y 51/51 anticipables. P5b, P8 y P12 quedaron `NO_EVALUABLE` en esa herramienta.
Eso no significa lo mismo en los tres casos:

| Requisito | Evidencia necesaria | Momento de comprobación | Responsable | Estado hoy |
|---|---|---|---|---|
| **P5b**: `date -u` de Sensor1 dentro de la franja [1794191400, 1794200400] | `REQ P5b CUMPLE` en `06-sensor1.stdout` del P0 r3 **inmediato**, con `RESULTADO_GLOBAL rc=0 modo=inmediato` | Paso A6, desde las 02:30:00Z del 09-nov. No se puede aprobar antes para una ejecución futura | Claude ejecuta y registra. Si no cumple, se detiene | **Sin observar.** Pendiente |
| **P8**: ventana fijada en epoch y publicada, con su commit, antes de T_g | Documento `PROTOCOLO-CARGA-v2.md` §3.2. Commit `8f17273b51ea72d94c394ef740b2dc9456690f45`, fecha 2026-11-06 02:26:43 −0500, **llegada a main 2026-11-06T07:26:48Z** según el registro de GitHub. Revisión r4 `034d57d`, llegada a main 2026-11-06T17:26:31Z. Tabla §3.2 idéntica de `8f17273` a `999bce6`: sha256 `d450f44d1720eab6a1a02e6c27e52337cd26e70ee4a64c2dc66ed99f4cc40460` | Verificada hoy; se repite en el paso A5 para demostrar que la franja no cambió antes de T_g | Claude verifica; Mark revisa la evidencia al dar la orden | **Evidencia existente: CUMPLE en la verificación del 07-nov** (`evidencia/20-procedimiento-final/p8-verificacion-20261107T020848Z/p8.txt`). P0 r3 la marca `NO_EVALUABLE` solo porque esa herramienta no consulta el repositorio |
| **P12**: muestreadores, incluido S14, arrancados antes de T_g − 300 s = 1794192900 (02:55:00Z) | Tres marcas reales: `arrancar-muestreadores.txt` (`ARRANQUE_CONFIRMADO`, 4 `vivo`, `FIN_ARRANCAR epoch=… rc=0`), línea `arrancados` de `eventos.log` y `"inicio"` de `s14.jsonl`. Las tres < 1794192900 | Paso B3, tras un arranque autorizado. No se arranca nada para resolverlo antes | Claude arranca y comprueba, **solo con la orden de Mark** | **Sin observar.** Solo se ha probado el comprobador, en banco, con marcas simuladas |

La línea base de S14 no se decide en P12: su cobertura la evalúa `evaluar_s14.py` en la fase D.

## 3. Calendario y viabilidad

Se comprobó cada epoch con `date -u` y con la zona `America/Lima`. Coincide con el protocolo r4 §3.2. El 09-nov es lunes
en UTC (ISO 1), domingo 08-nov en Perú. El criterio de día laborable se aplica en UTC.

| Hito | Epoch | UTC (lun 09-nov) | Perú (UTC−5) |
|---|---|---|---|
| Inicio de la fase A | — | ≈ 02:05:00 | dom 21:05:00 |
| **P0 r3 inmediato**, no antes de | 1794191400 | 02:30:00 | dom 21:30:00 |
| **Arranque de muestreadores** | 1794192600 | 02:50:00 | dom 21:50:00 |
| **Límite P12 e inicio de la línea base S14** | 1794192900 | 02:55:00 | dom 21:55:00 |
| **T_g**, arranque de generadores | 1794193200 | 03:00:00 | dom 22:00:00 |
| **Ventana fija** | 1794194100–1794197700 | 03:15:00–04:15:00 | dom 22:15:00–23:15:00 |
| Fin de `obs_pcap` y muestreadores de Sensor1 | 1794197760 | 04:16:00 | dom 23:16:00 |
| Parada de generadores | 1794197820 | 04:17:00 | dom 23:17:00 |
| Fin del muestreo del bastión | 1794197880 | 04:18:00 | dom 23:18:00 |
| Análisis, no antes de | 1794198600 | 04:30:00 | dom 23:30:00 |
| Lecturas posteriores, hasta | 1794200400 | 05:00:00 | lun 00:00:00 |

**Viabilidad a 07-nov, 02:08Z: la franja sigue siendo viable.** Faltan unas 48 h para el P0. Depende de tres cosas que
hoy no están aseguradas:
- la orden de Mark;
- una sesión activa de Claude en ese momento, porque nada queda programado;
- que nadie use el laboratorio en esa franja.

Si la franja se pierde, **no se desplaza**. Hace falta una orden nueva de Mark y una franja nueva, publicada antes, con
los mismos desfases y en otra madrugada laborable UTC.

## 4. Secuencia de ejecución futura

Convenciones:
- **[LECTURA]** no arranca, no para y no escribe nada en los hosts.
- **[ESCRITURA]** crea carpetas o ficheros de evidencia, solo dentro de la carpeta del ensayo.
- **[ARRANCA]** o **[DETIENE]** cambia procesos. Solo con la orden de §7.
- Si un paso no da el código esperado: **parar según §5**. No se reintenta sin decisión de Mark.

Variables:

```bash
# [LAPTOP Git Bash]
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06"
EJ="$R/evidencia/14-ecarga-ejecucion"          # evidencia del ensayo; no debe existir
W="/c/Users/markp/cf-ecarga-v2-1"               # copia publicada de las herramientas; no debe existir
```

```bash
# [BASTIÓN gadmin]
P=~/cf-e4/paquete-902991e; E=$P/deploy/etapa4/ecarga; X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z
CLI="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
```

`C` es la ruta de la copia publicada que imprime el paso A1 en la línea `COPIA`.

### Fase A: verificación, solo lectura (02:05–02:45Z)

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| A0 | [LECTURA] | laptop | `date +%s` < 1794191400; Mark confirma que el laboratorio está libre | `$EJ/A0.txt` |
| A1 | [LECTURA] | laptop, `00_referencias.sh` 2026-11-07.1 | rc 0 | `$EJ/A1-referencias.txt` |
| A2 | [LECTURA] | 4 hosts, `previa.sh`, `4e1dd442…` | rc 0, 4 × `SIN_PROCESOS_DEL_ENSAYO` | `$EJ/A2-previa/` |
| A3 | [LECTURA] | 3 hosts, post-copia r3 | rc 0, `CONFORME 3/3` | `$EJ/A3-postcopia-r3/` |
| A4 | [LECTURA] | 3 hosts, `tomar.sh` | rc 0 | `$C/…/instantaneas/antes-p0-inmediato/` |
| A5 | [LECTURA] | laptop y GitHub, `comprobar_p8.sh` | rc 0, `REQ P8 CUMPLE` | `$EJ/A5-p8/` |
| A6 | [LECTURA] | 4 hosts, P0 r3 `inmediato` | rc 0, `P0 INMEDIATO CONFORME`, 9/9, todas las anticipables CUMPLE y P5b CUMPLE | `$EJ/A6-p0-r3-inmediato/` y `.rc-driver` |
| A7 | [LECTURA] | 3 hosts, `tomar.sh` | `comparar` rc 0, 3 × IDENTICAS | `$EJ/A7-comparacion-paquete.txt` |
| A8 | [LECTURA] | laptop | carpeta `X` libre en bastión y Sensor1 | `$EJ/A8.txt` |

`[LAPTOP Git Bash] → lo ejecuto yo` (solo si Mark autoriza la fase A)
```bash
mkdir "$EJ" || exit 2; cd "$HOME" || exit 2
{ date -u +%FT%TZ; date +%s; [ "$(date +%s)" -lt 1794191400 ] && echo "ANTES DE P0: viable"; } | tee "$EJ/A0.txt"
bash "$R/evidencia/20-procedimiento-final/herramientas/00_referencias.sh" "$W" 2>&1 | tee "$EJ/A1-referencias.txt"; echo "rc=${PIPESTATUS[0]}"
C=$(sed -n 's/^COPIA //p' "$EJ/A1-referencias.txt")
cmp "$R/evidencia/20-procedimiento-final/herramientas/00_referencias.sh" "$C/evidencia/20-procedimiento-final/herramientas/00_referencias.sh"
bash "$C/evidencia/19-correccion-p11/laboratorio/previa.sh" "$EJ/A2-previa"; echo "rc=$?"
bash "$C/evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh" "$EJ/A3-postcopia-r3"; echo "rc=$?"
bash "$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh" antes-p0-inmediato; echo "rc=$?"
bash "$C/evidencia/20-procedimiento-final/herramientas/comprobar_p8.sh" "$EJ/A5-p8"; echo "rc=$?"
```

`[LAPTOP Git Bash] → lo ejecuto yo`, no antes de las 02:30:00Z. Si se lanza antes, P5b no cumple y el rc es 5.
```bash
[ "$(date +%s)" -ge 1794191400 ] || { echo "todavía no: P5b exige la franja"; exit 2; }
bash "$C/evidencia/19-correccion-p11/p0-r3/p0_r3.sh" inmediato "$EJ/A6-p0-r3-inmediato"; rc=$?
echo "$rc" > "$EJ/A6-p0-r3-inmediato.rc-driver"; echo "rc=$rc"
T="$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh"
bash "$T" despues-p0-inmediato; bash "$T" comparar antes-p0-inmediato despues-p0-inmediato | tee "$EJ/A7-comparacion-paquete.txt"
```

`[BASTIÓN gadmin] → lo ejecuto yo`
```bash
[ ! -e ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z ] && echo LIBRE || echo OCUPADA
```

`[SENSOR1 m4rk] → lo ejecuto yo` (desde el bastión)
```bash
[ ! -e ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z ] && echo LIBRE || echo OCUPADA
```

**Puerta G.** Solo se pasa a la fase B si se cumplen todas:
- A1, A2, A3, A5, A6 y A7 con su código esperado;
- A8 `LIBRE` en los dos hosts;
- la orden de ejecución de §7 está dada en el chat;
- la hora es anterior a las 02:50Z, con margen para terminar B2 antes de las 02:55:00Z.

### Fase B: muestreadores y P12, solo con la orden de ejecución (02:50–02:58Z)

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| B1 | [ESCRITURA] | bastión | `mkdir` rc 0 | `$X`, `$X/manual` |
| B2 | **[ARRANCA]** | Sensor1, `sensor1_muestreadores.sh` 2026-11-06.2, `arrancar` | rc 0, `ARRANQUE_CONFIRMADO` | `arrancar-muestreadores.txt` |
| B3 | [LECTURA] | Sensor1, `comprobar_p12.sh` | rc 0, `REQ P12 CUMPLE` | `$EJ/B3-p12/` |
| B4 | **[ARRANCA]** | bastión, `muestreo_bastion.sh` 2026-11-06.2, `real` | proceso vivo y PID guardado | `$X/bastion.pid`, `$X/bastion.out` |
| B5 | [LECTURA] | bastión y Sensor1 | muestras presentes y 4 `vivo` antes de T_g | `$X/manual/B5.txt` |

`[BASTIÓN gadmin] → lo ejecuto yo`
```bash
mkdir "$X" "$X/manual" || exit 2
```

`[SENSOR1 m4rk] → lo ejecuto yo` (desde el bastión). **ARRANCA los 4 muestreadores**, a las 02:50:00Z.
```bash
X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z; mkdir "$X" || exit 2
{ bash ~/cf-e4/paquete-902991e/deploy/etapa4/ecarga/sensor1_muestreadores.sh arrancar "$X/sensor1" 1794197760 2026-11-09T04:16:00Z
  r=$?; echo "FIN_ARRANCAR epoch=$(date -u +%s) rc=$r"; } 2>&1 | tee "$X/arrancar-muestreadores.txt"
```

`[LAPTOP Git Bash] → lo ejecuto yo`. Solo lectura.
```bash
bash "$C/evidencia/20-procedimiento-final/herramientas/comprobar_p12.sh" "$EJ/B3-p12"; echo "rc=$?"
```

`[BASTIÓN gadmin] → lo ejecuto yo`. **ARRANCA el muestreo y la guardia**, solo con P12 CUMPLE. FIN 04:18Z, PARADA 04:17Z.
```bash
setsid nohup bash $E/muestreo_bastion.sh "$X/bastion" 1794197880 1794197820 real > "$X/bastion.out" 2>&1 < /dev/null &
echo $! > "$X/bastion.pid"; cat "$X/bastion.pid"
sleep 35; { date -u +%FT%TZ; wc -l "$X/bastion/muestras.txt"; tail -2 "$X/bastion/eventos.log"; tail -1 "$X/bastion/guardia.jsonl"; } | tee "$X/manual/B5.txt"
```

`[SENSOR1 m4rk] → lo ejecuto yo`. Solo lectura.
```bash
bash ~/cf-e4/paquete-902991e/deploy/etapa4/ecarga/sensor1_muestreadores.sh estado ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1
```

### Fase C: calentamiento, ventana fija y parada (03:00–04:18Z)

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| C1 | **[ARRANCA]** | bastión → clientes, `generadores.sh` 2026-11-06.2, `arrancar` | rc 0, `ARRANQUE_CONFIRMADO`: seis PID estables 5 s | `$X/manual/arranque.rc` y `arranque.txt` |
| C2 | [LECTURA] | calentamiento, 03:00–03:15Z. No cuenta | sin parada de guardia | lecturas de vigilancia |
| C3 | [LECTURA] | ventana fija, 03:15–04:15Z. No se corta, no se mueve y no se prolonga | sin parada de guardia | `muestras.txt`, `guardia.jsonl`, `s14.jsonl` |
| C4 | **[DETIENE]** automático | 04:16Z los muestreadores terminan solos. 04:17Z `muestreo_bastion.sh` para los generadores | `PARADA confirmada`, `bastion.out` termina con rc 0 | `parada.jsonl`, `eventos.log` |
| C5 | [LECTURA] | bastión → clientes, `comprobar-parado` | rc 0, `PARADO_CONFIRMADO`; sin `PARADA-NO-CONFIRMADA` | `$X/manual/parado.txt` |

`[BASTIÓN gadmin] → lo ejecuto yo`. **ARRANCA los generadores**, en primer plano y solo con la orden. Si al llegar a este
paso ya pasó T_g, **no se arranca**: el protocolo no fija tolerancia y no se inventa una.
```bash
[ "$(date +%s)" -lt 1794193200 ] || { echo "T_g ya pasó: no se arranca" | tee "$X/manual/arranque.rc"; exit 2; }
while [ "$(date +%s)" -lt 1794193200 ]; do sleep 0.2; done
date -u +%FT%T.%NZ | tee "$X/manual/arranque.txt"
$CLI 'bash -s arrancar' < $E/generadores.sh 2>&1 | tee -a "$X/manual/arranque.txt"; rc=${PIPESTATUS[0]}
echo "arrancar rc=$rc" | tee "$X/manual/arranque.rc"
if [ $rc != 0 ]; then
  $CLI 'bash -s parar' < $E/generadores.sh; echo "parar rc=$?" | tee -a "$X/manual/arranque.rc"
  echo "E-carga ABORTADA en el arranque: no hay ventana que evaluar" | tee -a "$X/manual/arranque.rc"
fi
```

**Vigilancia durante C2 y C3.** Solo se lee `tail` de `$X/bastion/eventos.log`, `guardia.jsonl` y `parada.jsonl`, y
`sensor1_muestreadores.sh estado`.

`[BASTIÓN gadmin] → lo ejecuto yo`. Solo lectura, después de las 04:18Z.
```bash
{ $CLI 'bash -s comprobar-parado' < $E/generadores.sh; echo "rc=$?"; tail -3 "$X/bastion/parada.jsonl"; tail -2 "$X/bastion.out"
  ls "$X/bastion/PARADA-NO-CONFIRMADA" 2>/dev/null && echo "INTERVENCIÓN NECESARIA"; } 2>&1 | tee "$X/manual/parado.txt"
```

### Fase D: análisis (desde las 04:30Z; las lecturas posteriores, hasta las 05:00Z)

Se ejecuta **sea cual sea** lo ocurrido en la ventana, salvo que no llegara a haber ventana.

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| D1 | [ESCRITURA] | Sensor1, `sensor1_post.sh` 2026-11-06.2 | rc de cada paso en `post/rc.txt` | `$X/sensor1/post/` con `SHA256SUMS` |
| D2 | [LECTURA] | P0 r3 `anticipado` como lectura posterior | su rc se conserva y no decide nada por sí solo | `$EJ/D2-lecturas-posteriores/` |
| D3 | [ESCRITURA] | laptop → bastión, S11 y S15 | ficheros escritos | `$X/manual/s11-*`, `s15-*` |
| D4 | [ESCRITURA] | bastión, `obs_p4_post.sh` derivado | S7 evaluable | `$X/manual/s7-obs_p4_post.txt` |
| D5 | [ESCRITURA] | bastión, `derivar_bastion`, `construir_entrada`, `evaluar_ecarga veredicto` | `construir_entrada` rc 0; veredicto rc 0, 1 o 2 | `entrada-veredicto.json`, `trazabilidad.json`, `veredicto.json`, `veredicto.rc` |
| D6 | [ESCRITURA] | bastión, sellado | `SHA256SUMS` de `$X` | `$X/SHA256SUMS` |

`[SENSOR1 m4rk] → lo ejecuto yo`
```bash
bash ~/cf-e4/paquete-902991e/deploy/etapa4/ecarga/sensor1_post.sh ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 \
  1794194100 1794197700 1794192900 1794193200
```

`[LAPTOP Git Bash] → lo ejecuto yo`. **D2**: reutiliza los bloques ya probados para volver a ejecutar los verificadores y
`precheck.sh`. Sus bloques 01–03 dan S15 y su bloque 04 da S11 «después». Solo lectura.
```bash
bash "$C/evidencia/19-correccion-p11/p0-r3/p0_r3.sh" anticipado "$EJ/D2-lecturas-posteriores"; echo "$?" > "$EJ/D2-lecturas-posteriores.rc-driver"
A="$EJ/A6-p0-r3-inmediato/04-precheck-s11.stdout"; Z="$EJ/D2-lecturas-posteriores/04-precheck-s11.stdout"; M="$EJ/manual"; mkdir "$M" || exit 2
sed -n 's/^| //p' "$A" > "$M/s11-precheck-antes.txt"; sed -n 's/^| //p' "$Z" > "$M/s11-precheck-despues.txt"
{ diff <(grep -E '^[0-9a-f]{64} ' "$M/s11-precheck-antes.txt") <(grep -E '^[0-9a-f]{64} ' "$M/s11-precheck-despues.txt"); echo "diff rc=$?"
  grep -h 'ec78ca5 SHA256SUMS OK' "$M/s11-precheck-antes.txt" "$M/s11-precheck-despues.txt"; } > "$M/s11-comparacion.txt"
{ grep -E '^REQ [a-z]+ [A-Z_]+ P1\.' "$EJ/D2-lecturas-posteriores/resumen.txt"; cat "$EJ/D2-lecturas-posteriores"/0[123]-verificar-*.stdout; } > "$M/s15-verificadores-despues.txt"
scp -q -i ~/.ssh/id_ed25519 "$M"/s11-* "$M"/s15-* "$C/evidencia/06-observacion/obs_p4_post.sh" gadmin@10.10.10.30:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/manual/
```

`[BASTIÓN gadmin] → lo ejecuto yo`. **D4 y D5**. `<v>` se fija leyendo cada fichero, nunca antes, con la regla de §4.4.
```bash
scp -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/arrancar-muestreadores.txt "$X/manual/"
scp -r -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 "$X/post-sensor1"
(cd "$X/post-sensor1/post" && sha256sum -c --strict --quiet SHA256SUMS); echo "post sellado rc=$?"
[ "$(sha256sum < "$X/manual/obs_p4_post.sh" | cut -c1-64)" = 25d8d3697087d9c7c035986ec42d2f4d15e1fc9a6bf5c0e083d55a2a34a6db62 ] || exit 2
sed -E "s#^O=.*#O=$X/bastion#" "$X/manual/obs_p4_post.sh" > "$X/manual/obs_p4_post.derivado.sh"; sha256sum "$X/manual/"obs_p4_post*.sh | tee "$X/manual/s7-hashes.txt"
bash "$X/manual/obs_p4_post.derivado.sh" 1794194100 1794197700 > "$X/manual/s7-obs_p4_post.txt" 2>&1; echo "s7 rc=$?"
python3 -I $E/derivar_bastion.py "$X/bastion/muestras.txt" 1794194100 1794197700 > "$X/bastion_s.json"
python3 -I $E/construir_entrada.py --desde 1794194100 --hasta 1794197700 \
  --clasificacion "$X/post-sensor1/post/clasificacion/clasificacion.json" --comparar "$X/post-sensor1/post/comparar.json" \
  --perfiles "$X/post-sensor1/post/perfiles.json" --perfiles-rc "$(cat "$X/post-sensor1/post/perfiles.rc")" \
  --bastion "$X/bastion_s.json" --pcap "$X/post-sensor1/post/pcap_s.json" --s14 "$X/post-sensor1/post/s14.json" \
  --manual S7=<v>:"$X/manual/s7-obs_p4_post.txt" --manual S11=<v>:"$X/manual/s11-comparacion.txt" \
  --manual S15=<v>:"$X/manual/s15-verificadores-despues.txt" \
  --salida-entrada "$X/entrada-veredicto.json" --salida-traza "$X/trazabilidad.json"; echo "construir rc=$?"
python3 -I $P/deploy/etapa4/sensor1/evaluar_ecarga.py veredicto --entrada "$X/entrada-veredicto.json" > "$X/veredicto.json"; echo $? > "$X/veredicto.rc"
(cd "$X" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS)
```

### 4.4 Regla de S7, S11 y S15 (sin cambios de criterio)

| S | `true` | `false` | `null` |
|---|---|---|---|
| **S7** | «entregadas NO aceptadas: 0», «aceptadas en orden: True» y «publicador … sin retroceso: True» | alguna de las tres no se cumple | ninguna entrega en la ventana, o el guion falla |
| **S11** | `diff` vacío (rc 0) y las dos líneas `ec78ca5 SHA256SUMS OK` | algún hash difiere | falta alguno de los dos ficheros |
| **S15** | `P1.bastion`, `P1.sensor1` y `P1.srvdmz` en CUMPLE | alguno en NO_CUMPLE | alguno en ERROR o SIN_VERIFICAR |

**Única adaptación de método.** S11 «antes» y «después» salen de `precheck.sh` ejecutado por el bloque de P0, con su sha
`b3127edd…` comprobado, en vez de copiarlo a `$X/manual`. Es el mismo guion y la misma regla, y no deja ficheros nuevos en
los hosts antes de la orden.

### Fase E: conservar y publicar, sea cual sea el resultado

| Paso | Clase | Host | Código esperado | Evidencia |
|---|---|---|---|---|
| E1 | [ESCRITURA] local | laptop ← bastión | `sha256sum -c --strict` rc 0 sobre la copia | `$EJ/bastion-X/` |
| E2 | [LECTURA] | 3 hosts, `tomar.sh` | se publica el resultado de `comparar`, sea el que sea | `$EJ/E2-comparacion-paquete.txt` |
| E3 | [ESCRITURA] local | laptop | `SHA256SUMS` de 14 y `MANIFIESTO.sha256` verifican | `$EJ/SHA256SUMS` |
| E4 | publicación | laptop → GitHub, main | verificación sobre lo publicado | commit de docs |

`[LAPTOP Git Bash] → lo ejecuto yo`
```bash
scp -r -q -i ~/.ssh/id_ed25519 gadmin@10.10.10.30:cf-e4/ecarga-v2-ejecucion-20261109T0300Z "$EJ/bastion-X"
(cd "$EJ/bastion-X" && sha256sum -c --strict --quiet SHA256SUMS); echo "copia rc=$?"
T="$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh"
bash "$T" despues-ensayo; bash "$T" comparar despues-p0-inmediato despues-ensayo | tee "$EJ/E2-comparacion-paquete.txt"
cp -r "$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/antes-p0-inmediato" "$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/despues-p0-inmediato" \
      "$C/evidencia/18-cache-archivada-postcopia-p0/instantaneas/despues-ensayo" "$EJ/"
```

Identificador de la corrida: **`E-carga-v2-1`**. El README de `evidencia/14-ecarga-ejecucion/` recoge el veredicto de
`veredicto.json` tal como sale, K1–K5, S1–S15, K4b, clase, señales y propuestas, incidencias y la tabla de §6.

## 5. Interpretar y detenerse

| Situación | Significado | Qué se hace | Quién |
|---|---|---|---|
| A0: ya pasó la hora de inicio de P0 con margen insuficiente | Franja no viable | No se arranca nada. Se informa. No se desplaza | Claude informa; Mark decide |
| A1 rc ≠ 0 | Referencia, hash o commit posterior distinto | Parar y revisar. No se aceptan herramientas sin revisar | Claude |
| A2 rc ≠ 0 | Procesos del ensayo presentes o lectura fallida. El cribado es conservador: un texto puede detener, nunca aprobar | Parar y diagnosticar en solo lectura | Claude |
| A3 rc ≠ 0 | Paquete distinto | Parar. No se edita el paquete | Claude; Mark decide |
| A5 rc 1 o 3 | Franja cambiada o no demostrable | Parar | Claude |
| A6 rc 4 | Bloque con error; requisitos sin verificar | Parar. Sin verificar no es cumplido | Claude |
| A6 rc 5 | Algún requisito NO_CUMPLE o NO_EVALUABLE, incluido P5b | Parar y documentar | Claude |
| A7 rc ≠ 0 | El paquete cambió durante P0 | Parar | Claude |
| Puerta G sin orden de Mark | Falta autorización | No se pasa de la fase A. No se espera por iniciativa propia | Mark |
| B2 rc 3 o B3 NO_CUMPLE o ERROR | Muestreadores incompletos o tarde. No hay línea base válida para S14 | **[DETIENE]** `sensor1_muestreadores.sh parar "$X/sensor1"`, confirmar `PARADA_CONFIRMADA`. No se lanza C1. Se publica «no ejecutado» | Claude |
| B4 o B5 sin muestras antes de T_g | Sin guardia | **[DETIENE]** `kill -TERM $(cat "$X/bastion.pid")`, parar los muestreadores. No se lanza C1 | Claude |
| C1 rc 3, 4 o 5 | Arranque fallido, parcial o desconocido | `parar` de inmediato. Sin ventana evaluable. Los muestreadores siguen hasta su FIN para conservar la medida. Se publica «no ejecutado por fallo de arranque» | Claude |
| Guardia o condición de §3.7 | Parada anticipada | Automática por `muestreo_bastion.sh`. Los muestreadores siguen hasta su FIN. La ventana no se mueve. El resultado será «no estable» o «no demostrable» | automático |
| Mark pide parar | Parada manual | **[DETIENE]** `$CLI 'bash -s parar' < $E/generadores.sh`: rc 0 confirmada; rc 3 → `comprobar-parado`; rc 4 o 5 → repetir | Claude |
| `PARADA-NO-CONFIRMADA` o rc 4 | Generadores quizá vivos | Intervención inmediata con `sudo systemctl stop 'cyberflow-lab-*'` en clientes, o la consola | **Mark**: hacen falta su contraseña de sudo o la consola física |
| `construir_entrada` rc 2 | Sin medida EVE del periodo | No hay veredicto. Se publica la traza y el motivo | Claude |
| Veredicto rc 1 | «carga insuficiente», «no estable» o «no demostrable» | Se publica tal cual. **No se repite** sin orden nueva y versión nueva del protocolo | Claude; Mark decide |
| Veredicto rc 2 | Entrada inválida | Se publica. No se corrige ningún dato para que pase | Claude |
| Veredicto rc 0 | «estable con carga suficiente», `habilita_condicion_3` true | Se publica con su clase. **No inicia la 4B** | Mark decide |

Un `parar` o un `comprobar-parado` sin confirmar nunca se registra como «parado». Ninguna decisión de esta tabla cambia un
umbral.

## 6. Mediciones que siguen pendientes

Nada de esto está demostrado. Las lecturas en reposo (retención 1158 s, cobertura, P0) no prueban nada bajo carga y no se
usarán como evidencia de estas filas.

| Medición | Cómo se registra | Decide | Si falta evidencia |
|---|---|---|---|
| **Retención del anillo bajo carga** | No hay medida directa de la retención. `obs_pcap.py` lee cada PCAP cerrado cada 30 s (`obs_pcap/pcap.jsonl`, `obs_pcap.log`), y `salud_captura` registra el anillo en `muestras.jsonl`. `derivar_pcap.py` da la cadena, los saltos y la lectura completa | S2, S3 y clase | Lectura incompleta → S2/S3 `null` → «no demostrable». Salto > 7 s demostrado → S3 `false` → «no estable». La suposición de 900 s de `derivar_pcap` no se ajusta después |
| **Coste de los muestreadores** | **Sin métrica por proceso** en la instrumentación prevista. Su efecto está incluido en CPU, PSI, disco y memoria de `s14.jsonl` y `fino.jsonl`. La línea base también corre con ellos, así que el coste no se puede aislar. La cobertura de `s14.jsonl` muestra si el muestreo a 1 s siguió el ritmo | Indirecto, por S14. No es criterio propio | Se publica como «no medido por separado». No se estima ni se deduce de S14 |
| **S14** | `muestreo_s14.py` a 1 s; `evaluar_s14.py` 2026-11-06.2 con ventana [1794194100, 1794197700) y base [1794192900, 1794193200) → `post/s14.json` | S14: `true`, `false` o `null` | `null` (cobertura < 99 %, hueco > 4 s, tramo dudoso, base dudosa) → «no demostrable». Nunca `true` por interpolación. `false` → «no estable» |
| **Continuidad durante el ensayo** | Captura: `pcap.jsonl` (S2, S3). Suricata: `stats` de EVE (K5, S4, S12, S13). Servicios: `muestras.txt` del bastión cada 30 s (S1, S6, S8–S10; muestra a ≤ 60 s de cada borde, ningún hueco > 60 s). Cadena: `obs_p4_post.sh` (S7) | K5, S1–S13, clase | Fuente ausente, ilegible o de otro periodo → `null` en sus criterios → «no demostrable». Sin cobertura del bastión, S1, S6, S8, S9 y S10 quedan todos en `null` |
| **Carga real** | `comparar_suricata.py` (K1–K3), `evaluar_ecarga.py perfiles` (K4a; K4b informativo) | K1–K5 | Falla un K → «carga insuficiente». Falta un K → «no demostrable». 02-nov y reposo no cuentan |
| **Arranque y parada reales de los generadores** | `arranque.txt`, `parada.jsonl`, `parado.txt` | Condición para que exista ventana | Solo se han probado con dobles. Si fallan, §5 |

Orden de decisión (protocolo r4 §4.1): falla algún K → «carga insuficiente»; si no, falta algún K o S → «no demostrable»;
si no, falla algún S → «no estable»; si no → «estable». Después, una contradicción o una clase C3/`no_evaluable` limitan
el resultado como dice §4.1. E-carga no evalúa I5 ni admite episodios en la población principal.

## 7. Autorización que falta

Ninguna de estas órdenes está dada. El texto propuesto para Mark:

1. **Fase A:** «Autorizo ejecutar las verificaciones de solo lectura de la fase A y el P0 r3 inmediato en la franja
   publicada, desde las 02:05Z del lun 09-nov (21:05 del dom 08-nov en Perú), y confirmo que el laboratorio está libre».
2. **Ejecución:** «Autorizo ejecutar E-carga v2 según `PROCEDIMIENTO-ECARGA-v2-FINAL.md`, si se supera la puerta G: arrancar
   los muestreadores y el muestreo del bastión a las 02:50Z, arrancar `cyberflow-lab.target` en T_g 1794193200, y pararlo a
   las 04:17Z o por la guardia».
3. **Protocolo:** «Apruebo `PROTOCOLO-CARGA-v2` r4».
4. **Resultados:** «Se publican en `evidencia/14-ecarga-ejecucion/` sea cual sea el resultado».
5. **Disponibilidad:** Mark disponible durante la ventana para la intervención de `PARADA-NO-CONFIRMADA`, que necesita su
   contraseña de sudo o la consola física.

La orden debe darse en el chat de una sesión activa. Nada queda programado ni en espera.

## 8. Hallazgos de esta revisión

| # | Hallazgo | Tratamiento |
|---|---|---|
| 1 | Las secuencias r1 y r2 lanzaban `comprobar` desde el paquete, y la .2 escribe caché en él (causa del `.pyc` archivado en la entrega 18) | Eliminado: `comprobar` solo se ejecuta dentro de P0 r3 |
| 2 | P12 no tenía comprobación escrita | `comprobar_p12*.sh`. Lo que verifica es el texto del protocolo, sin criterio nuevo. Probado en banco con marcas simuladas: 15/15 como 65534, 14 + 1 omitida como root. **Su transporte ssh no se ha probado contra Sensor1**, porque este encargo no incluye conexiones. Un fallo da ERROR, nunca aprobado |
| 3 | P8 dependía de una frase del P0 | `comprobar_p8.sh`: commit, tabla y registro de pushes de GitHub |
| 4 | r1 y r2 lanzaban `muestreo_bastion.sh` junto con los muestreadores | Se lanza tras P12 CUMPLE, para no dejar una parada automática en marcha si P12 falla. Sigue siendo antes de T_g |
| 5 | `sensor1_post.sh` conserva `pgrep -af`, solo para un AVISO | No decide nada y corre desde fichero. No se cambia. El muestreo ya habrá terminado |
| 6 | `clasificar_periodo.py` carga `salud_captura.py` de `herramientas-20261106` sin `-B`: puede dejar caché allí, no en el paquete | No comprobado. No afecta a la medida. E2 compara el paquete después del ensayo |
| 7 | El procedimiento no fija tolerancia para T_g porque el protocolo tampoco lo hace | Si T_g ya pasó al llegar a C1, no se arranca |
| 8 | Coste de los muestreadores sin métrica por proceso | Declarado en §6. No se añade instrumentación nueva en este encargo |
