# F5 — Comparación de modelos (7 candidatos + OCSVM→IF), lista para el artículo

> **Superado para el artículo (2026-10-25).** La comparación entre algoritmos con los mismos datos del sensor está en
> `seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25/`. Esta tabla (candidatos históricos congelados,
> OCSVM entrenado en laboratorio) se conserva como registro de la decisión OCSVM→IF.

**Fecha:** 2026-10-18 · **Observación F5:** presentar la tabla de los 7 modelos y la de
reemplazo OCSVM→IF. **Decidido:** las métricas ya estaban calculadas (re-ejecución en
`recongelar/`, entorno congelado py3.14.4/sklearn1.9.0); aquí se vuelcan.

> **Actualización 2026-10-19 — el modelo desplegado SÍ cambió.** El operativo es ahora
> `if_limpio_2026_10` (181 ventanas Kali excluidas del train; ver la model card). Efecto en
> esta tabla: la fila del IF pasa a umbral `score_samples −0,569397` (= `decision_function
> −0,069397`) y **FPR test 4,53 %** (desde 4,45 %); la **detección en el umbral de operación
> es idéntica** y el ROC-AUC **equivalente** (≈0,92 sobre el conjunto que se pudo puntuar;
> la diferencia es ruido de muestra). El recálculo **exacto** de ROC-AUC/PR-AUC/Det@FPR5 %
> del limpio sobre el **oro de `recongelar/`** (84 ataques + 65 421 normal) queda **pendiente**
> (requiere puntuar el limpio en el Sensor); no se esperan cambios materiales: contaminado y
> limpio difieren en 181 de 204 148 ventanas de train. La **comparación de arquitecturas
> (Tabla 1) sigue válida tal cual**: no depende de qué variante del IF se despliegue.
> Evidencia de equivalencia (mismo set, 65 421 normal + 179 Kali): ROC-AUC 0,913 (contaminado)
> vs 0,919 (limpio); detección 81/179 en ambos; ΔFPR +0,07 pp.

**Fuentes (auditables):** `compare_frozen_models_metrics.py` (métricas de los 7),
`significancia_modelos.py` → `recongelar/results/ablacion/significancia-modelos.json`
(McNemar+Holm), `recongelar/artifacts/model/candidates/*.joblib` (los 7 congelados),
model card del IF, y la ficha de cambio OCSVM→IF (`02-metodologia/trazabilidad/`).

---

## Tabla 1 — Los 7 candidatos sobre ESTA red

Conjunto de evaluación: **84 ventanas de ataque (Kali) + 65 421 ventanas normales** del
conjunto de oro (prevalencia 0,13 %). Cada `joblib` se carga congelado, sin reentrenar.
Dos lecturas: **FPR** con el umbral propio de cada modelo (mide si *transfiere* a esta
red); **Det. @ FPR 5 %** recalibrando todos al mismo 5 % de FPR (compara solo la
arquitectura, a igualdad de falsos positivos). ROC-AUC y PR-AUC son de ranking (robustas
al desbalance).

| Modelo | ROC-AUC | PR-AUC | FPR (umbral propio) | Det. @ FPR 5 % |
|---|---:|---:|---:|---:|
| **Isolation Forest recalibrado (desplegado)** | **0,923** | **0,203** | **4,45 %** | **66,7 %** |
| IF scaled (laboratorio) | 0,825 | 0,004 | 30,3 % | 16,7 % |
| IF primary (laboratorio) | 0,828 | 0,004 | 29,1 % | 16,7 % |
| IF uniform (laboratorio) | 0,796 | 0,005 | 34,1 % | 16,7 % |
| OCSVM *(ganó en laboratorio)* | 0,456 | 0,001 | 99,6 % | 0,0 % |
| LOF (laboratorio) | 0,299 | 0,001 | 76,8 % | 0,0 % |
| Elliptic Envelope (laboratorio) | 0,344 | 0,001 | 86,9 % | 6,0 % |

**Lectura:** el **IF recalibrado gana en todas las métricas robustas al desbalance**. A
igualdad de FPR (5 %) detecta 66,7 % frente al 16,7 % del mejor de laboratorio; el OCSVM
—ganador en el banco— cae a ROC-AUC 0,456 (por debajo del azar) y marca el 99,6 % del
tráfico normal como anomalía: **inservible en esta red**. La diferencia del IF frente a
**OCSVM y LOF es significativa** (McNemar + corrección Holm, **p < 0,001**); las variantes
de IF entre sí **no** son significativamente distintas (coherente con elegir la más simple).

> **Precisión y F1 no son el titular**: con prevalencia 0,13 % (miles de normales frente a
> decenas de ataques) son bajos para todos por construcción. Por eso se reportan ROC-AUC,
> PR-AUC, FPR y detección.

