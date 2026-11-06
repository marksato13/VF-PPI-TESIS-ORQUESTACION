# Corrección de las herramientas de P0: propagación de errores (A) y escritura de caché (B) (06-nov, 21:10–22:10Z)

**Alcance.** Se corrigieron y probaron en banco las herramientas, y se hicieron lecturas de estado en el laboratorio.
**E-carga NO ejecutada y NO programada.**

No se hizo nada de lo siguiente:
- arrancar generadores ni muestreadores;
- modificar servicios;
- activar restricciones;
- copiar o instalar un paquete;
- borrar nada en los hosts;
- avanzar a la 4B o la 4C.

Tampoco cambian el detector, IF, las 28 características, α, los heurísticos, la política de respuesta ni los criterios
del ensayo.

**El P0 r2 NO se ha ejecutado contra el laboratorio.** Solo se ha probado en banco.

**Referencias confirmadas al empezar:**
- docs `origin/main` = `1f29d27`;
- producto: rama `recuperacion/etapa4a-pendientes-20261106` = `902991e` y `main` = `7b275b8`.

**Se conservan sin cambios:**
- las herramientas y la evidencia de [`../16-postcopia-p0/`](../16-postcopia-p0/): `p0/p0_anticipado.sh`, los bloques y
  el comprobador r2;
- las del 15 y el paquete sellado `~/cf-e4/paquete-902991e` de los hosts.

## 1. Defectos: causa, corrección y prueba

| | Defecto | Causa comprobada | Corrección | Prueba (banco, sin red) |
|---|---|---|---|---|
| **A** | `p0_anticipado.sh` termina con **rc 0 aunque fallen los 9 ssh** | `remoto()` escribe el rc y el transporte en `resumen.txt`, pero nada los agrega. El rc del proceso es el del último `echo "fin …"`. Además, los bloques no distinguían «no se pudo leer» de «no cumple», y `precheck.sh` (S11) no propaga errores: su rc es el de su última orden, y un `sudo -n` fallido produce el sha de la cadena vacía, que es justo el ruleset esperado de srv-dmz | **P0 r2** ([`p0-r2/`](p0-r2/)), herramienta nueva: el manejador agrega los resultados y los bloques se revisaron (§3). `precheck.sh` viaja **sin cambios** (`b3127edd…`) dentro de un envoltorio que evalúa su salida | 46/46 como 65534 y como root ([`p0-r2/banco/`](p0-r2/banco/)). Con los 9 ssh fallidos, el antiguo da **rc 0** y la r2, **rc 4** (§2) |
| **B** | `sensor1_muestreadores.sh comprobar` **escribe en el paquete** | La consulta de VERSION importa `evaluar_ecarga.py` con `python3 -I -c`. `-I` ignora `PYTHONDONTWRITEBYTECODE` y CPython guarda `deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc` **dentro** del paquete. Ocurrió en Sensor1 el 06-nov a las 21:05:27Z (§4) | Producto **`20dabe2`**: `sensor1_muestreadores.sh` 2026-11-06.3, con `python3 -I -B` en la consulta de VERSION y en `obs_pcap --en-seco`. Además, el P0 r2 nunca ejecuta una versión que pueda escribir (§3.3) | `test_regresion_comprobar_no_escribe_en_el_paquete`: copia **escribible** del paquete, 3 pasadas e inventario y hashes idénticos. Con `902991e` falla (crea `__pycache__/…cpython-313.pyc`) y con `20dabe2` pasa. El control `test_banco_detecta_escritura_de_cache` demuestra que el banco ve una escritura |
| C (observación, **no corregido**) | El comprobador post-copia r2 usa `comm` sin `LC_ALL=C` | En Sensor1 (locale no C) imprime `comm: … not in sorted order`. **No afecta al veredicto**: `inventario OK` exige también los recuentos 480/480, y el fallo de hoy salió de 481 ≠ 480. Puede, eso sí, nombrar mal los ficheros del detalle | Propuesta (no aplicada, fuera de los dos defectos encargados): `LC_ALL=C comm` en las líneas 100–101 de `post_copia_host_r2.sh`, como r3. El inventario de §4 se tomó con `LC_ALL=C` | — |

