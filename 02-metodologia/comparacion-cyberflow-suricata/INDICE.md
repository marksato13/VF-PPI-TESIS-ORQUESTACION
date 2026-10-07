# Índice — comparación CyberFlow vs Suricata

Guía rápida de las notas de esta carpeta (para redactar la metodología/resultados).

## Preparación de infraestructura (00–18)
Topología SPAN, captura, instalación offline de Suricata + ET Open, piloto pasivo,
propuesta NTP y auditoría pfSense. (Método inicial de comparación en vivo; superado
por el replay — ver nota 19.)

## Método y herramientas (19–22, 30)
- **19 — MÉTODO REPLAY PCAP**: el enfoque definitivo. Mismo PCAP a ambos detectores,
  tiempo anclado al paquete → **sin NTP, sin desfase de relojes**.
- **20 — puntuar-por-ventana.py**: scorer del modelo congelado (Pipeline + manifest).
- **21 — ESCENARIOS DE ATAQUE**: familias justificadas (MITRE + línea base).
- **22 — correr-piloto.py**: orquestador de un episodio (Suricata + CyberFlow + comparación).
- **30 — metricas.py**: TPR/FPR/Precisión/F1, latencia, cobertura y **ablación** (+ tests).

## Línea base y resultados (23–28, 31–32)
- **23 — RESULTADO PILOTO DNS**, **24 — LÍNEA BASE** (pps, umbrales justificados).
- **25 — RESULTADOS BATERÍA**, **26 — BATERÍA N=3**: CyberFlow **9/9** vs Suricata **0/9**
  (DNS, flood, escaneo). El resultado principal.
- **27 — EPISODIO NIKTO** (método) y **28 — RESULTADO NIKTO**: episodio de control
  CON firma → comparación de **tiempo** (Suricata 3,4 s gana por firma; CyberFlow 12 s).
- **31 — ABLACIÓN**: modelo 6/9, heurísticos 7/9, combinado **9/9** (justifica el híbrido).
- **32 — RESUMEN DE RESULTADOS**: síntesis para la defensa (incluye la 4ª familia,
  fuerza bruta, confirmada en vivo).

## Plan
- **29 — PLAN DE EVALUACIÓN**: métricas, criterios, modelos a comparar, backlog.

## Relacionado (otros repos)
- Producto *as-deployed*: `producto-as-deployed/` (código, modelo, enforcement). Docs
  clave: `GUION-DEMO.md`, `VALIDACION-INTERNA-TECNICA.md`, `MEJORA-PORT-SCAN.md`,
  `PLAN-REENTRENAMIENTO.md`, `evidencias/tiempos-2026-10-06.md`, `demo/brute/`.
