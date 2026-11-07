# Procedimiento final de E-carga v2 (07-nov)

**Estado: instrucciones consolidadas. E-carga NO se ha ejecutado ni programado.** Este documento no autoriza nada: no
se ha arrancado ningún generador ni muestreador, no se ha modificado ningún servicio, no se ha desplegado ningún paquete
y no se ha activado ninguna restricción. Para redactarlo no se contactó con ningún host.

**Revisión del 07-nov (06:00Z).** Corrige tres fallos de la revisión independiente: C1 podía arrancar con una parada ya
confirmada, el muestreo podía salir sin intentar la parada y S7 podía aprobar sin secuencia del publicador. Solo se ha
validado con dobles y reloj simulado ([`evidencia/21-correccion-guardia-parada-s7/`](../evidencia/21-correccion-guardia-parada-s7/README.md)). **Publicado no significa instalado:** los hosts
siguen con `902991e`, y esta secuencia exige antes el traslado de la fase T, que todavía no está autorizado.

**Qué sustituye.** Esta es la única secuencia de ejecución vigente. Sustituye a las secuencias de
[`PREPARACION-ECARGA-v2.md`](PREPARACION-ECARGA-v2.md) §3 y [`PREPARACION-ECARGA-v2-r2.md`](PREPARACION-ECARGA-v2-r2.md)
§6, y a la lista de órdenes de la r2 §8 y la r3 §8. Esos documentos se conservan sin cambios y siguen vigentes como
definición de:
- la fuente de cada K y S (r1 §4.1 y §4.2);
- la regla de S7, S11 y S15 (r1 §4.3), con la adaptación de la fase D;
- la parada (r2 §7).

Los criterios son los del [protocolo r4](../PROTOCOLO-CARGA-v2.md): aquí no cambia ningún K, S, umbral ni franja. Tampoco
cambian el detector, el modelo IF, las características, α, los heurísticos ni la política de respuesta.

**Revisión del 07-nov (13:52Z).** C1 relee la hora antes de emitir: si T_g ya pasó, rc 2 y cero órdenes. `arrancar_c1.sh`
2026-11-07.2, producto `f24c922`. También se estabilizan las pruebas. Solo con dobles ([`evidencia/23-correccion-c1-tg-estabilidad-banco/`](../evidencia/23-correccion-c1-tg-estabilidad-banco/README.md)). El traslado
pasa a `f24c922`: sigue sin autorizar y los hosts siguen con `902991e`.

## 1. Referencias confirmadas (07-nov, 13:52Z)

Consulta a los remotos sin ningún cambio posterior a las referencias revisadas.

| Qué | Referencia exacta |
|---|---|
| Documentación | `VF-PPI-TESIS-ORQUESTACION`, main, última revisada `0597f0646abe4c0e750dba38ba1e52dd777b6a20`, más el commit que publica esta revisión |
| Producto | rama `recuperacion/etapa4a-pendientes-20261106` en `ea3f3561cac20021cfcefed338600e7c938e93a6`. Último código: `f24c9221dc99b6f716a27d5ce55f9ea0dfa795cc`; después solo cambian pruebas. main del producto sigue en `7b275b8` |
| Paquete en los hosts | `~/cf-e4/paquete-902991e`, SHA256SUMS interno `8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c`; `ecarga/SHA256SUMS` `e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80`. **No se modifica** |
| Herramientas del bastión | `~/cf-e4/ecarga-bastion-f24c922`, carpeta aparte con 8 ficheros de `f24c922`, `SHA256SUMS` `439ccc0f34730af26245ac8b060dbca658e1146fb31fc2e3807b8fb16750466e`, tgz `3cc7aa3fd424fbdb253ada8b8d840d046e83e7e629fac1221a7a2aa02acada9a`. **Todavía no existe en el bastión**: la crea la fase T |
| Protocolo vigente | `PROTOCOLO-CARGA-v2.md` r4, commit `034d57d` |
| Evaluador | `evaluar_ecarga.py` 2026-11-06.4, `53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f` |

### Herramientas vigentes

