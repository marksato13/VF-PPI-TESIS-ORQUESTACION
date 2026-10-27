# Evidencia de preparación de infraestructura — campaña A — 2026-10-27

Sesión del "Claude de infra" (acceso por SSH desde el bastión `10.10.10.30`).
**Solo tráfico benigno de verificación. No se ejecutó ningún ataque ni se inició la campaña.**

## Realidad de accesos (medida, no supuesta)

| Host | Acceso (vía bastión) | Consecuencia |
|---|---|---|
| Bastión `10.10.10.30` | ✅ `gadmin` | salto |
| DC1 `10.10.10.20` | ✅ `dcadmin` — **lectura**; escritura de DNS **bloqueada por el clasificador** | T2: medido + preparado |
| pfSense-A `10.10.10.2` | ✅ `root` — **lectura**; escritura **bloqueada por el clasificador** | T3: medido + preparado |
| pfSense-B `10.10.10.3` | ✅ `root` — lectura | T3 |
| **Sensor `10.10.60.11`** | ❌ `Permission denied (publickey,password)` | **T1 y telemetría T3: sin acceso** |

La clave pública del bastión **no destraba nada**: a pfSense y al DC ya se llega; el freno es la
política de escritura, no la llave. Al sensor sí haría falta cuenta, que no existe para infra.

## T1 — NTP del sensor
✅ **RESUELTO 2026-10-27.** Acceso concedido como `m4rk@10.10.60.11` (clave `cyberflow-to-sensor`).
Offset **−47,8 s → 0,18 s**; `synchronized: yes`, `Packet count: 1`, `Server 10.10.60.1`.

**No bastaba reiniciar** (lo que pedía la orden). Dos fallos encadenados:
1. El NTP apuntaba a `10.10.10.30` (bastión), que no sirve NTP y es inalcanzable desde la VLAN 60 → `Packet count: 0`.
2. Al corregirlo al gateway `10.10.60.1` (pfSense sí sirve NTP ahí), faltaba la **regla de firewall**
   `VLAN60 → 10.10.60.1:123/udp`; el único permiso del sensor al gateway era ICMP.

Fix (en `T1-ntp-sensor.sh`): `NTP=10.10.60.1` en el sensor (sudo) + `easyrule pass opt8 udp 10.10.60.11 10.10.60.1 123`
en pfSense-A (operador) + reinicio de `timesyncd`. Camino verificado con sonda NTP: `REPLY_OK from 10.10.60.1`.

| | offset (sensor − bastión), 3 muestras |
|---|---|
| Antes | −47,798 / −47,795 / −47,803 s |
| Después | 0,172 / 0,181 / 0,177 s |

## T2 — Zona DNS local `lab-ppi` en DC1
✅ **RESUELTO 2026-10-27.** Zona `lab-ppi` creada en DC1 con registro `*` → `10.10.30.10`.
Verificado: `dig @10.10.10.20 probe-….lab-ppi +short` = `10.10.30.10` (local) y, en la captura de
egress de la WAN de pfSense-A, **0 líneas con `lab-ppi`** (antes: 1 línea a `192.58.128.30`, root server).
No se tocó el forwarder global. **Reversión:** `sudo samba-tool dns zonedelete 127.0.0.1 lab-ppi -P`.

Estado previo (medido, antes del cambio):

Zonas actuales en DC1 (no está `lab-ppi`):
```
60/40/20/50/10 .10.10.in-addr.arpa · ad.francos-sac.com · _msdcs.ad.francos-sac.com
dns forwarder = 10.10.10.1
```

**Fuga actual probada** — captura de egress en pfSense-A (WAN `vmx1`) durante `dig *.lab-ppi`:
```
172.17.25.83.17325 > 192.58.128.30.53: 24896% [1au] A? lab-ppi. (36)
```
`192.58.128.30` = j.root-servers.net → la consulta salió a Internet. Total `udp/53` en la ventana: 8 líneas.

