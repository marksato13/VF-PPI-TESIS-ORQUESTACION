# Etapa 4A: pendientes del cierre complementario (P1, P3, P4, P5) e integración en sombra (2026-11-06)

> **Veredicto.** P1, P4 y P5 están **resueltos y verificados**; P3 está **explicado, con incertidumbre declarada**; el
> instalador quedó **corregido y probado con fallos deliberados**. La integración en sombra (relé `--entrega paquete`,
> agente `--paquete`) funcionó toda la ventana fija de 60 min: **O1–O11 cumplen**. Hay tres resultados desfavorables,
> que se publican tal cual:
> 1. **O12, carga insuficiente:** 587 592 paquetes frente al umbral de 596 789. La observación **no permite concluir nada
>    sobre descartes bajo carga**; sí demuestra la medida (C0, `cero_explicito`) con la carga que hubo.
> 2. **Criterio §3 «`verificar_*.sh` sin FALLO» no cumplido tal como está escrito:** 3 FALLO en los guiones de la 4A.
>    Dos esperan **activo** el v1 que el cierre retiró a propósito; el otro busca `motor_startup` solo en el registro
>    actual, y la rotación diaria lo dejó en `.1`. Cada condición real se comprobó por otra vía (§8), pero el
>    criterio no se flexibiliza.
> 3. **Un error mío en la observación:** el verificador de PCAP tenía mal calculada la hora de fin (06:11:30Z). Siguió
>    leyendo, solo lectura, después de la ventana y lo detuve a las 05:56:25Z. No afecta a ningún dato de la ventana.
>
> **¿Está listo para iniciar el control formal de la 4B? Todavía no, por un único motivo:** el §3 sin FALLO. Para
> cerrarlo basta corregir los dos guiones de verificación, probarlos en banco y volver a ejecutarlos (solo lectura, sin
> reinstalar nada). P1 está cerrado y la integración verificada por O1–O11. La 4C y la campaña B **no** están
> autorizadas: I5 se seguirá exigiendo en los 30 min previos a la 4C, y la carga de esta hora no sirve para eso.

Petición: la de Mark del 06-nov («cierra los pendientes del cierre complementario antes de la 4B»), en siete partes, y
su corrección posterior sobre la seguridad del instalador (códigos de salida, `systemd-analyze verify`, respaldo
separado de la evidencia, reversión probada con fallos deliberados). Base: [`../etapa4a-cierre-complementario-2026-11-04/`](../etapa4a-cierre-complementario-2026-11-04/README.md).
Criterios fijados **antes** de instalar y de observar: [`CRITERIOS-FIJADOS.md`](CRITERIOS-FIJADOS.md) (commit `997c8e2`).
Mark ejecutó el único paso con sudo con contraseña (bastión); nunca se pidió ni se registró la contraseña.

No se inició la 4B, la 4C ni la campaña B. No hubo ataques, generadores ni restricciones. No se cambiaron las 28
features, el modelo, los umbrales α, las reglas ni la política `if_senal`; no se reentrenó; no se tocó el Word.

## 1. Versiones y hashes

| Qué | Valor |
|---|---|
| Código congelado de la 4A (Sensor1) | `ec78ca5`, `SHA256SUMS` OK antes y después |
| Modelo / manifiesto / esquema de features | `df547da0…` / `b3ad6805…` / `e032a1a2…` (iguales antes y después, §8 O11) |
| `suricata.yaml` | `0962ce68…` (`ring-size: 16384`, sin cambios) |
| Rama de pendientes (producto) | `recuperacion/etapa4a-pendientes-20261106`: `313f8f8` (P1, P4, P5) → **`b18c286`** (instaladores endurecidos) sobre `ce353ef` |
| Instalador | `p4-instalador 2026-11-06.2` (`p4_comun.sh` `d0073ec9…`, `bastion_p4.sh` `c26e21b6…`, `srvdmz_p4.sh` `e4a5fc11…`) |
| Paquete instalado | `~/cf-e4/paquete-b18c286` en bastión, srv-dmz y Sensor1: tgz `520b7bc5…`, `SHA256SUMS` interno `e0e72e23…`, verificado en los tres |
| Herramientas de medida en Sensor1 (sin sudo) | `~/cyberflow-e4/herramientas-20261106`: `salud_captura.py` `274b4d61…` (VERSION `2026-11-06.1`), `clasificar_periodo.py` `65af5e53…`, `vigia_4c.py` `2fe00200…`, `evidencia.sh` `ead0eab0…` (del paquete `313f8f8`; `b18c286` no las cambia) |
| Bastión instalado | `relay_eventos.py` `d21a3da2…`, `feed.py` `c41be50e…`, `pub.pem` `7ce39571…`, unidad `e7f89e15…` (`--entrega paquete`) |
| srv-dmz instalado | `agente_enforce_v2.py` `7884a6ba…`, `feed.py` `c41be50e…`, `pub.pem` `7ce39571…`, `cf-feed-ssh.sh` `c5701056…`, `cf-nft-helper` `3ba6374f…` (sin cambios), unidad `80e9aa62…` (`--paquete`) |

