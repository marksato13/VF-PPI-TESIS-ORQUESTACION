# Afirmaciones científicas

Cada una con su estado y su fuente primaria. **Ninguna se escribe de memoria.**

`OBTENIDO` medido · `VALIDADO` con prueba positiva y negativa · `PLANIFICADO` no ejecutado ·
`REFUTADO` desmentido por una medición · `HISTÓRICO` medido sobre una versión anterior
(modelo o escenario distinto al vigente)

> **Dos ámbitos — no mezclar.** `CLAIM-001`…`CLAIM-014` son del **modelo de laboratorio v2
> (OCSVM)** y de la validación **F6** con el sensor en línea: **históricas**. Sus fuentes
> están publicadas en [`../historico-laboratorio/`](../historico-laboratorio/README.md). El
> despliegue **vigente** —Isolation Forest recalibrado, sensor por SPAN y enforcement
> distribuido— empieza en `CLAIM-015`. Cada cifra va con su modelo, dataset, denominador y
> escenario. Fuente transversal: la
> [ficha técnica del despliegue](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md)
> (producto, `main@01b6f3f`).

## A · Modelo de laboratorio v2 (OCSVM) y validación F6 — histórico

| ID | Afirmación | Estado | Fuente primaria |
|---|---|---|---|
| `CLAIM-001` | ROC-AUC de 0,9741 sobre el conjunto de prueba (OCSVM v2) | **HISTÓRICO** | [`07-metricas-clasificacion-comparacion-7-modelos.md`](../historico-laboratorio/fase04-modelado/07-metricas-clasificacion-comparacion-7-modelos.md) |
| `CLAIM-002` | Detección del 88,8 % sobre ataques genuinos (143/161), OCSVM v2 | **HISTÓRICO** | [`06-modelo-final-congelado-ocsvm.md`](../historico-laboratorio/fase04-modelado/06-modelo-final-congelado-ocsvm.md) |
| `CLAIM-003` | FPR de 4,71 % en laboratorio (13/276), IC [2,8 – 7,9] | **HISTÓRICO** | [`09-validacion-cruzada-y-estabilidad.md`](../historico-laboratorio/fase04-modelado/09-validacion-cruzada-y-estabilidad.md) |
| `CLAIM-004` | FPR de 25,81 % y 22,97 % en operación (F6, OCSVM) | **HISTÓRICO** | [`02-resultados-f6.md`](../historico-laboratorio/fase07-validacion-final/02-resultados-f6.md) |
| `CLAIM-005` | Bloqueo en mediana de 8,0 s (6,1 – 13,7, n = 8), modalidad en línea de F6 | **HISTÓRICO** | ídem |
| `CLAIM-006` | Cero caídas registradas en 58 corridas, 55 con verificación explícita — **en F6** (OCSVM, sensor en línea); **no** demuestra la disponibilidad del despliegue vigente | **VALIDADO (F6)** | ídem |
| `CLAIM-007` | El pipeline es determinista: 10 ajustes → mismo SHA-256 | **VALIDADO** | [`09-validacion-cruzada-y-estabilidad.md`](../historico-laboratorio/fase04-modelado/09-validacion-cruzada-y-estabilidad.md); el CI del producto reproduce el modelo publicado en cada cambio |
| `CLAIM-008` | Umbral OCSVM estable: CV 4,10 %, banda [1,6496 – 1,8132] | **HISTÓRICO** | ídem |
| `CLAIM-009` | Las variables multicapa elevan la detección de 66,5 % a 88,8 %, p < 0,001 | **HISTÓRICO** | [`07-ablacion-multicapa.md`](../historico-laboratorio/fase04-modelado/07-ablacion-multicapa.md) |
| `CLAIM-010` | Las 6 comparaciones del OCSVM son significativas (McNemar + Holm, 21 pares) | **HISTÓRICO** | [`08-significancia-entre-modelos.md`](../historico-laboratorio/fase04-modelado/08-significancia-entre-modelos.md) |
| `CLAIM-011` | Reproducibilidad: al reevaluar salen 13/276 y 158/179 exactos | **VALIDADO** | [`03-entregables/02-validacion-y-confiabilidad/`](../../03-entregables/02-validacion-y-confiabilidad/) |
| `CLAIM-012` | El sistema es apto para operación desatendida | **REFUTADO** | `CLAIM-004`: el FPR operativo de F6 lo desmiente; con el despliegue vigente no se ha medido el FPR del sistema completo |
| `CLAIM-013` | Los resultados generalizan a otra red o fecha | **PLANIFICADO** | No hay jornada externa |
| `CLAIM-014` | El sistema es pertinente para usuarios reales | **PLANIFICADO** | TAM y juicio de expertos sin respuestas |

