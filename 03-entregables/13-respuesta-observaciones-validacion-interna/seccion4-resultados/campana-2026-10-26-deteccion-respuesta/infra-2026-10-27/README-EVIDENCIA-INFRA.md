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

## T3 — Regla pfSense + telemetría
🟡 **Estado previo medido; regla preparada (la aplicas en pfSense-A, MASTER); telemetría en el sensor.**
```
pfSense-A: carp MASTER (vmx3.10) · reglas 18081 = 0 · VLAN20 = vmx3.20
pfSense-B: reglas 18081 = 0
```
Detalle y reversión en `T3-regla-pfsense-18081.md`.

## Qué queda para cerrar "LISTO PARA CAMPAÑA A"
1. T1 en el sensor (offset ≤ 1 s).
2. T2: crear la zona en DC1 y volver a correr `T2-captura-egress-pfsense.sh` → 0 líneas `lab-ppi`.
3. T3: aplicar la regla en pfSense-A, `curl` desde la Kali (codigos), y la telemetría en el sensor.

Ofrecido: en cuanto exista la zona, infra puede relanzar la captura de egress (read-only) y devolver el "después".
