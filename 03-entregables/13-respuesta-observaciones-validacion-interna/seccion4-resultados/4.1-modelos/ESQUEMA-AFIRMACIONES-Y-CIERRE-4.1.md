# 4.1 — Esquema de afirmaciones permitidas y cierre (re-audit v2, 2026-10-23)

Evidencia dura en `../_campana/resultados-2026-10-23/eval41/v2/` (metricas.json sin redondear,
TABLA6/7 md+csv, ALFA-F6 md+csv, figura ROC/PR v2 png+svg, scores de los 9 candidatos, run-manifest).
Modelo operativo `if_limpio_2026_10` (203 967 ventanas normales de entrenamiento). Corte de repos:
`producto-main fa9e5b0`, `orquestacion-limpio` (este commit). Versiones: python 3.14.4, numpy 2.5.1,
scipy 1.18.0, sklearn 1.9.0, joblib 1.5.3.

## Esquema de afirmaciones permitidas (Afirmación | Respaldo | Limitación)

| Afirmación | Resultado que la respalda | Limitación obligatoria |
|---|---|---|
| El IF limpio detecta **54/84 (64,3 %)** de las ventanas de ataque con **FPR 4,53 %** en esta red. | Tabla 6 (TP54/FP2961/TN62460/FN30; ROC-AUC 0,925; AP 0,186). | **Evaluación reutilizada** (este set ya eligió modelo el 14-oct), no test ciego nuevo; **anomalía por ventana, no ataque confirmado**; el FPR offline incluye 45 558 ventanas vacías; es FPR del modelo solo, no del sistema ni impacto operativo. |
| **Limpio y contaminado detectaron ambos 54/84; difirieron en FP, ROC-AUC y AP.** | Tabla 7 + McNemar (descriptivo). | **No** afirmar "equivalentes", "ruido de muestra" ni superioridad: el contaminado tiene **AP 0,203 > 0,186** y **FPR 4,45 % < 4,53 %**; el limpio **ROC-AUC 0,925 > 0,923**. Mismo recall ≠ equivalencia estadística. Ver `CIERRE-4.1-REAUDIT-2026-10-23.md` (autoritativo). |
| El IF entrenado en **esta red** transfiere mejor que los candidatos de laboratorio. | Tabla 7: candidatos lab con FPR 29–99,6 % y ROC-AUC ≤ 0,83; OCSVM ROC-AUC 0,455 (bajo el azar, marca 99,6 % del normal). | Mide **transferencia** al entorno objetivo (datos de entrenamiento distintos), **no** superioridad intrínseca del algoritmo IF; comparación reutilizada. |
| El modelo es **débil en DNS** (0/8). | Per-familia proxy (Tabla 6). | Etiqueta **proxy observable** (no ground-truth); montaje de nota M apuntó al DMZ, no al resolver; ese hueco lo cubre el **heurístico** `dns_entropy` (eso es **4.2**, no 4.1). |
| α = 0,05 da **FPR ≈ 4,5 %** y es un *knee* razonable del compromiso FPR–recall. | ALFA-F6 (cortes en validación aplicados a test: α 0,01→FPR 0,87 %/recall 59,5 %; 0,05→4,52 %/64,3 %; 0,10→9,31 %/70,2 %). | Calibrado en validación de **esta** red; la literatura sustenta el **procedimiento**, no que 0,05 sea óptimo; **no había meta de aceptación pre-definida** (no se inventa post-hoc). |

### Afirmaciones NO permitidas
- "El IF limpio gana en todas las métricas" (falso: AP y FPR favorecen al contaminado).
- "Estadísticamente superior" (no se recalculó McNemar con estas predicciones; ver pendiente).
- Confundir **IF solo** con el **híbrido** (el híbrido es 4.2); **resultado actual** con el **histórico**;
  **ventana** con **episodio**; **FPR offline** con **impacto operativo**; o extrapolar a **otra red**.