| Uso | Herramienta | Versión o sha256 | Dónde corre |
|---|---|---|---|
| Referencias e integridad | `evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh` | 2026-11-07.4 | laptop |
| Traslado y su verificación | `evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh` + `instalar_bastion_host.sh` | 2026-11-07.2 | laptop → bastión |
| Procesos del ensayo | `evidencia/19-correccion-p11/laboratorio/previa.sh` + `previa_host.sh` | `4e1dd442…` | laptop → 4 hosts |
| Post-copia | **r3**: `evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh` | host `799af8f1…` | laptop → 3 hosts |
| P0 | **r3**: `evidencia/19-correccion-p11/p0-r3/p0_r3.sh` | 2026-11-06.r3; bloque Sensor1 `5ef3372a…` | laptop → 3 hosts + clientes |
| P8 | `evidencia/20-procedimiento-final/herramientas/comprobar_p8.sh` | 2026-11-07.1 | laptop + GitHub |
| P12 | `evidencia/20-procedimiento-final/herramientas/comprobar_p12.sh` + `comprobar_p12_host.sh` | host `b45e950b…` | laptop → Sensor1 |
| Instantáneas | `evidencia/18-cache-archivada-postcopia-p0/instantaneas/tomar.sh` | la publicada | laptop → 3 hosts |
| Muestreadores de Sensor1 | paquete: `sensor1_muestreadores.sh` | 2026-11-06.2 | Sensor1 |
| Muestreo y guardia | `ecarga-bastion-f24c922`: `muestreo_bastion.sh` 2026-11-07.1, `guardia.py` 2026-11-06.2 | ver §1 | bastión |
| Autorización de C1 | `ecarga-bastion-f24c922`: `arrancar_c1.sh` 2026-11-07.2, `puerta_c1.py` 2026-11-07.1, `generadores.sh` 2026-11-06.2 (mismos bytes que el paquete) | ver §1 | bastión → clientes |
| S7 | `ecarga-bastion-f24c922`: `s7_post.sh` y `derivar_s7.py` 2026-11-07.1 | ver §1 | bastión |
| Análisis | paquete: `sensor1_post.sh`, `derivar_bastion.py` (.2), `evaluar_s14.py` (.2). `ecarga-bastion-f24c922`: `construir_entrada.py` 2026-11-07.1 | r3 §6 | hosts |

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
| `--manual S14` y entrada manual de S7 | `construir_entrada.py` los rechaza |
| `muestreo_bastion.sh` y `construir_entrada.py` del paquete | Tienen los defectos corregidos. Siguen en el paquete sin editar, porque P0 y post-copia miden esos bytes |
| Bloque manual de C1 con `tail` y `$CLI 'bash -s arrancar'` | Arrancaba con la parada confirmada. Solo `arrancar_c1.sh` emite la orden |
| `obs_p4_post.sh` para fijar S7 | Su `all()` da True con listas vacías. Se conserva como cruce informativo; su rc no decide nada |
| Carpeta `evidencia/12-…` o `13-ecarga-ejecucion/` | Los resultados van a `evidencia/14-ecarga-ejecucion/` |

**Texto antiguo que este procedimiento aclara.** El protocolo r4 §3.3 y §3.5, puntos 9 y 10, siguen citando `ae2900e` y
`a12deae`. El punto 13 los resuelve: el paquete es `902991e`. El evaluador tiene el mismo sha en ese paquete, y los
verificadores son los mismos bytes de `a1cea5e`. El protocolo no se ha editado.

**Diferencia con la letra del protocolo.** El protocolo r4 §3.5 sitúa las herramientas en `902991e`. Con esta revisión,
seis ficheros de análisis y operación del bastión salen de `f24c922`. No cambia ningún K, S, umbral, franja ni el evaluador.
S7 sí se vuelve más estricto en la práctica: lo que antes aprobaba sin datos ahora queda `null`. Mark debe aceptarlo al
aprobar el protocolo (§7, orden 3).

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
| Traslado al bastión, terminado antes de | — | 02:05:00 | dom 21:05:00 |
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

