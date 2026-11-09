# Ajustes de la 4C (09-nov-2026): `g01` v2 y `s40` v3

**Estado: preparados y probados en banco; commit local; NO publicados, NO desplegados en ningún host, NO usados.** La publicación y el inicio de la Campaña A los confirma Mark por separado.

## Por qué
El sudoers de `m4rk` en el Sensor1 solo permite `/usr/bin/journalctl --no-pager *` (con `--no-pager` primero). Dos guiones de la 4B/4C usaban otra forma:
- **`s40` v2** extraía `salud/tcpdump-anillo.log` y `salud/tcpdump-via.log` con `sudo -n journalctl -u … -o short-iso-precise --no-pager`: sudo pidió contraseña y ambos quedaron vacíos en la 4B (se recuperaron sin sudo con `s40b`).
- **`g01`** lanza el vigía de la 4C sin `--journalctl`, o sea con `sudo -n journalctl -u ppi-motor-capture …`. Probado con el `vigia_4c.py` real del Sensor1: `tcpdump: ok false, journalctl rc=1: sudo: a password is required`, que en el vigía es **P4** («lecturas SIGUSR1 no disponibles», `vigia_4c.py` líneas 222–224): pausa desde el primer permiso.

## Qué cambia
| Guion | Cambio (única diferencia de código frente a la versión anterior) | sha256 |
|---|---|---|
| `guiones/g01_lanzar_bateria_e4.sh` v2 | `OS=` añade `--journalctl 'sudo -n journalctl --no-pager'` | `861c064c6b768652db47ee6de4537524788af26100497f128b9dc5350ab8f017` |
| `guiones/s40_cierre_e4.sh` v3 (parte de `s40` v2 de `etapa4-4b-enmienda-p1-2026-11-08`) | las dos extracciones pasan a `jtcp`: `journalctl --no-pager -u … -o short-iso-precise` **sin sudo**, con respaldo `sudo -n journalctl --no-pager …`, y el log debe traer `packets captured`; vacío, rc≠0 o sin lecturas = FALLO (→ `COPIAS INCOMPLETAS`, sin `SHA256SUMS` ni `COPIAS-COMPLETAS.ok`) | `b5790fe3219afe5cf1b1f36a87e3073484dca02022f878782d1b4c9481d7aade` |

`s40b` se conserva como recurso de reserva.

## Pruebas (`tests/test_ajustes_4c.py`, 9 OK; `evidencia/pytest-ajustes-4c.txt`)
- Stubs con el sudoers real: `s40` v2 reproduce el fallo de la 4B (`COPIAS INCOMPLETAS (2 fallos)`, ambos logs de 0 B); `s40` v3 completa, con ambos logs con lecturas; con el respaldo en `sudo -n --no-pager` también completa; con `journalctl` fallido, vacío o sin lecturas **no** escribe la marca.
- `s40` v3 solo cambia las extracciones de tcpdump; `g01` v2 solo cambia `OS=` (y comentarios).
- Con el `vigia_4c.py` real del Sensor1 (`62260830…`, verificado contra el `SHA256SUMS` del paquete): la orden de `g01` v1 da `tcpdump ok false`; la de `g01` v2 da `ok true` con las lecturas del PID 1355 y 0 descartes.
- **Mutaciones** (`evidencia/mutaciones.txt`): sin el respaldo con sudo, sin la comprobación de lecturas o con `g01` v2 = v1, las pruebas **fallan**; sin mutar, pasan.

## Lectura real en solo lectura (`evidencia/lectura-real-bastion-vigia.txt`)
Desde el bastión, la orden del sensor del vigía por `ssh sensor1`, con las carpetas de la 4B porque `~/cf-e4/4c` aún no existe: `g01` v1 → `tcpdump ok=False | sudo: a password is required`; `g01` v2 → `ok=True | 5 lecturas SIGUSR1 | PID 1355 | descartados_kernel 0`.

## Límites
No se probó la batería completa ni se ejecutó `g01` v2 (necesita la Kali y el control declarado). El `vigia_4c.py` del repositorio del producto (`2fe00200…`) **no es** el del paquete que corre en el Sensor1 (`62260830…`); se probó el del Sensor1.
