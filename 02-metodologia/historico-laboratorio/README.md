# Histórico del laboratorio (versión anterior: OCSVM, dataset v2, F6)

Informes de investigación de la **versión anterior** del sistema, conservados aquí para
que las afirmaciones históricas y la documentación del producto tengan una **fuente
accesible**. Quedaron fuera al reorganizar este repositorio en `01`–`04`; se recuperan
sin cambios de contenido desde el registro original (`investigacion/`).

> **Son históricos.** Describen el modelo de laboratorio **OCSVM** (`ocsvm_scaled`,
> umbral 1,8126), el dataset `multilayer-v2` y la validación **F6** con el sensor **en
> línea**. El despliegue vigente es otro (Isolation Forest recalibrado, sensor por SPAN y
> enforcement distribuido): ver la ficha técnica del producto en `main`
> (`docs/FICHA-TECNICA-DESPLIEGUE-VIGENTE.md`). Ninguna cifra de esta carpeta se traslada
> al despliegue vigente.

| Fase | Informe | Lo citan |
|---|---|---|
| F2 · variables | [`fase02-features-multicapa/01-diccionario-multicapa-G5.md`](fase02-features-multicapa/01-diccionario-multicapa-G5.md) | Diccionario de las 14 primeras variables |
| F2 · variables | [`fase02-features-multicapa/02-validacion-extractor-G5.md`](fase02-features-multicapa/02-validacion-extractor-G5.md) | Validación del extractor |
| F2 · variables | [`fase02-features-multicapa/03-diccionario-multicapa-v2.md`](fase02-features-multicapa/03-diccionario-multicapa-v2.md) | Datasheet, README del corpus |
| F3 · dataset | [`fase03-dataset/README.md`](fase03-dataset/README.md) | Historial del corpus, campaña por campaña |
| F3 · dataset | [`fase03-dataset/128-calibracion-PM-F1-v1.md`](fase03-dataset/128-calibracion-PM-F1-v1.md) | Calibración F1 |
| F3 · dataset | [`fase03-dataset/174-cierre-calibracion-fragmentacion-ip-real.md`](fase03-dataset/174-cierre-calibracion-fragmentacion-ip-real.md) | Diccionario de variables |
| F3 · dataset | [`fase03-dataset/175-limite-tls-handshake-failure-ratio.md`](fase03-dataset/175-limite-tls-handshake-failure-ratio.md) | Variable no observable |
| F3 · dataset | [`fase03-dataset/181-correccion-catalogo-auditoria-y-gates.md`](fase03-dataset/181-correccion-catalogo-auditoria-y-gates.md) | Datasheet |
| F4 · modelado | [`fase04-modelado/01-protocolo-modelado-F1-v2.md`](fase04-modelado/01-protocolo-modelado-F1-v2.md) | Protocolo de modelado |
| F4 · modelado | [`fase04-modelado/04-protocolo-modelado-multilayer-v2-y-hoja-de-ruta.md`](fase04-modelado/04-protocolo-modelado-multilayer-v2-y-hoja-de-ruta.md) | Diseño del motor |
| F4 · modelado | [`fase04-modelado/06-modelo-final-congelado-ocsvm.md`](fase04-modelado/06-modelo-final-congelado-ocsvm.md) | CLAIM-002 (143/161) |
| F4 · modelado | [`fase04-modelado/07-metricas-clasificacion-comparacion-7-modelos.md`](fase04-modelado/07-metricas-clasificacion-comparacion-7-modelos.md) | CLAIM-001 (ROC-AUC 0,9741), comparación de 7 candidatos |
| F4 · modelado | [`fase04-modelado/07-ablacion-multicapa.md`](fase04-modelado/07-ablacion-multicapa.md) | CLAIM-009 (66,5 % → 88,8 %) |
| F4 · modelado | [`fase04-modelado/08-significancia-entre-modelos.md`](fase04-modelado/08-significancia-entre-modelos.md) | CLAIM-010 (McNemar + Holm) |
| F4 · modelado | [`fase04-modelado/09-validacion-cruzada-y-estabilidad.md`](fase04-modelado/09-validacion-cruzada-y-estabilidad.md) | CLAIM-003, 007, 008 |
| F7 · validación | [`fase07-validacion-final/02-resultados-f6.md`](fase07-validacion-final/02-resultados-f6.md) | CLAIM-004, 005, 006 (F6) |

Los enlaces internos de estos informes apuntan a la estructura antigua y pueden no
resolver; su contenido y sus cifras son los originales. Del mismo modo, cuando un
entregable antiguo de `03-entregables/` cita `docs/faseXX-…/fichero.md`, el fichero
correspondiente —si es uno de los anteriores— está en esta carpeta como
`faseXX-…/fichero.md`.
