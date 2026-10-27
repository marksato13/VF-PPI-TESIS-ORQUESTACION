# Preparación del entorno real antes de la campaña A — 27-oct-2026

Comprobación y preparación del laboratorio usando los procedimientos del commit `96e1a0d`. **No se ejecutaron
ataques ni la campaña.** Este registro es de **estado del entorno**, separado de los futuros resultados
experimentales. Todo lo medido va en el reloj indicado.

## Accesos confirmados

| Máquina | Acceso | Permisos | Puedo administrar |
|---|---|---|---|
| Bastión VM-GESTION 10.10.10.30 | SSH `gadmin` (relé) | — | sí (punto de salto) |
| Sensor 10.10.60.11 | SSH `m4rk` (vía bastión, llave `cyberflow-to-sensor`) | NOPASSWD limitado (systemctl de servicios cyberflow, `nft list`, `cf-capturar`, grep/tail de eve); **`(ALL) ALL` solo con contraseña** | parcial (lo NOPASSWD sí; NTP/edición de config **no**, requiere contraseña) |
| srv-dmz 10.10.30.10 | SSH `adminsrvdmz` (vía bastión, llave `cyberflow-to-srv`) | **`(ALL) NOPASSWD: ALL`** | **sí, completo** |
| Kali 10.10.20.30 | SSH `adminatacante` (vía bastión, llave `cyberflow-to-atacante`) | — | sí (para verificación benigna) |
| DNS/AD 10.10.10.20 | **sin llave** | — | **no** (paso del usuario) |
| pfSense | **sin acceso** | — | **no** (paso del usuario) |

## Máquina → comprobación → evidencia → resultado → pendiente

| Máquina | Comprobación | Evidencia | Resultado | Pendiente |
|---|---|---|---|---|
| Bastión | Sincronización NTP | `chronyc tracking`: ref evlbi.aggo-conicet, System time 0,002 s, RMS 0,001 s | **Sincronizado** (referencia) | — |
| Sensor | Desfase vs bastión | 3 muestras RTT: **−47,77 s ±0,17** (m2/m3) | **Fuera de sincronía** | **CRÍTICO:** corregir NTP del sensor (sudo con contraseña / consola) |
| Sensor | Mecanismo de tiempo | `timesyncd` activo, `Server=10.10.10.30`, `NTPSynchronized=no` | Configurado pero no converge | igual que arriba |
| srv-dmz | Desfase vs bastión | 3 muestras: **+0,18 s ±0,18** | **Sincronizado** (sub-segundo) | — |
| Kali | Desfase vs bastión | 3 muestras: **+0,07 s ±0,09** | **Sincronizado** | — |
| DNS 10.10.10.20 | ¿Zona local / egress? | `dig @10.10.10.20 example.com` → `104.20.23.154` (IP pública) | **Reenvía a Internet**; no hay zona local | **CRÍTICO:** crear zona local reservada (DNS/AD) |
| srv-dmz | Endpoint 401 desplegado | `ppi-brute-lab` activo en :18081; local: sin cred→**401**, inválida→**401**, control→**200**; `/opt/brute-lab/brute.log` con los 3 códigos | **Desplegado y verificado en local** | — |
| Kali→srv-dmz | Alcance al endpoint | `curl`/connect a :18081 → **000 / cerrado-filtrado** | **No alcanzable** | **CRÍTICO:** regla pfSense `Kali 10.10.20.30 → srv-dmz 10.10.30.10 tcp/18081` |
| Kali→srv-dmz | Alcance HTTP/escaneo | connect :80 **abierto**, :443 **abierto**, resto filtrado | HTTP flood y escaneo alcanzan :80/:443 | escaneo verá sobre todo filtrado (limitación conocida 1-oct) |
| Sensor | Suricata/extractor ven el endpoint | **no comprobable aún**: sin tráfico Kali→18081 (pfSense) | **Bloqueado** | tras la regla pfSense: repetir y confirmar `event_type:http status:401` en eve + `http_*` en el motor |
| Sensor | Archivado (cf-capturar) | `cf-capturar /tmp/..pcap 5` → fichero creado, **0 paquetes descartados** | **Mecanismo OK** (captura host 10.10.20.30) | para captura continua full se necesita sudo o `cf-capturar` por episodio |
| Sensor | Rotación de fuentes | eve: logrotate **daily, maxsize 500M, rotate 7**; motor log diario; anillo recicla ~19 min; disco **21 GB** libres | No se pierden logs en una campaña de horas | archivar pcap continuo aparte (anillo recicla) |
| Sensor | Motor sin enforcement directo | `systemctl cat ppi-motor` **sin `--enforce`** | **OK** | — |
| srv-dmz | Enforcement actual | agente `ppi-enforce-agent.timer` **activo** (`--aplicar`); `cyberflow_limitados` tiene **1 elemento vivo** (10.10.50.52, LIMIT 4m) | **Enforcement VIVO** | poner en **sombra** justo antes de A (`modo_sombra.sh --ejecutar --motor-verificado`) y restaurar después |

## Cambios aplicados (y su reversión)

1. **Endpoint de prueba en srv-dmz** (servicio aislado de laboratorio; NO es captura ni resultado de CyberFlow):
   - Creado `/opt/brute-lab/app.py` y `/etc/systemd/system/ppi-brute-lab.service`; `systemctl start ppi-brute-lab` (escucha 18081).
   - **Estado previo:** 18081 libre, `/opt/brute-lab` inexistente, sin unidad.
   - **Reversión** (tras la campaña B): `[srv-dmz adminsrvdmz] → lo ejecuto yo`
     `sudo systemctl stop ppi-brute-lab; sudo systemctl disable ppi-brute-lab 2>/dev/null; sudo rm /etc/systemd/system/ppi-brute-lab.service; sudo systemctl daemon-reload; sudo rm -rf /opt/brute-lab`