**Viabilidad a 07-nov, 06:00Z: la franja sigue siendo viable y no se ha movido.** Faltan unas 45 h para el P0. Depende de
cuatro cosas que hoy no están aseguradas:
- la orden de traslado de Mark, ejecutada y verificada antes de las 02:05Z del 09-nov;
- la orden de ejecución de Mark;
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
B=~/cf-e4/ecarga-bastion-f24c922
CLI="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20"
```

`C` es la ruta de la copia publicada que imprime el paso A1 en la línea `COPIA`.

### Fase T: traslado aditivo al bastión (antes de la fase A)

Necesaria porque `paquete-902991e` conserva los guiones con los defectos. Solo con la orden de traslado de §7. Crea una
carpeta nueva y no toca el paquete, ningún servicio ni los otros hosts. No hay reinicios.

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| T1 | [LECTURA] | laptop, `00_referencias.sh` y `trasladar_bastion.sh preparar` | rc 0 y 0 `FALLO`; tgz `3cc7aa3f…` construido con `git show f24c922` | `$EJ/T1-referencias.txt`, `$EJ/T1-preparar.txt` |
| T2 | [ESCRITURA] | laptop → bastión, `trasladar_bastion.sh copiar` | rc 0, `ESTADO_FINAL=VERIFICADO` | `$EJ/T2-copiar.txt` |
| T3 | [LECTURA] | bastión, `trasladar_bastion.sh verificar` | rc 0, `ESTADO_FINAL=VERIFICADO`: lista exacta, `SHA256SUMS` `439ccc0f…`, `generadores.sh` y `guardia.py` iguales que en el paquete, `flock` presente | `$EJ/T3-verificar.txt` |

`[LAPTOP Git Bash] → lo ejecuto yo` (solo con la orden de traslado)
```bash
mkdir "$EJ" || exit 2; cd "$HOME" || exit 2
bash "$R/evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh" "$W-traslado" 2>&1 | tee "$EJ/T1-referencias.txt"; echo "rc=${PIPESTATUS[0]}"
CT=$(sed -n 's/^COPIA //p' "$EJ/T1-referencias.txt")
bash "$CT/evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh" preparar "$W-tgz" 2>&1 | tee "$EJ/T1-preparar.txt"; echo "rc=${PIPESTATUS[0]}"
bash "$CT/evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh" copiar "$W-tgz" 2>&1 | tee "$EJ/T2-copiar.txt"; echo "rc=${PIPESTATUS[0]}"
bash "$CT/evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh" verificar 2>&1 | tee "$EJ/T3-verificar.txt"; echo "rc=${PIPESTATUS[0]}"
```

Si T2 o T3 no dan rc 0, no se pasa a la fase A. Una carpeta a medias no existe: el guion verifica en un temporal antes de
renombrar. Esta parte **no se ha probado contra el bastión**: solo en un contenedor sin red y sin transporte.

### Fase A: verificación, solo lectura (02:05–02:45Z)

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| A0 | [LECTURA] | laptop | `date +%s` < 1794191400; Mark confirma que el laboratorio está libre | `$EJ/A0.txt` |
| A1 | [LECTURA] | laptop, `00_referencias.sh` 2026-11-07.4 | rc 0 | `$EJ/A1-referencias.txt` |
| A2 | [LECTURA] | 4 hosts, `previa.sh`, `4e1dd442…` | rc 0, 4 × `SIN_PROCESOS_DEL_ENSAYO` | `$EJ/A2-previa/` |
| A3 | [LECTURA] | 3 hosts, post-copia r3 | rc 0, `CONFORME 3/3` | `$EJ/A3-postcopia-r3/` |
| A3b | [LECTURA] | bastión, `trasladar_bastion.sh verificar` | rc 0, `ESTADO_FINAL=VERIFICADO` | `$EJ/A3b-verificar.txt` |
| A4 | [LECTURA] | 3 hosts, `tomar.sh` | rc 0 | `$C/…/instantaneas/antes-p0-inmediato/` |
| A5 | [LECTURA] | laptop y GitHub, `comprobar_p8.sh` | rc 0, `REQ P8 CUMPLE` | `$EJ/A5-p8/` |
| A6 | [LECTURA] | 4 hosts, P0 r3 `inmediato` | rc 0, `P0 INMEDIATO CONFORME`, 9/9, todas las anticipables CUMPLE y P5b CUMPLE | `$EJ/A6-p0-r3-inmediato/` y `.rc-driver` |
| A7 | [LECTURA] | 3 hosts, `tomar.sh` | `comparar` rc 0, 3 × IDENTICAS | `$EJ/A7-comparacion-paquete.txt` |
| A8 | [LECTURA] | laptop | carpeta `X` libre en bastión y Sensor1 | `$EJ/A8.txt` |

`[LAPTOP Git Bash] → lo ejecuto yo` (solo si Mark autoriza la fase A)
```bash
[ -d "$EJ" ] || exit 2; cd "$HOME" || exit 2
{ date -u +%FT%TZ; date +%s; [ "$(date +%s)" -lt 1794191400 ] && echo "ANTES DE P0: viable"; } | tee "$EJ/A0.txt"
bash "$R/evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh" "$W" 2>&1 | tee "$EJ/A1-referencias.txt"; echo "rc=${PIPESTATUS[0]}"
C=$(sed -n 's/^COPIA //p' "$EJ/A1-referencias.txt")
cmp "$R/evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh" "$C/evidencia/23-correccion-c1-tg-estabilidad-banco/herramientas/00_referencias.sh"
bash "$C/evidencia/19-correccion-p11/laboratorio/previa.sh" "$EJ/A2-previa"; echo "rc=$?"
bash "$C/evidencia/18-cache-archivada-postcopia-p0/comprobador-r3/comprobar_post_copia_r3.sh" "$EJ/A3-postcopia-r3"; echo "rc=$?"
bash "$C/evidencia/23-correccion-c1-tg-estabilidad-banco/traslado/trasladar_bastion.sh" verificar 2>&1 | tee "$EJ/A3b-verificar.txt"; echo "rc=${PIPESTATUS[0]}"
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
- T3, A1, A2, A3, A3b, A5, A6 y A7 con su código esperado;
- A8 `LIBRE` en los dos hosts;
- la orden de ejecución de §7 está dada en el chat;
- la hora es anterior a las 02:50Z, con margen para terminar B2 antes de las 02:55:00Z.