## B · Despliegue vigente — Isolation Forest recalibrado y enforcement distribuido

Evidencia de investigación en `04-evidencias/cyberflow/` (notas K–O) y en
`02-metodologia/comparacion-cyberflow-suricata/` (31, 32). Documentos del producto fijados
a `main@01b6f3f`:
[reconciliación](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/RECONCILIACION-MANIFIESTO-MOTOR.md) ·
[model card del IF](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/dataset/MODEL_CARD_IF_RECALIBRADO.md) ·
[system card](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/docs/dataset/SYSTEM_CARD_MOTOR.md).

| ID | Afirmación | Estado | Fuente primaria |
|---|---|---|---|
| `CLAIM-015` | El motor vivo ejecuta un **Isolation Forest recalibrado** (`if_recalibrado_2026_09`), umbral `score_samples = −0,568892` (= `decision_function = −0,068892`), `calibrado_en_esta_red = true`; SHA-256 del joblib `d27f68711fcb0f6657611bd7feb17759bc4fae36b9e61fbd5ca8d1190128125a` | **OBTENIDO** (SSH, 9-oct) | reconciliación del producto; [nota L](../../04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md) |
| `CLAIM-016` | FPR del IF recalibrado sobre **test normal retenido**: **4,45 %** (65 421 ventanas). No es el FPR del sistema completo ni borra el F6 histórico. La comparación con el 92,4 % del OCSVM sin recalibrar **no aísla el efecto de recalibrar**: cambiaron modelo, datos y alcance (exclusión del plano de control, deduplicación del espejo) | **OBTENIDO** | [nota L](../../04-evidencias/cyberflow/L-recalibracion-seco-sensor1-2026-09-29.md); `ensayo-if-v2.json` (Sensor1, SHA en la reconciliación) |
| `CLAIM-017` | Detección del IF recalibrado sobre la Kali: **69 % global (54/78)**, HTTP **27/27**, escaneo **27/43**, DNS **0/8** (ensayo DNS contra un host que no era el resolver) | **OBTENIDO** | [nota M](../../04-evidencias/cyberflow/M-deteccion-kali-sensor1-2026-09-30.md) |
| `CLAIM-018` | Aporte del **stack híbrido** por episodio (3 familias × 3): modelo solo **6/9**, heurísticos solos **7/9**, combinado **9/9**. El 9/9 **no** es del modelo solo | **OBTENIDO** | [`31-ABLACION-RESULTADO.md`](../comparacion-cyberflow-suricata/31-ABLACION-RESULTADO.md), [`32-RESUMEN-RESULTADOS.md`](../comparacion-cyberflow-suricata/32-RESUMEN-RESULTADOS.md) |
| `CLAIM-019` | En esa batería el stack cubrió 9/9 donde Suricata (ET Open) cubrió 0/9 — **bajo ese ruleset y configuración** | **OBTENIDO** | [`25-RESULTADOS-BATERIA.md`](../comparacion-cyberflow-suricata/25-RESULTADOS-BATERIA.md), [`32-RESUMEN-RESULTADOS.md`](../comparacion-cyberflow-suricata/32-RESUMEN-RESULTADOS.md) |
| `CLAIM-020` | **LIMIT automático en vivo** de punta a punta: el modelo detectó la anomalía → feed firmado → relay → el agente aplicó `nftables` (reversible) | **VALIDADO** | [nota O](../../04-evidencias/cyberflow/O-enforcement-vivo-campana-ataque-2026-10-01.md) |
| `CLAIM-021` | **BLOCK aislado en banco**: una regla explícita corta el ataque en el host | **VALIDADO** | [nota N](../../04-evidencias/cyberflow/N-e2e-enforcement-2026-09-30.md) |
| `CLAIM-022` | **BLOCK automático de punta a punta** originado por la detección en vivo | **PLANIFICADO** | [`PENDIENTES.md`](../../PENDIENTES.md) |
| `CLAIM-023` | Respuesta **PERMIT / LIMIT / BLOCK**: modelo → LIMIT; `brute_force` y `port_scan` → BLOCK; `http_abuse` y `dns_entropy` → LIMIT. Caducidad LIMIT 300 s, BLOCK 300/1800/3600 s con revisión humana desde el tercero, **nunca ∞ automático**, decaimiento 24 h | **VALIDADO** (código y pruebas) | [`publicar_feed.py`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/scripts/engine/publicar_feed.py), [`escalada.py`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/scripts/engine/escalada.py) y sus pruebas |
| `CLAIM-024` | El modelo consume **28** variables (contrato v2); el extractor v3 emite **31** (añade capa 2, fuera del scoring); 27 de 28 observables | **OBTENIDO** | [`multilayer-v2.json`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/configs/features/multilayer-v2.json), [`multilayer-v3.json`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/configs/features/multilayer-v3.json) |
| `CLAIM-025` | Replicabilidad **del despliegue**: 2.ª VM instalada sin Internet, ciclo desinstalar → reinstalar sano (no es replicación de resultados en otra red) | **VALIDADO** | [nota K](../../04-evidencias/cyberflow/K-despliegue-turnkey-sensor2-2026-09-29.md) |
| `CLAIM-026` | Los heurísticos vigentes son `VERSION_UMBRALES = 2026-10-06.2` y el feed se etiqueta con esa versión | **OBTENIDO** en código (`main@9425373`); en Sensor1 la etiqueta del feed **aún** es `2026-10-06.1` → **PLANIFICADO** su corrección | [`heuristicos.py`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/01b6f3fa71bb4daca320b8928ef912e5f4dc8dc2/scripts/engine/heuristicos.py); [`ESTADO.md`](../../ESTADO.md) |
| `CLAIM-027` | El umbral promovido al motor es el mismo punto de corte en `decision_function` y en `score_samples` (`offset_ = −0,5`); la única diferencia, 2,1·10⁻⁷, es el redondeo a 6 decimales del manifiesto | **VALIDADO** sobre el artefacto vivo (Sensor1, 10-oct) | [nota P](../../04-evidencias/cyberflow/P-equivalencia-umbral-sensor1-2026-10-10.md); [`verificar_equivalencia_umbral.py`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/98d7c62c90b656cca6ae5e0e9843107bb7687922/scripts/modeling/verificar_equivalencia_umbral.py) |