## 2. Reproducción antes/después: ssh rc 255 en los 9 bloques

Fuente: [`p0-r2/banco/muestras.txt`](p0-r2/banco/muestras.txt) (mismo doble de ssh y misma entrada para las dos versiones).

**Antes** (`../16-postcopia-p0/p0/p0_anticipado.sh`): rc del proceso **0**.

```
00-estado-bastion host=bastion rc=255 transporte=DISTINTO(nada) bloque=estado_host.sh sha=406ce22a2aa9
…  (los 9 con rc=255)
06-sensor1-comprobar host=sensor1 rc=255 transporte=DISTINTO(nada) bloque=sensor1_p0.sh sha=f02479681fd3
fin 2026-11-06T21:48:37Z portatil_epoch 1794001717
```

**Después** (`p0-r2/p0_r2.sh anticipado`): rc del proceso **4**.

```
BLOQUE 00-estado-bastion host=bastion rc=255 estado=ERROR motivo=SSH_FALLIDO rc 255 (ssh: connect to host … timed out (doble)) …
…  (los 9)
BLOQUES 0/9 ejecutados sin errores
PRECONDICIONES anticipables: 1/50 CUMPLE; no cumplidas o sin verificar: P1.bastion=SIN_VERIFICAR …
PRECONDICIONES de momento, documentales y de ejecución: P5b=SIN_VERIFICAR P8=NO_EVALUABLE P12=NO_EVALUABLE
RESULTADO_GLOBAL rc=4 modo=anticipado NO VERIFICADO: 9 bloque(s) con error; las precondiciones no se pueden dar por evaluadas
```

La única anticipable que cumple es P5c, que se calcula en el portátil.

Con **un solo** ssh fallido (el 5.º bloque), el antiguo también da rc 0. La r2 da rc 4 con «BLOQUES 8/9».

## 3. P0 r2

### 3.1 Contrato

**Contrato de cada bloque:**
- imprime `REQ <id> <CUMPLE|NO_CUMPLE|NO_EVALUABLE|ERROR> <detalle>`;
- termina con `FIN_BLOQUE <nombre> rc=<n>` y `exit n`: 0 si hizo todas sus lecturas, 3 si alguna falló;
- «no se pudo leer» es siempre `ERROR`, nunca `NO_CUMPLE` ni «0»;
- las órdenes del bloque que leen stdin llevan `< /dev/null` o su propia entrada, porque el bloque llega por stdin a
  `bash -s`. Las pruebas ejecutan los bloques exactamente así.

Un bloque cuenta como **«ejecutado sin errores»** solo si se cumplen las cinco condiciones:
- ssh rc 0;
- transporte igual: la 1.ª línea es el sha256 de los bytes recibidos y coincide con el local;
- `FIN_BLOQUE` es la última línea y su rc coincide con el de ssh;
- están todos los REQ esperados, una vez cada uno y bien formados;
- ninguno es `ERROR`.

Si falla alguna, se guarda el motivo y sus REQ quedan **`SIN_VERIFICAR`**, aunque el bloque dijera CUMPLE. Los motivos
posibles son:
- `SSH_FALLIDO`;
- `SIN_SALIDA`;
- `TRANSPORTE_DISTINTO`;
- `INCOMPLETO`;
- `INCOHERENTE`;
- `FALTAN_REQ`;
- `REQ_DUPLICADO`;
- `ERROR_EN_BLOQUE`;
- `RC_NO_CERO`;
- `CR_EN_BLOQUE`, cuando el bloque no se envía;
- `ERROR_LECTURA_LOCAL`.

