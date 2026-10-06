# 23 · Resultado del piloto E3-dns-01 (CyberFlow vs Suricata)

**Fecha:** 2026-10-05 · **Método:** replay offline del mismo PCAP (nota `19`).
**Campaña:** `E3-dns-01`. Ataque DNS de alta entropía (T1568.002).

## Montaje del episodio
- **Atacante:** Kali `10.10.20.30` → resolver real `10.10.10.20`.
- **Ventana (ground truth):** `2026-10-05T19:18:09Z` → `19:22:09Z` (240 s).
- **Carga:** **557 consultas**, nombres **aleatorios únicos** (`<rand>.ejemplo-inexistente`).
- **PCAP:** 18 ficheros del anillo `ppi-motor-capture` (`live-*.pcap`), 15 187 paquetes.
  Mismo PCAP a los dos detectores. Reloj = timestamp del paquete (sin NTP).
- **Detector CyberFlow evaluado:** el **desplegado** en Sensor1
  (`if_recalibrado_desplegable.joblib`, umbral `score_samples < -0.568892`, esquema v2, 28 features).
- **Suricata:** 7.0.3 + ET Open (53 013 reglas) en el comparador `10.10.60.13`.

## Tabla comparativa

| Detector | ¿Detecta el ataque DNS? | Tiempo de detección | Evidencia |
|---|---|---|---|
| **CyberFlow — modelo** (IsolationForest recalibrado) | **Sí** | **~131 s** | 10/24 ventanas de la Kali alertadas; primera a `19:20:20Z` |
| **CyberFlow — heurístico `dns_entropy`** (umbral original 0.9) | **No** (bug, ver abajo) | — | 0/24 ventanas con el umbral mal puesto |
| **CyberFlow — heurístico `dns_entropy`** (umbral corregido 0.45) | **Sí** | **~1 s** | 23/24 ventanas; primera a `19:18:10Z` → LIMIT |
| **Suricata** (ET Open, 53 013 reglas) | **No** | — | 0 alertas sobre el flujo Kali↔resolver (3 alertas totales en la ventana, ninguna del DNS) |

**Lectura:** ante DNS de alta entropía **sin firma**, **CyberFlow (modelo) detecta y Suricata no** → apoya la hipótesis H1. Pero el modelo detecta **tarde** (131 s) y por **volumen**, no por entropía: con `dns_query_count_60s=280` el `score` se queda rozando el umbral ~2 min antes de cruzar.

## Hallazgo: por qué el heurístico `dns_entropy` no dispara (bug de features)
Medido sobre la ventana de la Kali:

| Feature | Valor observado | Umbral del heurístico | ¿Se cumple? |
|---|---|---|---|
| `dns_query_count_60s` | 0 → 48 → … → **280** | ≥ 20 | ✅ |
| `dns_nxdomain_ratio_60s` | **0.0** | ≥ 0.5 | ❌ |
| `unique_dns_name_ratio_60s` | **0.5** (tope) | ≥ 0.9 | ❌ |

### Causa raíz (confirmada en código): doblado del espejo SPAN
El `dns_query` del extractor **solo cuenta consultas** (no respuestas). Entonces
`unique_dns_name_ratio=0.5` con nombres **todos únicos** solo se explica por una
cosa: **el espejo SPAN muestra cada trama dos veces** (sesión `Both` sobre dos
puertos origen). Se confirma con el conteo: `dns_query_count_60s=280`, el **doble**
de las ~140 consultas reales. Cada consulta se registra 2 veces → único/total = 0.5.

Por qué no se puede "deduplicar y ya": `dns_query_count_60s` **es una de las 28
features del modelo congelado**. El motor en vivo deduplica a nivel de **paquete**
(`v3.deduplicar_espejo`) para las features L3/L4, pero las features **DNS vienen del
`eve.json`** y quedan dobladas por igual en entrenamiento, en vivo y en el replay
(coherente con que el heurístico tampoco disparó en vivo, nota `O`). Deduplicar el
DNS ahora **cambiaría la entrada del modelo → lo invalidaría**.

**Por eso el arreglo correcto es en el heurístico** (que es ajustable por diseño,
`VERSION_UMBRALES`), no en el extractor: con el doblado, "todo único" = **0.5**, así
que el umbral debe ser **`unique_dns_name_ratio ≥ 0.45`** (no 0.9). El `nxdomain`
queda como condición OR (fue 0 aquí: el resolver responde SERVFAIL al TLD inexistente).

**Validado offline** sobre el mismo `features.csv` (monkeypatch del umbral, sin tocar
el sistema vivo): con `0.45` el heurístico dispara en **23/24 ventanas**, la primera a
`19:18:10Z` = **1,0 s**. La detección pasa de **131 s (modelo) → ~1 s (heurístico)**.

**FPR del umbral 0.45 — VALIDADO (nota `24`):** sobre 527 ventanas normales,
**0 dispararían** `dns_entropy(0.45)` → **FPR = 0 %**. El conteo DNS normal nunca
pasa de 8/60s (ataque: 280), así que el `≥20` ya separa por sí solo.

**Pendiente:** persistir el umbral `0.45` en `heuristicos.py` (bump de
`VERSION_UMBRALES`) y desplegarlo; **cambia el enforcement en vivo** (empezaría a
emitir LIMIT por DNS de alta entropía), así que requiere OK de Mark. Conviene además
una **línea base más larga** (horario activo de clientes) para reconfirmar el FPR.

## Limitaciones (honestidad metodológica)
- **N = 1** (un episodio). Falta **repetir ≥3** para dar intervalo, no un número.
- El modelo detecta por **volumen** (`dns_query_rate`), no por entropía → un **DGA sigiloso** (pocas consultas, muy únicas) probablemente **no** lo vería el modelo, y ahí el heurístico (hoy roto) es imprescindible.
- `dns_nxdomain_ratio=0` queda **por confirmar** (SERVFAIL vs rcode del extractor).
- Comparación de **detección**; el **bloqueo** inline es fase B.

## Próximas acciones
1. **Corregir el feature DNS** (`unique_dns_name_ratio` / NXDOMAIN) y re-correr E3 → medir el tiempo del heurístico.
2. **Repetir E3 ×3** + añadir `E1-scan`, `E2-brute`, `E4-flood` (nota `21`).
3. **Medir la línea base** (`‹BASE_*›`) para cerrar la justificación de umbrales (P0-06).
4. Firmar **P0-01** con el asesor.

## Reproducibilidad
Artefactos en Sensor1 `~/piloto/E3/` (PCAP, `features.csv`, `eve.json`) y en el comparador `/tmp/e3/`. Scorer: `20-puntuar-por-ventana.py`. Runner: `22-correr-piloto.py`.
