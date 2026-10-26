# Sección 4 (Results and Discussion) — evidencia reproducible (modelo limpio)

Trabajo de evidencia para la Sección 4 del artículo IJIES, con el modelo **desplegado**
`if_limpio_2026_10` y los heurísticos vigentes (`VERSION_UMBRALES 2026-10-06.2`). **No redacta
el artículo**: produce números, scripts y procedimiento reproducible (reglas del encargo).

Responde a las observaciones de validación interna: **F5** (modelos), **ablación** (aporte del
híbrido, 4.2), **Suricata** (4.3), **N1/N3** (LIMIT/BLOCK y tiempos, 4.4).

## Contenido

- `4.1-modelos/` — evaluación del IF limpio. Lo vigente:
  - `comparacion-metodos-2026-10-25/` — **comparación entre algoritmos** (IF congelado, OCSVM, LOF,
    Elliptic Envelope, PCA) con los mismos datos, escalador y umbral por cuantil; Tabla 7 nueva,
    puntuaciones por ventana, referencias verificadas. Sustituye a la Tabla 7 de 7 candidatos.
  - `calibracion-alfa-2026-10-24/` — sensibilidad de α con y sin las 80 ventanas Kali de validación.
  - `README-4.1-EVALUACION-MODELOS.md` y `../_campana/resultados-2026-10-23/eval41/v2/` — Tabla 6 y
    paquete canónico del 23-oct (hashes publicados; se conserva tal cual).
- `00-inventario/INVENTARIO-Y-FACTIBILIDAD.md` — estado de repos, artefactos y datos; qué es
  computable offline y qué falta; **lista exacta de faltantes + procedimiento** (reglas 8 y 9).
- `4.2-ablacion/`
  - `aporte-componentes-r2-2026-10-26/` — **VIGENTE (r2, 26-oct)**. Contiene:
    - Los episodios evaluados con la historia real.
    - Las categorías durante / posterior / sin detección / no evaluable.
    - La Tabla 8 revisada: 0 de 9 evaluables.
    - Las métricas por ventana re-verificadas.
    - El inventario 4.4 y el protocolo de ensayos nuevos.

    Ver `NOTA-R2.md`.
  - `aporte-componentes-2026-10-26/` — superada por r2; se conserva. Su Tabla 8 usaba una historia simulada. Contiene:
    - El antecedente 6/9 · 7/9 · 9/9, verificado: era del modelo contaminado y se reproduce 9/9.
    - Los 9 episodios del 5-oct re-procesados con el IF limpio (α 0,05 y 0,03), los heurísticos y el híbrido.
    - La Tabla 8 y las métricas por ventana sobre la población de la Tabla 7.
  - `ablacion_sensor.py` (+ `Tabla8-ablacion-sensor.md`, `matriz-episodios-sensor.csv`,
    `metadata-ablacion-sensor.json`) — **VÁLIDO**: IF limpio + heurísticos sobre datos del
    **sensor** (65 421 benignas + 181 ventanas Kali). Valida **FPR IF 4,53 %**.
  - `ablacion_limpio.py` — demostración de por qué el set de **laboratorio** no sirve para el
    modelo del sensor (artefacto sim→real, ~90 % FPR). Sus salidas NO son un resultado.
    Ver el `README.md` de esa carpeta.
- `_campana/` — kit para la campaña instrumentada (una corrida → Tablas 8/9/10):
  - `GUION-CAMPANA-LIMPIO.md` — runbook paso a paso.
  - `orquestar_campana.sh` — orquestador (Kali): batería N≥3 × DNS/flood/escaneo + fuerza bruta
    aparte; `marcas.jsonl` con t0/t_fin (reloj de pared + monotónico); prueba de corte real.
  - `analizar_vivo.py` — `marcas.jsonl` + `motor_decision.log` → Tabla 8 (ablación por episodio)
    + t1 + entrada para `30-metricas.py`.
  - `heuristicos_por_ventana.py` — componente heurístico en el camino de replay.

## Entradas externas (no versionadas aquí; con hash en los `metadata-*.json`)

- Datasets del sensor: `normal-reservado.csv` (65 421), `limpio.csv` (particionado con las 181
  ventanas Kali `eligible_training=False`).
- Paquete del modelo limpio (`paq_despues.joblib`, umbral `decision_function −0,069397` =
  `score_samples −0,569397`, verificado = el desplegado).
- Datasets de laboratorio: `producto-main/artifacts/dataset/multilayer-v2-{anomalies,normal}.csv`.
- Heurísticos: `producto-main/scripts/engine/heuristicos.py`.

## Estado

| Subsección | Hecho (offline, válido) | Pendiente (lo da la campaña) |
|---|---|---|
| 4.2 ablación | FPR IF 4,53 % validado; componentes en tráfico Kali real | batería fiel 3×3 → Tabla 8 |
| 4.3 Suricata | método + tooling listos (replay, modelo limpio) | PCAP por episodio → Tabla 9 |
| 4.4 tiempos | cadena t0–t5 mapeada; "no medido" declarado | ensayos post-limpio → Tabla 10 |

Revisión: 2026-10-25 (índice de 4.1); contenido de 4.2–4.4 del 2026-10-23. Repos base: `producto-main` fa9e5b0, `orquestacion-limpio` 2f72d4d.
</content>