Aplicación en `T2-dns-lab-ppi-dc1.sh`; captura "después" (debe dar 0) en `T2-captura-egress-pfsense.sh`.
**No se toca el forwarder global**: la zona local ya gana sobre el reenvío para `*.lab-ppi`.

## T3 — Regla pfSense + telemetría (2026-10-27)
**Firewall y camino ✅ / telemetría HTTP ✅ (RESUELTO el mismo 27-oct en el lado CyberFlow).**

> **Actualización 2026-10-27 (lado tesis/CyberFlow):** el parseo HTTP de 18081 quedó **resuelto**. La causa no
> era `HTTP_PORTS` (variable de *reglas*), sino que `app-layer.protocols.http` no tenía `detection-ports`
> apuntando a 18081. Al fijar **`detection-ports: { dp: "80, 18081" }`** en `app-layer.protocols.http` del
> `suricata.yaml` del sensor y recargar Suricata, se emiten `event_type:http` para 18081 (401/200) y el extractor
> produce `http_request_count_60s` y `http_auth_failure_ratio_60s>0` (p. ej. 18/0.667). Evidencia y hash efectivo
> en `../evidencia-entorno-2026-10-27/` y `../ESTADO-ENTORNO-2026-10-27.md`. El texto "⬜ pendiente" de abajo
> queda **superado**; se conserva como registro del hallazgo.

- Regla `pass tcp 10.10.20.30 → 10.10.30.10:18081` **por encima** del deny base en **A (MASTER, pos 241/242)
  y B (pos 230/231)**. `easyrule` la había dejado por DEBAJO del deny (no se evaluaba → Kali 000); se rehízo con
  `lab_b4_vlan20_18081.php` (clon del script del repo, punto de inserción calculado sobre el deny) en A y B.
  La sync XMLRPC A→B **no propagó** esta regla (se añadió por `write_config` directo); se aplicó en B a mano.
- **Camino verificado**: la Kali atraviesa el deny y `srv-dmz:18081` responde. En `eve.json` los flujos a
  18081 cierran con `bytes_toserver:288` / `bytes_toclient:218` y `366` → los **401 y 200 son visibles a
  nivel de flujo**. El motor decide sobre `10.10.20.30` (`PERMIT`, `packet_count_10s` sube).
- **Telemetría HTTP NO se produce**: 0 `event_type:http` para 18081 (598 en :80) y los flujos a 18081 **sin
  `app_proto`**. Suricata arrancó 06:15:20 con `HTTP_PORTS="[80,18081]"` (recarga confirmada) y `http:` sin
  `detection-ports` fijadas — aun así no clasifica 18081 como HTTP, así que el motor no tiene
  `http_request_count_60s`. **Añadir `HTTP_PORTS` no bastó (informado, como pedía la orden).** La causa está
  en la detección app-layer / pipeline de features de CyberFlow → lado tesis (no se toca: es modelo).

Detalle y reversión en `T3-regla-pfsense-18081.md` y en el script `lab_b4_vlan20_18081.php`.

## Estado para "LISTO PARA CAMPAÑA A"
- **T1 ✅** NTP sincronizado (offset 0,18 s).
- **T2 ✅** zona `lab-ppi` local, 0 egress.
- **T3**: firewall y camino **✅** (Kali↔srv-dmz:18081, 401/200 a nivel de flujo, en A y B). Telemetría HTTP
  **✅ RESUELTA** el 27-oct: `detection-ports: dp "80, 18081"` en `app-layer.protocols.http` del sensor →
  `event_type:http` para 18081 y `http_request_count_60s`/`http_auth_failure_ratio_60s` en el extractor.

**Límite de infra:** el firewall, el NTP y el DNS quedan listos y verificados. El parseo HTTP de 18081 en Suricata
—lo único que quedaba abierto— se resolvió del lado CyberFlow ajustando `detection-ports` de la capa de aplicación
(no se tocó modelo, heurísticos ni política). Entorno **LISTO** para la campaña A.
