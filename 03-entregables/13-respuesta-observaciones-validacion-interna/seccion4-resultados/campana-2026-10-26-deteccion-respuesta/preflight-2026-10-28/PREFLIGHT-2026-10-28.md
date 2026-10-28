# Preflight operativo de la campaña A — 2026-10-28

Base: commit `a072fea0d1593e246888635412f0c45c975c02ca`. Ejecutado entre **06:54:33 y 07:15:08 UTC** del 28-oct-2026.
Todas las comprobaciones son **actuales**: ninguna se reutiliza de las carpetas `evidencia-entorno-2026-10-27/`,
`evidencia-precheck/` ni `ESTADO-ENTORNO-2026-10-27.md`.

No se ejecutaron ataques ni se inició la campaña o el prompt 2. Tampoco se reentrenó, se cambiaron umbrales ni se
modificó Word. No se activó el modo sombra ni se vaciaron reglas. No se cambió ningún servicio, regla ni configuración.
Las únicas acciones con efecto fueron cuatro:

- una prueba del archivador en un directorio de preflight (§4), detenida por su PID;
- una vuelta única de cada perfil legítimo (§7), ejecutada con el propio código de los perfiles;
- dos tandas de transacciones benignas desde la Kali (DNS, GET y `/auth`) (§7);
- una copia temporal del generador en la Kali, validada sin ejecutar escenarios y borrada después (§2).

Las sondas están en `sondas/` y sus salidas crudas en `salidas/`, una `out_<sonda>.txt` por sonda. Cada sonda se lanza
con `[LAPTOP PowerShell] → lo ejecuto yo: sondas/run.ps1 <sonda> <host>`. El script salta por el bastión
`gadmin@10.10.10.30` y usa la llave del bastión hacia cada host.

> **Efecto colateral que hay que declarar.** Las transacciones benignas de 07:03:59 desde la Kali produjeron 2 ALERT
> reales del IF desplegado. Como el enforcement sigue **vivo**, el publicador del feed metió una entrada **LIMIT**
> entre 07:04:10 y 07:06:50 (§6). Las pruebas de visibilidad, por tanto, no son inocuas mientras no esté activo el
> modo sombra. Esto refuerza que la sombra es un paso obligatorio de inicio.

## 1. Máquinas y conectividad

| Hora UTC | Origen → destino | Herramienta | Resultado |
|---|---|---|---|
| 06:54:33–06:54:43 | bastión → 10 IP del laboratorio | `bash /dev/tcp` (el bastión no tiene nmap ni tcpdump) | Las 10 IP responden en TCP/22: **encendidas** |
| 06:54:3x | bastión → srv-dmz 10.10.30.10 | `/dev/tcp` | 80, 443 y 18081 abiertos |
| 06:54:3x | bastión → DNS/DC 10.10.10.20 | `/dev/tcp` | 53 abierto |
| 06:55:39 · 06:57:34 · 06:59:46 · 07:00:17 | bastión → sensor, clientes, Kali, srv-dmz | SSH con llave (BatchMode) | Sesión y `sudo -n -l` correctos en los 4 |
| 06:58:39–45 | clientes .21–.26 → srv-dmz:80 | código de los perfiles | Conexión TCP correcta desde las 6 IP |
| 06:59:47 · 07:03:59 | Kali → DNS:53, srv:80, srv:18081 | dig y curl | NOERROR `aa`, 200, 401/401/200 |
| 07:01:38 | bastión → Internet | dig y curl HEAD | **Sin DNS ni HTTPS** a Internet. chrony sí sincroniza por NTP |

Ninguna máquina estaba apagada y no se observó ningún bloqueo de red entre los hosts del laboratorio. Lo que sí estaba
detenido era un **servicio**: los perfiles legítimos (§7). En el DNS/DC no tengo llave SSH; su reloj se midió por SNTP
(§5).

## 2. Artefactos y hashes

**Configuración del analizador** (HEAD `analizar.py` f06849b5…). Comprobada con `sondas/compat_analizador.py` sobre una
**muestra real** de las últimas 3000 líneas de `motor_decision.log`. Salida en `salidas/out_compat_analizador.txt`.

- Las **7 configuraciones** son IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03 y HIB_0.01.
- Umbrales de análisis exactos: 0,05 → `-0.5694578968203694`, 0,03 → `-0.5898535710336618` y 0,01 →
  `-0.6223889502095352`. Respetan el orden.
