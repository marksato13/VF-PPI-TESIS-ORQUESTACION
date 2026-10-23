# Resultados de la campaña instrumentada — modelo limpio (2026-10-23)

Campaña ejecutada contra `if_limpio_2026_10` + heurísticos `2026-10-06.2`, en vivo, por el
relay (Kali 10.10.20.30 → DMZ 10.10.30.10; resolver 10.10.10.20). Ventana
**15:24:37 → 16:23:23 UTC**. Evidencia en esta carpeta: `marcas.jsonl` (Kali, t0/t_fin por
episodio, reloj de pared + monotónico), `motor_slice.jsonl` (288 ventanas del atacante del
`motor_decision.log`), `suricata_slice.jsonl` (vacío), `*.gnmap` (cortes), `analisis/`.

Diseño: DNS ×3, flood HTTP ×3 (→ LIMIT), fuerza bruta ×1, escaneo ×1 (→ BLOCK). N real por
familia abajo. **La captura de PCAP de archivo no corrió** (se arregló el `sudo` después de
arrancar): el 4.3 aquí es **Suricata en vivo** (`eve.json`, mismo reloj del sensor), no replay.

## Tabla 8 — Ablación de componentes (atribución sin solape)

| Familia | Episodios | IF limpio | Heurísticos | Híbrido (OR) |
|---|---:|---:|---:|---:|
| DNS (alta entropía) | 3 | 1/3 | **3/3** (`dns_entropy`→LIMIT) | **3/3** |
| Flood HTTP | 3 | 1/3 | **3/3** (`http_abuse`→LIMIT) | **3/3** |
| Fuerza bruta | 1 | 1/1 | **1/1** (`brute_force`→BLOCK) | **1/1** |
| Escaneo | 1 | 0/1 **(inconcluso)** | 0/1 **(inconcluso)** | 0/1 **(inconcluso)** |
| **Total (sin escaneo)** | **7** | **3/7** | **7/7** | **7/7** |

**Lectura (coincide con la historia, ahora sobre el modelo limpio):** el **modelo solo** es
débil (3/7; falla DNS 2/3 y flood 2/3); los **heurísticos** cubren DNS y flood (3/3 cada uno) y
cortan la fuerza bruta; el **híbrido** detecta las tres familias sin firma. Confirma la
complementariedad medida, no redundancia.

> **El escaneo quedó INCONCLUSO, no es un fallo del detector.** Corrió a las 16:16 contra una Kali
> **todavía bloqueada**: la fuerza bruta escaló su BLOCK a **1 800 s** (2.ª ofensa; observado en vivo
> en el `nft` del host) y la espera entre episodios (330 s) fue insuficiente. El tráfico del escaneo
> fue dropeado en el host → no llegó al espejo → el motor no lo vio. El corte `filtered` del escaneo
> era **residual** del BLOCK de la fuerza bruta. Requiere **re-test limpio** (ver abajo).

## Tabla 9 — CyberFlow vs Suricata (en vivo, mismo reloj del sensor)

| Familia/control | Episodios | CyberFlow | Suricata (ET Open) | t CyberFlow | t Suricata |
|---|---:|---:|---:|---|---|
| DNS alta entropía | 3 | **3/3** | 0/3 | 66–74 s* | no detectado |
| Flood HTTP | 3 | **3/3** | 0/3 | 12–238 s* | no detectado |
| Fuerza bruta | 1 | **1/1** | 0/1 | ~791 s* | no detectado |
| Escaneo | 1 | inconcluso | inconcluso | — | — |

Suricata: **0 alertas** del atacante en toda la ventana (ET Open por defecto no tiene firma para
estas familias sin firma). *Sin control Nikto en esta corrida.* Alcance, no absoluto.

## Tabla 10 — Respuesta y tiempos (con lo medido; "no medido" donde falta)

| Ensayo | Señal/origen | Acción | Aplicación verificada | t detección | t total | Reversión |
|---|---|---|---|---|---|---|
| Fuerza bruta | `brute_force` | **BLOCK** | **nft del host + corte real** (80/443 `filtered`) | ~791 s* | no medido | expiró (escalera 300→**1800 s**, 2.ª ofensa) |
| DNS ×3 | `dns_entropy` | LIMIT | rate 100/s (no corta) | 66–74 s* | — | timeout 300 s |
| Flood ×3 | `http_abuse` | LIMIT | rate 100/s | 12–238 s* | — | timeout 300 s |
| Escaneo | — | (BLOCK residual de la brute) | corte `filtered` **residual** | inconcluso | — | — |

- **t3 (regla nft) medido en vivo:** `cyberflow_bloqueados` con `10.10.20.30`, timeout ~1800 s.
- **t4 (corte) medido:** `*.gnmap` → 80/443 `filtered` para brute y scan.
- **t2 (emisión del feed) y t5 (reversión exacta): no medidos** por episodio (no se guardó la
  secuencia de feeds/nft en el tiempo; el feed se publica cada 10 s). **Duración de inferencia
  (reloj monótono): no medida** (el motor no la registra).

## Confounds declarados (y cómo se corrigen en el re-test)

1. **Realimentación del enforcement:** el LIMIT/BLOCK ralentizó las propias herramientas del
   atacante (`curl`/`nmap`), alargando episodios (flood-3: 16 min, brute: 14 min) e **inflando los
   t1**. → En el re-test, lanzar los ataques con **timeouts fijos** por cliente, independientes del
   enforcement.
2. **Bloqueo activo contaminó el escaneo:** espera de 330 s << 1 800 s del BLOCK escalado. → En el
   re-test: ejecutar **escaneo/recon PRIMERO** (antes de cualquier BLOCK), y espaciar ≥ **1 800 s**
   tras cualquier familia que produzca BLOCK.
3. **Sin PCAP de archivo:** el 4.3 fue Suricata en vivo. → Con `cf-capturar` ya listo, el re-test
   captura PCAP y permite el **replay** con ruleset/hashes congelados.

## Qué queda sólido de esta corrida (para el artículo, con sus caveats)

- La **ablación de componentes sobre el modelo limpio** (DNS/flood/brute): modelo solo 3/7,
  heurísticos 7/7, híbrido 7/7 — complementariedad medida.
- **CyberFlow 7/7 vs Suricata 0/7** en lo sin firma (en vivo, mismo reloj).
- **Enforcement real verificado**: `brute_force`→BLOCK con **regla nft en el host** y **corte real**,
  y **escalera 300→1800 s** observada.
- El **escaneo y los tiempos limpios** exigen el re-test descrito (spacing + timeouts + PCAP).
</content>
