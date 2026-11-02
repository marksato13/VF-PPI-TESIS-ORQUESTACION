# Estado observado del laboratorio antes de la Etapa 4

Lecturas del **2026-11-02**, entre las 19:06 y las 19:26 UTC. Solo lecturas: nada se reinició, instaló ni modificó, y `sudo` solo se usó para listar (`sudo -n -l`). Los guiones y sus salidas completas están en [evidencia/lectura-laboratorio/](evidencia/lectura-laboratorio/).

> **Corrección.** El cierre técnico de la Etapa 3 (`../etapa3-cierre-tecnico-2026-11-02/PROCEDIMIENTO-ETAPA4.md`) decía que Sensor1 ejecuta `7b275b8` y que bastaba un `git switch` en `~/cyberflow`. **Las dos cosas son falsas:**
> - El motor cargado es **24f8a80** (instalado en el paso 2, el 2026-11-01 a las 03:14 UTC).
> - El publicador, `escalada.py`, el panel y `cyberflow.toml` son la instantánea **as-deployed f57ca00**.
> - `~/cyberflow` **no es un checkout de git**.
>
> Ese procedimiento queda sustituido por [PROCEDIMIENTO-ETAPA4.md](PROCEDIMIENTO-ETAPA4.md).

## 1. Código en disco frente a código cargado

### 1.1 Proceso del motor (`ppi-motor`)

| Dato | Valor observado | Fuente |
|---|---|---|
| Unidad | `/etc/systemd/system/ppi-motor.service`, generada por `cyberflow_config.py`, **sin drop-ins** (`DropInPaths=` vacío), *enabled/active*, `NRestarts=0` | `s1_inventario.txt` |
| Proceso | PID 1289322, usuario m4rk, `cwd=/home/m4rk/cyberflow`, `exe=/opt/python3.14/bin/python3.14` (vía `.venv/bin/python`) | `s1_detalle.txt` |
| Arranque exacto | 2026-11-01 03:14:00.51 UTC: `btime` 1793389991 + 11284951/100 ticks = 1793502840,51 | `s1_detalle2.txt` |
| Argumentos | `--eve-path /var/log/suricata/eve.json --capture-dir /var/lib/ppi-motor-capture --model-path …/limpio-2026-10/if_limpio_2026_10_desplegable.joblib --manifest-path …/manifest-if-limpio-2026-10.json --detector-name if_limpio_2026_10 --schema …/multilayer-v2.json --entity-network 10.10.0.0/16 --excluir <11 IP> --excluir-protocolos 112,240 --log-path …/motor_decision.log --step-seconds 10 --history-seconds 230` (literal en `banco/observado-sensor1/ppi-motor.service` de la rama) | `/proc/1289322/cmdline` |
| Sin `--enforce` | ni en la unidad ni en el proceso | ídem |
| Endurecimiento | `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateDevices`, `ReadWritePaths=/home/m4rk/cyberflow/logs`, `ReadOnlyPaths=/var/lib/ppi-motor-capture /var/log/suricata`, `StandardOutput=null` | unidad |
| Dependencias | Python 3.14.4, scikit-learn 1.9.0, numpy 2.5.1, joblib 1.5.3 | `s1_detalle.txt` |

### 1.2 Procedencia de cada fichero

Se compara el sha256 de los 77 ficheros de `scripts/`, `configs/` y `deploy/` del Sensor1 con el blob de cada commit (`procedencia.py`, salida `procedencia.json`). Ficheros iguales:

| Commit | Iguales (de 77) |
|---|---|
| `24f8a80` | 23 |
| `7b275b8` | 22 |
| as-deployed `f57ca00` | 29 |
| `ec78ca5` | 18 |

Ficheros que importa el motor y ficheros de la cadena v1 (I = igual, D = distinto, – = ausente en el commit):

