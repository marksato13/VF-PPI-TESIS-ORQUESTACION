# Procedimiento para continuar la 4A (reconciliado, 2026-11-03). Preparado; **no ejecutado**

Este documento **no** sustituye a `etapa4-preparacion-2026-11-02/PROCEDIMIENTO-ETAPA4.md`: añade la fase **P0**
(cadena v1 sin aplicar), cambia el origen del paquete (rama de recuperación), fija los hashes y explica cómo se
garantiza la sombra y cómo se diagnostican los descartes. Los pasos §3–§7 de aquel procedimiento siguen valiendo
tal cual, salvo lo que se indica aquí. Secuencia: **4A** (instalación y validación técnica en sombra) → **4B**
(control normal nuevo) → **4C** (campaña A nueva en sombra) → campaña B con respuesta activa. Cada fase se pide
aparte.

## 1. Conjunto exacto que se propone instalar

| Pieza | Origen | Hash |
|---|---|---|
| Código instalado (motor, extractor, publicador v2, agente v2, relé v2, esquema, helper) | **ec78ca5** `ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742`, extraído por `paquete_candidata.sh`, que para si el código difiere | `evidencia/paquete/SHA256SUMS` (86 ficheros) |
| Herramientas de instalación (`deploy/etapa4`, `scripts/etapa4`) | rama **`recuperacion/etapa4a-20261103` @ b2f2994** (desciende de 3a9f26b) | ídem |
| `motor_decision.py` / `motor_incremental.py` | ec78ca5 | `b652582d…dfc565` / `95f3cd2e…0146d2` |
| `heuristicos.py` (2026-11-02.1) / `http_heuristica.py` | ec78ca5 | `5d30ffe6…217f68` / `a97c98ba…df3fdc` |
| `publicar_feed_v2.py` (`--politica if_senal`) / `escalada.py` / `feed.py` | ec78ca5 | `5733f17d…4002a2` / `0be76d51…7c9fe1` / `9aca9ddf…b592ce` |
| `agente_enforce_v2.py` / `cf_nft_helper.py` | ec78ca5 | `00b9d7ba…874779` / `3ba6374f…3c9c87` |
| `relay_eventos.py` / `detector_rapido.py` | ec78ca5 | `e24aefb2…3a810f` / `506ae603…26908d` |
| `extract_multilayer_v2.py` / `multilayer-v2.json` (copia del paquete) | ec78ca5 | `7130edae…636ccb` / `1445ccd4…3be90d` |
| `estado_sombra.py` / `vigia_4c.py` / `salud_captura.py` / `trafico_observado.py` | 3a9f26b = b2f2994 | `8a1417bf…0ff50e` / `62260830…77753d` / `0ed014cc…2594ef` / `bfa29d48…1cd8e4` |
| `instalar_srvdmz_sombra.sh` (condición previa v1) | **b2f2994** | `8d75646a…f2bbdb` |
| Drop-ins y unidades | b2f2994 (sin cambios desde 3a9f26b) | `ppi-motor…/etapa4.conf` `b4b75984…e16a5e`; `ppi-motor-capture…/etapa4.conf` `4465061f…865b9e`; `ppi-publicar-feed-v2.service` `afb71549…a1d88a`; `ppi-via-rapida@.service` `ee29d58c…8ae1c6`; `ppi-enforce-agent-v2-dmz.service` `2b5990e5…893c76`; `ppi-relay-eventos.service` `ae5b85f1…f26c48` |
| Modelo / manifiesto (no se copian: el drop-in apunta a los del Sensor1) | Sensor1 | `df547da0…a2fd60` / `b3ad6805…aa2a9e7` |
| Esquema que lee el motor (`--schema`, el del Sensor1) | Sensor1 | blob `9560ce9`, semánticamente igual al de ec78ca5 |

Herramientas de análisis y guiones (repositorio de documentación):

| Pieza | Hash | Nota |
|---|---|---|
| `herramientas/analizar_3b.py` | `4ff7d8f7…57e9` | sustituye al de `scripts/` en `~/cf-e4/herramientas` |
| `herramientas/referencia_trafico_4c.py` | `6735f649…1aae` | ídem |
| `herramientas/herramientas-e4.sha256` | — | sustituye al de `etapa4-preparacion`; las otras 10 líneas son iguales |
| `guiones/g01_lanzar_bateria_e4.sh` | `936e1605…ca63` | sustituye al g01 del 2-nov (que se conserva) |
| `guiones/k20_canal_control_simulado.sh` | `a080fc12…5fe2` | nuevo (4B y control de la 4C) |
| `guiones/r4.sh` | `74d4d085…73fa` | copia idéntica del de la preparación |
| `scripts-4c/generar_campana.py` (con compuerta) | `99e6bdae…` | sin cambios. El original `scripts/generar_campana.py` (`c586d813…`) se conserva |