### Fase B: muestreadores y P12, solo con la orden de ejecución (02:50–02:58Z)

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| B1 | [ESCRITURA] | bastión | `mkdir` rc 0 | `$X`, `$X/manual` |
| B2 | **[ARRANCA]** | Sensor1, `sensor1_muestreadores.sh` 2026-11-06.2, `arrancar` | rc 0, `ARRANQUE_CONFIRMADO` | `arrancar-muestreadores.txt` |
| B3 | [LECTURA] | Sensor1, `comprobar_p12.sh` | rc 0, `REQ P12 CUMPLE` | `$EJ/B3-p12/` |
| B4 | **[ARRANCA]** | bastión, `$B/muestreo_bastion.sh` 2026-11-07.1, `real` | proceso vivo y PID guardado | `$X/bastion.pid`, `$X/bastion.out` |
| B5 | [LECTURA] | bastión y Sensor1 | muestras presentes y 4 `vivo` antes de T_g. Es una vigilancia: quien decide es la puerta de C1 | `$X/manual/B5.txt` |

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
setsid nohup bash $B/muestreo_bastion.sh "$X/bastion" 1794197880 1794197820 real > "$X/bastion.out" 2>&1 < /dev/null &
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
| C1 | **[ARRANCA]** | bastión → clientes, `$B/arrancar_c1.sh` 2026-11-07.2 | rc 0, `RESULTADO-C1` = `ARRANCADO`, `ARRANQUE_CONFIRMADO`: seis PID estables 5 s | `$X/manual/c1-puerta.jsonl`, `arranque.rc`, `arranque.txt`, `RESULTADO-C1` |
| C2 | [LECTURA] | calentamiento, 03:00–03:15Z. No cuenta | sin parada de guardia | lecturas de vigilancia |
| C3 | [LECTURA] | ventana fija, 03:15–04:15Z. No se corta, no se mueve y no se prolonga | sin parada de guardia | `muestras.txt`, `guardia.jsonl`, `s14.jsonl` |
| C4 | **[DETIENE]** automático | 04:16Z los muestreadores terminan solos. 04:17Z `muestreo_bastion.sh` para los generadores | `RESULTADO-PARADA` = `confirmada`, rc 0, `comprobacion_final_rc` 0 | `RESULTADO-PARADA`, `parada.jsonl`, `eventos.log` |
| C5 | [LECTURA] | bastión → clientes, `comprobar-parado` | rc 0, `PARADO_CONFIRMADO`; sin `PARADA-NO-CONFIRMADA` | `$X/manual/parado.txt` |

