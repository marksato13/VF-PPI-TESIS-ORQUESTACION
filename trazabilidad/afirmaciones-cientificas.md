# Afirmaciones científicas

Cada una con su estado y su fuente primaria. **Ninguna se escribe de memoria.**

`OBTENIDO` medido · `VALIDADO` con prueba positiva y negativa · `PLANIFICADO` no ejecutado

| ID | Afirmación | Estado | Fuente primaria |
|---|---|---|---|
| `CLAIM-001` | ROC-AUC de 0,9741 sobre el conjunto de prueba | **OBTENIDO** | `docs/fase04-modelado/07-metricas-clasificacion-comparacion-7-modelos.md` |
| `CLAIM-002` | Detección del 88,8 % sobre ataques genuinos (143/161) | **OBTENIDO** | `docs/fase04-modelado/06-modelo-final-congelado-ocsvm.md` |
| `CLAIM-003` | FPR de 4,71 % en laboratorio (13/276), IC [2,8 – 7,9] | **OBTENIDO** | `docs/fase04-modelado/09-validacion-cruzada-y-estabilidad.md` |
| `CLAIM-004` | FPR de 25,81 % y 22,97 % en operación real | **OBTENIDO** | `docs/fase07-validacion-final/02-resultados-f6.md` |
| `CLAIM-005` | Bloqueo en mediana de 8,0 s (6,1 – 13,7, n = 8) | **OBTENIDO** | ídem |
| `CLAIM-006` | Cero caídas en 58 corridas, 55 con verificación explícita | **VALIDADO** | ídem |
| `CLAIM-007` | El pipeline es determinista: 10 ajustes → mismo SHA-256 | **VALIDADO** | `docs/fase04-modelado/09-validacion-cruzada-y-estabilidad.md` |
| `CLAIM-008` | Umbral estable: CV 4,10 %, banda [1,6496 – 1,8132] | **OBTENIDO** | ídem |
| `CLAIM-009` | Las variables multicapa elevan la detección de 66,5 % a 88,8 %, p < 0,001 | **OBTENIDO** | `docs/fase04-modelado/07-ablacion-multicapa.md` |
| `CLAIM-010` | Las 6 comparaciones del OCSVM son significativas (McNemar + Holm, 21 pares) | **OBTENIDO** | `docs/fase04-modelado/08-significancia-entre-modelos.md` |
| `CLAIM-011` | Reproducibilidad: al reevaluar salen 13/276 y 158/179 exactos | **VALIDADO** | `docs/entregables/02-validacion-y-confiabilidad/` |
| `CLAIM-012` | El sistema es apto para operación desatendida | **REFUTADO** | `CLAIM-004`: el FPR operativo lo desmiente |
| `CLAIM-013` | Los resultados generalizan a otra red o fecha | **PLANIFICADO** | No hay jornada externa. Ver `P-4` |
| `CLAIM-014` | El sistema es pertinente para usuarios reales | **PLANIFICADO** | SUS con 0 respuestas. Ver `P-3` |

## Afirmaciones que NO deben hacerse

| No decir | Por qué | Qué decir |
|---|---|---|
| «Nuestros resultados son replicables» | No hay datos nuevos | «Son **reproducibles**; la replicabilidad está pendiente» |
| «El modelo alcanza 88,8 %» sin matiz | Es el máximo sobre 7 candidatos evaluados en el mismo conjunto | «88,8 % es un máximo, no una estimación limpia» |
| «Calidad validada según ISO 25010» | 4 de 8 características sin evidencia | «Cuatro con evidencia y cuatro sin ella» |
| «El FPR es del 4,71 %» a secas | Solo en laboratorio | «4,71 % en laboratorio; 25,81 % y 22,97 % en operación» |
