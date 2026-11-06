# Traslado del paquete `902991e` al laboratorio: guiones r2 (corregidos y probados en banco)

> **Actualización (06-nov, 19:50Z): estado 2 ALCANZADO.**
> - Mark ejecutó el comando de §5 y terminó con **rc 0, «TRASLADO COMPLETO» 3/3** (`RUN=20261106T194952Z-10146`).
> - Las comprobaciones de §6 pasan en el bastión, Sensor1 y srv-dmz.
> - Evidencia en [`../evidencia/15-traslado-902991e/`](../evidencia/15-traslado-902991e/).
> - El primer intento acabó en rc 2, sin conexión, por la ruta larga de Windows: hay que lanzar el guion desde `~`
>   con su ruta absoluta.
> - P0 (estado 3) y E-carga (estado 4) siguen pendientes. E-carga no está ni ejecutada ni programada.
>
> El texto de abajo se conserva tal como se revisó.

**Estado: guiones corregidos y probados en banco. NO se ha ejecutado ninguna copia.** No hubo ninguna conexión ni
escritura en el laboratorio. No se ha arrancado ningún generador, no se ha modificado ningún servicio, no se ha
activado ninguna restricción, no se ha ejecutado ni programado E-carga y no se ha iniciado la 4B ni la 4C.

El destino sigue siendo el producto **`902991e`**, sin cambios: `ecarga/SHA256SUMS` `e001352c…` y evaluador
`53e9f7bd…`. No cambian S14, el motor, el modelo IF, las 28 características, α, los heurísticos ni la política de
respuesta.

**Guiones r2** (canónicos): [`traslado-902991e-r2/`](traslado-902991e-r2/), con `SHA256SUMS` propio.
- `paquete_902991e.sh`: portátil, `VERSION_GUION` `paquete_902991e r2 2026-11-07.1`.
- `reparto_bastion_902991e.sh`: bastión, lanzado por el anterior. Sustituye al bloque `REMOTO` incrustado.
- `op_host_902991e.sh`: cada host, `op_host_902991e r2 2026-11-07.1`.
- `pruebas/`: banco aislado (`test_traslado.py`, dobles de ssh, scp, rm y de las órdenes prohibidas, y
  `correr_banco_traslado.ps1`).
- `banco/`: salidas.

**Sustituidos:** `../evidencia/13-correccion-s14/paquete_902991e.sh` y `op_host_902991e.sh`. Se conservan **sin
modificar** como evidencia y **no se usan**.

## 1. Defectos, causa, corrección y prueba

Reproducción: `traslado-902991e-r2/banco/banco-anterior-65534.txt` y `anterior-detalle.txt`. Clasificación prueba a
prueba en `clasificacion-anterior.txt`.

