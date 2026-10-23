# 4.3 — Comparación por replay (pasada limpia 2026-10-23)

Método de replay (nota 19): un solo PCAP (`/tmp/campana-pcap/pass.pcap`, 9 470 paquetes, 1,1 MB,
captura `tcpdump host 10.10.20.30` en el sensor) pasado por CyberFlow (modelo limpio
`if_limpio_2026_10` + heurísticos `2026-10-06.2`, vía `extract_multilayer_v2` → score_samples) y por
Suricata 7.0.3. Episodios bien separados: DNS, flood HTTP, escaneo. Scripts/evidencia en esta carpeta
(`replay_43.py`, `features.csv`, `tabla9.json`).

## Tabla 9 (replay) — CyberFlow actual vs Suricata

| Familia | CyberFlow detecta | Componente (1ª señal) | Suricata (ET Open) |
|---|---|---|---|
| DNS alta entropía | **sí** | `dns_entropy` (heurístico) + modelo | **N/A en este replay** (ver nota) |
| Flood HTTP | **sí** | `http_abuse` (heurístico); modelo también | **N/A** |
| Escaneo de puertos | **no concluyente** | — (tráfico mínimo en el PCAP) | **N/A** |

Evidencia por ventana (atacante 10.10.20.30, reloj del paquete):
- **Flood** (17:19:10–17:19:40): `syn_count` 204→392, `http_request_count_60s` 136→543,
  `syn_completion_ratio` ~0,80 → `http_abuse` dispara. Detección sólida.
- **DNS** (17:17:30–17:18:10): ráfaga de flujos DNS; `dns_entropy` + modelo. Detección sólida.
- **Escaneo** (17:21:40–17:22:00): `flow_attempt_count_30s` **1–6**, casi sin tráfico → por debajo de
  cualquier umbral de `port_scan`. No detectado **offline**.

## Salvedades honestas (obligatorias)

1. **Suricata del sensor corre SIN reglas de amenaza.** `/var/lib/suricata/rules/suricata.rules` está
   **vacío** (SHA de cadena vacía); la instancia es una **fuente de eventos EVE** (http/dns/tls) para el
   motor, no un detector de firmas. Por eso "0 alertas" aquí **NO es un comparador válido** y **no se
   presenta como "Suricata no detecta"**. La comparación Suricata-ET-Open válida es la **histórica del
   14-oct** (ET Open, 53 013 reglas: **0/9** en DNS/flood/escaneo —sin firma— y **sí** en Nikto por firma;
   notas 26/28), sobre **otro PCAP**. **Faltante:** cargar el ruleset ET Open congelado del 14-oct (o un
   bundle offline) y re-correr `suricata -r pass.pcap` con él; declarar versión + SHA del ruleset.
2. **Desfase de relojes Kali↔sensor (~40 s):** las ráfagas aparecen en el PCAP (reloj del sensor) ~40 s
   antes que la marca `t0` de la Kali. Por eso **los tiempos absolutos "t desde el inicio" con la marca de
   la Kali no son fiables**; la comparación interna por replay (qué detecta primero, mismo PCAP) sí es
   limpia. Para tiempos absolutos hay que anclar `t0` al primer paquete del ataque (reloj del paquete).
3. **Escaneo con tráfico mínimo en el PCAP de archivo:** en vivo el escaneo produjo corte real
   (`filtered`), pero en la captura quedó muy poco tráfico de escaneo (se cortó muy rápido), así que el
   replay no lo detecta. **No se concluye que CyberFlow falle el escaneo**; se re-mide con un escaneo que
   complete más ventanas antes de cualquier corte (batería N≥3 limpia).
4. **Nikto:** aún no ejecutado (la Tabla 5 del artículo lo prevé). Pendiente.

## Estado 4.3
- **EJECUTADO (CyberFlow por replay):** DNS y flood detectados sobre el mismo PCAP; escaneo inconcluso.
- **PENDIENTE:** (a) Suricata con **ET Open** cargado para un comparador válido sobre este PCAP;
  (b) escaneo con más volumen/ventanas; (c) **Nikto** como control; (d) anclar tiempos al reloj del paquete.
- La afirmación defendible hoy: **CyberFlow (híbrido) detecta DNS y flood sin firma por replay; la
  comparación con Suricata-ET-Open válida es la histórica (0/9 sin firma, Nikto por firma) y debe
  rehacerse sobre este PCAP con el ruleset cargado.**
</content>