## 2. Matriz: pendiente → corrección → prueba → resultado → evidencia

| # | Pendiente (cierre 4A §11) | Corrección | Prueba | Resultado | Evidencia |
|---|---|---|---|---|---|
| **P1** | I5/C0 no demostrables: Suricata 7 omite los ceros en `stats.log` | `salud_captura` 2026-11-06.1 mide Suricata con los eventos `stats` de EVE (cero explícito / descartes / ausente / desactualizada / error / cobertura insuficiente; reinicio por identidad `t − uptime`; rotación .1/.gz; huecos). Integrada en `clasificar_periodo` (`--suricata-eve`), `vigia_4c` e I5 | 34 casos en banco (`test_etapa4_salud_eve.py`), 2 551 muestras reales del 04-nov; observación fija (§8) | **Resuelto**: la herramienta da estados medidos y no convierte una ausencia en cero. En vivo: ventana de observación **C0** (`cero_explicito`, 587 592 paquetes, 452 muestras, sin reinicio); I5 informativo **cumple** | §3, `evidencia/04-p1-medida/`, `evidencia/06-observacion/` |
| P3 | `rx_dropped` ≈ 14/s sin causa demostrada | Ninguna (diagnóstico, solo lectura) | Contadores separados del driver, del núcleo y de softnet; recuento de tramas en los PCAP | **Explicado con incertidumbre declarada**: contador del núcleo, no del driver; tramas 802.3/LLC dentro de VLAN sin manejador; no es pérdida de captura | §4, `evidencia/01-rx_dropped/` |
| **P4** | `firma_invalida` transitorio en el agente v2 | Entrega en un solo fichero `feed.par` (feed + firma + sha256), publicado con **un** `rename`; el agente lo lee con `--paquete`. Firma, secuencia e idempotencia sin cambios | Reproducción determinista en banco; cadena completa; interrupciones; concurrencia; laboratorio | **Resuelto en banco y en la observación**: 180 entregas en modo paquete, 180 aceptadas en orden, 0 `firma_invalida`, 0 `paquete_invalido` | §5, `evidencia/02-firma_invalida/`, `evidencia/03-banco/` |
| P5 | `SHA256SUMS` de `salida.txt` calculado antes de la última línea | `evidencia.sh`: `ev_sellar` cierra el `tee`, espera, comprueba 1 s sin cambios y solo entonces sella y verifica | 3 casos en banco (incluido un escritor que sigue escribiendo: «PARADA», no sella) | **Resuelto**: todas las carpetas de evidencia de hoy verifican | §6 |
| Instalador | (revisión de Mark de `313f8f8`) rc no comprobados, `verify` decidido por texto, evidencia dentro del respaldo | `p4_comun.sh`: cada paso con rc real; respaldo inmutable separado; reversión automática verificada (rc 20) o parada manual (rc 30) | 33 casos con errores deliberados en cada paso crítico | **Resuelto**: ningún falso OK; respaldo verificable; recuperación correcta; sombra conservada | §7, `evidencia/03-banco/regresion-instaladores.txt` |

Regresión completa del producto en banco Linux (Docker, sin red, repo de solo lectura): **786 passed, 7 skipped** en
`b18c286` (los 7 omitidos son los de siempre: compuerta sin el repo de docs montado y la prueba JS sin `node`).

## 3. P1: medida de Suricata por EVE `stats`

**Qué cambia.** `stats.log` de Suricata 7 no escribe los contadores que valen 0, así que «no aparece `kernel_drops`»
podía ser cero o falta de dato. Los eventos `stats` de EVE (cada 8 s) llevan `capture.kernel_packets`,
`capture.kernel_drops` y `uptime` **explícitos**. La versión nueva mide sobre ellos con los criterios de
`CRITERIOS-FIJADOS.md` §1: una ausencia nunca se convierte en cero; un reinicio se detecta por la identidad del proceso
(`t − uptime` estable ±3 s); hueco > 20 s o borde sin muestra a ≤ 10 s = `cobertura_insuficiente`.