| # | Defecto (versión anterior) | Causa | Corrección (r2) | Prueba (falla con la anterior por **éxito falso**) |
|---|---|---|---|---|
| D1 | `op_host` detecta hashes erróneos, un evaluador distinto o un manifiesto distinto, y termina con **rc 0** | Cada comprobación era `cmd && echo OK \|\| echo DISTINTO`, sin salir. El rc lo fijaba la última orden (`ls \| sed`) | Cada verificación devuelve su código (6–9). `fin()` limpia y sale con el código **original** | `test_regresion_host_paquete_invalido` ×6: alterado, ausente, inesperado, evaluador, versión y manifiesto de E-carga |
| D2 | El principal imprime `sensor1: rc N` pero termina con **rc 0** | El bucle remoto no acumulaba los rc y el heredoc acababa en `rm -f` | El reparto emite `RESULTADO <host> rc= estado=` por host y rc 1 si alguno falla. El principal exige 3/3 y, si no, rc 6 «TRASLADO INCOMPLETO» con la lista de hosts | `…fallo_de_scp…[sensor1/srvdmz]`, `…fallo_de_ssh[sensor1]`, `…tgz_truncado…`, `…destino_existente_en_un_host`, `…un_host_correcto_y_otro_fallido` |
| D3 | Inventario incompleto: no detectaba ficheros inesperados ni un `SHA256SUMS` sustituido | Solo `sha256sum -c`, que no ve ficheros sobrantes | Lista exacta de ficheros (`find` = `SHA256SUMS`). El hash del `SHA256SUMS` interno debe ser `SUMAS`, calculado en el portátil | `…[fichero-inesperado]`, `…[fichero-esperado-ausente]` |
| D4 | El aviso «sustituido» se creaba aunque el paquete nuevo no verificara. Cualquier fichero con ese nombre contaba como «aviso ya presente» | Se creaba de forma incondicional al final | El aviso solo se crea tras verificar e instalar con marca. Si existe y no es el esperado: rc 11 | `…fallo_al_crear_el_aviso`; en las 6 alteraciones se comprueba que no hay aviso |
| D5 | Un paquete inválido quedaba en `~/cf-e4/paquete-902991e`, con nombre utilizable, y bloqueaba el reintento | Se extraía directamente en el destino | Se extrae en `.paquete-902991e.parcial.<RUN>` (oculto). Solo se renombra al destino tras verificar todo, y entonces se escribe la marca `paquete-902991e.VERIFICADO.txt`. Utilizable = directorio **y** marca | `…recuperacion_destino_sin_marca`; las alteraciones comprueban que no queda destino |
| D6 | El `SHA256SUMS` interno podía listarse a sí mismo. En Linux salen 481 entradas, con `./SHA256SUMS` = hash del fichero vacío (`e3b0c442…`), y `-c` falla siempre, pero sin cortar el proceso | Se escribía con `> SHA256SUMS` **dentro** del árbol mientras `find` lo recorría (carrera). En el portátil salió 480 por azar | Se escribe fuera del árbol y luego se mueve. En el portátil y en Linux da 480 entradas y el mismo `SUMAS` `8480f0e0…` | `test_regresion_manifiesto_interno_sin_autorreferencia` |
| D7 | Limpieza y evidencia | Sin registro por host; la limpieza era la última orden | Limpieza que nunca sustituye el rc original. Registro `~/cf-e4/traslado-902991e.<RUN>.<host>.log` con host, operación, rc y `ESTADO_FINAL` | `…fallo_de_limpieza_tras_un_error` (host), `…fallo_de_limpieza_en_el_portatil…` |
| D8 | La referencia Git era la punta de la rama | `git archive $RAMA` y comparaba la punta con `902991e` | `git archive 902991ec077c…` fijado, con `merge-base --is-ancestor` respecto a la rama remota y `core.autocrlf=false` | `test_referencia_git_inaccesible` (contrato) |

## 2. Resultados de las pruebas aisladas

Banco Docker `--network none`, carpetas de solo lectura, `/tmp` y `/sim` en tmpfs. ssh y scp son dobles: cada host es
un directorio. systemctl, sudo, nft, reboot, shutdown, install, chmod, chown, iptables y useradd son dobles que
registran la llamada y fallan.

En **todas** las pruebas se comprueba al terminar:
- que no se llamó a ninguna orden prohibida;
- que ninguna orden registrada arranca o toca generadores, servicios, muestreadores o herramientas del ensayo;
- que **ningún fichero previo** de `~/cf-e4` cambió ni desapareció: `paquete-a12deae`, `paquete-ae2900e`, sus tgz,
  `4a/evidencia.log` y los registros de intentos anteriores.

| Ejecución | Resultado | Salida |
|---|---|---|
| r2, usuario 65534 | **33 pasan**, 0 fallan | `banco/banco-r2-65534.txt` |
| r2, root | **33 pasan**, 0 fallan | `banco/banco-r2-root.txt` |
| Anterior, 65534 | **32 fallan**, 1 pasa: **18 por éxito falso** (oculta el fallo), 14 de contrato | `banco/banco-anterior-65534.txt`, `clasificacion-anterior.txt` |
| `--solo-construir` en el portátil (Git Bash) | rc 0: 480 ficheros, `SUMAS` `8480f0e0…`, igual que en Linux. **No copia nada** | `banco/solo-construir-portatil.txt` |

Las 14 «de contrato» son pruebas en las que la anterior ya devolvía rc ≠ 0, o le faltaba el mecanismo nuevo (marca,
códigos, `YA_VERIFICADO`, restos `.parcial`). Su fallo **no** es éxito falso.

Casos cubiertos (r2: rc obtenido):
- copia correcta en cada host (0) y en los tres (0, «TRASLADO COMPLETO 3/3»);
- fallo de scp al bastión (4), a Sensor1 (6) y a srv-dmz (6);
- fallo de ssh al bastión (5) y a Sensor1 (6);
- tgz truncado en el host (4) y en la transferencia (6, con el host en 4);
- extracción fallida (5);
- fichero alterado, ausente o inesperado (6);
- evaluador distinto (7);
- manifiesto de E-carga distinto (8);
- versión incorrecta (9);
- destino existente, o marca de otro paquete (3);
- aviso no creable (11);
- un host bien y otro mal (6);
- limpieza fallida en el host (6, el original) y en el portátil (6, el original);
- referencia Git inaccesible (2, sin ningún ssh ni scp);
- reintento tras una copia parcial (0, con `YA_VERIFICADO` en los ya hechos);
- destino sin marca (6, y 0 tras apartarlo);
- restos de un intento interrumpido (0, sin tocarlos);
- paquete ya verificado que se altera después (6).

