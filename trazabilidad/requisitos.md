# Requisitos

Fuente: observaciones del jurado (`docs/requisitos-jurado/README.md` del
producto) y las consignas de las Sesiones 01, 02 y 04 del curso.

| ID | Requisito | Origen | Fase | Estado | Evidencia |
|---|---|---|---|---|---|
| `REQ-001` | El dataset debe incluir tráfico legítimo pesado (500–1500 bytes) | Jurado, obs. 1 | F04 | **Cumplido con reserva** | 90,84 % de payloads en rango · pero produce el FPR de `RISK-001` |
| `REQ-002` | Las variables deben cubrir capas 3, 4 y 7 | Jurado, obs. 2 | F03 | **Cumplido** | 28 variables, 27 observables, con diccionario |
| `REQ-003` | Cada variable con fórmula, ventana, fuente y coste | Jurado, obs. 2 | F03 | **Cumplido** | Diccionario generado desde el extractor congelado |
| `REQ-004` | Ablación que demuestre el aporte de cada capa | Jurado | F05 | **Cumplido** | 66,5 % → 88,8 %, p < 0,001 |
| `REQ-005` | Jornada de holdout temporal externa | Jurado | F08 | **No cumplido** | `P-4`, agendado 24 oct |
| `REQ-006` | 14 escenarios normales | Jurado, obs. 1 | F02 | **Parcial** | Faltan 4 · `P-5`, agendado 19 sep |
| `REQ-007` | Informe de evaluación crítica de 2–4 pp | Sesión 01, diap. 33 | F09 | **Cumplido** | `DOC-001`, 3,8 pp |
| `REQ-008` | Amenazas a la validez declaradas | Sesión 01, diap. 27 | F09 | **Cumplido** | Sección 5 de `DOC-001` |
| `REQ-009` | Evaluación contra ISO/IEC 25010 | Sesión 01, diap. 7 y 23 | F09 | **Cumplido** | 4 de 8 características con evidencia |
| `REQ-010` | Plan de validación de 1–2 pp con los 3 ejes | Sesión 02, diap. 33 | F09 | **Cumplido** | `DOC-002`, 2,0 pp |
| `REQ-011` | Confiabilidad con método concreto y verificable | Sesión 02, diap. 14–17 | F05 | **Cumplido** | Determinismo + bootstrap + test-retest |
| `REQ-012` | Replicabilidad por ciencia abierta | Sesión 02, diap. 19–22 | F04 | **Parcial** | Los 5 puntos del checklist sí; **falta DOI y preregistro** |
| `REQ-013` | Pertinencia validada con usuarios reales | Sesión 02, diap. 23–27 | F08 | **No cumplido** | `P-3`, SUS con 0 respuestas |
| `REQ-014` | Detección temprana con bloqueo inline | Objetivo de la tesis | F06 | **Cumplido** | Lead time mediano de 8,0 s en 58 corridas |
| `REQ-015` | Matriz de decisión con criterios ponderados | Sesión 04, diap. 14–15 | F09 | **Cumplido** | `DOC-003`, 9 candidatas, pesos al 100 % |
| `REQ-016` | Mapeo de ≥12 artículos con nombres reales de sección | Sesión 05 | F09 | **Cumplido** | `DOC-004`, 21 artículos, 7 semilla |
