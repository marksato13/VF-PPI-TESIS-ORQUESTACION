# 18 · Caché archivada, comprobador post-copia r3 y P0 r2 anticipado (06-nov-2026, 23:22–23:26Z)

**Resultado en una línea:** se archivó fuera del paquete la única caché autorizada y se retiró del paquete. El
comprobador post-copia r3 da **CONFORME 3/3** (480 ficheros en cada host). El **P0 r2 anticipado** termina con
**rc 5**: 9/9 bloques sin errores y 49/50 precondiciones anticipables CUMPLE. **P11 da NO_CUMPLE**: la herramienta se
detecta a sí misma (está diagnosticado), pero el NO_CUMPLE se mantiene y no se ha corregido. El paquete quedó idéntico
antes y después del P0 en los 3 hosts. **E-carga NO ejecutada y NO programada.**

Autorización (Mark, 06-nov): archivar la caché identificada fuera del paquete, corregir el comprobador y repetir la
verificación posterior y el P0 anticipado. **No** autorizada: ejecutar o programar E-carga, arrancar generadores o
muestreadores, modificar servicios ni activar restricciones. Nada de eso se hizo.

## 0. Referencias confirmadas antes de actuar

| Referencia | Valor |
|---|---|
| Docs `VF-PPI-TESIS-ORQUESTACION` | `origin/main` = `4aec489` (0 commits posteriores al empezar) |
| Producto `recuperacion/etapa4a-pendientes-20261106` | `20dabe2` (0 commits posteriores); `main` del producto `7b275b8`, sin tocar |
| Paquete en los hosts | `~/cf-e4/paquete-902991e`, `SHA256SUMS` `8480f0e0…df30c`, 480 ficheros. **Se mantiene: no se cambia de paquete ni se repite el traslado.** |
| P0 | P0 r2 ([`../17-correccion-p0/p0-r2/`](../17-correccion-p0/p0-r2/)) con su mecanismo sin escritura. El texto derivado en memoria tiene sha `4ed43856…42b6e` = `sensor1_muestreadores.sh` 2026-11-06.3 publicado en `20dabe2` (REQ `X.mecanismo_sin_escritura` CUMPLE) |

## 1. Caché archivada (solo el fichero autorizado)

| Dato | Valor |
|---|---|
| Fichero autorizado | `/home/m4rk/cf-e4/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc` |
| Comprobaciones previas | Existe, **no es enlace**, **es regular**, sha256 **`754ec72930cb1b187b387f0360ae65c25763ec0cccf4abe7dd5f8aa19be701d1`** = el esperado. `__pycache__` solo contenía ese fichero y el fichero no figura en el manifiesto |
| Metadatos | 27 980 B · `m4rk:m4rk` (1000:1000) · `-rw-r--r--` (644) · nacimiento = modificación = cambio `2026-11-06 21:05:27.803101848 +0000` · acceso `21:24:44.452345095` · inodo 1188649. Ver [`metadatos.txt`](archivo/destino-sensor1-20261106T232245Z/metadatos.txt) |
| **Destino nuevo** (fuera de todo paquete; `mkdir` sin `-p`, no existía) | **`/home/m4rk/cf-e4/archivo-cache-pyc-20261106T232245Z/`** (Sensor1, modo 0750) |
| Copia | `…/archivo-cache-pyc-20261106T232245Z/evaluar_ecarga.cpython-312.pyc`. Mismo sha256 `754ec729…01d1`; `cmp` idéntico; mismo tamaño; mtime conservado (`cp --preserve=mode,timestamps`) |
| Sello del destino | `SHA256SUMS` del destino `9f17d2e322a202fc07884c4eed90ccd5146a66c32f919031d27b7314ae5dfe2d`: metadatos, copia, instantáneas antes/después y diferencias |
| Retirada | **Solo después** de verificar la copia: `rm` del original y `rmdir` de `__pycache__`, que quedó vacío |

**Evidencia de que solo se retiró lo autorizado**, con instantáneas completas del paquete antes y después de la
retirada, hechas en el host. Las de estructura recogen tipo, modo, tamaño, mtime y ruta de todo; las de contenido, el
sha256 de cada fichero.

```
diferencia.estructura:
< d 775 m4rk /home/m4rk/cf-e4/paquete-902991e/deploy/etapa4/sensor1/__pycache__
< f 644 27980 1793999127.8031018480 m4rk /home/m4rk/cf-e4/paquete-902991e/deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc
diferencia.sha256:
< 754ec72930cb1b187b387f0360ae65c25763ec0cccf4abe7dd5f8aa19be701d1  ./deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc
```

