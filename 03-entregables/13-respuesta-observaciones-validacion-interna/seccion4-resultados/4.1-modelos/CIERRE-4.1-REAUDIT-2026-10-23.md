# 4.1 — Re-audit (4 puntos del compañero), 2026-10-23

Evidencia ejecutada en `../_campana/resultados-2026-10-23/eval41/v2/`. Modelo congelado
`if_limpio_2026_10`. Versiones: python 3.14.4, numpy 2.5.1, scipy 1.18.0, sklearn 1.9.0, joblib 1.5.3.

---
## PUNTO 1 — Validación, umbral operativo y sensibilidad de α (RECONCILIADO)

**Hallazgo:** el umbral operativo `−0,5693969936322356` se reproduce **exactamente** con el cuantil
α=0,05 (numpy lineal, alerta `score_samples < umbral`) sobre la **validación COMPLETA (65 633)** —
`delta = 0,0`. Mi `ALFA-F6` previo usó 65 553 (excluyendo entidad Kali) → `−0,5694578968…`
(`delta −6,1e-5`). **La diferencia de 80 ventanas es la causa.**

| Conjunto | n | Filtro | α | Umbral | Relación con operativo |
|---|---:|---|---|---|---|
| **Validación original** | **65 633** | `particion=validation` (tal cual) | 0,05 | **−0,5693969936322356** | **lo reproduce exacto** |
| Validación depurada | 65 553 | `particion=validation` y entidad ≠ 10.10.20.30 | 0,05 | −0,5694578968203694 | complementaria (−6,1e-5) |

**A/C — Qué calibró el modelo:** la calibración original usó la **validación completa, que incluye 80
ventanas de entidad Kali (10.10.20.30)** del 28-sep. De esas 80, **solo 17 tienen actividad** (contadores
> 0); 63 están quietas (0 paquetes). Es una **desviación declarable**: "validación = normal" incluyó 80
ventanas de una entidad atacante (en su mayoría inactivas). Efecto en el umbral: ~6e-5 (despreciable),
pero **se declara, no se corrige el despliegue aquí**. CSV completo: `p1-80-ventanas-kali-validacion.csv`.

**D/E/F — ALFA-F6 corregido** (ver `ALFA-F6.md` reescrito) usa la **validación original (65 633)** como
principal (reproduce el operativo) y deja la depurada como complementaria:

| α | Umbral | FPR obs (test) | Recall | Precisión | F1 |
|---:|---:|---:|---:|---:|---:|
| 0,01 | −0,622374 | 0,87 % | 59,52 % | 8,10 % | 0,143 |
| 0,025 | −0,595253 | 2,18 % | 63,10 % | 3,59 % | 0,068 |
| **0,05** | **−0,569397** | **4,53 %** | **64,29 %** | 1,79 % | 0,035 |
| 0,10 | −0,536932 | 9,33 % | 70,24 % | 0,96 % | 0,019 |

α=0,05 **no se re-elige** mirando test: es la configuración congelada; esto es sensibilidad.

---
## PUNTO 2 — Respaldo de scores auditable (RECALCULADO / CONSERVADO)

- **Canónico (sin pérdida): `scores-todos-candidatos-full.csv.gz`** — SHA-256
  `6e98219fb79a187b7256e664a4791a0619be70a68d9a23eee1e61c45de98ffc8`, **65 505 filas** (idx único,
  entity_ip, window_end_utc, label, familia_proxy + score de los 9), **0 no-finitos**, scores a
  `%.17g` (precisión completa).
- **Reproducción desde el respaldo:** recalculadas TP/FP/TN/FN/precisión/recall/F1/especificidad/FPR/
  ROC-AUC/AP de los 9 → **coinciden con `metricas.json` y TABLA6/7** (`p2-reproduccion.json`).
- **Efecto del redondeo (prompt 2C):** el gz previo a **6 decimales alteraba el ROC-AUC del OCSVM**
  (0,4799 vs 0,4555 real) por degeneración de sus scores (empates). Por eso el canónico es el
  **full**; el de 6 decimales queda **superado** (no usar para métricas de ranking).
