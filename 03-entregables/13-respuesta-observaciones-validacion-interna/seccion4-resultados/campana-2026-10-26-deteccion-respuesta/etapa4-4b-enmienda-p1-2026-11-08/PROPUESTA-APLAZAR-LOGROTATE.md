# Propuesta v2: aplazar la rotación diaria de las 00:00Z (19:00 de Perú) hasta cerrar la corrida (08-nov-2026)

**Estado: PROPUESTA corregida y probada en banco. No se aplicó nada en ningún host.** Sustituye a la v1, que tenía un tope **relativo**
(4,5 h desde el momento de aplicarla: aplicada a las 10:55 reanudaba a las 15:25, antes de las 19:00, y la rotación habría caído dentro del control).
La aplicación del cambio y el inicio de la 4B van por orden separada de Mark.

## 1. Qué se corrigió

| Defecto de la v1 | Corrección |
|---|---|
| Tope **relativo** (`540 × 30 s` desde que se aplica) | Tope **absoluto**: un temporizador transitorio `cf-4b-tope.timer` con `--on-calendar` de fecha y hora UTC fijas. Regla: `tope = hasta + 5 h` (≥ 3 h por encima de un replay el doble de lento que el estimado) |
| El aplazamiento se hacía a la vez que se armaba la reanudación | **Primero** se arma y se **verifica** la recuperación; **solo después** se para `logrotate.timer`; si cualquier verificación falla, no se para (y si falla tras parar, se revierte) |
| Reanudaba al aparecer un fichero | La reanudación **normal** exige el **cierre exitoso** de la corrida y **copias verificadas** (§4) y **ausencia de rotación** (§5); sin eso, solo reanuda el tope |
| Se comprobaba la rotación por el inodo | §5: inodo, tamaño, hash de los primeros bytes, ficheros rotados y ejecuciones de systemd |

## 2. Por qué no se puede aislar solo `eve.json` (sin cambios respecto a la v1)

Comparte bloque con `stats.log`, `fast.log` y `suricata.log` (`sharedscripts`, `copytruncate`); en la misma ejecución se renombra `motor_decision.log`
y se vacían `feed-v2/*.jsonl`, que `s40` copia al final. Los bloques `cyberflow` y `cyberflow-etapa4` son generados («NO editar a mano»).
Por eso se aplaza toda la ejecución diaria de `logrotate`, con reanudación automática.

## 3. Qué hace `cf-4b-rotacion` (`herramientas/cf_4b_rotacion.py`, sha256 `11a923240f510ab2…`)

| Subcomando | Qué hace |
|---|---|
| `armar --tope EPOCH` (root) | 1) línea base en `/var/lib/cf-4b-rotacion/base.json`; 2) arma `cf-4b-tope.timer` (absoluto) y `cf-4b-vigia.service`; 3) **verifica** que el tope armado coincide (±5 s) y que el vigía sigue activo; 4) solo entonces `systemctl stop logrotate.timer`, comprueba que paró y que no disparó; 5) escribe `parado.json`. Cualquier fallo: revierte (arranca el timer y retira las unidades) y sale con 3 |
| `comprobar` (solo lectura) | §5 |
| `cierre` (solo lectura) | §4 |
| `vigilar` (lo lanza `armar`) | Espera `parado.json`; cada 30 s: si cierre **y** comprobar dan OK, arranca el timer y se retira; en el tope arranca el timer pase lo que pase; si el timer ya estaba activo (alguien lo arrancó), termina sin tocar nada |
| `reanudar-tope` | Lo lanza el temporizador absoluto: arranca el timer si sigue parado (idempotente) |
| `desarmar` (root) | Manual: arranca el timer y retira las unidades |

## 4. «Cierre exitoso con copias verificadas» (reanudación normal)

