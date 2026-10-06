# 21 · P0-06 · Familias de ataque y escenarios (intensidad justificada)

**Fecha:** 2026-10-02
**Objetivo:** definir los episodios de ataque del experimento con intensidad y
umbrales **justificados**, no arbitrarios (indicación directa del asesor). Cada
episodio produce un `episodio-<id>.pcap` etiquetado que se corre por ambos
detectores (nota `19`).

## Principio de justificación (tres fuentes, no una)

Cada parámetro de intensidad se sostiene en **al menos** una de estas tres, y se
declara cuál:

1. **Línea base medida** en esta red (lo normal): un ataque es anómalo si
   **supera** el comportamiento normal medido (pps, ancho de banda, tamaño de
   paquete, nº de puertos/consultas por cliente). *Pendiente de medir — ver
   `## Línea base` abajo; los valores `‹BASE_*›` se rellenan con la medición.*
2. **Marco/estándar reconocido:** MITRE ATT&CK (técnica), y para los umbrales,
   referencias como OWASP (fuerza bruta), NIST SP 800-63B (bloqueo de cuentas),
   documentación de nmap (escaneo) y literatura de DGA/DNS. *Donde se cita un
   valor concreto de literatura queda marcado `[CITA]` para fijar la referencia
   exacta en la redacción final.*
3. **Umbral documentado del propio detector** (`scripts/engine/heuristicos.py`,
   `VERSION_UMBRALES` versionado, criterio razonado). La intensidad del ataque se
   fija **claramente por encima** del umbral, para que el episodio sea sin
   ambigüedad un ataque; así la comparación mide *quién y cuándo detecta*, no si
   el evento "cuenta".

## Familias seleccionadas (diseñadas para contrastar la hipótesis H1)

Dos familias **con firma** (donde Suricata debería ir bien) y dos **conductuales
sin firma fiable** (donde CyberFlow debería diferenciarse), más un control.

| ID | Familia | MITRE | Origen → destino | ¿Firma? |
|---|---|---|---|---|
| `E1-scan` | Escaneo de puertos | T1046 | Kali `10.10.20.30` → srv `10.10.30.10` | Sí (ET scan) |
| `E2-brute` | Fuerza bruta HTTP | T1110 | Kali → srv `10.10.30.10` (servicio con auth) | Sí (ET auth) |
| `E3-dns` | DNS alta entropía / DGA | T1568.002 | Kali → resolver `10.10.10.20` | **No** (conductual) |
| `E4-flood` | Flood/scraping HTTP | T1498/T1499 | Kali → srv `10.10.30.10` | Débil (volumétrico) |
| `E0-normal` | Control (sin ataque) | — | Clientes `.20-.26` → srv | — (mide FPR) |

### E1 · Escaneo de puertos (T1046)
- **Herramienta:** `nmap -sT -T4 -p 1-1000 10.10.30.10` (connect scan; no requiere root).
- **Duración/intensidad:** barrido sostenido de **≥1000 puertos** en la ventana.
- **Justificación:**
  - *Detector:* umbral `port_scan` = ≥20 intentos/30 s a ≥50 % de puertos únicos
    con ≤30 % de handshakes completados. Un barrido de 1000 puertos lo supera con
    amplio margen.
  - *Base:* un cliente legítimo contacta **unos pocos** puertos (80/443); `‹BASE_puertos_cliente›`.
  - *Estándar:* nmap/`[CITA]` sobre detección de recon por nº de puertos distintos.
- **Visibilidad (importante):** el firewall **filtra** la mayoría de puertos y los
  dropea antes del espejo (hallazgo nota `O`). Para que el episodio sea
  observable y comparable, **capturar el PCAP donde el escaneo es visible** (lado
  VLAN del atacante o pre-firewall), o acotar el alcance a los puertos
  **enrutados/abiertos**. Declararlo: CyberFlow/Suricata ven lo que cruza el
  espejo; el recon ya bloqueado por el firewall es dominio del firewall.

### E2 · Fuerza bruta HTTP (T1110)
- **Herramienta:** `hydra` contra un endpoint con autenticación (401/403) del srv.
- **Intensidad:** **≥20 intentos/60 s** con credenciales inválidas (≥80 % de fallo).
- **Justificación:**
  - *Detector:* umbral `brute_force` = ≥5 req/60 s y ≥80 % de fallo de auth; se
    fija en ≥20 para dejarlo inequívoco.
  - *Estándar:* OWASP (Credential Stuffing / Brute Force) y NIST SP 800-63B
    (bloqueo tras pocos intentos fallidos) → el umbral de 5-10 es práctica común `[CITA]`.
  - *Base:* un login legítimo falla rara vez; `‹BASE_auth_fail_cliente›`.
