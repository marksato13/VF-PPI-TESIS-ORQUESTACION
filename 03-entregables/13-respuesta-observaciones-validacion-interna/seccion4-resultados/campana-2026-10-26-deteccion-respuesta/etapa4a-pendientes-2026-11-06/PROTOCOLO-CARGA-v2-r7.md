# Protocolo E-carga v2, revisión r7: franja diurna del domingo 8 de noviembre, T_g 09:30Z (2026-11-08)

**Estado: propuesta publicada para aprobación de Mark. NO ejecutada ni programada.** Vale como protocolo solo si Mark la
aprueba en el chat antes de las 03:35 de Perú del domingo 8 de noviembre (08:35Z). Sin esa aprobación no queda ninguna franja
vigente: la r5 ya se ejecutó, con el veredicto «carga insuficiente» publicado en `e8fbd00`, y no se repite.

**Qué es.** Esta revisión repite la variante r5 (domingo, con `--forzar-laborable` en los seis perfiles, temporal y
reversible) con todos los epochs desplazados +23 400 s (6 h 30 min). La franja cae entonces en la banda 08–13Z, donde
`factor_horario` da 1,0. La r5 se conserva sin cambios como antecedente ejecutado:
[`PROTOCOLO-CARGA-v2-r5.md`](PROTOCOLO-CARGA-v2-r5.md), commit `70b945b`, resultado `e8fbd00`. La r6 (`eca1fae`) no se
ejecutó y tampoco cambia. Todo lo que este documento no cambia sigue con el texto de la r5 y, a través de ella, de la r4.

Esta revisión es la «orden nueva y otra versión del protocolo» que la r4 §5 exige para repetir. El veredicto de la r5 se
conserva tal como se publicó.

## 1. Qué cambia frente a la r5

| Punto | r5 | r7 |
|---|---|---|
| §2, franja | T_g 1794106800 (03:00Z) | T_g 1794130200 (09:30Z), con los mismos desfases |
| Base de `factor_horario` en la franja | 0,12 (banda 23–08Z), mantenida por la opción | **1,0** (banda 08–13Z), mantenida por la opción. Sin ella, en domingo, sería 0,3 |
| r4 §3.1, «ventana en 23:00–08:00 UTC» | Se mantenía | Excepción de esta revisión, solo para esta franja: ventana 09:45–10:45Z |
| r4 §3.3, fin de `salud_captura` y `obs_pcap` | 2026-11-08T04:16:00Z, epoch 1794111360 | 2026-11-08T10:46:00Z, epoch 1794134760 |
| r4 §3.4.1, tramos | 6 tramos desde 1794107700 | 6 tramos desde 1794131100 |
| r4 §3.5, punto 5 | Domingo UTC, con F2 | Igual: domingo UTC (`weekday()` 6), con F2 |
| r4 §3.5, punto 7 | `fin_utc` = 2026-11-08T04:16:00Z | `fin_utc` = 2026-11-08T10:46:00Z |
| r4 §3.5, punto 12, y §3.6.1 | Base de S14 [1794106500, 1794106800) | Base de S14 [1794129900, 1794130200) |
| Carpeta en los hosts | `ecarga-v2-ejecucion-20261108T0300Z` (ya usada) | `ecarga-v2-ejecucion-20261108T0930Z` |
| Evidencia | `evidencia/14-ecarga-ejecucion/` (publicada) | `evidencia/27-ecarga-r7-ejecucion/` |

Todos los epochs de la r5 usados en §3 se suman 23 400 s. Nada más se mueve.

**No cambian:** K1–K5 y sus umbrales (K3 sigue exigiendo 50 flujos de al menos 1 000 paquetes, contados por
`comparar_suricata.py` como hasta ahora), S1–S15 y sus umbrales, la duración de la ventana (3 600 s), el calentamiento
(900 s), λ_diseño, el orden de decisión de §4.1, `evaluar_ecarga.py` 2026-11-06.4, el detector, el modelo IF desplegado y
su umbral, las características, α, los heurísticos, la política de respuesta, el generador (`clientes_lab.py` `ae5134a7…`)
y los relojes reales del laboratorio.

## 2. Franja

La referencia es T_g = 1794130200, igual a 2026-11-08T09:30:00Z. El domingo 2026-11-08 tiene `weekday()` = 6 en UTC, y
toda la franja es también domingo en Perú.

