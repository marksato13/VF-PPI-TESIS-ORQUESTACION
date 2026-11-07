# 19 · Corrección del falso positivo de P11 (identificación de muestreadores)

**Estado (07-nov, 00:19Z):**
- Corrección hecha en el producto, probada en banco aislado y verificada en el laboratorio solo con lecturas.
- P0 r3 anticipado: **rc 0**. 51/51 anticipables CUMPLE; P5b, P8 y P12 NO_EVALUABLE.
- Paquete idéntico antes y después en los 3 hosts.
- **E-carga NO ejecutada y NO programada. No se ha avanzado a la 4B ni a la 4C.**
- Un P0 anticipado conforme **no sustituye al P0 inmediato** (P5b solo se evalúa dentro de la franja del 09-nov) y
  **no autoriza E-carga**.

## Referencias

| Qué | Ref / sha256 |
|---|---|
| Docs de partida (main) | `0749151` (entrega 18) |
| Producto de partida | `recuperacion/etapa4a-pendientes-20261106` @ `20dabe2` |
| **Producto corregido** | misma rama @ **`975e715808f3ad454055712660414f2e8fd50878`** (padre `20dabe2`); main del producto sigue en `7b275b8` |
| Paquete en los hosts | `paquete-902991e`, **sin cambios** (SHA256SUMS `8480f0e0…5917d5dc74a68df30c`, 480 ficheros) |
| `sensor1_muestreadores.sh` .2 (paquete) | `25fb732d…` |
| `sensor1_muestreadores.sh` .3 (`20dabe2`) | `4ed4385674e9f731c7d50f12b132d86a0a3625355df24ebaf4fa9fa0c8342b6e` |
| **`sensor1_muestreadores.sh` .4 (`975e715`)** | **`63f7495714bf43c750748a1a6aad1e0506d10478b67034e41bd395490c05f823`** |
| `deploy/etapa4/ecarga/SHA256SUMS` (`975e715`) | `b9e12216…` |
| Bloque `p0-r3/bloques/sensor1_r3.sh` | `5ef3372a671d0b41d928823caa6a92d8f109b5c329a56e1719ab5979f4f911cd` |
| `laboratorio/previa_host.sh` | `4e1dd442a81329f6e499dd505d3f511dd96799e7094638a0a69e9f354e6fdddf` |

Los otros cinco bloques del P0 r3 son copias byte a byte de los del P0 r2 (17):
- `estado_r2.sh` `990da850…`;
- `verificador_r2.sh` `8714361e…`;
- `precheck_r2.sh` `131f0a56…`;
- `clientes_r2.sh` `a1adfa79…`;
- `precheck.sh`.

Los sha de todo el contenido de esta carpeta están en [`SHA256SUMS`](SHA256SUMS).

## 1. Causa

`sensor1_muestreadores.sh` .3 (`procesos()`) buscaba los muestreadores con `pgrep -af PATRÓN`. Ese método falla así:
- `pgrep -f` compara el patrón con la **línea de órdenes completa** de cada proceso.
- El mecanismo sin escritura del P0 r2 ejecuta el guion como `bash -c "$txt"`. Por eso el argv del propio intérprete
  contiene **todo el texto del guion**, incluidos los nombres `muestreo_fino.py`, `obs_pcap.py`, etc.
- `pgrep` encontraba al intérprete que lo había lanzado y la comprobación daba «FALLO ya hay muestreadores en marcha»,
  aunque en Sensor1 no hubiera ninguno (diagnóstico en `../18-cache-archivada-postcopia-p0/p11-diagnostico/`).
- Cualquier proceso ajeno que llevara esos nombres como texto (un editor, un `grep`, un `less`) producía el mismo
  falso positivo.
- La versión anterior tampoco distinguía «no lo sé» de «no hay». Si la consulta fallaba, el resultado dependía del
  rc de `pgrep`.

## 2. Corrección (producto `975e715`, versión 2026-11-06.4)

La identificación se hace por el **proceso ejecutado y sus argumentos**, no por el texto de la línea de órdenes.

`procesos()`/`pgrep` se sustituye por un código Python fijo (`MUESTREADORES_PY`), ejecutado como
`python3 -I -B -S -c`, que no escribe caché.

### Qué cuenta como muestreador