**Límites del banco.** Los dobles reproducen los códigos de ssh y scp (255, 1) y una copia truncada con rc 0. No
reproducen la red real, las claves, `known_hosts`, el espacio en disco ni la latencia. El guion principal se probó en
Linux, y en el portátil solo en modo `--solo-construir`. Todo eso queda para el estado 2.

## 3. Códigos de salida

**`paquete_902991e.sh` (portátil):**

| rc | Significado | ¿Se puede seguir? |
|---|---|---|
| 0 | TRASLADO COMPLETO: bastión, Sensor1 y srv-dmz verificados (3/3) | Sí: es la única salida que permite pasar a P0 |
| 2 | PRECONDICION: uso, repositorio, `git fetch`, o `902991e` ausente o no publicado | No; no se copió nada |
| 3 | CONSTRUCCION: el paquete no supera la verificación local | No; no se copió nada |
| 4 | TRANSFERENCIA_AL_BASTION: scp del paquete o de `op_host` | No; ningún host preparado |
| 5 | SSH al bastión fallido, o sin resultados interpretables | No; estado de los hosts desconocido (comprobar §6) |
| 6 | TRASLADO INCOMPLETO: algún host no verificado (se listan) | No; recuperación según §4 |

**`reparto_bastion_902991e.sh`** (una línea `RESULTADO <host> rc= estado=` por host; rc 0 solo con 3/3):
- 30 `SCP_FALLIDO`;
- 31 `FICHEROS_AUSENTES_EN_BASTION`;
- 32 `TGZ_DISTINTO_EN_BASTION`;
- 96 `USO_REPARTO`;
- 97 `INCOHERENTE`;
- 98 `SIN_ESTADO_FINAL`;
- 255 `SSH_FALLIDO`;
- y los de `op_host`.

**`op_host_902991e.sh`** (última línea `<host>: ESTADO_FINAL=<estado> rc=<n>`):

| rc | Estado | Qué queda en el host |
|---|---|---|
| 0 | `VERIFICADO` / `YA_VERIFICADO` | `paquete-902991e/` + `paquete-902991e.VERIFICADO.txt` + aviso junto a `paquete-a12deae` |
| 2 | `USO` / `PRECONDICION` | nada nuevo, salvo quizá el registro |
| 3 | `DESTINO_EXISTE` | lo que ya había, sin tocar |
| 4 | `TGZ_AUSENTE` / `TGZ_DISTINTO` / `COPIA_LOCAL` | solo el registro |
| 5 | `EXTRACCION` | solo el registro |
| 6 | `INVENTARIO_INVALIDO` | solo el registro (o el paquete existente, sin tocar, si era una re-verificación) |
| 7 | `EVALUADOR_DISTINTO` | solo el registro |
| 8 | `MANIFIESTO_ECARGA_DISTINTO` | solo el registro |
| 9 | `VERSION_INCORRECTA` | solo el registro |
| 10 | `INSTALACION` / `INSTALADO_SIN_MARCA` | `paquete-902991e/` **sin marca**: **no utilizable** |
| 11 | `AVISO_FALLIDO` | paquete verificado y marcado, pero el host **no** cuenta como completo |

Si falla la limpieza, `.paquete-902991e.parcial.<RUN>` (oculto, nunca utilizable) o el tgz de `/tmp` pueden quedar.
Se registran como `limpieza-* rc≠0` y el código no cambia.

## 4. Recuperación de una copia parcial

Regla: **solo es utilizable `~/cf-e4/paquete-902991e` con `paquete-902991e.VERIFICADO.txt` que contenga
`SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c`, y solo si el principal terminó con rc 0.**
Nada se borra ni se sobrescribe: los registros de cada intento (`traslado-902991e.<RUN>.<host>.log`) se conservan.

1. **Conservar la transcripción** del intento fallido, con su rc.
2. **Por host, según su `RESULTADO`:**
   - **rc 0:** nada que hacer. En el reintento sale `YA_VERIFICADO`: se re-verifica entero y no se modifica.
   - **rc 2, 4, 5, 6, 7, 8, 9 o 30–32:** no quedó paquete. Revisar la causa (red, espacio, origen del paquete).
   - **rc 3 (`DESTINO_EXISTE`) o 10:** hay un `paquete-902991e/` sin marca coincidente. **Apartarlo sin borrarlo**:
     `mv ~/cf-e4/paquete-902991e ~/cf-e4/paquete-902991e.RETIRADO-<fecha>`, junto con la marca si la hubiera. Anotarlo.
   - **rc 11:** paquete verificado. Revisar qué ocupa `paquete-a12deae.NO-USAR.txt` (no se toca) y resolverlo antes de
     reintentar.
   - **255 o 5:** comprobar a mano (§6) qué quedó.
