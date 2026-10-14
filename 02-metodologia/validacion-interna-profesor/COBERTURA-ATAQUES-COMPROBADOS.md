# Cobertura: ataques que el sistema protege, comprobados

**Qué responde este documento:** contra qué ataques CyberFlow protege de verdad,
con qué los detecta (modelo o heurístico), qué acción aplica (LIMIT o BLOCK), y
con qué nivel de evidencia está comprobado. Lo que NO está cubierto se declara
igual: sin esa honestidad la tabla no vale.

> **Fuente de los números:** batería N=3 por familia (nota 26, 5-oct), ablación
> (nota 31) y episodio Nikto (nota 28), más el recorrido extremo-a-extremo del
> 13-oct. Mismo PCAP a CyberFlow y a Suricata, con el reloj del paquete y la
> configuración congelada. La «verdad» de cada episodio la fija el orquestador
> que lanzó el ataque, no las alertas.

---

## 1 · Tabla maestra

| Familia | Herramienta (Kali) | Lo detecta | Acción | Suricata (IDS) | Validación | Evidencia |
|---|---|---|---|---|---|---|
| **Escaneo de puertos** | `nmap -sT -sV -T4 -p-` | Modelo **y** heurístico `port_scan` | **BLOCK** | 0 (sin firma) | **Extremo a extremo** (vivo) | Recorrido 13-oct · N=3 |
| **Fuerza bruta HTTP** | `curl` ×20 hilos a `/login` | Heurístico `brute_force` (y modelo) | **BLOCK** | 0 (sin firma) | Replay de PCAP | Batería N=3 (flood) |
| **Flood / abuso HTTP** | flood de peticiones | Modelo y heurístico `http_abuse` | **LIMIT** | 0 (sin firma) | Replay de PCAP | Batería N=3 (flood) |
| **DNS de alta entropía** | consultas DGA / NXDOMAIN | Heurístico `dns_entropy` | **LIMIT** | 0 (sin firma) | Replay de PCAP | Batería N=3 (dns) |
| **Vulnerabilidades web (Nikto)** | `nikto -h http://...` | Modelo (Suricata **también**: tiene firma) | **LIMIT** | **Sí** (3,4 s) | Replay de PCAP | Episodio Nikto |

**Lo que NO cubre (declarado):**

| Familia | Estado | Por qué |
|---|---|---|
| **ARP spoofing (capa 2)** | **No cubierto** · trabajo futuro | La señal L2 es real (`unique_src_mac_30s` sube) pero se diluye entre las 31 variables; el modelo global la ignora. Pide una **regla determinista**, aún no escrita. |

---

## 2 · Cómo se detecta cada familia

Dos señales sobre las mismas variables de la ventana, y gana la más severa:

- **Modelo (Isolation Forest, no supervisado):** marca lo que se desvía de lo
  normal aprendido. Fuerte en escaneo y flood; **flojo en DNS** (0 % en la
  corrida real) — por eso existen los heurísticos.
- **Heurísticos deterministas (4 reglas versionadas):** cubren los huecos del
  modelo con umbrales explícitos y declarados (criterio razonado, **no**
  calibrados estadísticamente como el umbral del modelo):
  - `brute_force` → BLOCK (≥5 req/60 s con ≥80 % de fallo de auth)
  - `port_scan` → BLOCK (≥20 intentos/30 s a muchos puertos, baja completitud; **o** ráfaga ≥200/30 s)
  - `http_abuse` → LIMIT (≥100 req/60 s sin patrón de fuerza bruta)
  - `dns_entropy` → LIMIT (≥20 consultas/60 s con muchos NXDOMAIN o nombres únicos)

El reparto **LIMIT vs BLOCK** es por confianza: señal inequívoca (fuerza bruta,
escaneo) corta; señal ambigua (volumen HTTP, entropía DNS, anomalía del modelo)
degrada.

---

## 3 · Dos niveles de validación, y por qué

- **Extremo a extremo (en vivo):** el ataque sale de la Kali, el sensor lo ve por
  el espejo, decide, publica el feed firmado y el agente del host aplica nftables.
  Comprobado así el **escaneo de puertos** (opera a nivel TCP/flujo, que el espejo
  observa entero). Es el recorrido del 13-oct.
- **Replay de PCAP:** se reproduce el PCAP del episodio al motor y a Suricata.
  Necesario para las familias HTTP en claro porque **la segmentación del firewall
  no las deja llegar** desde la Kali: el cortafuegos solo permite 443 hacia la
  DMZ (el 80 está *filtered*, ICMP bloqueado), así que `nikto` y el flood sobre 80
  no viajan de extremo a extremo, y sobre 443 Suricata solo ve TLS cifrado. El
  replay mide la **detección** sobre tráfico real capturado, no simulado.

La campaña **C3** (propuesta) sube a N=5, añade fuerza bruta y tráfico legítimo
intenso, y mide los **falsos positivos de Suricata** sobre la línea base.

---

## 4 · Falsos positivos (por qué se puede confiar)

Sobre **527 ventanas de tráfico normal** del ensayo, **falsos positivos que
BLOQUEAN**:

| | Falsos que bloquean |
|---|---|
| Heurísticos (el camino que corta) | **0** |
| Combinado (CyberFlow) → BLOCK | **0** |
| Suricata | no medido (va en C3) |

**Hay que distinguir bloqueo de degradación.** El camino que BLOQUEA son los
heurísticos de alta confianza, y sobre tráfico legítimo **no se equivocan: 0
BLOCK**. El **modelo**, en cambio, tiene un **4,45 % de FPR** (sobre las 65 421
ventanas de prueba; objetivo fijado antes de mirar la prueba), así que en vivo
marca una fracción de las ventanas normales como anomalía — pero esas van a
**LIMIT** (rate-limit reversible), **nunca a BLOCK**. Comprobado en vivo el
14-oct: 168 ventanas de clientes en ALERT del modelo (→ LIMIT), 0 heurísticos,
0 bloqueos (recorrido `recorrido-normal-y-escaneo-2026-10-14/`).

Por eso la respuesta es **graduada**: un falso positivo del modelo cuesta solo
un rate-limit temporal, nunca un corte. Ese es, precisamente, el motivo de que
una anomalía del modelo dé LIMIT y no BLOCK.

---

## 5 · Resumen para la defensa

- **Protege, comprobado:** escaneo de puertos (E2E, BLOCK), fuerza bruta (BLOCK),
  flood/abuso HTTP (LIMIT), DNS de alta entropía (LIMIT), y Nikto (LIMIT).
- **Aporte frente a Suricata:** detecta lo que **no tiene firma** (escaneo, flood,
  DNS: 0 para Suricata) y además **bloquea**, que Suricata en SPAN no puede.
- **Límite honesto:** ARP spoofing de capa 2 queda como trabajo futuro (regla
  determinista), y los falsos positivos de Suricata se miden en C3.