**Medida retrospectiva del ensayo del 04-nov (rotulada como tal; NO reclasifica).** Sobre la ventana 06:26:55–07:26:55
la herramienta nueva da `cero_explicito` con **1 201 704** paquetes. **La clase oficial de esa ventana sigue siendo C3**
(se clasificó con las herramientas congeladas; criterio publicado: no se reclasifica).

**Por qué 1 201 704 y no 1 193 578.** Las dos cifras salen de las mismas muestras EVE; cambia qué muestras acotan los
extremos (`evidencia/04-p1-medida/bordes.py` → `bordes.txt`):

| Medida | Muestra inicial | Muestra final | Cobertura | Paquetes |
|---|---|---|---|---|
| Comparador del cierre 4A (`comparar_suricata.py`): primera y última muestra **dentro** de la ventana | 06:26:55,135 (`kernel_packets` 180 418) | 07:26:47,545 (1 373 996) | 3 592,4 s (450 muestras) | **1 193 578** |
| `salud_captura` 2026-11-06.1: muestras que **acotan** la ventana desde fuera (≤ desde, ≥ hasta, a ≤ 10 s) | 06:26:47,134 (174 661), 7,87 s antes | 07:26:55,546 (1 376 365), 0,55 s después | 3 608,41 s | **1 201 704** |

Diferencia: **8 126 paquetes = 5 757** (06:26:47,134 → 06:26:55,135) **+ 2 369** (07:26:47,545 → 07:26:55,546).
El comparador deja fuera ≈ 7,6 s de la ventana; la herramienta nueva la cubre entera a costa de incluir ≈ 8,4 s de
fuera. Ninguna de las dos tiene descartes (0 y 0). Para cubrir el periodo completo, la cota conservadora es la de la
herramienta nueva; por eso es la que se usa para I5. El umbral O12 (596 789 = 50 % de 1 193 578) se fijó con la cifra
del comparador antes de la observación y no se cambia.

**Lo que la herramienta ve en los datos reales del 04-nov** (2 551 muestras, 02:00–07:40, banco): descartes en tres
tramos (198 a las 02:08:27; 7 a las 03:05:47; 13 a las 03:53:56) y el reinicio de Suricata de las 06:16:5x detectado
por identidad de proceso (el incremento que lo cruza no se usa).

**I5.** Sin cambios de criterio: 0 `kernel_drops` en los 30 min previos al inicio de la 4C, terminando en la última
muestra (≤ 20 s de antigüedad). Lecturas informativas (no inician nada):
- 06-nov, antes de instalar: `cumple`, con 403 528 paquetes en 30 min.
- 06-nov 05:54Z, después de la observación: `cumple`, `cero_explicito`, con 304 391 paquetes y 226 muestras entre
  05:24:07 y 05:54:07Z (`evidencia/06-observacion/verif-post.txt`).

Estas lecturas solo comprueban que la medida funciona en vivo. I5 se evalúa en los 30 min previos al inicio real de
la 4C, no antes.

## 4. P3: `rx_dropped` de la NIC de captura (ens37), solo lectura

Cada contador por separado (`evidencia/01-rx_dropped/nic.txt`, dos lecturas a 60 s):

| Contador | Incremento en 60,1 s | Qué es |
|---|---|---|
| `rx_dropped` (sysfs / `ip -s`) | +842 (14,02/s) | Suma del núcleo |
| `drv dropped rx total` (vmxnet3, 4 colas) | **+0** | Descartes del driver |
| `rx_missed_errors` / `rx_fifo_errors` / `rx_over_errors` | +0 / +0 / +0 | Hardware |
| `rx_nohandler` | +0 | |
| `pkts rx OOB` (cola 0) | +0 (5 094 fijo) | El driver 6.8 no lo suma a `rx_dropped` |
| softnet `dropped` (4 CPU) | +0 | Backlog del núcleo |
| `otherhost` | +8 547 (142/s) | Tramas para otros MAC (puerto espejo); **se cuenta aparte**, no es descarte |

**Explicación.** En el núcleo 6.8, `__netif_receive_skb_core` entrega la trama a los *taps* AF_PACKET (Suricata,
tcpdump) **antes** de buscar manejador; una trama con etiqueta VLAN para la que el host no tiene interfaz VLAN y cuyo
protocolo interno no tiene manejador termina en `dev_core_stats_rx_dropped_inc` (`SKB_DROP_REASON_UNHANDLED_PROTO`).
Recuento en los PCAP del anillo (`nic_pcap.txt`, 60 s): tramas 802.3/LLC dentro de VLAN ≈ 1,03/s en cada una de 14
VLAN = **14,50/s**, frente a `rx_dropped` **14,03/s** en el mismo intervalo. **Esas tramas están en los PCAP**: no se
pierde tráfico capturado.

