# Apuntes — Aprendizaje del modelo y reentrenamiento (para la metodología)

**Fecha:** 2026-10-18 · Base: código real de `producto-main` verificado en el Sensor.

---

## 0. El concepto que no hay que equivocar

CyberFlow usa **aprendizaje NO supervisado**. El modelo (Isolation Forest) aprende
**solo de tráfico normal** y marca lo que se desvía; **no se entrena con ataques
etiquetados**. Por eso detecta comportamientos que nunca vio (sin firma).

Lo "supervisado" **no es el modelo, es la decisión humana de reentrenar**: un candidato
nunca se despliega solo; una persona lo promueve. En el panel esto se llamaba
"aprendizaje supervisado" y **se corrigió a "Reentrenamiento con aprobación humana"**
(corrección de la revisión). **No escribir "aprendizaje supervisado" en la tesis** — es
el mismo error ya corregido. Correcto: **modelo no supervisado + reentrenamiento con
aprobación humana (human-in-the-loop)**.

---

## 1. Cómo funciona el aprendizaje (ciclo completo)

1. **Acumulación** (`cyberflow_aprendizaje.py`, nocturno): mientras el motor opera, un
   temporizador escribe cada 10 min filas de línea base (esquema v3) con la misma cadena
   del motor. Es la materia prima.
2. **Saneo / anti-envenenamiento:** cada IP que el motor marcó (ALERT/LIMIT/BLOCK) queda
   señalada → sus ventanas **no entran** al entrenamiento (`eligible_training=false`).
   Además, los tramos declarados en `excluir_ventanas` se excluyen (p.ej. la ráfaga Kali
   del 27-sep). Esto protege contra el envenenamiento lento de datos.
3. **Partición con guarda** (`particionar_linea_base.py`): train / validation / test.
4. **Entrenar candidato** (`entrenar_preliminar.py`): IF sobre `train`; el **umbral se
   fija en `validation`** (percentil α=0.05), **nunca viendo test ni los ataques**.
   FPR sobre test = descriptivo.
5. **Deriva:** se mide PSI; si la señal se sostiene 3 días, adelanta el reentrenamiento
   (cadencia normal 30 días). **La deriva nunca cambia el modelo por sí sola.**
6. **Promoción con aprobación humana** (`promover_preliminar.py`): convierte el paquete
   en el artefacto que carga el motor (Pipeline), **verifica** orden de variables, offset,
   equivalencia de decisiones y hashes, y **se niega a sobrescribir**. Solo un operador
   la ejecuta. El `.toml` sección `[reentrenamiento]` define la política.

---

## 2. Cómo se VALIDA el reentrenamiento

El objetivo de la validación no es "el modelo aprendió los ataques" (no los aprende),
sino que **el mecanismo es seguro, reproducible y nunca despliega solo**. Procedimiento:
`producto-main\docs\RUNBOOK-REENTRENAMIENTO-DEMO.md` ("ensayo en seco").

| Paso | Qué demuestra |
|---|---|
| Construir candidato (train→umbral en validation) | el modelo se entrena sin ver test ni ataques |
| Puntuar ANTES y DESPUÉS sobre el **mismo hold-out independiente** (normal externo→FPR; ataques externos→TPR) | comparación justa, sin reutilizar datos de ajuste |
| `comparar_reentrenamiento.py` (candado de comparabilidad) | si los conjuntos no casan (hash/esquema) → **"EVALUACIÓN INCOMPLETA — NO PROMOVER"** |
| Criterio: FPR≤ actual **y** TPR≥ actual en pares válidos | solo entonces → **"candidato a revisión manual"**, nunca despliegue automático |
| Aprobación humana (`promover_preliminar.py`) | la "decisión supervisada" real; nada llega a producción solo |

### Evidencia que YA existe (no hay que inventar)
- **Pipeline E2E (sintético):** `tests/test_retraining_demo.py` — partición, entrenamiento,
  puntuación de ambos formatos y **rechazo de pares sin match**. *(Sus cifras NO van a la tesis.)*
- **Determinismo / estabilidad / significancia:** `recongelar/results/ablacion/`
  (`determinismo.json`, `validacion-cruzada-estabilidad.json`, `significancia-modelos.json`).
- **Corrida real de hoy (18-oct):** reproduje el informe ANTES real del Sensor
  (`ensayo-if-v2.json`: FPR 0.044527, umbral decision_function −0.06889178…) **al 6.º
  decimal**, y medí el efecto de quitar la contaminación → ΔFPR +0.07 pp, detección
  idéntica. Es una ejecución real de los pasos 1–3 del ensayo.
  Ver `ensayo-contaminacion-kali-contaminado-vs-limpio.md`.

---

## 3. Qué está implementado y qué falta

**Implementado y verificado (código):**
- `cyberflow_aprendizaje.py` (acumulación, saneo, deriva, candidato) ✅
- `entrenar_preliminar.py` / `particionar_linea_base.py` ✅
- `promover_preliminar.py` (promoción con verificación de equivalencia + hashes) ✅
- `comparar_reentrenamiento.py` (candado de comparabilidad + veredicto) ✅
- `test_retraining_demo.py` (E2E sintético) ✅
- Panel: vista "Reentrenamiento con aprobación humana" + endpoint `/api/aprendizaje` ✅

**Falta (menor, de evidencia, no de código):**
- [ ] **Una corrida real documentada** del ensayo en seco con **dos CSV externos nuevos**
  (normal y ataques) no usados para ajustar — hoy el `comparar` da "incompleto" si no se le
  dan esos pares. La corrida de contaminación de hoy cubre FPR pareado; faltaría el par de
  **ataques externo** para un veredicto de promoción completo. (Prerrequisito: reservar
  esos 2 CSV; se puede hacer tras cerrar el piloto.)
- [ ] **F6 — narrativa de α=0.05:** unificar la contradicción del FPR de operación
  (22,97–25,81 % con otro modelo/escenario) vs el 4,45 %; añadir 2–3 referencias. (Redacción.)
- [ ] **F5 — tabla de los 7 modelos** para el artículo: el material ya está calculado en
  `recongelar/artifacts/model/` + `results/ablacion/`; falta volcarlo a la tabla del artículo.

---

## 4. Hallazgo en la GUI (corregido el 18-oct)

El encabezado ya decía "Reentrenamiento con aprobación humana", pero **el mapa y los
detalles seguían diciendo "SUPERVISADO / aprendizaje supervisado"** (el mislabel que la
revisión pidió quitar). Corregido en 4 sitios visibles de `dashboard.py` y desplegado:
- nodo del mapa (`tag`), banda del mapa (`txt`), título del flujo de detalle (`flujoTit`),
  y la descripción del inventario `scripts/modeling/`.

---

## Frase lista para la metodología

> CyberFlow emplea **detección no supervisada** (Isolation Forest entrenado solo con
> tráfico normal). El reentrenamiento es **periódico y con aprobación humana**: un
> candidato se entrena en un entorno aislado, se compara contra el modelo vigente sobre un
> conjunto de validación independiente bajo un criterio que exige FPR ≤ y TPR ≥ a los
> actuales, y **únicamente un operador puede promoverlo**; no existe despliegue automático.
> El tráfico sospechoso se excluye del entrenamiento (`eligible_training`, `excluir_ventanas`)
> como defensa frente al envenenamiento de datos.