- **Antes:** 482 ficheros regulares (480 + `SHA256SUMS` + la caché).
- **Después:** 481. `sha256sum -c --strict` del manifiesto OK; `SHA256SUMS` sigue en `8480f0e0…`.
- Fuera de ese fichero y ese directorio no hubo ninguna línea de diferencia.
- **No se tocaron** otros `.pyc` ni las cachés históricas de `paquete-ae2900e` y `paquete-a12deae`. El post-copia sigue
  informando de 482 ficheros en el `paquete-a12deae` de Sensor1, sin cambios.

Ficheros:
- Guion: [`archivo/archivar_cache.sh`](archivo/archivar_cache.sh) (sha `59cd3bae…8c51`; el host imprimió ese mismo
  sha de los bytes recibidos).
- Envío: [`archivo/ejecutar_en_sensor1.sh`](archivo/ejecutar_en_sensor1.sh).
- Salida: `archivo/sensor1-20261106T232245Z.{stdout,stderr,rc}` (rc 0, stderr vacío).
- Destino traído en solo lectura, sin el `.pyc`; sello verificado en local:
  [`archivo/destino-sensor1-20261106T232245Z/`](archivo/destino-sensor1-20261106T232245Z/).
- Banco previo, sin red, con el paquete real `902991e` y una caché simulada:
  [`archivo/banco/`](archivo/banco/). 9/9 comprobaciones, como 65534 y como root:
  - el paquete de prueba es `902991e` (SUMAS `8480f0e0…`);
  - correcto;
  - repetición (ya archivado → rc 4);
  - hash distinto;
  - enlace simbólico;
  - ausente;
  - `__pycache__` con otro `.pyc`;
  - destino existente;
  - no regular.

  En todas las paradas el resultado es rc 4 y el paquete queda **sin ningún cambio**. Las variables `BANCO_*` solo
  existen en el banco; en Sensor1 la salida dice «modo real».

## 2. Comprobador post-copia r3

**Defecto de la r2.** Ordenaba con `LC_ALL=C sort`, pero comparaba con `comm` en el locale del host. En Sensor1 eso
producía «comm: … not in sorted order» y un detalle poco fiable. El veredicto de la r2 no podía ser un OK falso por
la colación. **Además, el banco r3 demuestra otro defecto de la r2:** ignora el rc de `comm`. Si `comm` falla, las
listas quedan vacías y, con 480/480, la r2 da **CONFORME falso**.

**r3**, en [`comprobador-r3/`](comprobador-r3/):

| Fichero | sha256 |
|---|---|
| `post_copia_host_r3.sh` | `799af8f10d4f6dce5abd37ac6fa1ac250d14aadfd03bb7654dab8b070d1965d6` |
| `comprobar_post_copia_r3.sh` | `9810b8550d45c3204a507b7bd3500c9a9052504b06a676f04a1582d7b994c813` |

- `export LC_ALL=C` para todo el guion; además, `LC_ALL=C` explícito en los dos `sort` y en los dos `comm`.
- `comm --check-order` y comprobación del rc: si falla o la entrada no está ordenada, el inventario es **ERROR**
  (host ERROR_LECTURA, rc 3). Nunca es OK.
- Recuentos de ausentes e inesperados en el detalle.
- El driver comprueba cada escritura de `resumen.txt`; si alguna falla, el resultado es rc 4 EVIDENCIA_INCOMPLETA.
- **La r2 se conserva intacta** en [`../16-postcopia-p0/comprobador-r2/`](../16-postcopia-p0/comprobador-r2/)
  (`post_copia_host_r2.sh` `07063091…6520`, `comprobar_post_copia_r2.sh` `ac783368…2b82`).

**Banco** (sin red; el paquete real `902991e`; ssh y órdenes de escritura son dobles; se comprueba que los hosts
simulados no cambian ningún byte). Salidas en [`comprobador-r3/banco/`](comprobador-r3/banco/):

| Ejecución | Resultado |
|---|---|
| r3 como 65534 | **63 passed** |
| r3 como root | **62 passed, 1 skipped** (la de `chmod 000`, que root lee; el error de lectura queda cubierto por la prueba del directorio) |
| r2 sin cambios (regresión) | 27 passed |

Pruebas nuevas en la r3 (36), además de las 27 heredadas de la r2:
- **8 configuraciones regionales:**
  - sin locale;
  - `LC_ALL=C`, `POSIX`, `C.UTF-8`, `es_PE.UTF-8` y `en_US.UTF-8`;
  - `LANG=es_PE.UTF-8`;
  - `LC_COLLATE=es_PE` con `LANG=en_US`.

  `es_PE` y `en_US` se compilan con `localedef` a partir de las fuentes de glibc. La prueba exige que cambien la
  colación: si no, falla, no se salta. En cada configuración se prueba:
  - inventarios iguales → CONFORME;
  - fichero añadido (el `.pyc` real) → FALLO, que lo nombra exactamente con «inesperados (1)»;
  - fichero ausente → FALLO con «ausentes (1)» y su ruta;
  - error de lectura → ERROR_LECTURA.