## Precisión baja (1,79 %) — explicación sin minimizar
Precisión = 54/3015 = 1,79 %. Con **prevalencia 0,128 %** (84 ataques entre 65 505 ventanas), un FPR de
4,53 % genera **2 961 falsos positivos** frente a 54 verdaderos → la precisión es baja **por construcción**.
ROC-AUC alta (0,925) mide *ranking*, **no** garantiza un punto de operación con buena precisión. El LIMIT es
reversible pero **también afecta tráfico legítimo** mientras está activo. No se declara "aceptable" por el
desbalance ni porque el modelo dé LIMIT y no BLOCK: se declara el costo y que el sistema completo (heurísticos
+ revisión humana + caducidad) es lo que acota el impacto — y eso se mide en 4.2/4.4, no aquí.

## Coherencia con el artículo (3.3.7 y 3.6) — a verificar con el Word
Cambios metodológicos que **deben declararse** (no reescribir como si fueran planificados):
1. Modelo desplegado: OCSVM → IF recalibrado → **IF limpio** (exclusión de 181 ventanas Kali del 27-sep).
2. El conjunto 84+65 421 es una **evaluación reutilizada** (eligió modelo el 14-oct); no es confirmación independiente.
3. Se **retiró** la columna "Det@FPR5%" previa (corte sobre test = fuga); la sensibilidad correcta es ALFA-F6.
**Pendiente:** contrastar el texto real de 3.3.7 y 3.6 contra lo ejecutado (requiere abrir el Word).

## Estado de finalización
- **VERIFICADO:** hashes de artefactos (candidatos coinciden con `model_hashes`; limpio/contaminado con sus manifiestos), orden de las 28 variables, escalador único (Pipeline), `score_samples` sin fallback, umbral del manifiesto a precisión completa, chequeos de suma (84/65 421/65 505).
- **EJECUTADO:** 9 configuraciones puntuadas sobre las mismas 84+65 421; Tabla 6, Tabla 7, ALFA-F6, figura a resolución completa.
- **CORREGIDO:** Det@FPR5% retirada (fuga); umbral del contaminado corregido; `IF uniform ≡ IF exact` señalado; "no gana en todo" (AP/FPR favorecen al contaminado); familia marcada como proxy; evaluación declarada **reutilizada**; 45 558 ventanas vacías declaradas.
- **ENTREGADO Y PUBLICADO:** tablas md+csv, `metricas.json` (sin redondear), **scores de los 9 candidatos** (`scores-todos-candidatos.csv.gz`, 65 505 filas), run-manifest con hashes/versiones, figura png+svg, scripts (`eval_41_v2.py`, `construir_41_v2.py`). Respaldo durable duplicado en el sensor `artifacts/eval-4.1-2026-10-23/`. (Queda "publicado" al hacer el push.)
- **McNemar+Holm (HECHO, `SIGNIFICANCIA-McNemar.md`):** vs candidatos de laboratorio/OCSVM/LOF/EE, p_Holm≈0 (el limpio comete muchísimos menos FP). **vs contaminado: b=179 (limpio mejor) < c=227 (contaminado mejor), p=0,0196** → la diferencia limpio↔contaminado es mínima y **marginalmente a favor del contaminado**; **NO se afirma que el limpio sea superior**. Unidad = ventana, con **dependencia temporal** declarada → se reporta como diferencia **descriptiva** pareada, no inferencia estricta.
- **Cross-check 3.3.7/3.6 (HECHO, `COHERENCIA-ARTICULO-3.3.7-3.6.md`):** 3.3.7/3.6 **coinciden** con lo ejecutado (congelado+manifiesto+SHA, 65 421 FPR, ROC-AUC con −score, ventana vs episodio, Tabla 5). **A declarar en el artículo:** resumen/keywords aún dicen "One-Class SVM" (el modelo es IF); familia = proxy observable; Nikto aún no ejecutado (4.3); evaluación reutilizada.
- **PENDIENTE (estructural):** **Test ciego independiente** — esta evaluación es reutilizada (eligió modelo el 14-oct); cerrarlo exige una captura de ataque nueva no vista. No se puede resolver sin re-correr una batería sobre tráfico de ataque fresco.

**Veredicto:** **4.1 lista para redactar** con el esquema de afirmaciones de arriba y sus limitaciones declaradas.
Lo único que condicionaría una afirmación concreta del texto es (a) si se quiere "superioridad estadística"
(entonces falta McNemar) y (b) la alineación fina con 3.3.7/3.6.
</content>