**Incertidumbre declarada.** (1) La lectura del código es sobre el núcleo 6.8 de upstream, no sobre las fuentes de
Ubuntu `6.8.0-53-generic`. (2) La coincidencia 14,50/s ↔ 14,03/s es una correspondencia de tasas en un intervalo, no
una traza trama a trama (no se usó `dropwatch`/`perf`, que requieren privilegios y cambiarían el host). (3) Por eso el
texto del cierre 4A «tramas sin manejador» se corrige: no estaba demostrado entonces y `rx_nohandler` es 0 (§10).
Offloads: `rx-vlan-offload on`, GRO/LRO off.

## 5. P4: `firma_invalida` transitorio

**Causa (reproducida).** El relé entregaba en dos `mv` sucesivos (firma, luego feed). Si el agente leía entre los dos,
veía una firma nueva con un feed viejo → `firma_invalida`; medio segundo después leía la pareja completa y la aceptaba.

**Las 14 incidencias del laboratorio** (`evidencia/02-firma_invalida/`, correlación de las trazas del relé y del
agente; relojes por NTP): todas ocurrieron **dentro** de una entrega del relé en modo **pareja**, entre 1 y 10 ms antes
de `entregado_en`, y la **misma secuencia** se aceptó 0,509–0,513 s después. Las 13 iniciales (04-nov 06:26 → 06-nov
02:14 UTC) son las del informe; la **14.ª** (seq 4380, 06-nov 04:00:55Z) apareció después del diagnóstico, con el
relé aún en pareja (antes del cambio de las 04:39). **Ninguna ocurrió en modo paquete.** La lista completa, con
secuencia, entrega y aceptación posterior, está en `evidencia/06-observacion/obs-post-p4.txt`.

La traza del agente tiene otros dos motivos, ambos fuera de la ventana y propios del diseño:
- **`feed_caducado`** (seq 3654, 06-nov 00:00:29Z): tras el arranque, el agente leyó el feed del 04-nov que había
  quedado en disco y lo rechazó por caducado.
- **`misma_secuencia`** (seq 4351, 03:51:29Z): es una recepción `repetido`, no un rechazo. El agente releyó la misma
  secuencia al reiniciarse en la fase A, lo que muestra que la idempotencia funciona.

**Corrección.** Paquete `feed.par` (`cyberflow-feed-paquete/1`: feed y firma en base64 + sha256 de cada uno),
escrito en `.feed.par.tmp` y publicado con **un** `rename` (SSH forzado `cf-feed-ssh.sh` o `os.replace` local). El
agente `--paquete` abre el fichero una vez; un paquete dañado es `paquete_invalido` (distinto de `firma_invalida`). La
verificación ed25519, la protección de secuencia y la idempotencia no cambian.

**Banco.** Cadena completa (publicador → relé → agente `--seguir`), 400 generaciones por corrida con 3 ms entre los dos
`mv` (`p4-cadena*.txt`): pareja 3, 0 y 5 rechazos `firma_invalida` (recuperación 0,51 s); paquete **0** en todas. Retraso
publicación → aceptación p50 ≈ 0,07 s en ambos modos.

**Hueco de secuencias 3654 → 3713 (no es de P4).** La traza del relé salta del 04-nov 22:31:53Z (seq 3654) al 06-nov
00:18:21Z (seq 3713); esa primera línea empieza con 219 bytes NUL (escritura cortada por una parada no limpia del
host; el bastión arrancó el 06-nov 00:00:08Z). En ese intervalo el relé no entregó nada; el agente aceptó la secuencia
siguiente, como está previsto (`hueco_seq.txt`).

## 6. P5: manifiestos sobre ficheros finalizados

`deploy/etapa4/comun/evidencia.sh`: `ev_abrir` redirige la salida a `tee`; `ev_sellar` devuelve la salida al
terminal, **cierra** la tubería, **espera** a `tee`, comprueba que nada cambia durante 1 s y solo entonces escribe
`SHA256SUMS` y lo verifica; si algo sigue cambiando dice «PARADA» y no sella. Lo usan los instaladores y la
herramienta de Sensor1. Todas las carpetas de evidencia de hoy verifican (bastión, srv-dmz fase A/C, Sensor1).

El `MANIFIESTO.sha256` de esta carpeta se calcula sobre los bytes **publicados** (`git archive` del commit) y se
verifica contra esa copia (§12).

## 7. Instalador `p4-instalador 2026-11-06.2` (corrección pedida tras revisar `313f8f8`)