| `CLAIM-028` | La cadena publicada entrenar (contrato v2) → `promover_preliminar.py` → verificar produce un artefacto que el motor carga, y desde el paquete original reproduce el modelo vivo **funcionalmente** (scores idénticos en 5000 filas, mismo orden de variables, umbral igual salvo redondeo); **no** es una reproducción byte a byte | **VALIDADO** (Sensor1, 10-oct) | [nota Q](../../04-evidencias/cyberflow/Q-promocion-reproducible-sensor1-2026-10-10/README.md); `tests/test_promover_preliminar.py` |

## Afirmaciones que NO deben hacerse

| No decir | Por qué | Qué decir |
|---|---|---|
| «El motor despliega OCSVM» | El motor vivo ejecuta el IF recalibrado (SSH, 9-oct) | «El modelo activo es el Isolation Forest recalibrado; el OCSVM es el modelo de laboratorio histórico» |
| «La recalibración bajó el FPR de 92,4 % a 4,45 %» | Entre ambas mediciones cambiaron modelo, datos y alcance | «Sin recalibrar, el OCSVM dio 92,4 % en los primeros minutos; el IF recalibrado da 4,45 % sobre test normal retenido. La comparación no aísla el efecto de recalibrar» |
| «Cero caídas» como disponibilidad del sistema actual | Las 58 corridas son de F6 (OCSVM, sensor en línea) | «En F6 no se registró ninguna caída en 58 corridas (55 verificadas); el despliegue vigente no se ha medido con ese protocolo» |
| «Nuestros resultados son replicables» | No hay datos nuevos de otra red | «Son **reproducibles**; la replicabilidad en otra red está pendiente» |
| «El modelo alcanza 88,8 %» sin matiz | Es el máximo del OCSVM sobre 7 candidatos evaluados en el mismo conjunto | «88,8 % es un máximo histórico del OCSVM, no una estimación limpia» |
| «CyberFlow detecta 9/9» | El 9/9 es del stack por episodio, no del modelo solo (6/9) | «El stack (modelo + heurísticos) cubrió 9/9; el modelo solo, 6/9» |
| «El FPR del sistema es 4,45 %» | Es del modelo sobre test normal retenido | «4,45 % es el FPR del IF sobre test normal; el del sistema se mide aparte» |
| «Suricata nunca detecta» | El 0/9 es bajo ET Open en esa configuración | «Bajo ese ruleset, Suricata cubrió 0/9 de esa batería» |
| «El panel muestra las métricas del modelo desplegado» | Hasta regenerar su unidad, el panel de Sensor1 muestra las del OCSVM (detector por omisión) | «Las cifras del modelo vigente están en la ficha técnica y la model card; el panel se corrige al regenerar su unidad» |
| «El artefacto se reproduce byte a byte» | La reproducción desde el paquete da los mismos scores, pero otro fichero | «Se reproduce funcionalmente: mismos scores y mismo umbral salvo redondeo» |
| «Bloqueo inline en el sensor» | El sensor es SPAN y no bloquea; lo aplica el agente del host | «El sensor decide; el host aplica la acción por feed firmado» |
| «Calidad validada según ISO 25010» | 4 de 8 características sin evidencia | «Cuatro con evidencia y cuatro sin ella» |