Se leen los argumentos reales de cada proceso en `/proc/<pid>/cmdline` (separados por NUL). Un proceso es muestreador
solo si cumple las dos condiciones:
1. El **ejecutable** (basename de argv[0]) es un intérprete Python: `python`, `python3`, `python3.14`…
2. Su **primer argumento de guion**, después de saltar las opciones del intérprete, tiene uno de estos basenames:
   - `muestreo_fino.py`;
   - `obs_pcap.py`;
   - `muestreo_s14.py`;
   - `salud_captura.py`, pero solo si el argumento siguiente es `muestrear`.

Reglas para saltar las opciones del intérprete:
- `-X` y `-W` llevan valor;
- `--check-hash-based-pycs` lleva valor;
- `--` termina las opciones;
- `-c` y `-m` significan que no hay guion, así que el proceso no es muestreador.

Con esto **no** son muestreadores:
- un `bash` (o cualquier intérprete) cuyo texto contenga los nombres;
- `grep muestreo_fino.py`;
- `python3 -c "…muestreo_fino.py…"`;
- `vim obs_pcap.py`;
- `python3 otro.py muestreo_fino.py`.

**Sí** lo son:
- `python3 /ruta con espacios/muestreo_fino.py …`;
- `/opt/venv/bin/python3 -u obs_pcap.py`;
- `python3 salud_captura.py muestrear`.

No se descartan en bloque ni los procesos `bash` ni los ascendientes del comprobador. No se usa `grep -v pgrep`.

### Tres estados

| rc del código | Estado | Resultado en `comprobar` |
|---|---|---|
| 0 | **ausencia confirmada** (se leyó al menos 1 proceso; 0 presentes, 0 ilegibles) | `OK ningún muestreador en marcha` |
| 10 | **presencia detectada** (una línea `MUESTREADOR pid=… nombre argv=…` por cada uno) | `FALLO ya hay muestreadores en marcha` |
| cualquier otro | **DESCONOCIDO**: no se pudo enumerar `/proc`, un proceso vivo tiene argv ilegible, no se leyó ningún proceso o el intérprete falló | `FALLO estado de los muestreadores DESCONOCIDO` (**nunca** se aprueba) |

Procesos que terminan durante la consulta:
- `FileNotFoundError` o `ProcessLookupError`, o un `OSError` en un pid que ya no existe, cuentan como
  **desaparecidos**. Se informan en la línea `CONSULTA revisados=… desaparecidos=… ilegibles=… presentes=…`.
- Si el proceso sigue vivo y no se puede leer, cuenta como **ilegible** y el estado es DESCONOCIDO.
- Si hay algún presente, la presencia manda aunque también haya ilegibles.

`json.dumps` escapa el argv en ASCII. El banco encontró un fallo real con argv no UTF-8 (`UnicodeEncodeError`), y la
versión publicada ya lo tiene corregido.

### Requisitos que no cambian

Se mantienen los cuatro muestreadores. No cambian:
- el requisito P11;
- el detector, el IF, las features, α y las heurísticas;
- la política de respuesta;
- los criterios del ensayo.

## 3. Mecanismo sin escritura del P0 r3 y su integridad

El P0 r3 (`p0-r3/p0_r3.sh`) es el P0 r2 con **un único bloque cambiado**: el de Sensor1, `sensor1_r3.sh`.

**No se modifica el paquete de los hosts.** El bloque deriva la .4 **en memoria** a partir de la .2 del paquete:
1. Exige que la .2 tenga sha `25fb732d…`.
2. Aplica las ediciones de `20dabe2` y exige que el resultado tenga el sha de la .3 (`4ed43856…`).
3. Sustituye la línea 2, las líneas 22–25 y las líneas 63–64 por el texto publicado en `975e715`. Ese texto va
   incrustado en el bloque como heredoc literal.
4. Exige que el resultado tenga el sha de la .4 (`63f74957…`).
5. Solo entonces lo ejecuta con `bash -c`.

Comportamiento según el paquete:
- un paquete que ya esté en .4 se ejecuta tal cual;
- cualquier otro sha da ERROR y no se ejecuta nada.

En la ejecución del laboratorio, el bloque lo dejó registrado así:
- `REQ X.mecanismo_sin_escritura CUMPLE derivada en memoria la 2026-11-06.4 (63f74957…) desde la .2 del paquete (paso .3 4ed43856…); nada escrito`.

**Fuente publicada del nuevo texto:**
- el fichero `deploy/etapa4/ecarga/sensor1_muestreadores.sh` del commit `975e715`;
- en esta carpeta, `p0-r3/pruebas/fuente/sensor1_r3.plantilla.sh` y `generar_sensor1_r3.py`.

