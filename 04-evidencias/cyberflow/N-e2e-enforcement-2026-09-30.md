# N · E2E de enforcement: un BLOCK real corta el ataque en el host

**Fecha:** 30 de septiembre de 2026
**Objetivo:** demostrar que la acción **no se queda en alerta** — un veredicto BLOCK
**corta de verdad** el tráfico del atacante en el host protegido (no "demostrativo").

## Montaje
- **Agente** (`scripts/enforce/agente_enforce.py`) desplegado en el host DMZ
  `adminsrvdmz@srv-dmz (10.10.30.10)`.
- **Feed firmado (ed25519)** generado en el bastión con `scripts/engine/feed.py`,
  bloqueando la Kali `10.10.20.30` (BLOCK, timeout 300 s).
- El agente trae el feed, **verifica la firma**, y sincroniza nftables en una tabla
  **aislada** `inet cyberflow` (cadena hook input, `policy accept` → solo cae lo que
  esté en los sets).

## Hallazgo descartado: no hay NAT inter-VLAN
Se sospechó que pfSense hacía SNAT (el host vería la IP del gateway, no la de la
Kali). **Falso**, medido con `tcpdump` en el host:

```
ens35 In  IP 10.10.20.30.33820 > 10.10.30.10.80: Flags [S]
ens35 Out IP 10.10.30.10.80 > 10.10.20.30.33820: Flags [S.]
```

El host **ve la IP real** de la Kali. El bloqueo host-based por IP de origen es viable.

## Resultado: el BLOCK corta
Con la IP de la Kali en la ruta de `drop` (regla `ip saddr 10.10.20.30 counter drop`):

| | Antes | Con BLOCK |
|---|---|---|
| `curl http://10.10.30.10/` desde la Kali | **http_200** en 0,003 s | **http_000 (FALLO)** |
| contador nftables | — | **12 paquetes dropeados** |

Tras la prueba: **tabla eliminada, host restaurado a pristino** (`curl` vuelve a
http_200), `/tmp` limpio (incluida la clave privada de firma).

## Detalle operativo (caducidad)
El feed lleva `hasta` **absoluto**; el set de nftables usa `timeout` nativo → los
bloqueos **caducan solos** (fail-safe: nada queda colgado). En un primer intento el
set se vació porque pasó demasiado tiempo entre generar el feed y probar (el `hasta`
expiró) — comportamiento **correcto**, no un bug. En producción el **publicador
refresca el feed en un timer** (cadencia << timeout, p.ej. 15 s << 300 s), así un
bloqueo activo se mantiene vivo mientras dure la amenaza y desaparece solo cuando
cesa.

## Qué valida y qué falta
- ✅ **Valida la acción real** (parte de B2/B4): agente + feed firmado + nftables
  cortan el ataque en el host, con verificación de firma y caducidad.
- **Falta para producción** (todo en `main`, dormido): publicador en timer +
  transporte del feed a los hosts (el host no alcanza al sensor directo; usar el
  bastión como distribuidor, o un canal dedicado) + integración motor→feed en vivo
  (que la detección real dispare el feed sola).

## Seguridad de la prueba
Tabla aislada (no tocó el firewall del host), `policy accept` (solo cae lo del set),
solo la IP de la Kali, timeout corto, host restaurado. Acceso del agente por llave
dedicada (`cyberflow-to-srv`); el `sudo` del `nft` es passwordless en ese host.