3. **Restos `.paquete-902991e.parcial.*`:** no son utilizables y el reintento no los toca; los informa como
   `restos-previos`. Se pueden examinar y retirar a mano después, dejando constancia.
4. **Reintentar el mismo comando** (§5). Cada intento usa un RUN nuevo. Los hosts ya verificados se re-verifican; los
   demás se copian de cero. Solo rc 0 (3/3) da el traslado por completo.

Estos pasos de recuperación (`mv` en los hosts) también son escrituras remotas: necesitan la misma autorización que la
copia.

## 5. Comando futuro de copia — **NO EJECUTADO**

Solo tras autorización explicita y separada. Se ejecuta desde la carpeta publicada, comprobando antes su
`SHA256SUMS`:

```bash
# [LAPTOP Git Bash markp] → NO EJECUTADO. Requiere autorización explícita de Mark (escritura remota en 3 hosts).
cd "/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4a-pendientes-2026-11-06/ecarga-v2-preparacion/traslado-902991e-r2"
sha256sum -c --strict --quiet SHA256SUMS || exit 1
bash paquete_902991e.sh > "$HOME/traslado-902991e-$(date -u +%Y%m%dT%H%M%SZ).txt" 2>&1; echo "rc=$?"
```

El rc se toma de `bash` directamente, no de una tubería con `tee`. Solo `rc=0` y la línea `RESULTADO_GLOBAL rc=0
TRASLADO COMPLETO` dan la copia por hecha. La transcripción se publicará como evidencia del estado 2.

## 6. Comprobaciones que confirmarán la copia en cada host (estado 2; solo lectura)

```bash
# [BASTIÓN gadmin], [SENSOR1 m4rk] y [SRV-DMZ adminsrvdmz] → NO EJECUTADO; tras la copia autorizada, en cada host
cd ~/cf-e4
grep -x 'SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c' paquete-902991e.VERIFICADO.txt
(cd paquete-902991e && sha256sum SHA256SUMS && sha256sum -c --strict --quiet SHA256SUMS && echo hashes-OK)
diff <(sed -E 's/^[0-9a-f]{64}  //' paquete-902991e/SHA256SUMS | LC_ALL=C sort) \
     <(cd paquete-902991e && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort) && echo inventario-exacto
sha256sum paquete-902991e/deploy/etapa4/sensor1/evaluar_ecarga.py paquete-902991e/deploy/etapa4/ecarga/SHA256SUMS
(cd paquete-902991e/deploy/etapa4/ecarga && sha256sum -c --strict --quiet SHA256SUMS && echo ecarga-OK)
grep -x 'VERSION = "evaluar_s14 2026-11-06.2"' paquete-902991e/deploy/etapa4/ecarga/evaluar_s14.py
grep -x 'VERSION = "construir_entrada 2026-11-06.3"' paquete-902991e/deploy/etapa4/ecarga/construir_entrada.py
cat paquete-a12deae.NO-USAR.txt; ls -d .paquete-902991e.parcial.* 2>/dev/null; tail -1 traslado-902991e.*.log
```

Esperado en cada host:
- `SHA256SUMS` interno `8480f0e0…`, `hashes-OK` e `inventario-exacto` (480 ficheros);
- evaluador `53e9f7bd…`, `ecarga/SHA256SUMS` `e001352c…` y `ecarga-OK`;
- las dos líneas `VERSION`;
- el aviso que nombra `paquete-902991e`;
- ningún `.parcial` nuevo;
- un registro con `ESTADO_FINAL=VERIFICADO rc=0` (o `YA_VERIFICADO`).

Además, `paquete-a12deae/` y los demás paquetes anteriores deben seguir intactos. La comprobación P0 (protocolo r4
§3.5, puntos 10–13) es aparte: es el estado 3.

## 7. Estados (separados)

| # | Estado | ¿Completado? |
|---|---|---|
| 1 | **Guiones corregidos y probados en banco** | **Sí**: r2 33/33 (65534 y root). La anterior oculta el fallo en 18 casos. Con los límites de §2 |
| 2 | Paquete copiado y verificado en el laboratorio | **No.** Comando sin ejecutar (§5). En los hosts solo hay `paquete-a12deae`, que no se usa |
| 3 | Preparación comprobada mediante P0 | **No** |
| 4 | E-carga ejecutada y evaluada | **No.** Ni ejecutada ni programada |
