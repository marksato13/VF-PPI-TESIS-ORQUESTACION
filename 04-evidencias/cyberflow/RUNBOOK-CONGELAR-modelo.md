# Runbook — congelar el modelo recalibrado (→ `calibrado=true` → `v1.0.0`)

**Estado:** planificado, **no ejecutado**. Toca el **modelo vivo** de producción
(sensor1) → coordinar con el fin del piloto. Es el único paso que falta para `v1.0.0`.

## 0. Decisión de modelo

Usar el **IsolationForest recalibrado** del ensayo (`artifacts/preliminar/ensayo-if-v2.joblib`).
Razones: (a) tiene las cifras medidas — FPR **4,45 %** (nota `L`), TPR **69 % global /
100 % HTTP** (nota `M`); (b) **alinea** con el manifiesto, que declara
`if_primary_weighted` (IsolationForest) como conclusión principal, resolviendo de
paso la discrepancia «manifiesto declara IF pero el motor corre OCSVM».

## 1. Dos incompatibilidades a resolver ANTES de desplegar

El motor (`scripts/engine/motor_decision.py`) espera:

1. **Un objeto con `.score_samples(X_crudo)`** — es decir, un `sklearn.pipeline.Pipeline`
   que primero escala y luego puntúa. El `ensayo-if-v2.joblib` es un **dict**
   (`modelo` + `escalador` sueltos): **no** sirve tal cual.
2. **Un umbral en espacio `score_samples`**, leído del `manifest.json`. El umbral del
   ensayo (`-0,068892`) está en espacio `decision_function`
   (`score_samples = decision_function + offset_`): **hay que recalcularlo**.

## 2. Producir el artefacto congelado (NO invasivo: escribe en un candidato)

> **✅ HECHO (30-sep).** Candidato construido en el sensor1, sin tocar producción:
> - Artefacto: `artifacts/preliminar/if_recalibrado_desplegable.joblib`
>   (`Pipeline([scaler, IsolationForest])`, con `.score_samples` sobre crudo).
>   `sha256 = d27f68711fcb0f6657611bd7feb17759bc4fae36b9e61fbd5ca8d1190128125a`.
> - **Umbral convertido a `score_samples` = -0,568892** (= `decision_function` -0,068892
>   + `offset_` -0,5). Verificado: detecta **las mismas 54 ventanas** que en la nota `M`.
> - Fragmento de manifiesto: `artifacts/preliminar/manifest-if-recalibrado.json`
>   (detector `if_recalibrado_2026_09`).
> - Deja para el paso 3 (sudo) solo apuntar el servicio a este artefacto.
>
> **Nota metodológica:** el TPR *global* es sensible al nº de ventanas-cola de baja
> señal que se cuenten (bajó de 0,69 a 0,635 al crecer el denominador de 78→85
> ventanas, con las **mismas 54 detecciones**). Las cifras robustas para la tesis
> son **por categoría** (HTTP 100 %, escaneo ~63 %, DNS 0 %) y el conteo de
> detecciones fuertes, no el global suelto.

Receta usada (referencia, ya ejecutada):

Guion a ejecutar en el sensor con el venv (`.venv/bin/python`), escribiendo en
`artifacts/model/candidates/` — **sin tocar el modelo desplegado**:

1. Reconstruir el pipeline con los objetos ya ajustados del ensayo:
   `Pipeline([("scaler", escalador), ("model", modelo)])` (ambos ya `fit`).
2. Recalcular el umbral en `score_samples`:
   - Re-particionar la línea base (`particionar_linea_base.py --solo-elegibles`).
   - `umbral = quantile(pipeline.score_samples(X_validation), alpha=0,05)`.
3. **Verificar** antes de aceptar:
   - `FPR(test) = mean(score_samples(test) < umbral)` ≈ **0,045**.
   - `TPR(kali) = mean(score_samples(ventanas_10.10.20.30_30sep) < umbral)` ≈ **0,69**
     (100 % en HTTP) — reproduce la nota `M` con la nueva forma.
4. `joblib.dump(pipeline, artifacts/model/candidates/if_recalibrado_2026-09.joblib)`.
5. Escribir/añadir en `artifacts/model/manifest.json` el detector nuevo:
   ```
   "detectors": { "if_recalibrado_2026_09": {
       "comparison": "score < threshold",
       "calibration": { "threshold": <umbral score_samples> },
       ... (features, runtime.python=3.14.4, alpha, sha256) } }
   ```

## 3. Desplegar (requiere `sudo` de Mark)

1. **Respaldar** el actual: `cp artifacts/model/ocsvm_scaled.joblib artifacts/model/ocsvm_scaled.joblib.pre-congelar`.
2. Apuntar el servicio al modelo nuevo: en `configs/cyberflow.local.toml`
   `[rutas] modelo = "artifacts/model/candidates/if_recalibrado_2026-09.joblib"`,
   y el motor con `--detector-name if_recalibrado_2026_09` (regenerar unidad con
   `cyberflow_config.py --escribir`).
3. `[motor] calibrado_en_esta_red = true`.
4. `sudo systemctl daemon-reload && sudo systemctl restart ppi-motor`.

## 4. Verificar

- `bash scripts/setup/doctor.sh` → §7 debe pasar de «SIN calibrar» a calibrado.
- Revisar `logs/motor_decision.log`: los `detector_name` deben ser el nuevo y los
  scores/umbral coherentes; los PERMIT/ALERT deben tener sentido (no volver al 92 %).
- (Opcional) un mini re-score de control de unas ventanas normales recientes.

## 5. Rollback

Si algo va mal: restaurar `ocsvm_scaled.joblib.pre-congelar`, volver
`calibrado=false`, `--detector-name ocsvm_scaled`, `daemon-reload` + `restart`.

## 6. Coordinación

- No congelar durante una ventana de piloto legítimo activa. La fase de ataque ya
  se hizo (nota `M`), así que el piloto ya cumplió su función; confirmar con Mark
  que se puede cambiar el modelo vivo.
- Tras congelar y verificar → **etiquetar `v1.0.0`** (P2) y, si se quiere, DOI
  Zenodo (`.zenodo.json` ya está).

## 7. Pendiente honesto que NO bloquea v1.0.0

- DNS-entropy 0 % (nota `M`): el ataque apuntó al DMZ, no al resolver real; y aun
  así es señal débil. Documentar como **limitación** (junto al ARP spoof L2), no
  intentar taparlo forzando el umbral.