| Paso | Epoch | UTC (dom 08-nov) | Perú (UTC−5, dom 08-nov) |
|---|---|---|---|
| Traslado ya verificado, drop-ins aplicados (F3) e inicio de la fase A | 1794126900 | 08:35:00 | 03:35:00 |
| P0, comprobación previa | 1794128400 | 09:00:00 | 04:00:00 |
| Arranque de muestreadores | 1794129600 | 09:20:00 | 04:20:00 |
| Límite P12 e inicio de la base de S14 | 1794129900 | 09:25:00 | 04:25:00 |
| T_g, arranque de generadores | **1794130200** | 09:30:00 | 04:30:00 |
| Calentamiento (no cuenta) | 1794130200–1794131100 | 09:30:00–09:45:00 | 04:30:00–04:45:00 |
| **Ventana fija** | **1794131100–1794134700** | **09:45:00–10:45:00** | **04:45:00–05:45:00** |
| Fin de `obs_pcap.py` y muestreadores de Sensor1 | 1794134760 | 10:46:00 | 05:46:00 |
| Parada de generadores | 1794134820 | 10:47:00 | 05:47:00 |
| Fin del muestreo del bastión | 1794134880 | 10:48:00 | 05:48:00 |
| Análisis de perfiles, no antes de | 1794135600 | 11:00:00 | 06:00:00 |
| Lecturas posteriores y verificadores, hasta | 1794137400 | 11:30:00 | 06:30:00 |

## 3. Por qué esta franja

**La r5 no falló por inestabilidad, sino por falta de carga medida en K3.** El diagnóstico en seco del 08-nov (solo
lectura, sin otro ensayo) encontró 37 flujos de al menos 1 000 paquetes en la ventana de la r5: 22 de los perfiles y 15 del
tráfico de fondo del bastión. Cada conexión entre VLAN aparece dos veces en EVE (VLAN 20 y 30, con distinto `flow_id`), así
que las conexiones distintas de los perfiles fueron unas 11. El comparador no se toca: los duplicados inflan la cuenta y no
explican el fallo.

**La causa probable es la base nocturna 0,12.** El EVE del martes 3 de noviembre, con los mismos perfiles y el mismo
generador, da por hora:

| Banda UTC del 03-nov | `factor_horario` | Registros ≥ 1 000 paquetes de perfiles, por hora | Conexiones sin duplicar, por hora |
|---|---:|---:|---:|
| 03–04Z | 0,12 | 44 | 22 |
| 08–12Z | 1,0 | 612 | 312 |
| 15–18Z | 0,9 | 549 | 277 |
| 19–22Z | 0,35 | 186 | 94 |

Son medidas de otro día, con fondo de día laborable. No sustituyen a K3 ni predicen el resultado: solo muestran que, con base
1,0, los perfiles generaron en el pasado bastante más de 50 registros por hora. Si en la r7 K3 no llega, el resultado vuelve a
ser «carga insuficiente» y se publica tal cual.

**Por qué las 09:30Z.** Entre las bandas con base 1,0, la de 08–13Z es la única que cabe entera hoy con todas las
verificaciones: la franja completa (fase A a lecturas) va de 08:35 a 11:30Z, y la ventana de 09:45 a 10:45Z con la parada a
las 10:47Z. Con `--forzar-laborable`, el factor es 1,0 desde T_g hasta la parada, sin cambio de banda: el siguiente cambio,
a 0,55, llega a las 13:00Z.

**Tareas programadas.** Lectura de `systemctl list-timers` y `/etc/crontab` en los cuatro hosts, a las 05:56Z del 08-nov
(solo lectura). Entre el arranque de los muestreadores (09:20Z) y el fin del muestreo del bastión (10:48Z) **no cae ninguna
tarea programada del sistema** en ningún host. Solo corren las periódicas que forman parte del régimen normal y corrían
igual en la r5: `cyberflow-acumular`, `cyberflow-limpieza`, `cf-tcpdump-estadisticas` y `sysstat-collect` en Sensor1,
`sysstat-collect` en clientes y srv-dmz, `sysvol-sync` cada 15 min en el bastión y `cron.hourly` a los :17. Fuera de esa
parte, dentro de la franja:

| Hora UTC | Host | Tarea | Fase en que cae | Efecto |
|---|---|---|---|---|
| 09:03:51 | clientes | `apt-daily` (`apt update`; el sello de la última actualización es del 07-nov 05:59Z, así que esta vez descarga listas) | P0 y A7, 41 min antes de la ventana | Unos segundos de CPU y red en clientes, sin generadores arrancados. No toca unidades ni `clientes_lab.py`; F3 y C1b lo comprueban |
| ≈ 11:15–11:20 | bastión | `francos-exportar-red` (06:15 de Lima, ± 5 min) | Fase D, después de la parada | Ninguno sobre la medida, que ya terminó |
| 11:25 | Sensor1 y bastión | `motd-news` (Sensor1); `cron.daily` (bastión, 06:25 de Lima) | Lecturas posteriores | Ninguno sobre la medida |

