# O · Enforcement EN VIVO + primera campaña de ataque sobre el sistema vivo

**Fecha:** 2026-10-01 (UTC)
**Objetivo:** pasar el enforcement de modo sombra (dry-run) a **vivo**, y validar
con un ataque real que el sistema **actúa** (no solo alerta).

## Contexto (lo hecho en esta tanda)
- **#1 Autenticación del panel:** habilitada (el código ya existía: login scrypt,
  TLS, roles `lector`/`admin`, cerrojo, auditoría). Panel en `https://10.10.60.11:8788`.
- **#3 Panel muestra la acción:** columna **Acción** (PERMIT/LIMIT/BLOCK) en la
  tabla de decisiones y el CSV, derivada del veredicto + `heurístico`
  (commit `27a96a7`). *(Falta desplegar el `dashboard.py` al sensor.)*
- **#2 Enforcement en vivo** (esta nota).

## #2 — Go-live del enforcement
**Arreglo que lo hizo posible (commit `5368613`):** el agente ejecutaba `nft`
**sin privilegios** → habría fallado desde el cron del host. Se añadió `--sudo`
(nft con `sudo -n`, mínimo privilegio: se eleva el nft, no el proceso) y **reporte
de errores** (antes decía "aplicado" aunque `nft` fallara).

Verificado en el host DMZ (`adminsrvdmz@10.10.30.10`):
- `sudo -n nft` es **NOPASSWD** → `--sudo` funciona.
- Cron del agente con `--aplicar --sudo`.
- Tabla `inet cyberflow` creada: cadena `entrada` (hook input, priority -10,
  policy accept), set `cyberflow_bloqueados` (drop) y `cyberflow_limitados`
  (rate-limit `over 100/second burst 5 → drop`).
- El motor reiniciado (`ppi-motor`) **ya emite el campo `heurístico`** (antes no
  existía): la tubería hacia BLOCK está completa.

## Campaña de ataque `prueba-ataque-20261001-031730`
Kali `10.10.20.30` (encendida por Mark). Ad-hoc (la Kali no tenía el repo).

| Fase | Comando | Ventana UTC |
|---|---|---|
| DNS-entropy | 200 consultas NXDOMAIN únicas a `dig @10.10.10.20` | 03:17:30→35Z |
| Port-scan | `nmap -sT -T4 -p1-1000 10.10.30.10` (80/443 abiertos, 998 filtrados) | 03:17:35→53Z |

## Resultado

**✅ El enforcement actuó sobre el ataque real.** El `shadow.log` del host:
```
{"estado":"aplicado","errores":0,"limit":["10.10.20.30"]}
```
Cadena completa automática: **modelo detecta el escaneo (ALERT ventana 03:17:40)
→ feed firmado con LIMIT para 10.10.20.30 → relay → el agente aplica `nft` en el
host.** El sistema **rate-limitó a la Kali solo**, y lo retiró al cesar el ataque.
Es el claim central —detección temprana **y respuesta**— demostrado en vivo.

### Hallazgos (resultado legítimo, no fallo de la prueba)

1. **No salió BLOCK: el heurístico `port_scan` no disparó.** Causa probable: el
   **firewall FILTRÓ 998/1000 puertos** (los dropeó). Esos SYN mueren en el
   firewall y **no cruzan el troncal espejado**, así que el sensor solo vio los 2
   puertos abiertos (80/443) — por debajo del umbral `≥20 puertos` de `port_scan`.
   **Insight:** el sensor ve el tráfico *enrutado*; el reconocimiento que el
   firewall ya bloquea le es invisible (y está bien: el firewall ya lo paró).
   CyberFlow **complementa** al firewall, no lo reemplaza. El modelo sí marcó la
   anomalía de los puertos abiertos (→ LIMIT aplicado).

2. **`dns_entropy` no disparó** pese a 200 consultas NXDOMAIN únicas (los umbrales
   `≥20 consultas / ≥90% únicas / ≥50% NXDOMAIN` deberían cumplirse). Sospecha: el
   sensor/Suricata **no registró las consultas DNS en vivo** (es el hueco histórico
   del DNS, nota M, 0%). Pendiente: mirar `dns_query_count_60s` real en la ventana.

3. **Dinámica:** un ataque de **ráfaga corta** (23 s) caduca de la ventana del feed
   (120 s) antes de que la cadena de crones de 1 min lo mantenga. Un ataque
   **sostenido** persiste (el LIMIT estuvo aplicado varios ciclos antes de salir).

## Qué falta
- **Demostrar un BLOCK real:** fuerza bruta **sostenida** (`hydra`) contra un
  endpoint con auth (401/403) del DMZ → dispara `brute_force` → BLOCK. Es tráfico
  al puerto abierto (80), que el sensor **sí ve**. (Confirmar que el DMZ sirve un
  401; `/` da 200.)
- **Diagnosticar el DNS (#4):** por qué no se cuentan las consultas en vivo.
- **Revisar umbrales/visibilidad** de `port_scan` a la luz del hallazgo del
  firewall (¿medir recon en el lado VLAN, o aceptar que es dominio del firewall?).
- Desplegar el `dashboard.py` (#3) al sensor.

Ver [[PENDIENTES]] y `N-e2e-enforcement-2026-09-30.md` (el BLOCK aislado ya
probado en banco con regla explícita).