---

## Tabla 2 — Reemplazo OCSVM → IF en el artículo (con lo ya medido)

La versión anterior usaba OCSVM; el desplegado es el IF recalibrado. Regla: **cada cifra
del OCSVM se sustituye por la del IF con su denominador**; las que no tienen equivalente
medido se marcan o se declaran históricas de F6.

| En el artículo | Quitar (OCSVM) | Poner (IF recalibrado) + denominador | Estado |
|---|---|---|---|
| Modelo / detector | One-Class SVM | **Isolation Forest recalibrado** (`if_recalibrado_2026_09`), Pipeline escalador+IF | listo |
| Contaminación | `nu = 0,05` | percentil **α = 0,05** sobre validación | listo |
| Umbral | `1,8126` | **`score_samples < −0,568892`** (= `decision_function < −0,068892`) | listo |
| Detección global | 88,8 % (143/161) | **64,3 % = 54/84** ventanas Kali | listo |
| Detección por familia | — | **HTTP 35/43 · escaneo 19/33 · DNS 0/8** | listo |
| FPR | 4,71 % (13/276) | **4,45 % sobre test normal retenido (65 421)**. No presentar como «bajada desde 92,4 %» | listo |
| **ROC-AUC** | 0,9741 | **0,923** (IF) vs **0,456** (OCSVM) en el oro de esta red | ✅ **ahora medido** (era «a medir») |
| **Significancia (McNemar+Holm)** | 6 comparaciones del OCSVM | **IF vs OCSVM/LOF: p < 0,001**; IF-variantes entre sí n.s. | ✅ **ahora medido** (era «a medir») |
| Datos de calibración | 1 373 normal + 179 anóm. (lab) | IF sobre **337 980 ventanas** de Sensor1 (train 204 148 / val 65 633 / test 65 421) | listo |
| Variables | 28 (a veces 31) | el modelo consume **28** (contrato v2); 27/28 observables; v3 emite 31 (+L2, fuera del scoring) | listo |
| Cobertura del sistema | — | **stack híbrido 9/9** por episodio (modelo solo 6/9, heurísticos 7/9) | listo |
| FPR en operación | 25,81 % / 22,97 % | **No reutilizar** (son del OCSVM en F6). El FPR del sistema completo se mide aparte | a medir |
| Tiempo de respuesta | mediana 8,0 s (n=8) | **No trasladable** (era bloqueo local F6). Vigente, distribuida: **41,4 s** extremo a extremo (cadena 10 s) | actualizado |
| Disponibilidad | «cero caídas en 58 corridas» | **Solo de F6** (OCSVM en línea); conservar **asociada a F6**, no como disponibilidad del IF | histórico |

---

## Tabla 3 — Ablación por componentes (qué aporta cada pieza)

Sobre 9 episodios (3 familias × 3 repeticiones):

| Configuración | Episodios detectados |
|---|---:|
| Modelo solo | 6 / 9 |
| Heurísticos solos | 7 / 9 |
| **Modelo + heurísticos** | **9 / 9** |

El modelo detectó flood HTTP y escaneo pero **0/3 DNS**; el heurístico `dns_entropy` cubrió
ese hueco. **La complementariedad es el resultado medido**, no se atribuye 9/9 al modelo
solo. (Fuente: notas 31-ablación, 32-resumen; `recongelar/results/ablacion/`.)

---

## Caveats honestos (van en el artículo)

1. **Sesgo de selección declarado:** la promoción histórica del OCSVM se hizo *tras ver el
   test*. La elección del IF **no se presenta como preregistrada**; se presenta como el
   modelo que **transfiere** a la red objetivo, con criterio (FPR 5 %) fijado en validación.
2. **El 4,45 % es del modelo solo**, sobre test normal retenido — no es el FPR del sistema
   completo con heurísticos, ni una garantía de FPR continuo.
3. **No escribir «la recalibración bajó el FPR de 92,4 % a 4,45 %»**: entre ambas mediciones
   cambiaron modelo, datos y alcance; no aísla el efecto de recalibrar.

## Qué cierra esto de F5

- ✅ Tabla de 7 modelos (ROC-AUC, PR-AUC, FPR, detección) + significancia → **cierra** los
  ítems «ROC-AUC a medir» y «significancia a medir» de la ficha OCSVM→IF.
- ✅ Tabla de reemplazo OCSVM→IF actualizada.
- Queda abierto (redacción, no cómputo): **F6** (narrativa α=0.05 y el FPR de operación, que
  es OCSVM/F6 y no se reutiliza) y el **FPR del sistema completo** (a medir aparte).