- **Versión canónica:** `eval41/v2/` (NO el primer pase `eval41/`). Respaldo durable también en el
  sensor `artifacts/eval-4.1-2026-10-23/`. Hashes de modelos verificados vs `model_hashes` (candidatos
  coinciden; limpio/contaminado con sus manifiestos) en `run-manifest.json` / `hashes-deps-aux.json`.

---
## PUNTO 3 — Ventanas con `packet_count_10s = 0` (AUDITADO)

`packet_count_10s` existe en las 65 421 (0 vacías, 0 no-numéricas, **45 558 cero real** — no es un
default que enmascare un campo ausente). Estratificación (evaluación principal intacta; esto es
complementario, **no se eliminan filas**):

| Categoría | n | FP del IF | TN | FPR |
|---|---:|---:|---:|---:|
| Con paquetes en 10 s | 19 863 | 2 837 | 17 026 | **14,28 %** |
| 0 pkts/10 s con actividad retrospectiva (30/60 s) | 12 208 | 124 | 12 084 | 1,02 % |
| 0 pkts/10 s sin actividad observable | 33 350 | **0** | 33 350 | **0 %** |
| **Total** | **65 421** | **2 961** | 62 460 | 4,53 % |

**Lecturas (declaradas):**
- El **FPR global 4,53 % se diluye** por 45 558 ventanas casi vacías (0 FP las 33 350 sin actividad).
  **Entre ventanas con paquetes, el FPR del modelo es 14,28 %.** Cambia la composición/prevalencia →
  se presenta como **análisis complementario**, no como el mismo experimento.
- **Offline vs motor en vivo (prompt 3E):** el motor **en vivo marca PERMIT** las ventanas sin paquetes
  (heurístico `no_live_packets`) y **no puntúa el modelo**; el evaluador **offline sí** las puntúa. 124
  de los 2 961 FP offline (4,2 %) caen en ventanas con 0 paquetes → en operación serían PERMIT. La
  **decisión del motor ≠ clasificador IF ≠ híbrido completo**: aquí se reporta el **clasificador IF**.

---
## PUNTO 4 — Conclusiones y etiquetas corregidas

- **A. Limpio vs anterior:** se RETIRA "son equivalentes / ruido de muestra / no hubo degradación". La
  afirmación respaldada es: **"Ambos detectaron 54/84; difirieron en FP, ROC-AUC y AP"** (limpio
  ROC-AUC 0,9247/AP 0,1858/FPR 4,53 %; contaminado 0,9228/0,2026/4,45 %). McNemar pareado
  (**descriptivo**, ventanas dependientes): vs contaminado **b=179 / c=227** (discordantes),
  p ≈ 0,02 — **no se afirma superioridad estadística**; "p=0" frente a los de laboratorio se reporta como
  **p < 1e-16**, no cero literal. Mismo recall **no** demuestra equivalencia estadística.
- **B. α:** no se llama "óptimo" ni "punto de equilibrio". Se describe el **compromiso observado**
  detección↔falsas alarmas (tabla α). La sensibilidad posterior **no** convierte la elección original en
  optimizada de antemano; no había meta de aceptación pre-definida más allá del objetivo de ~5 % de FPR.
- **C. Familias:** etiqueta por **contadores observables** (HTTP/DNS/resto=escaneo). Identifica
  actividad, **no confirma el tipo de ataque**; "escaneo" es **residual**. No hay marcas de campaña por
  ventana (nota M declara que la asignación no quedó registrada) → se mantiene **aproximada/auxiliar**;
  **no** se presenta "resto" como escaneo confirmado ni sus % como sensibilidad confirmada por ataque.
- **D. Precisión baja:** recall 54/84; **precisión 54/(54+2961)=1,79 %**; las 2 961 son normales mal
  señaladas. El desbalance contribuye pero **no justifica** el costo de falsas alarmas; **ROC-AUC alta no
  garantiza buen punto de operación**; **LIMIT reversible también afecta tráfico legítimo**. No se oculta
  precisión/F1 ni se atribuye al híbrido una mejora no medida aquí.
- **E. Transferencia/reutilización:** modelos entrenados con datos de **distinto origen** → la comparación
  mide **transferencia**, no superioridad intrínseca del algoritmo. El conjunto 84+65 421 **se reutilizó
  para decisiones de desarrollo (14-oct)** → no es test ciego; un test independiente es **limitación
  futura** (no existe aún).