- El desplegado, `-0.5693969936322356`, se mantiene **aparte**.
- El lector corregido está presente: `REQ_MOTOR` no exige `threshold`, y `estado_umbral_registrado` distingue
  `clave_ausente`, `null` y `numerico`.
- Resultado sobre la muestra real: 3000 líneas → 3000 registros, **0 incidencias**, 0 ventanas duplicadas. Los 3000
  umbrales son de tipo `numerico`.
- Emisiones observadas: 24 ALERT con emisor `IF_desplegado` y configuración «confirmada».
- Señales derivadas: IF_0.05 24, IF_0.03 2, IF_0.01 0, HEUR 0, HIB 24/2/0. Son **clasificaciones derivadas, no
  emisiones**.

**Sensor** (`salidas/out_p04_sensor_hashes.txt`). Estos hashes coinciden con `config-campana.json`:

| Artefacto | sha256 (prefijo) |
|---|---|
| extract v2 | 7130edae |
| extract v3 | 5adbfbf4 |
| `motor_decision.py` | 4c41ec44 |
| heurísticos | 10deb05d (`VERSION_UMBRALES 2026-10-06.2`) |
| `publicar_feed.py` | f7bc4c7d |
| modelo `.joblib` | df547da0 |
| manifiesto del modelo | b3ad6805 |

- El manifiesto del modelo registra el umbral `-0.5693969936322356` y α 0,05.
- La línea 78 del toml (`umbral = 1.8126…`) no es la del motor, que toma el umbral del manifiesto.
- `~/bin/archivar_captura.sh` = `2181af5f…`, **igual a HEAD**.
- venv: Python 3.14.4 y sklearn 1.9.0.

**Copias que faltan en las máquinas** (pasos de inicio, no defectos):

- **Kali**: no tiene `generar_campana.py`, `esquema_campana.py` ni `escenarios.json`. Copié los bytes de HEAD a un
  directorio temporal y pasaron `validar(exigir_herramientas=True)` → **SIN PROBLEMAS**. Los comandos se construyeron,
  no se ejecutaron. Después borré la copia (`salidas/out_p06_kali.txt`).
- **srv-dmz**: no tiene `modo_sombra.sh` ni `restaurar_enforcement.sh` (`salidas/out_p07_srv.txt`). Con los bytes de HEAD,
  `tests/test_sombra.sh` da **11/11** en el portátil, con comandos simulados.
- **Sensor**: no existe todavía el directorio de archivado de la campaña. El de la prueba es aparte (§4).

## 3. Servicios y fuentes de evidencia

| Fuente | Estado actual | Lectura · rotación · formato |
|---|---|---|
| `ppi-motor` | active desde 24-oct 10:49, PID 2558538, NRestarts 0. argv **sin `--enforce`** | `motor_decision.log`: últimas 3000 líneas todas `event=decision`, sin faltar ningún campo de `REQ_MOTOR`. Último registro con 4,4 s de antigüedad. Rotación diaria (logrotate `daily`, `maxsize 200M`, `rotate 14`, `create`) |
| `ppi-motor-capture` | active desde 21-oct 19:09, PID 1393, NRestarts 0 | `tcpdump -i ens37 … -G 15`, sin filtro. Anillo de unos 15 min (la limpieza borra con `-mmin +15`). Ficheros `tcpdump:m4rk 640`, legibles |
| Suricata 7.0.3 | active desde 27-oct 07:23 | `eve.json` legible por m4rk, JSON válido. Tipos flow, ssh, dns, tls, http y fileinfo. Rotación diaria (`maxsize 500M`, `copytruncate`, `rotate 7`) |
| Features (`acumular`) | timer cada 10 min | `artifacts/linea-base/multilayer-v3.csv`, 46 columnas, con filas para la Kali y .21–.26 en las ventanas del preflight (§7) |
| Publicador del feed | timer cada 10 s | `~/feed/feed.json` y `estado.json` firmados. Hay un aviso cosmético: `--umbrales 2026-10-06.1` ≠ código `.2` |
| Endpoint `/auth` (srv-dmz) | `ppi-brute-lab` active, **UnitFileState disabled** | `brute.log` registra las 6 peticiones del preflight con usuario y código |
| Web `:80`/`:443` (srv-dmz) | `lab-web-http` y `lab-web-https` active | GET 200 |
| Generadores legítimos | **detenidos y deshabilitados desde el 15-oct 11:11:50** | ver §7 |