`[BASTIÓN gadmin] → lo ejecuto yo`. **ARRANCA los generadores**, en primer plano y solo con la orden. Se lanza antes de T_g.
El guion espera a T_g y decide justo antes de emitir la orden, dentro del cerrojo `ordenes.lock`. Exige:
- muestreador vivo, de esta versión y en modo real;
- ninguna solicitud de parada, ni previa ni en el historial de la guardia;
- última lectura de la guardia válida, completa y de hace ≤ 60 s.

Si algo falla, no emite la orden y deja el motivo. Si T_g ya pasó, también durante la espera o al evaluar la puerta, **no se arranca** (rc 2, cero órdenes): el protocolo no fija tolerancia y no se
inventa una. Al volver de `arrancar`, relee la solicitud y el muestreador, y para si hace falta.
```bash
bash $B/arrancar_c1.sh "$X" 1794193200; echo "arrancar_c1 rc=$?"; cat "$X/manual/RESULTADO-C1"
```

**Vigilancia durante C2 y C3.** Solo se lee `tail` de `$X/bastion/eventos.log`, `guardia.jsonl` y `parada.jsonl`, y
`sensor1_muestreadores.sh estado`. Si `RESULTADO-PARADA` no existe, el proceso sigue en marcha o murió: nunca significa parada hecha.

`[BASTIÓN gadmin] → lo ejecuto yo`. Solo lectura, después de las 04:18Z.
```bash
{ $CLI 'bash -s comprobar-parado' < $B/generadores.sh; echo "rc=$?"; cat "$X/bastion/RESULTADO-PARADA"; tail -3 "$X/bastion/parada.jsonl"; tail -2 "$X/bastion.out"
  ls "$X/bastion/PARADA-NO-CONFIRMADA" "$X/bastion/C1-PARADA-NO-CONFIRMADA" 2>/dev/null && echo "INTERVENCIÓN NECESARIA"; } 2>&1 | tee "$X/manual/parado.txt"
```

### Fase D: análisis (desde las 04:30Z; las lecturas posteriores, hasta las 05:00Z)

Se ejecuta **sea cual sea** lo ocurrido en la ventana, salvo que no llegara a haber ventana.

| Paso | Clase | Host y versión | Código esperado | Evidencia |
|---|---|---|---|---|
| D1 | [ESCRITURA] | Sensor1, `sensor1_post.sh` 2026-11-06.2 | rc de cada paso en `post/rc.txt` | `$X/sensor1/post/` con `SHA256SUMS` |
| D2 | [LECTURA] | P0 r3 `anticipado` como lectura posterior | su rc se conserva y no decide nada por sí solo | `$EJ/D2-lecturas-posteriores/` |
| D3 | [ESCRITURA] | laptop → bastión, S11 y S15 | ficheros escritos | `$X/manual/s11-*`, `s15-*` |
| D4 | [ESCRITURA] | bastión, `$B/s7_post.sh` 2026-11-07.1 | rc 0 y `s7.json` escrito, con el valor que salga. `obs_p4_post.sh` derivado solo como cruce informativo | `$X/manual/s7/`, `$X/manual/s7-obs_p4_post.txt` |
| D5 | [ESCRITURA] | bastión, `derivar_bastion`, `$B/construir_entrada.py` 2026-11-07.1, `evaluar_ecarga veredicto` | `construir_entrada` rc 0; veredicto rc 0, 1 o 2 | `entrada-veredicto.json`, `trazabilidad.json`, `veredicto.json`, `veredicto.rc` |
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