El test `test_bloque_r3_reproducible_desde_la_plantilla` regenera el bloque a partir de esa fuente y del producto, y
comprueba que sale byte a byte igual. `test_r3_texto_publicado_alterado_no_se_ejecuta` comprueba que, si se altera el
texto incrustado, el bloque se niega a ejecutarlo.

Cambios del driver:
- `P11.muestreadores` es un requisito nuevo en `ESPERADOS[06-sensor1]`.
- Si falta, el P0 da ERROR (`test_p11_muestreadores_ausente_no_verifica`).
- Sus valores:
  - `CUMPLE` con `OK    ningún muestreador en marcha`;
  - `NO_CUMPLE` con `FALLO ya hay muestreadores en marcha`;
  - `ERROR` con DESCONOCIDO o cuando no hay exactamente una línea de veredicto.

Cambio menor, documentado aparte: `P13.inventario` usa ahora `comm --check-order` con comprobación de rc, el mismo
endurecimiento del comprobador post-copia r3.

## 4. Reproducción antes / después

| Ejecución | Sin muestreadores | Con muestreador real (banco) |
|---|---|---|
| **Laboratorio, P0 r2 (18, conservado)** `../18-…/p0-r2-anticipado-20261106T232410Z/` | `FALLO ya hay muestreadores en marcha` → **P11 NO_CUMPLE, rc 5** (falso positivo) | — |
| **Laboratorio, P0 r3 (esta entrega)** `laboratorio/p0-r3-anticipado-20261107T001801Z/` | `CONSULTA revisados=213 desaparecidos=0 ilegibles=0 presentes=0` → **P11 y P11.muestreadores CUMPLE, rc 0** | (no se arrancan procesos en el laboratorio) |
| Banco, bloque **anterior** `sensor1_r2` (`p0-r3/banco/banco-regresiones-p11-con-sensor1_r2-anterior.txt`) | **4 FALLAN**: con los paquetes .2 y .3 y con procesos ajenos, «ya hay muestreadores»; el .4 da ERROR porque r2 rechaza un guion que no conoce | — |
| Banco, bloque **r3** (`p0-r3/banco/banco-p0-r3-*.txt`) | las mismas 4 pruebas **PASAN** | cada uno de los 4 y varios a la vez → **NO_CUMPLE**, y el P0 **no permite avanzar** |
| Producto, `20dabe2` (.3) con los tests nuevos (`regresiones/producto-ecarga-v3-anterior-65534.txt`) | **3 regresiones FALLAN**: sin muestreadores por `bash -c`, y ajenos con los nombres (fichero y `bash -c`) | — |
| Producto, `975e715` (.4) | pasan | detectados |

El P0 r2 con rc 5 y toda la evidencia de la entrega 18 se conservan **sin cambios** como evidencia histórica.

## 5. Pruebas aisladas

Las pruebas se hicieron así:
- en Docker con `--network none` e imagen `cyberflow-etapa3-banco:1`;
- con procesos **reales** del contenedor y, para los fallos de lectura, con un `/proc` simulado inyectado (`_Proc`);
- como usuario 65534 y como root.

### Casos exigidos