Dependencias que ya están en el laboratorio y no cambian: el venv del Sensor1 (Python 3.14.4, sklearn 1.9.0,
numpy 2.5.1, joblib 1.5.3), la clave de firma del feed (`artifacts/feed-keys/priv.pem`, que vive solo en el
Sensor1), Suricata, el SPAN a ens37 y el endpoint `ppi-brute-lab` (`10.10.30.10:18081/auth`, disabled hasta la 4C).
Nuevas, creadas por los instaladores: el par de claves del relé v2, las cuentas `cffeed`/`cfagente` y el sudoers
del helper en srv-dmz.

## 2. Fase P0 (nueva): la cadena v1 deja de aplicar

**Por qué.** El 2-nov el agente v1 estaba disabled/inactive. Desde el 03-nov 02:50 UTC (demo) está enabled/active
con `--aplicar --sudo`. A las 01:04 UTC del 04-nov mantenía un LIMIT a **10.10.20.21**, un cliente legítimo. Con el
v1 aplicando, la 4A no es sombra (`estado_sombra.py` rc 1) y cualquier control posterior queda contaminado.

**Quién.** `→ lo ejecutas tú` (Mark): modifica reglas activas y unidades con sudo, y este encargo no lo autoriza.
Pide autorización expresa antes de hacerlo.