Fuera de la franja quedan `apt-daily-upgrade` de Sensor1 (06:34Z) y de clientes (06:48Z), `e2scrub_all` del bastión
(08:10Z), y `cron.weekly` (11:47Z) y `apt-daily-upgrade` (11:53Z) del bastión, después de las lecturas. srv-dmz tiene
`apt-daily` y `apt-daily-upgrade` desactivados. La lectura se repite, informativa, al empezar la
fase A (A0c). Si entonces alguna tarea cayera entre las 09:20 y las 10:48Z, se avisa a Mark antes de la puerta G. `e2scrub_all` no vuelve hasta el
domingo 15. Los temporizadores propios de CyberFlow cada 5 o 10 min (`cyberflow-acumular`, `cyberflow-limpieza`,
`cf-tcpdump-estadisticas`, `sysstat-collect`) son parte del régimen normal y corrían igual en la r5. `logrotate` (00:00Z) y
`cyberflow-aprendizaje` (00:30Z) ya pasaron.

**Lo que no se sabe.** El 3 de noviembre y en la r5, las descargas grandes dejan ver unos 5 paquetes y unos 1 000 bytes del
servidor hacia el cliente. La causa está sin determinar. No cambia cómo cuenta K3 ni ningún umbral. Se declara como
observación abierta.

## 4. Condiciones para contar como E-carga formal y abrir la 4B

Las de la r5, con su nombre:

| # | Condición | Evidencia |
|---|---|---|
| F1 | Mark aprueba esta r7 en el chat, y su commit llega a main antes de T_g | Orden del chat, y P8 r7 con el registro de pushes de GitHub |
| F2 | Las seis unidades tienen exactamente el argv de la variante antes de la fase A | `comprobar_forzar.sh con` (F3 y A3c): argv exacto, drop-in único y `clientes_lab.py` `ae5134a7…` |
| F3 | Los seis procesos corren con ese argv tras T_g | `comprobar_forzar.sh vivo`, durante el calentamiento |
| F4 | Se cumplen sin cambios P0, P8, P12, puerta G, C1, ventana y parada | Mismas evidencias del procedimiento |
| F5 | El veredicto sale de `evaluar_ecarga.py veredicto` sin tocar ningún dato ni umbral | `veredicto.json`, `trazabilidad.json` |
| F6 | Relojes reales. Sin `faketime`, sin cambiar la zona horaria y sin tocar NTP | Lecturas de P0 y `eventos.log` |
| F7 | La opción se retira antes de la 4B y la retirada se comprueba | `comprobar_forzar.sh sin`, antes de pedir la 4B |
| F8 | Nada de esta franja se usa para entrenar, calibrar ni fijar umbrales | Declaración en la publicación |
| F9 | La publicación dice «variante r7, domingo diurno (T_g 09:30Z) con factor de laborable forzado en los seis perfiles» | README de la evidencia |

**Qué abre.** Con F1–F9 y el veredicto «estable con carga suficiente», se cumple la condición (3) del criterio de avance.
No inicia la 4B: sigue haciendo falta la petición expresa de Mark.

**Qué no abre.** Si falla alguna de F1–F9, la franja se conserva y se publica como **ensayo técnico**, no como E-carga formal.
Un fallo de F2 o F3 antes de la ventana detiene la ejecución.

**Un veredicto adverso cuenta.** La r4 §5 sigue aplicando: se publica tal cual, y repetir exige otra orden y otra versión.

## 5. Lo que esta variante no demuestra

Además de lo declarado en la r4 §6 y la r5 §5:
- no demuestra estabilidad con la base nocturna 0,12, que la r5 midió con carga insuficiente;
- no demuestra estabilidad con el tráfico de fondo de un día laborable: el fondo es el de un domingo por la mañana;
- la estabilidad queda demostrada, si sale, para esta franja y esta carga medida.

## 6. Aplicación y reversión

Igual que la r5: drop-ins de systemd, sin editar unidades ni generador. La aplicación (F2) y la retirada (R) piden contraseña
de sudo y las ejecuta Mark. La copia de `forzar_laborable.sh` que ya está en clientes (`~/cf-e4/variante-r5/`) se reutiliza
tras comprobar su sha256. Los comandos están en
[`ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r7.md`](ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r7.md).
