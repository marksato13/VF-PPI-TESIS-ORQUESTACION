# Traslado del paquete `902991e` (estado 2): copiado y verificado en los tres hosts

Mark lanzó el traslado con los guiones r2 de `../../ecarga-v2-preparacion/traslado-902991e-r2/`
(`SHA256SUMS` comprobado antes de lanzarlo).

| Fichero | Qué es |
|---|---|
| `intento-fallido-20261106T194310Z.txt` | Primer intento, 19:43Z: **rc 2 PRECONDICION**, sin ninguna conexión |
| `traslado-902991e-20261106T194952Z.txt` | Intento válido, 19:49Z: **rc 0, TRASLADO COMPLETO 3/3** |
| `post_copia_host.sh` | Comprobación de solo lectura de §6 de `TRASLADO-PAQUETE-902991e-r2.md` |
| `post-copia-3-hosts.txt` | Su salida en el bastión, Sensor1 y srv-dmz (19:51Z) |

**Primer intento.** Se lanzó desde la carpeta de los guiones, cuya ruta pasa de 260 caracteres. `git.exe` de UCRT64
es un programa nativo de Windows y no arranca desde esa carpeta (rc 126, «path longer than allowed»). El guion lo
informó como «no es un repositorio git» porque descarta el stderr de git. Para corregirlo hace falta una revisión del
guion (r3, pendiente de autorización). No se copió nada. El intento válido se lanzó desde `~`, con la ruta absoluta
del guion.

**Resultado del intento válido** (`RUN=20261106T194952Z-10146`):
- tgz `bda65802…`, `SUMAS` `8480f0e0…`, 480 ficheros;
- evaluador `53e9f7bd…`, `ecarga/SHA256SUMS` `e001352c…`;
- `ESTADO_FINAL=VERIFICADO rc=0` en el bastión, Sensor1 y srv-dmz.

El hash del tgz depende de la fecha en que se construye. El criterio es `SUMAS`, que es el mismo que en el banco.

**Comprobación posterior** en cada host:
- marca con `SUMAS`, `hashes-OK`, inventario exacto (480), evaluador, `ecarga-OK` y las dos `VERSION`;
- aviso `paquete-a12deae.NO-USAR.txt` que nombra `paquete-902991e`;
- 0 restos `.parcial`;
- `paquete-a12deae` con su `ecarga/SHA256SUMS` `9ff24889…`, que verifica.

En Sensor1, `paquete-a12deae` tiene un fichero más que en los otros hosts:
`deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc`, de las 16:35Z. Es anterior a la copia: lo dejó
la lectura en vivo de esa tarde. Tras la copia no cambió ningún fichero de `paquete-a12deae`.

**No hecho:**
- P0 (estado 3);
- E-carga, ni ejecutada ni programada (estado 4).

No se arrancó ningún generador ni se modificó ningún servicio ni restricción.