1. **Respaldo del estado de la demo.** `[LAPTOP Git Bash → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecutas tú
   (`CON_SUDO=1`, lee el ruleset):

   ```
   CON_SUDO=1 bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/respaldo_srvdmz.sh   # → ~/respaldos-etapa4/srvdmz-<UTC> (anótalo como «estado demo»)
   ```

2. **Parar y deshabilitar el v1 y retirar su tabla.** `[SRV-DMZ adminsrvdmz]` → lo ejecutas tú.

   ```
   sudo systemctl disable --now ppi-enforce-agent.timer
   sudo systemctl stop ppi-enforce-agent.service
   sudo nft list table inet cyberflow > ~/respaldos-etapa4/tabla-v1-antes-de-retirar-$(date -u +%Y%m%dT%H%M%SZ).nft
   sudo nft delete table inet cyberflow
   ```

3. **Comprobación.** `[SRV-DMZ adminsrvdmz]` → lo ejecuto yo (lectura):
   `systemctl is-enabled ppi-enforce-agent.timer; systemctl is-active ppi-enforce-agent.timer; sudo -n nft list tables`.
   - **Esperado:** `disabled`, `inactive` y ninguna `table inet cyberflow`.
4. **Respaldo base de la 4A.** Se repite el paso 1. Ese `srvdmz-<UTC>` es el `<RESPALDO_SRVDMZ>` contra el que comparan
   `estado_sombra.py`, `revertir_srvdmz.sh` y `g01`.

**Reversión de P0** (volver a la demo): `sudo nft -f <tabla-v1-…>.nft && sudo systemctl enable --now ppi-enforce-agent.timer`.
El agente rehace sus sets en el siguiente ciclo.

**Sensor1 y bastión en P0.** No se tocan. El publicador v1 (`ppi-publicar-feed.timer`), el relé v1 y el panel
siguen como están; sin agente v1 que aplique, el feed v1 solo se publica y se entrega.

## 3. Instalación (PROCEDIMIENTO-ETAPA4 §3–§5, con estos cambios)

1. **Paquete.** `[LAPTOP Git Bash]` → lo ejecuto yo, desde `producto-recuperacion` (rama de recuperación):
   `bash deploy/etapa4/laptop/paquete_candidata.sh <salida>`. Las líneas de código de `SHA256SUMS` deben coincidir con
   `evidencia/paquete/SHA256SUMS`. `VERSION-ETAPA4` cambia en cada construcción porque lleva la hora.
2. **Respaldos** de Sensor1 y bastión (§3 del procedimiento). El de srv-dmz es el del paso 4 de P0.
3. **Instalación en sombra** (§4): `instalar_sensor1_sombra.sh` fases 0–5, `instalar_bastion_sombra.sh`, e
   `instalar_srvdmz_sombra.sh`, que ahora **para** si P0 no está hecha.
   `→ lo ejecutas tú` lo que pide sudo con contraseña (como el 2-nov).
4. **Comprobaciones** (§5): `verificar_sensor1.sh`, `verificar_bastion.sh`, `verificar_srvdmz.sh` (con
   `CON_SUDO=1`), y ≥ 60 min de observación sin tramos C2/C3 (§5.3).

## 4. Cómo se garantiza la sombra (todas obligatorias, fallo cerrado)

| Comprobación | Dónde | Esperado |
|---|---|---|
| El argv del motor sin `--enforce`; el motor es el candidato | Sensor1 (`verificar_sensor1.sh`, g01) | `candidato=1 enforce=0` |
| La unidad v2 sin `--aplicar` | instalador (grep) y `estado_sombra.py` | para si lo lleva |
| Ningún proceso de agente con `--aplicar`, ni v1 ni v2 (argv real, no `pgrep`) | `estado_sombra.py --alcance completo` | rc 0 `estado=sombra` |
| Timer v1 disabled/inactive y sin tabla v1 | instalador corregido y `estado_sombra.py` | para (instalador) o rc 1 / 3 |
| La traza del agente v2 sin eventos `aplicacion` | `verificar_srvdmz.sh` | 0 eventos |
| El ruleset igual al respaldo base (sin contadores) | `revertir_srvdmz.sh` / `estado_sombra.py --respaldo` | sin diferencias |
| Durante 4B/4C | vigía cada 300 s | rc ≠ 0: X2, se cancela |

**El panel no sirve como prueba de sombra ni de publicación durante 4A–4C.** El ca66db5 calcula su propia acción
con la política v1 sobre el mismo `motor_decision.log` (COMPARACION-COMPONENTES §4). La evidencia de lo publicado
sale de `~/feed-v2/traza.jsonl` y `senales-if.jsonl`; la de lo aplicado, de la traza del agente v2.

## 5. Diagnóstico de los descartes de captura y de Suricata (solo lectura)

`[SENSOR1 m4rk]` → lo ejecuto yo, durante la observación de la 4A.

1. **Anillo y vía rápida (tcpdump).** El timer `cf-tcpdump-estadisticas` envía SIGUSR1 cada 30 s. Se exportan con
   `sudo -n journalctl -u ppi-motor-capture …` y `-u ppi-via-rapida@ens37 …` (SALUD-CAPTURA §5) y se clasifican con
   `salud_captura.py intervalos` + `clasificar`. `dropped by kernel` > 0 en un tramo da C2. Antes de la 4A hace
   falta `sudo -n journalctl` para m4rk (pendiente C de la preparación).
2. **Suricata.** En `stats.log` (`capture.kernel_drops`, `capture.kernel_packets`), por intervalo de 8 s, con el
   muestreador de SALUD-CAPTURA §5. Para atribuir las ráfagas, en el mismo periodo:
   - rotación de `eve.json` (`ls -l --time-style=+%s /var/log/suricata/`, `logrotate` con `copytruncate`) frente a
     los instantes de descarte;
   - ráfagas por intervalo en el PCAP archivado (la herramienta `s71_rafagas_pcap.sh` del 3B), frente a los perfiles
     `descargas`/`erratico`;
   - hilos y `cluster_flow`: `grep -nE 'threads|cluster-type|ring-size' /etc/suricata/suricata.yaml` (lectura), y la
     CPU por hilo en `muestras.jsonl`.
   Si se identifica una causa, la corrección se propone aparte y **no** se aplica en este encargo. Si no se
   identifica, la 4C sigue siendo posible con el riesgo declarado de episodios C1, que van fuera de la población
   principal (solo C0 entra, PROTOCOLO-4C corregido §6).
3. **Interfaz.** `ip -s link show ens37` (`rx_dropped`): se informa sin clasificar.

## 6. Reversión de la 4A

Sin cambios respecto a PROCEDIMIENTO-ETAPA4 §7: `revertir_sensor1.sh`, `revertir_bastion.sh` y
`revertir_srvdmz.sh` contra los respaldos de §3 (el de srv-dmz es la base de P0). Revertir la 4A **no** vuelve a
activar el agente v1. Volver al estado de la demo es la reversión de P0 (§2), que es otra decisión.

## 7. Pendientes antes de instalar (bloqueos)

| # | Pendiente | Quién | Estado |
|---|---|---|---|
| B1 | P0: el agente v1 aplica (LIMIT a .21) | Mark, con autorización | **bloquea** |
| B2 | Petición escrita de la 4A (C1 de la preparación) | Mark | pendiente |
| B3 | `sudo -n journalctl` para m4rk (SIGUSR1) | Mark | pendiente (2-nov) |
| B4 | Aceptar el canal SSH persistente con la Kali, en la 4C **y en el control** (`k20`) | Mark | pendiente |
| B5 | Copiar `scripts-4c/` a la Kali y verificar c03 (seis hashes) | yo, con permiso para la Kali | pendiente (es 4C) |
| B6 | Coste del vigía en vivo | se mide en la 4A | pendiente |
| B7 | Panel frente a feed v2: no hay correspondencia | decisión: aceptar que la evidencia no sale del panel, o adaptarlo antes de la 4B | abierto |
| B8 | Descartes de Suricata sin causa (I5 exige 0 en 30 min para la 4C) | diagnóstico en la 4A (§5) | abierto |