**Por bloque** se conservan `.stdout`, `.stderr`, `.rc` y `.motivo`. Las escrituras de evidencia se comprueban: si
alguna falla, rc 4. Nada pasa por `tee`, y ningún `echo` ni limpieza fija el rc.

### 3.2 Categorías y código global

| Categoría | Puntos (§3.5 r4) | Cómo cuenta |
|---|---|---|
| anticipable | 1, 2, 3, 4, 5a, 5c, 6, 7, 9, 10, 11, 13 y extras `X.*` (sincronización, cadena v2/v1, mecanismo sin escritura, paquete sin cambios…) | Deben estar **todas** en CUMPLE. `NO_EVALUABLE` también impide el rc 0 |
| momento | 5b (`date -u` dentro de la franja 1794191400–1794200400) | En modo `anticipado` se informa aparte. En modo `inmediato` **es obligatorio** CUMPLE |
| documental | 8 | No lo comprueba la herramienta (`NO_EVALUABLE`, aparte) |
| ejecución | 12 (muestreadores antes de T_g − 300 s) | Ocurre después de P0, en la ejecución |

**rc global:**
- **0**: 9/9 bloques sin errores **y** todas las anticipables CUMPLE (y 5b en modo inmediato);
- **2**: uso o precondición local; no se conecta;
- **4**: algún bloque con error o sin verificar. Manda sobre el 5;
- **5**: bloques sin errores, pero alguna precondición NO_CUMPLE o NO_EVALUABLE.

El resumen final separa siempre `BLOQUES k/9 ejecutados sin errores` de `PRECONDICIONES anticipables: n/N CUMPLE` y
termina en una línea `RESULTADO_GLOBAL rc=… modo=… <veredicto>`.

### 3.3 Mecanismo para repetir lecturas sin escribir (explicado y probado; **no usado aún en el laboratorio**)

El bloque `sensor1_r2.sh` **nunca** ejecuta `comprobar` con una versión que pueda escribir caché. Según el sha del
guion que tenga el paquete:

| sha del guion | Qué hace el bloque |
|---|---|
| `4ed43856…`, la .3 publicada | Lo ejecuta tal cual |
| `25fb732d…`, la .2 de `902991e` | Deriva **en memoria** la .3 con las mismas tres sustituciones del commit `20dabe2` (VERSION y `-B` en las líneas 31 y 66). Exige que el texto derivado tenga **exactamente** el sha `4ed43856…` de la .3 publicada y lo ejecuta con `bash -c "$texto" "$ruta_del_guion_del_paquete" comprobar …`. Así `$0` es la ruta real y `E`/`P` se resuelven igual |
| cualquier otro | **No ejecuta** `comprobar` (`ERROR`) |

En el caso derivado no se escribe ni se despliega ningún fichero, y el paquete sellado no se modifica. Además, el
bloque compara el inventario completo del paquete antes y después (tipo, modo, tamaño, mtime y ruta) en
`X.paquete_sin_cambios`.

**Pruebas del mecanismo:**
- `test_sensor1_mecanismo_sin_escritura`: 3 pasadas por variante, la derivada y la publicada; inventario idéntico, sin
  `__pycache__` y «VERSION 2026-11-06.4» OK;
- `test_control_la_2_ejecutada_tal_cual_escribe_cache`: la .2 ejecutada directamente sobre el mismo paquete escribible
  sí escribe;
- `test_sensor1_guion_desconocido_no_se_ejecuta`;
- `test_versiones_de_referencia`.

### 3.4 Casos del banco (46)