| Fichero | sha256 (12) | 24f8a80 | 7b275b8 | f57ca00 | ec78ca5 |
|---|---|---|---|---|---|
| `scripts/engine/motor_decision.py` | 6c274d9e3529 | **I** | D | D | D |
| `scripts/engine/motor_incremental.py` | a403307aa5f7 | **I** | – | – | D |
| `scripts/engine/heuristicos.py` | 10deb05d22fa | **I** | I | I | D |
| `scripts/engine/feed.py` | b4d36adb3f29 | **I** | I | I | D |
| `scripts/engine/vista_vivo.py` | 94d3df28ae21 | I | I | I | I |
| `scripts/features/extract_multilayer_v2.py` | 7130edae65af | I | I | I | I |
| `scripts/features/extract_multilayer_v3.py` | 5adbfbf48455 | I | I | I | I |
| `scripts/features/acumular_v3.py` | 9c35b831453d | I | I | I | I |
| `scripts/engine/publicar_feed.py` | f7bc4c7d8e7a | D | D | **I** | D |
| `scripts/engine/escalada.py` | 7d80ab4a9264 | D | D | **I** | D |
| `scripts/engine/dashboard.py` | b07fb57a22eb | D | D | **I** | D |
| `configs/cyberflow.toml` | 18bd43be2310 | D | D | **I** | D |
| `configs/features/multilayer-v2.json` | e032a1a28650 | D\* | D\* | D\* | D\* |

\* `multilayer-v2.json` solo difiere por finales CRLF: 37 CR en 4 114 bytes. Normalizado es idéntico (ya constaba en el 3A).

**Qué está en disco:** el conjunto de importaciones del motor (`motor_decision`, `motor_incremental`, `heuristicos`, `dns`/`http`: no existen en 24f8a80, y `motor_decision` de 24f8a80 no los importa) coincide con 24f8a80. La cadena v1 es f57ca00, igual que en el protocolo 3B.

**Qué está cargado: evidencia fuerte, no criptográfica.**

- **Fechas de los ficheros importados.** Todos tienen `mtime = ctime` anterior o igual al arranque:
  - `motor_decision.py` y `motor_incremental.py`: 1793502840, el mismo segundo que el arranque (.51), es decir, se copiaron justo antes del `restart`;
  - `heuristicos.py`: 1792036108;
  - `vista_vivo.py`: 1791649962;
  - `feed.py`: 1790797943;
  - esquema: `ctime` 1789673142.

  Ninguno ha cambiado después de que el proceso los importara.
- **Registro de arranque.** `motor_startup` (ts 1793502843,23) dice `procesamiento: incremental`, umbral −0.5693969936322356 y 7 490 `claves_previas_cargadas`.
- **Formato de las decisiones.** Las últimas **no** traen `decision_if`, `auth_failure`, `dns_vista` ni `http_vista`, como corresponde a 24f8a80 (los añade la Etapa 3).

**Límite declarado:** no hay una prueba criptográfica del código en memoria. Python no conserva el fuente, y `__pycache__` de `scripts/engine` pertenece a root desde el 1-oct: su contenido está **sin listar**. Para la Etapa 4, `comprobar_importaciones.sh` registra con `python -v`, antes de arrancar, de qué fichero se carga cada módulo, y el procedimiento compara el `cmdline` del proceso después.

### 1.3 Modelo, escalador, esquema, configuración y umbral

| Elemento | Valor |
|---|---|
| Modelo desplegable | `if_limpio_2026_10_desplegable.joblib` sha256 `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60`, igual al `model_sha256` del manifiesto |
| Manifiesto | `manifest-if-limpio-2026-10.json` sha256 `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7` (19-oct). `isolation_forest_pipeline`: **el escalador va dentro del pipeline**. 28 características. Umbral −0.5693969936322356 (`score_samples`, α 0,05) |
| Esquema | `configs/features/multilayer-v2.json` sha256 `e032a1a28650d438ae707c93b3045801770b3a069b4395426077af3bbd2b0e33` (CRLF) |
| `cyberflow.local.toml` | sha256 `5b15774937299f7178be75516cb43efebfa7742c8268332f165285eb17e3167a`. Su `umbral = 1.8126…` es **obsoleto y no se usa**: el motor toma el del manifiesto y lo anota en cada decisión. Su `mac_esperada 00:0c:29:15:7c:02` ≠ la MAC actual de ens37 `00:0c:29:3d:f9:4e` (no se actualizó tras la restauración del 30-oct) |

La Etapa 4 **no cambia** nada de esta tabla.

## 2. Captura, Suricata y salud