`[BASTIÓN gadmin] → lo ejecuto yo`. **D4 y D5**. S7 sale de `s7.json` sin intervención manual. El `<v>` de S11 y S15 se fija
leyendo cada fichero, nunca antes, con la regla de §4.4.
```bash
scp -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/arrancar-muestreadores.txt "$X/manual/"
scp -r -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 "$X/post-sensor1"
(cd "$X/post-sensor1/post" && sha256sum -c --strict --quiet SHA256SUMS); echo "post sellado rc=$?"
[ "$(sha256sum < "$X/manual/obs_p4_post.sh" | cut -c1-64)" = 25d8d3697087d9c7c035986ec42d2f4d15e1fc9a6bf5c0e083d55a2a34a6db62 ] || exit 2
sed -E "s#^O=.*#O=$X/bastion#" "$X/manual/obs_p4_post.sh" > "$X/manual/obs_p4_post.derivado.sh"; sha256sum "$X/manual/"obs_p4_post*.sh | tee "$X/manual/s7-hashes.txt"
bash $B/s7_post.sh "$X/bastion" "$X/manual/s7" 1794194100 1794197700; echo "s7_post rc=$?"
bash "$X/manual/obs_p4_post.derivado.sh" 1794194100 1794197700 > "$X/manual/s7-obs_p4_post.txt" 2>&1; echo "cruce informativo rc=$?"
python3 -I $E/derivar_bastion.py "$X/bastion/muestras.txt" 1794194100 1794197700 > "$X/bastion_s.json"
python3 -I $B/construir_entrada.py --desde 1794194100 --hasta 1794197700 \
  --clasificacion "$X/post-sensor1/post/clasificacion/clasificacion.json" --comparar "$X/post-sensor1/post/comparar.json" \
  --perfiles "$X/post-sensor1/post/perfiles.json" --perfiles-rc "$(cat "$X/post-sensor1/post/perfiles.rc")" \
  --bastion "$X/bastion_s.json" --pcap "$X/post-sensor1/post/pcap_s.json" --s14 "$X/post-sensor1/post/s14.json" \
  --s7 "$X/manual/s7/s7.json" --manual S11=<v>:"$X/manual/s11-comparacion.txt" \
  --manual S15=<v>:"$X/manual/s15-verificadores-despues.txt" \
  --salida-entrada "$X/entrada-veredicto.json" --salida-traza "$X/trazabilidad.json"; echo "construir rc=$?"
python3 -I $P/deploy/etapa4/sensor1/evaluar_ecarga.py veredicto --entrada "$X/entrada-veredicto.json" > "$X/veredicto.json"; echo $? > "$X/veredicto.rc"
(cd "$X" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS)
```

### 4.4 Regla de S7, S11 y S15 (sin cambios de criterio)

| S | `true` | `false` | `null` |
|---|---|---|---|
| **S7**, por `derivar_s7.py` | hay entregas, todas aceptadas; al menos dos aceptadas en orden creciente; al menos dos lecturas `feed_seq` sin retroceso, sin ninguna fallida y con cobertura ≤ 60 s | incumplimiento **observado**: entregada sin aceptar, desorden o retroceso. Se conserva aunque falte otra evidencia | sin incumplimiento observado y sin evidencia suficiente: ninguna entrega, lista vacía, una sola lectura, lectura fallida, traza ilegible o falta `s7.json` |
| **S11** | `diff` vacío (rc 0) y las dos líneas `ec78ca5 SHA256SUMS OK` | algún hash difiere | falta alguno de los dos ficheros |
| **S15** | `P1.bastion`, `P1.sensor1` y `P1.srvdmz` en CUMPLE | alguno en NO_CUMPLE | alguno en ERROR o SIN_VERIFICAR |

**Única adaptación de método.** S11 «antes» y «después» salen de `precheck.sh` ejecutado por el bloque de P0, con su sha
`b3127edd…` comprobado, en vez de copiarlo a `$X/manual`. Es el mismo guion y la misma regla, y no deja ficheros nuevos en
los hosts antes de la orden.

