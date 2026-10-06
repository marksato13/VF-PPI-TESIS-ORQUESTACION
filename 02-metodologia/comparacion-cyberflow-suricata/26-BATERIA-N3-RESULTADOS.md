# 26 · Batería N=3 por familia — CyberFlow vs Suricata

**Fecha:** 2026-10-05 · 9 episodios (E3-dns, E4-flood, E1-scan × 3 repeticiones),
automatizados (orquestador en el bastión). Método: replay offline del mismo PCAP
(nota `19`); **timing anclado al reloj del SENSOR** (corrige el desfase visto antes);
Suricata sobre PCAP **deduplicado** (excluidas las anomalías STREAM artefactuales);
umbral DNS corregido a 0,45 (notas `23`/`24`).

## Resultados por repetición

| Fam | Rep | CyberFlow heurístico | t_det heur (s) | CyberFlow modelo | t_det modelo (s) | Suricata |
|---|---|---|---|---|---|---|
| E3-dns | 1 | `dns_entropy`→LIMIT | 13 | — (0) | — | 0 |
| E3-dns | 2 | `dns_entropy`→LIMIT | 9 | — (0) | — | 0 |
| E3-dns | 3 | `dns_entropy`→LIMIT | 14 | — (0) | — | 0 |
| E4-flood | 1 | `http_abuse`→LIMIT | 10 | sí (10 vent.) | 10 | 0 |
| E4-flood | 2 | `http_abuse`→LIMIT | 14 | sí (10) | 4 | 0 |
| E4-flood | 3 | `http_abuse`→LIMIT | 19 | sí (10) | 9 | 0 |
| E1-scan | 1 | — | — | sí (1 vent.) | 23 | 0 |
| E1-scan | 2 | `port_scan`→BLOCK | 21 | sí (2) | 21 | 0 |
| E1-scan | 3 | — | — | sí (1) | 23 | 0 |

## Resumen (mediana [rango])

| Familia | CyberFlow detecta | t_detección (s) | Suricata detecta |
|---|---|---|---|
| **E3-dns** | **3/3** (heurístico `dns_entropy`) | **13 [9–14]** | **0/3** |
| **E4-flood** | **3/3** (modelo **y** `http_abuse`) | modelo **9 [4–10]** · heur 14 [10–19] | **0/3** |
| **E1-scan** | **3/3** (modelo, marginal); `port_scan` **1/3** | modelo **23 [21–23]** | **0/3** |

## Hallazgos
1. **Suricata (ET Open, 53 013 reglas): 0 detecciones en los 9 episodios.** Consistente
   con el piloto: sin firma para DGA, flood volumétrico ni escaneo `-sT` interno.
2. **CyberFlow detecta en las 3 familias, en todas las repeticiones** (vía heurístico
   para DNS y flood; vía modelo para el escaneo).
3. **DNS:** el heurístico corregido dispara **3/3** en **9–14 s** (antes: nunca). El
   modelo **no** disparó en corridas de 90 s (necesita más volumen/tiempo — antes
   detectó a 131 s en una corrida de 4 min). → el **heurístico es la vía rápida y
   fiable** para DGA; el modelo, lento y dependiente del volumen.
4. **Flood:** modelo y heurístico, ambos **3/3**, rápido (modelo mediana 9 s).
5. **Escaneo:** el modelo lo marca **3/3** pero **marginal** (1–2 ventanas, ~23 s);
   `port_scan` solo disparó **1/3** → **debilidad real**: un escaneo breve (~17 s) no
   siempre llena una ventana de 30 s con las 3 condiciones. **Acción:** escaneos más
   largos o ajustar la ventana del heurístico; reportar como limitación.

## Limitaciones (honestas)
- **N=3** (piloto ampliado, no campaña grande). Para la tesis conviene N mayor.
- Tiempos ahora **anclados al reloj del sensor** (consistentes y comparables entre
  detectores); son mayores que el "~1 s" del primer piloto porque `t0` = **lanzamiento
  del ataque** (no la 1ª ventana) y la feature de 60 s necesita acumular.
- **Suricata 0/9** con ET Open **por defecto** + `-sT` + HOME_NET=DMZ + replay; un
  ruleset afinado o `-sS` podrían variar. Reportar como alcance, no como absoluto.
- Enforcement **en vivo** durante la batería: no afecta la detección (el sensor ve el
  tráfico en el espejo antes del bloqueo en el host).
- Falta **E2-brute** (necesita endpoint 401) y la comparación de **bloqueo** (fase B).

## Conclusión para la tesis
Bajo los mismos ataques y la misma línea base, **CyberFlow (conductual) detecta las
tres familias en las 3 repeticiones y Suricata (firmas) ninguna** — el aporte que
pide el asesor, cuantificado. El valor diferencial está en lo **sin firma** (DGA,
volumen, escaneo), donde el heurístico/modelo actúan y las firmas no.