| Caso | Prueba(s) | Resultado |
|---|---|---|
| Sin muestreadores (fichero) | `test_muestreadores_sin_ninguno_desde_fichero`; banco P0 `test_todos_correctos_anticipado` | ausencia confirmada |
| Sin muestreadores por el mecanismo del P0 (`bash -c`) | `test_regresion_muestreadores_sin_ninguno_por_el_mecanismo_del_p0`; `test_regresion_p11_sin_muestreadores_cumple[.2/.3/.4]` | ausencia (con la .3 **falla**) |
| Cada uno de los 4 por separado (fichero y `bash -c`) | `test_cada_muestreador_presente_se_detecta[4×2]`; `test_r3_cada_muestreador_presente[4]` | presencia, NO_CUMPLE |
| Varios a la vez | `test_varios_muestreadores_simultaneos[2]`; `test_r3_varios_muestreadores` | presencia, uno por línea |
| Intérprete del comprobador con los nombres en su argv | los dos de `bash -c` anteriores, además de `test_identificacion_por_argv` (bash, `python3 -c`, `-m`) | no cuenta |
| Procesos ajenos con los nombres en el texto | `test_regresion_procesos_ajenos_con_los_nombres_en_el_texto[fichero, bash-c]`; `test_regresion_p11_ajenos_con_los_nombres_no_son_muestreadores` | ausencia (con la .3 **falla**) |
| Ajenos junto a un muestreador real | `test_ajenos_no_ocultan_un_muestreador_real` | presencia, solo el real |
| Argumentos y rutas con espacios, argv no UTF-8 | `test_muestreador_en_ruta_con_espacios_se_detecta`; `test_unidad_argv_con_bytes_no_utf8_y_espacios` | detectado; argv escapado |
| Error al consultar procesos | `test_unidad_no_se_puede_enumerar_proc`; `test_consulta_fallida_es_desconocido_nunca_ausencia_ni_presencia[rc 2, rc 1, kill -9]` | DESCONOCIDO |
| Error al leer los argumentos de un proceso vivo | `test_unidad_argv_ilegible_de_proceso_vivo_es_desconocido`; `test_unidad_lectura_que_falla_a_mitad_en_proceso_vivo` | DESCONOCIDO |
| Proceso que termina durante la lectura | `test_unidad_proceso_que_termina_durante_la_lectura[3]`; `test_unidad_error_de_permiso_de_un_proceso_que_ya_termino`; `test_procesos_que_terminan_durante_la_consulta` (procesos cortos reales) | desaparecido, sin cambiar el estado |
| Ningún proceso legible | `test_unidad_ningun_proceso_legible_no_es_ausencia` | DESCONOCIDO |
| Presencia junto a ilegibles | `test_unidad_presencia_manda_aunque_haya_ilegibles` | presencia |
| Ejecuciones repetidas sin escrituras | `test_comprobar_repetido_por_el_mecanismo_del_p0_no_escribe`; `test_r3_tres_pasadas_sin_escrituras_por_cada_version` | 0 ficheros nuevos, paquete igual |
| Sin `pgrep` en la identificación | `test_guion_sin_pgrep_en_la_identificacion` | — |

### Recorrido completo del P0 r3

| Caso | Prueba | Resultado |
|---|---|---|
| Ausencia y todo lo demás válido | `test_todos_correctos_anticipado`, `test_inmediato_conforme`, `test_entorno_sano_del_banco` (Sensor1 sano simulado) | **P11 CUMPLE**, rc 0 |
| Presencia real | `test_presencia_real_no_habilita_el_avance` | **P11 NO_CUMPLE**, el P0 no permite avanzar |
| Consulta fallida | `test_consulta_desconocida_no_se_aprueba`, `test_r3_consulta_fallida_es_error_y_no_se_oculta[3]` | ERROR, nunca aprobado |
| Un fallo seguido de operaciones correctas | `test_error_seguido_de_operaciones_correctas`, `test_r3_consulta_fallida_es_error_y_no_se_oculta` | el fallo se mantiene |

### Totales

| Banco | Fichero | Resultado |
|---|---|---|
| Producto `975e715`, E-carga, 65534 | `regresiones/producto-ecarga-v4-65534.txt` | 141 passed |
| Producto `975e715`, E-carga, root | `regresiones/producto-ecarga-v4-root.txt` | 141 passed |
| Producto `20dabe2` con los tests nuevos | `regresiones/producto-ecarga-v3-anterior-65534.txt` | **3 failed** (exactamente las 3 regresiones), 100 passed, 38 skipped |
| Producto `975e715`, suite completa | `regresiones/producto-suite-completa-65534.txt` | 1063 passed, 53 skipped |
| P0 r3, 65534 | `p0-r3/banco/banco-p0-r3-65534.txt` | 67 passed |
| P0 r3, root | `p0-r3/banco/banco-p0-r3-root.txt` | 67 passed |
| P0 r3 con el bloque anterior `sensor1_r2` | `p0-r3/banco/banco-regresiones-p11-con-sensor1_r2-anterior.txt` | **4 failed** (las 4 regresiones de P11) |
| Comprobación previa del laboratorio | `laboratorio/banco-previa-65534.txt` | fallos=0 |

## 6. Regresiones pertinentes

| Qué | Fichero | Resultado |
|---|---|---|
| Propagación de errores del P0 (ssh fallidos, bloque incompleto, error que precede a operaciones correctas, transporte distinto, CR) | dentro de `banco-p0-r3-*.txt` | pasan |
| Sin escrituras (`test_banco_detecta_escritura_de_cache`, `test_regresion_comprobar_no_escribe_en_el_paquete`, tres pasadas) | producto y P0 r3 | pasan |
| P0 r2 de la entrega 17, sin cambios, con su producto `20dabe2` | `regresiones/p0-r2-banco-17-sin-cambios-65534.txt` | 46 passed |
| Comprobador post-copia r3 de la entrega 18, sin cambios | `regresiones/postcopia-r3-banco-18-65534.txt` | 63 passed |