| Requisito de Mark | Cómo queda |
|---|---|
| Código de salida de cada operación crítica | Todas pasan por `paso`: copia del respaldo, `install`, `daemon-reload`, `systemd-analyze verify`, reinicio, `is-active`, cmdline, entrega/recepción, hashes, sombra. Tras un fallo **nunca** se escribe «RESULTADO: OK» |
| `systemd-analyze verify` | Se decide por su **rc**; el texto solo se registra. Se verifica la unidad nueva **antes** de instalarla y la instalada después. En el laboratorio, rc 0 en bastión y srv-dmz |
| Respaldo inmutable separado | `~/respaldos-etapa4/<host>-p4-…/`: ficheros, `modos.txt`, `instalados-antes.sha256`, `SHA256SUMS`; solo lectura y **verificado en modo estricto** (mismo conjunto de ficheros que el manifiesto) **antes** del primer cambio. La evidencia va a `~/evidencia-etapa4/…`, fuera |
| Fallos antes / después de cambiar | rc **10** «PARADA SIN CAMBIOS»; rc **20** «REVERTIDO AUTOMÁTICAMENTE» (ficheros con su modo y dueño, `daemon-reload`, reinicio, activo, hashes = respaldo, sin `--aplicar`, ruleset igual), y **no** se sigue a la fase siguiente ni a la observación; rc **30** «REVERSIÓN AUTOMÁTICA FALLIDA — INTERVENCIÓN MANUAL», con lo que falta |
| Automática ≠ manual | Automática solo desde `p4_fallo`. Manual: `bastion_p4.sh revertir R` (Mark), `srvdmz_p4.sh revertir R`, y `srvdmz_p4.sh revertir-heredado R0` para el respaldo de la versión .1 (que contiene su evidencia de fase A: se verifican los ficheros listados y se informa lo no listado). Si la fase C de srv-dmz se revierte sola, el relé sigue en paquete: el instalador lo dice y pide revertir el bastión a mano |

**Pruebas con errores deliberados** (`tests/test_etapa4_p4_instaladores.py`, 33 casos, los guiones reales con órdenes
falsas `sudo`/`systemctl`/`systemd-analyze`/`nft`/`ssh` que fallan donde se les pide):
- Bastión, antes del cambio (rc 10): paquete corrupto, `cp` del respaldo, ssh a srv-dmz, `verify` de la unidad nueva
  con rc≠0 y **sin texto**, relé inactivo.
- Bastión, después (rc 20): `install` de los `.py`, `install` de la unidad, `daemon-reload`, `verify` de la instalada
  (solo rc), reinicio, `is-active` tras reiniciar, sin entrega en modo paquete.
- srv-dmz fase C, antes (rc 10): sin fase A, `feed.par` ausente o viejo, `cp`, `nft` ilegible, `verify` nueva.
- srv-dmz fase C, después (rc 20): `install`, `daemon-reload`, `verify` instalada, reinicio, `is-active`, sin recepción.
- Reversión que también falla (rc 30) en ambos; **ruleset alterado** tras reiniciar → rc 30 (restaurar ficheros no lo
  deshace; nunca se da por revertido); respaldo manipulado → la reversión manual se niega (rc 30) sin tocar nada.
- `verify` que imprime avisos con rc 0 → OK (no se decide por texto).
- Éxito y reversión manual en ambos; `revertir-heredado` con el formato de la versión .1.
- En cada caso: rc esperado; «RESULTADO: OK» si y solo si rc 0; respaldo estricto y sin evidencia; tras rc 10/20
  hashes, modos y servicio como antes; sin `--aplicar`; `nft` solo con `list ruleset`; evidencia sellada y fuera.

Dos defectos que encontraron estas pruebas y se corrigieron antes de publicar: la fase C solo comprobaba **después**
de cambiar que el código de la fase A estuviera instalado (ahora es precondición, rc 10), y la reversión de srv-dmz
contaba como fallo la falta de recepción cuando el relé seguía en paquete (ahora es un aviso explícito).

## 8. Integración en sombra y observación fija

**Instalación** (`evidencia/05-instalacion/`):

| Hora (UTC) | Paso | Quién | rc | Respaldo / evidencia |
|---|---|---|---|---|
| 03:51 | srv-dmz fase A (versión .1: `cf-feed-ssh.sh` admite pareja **y** paquete; código nuevo; unidad sin cambios) | Claude | OK | `/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-20261106T035127Z` (13 ficheros sellados; contiene la evidencia de la fase A: defecto de la .1) |
| 04:38:48–04:39:07 | Bastión `bastion_p4.sh instalar` (.2): relé `--entrega paquete` | **Mark** (sudo con contraseña) | **0** | `/home/gadmin/respaldos-etapa4/bastion-p4-20261106T043848Z` (estricto, solo lectura) · `/home/gadmin/evidencia-etapa4/bastion-p4-20261106T043848Z` |
| 04:39:44–04:39:49 | srv-dmz `srvdmz_p4.sh fase-c` (.2): agente `--paquete` | Claude | **0** | `/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z` · `/home/adminsrvdmz/evidencia-etapa4/srvdmz-p4-fase-c-20261106T043944Z` |