**Hallazgo del motor en vivo, medido y no corregido.** Algunas ventanas con tráfico se registran con
`packet_count_10s = 0`, sin pasar por el IF (`no_live_packets_heuristic`). Pasa cuando el motor evalúa la ventana muy
poco después de su cierre, antes de que se cierre el PCAP de 15 s que la contiene. Lo cuantifica
`salidas/out_p16_sensor_retraso_vs_vacias.txt`, sobre las ventanas de 05:10 a 07:00 cruzadas con las features por lotes:

| Retraso de evaluación (`logged_at − window_end`) | Ventanas-entidad con tráfico según features | Evaluadas con 0 paquetes vivos |
|---|---|---|
| < 5 s | 941 | **229 (24 %)** |
| 5–15 s | 1497 | 12 (1 %) |
| ≥ 15 s | 353 | 0 |
| **Total** | 2791 | **241 (8,6 %)** |

En el preflight se observó en las ventanas de 06:58:50 (.21–.26) y 06:59:50 (Kali). Ambas se evaluaron entre 2,4 y
3,1 s después del cierre y no se puntuaron, aunque las features registran 24–1698 paquetes. Es comportamiento del
sistema **tal como está desplegado**: el analizador mide lo que el motor emite. Su impacto en la detección por episodio
**no está medido**. El preflight no lo corrige. Queda como decisión pendiente (§9).

## 4. Captura full-SPAN, archivador y capacidad

- **Captura completa**: el argv real es `tcpdump -i ens37 -n -s 0 -U -B 65536 -Z tcpdump -w …live-%Y%m%d%H%M%S.pcap -G 15`.
  No hay filtro BPF, así que no es un filtro solo para la Kali. ens37 está en PROMISC. En el PCAP aparecen 32 IP de
  origen en un solo fichero cerrado, y tráfico de la Kali, de los 6 perfiles, del DC y del bastión.
- **Las tramas van etiquetadas con 802.1Q** (VLAN 10, 20…). Son 4847 de 4849 en un fichero. Un filtro BPF `host X`
  **sin `vlan` da 0 paquetes**; con `(F) or (vlan and (F))` aparecen todos (`salidas/out_p13b_sensor_vlan_alertas.txt`).
  Los scripts de la campaña no filtran PCAP por BPF. Cualquier atribución manual sobre el PCAP debe usar filtros
  conscientes de VLAN.
- **Prueba del archivador**, autorizada (p11a y p11b):
  - Destino `/home/m4rk/cf-preflight-20261028/archivador-070336`, identificado como preflight y separado de la campaña.
  - Inicio a las 07:03:36 (PID 2065599, intervalo 20 s).
  - Parada a las 07:04:50 con SIGTERM **solo** a ese PID, tras comprobar su cmdline. Código de salida **0**; el proceso
    ya no existe.
  - Resultado: `ESTADO.txt` = `OK: vistos=80 archivados=80, sin fallos`, 0 líneas FALLO/PERDIDO.
  - Inventario por marca de paquete: 80 ficheros, 0 duplicados, 0 solapes, 0 huecos o reinicios. La mayor separación
    entre ficheros es 0,462 s. Cubre 06:44:51–07:04:52, lo que incluye [inicio, parada].
  - Integridad: 80 de 80 copias coinciden con su registro OK. Las 60 que siguen en el anillo son idénticas al origen;
    las otras 20 ya se habían podado.
  - **El fichero activo al parar** (`live-20261028070438.pcap`) **no se copió como cerrado**. Se copió en el barrido
    final, después de `CLOSE_AGE` (07:05:21).
  - La carpeta de la prueba (125 MB) queda en el sensor como evidencia y no es de la campaña.
- **Pérdidas**:
  - Contadores de la NIC en una ventana de 90 s (07:06:53–07:08:23): rx_packets +14 809, rx_dropped +1263. El PCAP
    tiene 14 803 paquetes con marca en esa ventana, es decir PCAP/rx_packets = 0,9996.
  - `rx_dropped` de la NIC incluye tramas que la pila descarta tras entregarlas a los sockets de captura, así que por sí
    solo no equivale a pérdida de tcpdump.
  - **Los descartes del propio tcpdump (PID 1393) no están medidos**: el proceso no se ha detenido y no publica sus
    estadísticas.
  - Que no haya huecos entre ficheros **no** prueba que haya cero pérdida de paquetes.