**Adaptación de S7.** El valor ya no lo escribe nadie a mano: va de `s7.json` a `entrada-veredicto.json` tal cual, con su motivo
en `trazabilidad.json`. Los tres cumplimientos de r1 §4.3 no cambian. Lo que cambia es que `true` exige datos: tres casos que
antes aprobaban por una lista vacía o de un elemento ahora dan `null`. También dan `null` una sola aceptada, una lectura fallida
y la falta de cobertura. Un incumplimiento observado prevalece sobre `null`, incluso si no hubo entregas.

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
| T2 o T3 rc ≠ 0, o A3b rc ≠ 0 | Herramientas del bastión ausentes o distintas | Parar. No se pasa a la fase A ni a la puerta G. Nunca se lanza el `muestreo_bastion.sh` del paquete en su lugar | Claude; Mark decide |
| A3 rc ≠ 0 | Paquete distinto | Parar. No se edita el paquete | Claude; Mark decide |
| A5 rc 1 o 3 | Franja cambiada o no demostrable | Parar | Claude |
| A6 rc 4 | Bloque con error; requisitos sin verificar | Parar. Sin verificar no es cumplido | Claude |
| A6 rc 5 | Algún requisito NO_CUMPLE o NO_EVALUABLE, incluido P5b | Parar y documentar | Claude |
| A7 rc ≠ 0 | El paquete cambió durante P0 | Parar | Claude |
| Puerta G sin orden de Mark | Falta autorización | No se pasa de la fase A. No se espera por iniciativa propia | Mark |
| B2 rc 3 o B3 NO_CUMPLE o ERROR | Muestreadores incompletos o tarde. No hay línea base válida para S14 | **[DETIENE]** `sensor1_muestreadores.sh parar "$X/sensor1"`, confirmar `PARADA_CONFIRMADA`. No se lanza C1. Se publica «no ejecutado» | Claude |
| B4 o B5 sin muestras antes de T_g | Sin guardia | **[DETIENE]** `kill -TERM $(cat "$X/bastion.pid")`, parar los muestreadores. No se lanza C1 | Claude |
| C1 rc 2 | **Ninguna orden emitida.** Parada previa, guardia sin lectura válida o reciente, muestreador caído o T_g ya pasado. Motivo en `RESULTADO-C1` y `c1-puerta.jsonl` | No se arranca, no se repite y no se fuerza. Los muestreadores siguen hasta su FIN. Se publica «no ejecutado» con el motivo | Claude |
| C1 rc 3 | Arranque fallido, parcial o desconocido, o parada pedida durante el arranque; parada ya confirmada | Sin ventana evaluable. El muestreador sigue vigilando hasta FIN. Se publica «no ejecutado por fallo de arranque» | automático |
| C1 rc 4 | Parada del arranque NO confirmada: `C1-PARADA-NO-CONFIRMADA` | Igual que `PARADA-NO-CONFIRMADA` | **Mark** |
| Guardia o condición de §3.7 | Parada anticipada | Automática por `muestreo_bastion.sh`. Los muestreadores siguen hasta su FIN. La ventana no se mueve. El resultado será «no estable» o «no demostrable» | automático |
| Mark pide parar | Parada manual | **[DETIENE]** `$CLI 'bash -s parar' < $E/generadores.sh`: rc 0 confirmada; rc 3 → `comprobar-parado`; rc 4 o 5 → repetir | Claude |
| `RESULTADO-PARADA` con `intervencion_necesaria` true, `PARADA-NO-CONFIRMADA`, `C1-PARADA-NO-CONFIRMADA` o rc 4 | Generadores quizá vivos | Intervención inmediata con `sudo systemctl stop 'cyberflow-lab-*'` en clientes, o la consola | **Mark**: hacen falta su contraseña de sudo o la consola física |
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
| **Continuidad durante el ensayo** | Captura: `pcap.jsonl` (S2, S3). Suricata: `stats` de EVE (K5, S4, S12, S13). Servicios: `muestras.txt` del bastión cada 30 s (S1, S6, S8–S10; muestra a ≤ 60 s de cada borde, ningún hueco > 60 s). Cadena: `s7_post.sh` y `derivar_s7.py` (S7) | K5, S1–S13, clase | Fuente ausente, ilegible o de otro periodo → `null` en sus criterios → «no demostrable». Sin cobertura del bastión, S1, S6, S8, S9 y S10 quedan todos en `null` |
| **Carga real** | `comparar_suricata.py` (K1–K3), `evaluar_ecarga.py perfiles` (K4a; K4b informativo) | K1–K5 | Falla un K → «carga insuficiente». Falta un K → «no demostrable». 02-nov y reposo no cuentan |
| **Arranque y parada reales de los generadores** | `c1-puerta.jsonl`, `arranque.txt`, `RESULTADO-C1`, `parada.jsonl`, `RESULTADO-PARADA`, `parado.txt` | Condición para que exista ventana | Solo se han probado con dobles. Si fallan, §5 |
| **Puerta, cerrojo y traslado en el bastión real** | `flock` y `/proc` del bastión, duración real de una muestra frente al límite de 60 s, transporte de T2 y T3 | Si C1 puede emitirse | Sin observar. Un fallo deniega el arranque o detiene la fase T: nunca aprueba |