- La **regresión r2 con `es_PE`** reproduce el aviso de Sensor1 y su veredicto FALLO. La r3, en el mismo estado,
  nombra el fichero sin aviso.
- **`comm` que falla:** la r2 da CONFORME 3/3 falso (defecto demostrado); la r3 da ERROR_LECTURA en los 3 hosts y
  rc 4.
- **`sort` que entrega una lista desordenada:** la r3 da ERROR, nunca OK.

Ejecución: [`comprobador-r3/pruebas/correr_banco.ps1`](comprobador-r3/pruebas/correr_banco.ps1) con
`-Bundle <bundle del producto> -I18n <fuentes de locales>`.

## 3. Verificación posterior con la r3 (después del archivado)

Carpeta [`postcopia-r3-20261106T232304Z/`](postcopia-r3-20261106T232304Z/), con stdout, stderr y rc por host:

| Host | rc | Estado | Detalle |
|---|---|---|---|
| bastión (`gadmin`) | 0 | CONFORME 12/12 | inventario «480 ficheros, ninguno ausente, ninguno inesperado» |
| Sensor1 (`m4rk`) | 0 | **CONFORME 12/12** | ídem; antes del archivado la r2 daba aquí NO_CONFORME 11/12 |
| srv-dmz (`adminsrvdmz`) | 0 | CONFORME 12/12 | ídem |

`RESULTADO_GLOBAL rc=0 CONFORME 3/3`; stderr vacío en los tres. En cada host:
- `SHA256SUMS` es `8480f0e0…` y la marca `VERIFICADO` lo confirma;
- `sha256sum -c --strict` sale OK;
- evaluador `53e9f7bd…` y `ecarga/SHA256SUMS` `e001352c…`, que también verifica;
- versiones `evaluar_s14 2026-11-06.2` y `construir_entrada 2026-11-06.3`;
- aviso junto a `paquete-a12deae`;
- ningún resto parcial.

El host recibió los bytes con sha `799af8f1…` = la r3 local.

## 4. P0 r2 en modo ANTICIPADO

Carpeta [`p0-r2-anticipado-20261106T232410Z/`](p0-r2-anticipado-20261106T232410Z/): por bloque `stdout`, `stderr`,
`rc` y `motivo`, además de `resumen.txt`; el rc del driver está en `p0-r2-anticipado-20261106T232410Z.rc-driver`.

| Resumen | Valor |
|---|---|
| Bloques | **9/9 ejecutados sin errores** (ssh rc 0, transporte igual, `FIN_BLOQUE` coherente, REQ completos) |
| Anticipables | **49/50 CUMPLE**; **P11 = NO_CUMPLE** |
| Momento / documental / ejecución | P5b NO_EVALUABLE (23:24:56Z es anterior a la franja [1794191400, 1794200400]) · P8 NO_EVALUABLE · P12 NO_EVALUABLE |
| **RESULTADO_GLOBAL** | **rc 5**, modo anticipado, PRECONDICIONES NO CONFORMES: P11=NO_CUMPLE |

**El rc 5 se conserva tal cual: no se reinterpreta como éxito.**

Algunos CUMPLE relevantes:
- P13: sumas, hashes e inventario de 480;
- P9: evaluador `53e9f7bd…` VERSION 2026-11-06.4;
- `X.mecanismo_sin_escritura` y `X.dir_no_creado`;
- `X.paquete_sin_cambios`: 566 entradas idénticas antes y después;
- P3: 0 procesos con `--aplicar`/`--enforce`, ruleset de Sensor1 `24c320e3…` y srv-dmz sin tablas;
- v1 apagado y cadena v2 activa;
- P11.retención: el fichero más antiguo del anillo tiene 1200 s, sin carga;
- P6: `/home` 11 951 MiB y MemAvailable 6625 MiB;
- P4/P10 en clientes.

### P11 = NO_CUMPLE: motivo documentado, sin reparar

`sensor1_muestreadores.sh comprobar` informó «FALLO ya hay muestreadores en marcha». Para entenderlo se hizo, en solo
lectura, lo siguiente:

1. **En Sensor1 no hay ningún muestreador.**
   [`p11-diagnostico/sensor1-20261106T232600Z.stdout`](p11-diagnostico/sensor1-20261106T232600Z.stdout) muestra:
   - con el mismo patrón, escrito con clases de caracteres para que no coincida consigo mismo, `pgrep` da rc 1;
   - solo corren el motor, el panel, el feed v2 y la captura de vía rápida (procesos de hace ~84 400 s);
   - no hay unidades `*muestre*`.