Verificado después: respaldo y evidencia del bastión verifican; relé PID 70246, `NRestarts` 0, entregas
`"entrega": "paquete"`; agente con `--paquete`, sin `--aplicar`; ruleset de srv-dmz vacío (`e3b0c442…`); v1 inactivos.

**Observación.** Último reinicio de la instalación 04:39:49Z → ventana fija **04:50:00Z–05:50:00Z** (epoch
1793940600–1793944200), fijada a las 04:41 antes de empezar. Sin ninguna acción sobre el laboratorio. Lecturas:
bastión cada 30 s (`obs_muestreo.sh`, también Sensor1 y srv-dmz por ssh), Sensor1 cada 10 s
(`salud_captura muestrear`) y lectura de cada PCAP del anillo en cuanto se cierra (`obs_pcap.py`: el anillo guarda
≈ 17 min, así que O2 no podía medirse al final).

| # | Criterio (fijado antes) | Resultado | ¿Cumple? |
|---|---|---|---|
| O1 | Sin cambio de PID ni de `NRestarts` en los 7 servicios | 121 muestras en la ventana (125 con ±60 s), intervalo máx. 30 s. PID constantes: motor 1384, captura 1355, vía rápida 1387, suricata 1351, publicador 1386, relé 70246, agente 15020; todos con `NRestarts` 0 y activos | **Sí** |
| O2 | PCAP del anillo legibles, incluido el primero | 717 ficheros empiezan en la ventana (primero `live-20261106045002.pcap`, último `…054955`), **0 errores de formato**, 585 151 registros completos, 0 vacíos | **Sí** |
| O3 | Salto del anillo ≤ 7 s; rotación de `eve.json` | Salto máximo entre ficheros: **6,0 s**; hueco máximo entre el último paquete de un fichero y el primero del siguiente: 0,496 s. `eve.json` no rotó (última rotación 05-nov 23:59:57) | **Sí** |
| O4 | EVE sin hueco > 20 s y un solo proceso | 452 muestras, acotadas a 0,99 s antes y 7,43 s después; sin reinicios (arranque estimado 05-nov 23:59:00Z); sin repetidas ni parciales | **Sí** |
| O5 | `clasificar_periodo --suricata-eve`; clase tal cual; estado de Suricata medido | **C0** (anillo C0, vía rápida C0), `suricata_reinicios_dentro` 0; Suricata `cero_explicito` | **Sí** |
| O6 | `/home` libre ≥ 2 GB; carga y memoria | `/home` libre ≥ 12,16 GB; carga a 1 min con máximo 1,10 y mediana 0,18; `MemAvailable` ≥ 5,78 GB | **Sí** |
| O7 | Entregadas = aceptadas, en orden; publicador sin retroceso | 180 entregas en modo **paquete** (seq 4527–4706, sin huecos) y 180 aceptadas en orden; 0 entregadas sin aceptar. Publicador 4524 → 4709 sin retroceso. Retraso entre la generación y la aceptación: p50 0,83 s, p95 1,41 s, máximo 1,60 s (incluye el sondeo de 1 s del relé) | **Sí** |
| O8 | 0 `firma_invalida`, 0 `paquete_invalido` | 0 y 0 en la ventana; los acumulados (14 y 0) no cambiaron | **Sí** |
| O9 | Panel HTTPS 401 desde el bastión; agente verificado en srv-dmz | 401 en 125/125 muestras. Agente comprobado directamente en srv-dmz: activo, mismo PID y 180 aceptaciones | **Sí** |
| O10 | 0 aplicaciones; rulesets iguales; sin `--aplicar`/`--enforce`; v1 inactivos | 0 eventos `aplicacion`. Ruleset de Sensor1 `24c320e3…` y de srv-dmz `e3b0c442…` (sin tablas), iguales en todas las muestras y antes/después. 0 procesos con `--aplicar`/`--enforce`; v1 inactivos | **Sí** |
| O11 | Hashes congelados iguales antes y después | Ninguna diferencia entre `obs-antes-*` y `obs-despues-*`: modelo `df547da0…`, manifiesto `b3ad6805…`, esquema `e032a1a2…`, `ec78ca5` `SHA256SUMS` OK, `suricata.yaml` `0962ce68…`, instalados de bastión y srv-dmz | **Sí** |
| O12 | **Comparable** si hay ≥ 596 789 paquetes | **587 592** (98,5 % del umbral; 49,2 % de la hora del ensayo). **Carga insuficiente**: no se concluye nada sobre descartes bajo carga | **No** |