| Caso pedido | Prueba | Resultado r2 |
|---|---|---|
| Todos los bloques correctos | `test_todos_correctos_anticipado`, `test_inmediato_conforme` | rc 0; 9 llamadas; stdout, stderr, rc y motivo por bloque |
| Un bloque fallido y el resto correcto | `test_un_bloque_falla_y_el_resto_bien` | rc 4, «BLOQUES 8/9», P1.sensor1 SIN_VERIFICAR, stderr del ssh guardado |
| 9 fallos de ssh | `test_regresion_nueve_ssh_fallidos` | Antiguo rc 0; r2 rc 4, 0/9 y las 9 llamadas hechas |
| Transporte distinto | `test_transporte_distinto` | rc 4; sus REQ quedan SIN_VERIFICAR aunque digan CUMPLE |
| Resultado ausente o incompleto | `test_resultado_ausente_incompleto_o_incoherente` (7 variantes) | rc 4: SIN_SALIDA, INCOMPLETO, FALTAN_REQ, REQ_DUPLICADO, mal formada, INCOHERENTE y RC_NO_CERO |
| Error de lectura | `test_error_de_lectura_en_el_host`, `test_bloque_con_cr_no_se_envia` y bloques por dentro (`estado`, `clientes`, `sensor1`, `verificador`, `precheck`) | `ERROR` y bloque rc 3, que da global rc 4. Un bloque con CR no se envía (8 llamadas) |
| Precondición incumplida | `test_precondicion_incumplida`, `test_precheck_hash_distinto_es_no_cumple` | rc 5 con «BLOQUES 9/9»: ejecutar sin errores no equivale a conforme |
| Error seguido de operaciones correctas | `test_error_seguido_de_operaciones_correctas`, `test_error_manda_sobre_no_cumple` | rc 4; las 9 llamadas se hacen y la última línea es `RESULTADO_GLOBAL rc=4` |
| Condiciones aún no evaluables | `test_inmediato_fuera_de_franja_no_es_conforme`, `test_anticipable_no_evaluable_no_es_conforme`, `test_sensor1_franja` | Anticipado: 5b aparte (rc 0). Inmediato: 5b NO_EVALUABLE da rc 5. Anticipable NO_EVALUABLE da rc 5 |
| `sudo -n` fallido en `precheck.sh` | `test_regresion_precheck_sudo_fallido_no_pasa_por_ruleset_vacio` | `X.precheck_stderr` ERROR; sin el envoltorio, esa salida pasaría por conforme |
| Salida real del 06-nov | `test_precheck_salida_real_del_06nov_cumple` | Las 19 REQ del envoltorio CUMPLE con las secciones reales del P0 anticipado |
| Lo que hay hoy en Sensor1 | `test_sensor1_pyc_anadido_es_no_cumple_no_error` | P13.inventario NO_CUMPLE (nombra el `.pyc`), sin ERROR y sin tocar el fichero |

## 4. Inventario actual de `~/cf-e4/paquete-902991e` en Sensor1 (lecturas, 21:24Z)

Fuentes, en [`lecturas/`](lecturas/):
- `post-copia-r2-20261106T212402Z/`: comprobador r2 sin cambios;
- `inventario-sensor1.stdout`: [`inventario_detalle.sh`](lecturas/inventario_detalle.sh), solo `find`, `stat`, `od` y
  `sha256sum`, con `LC_ALL=C`.

**Comprobador post-copia r2:**

| Host | Resultado |
|---|---|
| bastión | CONFORME 12/12 |
| srv-dmz | CONFORME 12/12 |
| **Sensor1** | **NO_CONFORME 11/12**: solo falla `inventario` (480 en el manifiesto, 481 presentes) |
| global | **rc 4** |

Hashes, `SHA256SUMS -c`, marca, evaluador y versiones: OK en los tres hosts.

**Fichero añadido** (el único; ausentes: ninguno):

| Campo | Valor |
|---|---|
| Ruta | `deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc` (y su directorio `__pycache__`) |
| Tamaño, modo, dueño | 27 980 B, `-rw-r--r--`, m4rk |
| Nacido = modificado | **2026-11-06 21:05:27.803101848Z** |
| sha256 | `754ec72930cb1b187b387f0360ae65c25763ec0cccf4abe7dd5f8aa19be701d1` |
| Cabecera | magic 3531 (CPython 3.12), flags 0, mtime del fuente 1793985517, tamaño del fuente 21 362 = mtime y tamaño de `evaluar_ecarga.py` del paquete (`53e9f7bd…`) |