- **Requisito:** confirmar que el srv expone un recurso que devuelve 401/403 (hoy
  `/` da 200). Si no, preparar un endpoint de prueba con auth básica.

### E3 · DNS de alta entropía / DGA (T1568.002) — diferenciador
- **Herramienta:** consultas a `10.10.10.20` de nombres aleatorios/únicos
  (p. ej. `dig @10.10.10.20 <rand>.<tld-inexistente>`), **sostenido** (ver nota).
- **Intensidad:** **≥60 consultas/60 s**, ≥90 % nombres únicos, mayoría NXDOMAIN.
- **Justificación:**
  - *Detector:* umbral `dns_entropy` = ≥20 consultas/60 s con ≥90 % únicas **o**
    ≥50 % NXDOMAIN; se fija ≥60 para margen.
  - *Estándar/literatura:* detección de DGA por alta proporción de nombres únicos
    y NXDOMAIN `[CITA]`.
  - *Hipótesis:* Suricata (firmas) **no** alerta de DGA genérico sin regla
    específica → aquí CyberFlow debería diferenciarse. Es el caso del 0 % histórico
    (nota `M`).
- **Nota de medición:** en la corrida del 1-oct 200 consultas en 5 s **no**
  dispararon el heurístico en vivo (nota `O`); hay que **diagnosticar si el sensor
  cuenta las consultas DNS** (feature `dns_query_count_60s`) antes de dar E3 por
  válido. Pendiente ligado a P0-09.

### E4 · Flood / scraping HTTP (T1498/T1499)
- **Herramienta:** peticiones HTTP de alto volumen al srv (sin patrón de auth).
- **Intensidad:** **≥150 req/60 s** (supera `http_abuse` = ≥100), por encima de `‹BASE_http_req_cliente›`.
- **Justificación:** *Detector* `http_abuse` ≥100 req/60 s; *Base:* volumen normal
  por cliente medido; *Estándar:* umbrales de rate/volumen `[CITA]`. Suricata sin
  regla volumétrica específica puede **no** alertar → contrasta con el modelo.

### E0 · Control sin ataque (FPR)
- Solo tráfico legítimo de los 6 clientes `.20-.26` durante el mismo tiempo que un
  episodio. Mide **FPR** de cada detector (ventanas normales alertadas / normales).

## Parámetros comunes de cada episodio
- **Duración:** 3-5 min por episodio (varias ventanas de 10 s → medición estable y
  tiempo para que las firmas de Suricata disparen). Sostenido, no ráfaga.
- **Repeticiones:** ≥3 por familia (para intervalo, no un solo número).
- **Etiquetado (ground truth):** por episodio — `id, familia, MITRE, t_inicio,
  t_fin, origen, destino, intensidad, herramienta/versión`.
- **Aislamiento:** un episodio a la vez; registrar que la Kali solo emite en su
  ventana (fuera de la línea base limpia).

## Línea base (pendiente de medir — sustenta `‹BASE_*›`)
Medir sobre tráfico **normal** (sin Kali), por cliente y por ventana:
- `BASE_pps`, `BASE_bps`, `BASE_tam_paquete` (media/percentil 95).
- `BASE_puertos_cliente` (puertos distintos por cliente/ventana).
- `BASE_http_req_cliente`, `BASE_auth_fail_cliente`, `BASE_dns_query_cliente`.

Con esos valores, cada intensidad se expresa también como "N× sobre lo normal", que
es la justificación más fuerte frente al asesor (anómalo = supera lo medido).

## Trazabilidad
- Hipótesis H1: `01-PLAN-P0.md` (P0-01). Métricas: `03-METRICAS-Y-EVIDENCIAS.md`.
- Método de medición: `19-METODO-REPLAY-PCAP.md`. Scorer: `20-puntuar-por-ventana.py`.
- Umbrales del detector: módulo de heurísticos del **CyberFlow desplegado en
  Sensor1** (`VERSION_UMBRALES "2026-09-30.1"`). Nota: ese módulo **no** está en el
  clon local `producto/`; vive en el sensor (`/home/m4rk/cyberflow/scripts/engine/`).
  El experimento evalúa el detector **desplegado**, no el clon local.
