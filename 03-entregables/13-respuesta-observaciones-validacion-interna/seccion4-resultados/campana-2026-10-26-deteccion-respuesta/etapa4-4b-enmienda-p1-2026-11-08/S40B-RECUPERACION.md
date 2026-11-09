# s40b: recuperación de las dos extracciones de tcpdump tras el s40 v2 (09-nov-2026)

**Estado: ejecutado una vez en el Sensor1 (09-nov 03:21:57Z, rc 0), autorizado por Mark. Commit local para revisión; sin publicar en GitHub.**

## Qué pasó
`s40` v2 terminó el 09-nov a las 03:01:18Z con `COPIAS INCOMPLETAS (2 fallos)`. Solo fallaron las dos extracciones del journal de `tcpdump` (`salud/tcpdump-anillo.log`, `salud/tcpdump-via.log`): usaban `sudo -n journalctl … -o short-iso-precise`, forma que el sudoers de `m4rk` no permite. Ambos archivos quedaron con 0 bytes. El `s40` v1 original tenía las mismas dos líneas sin comprobar y los habría dejado vacíos en silencio.
Todas las demás copias se hicieron y sus tamaños quedaron en `copias/FUENTES-al-copiar.tsv`.

## Qué hace `guiones/s40b_completar_copias_e4.sh` (sha256 en `guiones/s40b_completar_copias_e4.sha256`)
No repite nada de `s40`: no toca `cierre.t`, no para ni arranca procesos, no vuelve a copiar fuentes, no usa sudo. Se ejecuta **una vez** (`copias/s40b-ejecutado.txt`).
Precondiciones (si falla alguna, `PARAR` rc 2 sin escribir nada): hay `cierre.t` y `archivo-pcap.rc` = 0; existe `COPIAS-INCOMPLETAS.txt` y menciona **solo** esas dos extracciones; no hay `COPIAS-COMPLETAS.ok` ni `SHA256SUMS`; los dos logs están vacíos.
Solo escribe `COPIAS-COMPLETAS.ok` y `SHA256SUMS` si, **por separado**:

1. `journalctl -u <unidad> --since <inicio del archivo − 120 s> -o short-iso-precise` termina con rc=0 para cada unidad;
2. la extracción no está vacía; todas sus lecturas SIGUSR1 (una línea con `captured`, `received by filter` y `dropped by kernel`) pertenecen a procesos del **cgroup de su unidad** (`ppi-motor-capture` → tcpdump[1355]; `ppi-via-rapida@ens37` → bash[1389], hijo del servicio) y no hay lecturas truncadas; los dos archivos no son idénticos;
3. cubre la ventana requerida: primera lectura ≤ inicio del archivo + 40 s y última ≥ `cierre.t` − 60 s (los huecos se informan, no bloquean: los clasifica `s50` como C3);
4. las copias de `s40` siguen cubriendo `FUENTES-al-copiar.tsv` y empiezan por los bytes de su fuente.

Los hashes de los dos logs quedan **aparte**, en `salud/SHA256SUMS-tcpdump`, fuera de `copias/SHA256SUMS`. La evidencia del fallo se conserva en `copias/s40-fallido/` (`COPIAS-INCOMPLETAS.txt`, `estado-antes.txt`, `extraccion.txt`) y el original `copias/COPIAS-INCOMPLETAS.txt` no se toca. `copias/COPIAS-RECUPERADAS-s40b.txt` explica la recuperación.

## Pruebas (banco, usuario 65534, sin red)
`tests/test_s40b.py`, **17 pruebas OK**. El escenario previo es real: se ejecuta `s40` v2 con un `sudo` falso que rechaza esa forma y se comprueba que da `COPIAS INCOMPLETAS (2 fallos)`. Casos: recuperación correcta (logs con contenido, hashes aparte que verifican y no están en `copias/SHA256SUMS`, `cierre.t` y copias intactos, evidencia conservada); **extracción vacía** (anillo, vía), **journalctl con rc≠0** (anillo, vía), vía con lecturas del anillo, dos logs idénticos, no cubre el inicio, no cubre el final, lecturas truncadas, copia ya tomada alterada → en todos: rc 1, **sin** `COPIAS-COMPLETAS.ok` ni `SHA256SUMS`, logs como estaban y sin temporales; un hueco se informa pero no bloquea; otros fallos distintos de las dos extracciones → no se ejecuta; sin `s40` fallido → no hace nada; **una sola vez**; ya completas → no hace nada; logs con contenido → no se pisan.
Además, el verificador embebido se probó contra una copia de lectura del journal **real** del Sensor1 antes de ejecutar: 1216 lecturas por unidad, PID 1355 (anillo) y 1389 (vía), hueco máximo 30,9 s, 0 descartes; y la prueba cruzada (vía contra los PID del anillo) se rechaza. Esa prueba corrigió dos supuestos míos del formato: una lectura es **una línea** y la vía se etiqueta `bash[PID]`.

## Resultado real (Sensor1, `evidencia-pendiente/4b-cierre/`)
`s40b` rc 0 → `COPIAS COMPLETAS`; `cf-4b-rotacion cierre` → `RESULTADO_CIERRE OK`; el vigía registró `REANUDADO_NORMAL` a las 03:22:13Z (`logrotate.timer` activo; tope y vigía retirados).
Hashes aparte: `tcpdump-anillo.log` `b64cf99f…`, `tcpdump-via.log` `d29c13b6…` (completos en `salud/SHA256SUMS-tcpdump`).
Efecto esperado de la reanudación: al reanudar `logrotate.timer` con `Persistent=true` se ejecutó la rotación diaria pendiente, de modo que las **fuentes vivas** están rotadas; las copias ya estaban tomadas.