- **Espacio**: el tráfico benigno ocupa 6,51 MB/min, unos 391 MB/h; 5 h serían unos 2 GB. El sensor tiene 21 GB libres
  en `/` (42 % usado). El volumen **durante los ataques será mayor** (barridos, ráfagas HTTP), así que el consumo **debe
  vigilarse durante la campaña** (`df -h` y tamaño del destino).

## 5. Relojes

La referencia es el bastión VM-GESTION (chrony, ref. 168.96.251.195), que va 1,2 ms atrasado respecto a NTP. El método
toma varias muestras por SSH, cuenta el desfase al punto medio del RTT y da como incertidumbre la mitad del RTT mínimo
(`sondas/p10b_relojes.sh`).

| Host | Hora UTC | Desfase | Incertidumbre | Sincronizado | Fuente NTP | Tolerancia ≤ 1 s |
|---|---|---|---|---|---|---|
| Sensor | 07:02:49 | +5,1 ms | ±0,6 ms | sí | 10.10.60.1 | sí |
| Kali | 07:02:51 | −20,1 ms | ±0,8 ms | sí | 2.debian.pool.ntp.org (**Internet**) | sí |
| srv-dmz | 07:02:53 | +5,3 ms | ±0,3 ms | sí | ntp.ubuntu.com (**Internet**) | sí |
| Clientes | 07:02:55 | +5,1 ms | ±0,5 ms | sí | ntp.ubuntu.com (**Internet**) | sí |
| DNS/DC | 07:02:22 | +0,9 ms | ±0,3 ms | estrato 2 (SNTP) | — | sí |

La tolerancia de 1 s viene de `INSTRUCCIONES-INFRA-2026-10-27.md:39` y `verificar_integridad.py`. El «+0,18 s» del
27-oct era el RTT de establecer la sesión SSH, no desfase. El intento `p10_relojes.sh` no produjo salida y se rehízo
como p10b; se conservan ambos.

- **Inicio y fin del generador**: la Kali va 20 ms por detrás del sensor. Las marcas de inicio y fin del generador son
  comparables con `window_end` y `logged_at` con un error muy inferior a la ventana de 10 s.
- **`logged_at` frente a `window_end`** (muestra de 3000):
  - mediana +9,06 s, mínimo −1,45 s, máximo 231,7 s;
  - en el preflight, las ALERT de la Kali tuvieron +10,05 y +10,17 s.
- Las clasificaciones derivadas se ordenan por `logged_at` y no se presentan como emisiones (§2).

## 6. Estado de respuesta

**Motor.** El argv no lleva `--enforce`. El motor decide y el publicador del sensor convierte las ALERT en feed.

**Cadena de enforcement viva.** Funciona así:

- el publicador del sensor genera el feed cada 10 s;
- el relé del bastión lo reenvía (`ppi-relay-feed.timer`, active);
- en srv-dmz, `ppi-enforce-agent.timer` (active y enabled) ejecuta `agente_enforce.py … --aplicar --sudo` cada minuto.

**Sets de nftables**, consultados de verdad (`sudo -n nft list set …`, rc=0):

| Hora | `cyberflow_bloqueados` | `cyberflow_limitados` |
|---|---|---|
| 07:00:17 | 0 elementos | **{10.10.50.52}** (residual: 89 ALERT de esa IP hoy) |
| 07:12:17 | 0 elementos | 0 elementos |

En el sensor solo existe la tabla `inet cyberflow_panel`, sin elementos.

**Feed.**

- A las 07:01:35 tenía 0 entradas (umbrales `2026-10-06.2`).
- `estado.json` registra 7 IP, todas con `bloqueos 0`.
- **Entre 07:04:10 y 07:06:50 hubo 1 entrada LIMIT**, con `"limit": 1` en 17 ejecuciones seguidas
  (`salidas/out_p17_sensor_feed_0704.txt`).
- La única ALERT dentro de la ventana de 120 s del publicador es la de **10.10.20.30**: IF, score
  −0,5823 < −0,5694, registrada a las 07:04:10 (`salidas/out_p18_sensor_alertas_0702_0707.txt`). Fue provocada por las
  transacciones benignas del preflight.
