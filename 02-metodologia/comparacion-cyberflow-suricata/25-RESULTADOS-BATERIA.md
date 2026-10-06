# 25 · Resultados de la batería (E3 · E4 · E1) — CyberFlow vs Suricata

**Fecha:** 2026-10-05 · Método: replay offline del mismo PCAP (nota `19`), detector
CyberFlow **desplegado** (modelo IF + heurísticos) vs Suricata 7.0.3 + ET Open
(53 013 reglas). Umbrales justificados por la línea base (nota `24`).

## Tabla comparativa (N=1 por familia — piloto)

| Familia (MITRE) | CyberFlow — modelo | CyberFlow — heurístico | Suricata (ET Open) |
|---|---|---|---|
| **E3 · DNS alta entropía** (T1568.002) | detecta, **~131 s** (por volumen, lento) | **`dns_entropy` → LIMIT, ~1 s** (tras fix; FPR 0/527) | **No detecta** (sin firma DGA) |
| **E4 · Flood HTTP** (T1498/99) | detecta, **~4 s** | **`http_abuse` → LIMIT, ~4 s** (3889 req/60s) | ET **INFO** "Web Crawl using Curl" (bajo, por User-Agent) + ruido STREAM (artefacto) |
| **E1 · Escaneo de puertos** (T1046) | marginal (1 ventana) | **`port_scan` → BLOCK** (flow=1606, puertos únicos 0,51, handshakes 0,25 % — cumple las 3) | **No detecta** (ET SCAN apunta a `-sS`/fingerprint; HOME_NET=DMZ) |

**Lectura (apoya H1):** el detector **conductual** de CyberFlow caza las tres
familias (LIMIT/LIMIT/BLOCK), rápido; Suricata (firmas) **no ve** DGA ni escaneo
`-sT`, y el flood solo lo marca como INFO por el User-Agent de `curl`. Donde no hay
firma, CyberFlow detecta y Suricata no.

## Hallazgos de método (importantes, honestos)
1. **Desfase de reloj:** los `t0` de ataque salieron del reloj de la **Kali** y las
   ventanas del reloj del **sensor/pcap** → los tiempos absolutos (~1 s, ~4 s, ~131 s)
   son **aproximados**. El "quién detecta primero (CyberFlow vs Suricata)" sí es
   consistente (ambos sobre el reloj del pcap). **Pendiente:** anclar `t0` al primer
   paquete de ataque del PCAP (lo que ya recomendaba la nota `19`).
2. **Doblado del espejo:** neutral para CyberFlow (entrenado así) pero **ensucia el
   motor de stream de Suricata** (762 de 950 alertas de E4 eran anomalías STREAM por
   paquetes duplicados). **Resuelto:** se dedupe el PCAP para Suricata con el mismo
   criterio del motor en vivo (`deduplicar_espejo`: clave de 10 campos, ventana 5 ms,
   |ΔTTL|≤1, se queda la de mayor TTL). CyberFlow sigue con el PCAP doblado.
   - **Suricata deduplicado (justo):** E1 scan = 4 alertas, **todas STREAM** (residuo
     de reensamblado), **0 detecciones reales**. E4 flood = 6 alertas, todas STREAM.
     → **Confirma que los negativos de Suricata son reales, no artefacto del doblado.**
     El único acierto de Suricata fue, en el run crudo de E4, un **ET INFO "Web Crawl
     using Curl"** (bajo nivel, por el User-Agent de `curl` — trivialmente evadible).
3. **Suricata depende del ruleset y del tipo de escaneo:** `-sS` o reglas afinadas
   podrían detectar el escaneo; ET Open por defecto + `-sT` interno no lo hizo.
   Reportarlo como alcance, no como "Suricata no sabe escanear".
4. **El escaneo SÍ fue visible al espejo** (flow=1606), al contrario de lo que se
   temió en la nota `O` (no todo el recon lo filtró el firewall).

## Limitaciones
- **N=1 por familia.** Falta repetir **≥3** para intervalos.
- Falta **E2-brute** (necesita endpoint con 401 en el servidor).
- Comparación de **detección**; el **bloqueo** (quién corta mejor) es fase B.

## Próximas acciones
1. **Suricata justo:** re-correr E1/E4 con PCAP **deduplicado** (quita el ruido STREAM).
2. **Timing correcto:** `t0` = primer paquete de ataque del PCAP (anclar al reloj del pcap).
3. **Repetir ≥3** por familia + **E2-brute** (tras preparar el 401).
4. Desplegar el fix DNS (0,45) en vivo — con OK de Mark (cambia enforcement).

## Artefactos
Sensor1 `~/piloto/{E3,E4,E1,BASE}/` (PCAP, features.csv, eve.json). Comparador
`/tmp/{e1,e3,e4}/`. Scorer `20-`, merger de PCAP `/tmp/merge.py`.