## 7. Laboratorio: solo lectura (07-nov, 00:18–00:20Z)

Secuencia completa en `laboratorio/secuencia.sh`, lanzada desde `[LAPTOP Git Bash]`. Cada paso guarda stdout, stderr
y rc. No se arrancó, paró ni instaló nada, y no se escribió en los hosts.

| Paso | Salida | Resultado |
|---|---|---|
| 1. Sin generadores ni muestreadores del ensayo (bastión, Sensor1, srv-dmz, clientes): cribado conservador por texto con `ps`, y en Sensor1 además la identificación .4 por argv | `laboratorio/previa-20261107T001801Z/` | **rc 0**, los 4 SIN_PROCESOS_DEL_ENSAYO; guion `4e1dd442…` recibido íntegro |
| 2. Comprobador post-copia r3 (18, sin cambios) | `laboratorio/postcopia-r3-20261107T001801Z/` | **CONFORME 3/3**, 12/12 cada host; recibido `799af8f1…` |
| 3. Instantánea antes del P0 y comparación con la última de la entrega 18 | `laboratorio/instantaneas/antes-p0-…`, `comparacion-18despues-vs-antes-p0-….txt` | IDÉNTICAS en los 3 hosts |
| 4. **P0 r3 anticipado** | `laboratorio/p0-r3-anticipado-20261107T001801Z/` (+ `.rc-driver` = 0) | **rc 0**; 9/9 bloques; **51/51 anticipables CUMPLE**; P5b, P8 y P12 NO_EVALUABLE |
| 5. Instantánea después y comparación antes/después | `laboratorio/instantaneas/despues-p0-…`, `comparacion-antes-despues-p0-….txt` | **IDÉNTICAS** en los 3 hosts |

Requisitos de P11 en Sensor1 (`06-sensor1.stdout`):
- `P11 CUMPLE comprobar rc 0`.
- `P11.muestreadores CUMPLE ningún muestreador en marcha (ausencia confirmada: revisados=213 desaparecidos=0 ilegibles=0 presentes=0)`.
- `P11.retencion CUMPLE`: el fichero más antiguo del anillo tiene 1158 s (≥ 900 s).
- `X.paquete_sin_cambios CUMPLE`: inventario idéntico antes y después, 566 entradas.
- `X.dir_no_creado CUMPLE`.

### Paquete intacto

Antes y después del P0, en los 3 hosts:
- **481 ficheros** listados por la instantánea;
- SHA256SUMS del paquete **`8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c`**;
- huella de contenidos `281d5f3e…a03955`.

Huellas de estructura:
- bastión `83c19ee5…`;
- Sensor1 `9e379531…`;
- srv-dmz `24a582f4…`.

Las tres coinciden también con la instantánea «después» de la entrega 18, de modo que no hubo cambios entre las dos
entregas. P13 informa «480 ficheros = manifiesto», la misma cifra que el post-copia r3; la instantánea cuenta 481 con
su propio criterio, igual que en la entrega 18.

## 8. Lo que solo se puede medir durante E-carga

- **P5b**: dentro de la franja [1794191400, 1794200400] del 09-nov. Solo lo evalúa el **P0 inmediato**.
- **P12**: los muestreadores arrancan antes de T_g − 300 s. Se cumple en la ejecución.
- Retención del anillo **bajo carga**. Hoy son 1158 s en reposo; bajo carga la rotación es más rápida.
- S14 y la continuidad de los PCAP bajo carga real.
- Detección de un muestreador **real** en el laboratorio. Por decisión expresa no se arrancan procesos para probarla;
  queda demostrada solo en banco.

## Contenido

```
p0-r3/
  p0_r3.sh                   driver (VERSION 2026-11-06.r3)
  bloques/                   sensor1_r3.sh (nuevo) + 5 bloques copiados del P0 r2
  pruebas/                   test_p0_r3.py, correr_banco.ps1, dobles/, fixtures/ (.2 y .3), muestras.py,
                             fuente/ (plantilla y generador del bloque r3)
  banco/                     resultados del banco (65534, root, regresiones con el bloque anterior)
regresiones/                 producto .4 y .3, suite completa, P0 r2 (17) y post-copia r3 (18) sin cambios
laboratorio/
  previa.sh, previa_host.sh  comprobación previa de solo lectura (y su banco)
  secuencia.sh               orden seguido en el laboratorio
  previa-*/ postcopia-r3-*/ p0-r3-anticipado-*/ instantaneas/   salidas (stdout, stderr, rc)
SHA256SUMS                   sha256 de cada fichero de esta carpeta
```