**Procedencia: lo generó la comprobación anticipada de P0 de este mismo día.** El bloque `06-sensor1-comprobar`
empezó a las 21:05:27Z (`../16-postcopia-p0/p0-anticipado-20261106T210504Z/06-sensor1-comprobar.stdout`). La línea 31
de `sensor1_muestreadores.sh` usa el `python3` del sistema, 3.12.3, que es `cpython-312`. La comprobación post-copia de
las 21:02Z había dado 480/480. **No es histórico.**

**Históricos, ajenos a `902991e`, solo listados:**
- `paquete-ae2900e/…/__pycache__/evaluar_ecarga.cpython-312.pyc` (08:05Z);
- `paquete-a12deae/…` (16:35Z, ya documentado en el 15).

El de `ae2900e` no afecta al punto 9, porque `sha256sum -c` solo comprueba los ficheros listados.

**Verificador de Sensor1 (otra ruta del P0).** `comprobar_importaciones.sh:29` ejecuta
`$PY motor_decision.py --help` sin `-B`. La lectura [`lecturas/cache_ec78ca5.sh`](lecturas/cache_ec78ca5.sh)
(21:49Z) encuentra **0 `.pyc` y 0 `__pycache__`** en `~/cyberflow-e4/ec78ca5`: esa ruta no ha escrito caché ahí.

## 5. Actuación puntual propuesta (NO ejecutada; este encargo no autoriza borrar)

Para que el paquete sellado `902991e` vuelva a su inventario de 480, la actuación sería retirar **exactamente** el
`.pyc` de §4 y su directorio, solo si el sha coincide y el directorio queda vacío.

`[SENSOR1 m4rk]` → **lo ejecutas tú, o yo con tu autorización expresa** (es un borrado en un host y este encargo no lo
autoriza):

```bash
f=~/cf-e4/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc
[ "$(sha256sum < "$f" | cut -c1-64)" = 754ec72930cb1b187b387f0360ae65c25763ec0cccf4abe7dd5f8aa19be701d1 ] \
  && rm -- "$f" && rmdir -- "$(dirname "$f")" && echo RETIRADO || echo "NO RETIRADO: el sha no coincide o el directorio no está vacío"
```

Después hay que repetir la comprobación post-copia r2; debería volver a CONFORME 3/3. La alternativa es no tocar
nada y sustituir el paquete por el de `20dabe2` (§7, ruta B).

## 6. Regresiones

| Regresión | Resultado | Evidencia |
|---|---|---|
| Banco E-carga del producto (`tests/test_etapa4_ecarga_prep.py`): **arranque, parada, configuración, PCAP, S14**, E2E y la nueva | **87/87** como 65534 y como root | [`regresiones/producto-ecarga-65534.txt`](regresiones/producto-ecarga-65534.txt), [`-root`](regresiones/producto-ecarga-root.txt) |
| La nueva regresión con la versión `902991e` (`ECARGA_DIRS`) | **Falla**, como debe (crea `__pycache__`); el control pasa | [`regresiones/producto-ecarga-version-902991e.txt`](regresiones/producto-ecarga-version-902991e.txt) |
| Suite completa del producto | **65534: 1009 passed / 53 skipped / 0 failed.** **root: 1049 passed / 9 skipped / 4 failed.** Los 4 fallos son pruebas de `nft` real de etapa 2 (`netlink: Operation not permitted`): el contenedor se lanzó sin `CAP_NET_ADMIN`. Repetidas con `--cap-add NET_ADMIN` (sin red), sus dos ficheros dan **105/105**. Son ajenos al cambio, que no toca etapa 2 ni nft | [`regresiones/producto-suite-completa-65534.txt`](regresiones/producto-suite-completa-65534.txt), [`-root`](regresiones/producto-suite-completa-root.txt), [`producto-nft-root-netadmin.txt`](regresiones/producto-nft-root-netadmin.txt) |
| Comprobación **post-copia** (banco del comprobador r2, sin cambios) | **27/27** (65534) y **26 + 1 omitida** (root), igual que en el 16 | [`regresiones/postcopia-r2-banco-*.txt`](regresiones/) |
| P0 r2 | **46/46** (65534 y root) | [`p0-r2/banco/`](p0-r2/banco/) |