Orden de decisión (protocolo r4 §4.1): falla algún K → «carga insuficiente»; si no, falta algún K o S → «no demostrable»;
si no, falla algún S → «no estable»; si no → «estable». Después, una contradicción o una clase C3/`no_evaluable` limitan
el resultado como dice §4.1. E-carga no evalúa I5 ni admite episodios en la población principal.

## 7. Autorización que falta

Ninguna de estas órdenes está dada. El texto propuesto para Mark:

0. **Traslado, antes que nada:** «Autorizo el traslado aditivo de `f24c922` al bastión según la fase T: crear `~/cf-e4/ecarga-bastion-f24c922`, sin tocar `paquete-902991e`, y verificarlo». El P0 inmediato no se autoriza sin esta orden cumplida.
1. **Fase A:** «Autorizo ejecutar las verificaciones de solo lectura de la fase A y el P0 r3 inmediato en la franja
   publicada, desde las 02:05Z del lun 09-nov (21:05 del dom 08-nov en Perú), y confirmo que el laboratorio está libre».
2. **Ejecución:** «Autorizo ejecutar E-carga v2 según `PROCEDIMIENTO-ECARGA-v2-FINAL.md`, si se supera la puerta G: arrancar
   los muestreadores y el muestreo del bastión a las 02:50Z, arrancar `cyberflow-lab.target` en T_g 1794193200, y pararlo a
   las 04:17Z o por la guardia».
3. **Protocolo:** «Apruebo `PROTOCOLO-CARGA-v2` r4, con las herramientas del bastión de `f24c922` y S7 derivado según §4.4».
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
| 7 | El procedimiento no fija tolerancia para T_g porque el protocolo tampoco lo hace | Si T_g ya pasó al llegar a C1 o antes de emitir la orden, no se arranca |
| 8 | Coste de los muestreadores sin métrica por proceso | Declarado en §6. No se añade instrumentación nueva en este encargo |
| 9 | La primera pasada de `00_referencias.sh` (2026-11-07.1) tras publicar dio rc 1 con 4 FALLO falsos: `git.exe` no arranca con el directorio de trabajo en la copia de ruta larga | Corregido en la .2 (`cd "$HOME"` antes de esas consultas). Salida conservada en `evidencia/20-procedimiento-final/banco/referencias-primera-pasada-rc1.txt` |
| 10 | C1 podía arrancar con `parada=confirmada`, y ese estado hacía ignorar nuevas solicitudes | `arrancar_c1.sh`, `puerta_c1.py`, cerrojo, solicitud persistente y reapertura. Con dobles, `evidencia/21-correccion-guardia-parada-s7/` |
| 11 | Un retraso entre la comprobación de PARADA y el final de la espera dejaba `parada=ninguna`, 0 intentos y rc 0 | `cerrar_parada` y `RESULTADO-PARADA`. Reloj simulado, `evidencia/21-correccion-guardia-parada-s7/` |
| 12 | S7 podía registrarse `true` sin secuencia del publicador | `derivar_s7.py`, `s7_post.sh`, `--s7`; entrada manual de S7 rechazada. Con dobles, `evidencia/21-correccion-guardia-parada-s7/` |
| 13 | Una espera real de la franja puede dejar la lectura de la guardia cerca del límite de 60 s si una muestra tarda mucho | Efecto seguro: C1 rc 2. Sin ajustar el límite; se observará en el ensayo |
| 14 | C1 emitía la orden si el reloj superaba T_g durante la espera o al evaluar la puerta | `arrancar_c1.sh` 2026-11-07.2, `f24c922`. Con dobles, `evidencia/23-correccion-c1-tg-estabilidad-banco/` |
| 15 | Pruebas de `27bcd46` intermitentes: T_g con margen casi nulo y parada demasiado cerca de T_g | Solo pruebas, hasta `ea3f356`. `evidencia/23-correccion-c1-tg-estabilidad-banco/` |
