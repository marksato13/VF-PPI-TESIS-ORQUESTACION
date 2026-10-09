# Afirmaciones científicas

Cada una con su estado y su fuente primaria. **Ninguna se escribe de memoria.**

`OBTENIDO` medido · `VALIDADO` con prueba positiva y negativa · `PLANIFICADO` no ejecutado
· `HISTÓRICO` medido sobre una versión anterior (modelo/escenario distinto al vigente)

> **Dos ámbitos — no mezclar.** Las afirmaciones `CLAIM-001`…`CLAIM-014` son del
> **modelo de laboratorio v2 (OCSVM)** y de la validación **F6**: son **HISTÓRICAS**.
> El despliegue **vigente** usa el **Isolation Forest recalibrado** (`if_recalibrado_2026_09`)
> con **enforcement distribuido** (SPAN → feed firmado → agente); sus afirmaciones son
> `CLAIM-015` en adelante. Cada cifra va con su modelo, dataset, denominador y escenario.
> Fuente transversal: `CYBERFLOW/producto-as-deployed/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md`.

## A · Modelo de laboratorio v2 (OCSVM) y validación F6 — HISTÓRICO

| ID | Afirmación | Estado | Fuente primaria |
|---|---|---|---|
| `CLAIM-001` | ROC-AUC de 0,9741 sobre el conjunto de prueba (OCSVM v2) | **HISTÓRICO** | `docs/fase04-modelado/07-metricas-clasificacion-comparacion-7-modelos.md` |
| `CLAIM-002` | Detección del 88,8 % sobre ataques genuinos (143/161), OCSVM v2 | **HISTÓRICO** | `docs/fase04-modelado/06-modelo-final-congelado-ocsvm.md` |
| `CLAIM-003` | FPR de 4,71 % en laboratorio (13/276), IC [2,8 – 7,9] | **HISTÓRICO** | `docs/fase04-modelado/09-validacion-cruzada-y-estabilidad.md` |
| `CLAIM-004` | FPR de 25,81 % y 22,97 % en operación real (F6, OCSVM) | **HISTÓRICO** | `docs/fase07-validacion-final/02-resultados-f6.md` |
| `CLAIM-005` | Bloqueo en mediana de 8,0 s (6,1 – 13,7, n = 8), modalidad en línea F6 | **HISTÓRICO** | ídem |
| `CLAIM-006` | Cero caídas en 58 corridas, 55 con verificación explícita | **VALIDADO** | ídem |
| `CLAIM-007` | El pipeline es determinista: 10 ajustes → mismo SHA-256 | **VALIDADO** | `docs/fase04-modelado/09-validacion-cruzada-y-estabilidad.md` |
| `CLAIM-008` | Umbral OCSVM estable: CV 4,10 %, banda [1,6496 – 1,8132] | **HISTÓRICO** | ídem |
| `CLAIM-009` | Las variables multicapa elevan la detección de 66,5 % a 88,8 %, p < 0,001 | **HISTÓRICO** | `docs/fase04-modelado/07-ablacion-multicapa.md` |
| `CLAIM-010` | Las 6 comparaciones del OCSVM son significativas (McNemar + Holm, 21 pares) | **HISTÓRICO** | `docs/fase04-modelado/08-significancia-entre-modelos.md` |
| `CLAIM-011` | Reproducibilidad: al reevaluar salen 13/276 y 158/179 exactos | **VALIDADO** | `docs/entregables/02-validacion-y-confiabilidad/` |
| `CLAIM-012` | El sistema es apto para operación desatendida | **REFUTADO** | `CLAIM-004`: el FPR operativo lo desmiente |
| `CLAIM-013` | Los resultados generalizan a otra red o fecha | **PLANIFICADO** | No hay jornada externa. Ver `P-4` |
| `CLAIM-014` | El sistema es pertinente para usuarios reales | **PLANIFICADO** | TAM/juicio de expertos sin respuestas. Ver `P-3` |

## B · Despliegue vigente — Isolation Forest recalibrado + enforcement distribuido

Evidencia en `04-evidencias/cyberflow/` (notas L–O) y
`02-metodologia/comparacion-cyberflow-suricata/` (31, 32). Verificación por SSH en
Sensor1: `CYBERFLOW/producto-as-deployed/docs/RECONCILIACION-MANIFIESTO-MOTOR.md`.

