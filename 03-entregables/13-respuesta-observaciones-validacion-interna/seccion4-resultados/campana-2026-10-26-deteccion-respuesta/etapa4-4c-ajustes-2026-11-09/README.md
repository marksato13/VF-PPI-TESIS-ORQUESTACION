# Ajustes de la 4C (09-nov-2026): `g01` v2 y `s40` v3

**Estado: preparados y probados en banco; commit local; NO publicados, NO desplegados en ningún host, NO usados.** La publicación y el inicio de la Campaña A los confirma Mark por separado.

## Por qué
El sudoers de `m4rk` en el Sensor1 solo permite `/usr/bin/journalctl --no-pager *` (con `--no-pager` primero). Dos guiones de la 4B/4C usaban otra forma:
- **`s40` v2** extraía `salud/tcpdump-anillo.log` y `salud/tcpdump-via.log` con `sudo -n journalctl -u … -o short-iso-precise --no-pager`: sudo pidió contraseña y ambos quedaron vacíos en la 4B (se recuperaron sin sudo con `s40b`).
- **`g01`** lanza el vigía de la 4C sin `--journalctl`, o sea con `sudo -n journalctl -u ppi-motor-capture …`. Probado con el `vigia_4c.py` real del Sensor1: `tcpdump: ok false, journalctl rc=1: sudo: a password is required`, que en el vigía es **P4** («lecturas SIGUSR1 no disponibles», `vigia_4c.py` líneas 222–224): pausa desde el primer permiso.

## Qué cambia
| Guion | Cambio (única diferencia de código frente a la versión anterior) | sha256 |
|---|---|---|
| `guiones/g01_lanzar_bateria_e4.sh` v3 | (1) `OS=` añade `--journalctl 'sudo -n journalctl --no-pager'`; (2) la comprobación «ya hay un generador» pasa de `pgrep -fc 'generar_campana.py --config'` a `pgrep -fc '[g]enerar_campana.py --config'` (la original se contaba a sí misma dentro del `bash -c` remoto y paraba `g01` con «PARAR: ya hay un generador» sin ningún generador; ocurrió en el primer intento real, 09-nov 03:46 Perú, ver `evidencia/g01-primer-intento-parar-generador.txt`) | `05b729ebe5cefed543eadceb4a8aa0bf0d9e3fc7511de3f8922c5f296af4d0c2` |
| `guiones/s40_cierre_e4.sh` v3 (parte de `s40` v2 de `etapa4-4b-enmienda-p1-2026-11-08`) | las dos extracciones pasan a `jtcp`: `journalctl --no-pager -u … -o short-iso-precise` **sin sudo**, con respaldo `sudo -n journalctl --no-pager …`, y **se verifica cada log por separado**: rc=0, no vacío, lecturas SIGUSR1 completas (sin truncar), de procesos del **cgroup de su unidad** (anillo = tcpdump de `ppi-motor-capture`; vía = hijo de `ppi-via-rapida@ens37`), y cobertura de la ventana (primera lectura ≤ inicio del archivo + 40 s, última ≥ `cierre.t` − 60 s); los dos logs no pueden ser idénticos. Cualquier fallo = FALLO (→ `COPIAS INCOMPLETAS`, sin `SHA256SUMS` ni `COPIAS-COMPLETAS.ok`) | `d7c13bef6ac9d158978db123a8372801fcb987f1fa9b8a6b1712cb2687261546` |

`s40b` se conserva como recurso de reserva.

## Pruebas (`tests/test_ajustes_4c.py`, 15 OK; `evidencia/pytest-ajustes-4c.txt`)
- Stubs con el sudoers real y un escenario de 4 h de lecturas cada 30 s con un cgroup por unidad: `s40` v2 reproduce el fallo de la 4B (`COPIAS INCOMPLETAS (2 fallos)`, ambos logs de 0 B); `s40` v3 completa, con ambos logs cubriendo la ventana; con el respaldo en `sudo -n --no-pager` también completa; con `journalctl` fallido, log vacío, sin lecturas, lecturas truncadas, lecturas del PID de otra unidad, vía que no cubre el inicio o anillo que no cubre el final, **no** escribe la marca.
- `s40` v3 solo cambia las extracciones de tcpdump; `g01` v2 solo cambia `OS=` (y comentarios).
- Con el `vigia_4c.py` real del Sensor1 (`62260830…`, verificado contra el `SHA256SUMS` del paquete): la orden de `g01` v1 da `tcpdump ok false`; la de `g01` v2 da `ok true` con las lecturas del PID 1355 y 0 descartes.
- **Mutaciones** (`evidencia/mutaciones.txt`): sin el respaldo con sudo (1 de 1), sin la verificación de cobertura/unidad/truncado (5 de 5) o con `g01` v2 = v1 (1 de 1), las pruebas **fallan**; sin mutar, pasan. Quitar solo la comprobación de «log vacío» no hace fallar nada: es un mutante equivalente, porque la verificación de cobertura ya rechaza un log sin lecturas. Una primera versión de las pruebas dejaba sin probar la comprobación de PID por unidad (los stubs producían logs idénticos y otra comprobación los atrapaba); se corrigió.

## Lectura real en solo lectura (`evidencia/lectura-real-bastion-vigia.txt`)
Desde el bastión, la orden del sensor del vigía por `ssh sensor1`, con las carpetas de la 4B porque `~/cf-e4/4c` aún no existe: `g01` v1 → `tcpdump ok=False | sudo: a password is required`; `g01` v2 → `ok=True | 5 lecturas SIGUSR1 | PID 1355 | descartados_kernel 0`.

## Límites
No se probó la batería completa ni se ejecutó `g01` v2 (necesita la Kali y el control declarado). El `vigia_4c.py` del repositorio del producto (`2fe00200…`) **no es** el del paquete que corre en el Sensor1 (`62260830…`); se probó el del Sensor1.