- **No está verificado** si el agente de srv-dmz llegó a aplicarla: la consulta de las 07:12 es posterior a la expiración.
- A las 07:11:30, `estado.json` daba 10.10.20.30 con `bloqueos 0`, así que no hubo escalada a BLOCK.

**El estado de respuesta no es estable.** El conjunto LIMIT cambia con el tráfico (10.10.50.52 entra y sale; la Kali
entró por tráfico benigno). Antes de A hay que activar la sombra y verificar sets vacíos **después** de activarla.

**Procedimiento de sombra con los permisos disponibles.**

- `adminsrvdmz` tiene `NOPASSWD: ALL`, así que puedo ejecutar `modo_sombra.sh --ejecutar --motor-verificado` y
  `restaurar_enforcement.sh --ejecutar --escalada-revisada` en cuanto se copien.
- `modo_sombra.sh` lee la escalada de `FEED_DIR=/home/m4rk/feed`, que está en el **sensor**. Ejecutado en srv-dmz la
  registrará como DESCONOCIDA. La copia de `estado.json` debe **guardarse desde el sensor** (lectura como m4rk, sin sudo)
  en el mismo paso.
- Comprobado: las herramientas existen y los permisos alcanzan. **No comprobado**: la ejecución real, porque está
  prohibida en este preflight.

## 7. Dependencias de los cinco escenarios (solo benignas)

| Dependencia | Comprobación actual | Resultado |
|---|---|---|
| Zona DNS local | 06:59:47, `dig @10.10.10.20 preflight-1793170787.lab-ppi`. 07:03:59, `pfmarca1/2-1793171039.lab-ppi` | 10.10.30.10, NOERROR, flag `aa` (autoritativa local). SOA de VM-AD-DC |
| HTTP | GET :80 desde la Kali (06:59:47 y 07:03:59) | 200 |
| `/auth` 401 y control 200 | sin credencial, credencial falsa, control (06:59:47 y 07:03:59) | 401, 401, 200. `brute.log` registra `user=-`, `user=fake` y `user=control` |
| Visibilidad en PCAP | filtros con VLAN sobre el archivado de la prueba | Kali→DC udp/53: 8 paquetes. Kali↔srv :80: 48. Kali↔srv :18081: 136, con 8×`HTTP/1.0 401` y 4×`HTTP/1.0 200` en claro. Los 3 nombres `preflight`/`pfmarca` en DNS. 16 apariciones del User-Agent `cf-preflight-2026-10-28` |
| Visibilidad en EVE | grep sobre `eve.json` | Eventos dns de los 3 nombres (query + answer NOERROR). Eventos http :80 200 y :18081 `/auth` 401/401/200 en las dos tandas. Eventos dns, flow, http y tls de .21–.26 desde 06:58 |
| Visibilidad en el motor y las features | `motor_decision.log` y `multilayer-v3.csv` | Kali en la ventana 07:04:00: `packet_count_10s` 48, `http_auth_failure_ratio_60s` 0,5, ALERT IF. Ventana 06:59:50: features 52 paquetes, pero el motor la evaluó con 0 (hallazgo §3). .21–.26: features con 24–1698 paquetes en 06:58:50; el motor las registró con 0 paquetes vivos |
| Seis perfiles legítimos | `systemctl` en clientes (06:57:34) | **`cyberflow-lab.target` inactive y disabled desde el 15-oct 11:11:50; 0 procesos.** adminclientes tiene NOPASSWD para `start/stop/restart cyberflow-lab.target` |
| Perfiles: una vuelta | p05c (06:58:39–45), con el código de cada perfil desde su IP .21–.26 | Las 6 vueltas terminan con todas las acciones ok y rc=0. El target sigue inactive y disabled. Las unidades no llevan `--intensidad` ni `--forzar-laborable` |
| Atribución | — | Origen y destino por IP en PCAP, EVE, `brute.log` y motor. Los perfiles tienen IP propias (.21–.26) distintas de la Kali (.30) y del bastión (.10.30). Las marcas de inicio y fin del generador más los relojes (§5) delimitan cada episodio |

**Error propio declarado.** El primer intento de vuelta única (`p05b`, 06:58:13–19) leyó solo la primera línea de un
`ExecStart` multilínea y salió desde **10.10.20.20**, no desde .21–.26. Se rehízo como `p05c` leyendo
`systemctl show -p ExecStart`. Se conservan los dos.