**Aceptación de la instalación (criterio §3, después de instalar).** Se cumple todo menos `verificar_*.sh` sin FALLO
(`evidencia/06-observacion/verif-post.txt`):

| Guion | Resultado | FALLO | Por qué; comprobación independiente |
|---|---|---|---|
| `verificar_srvdmz.sh` (`CON_SUDO=1`, respaldo de la fase C) | **OK**: sombra demostrada, feed.par < 60 s, helper rechaza un perfil ajeno | — | — |
| `verificar_bastion.sh` | **1 FALLO** | «relé v1 sigue activo e intacto» | Comprueba `is-active ppi-relay-feed.timer`, de cuando v1 seguía activo. El cierre 4A retiró v1 a propósito y ahora está `disabled/inactive`, que es el estado exigido en O10 |
| `verificar_sensor1.sh` | **2 FALLO** | «ppi-publicar-feed.timer activo» | Mismo defecto: espera activo el v1 retirado (`disabled/inactive`) |
| | | «motor_startup del candidato» | El guion busca el evento en `motor_decision.log`, pero el arranque (05-nov 23:59:01Z) quedó en `motor_decision.log.1` por la rotación diaria de las 23:59:03. En ese `.1`: `disparo: eventos`, `if_limpio_2026_10` y el umbral del manifiesto `-0.5693969936322356` (`motor_startup.txt`) |

Los tres son defectos de los guiones, no del sistema. Aun así el criterio está escrito como «sin FALLO» y **no se
cumple**. Corrección propuesta, no aplicada: v1 retirado debe esperarse inactivo, y `motor_startup` debe buscarse
también en el registro rotado. Después, prueba en banco y nueva ejecución de solo lectura.

## 9. Veredicto por componente

| Componente | Veredicto |
|---|---|
| P1: medida de Suricata por EVE `stats` (`salud_captura` 2026-11-06.1, `clasificar_periodo`, `vigia_4c`, I5) | **Cerrado.** Probado en banco y en vivo: C0 y `cero_explicito` medidos, I5 informativo `cumple`. La ventana del ensayo del 04-nov sigue siendo C3 |
| P3: `rx_dropped` | **Explicado con incertidumbre declarada.** Contador del núcleo, no del driver; las tramas están en los PCAP. Falta una traza trama a trama y las fuentes de Ubuntu (§4) |
| P4: entrega `feed.par` | **Cerrado.** Reproducido, corregido, sin rechazos en banco ni en 180 entregas reales, firma y secuencia intactas |
| P5: sellado de evidencia | **Cerrado.** Todas las carpetas de hoy verifican, también en la copia del repo |
| Instalador `p4-instalador 2026-11-06.2` | **Correcto.** 33 casos con fallos deliberados; en el laboratorio, rc 0 en bastión y en srv-dmz, con respaldos estrictos fuera de la evidencia |
| Integración en sombra (relé paquete + agente paquete) | **Verificada en O1–O11**, sin aplicaciones ni cambios de ruleset |
| Carga de la observación (O12) | **Insuficiente.** No se concluye nada sobre descartes bajo carga |
| Aceptación §3 (`verificar_*.sh` sin FALLO) | **No cumplida tal como está escrita:** 3 FALLO por defectos de los guiones (§8) |
| Panel | Responde 401 sin sesión; sigue sin ver al agente (P6 del cierre, conocido) |
| 4B, control formal | **Todavía no:** falta el §3 sin FALLO. Puede seguir preparándose |
| 4C y campaña B | **No autorizadas** |

## 10. Correcciones al cierre complementario

En `../etapa4a-cierre-complementario-2026-11-04/README.md` se añaden notas marcadas «**Corrección (pendientes 4A,
06-nov)**», sin borrar el texto original:
- **§6.3, `rx_dropped`:** «tramas sin manejador» no estaba demostrado entonces y `rx_nohandler` es 0. Diagnóstico y su
  incertidumbre: §4 de este informe.
- **Veredicto y §11, criterio de avance unificado:** la 4B **puede prepararse**; su **control formal** espera a que
  P1 esté cerrado y la integración verificada; la 4C y la campaña B **no** están autorizadas. (El cierre decía en un
  sitio «no iniciar la 4B hasta resolver P1» y en otro solo «no iniciar la 4C».)