Todo esto debe cumplirse a la vez:
1. `replay/rc.txt` empieza por `rc=0`; existe `cierre.t` (`s40` empezó);
2. `archivo-pcap.rc` = 0 y `copias/archivador-ESTADO.txt` empieza por `OK`; `copias/archivar.log` sin `FALLO` ni `PERDIDO`;
3. `copias/SHA256SUMS` existe, **cada fichero listado verifica** y están listados los imprescindibles: `motor_decision.log`, `ciclos.jsonl`, `eve-segmento.json`, `stats-fin.log`, `muestras.jsonl`, `archivar.log`, `archivador-ESTADO.txt`, `servicios-fin.txt`, `sha256-feed-final.txt`, `feed-v2/feed.json`, `feed-v2/via-rapida-resumen.jsonl`, `feed-v2/traza.jsonl`;
4. la copia del motor no es menor que la línea base y el segmento EVE no está vacío.

Esto decide solo si ya es **seguro dejar rotar**, no si la 4B fue válida (un AVISO de servicios de `s40` no lo impide; el análisis lo trata como C3).

## 5. Comprobación de rotación (más que el inodo)

Para `eve.json`, `stats.log`, `motor_decision.log`, `_state-e4/ciclos.jsonl` y `feed-v2/{via-rapida-resumen,traza,senales-if,senales-rapidas}.jsonl`:
mismo inodo; tamaño **no menor**; hash de los **primeros N bytes** (N = min(tamaño de la base, 16 MiB)) igual al de la base (un `copytruncate` seguido de escritura, aunque iguale o supere el tamaño, lo cambia);
ningún fichero rotado nuevo ni modificado (`eve.json.*`, `stats.log.*`, `suricata.log.*`, `fast.log.*`, `motor_decision.log.*`, `feed-v2/*.jsonl.*`: 67 hoy);
y en systemd: `logrotate.service` sin ejecuciones desde la base (`InvocationID`, `ExecMainStartTimestampMonotonic`) y `logrotate.timer` sin disparos (`LastTriggerUSec*`).
Lectura real del Sensor1 (08-nov, solo lectura, script por stdin sin guardarlo): los formatos de `systemctl show` coinciden con lo previsto, la base se toma en 0,4 s y la comprobación inmediata da OK.

## 6. El cambio (lo ejecuta Mark, con su sudo, solo tras su orden; **después** de `CON_SUDO=1 verificar_srvdmz.sh` y **antes** de `s10`)

`[SENSOR1 m4rk]` → **lo ejecutas tú** (`install` y `armar` piden sudo). `<TOPE>` = epoch de `hasta + 5 h` (lo calculo y lo fijo en tu orden):
```bash
cd /home/m4rk/cf-e4/herramientas && sha256sum -c --quiet cf_4b_rotacion.sha256 \
 && sudo install -m 0755 -o root -g root cf_4b_rotacion.py /usr/local/sbin/cf-4b-rotacion \
 && sudo /usr/local/sbin/cf-4b-rotacion armar --tope <TOPE>
```
Salida esperada: `recuperación ARMADA y verificada` y `logrotate.timer PARADO`, rc 0. Con rc ≠ 0 **no se sigue** y `logrotate.timer` queda activo.
Yo verifico después (solo lectura): `logrotate.timer` inactivo, `cf-4b-tope.timer` y `cf-4b-vigia.service` activos, `comprobar` OK; y lo repito a las 18:55 y a las 19:05, y de hora en hora.

## 7. Cómo se restablece aunque se cierre mi sesión

Todo vive en systemd (root): el temporizador absoluto y el vigía no dependen de mi sesión. Si el Sensor1 se reinicia, `logrotate.timer` (`enabled`) vuelve solo.
A mano: `sudo /usr/local/sbin/cf-4b-rotacion desarmar` o `sudo systemctl start logrotate.timer`. El registro queda en `/var/lib/cf-4b-rotacion/log.txt`
(`REANUDADO_NORMAL` o `REANUDADO_POR_TOPE_SIN_CIERRE_VERIFICADO`).