2. **Causa reproducida sin red**
   ([`p11-diagnostico/reproducir_autocoincidencia.sh`](p11-diagnostico/reproducir_autocoincidencia.sh) →
   [`reproduccion-banco.txt`](p11-diagnostico/reproduccion-banco.txt)):
   - `procesos()` ejecuta `pgrep -af "salud_captura.py muestrear|muestreo_fino.py|obs_pcap.py|muestreo_s14.py"`;
   - `pgrep` se excluye a sí mismo, pero no al `bash` que lo ejecuta;
   - el mecanismo sin escritura del P0 r2 corre el texto derivado con `bash -c "$txt"`, así que la línea de órdenes de
     ese bash **es el guion entero**, que contiene el patrón.
   - Resultado: `bash -c "$txt"` → «ya hay muestreadores en marcha»; el mismo texto desde un fichero → «ningún
     muestreador en marcha».
3. El banco del P0 r2 (17, 46/46) no lo detectó. Esta es la **primera ejecución del P0 r2 contra el laboratorio**.

**Decisión:** P11 queda **NO_CUMPLE** en este P0 anticipado. No se corrigió `p0_r2.sh`, `sensor1_r2.sh` ni
`sensor1_muestreadores.sh`, porque la autorización cubría el comprobador post-copia, no las herramientas de P0. Tampoco
se tocó ningún servicio ni proceso. La corrección propuesta queda para decisión de Mark, por ejemplo:
- hacer que `procesos()` excluya su propio árbol (`$$`/`$BASHPID` y sus padres);
- o usar un patrón que no pueda coincidir consigo mismo.

En cualquier caso debe llevar una prueba de regresión con `bash -c`. **Hasta entonces, P11 no puede darse por
cumplido** con esta herramienta en modo sin escritura.

### Este P0 anticipado ≠ el P0 inmediato previo al ensayo

- Este es un P0 **anticipado** (06-nov, 23:24Z): solo comprueba lo que puede comprobarse días antes.
- **No sustituye** al P0 **inmediato** exigido por el protocolo r4 §3.5 dentro de la franja `1794191400`–`1794200400`
  (09-nov), en el que P5b es obligatorio.
- El estado de hoy no garantiza el del 09-nov.
- Además, el P0 inmediato tendrá el mismo problema de P11 mientras no se corrija la herramienta.

## 5. Paquete antes y después del P0 (inventario y hashes)

Instantáneas de solo lectura en los 3 hosts: [`instantaneas/`](instantaneas/).
- Herramientas: `instantanea_host.sh` `b4dfd6df…` y `tomar.sh` `5bd4096c…`.
- Contenido de cada instantánea: estructura completa (tipo, modo, tamaño, mtime con ns, propietario, ruta; también
  directorios) y sha256 de cada fichero regular.

| Host | Antes del P0 (`antes-p0/`) | Después del P0 (`despues-p0/`) | Comparación |
|---|---|---|---|
| bastión | estructura `83c19ee5…`, contenidos `281d5f3e…`, 481 ficheros | idéntico | **IDÉNTICAS** |
| Sensor1 | estructura `9e379531…`, contenidos `281d5f3e…`, 481 ficheros | idéntico | **IDÉNTICAS** |
| srv-dmz | estructura `24a582f4…`, contenidos `281d5f3e…`, 481 ficheros | idéntico | **IDÉNTICAS** |

- Resultado: [`comparacion-antes-despues-p0.txt`](instantaneas/comparacion-antes-despues-p0.txt) → `RESULTADO_COMPARACION
  rc=0`. 481 = 480 del manifiesto + `SHA256SUMS`.
- `contenidos` (`281d5f3e…`) es el mismo en los tres hosts y coincide con el `despues.sha256` del archivado. Los tres
  paquetes tienen, por tanto, exactamente el mismo contenido, y **el P0 no modificó el paquete**.

## 6. Lo que NO se hizo y lo que NO se afirma

- **E-carga NO ejecutada y NO programada.** No se arrancaron generadores ni muestreadores; no se modificó ningún
  servicio ni se activó ninguna restricción.
- Sin cambios en detector, IF, características, α, heurísticas, política de respuesta ni criterios del ensayo.
- **No se declara validado el comportamiento con carga.** La retención del anillo (1200 s) está medida **sin carga**.
- No se borró ninguna evidencia anterior. Las carpetas 15, 16 y 17 quedan intactas. El único cambio en el laboratorio
  es la retirada del `.pyc` autorizado y de su `__pycache__` vacío, más el directorio nuevo de archivo.
- No se cambió de paquete ni se repitió el traslado.

**Fin del encargo. Pendiente de decisión de Mark:** corregir la autocoincidencia de P11 en las herramientas de P0, y
después la autorización expresa, si procede, para el P0 inmediato y E-carga.