**Omisiones** (todas de entorno, ninguna por fallo):
- en la suite como 65534:
  - 16 instaladores P4 y 9 + 3 + 1 de etapa 2, que requieren root o nft;
  - 6 de compuerta, porque el repositorio de documentación no está montado;
  - 1 de la GUI, porque no hay node en el contenedor;
- en el banco post-copia como root, 1 (la de permisos: root lee sin permisos);
- **no hay prueba en vivo** de `arrancar` ni `parar` con el systemd real, ni del coste de `muestreo_s14`, ni de la
  retención con carga. Siguen pendientes de medirse durante el ensayo.

## 7. Revisión publicada y uso de la versión corregida (preparado; **se detiene antes de copiar**)

**Producto:** commit **`20dabe2`** en la rama `recuperacion/etapa4a-pendientes-20261106`. No está fusionado en `main`,
que sigue en `7b275b8`. Cambian **4 ficheros**:

| Fichero | Antes (`902991e`) | Después (`20dabe2`) |
|---|---|---|
| `deploy/etapa4/ecarga/sensor1_muestreadores.sh` | 2026-11-06.2 `25fb732d…` | 2026-11-06.3 `4ed43856…` |
| `deploy/etapa4/ecarga/SHA256SUMS` | `e001352c…` | `41d9a397…` |
| `deploy/etapa4/ecarga/README.md` | `0849d1f8…` | `1c95a21b…` (versión y nota) |
| `tests/test_etapa4_ecarga_prep.py` | `dfa035e2…` | `730ef79d…` (2 pruebas nuevas) |

El evaluador (`53e9f7bd…`), `evaluar_s14` 2026-11-06.2, `construir_entrada` 2026-11-06.3, `generadores.sh` y los
verificadores no cambian.

**Paquete del commit**, construido en local con la misma lógica que `paquete_902991e.sh` y sin copiarlo:
- 480 ficheros;
- `SHA256SUMS` interno **`85358f509604bd03b1cfec99d3fc5b6ec17f62ce11db9a12872dccbe5d783e4a`**;
- solo difieren las 4 entradas de la tabla;
- la misma construcción reproduce para `902991e` su `8480f0e0…`.

**Ruta A: sin copiar nada.** Se mantiene `paquete-902991e`:
- El P0 r2 deriva la .3 en memoria (§3.3), así que la comprobación ya no escribe.
- Requisito: retirar el `.pyc` de §5; si no, P13.inventario da NO_CUMPLE y el P0 r2, rc 5.
- `arrancar` de la .2 no escribe caché: ejecuta guiones y solo importan stdlib.
- **No volver a ejecutar `comprobar` de la .2 directamente.**
- El punto 13 del protocolo («el paquete es el de `902991e`») no cambia.

**Ruta B: paquete `20dabe2`.** Pasos mínimos, **ninguno ejecutado**:
1. **Protocolo.** El punto 13 de r4 nombra `902991e` y `e001352c`. Cambiar esa referencia es una revisión (r5) que
   aprueba Mark. No se ha editado.