2. **Tráfico de verificación benigno** (no campaña): 6 `curl` Kali→18081 (todos 000 por pfSense) y 3 `curl` locales en srv-dmz. Sin cambio de estado.
3. **Fichero temporal** `/tmp/cf-verif-*.pcap` (24 B, root) de la prueba de `cf-capturar`. Reversión: `sudo rm /tmp/cf-verif-*.pcap` (trivial).

**No se tocó:** modelo, umbrales, heurísticos, política de respuesta, Word, ni el enforcement vivo (sigue en
`--aplicar`; la sombra se activará justo antes de A y se restaurará después).

## Pendientes críticos (requieren intervención del usuario)

1. **NTP del sensor** (−47,8 s): `[SENSOR root]` sincronizar (`timedatectl set-ntp`/`systemctl restart systemd-timesyncd`, o corrección documentada) y guardar el desfase antes/después. Sin esto, 4.4 no tiene relojes comparables sensor↔Kali.
2. **Zona DNS local reservada** en `[DNS/AD 10.10.10.20]`: crear `*.lab-ppi` (o sinkhole) que resuelva local y no reenvíe; confirmar con `dig` y con tráfico de salida que no sale a terceros.
3. **Regla pfSense**: permitir `Kali 10.10.20.30 → srv-dmz 10.10.30.10 tcp/18081` (solo eso), para el endpoint de fuerza bruta. Tras abrirla, repetir la verificación Suricata/extractor.

(1) y (3) además desbloquean la verificación de telemetría del endpoint. El escaneo tendrá cobertura parcial por el
filtrado del cortafuegos (limitación conocida, no bloqueante).

## Actualización 27-oct (tras el Claude de infra; evidencia en `infra-2026-10-27/`)

- **T1 NTP del sensor — CERRADO.** Antes: −47,80/−47,80/−47,80 s (sync=no). Después: **+0,172/+0,181/+0,177 s** (sync=yes,
  Server 10.10.60.1). Causa real: el bastión no sirve NTP y faltaba la regla FW VLAN60→10.10.60.1:123; fix:
  NTP=10.10.60.1 + regla. Relojes ya **comparables** (sensor +0,18, srv-dmz +0,18, Kali +0,07, bastión ref).
- **T2 zona DNS `lab-ppi` — CERRADO.** Creada en DC1, `*`→10.10.30.10; `dig @10.10.10.20 probe-*.lab-ppi`=10.10.30.10
  (local); egress en WAN de pfSense-A = **0** líneas con `lab-ppi`. No se tocó el forwarder global. `dns_inusual`
  habilitado con `zona_dns=lab-ppi`.
- **T3 endpoint — red OK, parseo HTTP PENDIENTE.**
  - Endpoint confirmado en `0.0.0.0:18081` (401/401/200 en la IP de la VLAN).
  - **Firewall RESUELTO** (infra): la regla pass quedó **por encima** del deny en pfSense-A (MASTER) y B; la Kali
    atraviesa y srv-dmz:18081 responde (401/200 **a nivel de flujo**: bytes_toserver 288 / toclient 218 y 366). El
    motor decide sobre 10.10.20.30 (PERMIT, sube `packet_count_10s`). (`easyrule` la había dejado bajo el deny; se
    rehízo con el clon del script y se aplicó en B a mano porque XMLRPC no propagó un cambio por `write_config`.)
  - **Pendiente (único):** Suricata **no clasifica 18081 como HTTP** (0 `event_type:http` en :18081; 598 en :80), así
    que **no hay `http_request_count_60s`**. Causa: el bloque `app-layer.protocols.http` de `suricata.yaml` no tiene
    `detection-ports` (tls sí dp 443, dns dp 53); el `HTTP_PORTS` que se añadió es la variable de **reglas**, no el
    app-layer. **Fix (edit root en el sensor, lo aplica el infra):** añadir `detection-ports: { dp: "80, 18081" }` al
    bloque `http:` y `systemctl restart suricata`. Reversión: quitar esas 2 líneas y reiniciar. Tras eso yo relanzo la
    pasada benigna y confirmo `event_type:http` (401/200) + `http_request_count_60s>0`.
  - El extractor toma `http_*` de los `event_type:http` de eve.json (`load_app_observations`), por eso depende de ese
    parseo; no es un cambio de modelo/umbrales.

## Veredicto

**NO LISTO PARA CAMPAÑA A (1 requisito pendiente).** Cerrados: relojes (sensor sincronizado), zona DNS local,
endpoint desplegado y **camino de red del endpoint** (firewall reordenado en pfSense-A/B; la Kali llega a :18081).
**4 de 5 escenarios listos** (DNS inusual, inundación HTTP, escaneo breve, escaneo sostenido). **Falta solo** que
Suricata parsee 18081 como HTTP (añadir `detection-ports` al bloque `http:` y reiniciar — edit root en el sensor, lo
aplica el infra) para que el extractor produzca `http_request_count_60s` y habilitar la **fuerza bruta HTTP**
(`fuerza_bruta_http`). La sombra del enforcement se activa justo antes de A.

Commit base de procedimientos: `96e1a0d` · repo VF-PPI-TESIS-ORQUESTACION.