## 8. Pruebas

`tests/test_cf_4b_rotacion.py`: **46 pruebas OK** (banco sin red, systemd **falso**): orden armar→verificar→parar; no se para si falla el tope, el vigía, la coincidencia del tope o si el vigía cae; reversión si el timer no para o dispara durante el stop;
tope en fecha absoluta (nunca `--on-active`); ocho formas de rotación detectadas (incluida «mismo inodo y mayor tamaño», que solo delata el prefijo); once roturas del cierre;
**copia fallida con manifiesto consistente** (truncada, sin salto final, otro contenido del mismo tamaño, vacía, `cp` cortado): `SHA256SUMS` verifica pero el cierre da FALLO por «copia fiel» y no se reanuda en normal (5 casos);
reanudación normal solo con cierre OK y sin rotación; sin cierre solo reanuda el tope; con rotación detectada no hay reanudación normal; vigía armado antes de parar no confunde «timer activo» con reanudación; idempotencia; desarmado;
y la regresión del hallazgo de §9. Registro: `evidencia-pendiente/pytest-cf-4b-rotacion.txt`.

## 9. Validación en systemd real (08-nov, Sensor1, systemd 255, gestor de **usuario** de `m4rk`, sin root)

`tests/prueba_systemd_real.sh` (salida: `evidencia-pendiente/systemd-real-prueba.txt`). Se usó una unidad de prueba `cf-prueba-logrotate.timer/.service` en su lugar, con `Persistent=true`,
y la herramienta con `CF_TIMER`/`CF_SERVICIO` apuntando a ella. **`logrotate`, `logrotate.timer` y todo el sistema quedaron sin tocar** (al final: `logrotate.timer` activo, último disparo 00:00 UTC; cero unidades de prueba; árbol de prueba borrado).

| Escenario | Resultado en systemd real |
|---|---|
| S1 · sin cierre; el elapse diario de la unidad de prueba cae con el timer parado | El `armar` real deja el tope **absoluto** (`NextElapseUSecRealtime` coincide), el vigía activo y **luego** para el timer. El elapse pasa con el timer parado: 0 ejecuciones. Al llegar el tope (15:53:22) el timer arranca solo (`REANUDADO_POR_TOPE_SIN_CIERRE_VERIFICADO`) y, por `Persistent=true`, **se ejecuta una vez la ejecución perdida** (15:53:23) |
| S2 · cierre exitoso con copias fieles | Con 40 s sin cierre sigue parado; al escribirse el cierre válido el vigía reanuda a los ~20 s, **359 s antes del tope** (`REANUDADO_NORMAL`) |
| S3 · copia fallida de `s40`, `SHA256SUMS` consistente (`sha256sum -c` OK) | `cierre` da FALLO («copia fiel de motor_decision.log: 37508 B frente a 75000 B, no empieza por los bytes de la fuente»); a los ~50 s sigue parado; solo reanuda el **tope** (`REANUDADO_POR_TOPE_SIN_CIERRE_VERIFICADO`) |

**Hallazgo (corregido):** en la primera pasada `armar` revertía siempre («logrotate.timer disparó mientras se paraba»). Un timer parado informa `LastTriggerUSec` **vacío** (verificado), y el comparador lo tomaba por un disparo.
Eso habría pasado también con el `logrotate.timer` real. Corrección: `sistema_igual` solo compara el timer si ambos lados traen valor; el disparo previo al `stop` lo cubre la comparación de ficheros (inodo, tamaño, prefijo, rotados) que ahora `armar` repite tras parar. Con el timer parado no puede haber disparos.

**Lo que esta prueba no puede decir:** que `logrotate.service` real se comporte igual con los permisos de root (solo se probó el mecanismo de timers); el `logrotate.service` real no se ejecutó. Una ejecución perdida y recuperada por `Persistent=true` rotará los logs al reanudar: es el comportamiento buscado (la rotación ocurre después de `s40`).
