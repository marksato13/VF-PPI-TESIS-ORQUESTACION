# 31 · Resultado de la ablación (modelo vs heurísticos vs combinado)

**Fecha:** 2026-10-06 · Generado con `30-metricas.py` sobre los veredictos por
episodio de la **batería N=3** (nota `26`). Responde a la §2 del plan (nota `29`):
aislar cuánto aporta cada componente de CyberFlow.

## Resultado

| Configuración | Episodios detectados | Cobertura |
|---|---|---|
| **Modelo solo** (IsolationForest recalibrado) | 6/9 | 0,667 |
| **Heurísticos solos** | 7/9 | 0,778 |
| **Combinado (modelo OR heurísticos)** | **9/9** | **1,000** |
| Suricata (ET Open, referencia) | 0/9 | 0,000 |

Métricas del combinado (CyberFlow completo), con la línea base como negativos:
**TPR 1,0 · FPR 0,0 (0/527) · latencia mediana 13 s [4–23]**.

## Por qué cada parte NO basta sola (lo que demuestra la ablación)

- **El modelo solo falla en DNS (DGA):** 0/3 en las corridas de 90 s (necesita más
  volumen/tiempo). Lo salvan los heurísticos.
- **Los heurísticos solos fallan en 2 de 3 escaneos:** `port_scan` solo disparó 1/3
  (un escaneo corto no llena la ventana de 30 s). Lo salva el modelo (3/3 marginal).
- **Combinados: 9/9.** Cada componente cubre el hueco del otro.

## Lectura para la tesis

Esta es la justificación cuantitativa del **diseño híbrido** (ML + reglas
deterministas): no es redundancia, es **complementariedad medida**. Un detector
conductual puro (solo modelo) se quedaría en 6/9; solo reglas, en 7/9; la
arquitectura de CyberFlow que combina ambos llega a 9/9 con FPR 0 en la línea base.
Junto con la comparación externa (CyberFlow 9/9 vs Suricata 0/9 en lo sin firma;
Nikto donde Suricata gana por firma, nota 28), cierra el argumento de aportación.

## Limitaciones

- N=3 por familia (9 episodios). Repetir con N mayor para intervalos de confianza.
- Veredictos tomados de la nota 26 (mismos PCAP, reloj del sensor). La latencia del
  combinado es la detección más temprana (modelo o heurístico) por episodio.
- `precision`/`F1` mezclan unidades (TP por episodio, FP por ventana benigna); se
  reportan con esa salvedad (ver `30-metricas.py`). El dato robusto es cobertura+FPR.
- Reproducible: `python3 30-metricas.py <entrada.json>` con los veredictos de la
  nota 26.