| ID | Afirmación | Estado | Fuente primaria |
|---|---|---|---|
| `CLAIM-015` | El motor vivo corre **Isolation Forest recalibrado** (`if_recalibrado_2026_09`), umbral `score_samples=−0,568892` (=`decision_function=−0,068892`), `calibrado_en_esta_red=true`; SHA-256 `d27f68…125a` | **OBTENIDO** (SSH 2026-10-09) | `RECONCILIACION-MANIFIESTO-MOTOR.md`; `04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md` |
| `CLAIM-016` | FPR del IF recalibrado sobre **test normal retenido**: **4,45 %** (65 421 ventanas); baja desde 92,4 % sin recalibrar. **No** es el FPR del sistema completo ni borra el F6 histórico | **OBTENIDO** | nota `L`; `ensayo-if-v2.json` (Sensor1) |
| `CLAIM-017` | Detección del IF recalibrado sobre Kali: **69 % global (54/78)**, HTTP **27/27**, escaneo **27/43**, DNS **0/8** | **OBTENIDO** | `04-evidencias/cyberflow/M-deteccion-kali-sensor1-2026-09-30.md` |
| `CLAIM-018` | Aporte del **stack híbrido** por episodio (3 familias × 3): modelo solo **6/9**, heurísticos solos **7/9**, combinado **9/9**. El 9/9 **no** es del modelo solo | **OBTENIDO** | `02-metodologia/comparacion-cyberflow-suricata/31-ABLACION-RESULTADO.md`, `32-RESUMEN-RESULTADOS.md` |
| `CLAIM-019` | En esa batería, CyberFlow (stack) cubrió 9/9 donde Suricata (ET Open) cubrió 0/9 — **bajo ese ruleset/configuración**, no «Suricata nunca detecta» | **OBTENIDO** | `25-RESULTADOS-BATERIA.md`, `32-RESUMEN-RESULTADOS.md` |
| `CLAIM-020` | **LIMIT automático en vivo** end-to-end: el modelo detectó la anomalía → feed firmado → relay → agente aplicó `nftables` (rate-limit específico a la Kali, reversible) | **VALIDADO** | `04-evidencias/cyberflow/O-enforcement-vivo-campana-ataque-2026-10-01.md` |
| `CLAIM-021` | **BLOCK aislado en banco**: una regla explícita corta el ataque en el host | **VALIDADO** | `04-evidencias/cyberflow/N-e2e-enforcement-2026-09-30.md` |
| `CLAIM-022` | **BLOCK automático end-to-end originado por la detección en vivo** | **PLANIFICADO** | PENDIENTES §enforcement; falta la corrida con `brute_force` sostenido |
| `CLAIM-023` | Escalera de caducidad **LIMIT 300 s · BLOCK 300/1800/3600 s** + revisión humana, **nunca ∞ automático**; decaimiento 24 h | **VALIDADO** | `scripts/engine/escalada.py` + `tests/test_escalada.py` |
| `CLAIM-024` | El modelo consume **28** variables (contrato v2); el extractor v3 emite **31** (añade capa 2, fuera del scoring); 27 de 28 observables | **OBTENIDO** | `configs/features/multilayer-v2.json` y `multilayer-v3.json`; FICHA §3 |
| `CLAIM-025` | Replicabilidad llave-en-mano: 2ª VM instalada **100 % offline**, ciclo desinstalar→reinstalar sano | **VALIDADO** | `04-evidencias/cyberflow/K-despliegue-turnkey-sensor2-2026-09-29.md` |

## Afirmaciones que NO deben hacerse

| No decir | Por qué | Qué decir |
|---|---|---|
| «El motor despliega OCSVM» | El motor vivo corre IF recalibrado (SSH 9-oct); OCSVM es histórico | «El modelo activo es el Isolation Forest recalibrado; OCSVM es el modelo de laboratorio histórico» |
| «Nuestros resultados son replicables» | No hay datos nuevos de otra red | «Son **reproducibles**; la replicabilidad en otra red está pendiente» |
| «El modelo alcanza 88,8 %» sin matiz | Es el máximo del OCSVM sobre 7 candidatos evaluados en el mismo conjunto (histórico) | «88,8 % es un máximo histórico del OCSVM, no una estimación limpia» |
| «CyberFlow detecta 9/9» | El 9/9 es del **stack híbrido** por episodio, no del modelo solo (6/9) | «El stack (modelo + heurísticos) cubrió 9/9; el modelo solo, 6/9» |
| «El FPR del sistema es 4,45 %» | Es del modelo sobre test normal retenido, no del sistema con heurísticos+enforcement | «4,45 % es el FPR del IF sobre test normal; el del sistema se mide aparte» |
| «Suricata nunca detecta» | El 0/9 es bajo ET Open en esa configuración | «Bajo ese ruleset, Suricata cubrió 0/9 de esa batería» |
| «Bloqueo inline en el sensor» | El sensor es SPAN y no bloquea; lo aplica el agente en el host | «El sensor decide; el host aplica la acción por feed firmado» |
| «Calidad validada según ISO 25010» | 4 de 8 características sin evidencia | «Cuatro con evidencia y cuatro sin ella» |
