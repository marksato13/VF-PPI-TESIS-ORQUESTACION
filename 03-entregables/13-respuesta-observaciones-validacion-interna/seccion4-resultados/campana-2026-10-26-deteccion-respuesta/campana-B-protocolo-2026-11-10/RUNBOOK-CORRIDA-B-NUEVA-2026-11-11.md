# RUNBOOK y estado de la nueva Campaña B (11-nov-2026) — punto de reanudación operativo

**Autorización de Mark (11-nov ~04:00Z):** nueva Campaña B de 25 episodios con `g01c`, `--aplicar` SOLO sobre Kali 10.10.20.30; incluye muestreador de srv-dmz y envoltorio de clientes (E4). Control de 30 min y respaldo de srv-dmz ANTES de activar el agente; si algo previo falla, PARAR antes de lanzar y avisar. Avisar al arrancar (ID de corrida, hora, ruta de evidencia). Cierre: retorno a sombra, evidencia conservada, balance de los 25 con E1–E5 e indeterminados/no evaluables. E3 = `CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md` (LIMIT: SPAN o salida con hora; BLOCK: SPAN única). D5 a fin + 75 s (g01c).

## Reglas duras
- Durante el control de 30 min: **ningún SSH a Kali ni a srv-dmz** (salvo el canal simulado `k20`). Durante la batería: vigilar desde el bastión y **sin ssh a la Kali**.
- Cualquier fallo tras activar `--aplicar`: reversión inmediata (`b_revertir_srvdmz.sh` con `CF_MODO=real`, ejecutado por mí en srv-dmz: `adminsrvdmz` tiene NOPASSWD ALL) y aviso a Mark. `cf-b-fin` revierte solo a las 8 h.
- Sin sudo de Mark: el armado de logrotate (`cf-4b-rotacion armar`) NO se hace (próxima rotación diaria 2026-11-12 00:00Z, fuera de la ventana ≈ 04:30–11:00Z); anotarlo en el balance.
- No `cd` a rutas > 260 caracteres.

## Hosts y rutas
Bastión `gadmin@10.10.10.30` (alias ssh: sensor1, kali, srvdmz, clientes). Scripts locales: `...\campana-B-protocolo-2026-11-10\guiones\` (g01c, b_activar_srvdmz, b_revertir_srvdmz, b_r6_control, b_r7_sensor, k01_clientes_factor1_tx_e4) y `...\etapa4-4b-enmienda-p1-2026-11-08\guiones\s10_sensor_archivo_e4.sh` y `...\etapa4-preparacion-2026-11-02\guiones\b01_bastion_control_e4.sh`. Ejecutores: `scratchpad\run_react.ps1 -Hop {local|sensor|kali|srvdmz|clientes} -Script X.sh` (envía el guion por base64; ojo: el texto del guion queda en el argv del `bash -c`: en `pgrep -f` usar `[x]` para no autocoincidir).

## Secuencia
1. **Preparación (observación, reversible):** apartar `~/cf-e4/4c` de clientes (evidencia de B2) · srv-dmz: `sudo -n systemctl start ppi-brute-lab` + `c05_brute_prep_e4.sh completa` desde el bastión (401/401/200/404) · muestreador srv-dmz (`cf_d5_instrumentacion.sh srvdmz iniciar --aplicar`) · Sensor1 `s10_sensor_archivo_e4.sh 4c` + muestreo de espejo 1 s de `ens37` (1800 s) · clientes `k01_clientes_factor1_tx_e4.sh 4c`.
2. **Espejo estricto 30 min:** 0 s < 20 pkt/s (formato del log: `HH:MM:SS rx_packets rx_dropped` por segundo).
3. **Control 30 min:** `b01_bastion_control_e4.sh 4c <DESDE> <HASTA> <INICIO_ARCHIVO>` (DESDE ≥ INICIO_ARCHIVO + 230 s, y ≥ factor 1,0 + 230 s) + `k20_canal_control_simulado.sh`. Revisar 0 propuestas/0 señales. I1–I8: `p10b_relojes.sh`, `clasificar_periodo.py` (periodo terminando 75 s antes de la lectura), `i5`, verificadores del paquete a1cea5e (Sensor1 con umbral α=0,01 en `~/cf-b/verif-B`).
4. **Respaldo srv-dmz y activación:** estado previo (PRE-B) · `CF_SRC_REVERSION=<b_revertir_srvdmz.sh> CF_MODO=real bash b_activar_srvdmz.sh` · `g01c_lanzar_bateria_b_d5.sh <HASTA_CONTROL_ISO> srvdmz-p4-fase-c-20261106T043944Z`.
5. **Durante:** monitor desde el bastión (puerta D5, vigía, marcas), criterios P1–P5 / X1–X3 del vigía B; si se cancela: reversión.
6. **Cierre:** `b20`, `s20`, `s30`, `s40` v3, reversión R0–R7 (`b_revertir_srvdmz.sh`, `b_r6_control.sh`, `b_r7_sensor.sh`), parar brute-lab/muestreador/envoltorio de clientes (`clientes_restaurar.sh`), apartar `4c`, análisis `analizar_b.py` + `e3_v2` (BLOCK_ADMITE_SALIDA=False).

## Estado (actualizar en cada hito)
- 04:07Z: preflight v3 26 OK/0 FALLAN/1 PENDIENTE (logrotate diario). Sensor1: todos los servicios activos NR=0, motor α=0,01 (umbral −0,6223889502095352), captura y EVE vivos, 38 GB libres, sin `~/cf-e4/4c`. Clientes: 6 perfiles, 1 proceso cada uno (sin duplicados), `~/cf-e4/4c` con restos de B2 (por apartar). Scripts nuevos: `k01_clientes_factor1_tx_e4.sh` (sha db25c8bd…).
- 04:14Z preparación en marcha: brute-lab activo (401/401/200/404 OK), muestreador srv-dmz vivo (sets vacíos), s10 4c a las 04:09:53Z (INICIO_ARCHIVO 2026-11-11T04:09:53Z, archivador/recursos/salud OK), espejo 1 s desde 04:09:47Z (termina 04:39:47Z; hasta 04:13 mínimo 78 pkt/s), clientes: 4c de B2 apartado a ~/cf-e4/4c-B2-cancelada-X1-clientes-20261111T0411Z y k01 tx (factor 1,0 + transacciones-<perfil>.tsv, 6 perfiles sin duplicados) desde 04:12:55Z. Siguiente: al pasar el espejo, b01 4c control [~04:44, ~05:14] + k20, I1-I8, activar y g01c.