| Elemento | Observado |
|---|---|
| `ppi-motor-capture` | PID 1375 desde 2026-10-30 19:55:21. `tcpdump -i ens37 -n -s 0 -U -B 65536 -Z tcpdump -w /var/lib/ppi-motor-capture/live-%Y%m%d%H%M%S.pcap -G 15`. tcpdump 4.99.4 y libpcap 1.10.4 (TPACKET_V3). `getcap` vacío |
| Anillo | 62–76 ficheros, `tcpdump:m4rk` 2750. `cyberflow-limpieza.timer` cada 5 min borra los de más de 15 min. Salto entre inicios de 15–16 s (el redondeo de `-G` al segundo) |
| ens37 (vmxnet3) | promiscuo; gro/lro/tso/gso off; IPv6 off; `rx-vlan-offload` on. A las 19:25:12: `rx_packets` 68 575 027; **`rx_dropped` 3 610 040**, que crece de forma regular (+140 cada 10 s); `rx_missed/fifo/over_errors` = 0 |
| Filtro VLAN | `tcpdump -d -y EN10MB 'tcp or (vlan and tcp)'` compila sin privilegios, con la rama 0x8100/0x88a8 |
| Suricata | 7.0.3, PID 1372 desde 2026-10-30 19:55:21; af-packet ens37, `cluster_flow`, 4 hilos, `stats.log` cada 8 s. Contadores acumulados: 18:10:17 → 66 255 033 paquetes / 19 622 descartes; 19:10:09 → 68 297 135 / 22 938, es decir, **+3 316 descartes de +2 042 102 paquetes (0,16 %) en esa hora**. Entre 19:25:05 y 19:25:37: 0 descartes en 4 300 paquetes. Los descartes llegan **a ráfagas**. `tcp.reassembly_gap` 1 035 409 |
| Rotación de Suricata | logrotate diario, `maxsize 500M`, `copytruncate` + HUP; `eve.json` 395 MB |
| Motor | `motor_decision.log` con logrotate de cyberflow (diario, 200M, rotate 14). `_state/ciclos.jsonl`: ciclos de 0,22–0,67 s; `inicio_ciclo − marca_pcap` 3,8–14,5 s; 4–12 ventanas pendientes |
| Relojes | Sensor1, bastión, srv-dmz y cliente sincronizados por NTP; Sensor1 contra 10.10.60.1 |

**Muestreo de salud en vivo.** `salud_captura.py muestrear` se ejecutó 4 veces cada 10 s, solo leyendo. Salida en `evidencia/salud-en-vivo/`:

- interpreta los formatos reales de `stats.log`, sysfs, el anillo, `ciclos.jsonl` y systemd;
- `/proc/1375/io` (tcpdump con `-Z`) da `PermissionError` y queda como `null` con su motivo, no como 0;
- clasificar ese tramo da **C3** («tcpdump sin lecturas SIGUSR1 que acoten el periodo»): es el comportamiento buscado. Sin estadísticas de tcpdump no se presume C0.

## 3. Cadena de publicación, relé y agentes

| Host | Componente | Estado observado |
|---|---|---|
| Sensor1 | `ppi-publicar-feed.timer` (v1, cada 10 s) | activo. `publicar_feed.py --umbrales 2026-10-06.1`; `feed.json` declara `2026-10-06.2`. En la lectura, 0 entradas (en una pasada anterior, `limit` 3). `estado.json` con todos los `bloqueos` a 0. Llaves en `artifacts/feed-keys` (`priv.pem` 0600, **no se leyó**) |
| Sensor1 | v2 / vía rápida | **no instalados**: no hay `~/feed-v2` ni unidades v2 |
| Sensor1 | sudo de m4rk | `(ALL:ALL) ALL` con contraseña, más NOPASSWD para `systemctl show/status/is-*`, `journalctl`, `nft list *`, restart de ppi-motor/captura/suricata, `daemon-reload`, enable/disable de unidades concretas y `/usr/local/sbin/cf-capturar` (`timeout tcpdump host 10.10.20.30`) |
| Sensor1 | `authorized_keys` de m4rk | una llave ed25519 (`vm-gestion-to-cyberflow`), sin opciones |
| Bastión | `ppi-relay-feed.timer` (v1, `*:*:03/10`) | activo. `/home/gadmin/relay-feed.sh` sha256 `294fe7e2…` hace scp del feed del sensor (llave `cyberflow-to-sensor`) a `adminsrvdmz@10.10.30.10:/home/adminsrvdmz/enforce/` (llave `cyberflow-to-srv`). **Funciona**: el `feed.json` de srv-dmz se actualizó a las 19:11:56. Sin `/opt/cyberflow` |
| srv-dmz | `ppi-enforce-agent.timer` / `.service` (v1) | **disabled / inactive**. La unidad lleva `--aplicar --sudo`. `agente_enforce.py` del 15-oct 21:32. `shadow.log` escrito por última vez el 06-oct |
| srv-dmz | `ppi-brute-lab` | disabled / inactive |
| srv-dmz | v2 | no existen `/etc/cyberflow`, `/opt/cyberflow`, `/var/lib/cyberflow` ni las cuentas `cffeed`/`cfagente`. Python 3.12.3, OpenSSL 3.0.13, `/usr/sbin/nft`, systemd 255 |
| srv-dmz | sudo de adminsrvdmz | `NOPASSWD: ALL` y `/usr/local/sbin/cf-nft-mostrar` |
| srv-dmz | **reglas nft efectivas** | **no leídas** (requieren root): **pendiente**, con `CON_SUDO=1 respaldo_srvdmz.sh` |
| DC1 `VM-AD-DC` (10.10.10.20) | — | sin unidades `ppi-*` y sin `/etc/cyberflow` ni `/opt/cyberflow`; nft **no leído** (pendiente) |