2. **Herramientas.** Los guiones del traslado r2 y del comprobador post-copia r2 tienen las constantes de `902991e`:
   - `C`, `CFULL` y `ECARGA` en `paquete_902991e.sh`, `reparto_bastion_902991e.sh` y `op_host_902991e.sh`;
   - `C`, `SUMAS` y `ECARGA` en `post_copia_host_r2.sh`.
   Hace falta una r3 parametrizada (`C=20dabe2`, `CFULL=20dabe26ed766920fa2683cfedb03e11e2dd971b`,
   `ECARGA=41d9a397…`, `SUMAS=85358f50…`), probada en su banco antes de usarse. No preparada en este encargo.
3. **Copia,** con la r3 y con la autorización de Mark:
   `[LAPTOP Git Bash] → lo ejecutas tú` (escribe en los tres hosts y necesita orden expresa). Se lanza desde `~`, con la
   ruta absoluta del guion (trampa de los 260 caracteres).
4. **Post-copia** (r3) y **P0 r2**:
   `[LAPTOP Git Bash] → lo ejecuto yo cuando lo autorices` (solo lectura):
   `bash p0_r2.sh anticipado <SALIDA_NUEVA> --paquete 20dabe2 --sumas 85358f509604bd03b1cfec99d3fc5b6ec17f62ce11db9a12872dccbe5d783e4a`

## 8. Corrección en banco, comprobación anticipada y P0 inmediato

| | Qué demuestra | Estado |
|---|---|---|
| **Corrección en banco** | Las herramientas propagan errores (A) y no escriben (B) | **Hecha y publicada**: producto `20dabe2` y [`p0-r2/`](p0-r2/) con 46/46 |
| **Comprobación anticipada** | El estado de hoy cumple lo anticipable. **No** garantiza el del 09-nov | La de las 21:05Z (16) se hizo con la herramienta defectuosa: sus lecturas son válidas, pero su rc 0 no valía como agregado y el bloque 06 dejó el `.pyc`. **Hoy no se ha repetido con la r2.** Hoy Sensor1 daría P13.inventario NO_CUMPLE (§4) |
| **P0 inmediato** | Todo lo anticipable y además 5b (dentro de la franja) | `bash p0_r2.sh inmediato …` en 1794191400 (09-nov 02:30Z). Pendiente, con orden de Mark |

**Retención del anillo con carga:** sigue **pendiente de medir durante el ensayo**. La lectura sin carga (929 s a las
21:05Z) no la demuestra y no se ha cambiado ningún umbral.

## 9. Pendientes en los hosts (ninguno ejecutado)

1. Decidir la ruta A o la B (§7).
2. Ruta A: retirar el `.pyc` (§5) y repetir la post-copia r2.
3. Ruta B: protocolo r5 (punto 13), r3 de traslado y post-copia con banco, copia autorizada y post-copia.
4. Repetir la comprobación anticipada con `p0_r2.sh anticipado` (solo lectura) y el P0 inmediato en la franja.
5. Orden expresa de Mark para E-carga (protocolo r4 o r5), que este encargo no da.
6. Opcional: defecto C (`LC_ALL=C comm`, comprobador r3).

## 10. Ficheros

| Ruta | Qué es |
|---|---|
| `p0-r2/p0_r2.sh` | Manejador P0 r2 |
| `p0-r2/bloques/*_r2.sh` | Bloques revisados: `estado`, `verificador`, `precheck` (envoltorio), `clientes` y `sensor1` |
| `p0-r2/bloques/precheck.sh` | S11 sin cambios (`b3127edd…`) |
| `p0-r2/pruebas/` | `test_p0_r2.py`, dobles `ssh` y `ssh_bloques`, `fixtures/` (la .2 de `902991e`), `correr_banco.ps1` y `muestras.py` |
| `p0-r2/banco/` | Resultados 65534 y root, y `muestras.txt` |
| `lecturas/` | Post-copia r2 de las 21:24Z, inventario detallado de Sensor1 y lectura de caché de `ec78ca5` |
| `regresiones/` | Bancos del producto (E-carga y suite completa) y del comprobador post-copia |
| `SHA256SUMS` | Sello de esta carpeta |