- **§7 y §8:** «C3, no evaluable» significa que **faltaba la medida**, no que hubiera evidencia de descartes; la medida
  retrospectiva (cero explícito) está en §3 de este informe y no reclasifica la ventana.
- **§11 P5:** resuelto (§6).

Su `MANIFIESTO.sha256` se regenera porque cambia el README; las líneas de `evidencia/` no cambian.

## 11. Procedimientos

**Reversión manual** (ninguna se ha necesitado):
- `[BASTIÓN gadmin] → lo ejecutas tú (sudo con contraseña)`:
  `bash ~/cf-e4/paquete-b18c286/deploy/etapa4/pendientes/bastion_p4.sh revertir /home/gadmin/respaldos-etapa4/bastion-p4-20261106T043848Z`
  → relé por pareja.
- `[SRV-DMZ adminsrvdmz] → lo ejecuto yo (sudo -n)`, **después** del bastión:
  `bash ~/cf-e4/paquete-b18c286/deploy/etapa4/pendientes/srvdmz_p4.sh revertir /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z`
  → agente con `--feed/--firma` (código de la fase A, que admite ambos modos).
- Para volver al estado previo a la fase A: `srvdmz_p4.sh revertir-heredado /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-20261106T035127Z`.
- Códigos: 0 OK · 30 reversión fallida (se detiene y dice qué falta). La reversión nunca arranca v1 ni usa `--aplicar`.

**Medidas repetibles:** `evidencia/06-observacion/obs_sensor_post.sh` y `obs_p4_post.sh` (aceptan `desde hasta`).

## 12. Limitaciones

- **Carga.** La hora observada tuvo menos carga que el umbral comparable (O12). No dice nada sobre descartes con
  ráfagas ni sobre P2 (anillo de Suricata con carga real).
- **No es una prueba de eficacia.** Sin ataques ni generadores, el feed no tuvo entradas. La cadena se demostró con
  feeds firmados reales, pero vacíos; la aplicación de restricciones no se probó, porque no estaba autorizada.
- **P3.** La explicación se apoya en el código de upstream 6.8 y en una correspondencia de tasas (§4).
- **Fase A con la versión .1.** Su respaldo contiene su propia evidencia. Por eso existe `revertir-heredado`, que
  solo usa los ficheros del manifiesto.
- **Verificador de PCAP** (`obs_pcap.py`): la hora de fin estaba mal calculada (06:11:30Z en vez de 05:51:30Z).
  Siguió leyendo, solo lectura, hasta que lo detuve a las 05:56:25Z (`sensor1/incidencias.txt`). Los ficheros de la
  ventana ya estaban leídos.
- **`pgrep` en el sellado.** Los dos primeros intentos de sellar se pararon solos, porque el patrón coincidía con la
  propia orden. No se selló nada a medias: el guion que funcionó compara el ejecutable exacto (`sellar_s1.sh`).
- **Los relojes** de los tres hosts se sincronizan por NTP (los `verificar_*.sh` dan «reloj sincronizado»). Las
  correlaciones relé ↔ agente dependen de ello.

## 13. Evidencia

```
README.md                    este informe
CRITERIOS-FIJADOS.md         criterios publicados antes de instalar y de observar (997c8e2, sin cambios)
MANIFIESTO.sha256            sha256 de cada fichero (bytes publicados), dos espacios, orden LC_ALL=C sort -f
evidencia/
  01-rx_dropped/             contadores NIC/driver/softnet y recuento de tramas en los PCAP (P3)
  02-firma_invalida/         correlación relé ↔ agente de cada rechazo; hueco de secuencias
  03-banco/                  cadena P4 pareja/paquete; regresiones (313f8f8 y b18c286)
  04-p1-medida/              extracción de EVE stats y explicación de 1 193 578 / 1 201 704
  05-instalacion/            verify de systemd, fase A, bastión (salida de Mark), fase C
  06-observacion/            guiones, estado antes/después, análisis posteriores, verificar_*.sh, motor_startup, O6
    bastion/                 muestras cada 30 s y copias de las trazas del relé y del agente (con su SHA256SUMS)
    sensor1/                 muestras de salud_captura, lectura de cada PCAP, clasificación final y prueba en seco,
                             incidencias.txt (con su SHA256SUMS; ambos verificados en esta copia)
```

Respaldos e instalaciones en los hosts (no se copian aquí; se citan en §8 y §11). Los guiones de producto están en la
rama `recuperacion/etapa4a-pendientes-20261106` (`b18c286`).
