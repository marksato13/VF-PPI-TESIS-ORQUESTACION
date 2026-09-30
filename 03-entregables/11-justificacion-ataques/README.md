# Justificación de los escenarios de ataque (fase de evaluación)

**Propósito.** Fundamentar *por qué* CyberFlow se evalúa con estos ataques y no
con otros: cada uno se elige por ser (a) **frecuente y representativo** en redes
segmentadas con una DMZ, según marcos y reportes de la industria; (b) **mapeable
a MITRE ATT&CK**; y (c) **observable** por al menos una variable del contrato de
features. Es la contraparte defensiva del corpus de anomalías del datasheet.

> Alcance ético: el tráfico ofensivo se genera **solo dentro del laboratorio
> propio y autorizado** (Kali `10.10.20.30` → DMZ `10.10.30.10`). No es una guía
> de ataque contra terceros (ver el datasheet, «Usos prohibidos»).

---

## 1. Criterio de selección

Un ataque entra en la evaluación si cumple los tres filtros:

1. **Prevalencia declarada** por una fuente reconocida (MITRE ATT&CK, OWASP,
   Verizon DBIR, FortiGuard Labs / Fortinet, ESET), no por intuición.
2. **Superficie coherente** con el escenario: una DMZ con un servicio web/DNS
   detrás de un cortafuegos segmentado por VLAN.
3. **Observabilidad**: deja una huella medible en las variables L2/L3/L4/L7 del
   sistema (si no la deja, no es evaluable aquí y se declara como tal).

---

## 2. Mapa ataque → técnica → respaldo → variables → detección

| Ataque (comando de lab) | MITRE ATT&CK | Táctica | Respaldo de prevalencia | Variables que lo delatan | Detección medida |
|---|---|---|---|---|---|
| **Escaneo de puertos** `nmap -sT -p-` | **T1046** Network Service Discovery · **T1595.001** | Reconocimiento / Descubrimiento | DBIR (acción «Scanning» previa a intrusión); FortiGuard (escaneo masivo continuo) `[verificar cifra/edición]` | `unique_dst_port_ratio_30s`, `syn_completion_ratio_10s`, `flow_attempt_rate_10s`, `rst_ratio_10s` | **79 %** |
| **Escaneo amplio** `nmap -p 1-1000/1-5000` | **T1046** · **T1595** | Reconocimiento | ídem | `unique_dst_port_ratio_30s`, `syn_rate_10s` | (por medir) |
| **Ráfaga TCP / SYN** `tcp-syn-rate` | **T1046** + **T1499** Endpoint DoS a tasa alta | Descubrimiento / Impacto | FortiGuard (DoS volumétrico); NIST SP 800-115 (pruebas de red) | `syn_rate_10s`, `rst_ratio_10s`, `flow_attempt_rate_10s` | (por medir) |
| **Sondeo UDP** `nping --udp -p 53` | **T1046** | Descubrimiento | NIST SP 800-115 | `packet_rate_10s`, `protocol_diversity_30s` | (por medir) |
| **Escaneo web (nikto)** | **T1595.002** Vulnerability Scanning | Reconocimiento | **OWASP** (escaneo automatizado); DBIR (Basic Web App Attacks) | `http_request_rate_60s`, `http_error_ratio_60s`, `http_method_entropy_60s` | **87 %** |
| **Fuerza bruta / flood login** | **T1110** Brute Force · **T1499** | Acceso a credenciales / Impacto | **OWASP A07:2021**; DBIR (credenciales, vector nº1 sostenido) `[verificar]` | `flow_attempt_rate_10s`, `http_request_rate_60s`, `syn_rate_10s` | **87 %** |
| **Password spraying** `password-spray` | **T1110.003** Password Spraying | Acceso a credenciales | ESET Threat Report (ataques de fuerza bruta a servicios expuestos) `[verificar]`; DBIR | `http_auth_failure_ratio_60s`, `http_request_rate_60s` | (por medir) |
| **DNS de alta entropía** `dns-entropy` | **T1568.002** DGA · **T1071.004** DNS | Comando y control / Exfiltración | FortiGuard/ESET (C2 y túnel DNS); literatura de detección DGA | `dns_nxdomain_ratio_60s`, `unique_dns_name_ratio_60s`, `dns_query_rate_60s` | (por medir) |
| **ARP spoofing (L2)** `arpspoof` | **T1557.002** AiTM: ARP Cache Poisoning | Acceso a credenciales / Colección | MITRE; guías de segmentación (CIS) | `unique_src_mac_30s`, `mac_ip_binding_changes_60s`, `arp_request_rate_10s` | **0 %** (ver §4) |

> Las cifras marcadas `[verificar]` son afirmaciones de prevalencia que deben
> anclarse a la **edición y página exactas** del reporte antes de publicar. Aquí
> se citan por serie; no se inventan porcentajes.

---

## 3. Por qué este conjunto y no otro

- **Cubre la cadena, no un punto suelto:** reconocimiento (escaneos) →
  acceso a credenciales (fuerza bruta / spraying) → C2/exfil (DNS) → y un caso de
  **capa 2** (ARP). Evaluar solo un tipo daría una métrica sesgada.
- **Golpea la superficie real del escenario:** un servidor web/DNS en DMZ es
  exactamente lo que un atacante interno (VLAN de usuarios comprometida) sondea
  primero. Las VLAN y el cruce por pfSense hacen que ese tráfico suba al espejo.
- **Es reproducible y acotado:** herramientas estándar (`nmap`, `nping`, `curl`,
  `dig`, `arpspoof`), parámetros cerrados (lista blanca en `run-anomaly-v2.sh`),
  solo contra la DMZ autorizada.
- **Contrasta con el «tráfico pesado como normalidad»** del datasheet: descargas
  grandes y flujos concurrentes son normales; lo que separa el ataque es el
  *patrón* (muchos destinos/puertos, fallos de auth, NXDOMAIN), no el volumen.

---

## 4. Límite declarado (honestidad metodológica)

El **ARP spoofing** produce una señal L2 real (`unique_src_mac_30s` sube) pero el
modelo global la **diluye entre 28 variables** y no la marca (0 % medido). Se
declara como **trabajo futuro**: pide una **regla determinista** de capa 2, no un
detector de una sola clase. No se presenta como detectado.

---

## 5. Fuentes (anclar edición/año al citar)

- **MITRE ATT&CK** — `attack.mitre.org` (IDs de técnica usados arriba).
- **OWASP Top 10:2021** — A07 Identification and Authentication Failures; escaneo
  automatizado de aplicaciones.
- **Verizon DBIR** (anual) — prevalencia de escaneo, credenciales y web app.
- **Fortinet — Global Threat Landscape Report** (FortiGuard Labs, semestral).
- **ESET Threat Report** (cuatrimestral) — fuerza bruta a servicios expuestos.
- **NIST SP 800-115** — guía técnica de pruebas de seguridad (respalda el método).
- **CIS Controls / Benchmarks** — segmentación y monitoreo L2.

---

## 6. Trazabilidad

- Catálogo operativo (comandos por escenario, ya en la red actual):
  producto `configs/escenarios.json`.
- Ejecutor en la Kali: producto `scripts/kali/run-anomaly-v2.sh`
  (**pendiente**: re-apuntar `TARGET` de `10.30.0.10` a `10.10.30.10`).
- Composición del corpus de anomalías: producto `docs/dataset/DATASHEET_MULTILAYER_V2.md`.
- Medición de detección con el modelo **recalibrado**: pendiente de la corrida —
  ver `04-evidencias/cyberflow/RUNBOOK-KALI-deteccion.md` y la nota `L`.