## 4. Tráfico legítimo, Kali y piloto-con-dns

| Elemento | Observado |
|---|---|
| Cliente `clientesadmin` (10.10.20.20) | seis perfiles (`cyberflow-lab-{ofimatica,navegacion,descargas,aplicacion,ligero,erratico}`) activos desde el **2026-11-01 10:36:59 UTC**. Unidades *disabled* al arranque. `clientes_lab.py` **sin** envoltorio (curva horaria natural) con `--servidor 10.10.30.10 --dns 10.10.10.20`. `clientes_lab.py` `ae5134a7…`, `clientes_config.py` `9aa2e2e0…`. VM en UTC |
| Curva horaria (UTC) | 8–13 h ×1,0; 13–15 h ×0,55; 15–19 h ×0,9; 19–23 h ×0,35; resto ×0,12. Fin de semana ×0,3. Intensidad por defecto 1,0, sin `--forzar-laborable`. Ritmos: ofimática 3,0; navegación 1,5; descargas 8,0; aplicación 2,0; ligero 12,0; errático 5,0 (ráfagas ×6) |
| Kali (10.10.20.30) | encendida, sin procesos de ataque (`nmap`, `curl`, `dig`, etc.) |
| **piloto-con-dns** | la última fila del dataset con esa etiqueta es del **2026-09-30T03:20:50** (365 680 filas). El acumulador usa ahora `--campaign-id linea-base`. **No hay prueba de que la campaña se cerrara formalmente** (ni registro de cierre ni decisión escrita): queda como **condición pendiente**, a confirmar por Mark antes de instalar. No se da por terminada |

## 5. Qué cambia la Etapa 4 respecto a este estado

| Componente | Hoy | 4A (sombra) | Reversión |
|---|---|---|---|
| Motor | 24f8a80 en `~/cyberflow`, periódico, `_state` | ec78ca5 en `~/cyberflow-e4/ec78ca5` (drop-in), `--disparo eventos`, `_state-e4`. Mismos modelo, manifiesto, esquema, red, exclusiones, paso, horizonte y log | retirar el drop-in: vuelve el `ExecStart` base, sin tocar `~/cyberflow` |
| Anillo | `-G 15` | `-G 5` (drop-in) | retirar el drop-in |
| Publicador v1, relé v1, panel, acumulador | activos | **sin cambios** | — |
| Publicador v2, vía rápida, estadísticas SIGUSR1 | no existen | nuevos, en sombra | parar, deshabilitar y borrar sus unidades. La evidencia se conserva |
| Relé v2 | no existe | bastión → srv-dmz (sin DC1), con llaves nuevas de comando forzado | parar y retirar; las llaves de Sensor1 y srv-dmz se retiran de sus `authorized_keys` |
| Agente v2 dmz | no existe | **sin `--aplicar`** | parar, desinstalar y borrar las cuentas; la traza se copia |
| Agente v1 srv-dmz | disabled/inactive | **sin cambios** | — |
| DC1 | sin CyberFlow | **sin cambios** | — |
