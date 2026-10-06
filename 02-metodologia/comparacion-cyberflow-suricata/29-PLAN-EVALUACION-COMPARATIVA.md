# 29 · Plan de evaluación comparativa y mejora de CyberFlow

Insumo para la **fase de metodología** (evaluación experimental) y para el backlog
del producto. Define QUÉ se mide, CÓMO, contra QUÉ, y qué mejoras persiguen una
contribución **defendible**. La redacción académica la lleva el compañero; este
documento es el contrato técnico de qué medir.

## 0. Reencuadre honesto del objetivo

**No** se busca demostrar que CyberFlow es "mejor que todo". El episodio Nikto
(nota `28`) ya mostró que, ante un ataque **con firma**, Suricata detecta antes
(3,4 s vs 12 s). Una tesis demuestra una **contribución acotada y medida**:

> **CyberFlow detecta una clase de amenazas que las firmas no ven (sin firma /
> conductual), con un FPR operable y respuesta automática, como COMPLEMENTO —no
> reemplazo— de un IDS por firmas.**

Todas las métricas de abajo sirven para **cuantificar esa contribución**, no para
un "le gano en todo" (que es indefendible y falso).

### Ejes donde CyberFlow SÍ tiene ventaja (lo que se demuestra)

| Eje | Quién gana | Evidencia |
|---|---|---|
| Cobertura de lo **sin firma** (DGA, flood, scan, ARP) | **CyberFlow** | batería 3/3 vs 0/9 (nota 26) |
| Firma conocida (tiempo/precisión) | Suricata | Nikto 3,4 s vs 12 s (nota 28) |
| Adaptación a la red real (FPR sim→real) | **CyberFlow** | 92,4 % → 4,45 % |
| Respuesta automática (PERMIT/LIMIT/BLOCK) | **CyberFlow** | enforcement en vivo |
| Interpretabilidad / mantenimiento | matizado | reglas vs reentrenamiento |

## 1. Marco de métricas

### A. Eficacia de detección (por familia y agregado)
- **TPR / Recall**, **FPR**, **Precisión**, **F1**, **Exactitud**.
- **Cobertura** = nº de familias detectadas (el diferenciador clave).
- **Curva Precisión-Recall / AUC** del modelo variando el umbral → justifica el
  umbral congelado `score_samples < −0,568892`.
- Matriz de confusión por familia; ventana como unidad (o episodio).

### B. Tiempo (diferenciado — ya definido en nota 26/tiempos)
- `t_detección` / `t_decisión` / `t_respuesta`, anclados al reloj del paquete.
- **Comparable entre detectores solo donde AMBOS detectan** (hoy: Nikto). En el
  resto se reporta como caracterización propia de CyberFlow, no como carrera.

### C. Operación / robustez
- **FPR bajo deriva** (distribution shift sim→real) — punto fuerte.
- **Throughput sostenible** (pps) y **drops** de captura (RX-drops del espejo).
- **Recursos** (CPU/RAM) por detector → coste de la detección (fairness).
- **Reproducibilidad**: mismo PCAP (hash) → mismo resultado.

### D. Criterios cualitativos (tabla, no numérica)
Dependencia de firmas, capacidad ante zero-day/desconocido, interpretabilidad del
veredicto, esfuerzo de mantenimiento (reglas vs reentrenamiento), licencia/opensource.

## 2. Contra qué comparar ("otros modelos")

1. **Suricata (firmas, ET Open)** — baseline principal. ✅ hecho (notas 26, 28).
2. **Ablación interna** (barata y muy citable): *modelo solo* vs *modelo +
   heurísticos* vs *heurísticos solos* → aísla el aporte de cada componente.
3. **Baseline estadístico** (umbral simple sobre una sola feature) → demuestra que
   el ML aporta sobre lo trivial.
4. **OCSVM vs IsolationForest** (opcional) → justifica la elección del modelo de
   anomalía (ya hubo un OCSVM previo).
5. **Zeek** como 2º IDS conductual (ambicioso, solo si sobra tiempo).

## 3. Protocolo experimental (reusa lo existente)

- Método **replay del mismo PCAP** a cada detector, reloj del paquete (nota 19).
- Episodios: familias de la batería (DGA, flood, scan) + **Nikto** (control con
  firma) + **E2-brute** (pendiente endpoint 401). Kali 10.10.20.30 → DMZ 10.10.30.10.
- **N ≥ 3** por episodio (hoy N=1–3); reportar **mediana [rango]**.
- Suricata+ET Open corre en el comparador (10.10.60.13); CyberFlow en sensor1.
- Artefactos verificables: PCAP (hash), `eve.json`, `motor_decision.log`,
  `features.csv`, `comparacion.json` (orquestador nota 22).

## 4. Backlog de mejora del producto (priorizado, atado a debilidades MEDIDAS)

| # | Mejora | Por qué (evidencia) | Esfuerzo |
|---|---|---|---|
| 1 | Afinar `port_scan` (ventana/umbral para escaneos cortos) | disparó 1/3 (nota 26) | bajo |
| 2 | Respuesta rápida para severidad alta (feed event-driven, no solo minutely) | respuesta 1–2,5 min (tiempos) | medio |
| 3 | Reentrenar **v3 con features L2** | ARP spoof 0 %; recom. ing. Fernando | alto |
| 4 | Mejorar modelo **DNS** (hoy 0 %, lo salva el heurístico) | nota 26 | medio |
| 5 | Cerrar **fuerza bruta (E2)** con endpoint 401 | modelo 50–55 % | bajo (falta abrir red) |
| 6 | **Ampliar N** (campaña grande, repeticiones) | N=1–3 hoy | medio |

> Toda mejora apunta a la contribución honesta (cobertura, FPR, operación), **no** a
> intentar ganarle a las firmas en su terreno.

## 5. Criterio de cierre

La evaluación está "lista para defender" cuando, por cada familia y con N≥3, hay
una tabla con TPR/FPR/Precisión/F1 + los 3 tiempos, la matriz de cobertura
CyberFlow-vs-Suricata, y la ablación que aísla el aporte de modelo vs heurísticos —
todo reproducible desde los PCAP (hash) y los scripts de las notas 19–28.