### Matriz de afirmaciones permitidas (reemplaza la del ESQUEMA en lo que toca)
| Afirmación permitida | Evidencia | Limitación |
|---|---|---|
| IF limpio: recall 54/84 (64,3 %), FPR 4,53 %, ROC-AUC 0,925, AP 0,186 | Tabla 6 / metricas.json | eval reutilizada; anomalía por ventana; FPR incluye 45 558 ventanas casi vacías |
| Limpio y contaminado **detectaron ambos 54/84**; difieren en FP/ROC-AUC/AP | Tabla 7, McNemar | **no** "equivalentes" ni superioridad; descriptivo (ventanas dependientes) |
| El IF de esta red **transfiere** mejor que los de laboratorio (FPR 29–99,6 %) | Tabla 7 | transferencia, no superioridad intrínseca; eval reutilizada |
| Entre ventanas **con paquetes**, FPR del IF = 14,28 % | P3 | composición/prevalencia distinta; complementario |
| α compromete detección↔FPR (tabla α) | ALFA-F6 (val 65 633) | no "óptimo"; calibrado en esta red; sin meta previa |
| Familias por contadores (HTTP/DNS/escaneo) | per-familia proxy | aproximado; "escaneo" residual; no confirmado por ataque |

---
## Cambios necesarios en el Word (correspondencia 3.3.3–3.3.7, 3.6, Tablas 3/5 ↔ 4.1)
1. **Resumen + palabras clave + introducción/contribuciones:** dicen **"One-Class SVM"**; el modelo
   operativo y evaluado es **Isolation Forest limpio**. Propagar OCSVM→IF (dejando OCSVM como candidato
   comparado en Tabla 7). *(3.3.7 ya dice "el IF"; abstract/keywords no.)*
2. **Declarar** que el conjunto de evaluación (84+65 421) **se reutilizó** para la selección de modelo
   (transferencia, no test ciego).
3. **α=0,05:** describirla como criterio de calibración con su **compromiso** (no "óptimo"); citar la
   sensibilidad como análisis, no como selección.
4. **Familias:** declarar etiqueta **observable/aproximada** (nota M), "escaneo" residual.
5. **Validación:** nota de que la validación de calibración **incluyó 80 ventanas de entidad Kali**
   (17 con actividad) — desviación menor del criterio "normal"; efecto ~6e-5 en el umbral.
6. **3.3.3–3.3.6 / Tablas 3 y 5:** verificar contra esta lista (pendiente de abrir esas secciones en el
   Word; 3.3.7 y 3.6 ya contrastadas y coherentes — ver `COHERENCIA-ARTICULO-3.3.7-3.6.md`).

---
## Cierre (por estado)
- **VERIFICADO:** umbral operativo = cuantil α=0,05 sobre validación 65 633 (delta 0,0); respaldo full
  reproduce todas las métricas; hashes de modelos vs manifiesto; `packet_count_10s` real (no default).
- **CORREGIDO:** ALFA-F6 (val original); retirados "equivalentes/ruido/no degradación"; "p=0"→"p<1e-16";
  α no "óptimo"; familias=aproximadas; respaldo canónico = full (6-dec superado).
- **RECALCULADO:** α en ambos conjuntos; métricas de los 9 desde el respaldo; FPR estratificado por P3.
- **PUBLICADO O CONSERVADO:** respaldo full + artefactos en `eval41/v2/` (repo) y en el sensor
  `artifacts/eval-4.1-2026-10-23/`; pendiente el **push** de Mark.
- **PENDIENTE (limitaciones que permanecen):** (a) **test ciego independiente** (eval reutilizada) —
  exige captura de ataque nueva; (b) **Suricata ET Open** sobre el mismo PCAP (VM comparadora
  10.10.60.13, sin acceso mío) para 4.3; (c) etiquetas de familia **confirmadas** por marcas de campaña;
  (d) cross-check fino de **3.3.3–3.3.6 y Tablas 3/5** contra el Word.

**4.1 lista para redactar** con esta matriz de afirmaciones y sus limitaciones; lo pendiente son
limitaciones declaradas, no cálculos faltantes del IF.
</content>