Los perfiles legítimos **no** se han sustituido por tráfico del bastión, ni se han cambiado escenarios, intensidades o
duraciones.

## 8. Continuidad

- **Persistencia del generador**:
  - Maneja solo SIGINT (KeyboardInterrupt), no SIGHUP ni SIGTERM. Los hijos de cada episodio llevan
    `start_new_session=True` y el generador no reanuda.
  - Por eso debe ir **dentro de `tmux` en la Kali** (instalado; linger off) y pararse con **Ctrl-C** dentro de la
    sesión.
  - En el bastión no hay tmux ni screen; solo nohup, setsid y systemd-run.
- **Archivador**: se lanza con `setsid nohup` en el sensor, guardando el PID; se para con SIGTERM a ese PID tras
  comprobar su cmdline, como en p11b. Su `ESTADO.txt` y `archivar.log` permiten vigilarlo.
- **Supervisión del avance**:
  - salida del generador en tmux;
  - `ESTADO.txt` del archivador;
  - `tail` de `motor_decision.log`;
  - feed y `nft list set` en srv-dmz (en sombra deben seguir vacíos);
  - `df -h` del sensor.
- **Dependencias de LAN**: sensor (captura, motor, Suricata, archivador), Kali, srv-dmz (web, `/auth`, agente),
  DNS/DC (zona local), clientes (perfiles), bastión (relé y punto de acceso) y el SPAN hacia ens37.
- **Dependencias de Internet**: el NTP de la Kali, srv-dmz y clientes. Si Internet falla durante la campaña, los relojes
  derivan lentamente; hay que medirlos de nuevo al terminar (`comprobar_relojes.sh`). El bastión no tiene Internet
  salvo NTP.
- **Hosts que deben seguir encendidos**: todos los anteriores, más pfSense.
- **Rotaciones**: si A cruza la medianoche UTC, `motor_decision.log` rota hacia las 00:00 (`create`) y `eve.json` rota
  con `copytruncate`. El análisis debe leer también el `.1`. Programar A sin cruzar la medianoche evita el problema.
- **Endpoint `ppi-brute-lab` en `disabled`**: no sobrevive a un reinicio de srv-dmz.
- **Pausan la campaña** (se reanuda en un episodio nuevo):
  - caída de la sesión tmux;
  - reinicio de la Kali.
- **Invalidan los episodios en curso**:
  - parada o reinicio de `ppi-motor` o `ppi-motor-capture` (cambia el NRestarts);
  - fallo del archivador (`FALLO` o `PERDIDO`);
  - salida de la sombra (sets no vacíos);
  - perfiles legítimos caídos;
  - desfase mayor de 1 s;
  - pérdida del SPAN.

## 9. Tabla de estado

| Componente | Comprobación actual | Evidencia | Estado | Pendiente |
|---|---|---|---|---|
| Máquinas encendidas y conectividad LAN | TCP/22 en 10 IP y servicios 53/80/443/18081 (06:54) | `out_p01.txt` | OK | — |
| Hashes de motor, extractor, heurísticos, publicador y modelo | sha256 frente a `config-campana.json` (06:56) | `out_p04_sensor_hashes.txt` | OK | — |
| Analizador HEAD: 7 configuraciones, umbrales y lector | Muestra real de 3000 registros, 0 incidencias | `out_compat_analizador.txt` | OK | — |
| Copias en la Kali (generador, esquema, escenarios) | Ausentes; la copia temporal de HEAD valida | `out_p06_kali.txt` | OK | Paso de inicio: copiar los bytes de HEAD y comprobar su sha256 |
| Copias en srv-dmz (sombra y restauración) | Ausentes; harness 11/11 en el portátil | `out_p07_srv.txt` | OK | Paso de inicio: copiar y comprobar el sha256 |
| Motor, captura y Suricata | Activos, NRestarts 0, fuentes legibles | `out_p02…`, `out_p03…` | OK | — |
| Cobertura de paquetes del motor en vivo | 241 de 2791 ventanas-entidad con tráfico evaluadas con 0 paquetes (24 % si se evalúan antes de 5 s) | `out_p15…`, `out_p16…` | NO VERIFICADO | Impacto por episodio no medido. **Decisión de Mark**: declararlo como limitación del sistema tal como está desplegado, o corregirlo antes de A (fuera de este preflight) |
| Captura full-SPAN en ens37 | argv sin filtro, multi-origen, 802.1Q | `out_p02…`, `out_p13b…` | OK | Usar filtros conscientes de VLAN en cualquier atribución manual |
| Archivador | Prueba de 07:03:36 a 07:04:50, rc 0, 80/80, sin huecos | `out_p11a…`, `out_p11b…` | OK | Paso de inicio: lanzarlo hacia el destino de la campaña |
| Pérdidas de tcpdump | Estadísticas del PID 1393 no disponibles | `out_p11b…`, `out_p13_visibilidad.txt` | NO VERIFICADO | Declararlas «no medidas». Cota NIC/PCAP 0,9996 en 90 s |
| Espacio en disco | 21 GB libres frente a unos 2 GB benignos en 5 h | `out_p11b…` | OK | Vigilar durante los ataques |
| Relojes | 5 hosts con \|desfase\| ≤ 20 ms, sincronizados | `out_p10b_relojes.txt` | OK | Medirlos otra vez al terminar A |
| Endpoint `/auth` | 401, 401, 200 y registro en `brute.log` | `out_p06…`, `out_p07…`, `out_p12…` | OK | Unidad `disabled`: no sobrevive a un reinicio |
| Zona DNS local | NOERROR `aa` para 3 nombres nuevos | `out_p06…`, `out_p12…` | OK | — |
| Visibilidad en PCAP, EVE, motor y features | Transacciones marcadas encontradas en las 4 fuentes | `out_p13…`, `out_p13b…` | OK | — |
| Perfiles legítimos | Target inactive y disabled desde el 15-oct; 1 vuelta correcta por perfil | `out_p05…`, `out_p05c…` | **BLOQUEO** | Arrancar `cyberflow-lab.target` (NOPASSWD de adminclientes) por decisión de Mark, más al menos 30 min de control normal antes del primer episodio |
| Estado de respuesta (sets y feed) | Sets vacíos a las 07:12; LIMIT residual a las 07:00 y LIMIT de la Kali por el preflight | `out_p07…`, `out_p14…`, `out_p17…`, `out_p18…` | OK | Paso de inicio: activar la sombra, guardar la escalada desde el sensor y verificar sets vacíos |
| Modo sombra | Herramientas y permisos disponibles; no ejecutado | `out_p07…`, harness 11/11 | NO VERIFICADO | Activar y verificar al iniciar A (prohibido en este preflight) |
| Continuidad (tmux, parada, recuperación) | tmux presente en la Kali; señales del generador analizadas | `out_p06…`, `out_p09…` | OK | Ejecutar A en tmux y pararla con Ctrl-C |

## Conclusión

**Preflight bloqueado.** Causas e intervención que necesita cada una:

1. **Los perfiles legítimos no están en marcha** (`cyberflow-lab.target` inactive y disabled desde el 15-oct). Sin ellos
   no hay control normal ni tasa de falsos positivos. Se arregla con
   `[CLIENTES adminclientes] sudo systemctl start cyberflow-lab.target`. Tengo NOPASSWD, pero no lo arranco sin tu
   decisión, porque es un cambio de servicio. Después hacen falta al menos 30 min de control normal antes del primer
   episodio.
2. **Decisión pendiente sobre la cobertura del motor en vivo.** Un 8,6 % de las ventanas-entidad con tráfico se evalúan
   con 0 paquetes. Hay que decidir si se acepta y se declara como limitación del sistema tal como está desplegado, o si
   se corrige antes de A. Corregirlo cambiaría el motor y queda fuera de este encargo.

Una vez resueltos, los pasos de inicio son estos y no forman parte de este preflight:

1. Copiar a la Kali el generador, el esquema y los escenarios (con su sha256), y a srv-dmz la sombra y la restauración.
2. Guardar `estado.json` desde el sensor y activar el modo sombra.
3. Verificar sets vacíos y que el agente está detenido y enmascarado.
4. Lanzar el archivador hacia el destino de la campaña.
5. Lanzar el generador dentro de tmux.
6. Medir los relojes al inicio y al final.

Solo después de activar y verificar la sombra podría declararse «Listo para lanzar ataques». **Esa declaración no se
hace aquí.**
