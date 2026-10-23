# Plan de implementación — Observaciones de la validación interna

**Sesión validada:** 2026-10-15 · **Plan redactado:** 2026-10-16
**Tracker de origen:** `RESPUESTA-OBSERVACIONES-validacion-interna-CyberFlow.xlsx`
(generado por `generar_respuesta_observaciones.py`, en esta misma carpeta).
**Respaldo del estado previo:**
`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\_RESPALDOS\estado-post-validacion-2026-10-16\`
(commit `6d92ff3`, tag `validacion-interna-2026-10-15`).

---

## Guardarraíl (regla que no se rompe)

**12 de 13 observaciones son documentación/consistencia. Ninguna obliga a reentrenar.**
El modelo de producción **`if_recalibrado_2026_09` (θ=-0.568892, α=0.05, FPR 0.044527)
queda byte-idéntico**; su hash de respaldo es
`d27f68711fcb0f6657611bd7feb17759bc4fae36b9e61fbd5ca8d1190128125a`.

La única tarea con cómputo (F5, re-ejecutar la comparación de modelos) **produce una
tabla nueva como evidencia del artículo; NO sustituye ni reentrena el modelo desplegado.**

## Decisiones del equipo (ya tomadas, 2026-10-16)

- **IPv6 (F4 / E3): trabajo futuro.** Se declara en limitaciones y trabajo futuro.
  No se toca el modelo congelado ni el dataset. Coherente con el alcance IPv4 defendido.
- **Comparación de modelos (F5): re-ejecutar sobre la línea base real.** Se regeneran
  las métricas de los 7 modelos sobre el tráfico real del piloto, como evidencia fresca.
  El modelo de producción no cambia (ver guardarraíl).

---

## Paquetes de trabajo

### 🅐 ALCANCE — frase canónica única (F3, E2, N2, X2, + IPv6 F4/E3) · Alta

Redactar **una sola definición de alcance** y repetirla, palabra por palabra, en los
tres soportes (artículo, presentación, panel). Borrador:

> *«CyberFlow analiza las capas de red (L3), transporte (L4) y aplicación (L7) sobre
> IPv4. Observa el tráfico de la LAN y el que va hacia Internet mediante un puerto
> espejo (SPAN); no inspecciona capa 2 ni IPv6. El sensor observa en paralelo —no en
> línea— y la respuesta (LIMIT/BLOCK) se aplica en el host protegido.»*

| Obs | Acción concreta | Dónde |
|---|---|---|
| F3 | Declarar «L3/L4/L7 sobre IPv4» en título/resumen, apartado de alcance y 1ª diapositiva | Artículo · Presentación |
| N2 | Añadir explícito «LAN + tráfico hacia Internet» a la frase de alcance | Artículo · Presentación |
| X2 | Quitar «mecanismo de control inline» del título → «observación en paralelo (SPAN), acción en el host» | Artículo · Presentación |
| E2 | Pasada de trazabilidad: verificar que los 3 soportes digan lo mismo | Artículo · Presentación · Panel |
| F4/E3 | IPv6 a limitaciones + trabajo futuro (NO se implementa) | Artículo (limitaciones) |

### 🅓 TIEMPOS — unificar y separar los tres (N3) · Alta — material ya medido

- Presentar **tres tiempos por separado**: detección, decisión y respuesta.
- **Cifras canónicas nuevas** (de `producto-main\docs\evidencias\tiempos-2026-10-15-cadena-10s.md`):
  decisión→nft **15,3 s**, escaneo→bloqueo **41,4 s**, cadena escalonada a 10 s.
- **Barrido de consistencia:** reemplazar las cifras viejas (p.ej. «51–141 s») allí donde
  aparezcan en docs y presentación. Mismas cifras en todos lados.

### 🅒 RESPUESTA / ENFORCEMENT (N1, N4)

| Obs | Acción | Dónde | Prioridad |
|---|---|---|---|
| N1 | Llevar la tabla de decisión LIMIT vs BLOCK (ya en panel #s-variables) a metodología y presentación; definir qué es LIMIT (limita tasa, no corta) | Artículo · Presentación | Alta |
| N4 | Integración con pfSense perimetral → discusión + trabajo futuro (prototipo de agente a evaluar) | Artículo (trabajo futuro) | Media |

### 🅑 MODELO Y PARÁMETROS (F5, F6, F7) · Alta

- **F5 — tabla de los 7 modelos + tabla OCSVM→IF (RE-EJECUTAR sobre línea base real).**
  - Fuente de material existente: `producto-main\artifacts\model\manifest.json` (comparación
    ago-2026) y `orquestacion-limpio\02-metodologia\trazabilidad\FICHA-CAMBIO-ARTICULO-OCSVM-A-IF.md`.
  - Utilería para el re-run: `producto-main\scripts\modeling\` →
    `train_multilayer_v2.py`, `calibrate_multilayer_v2_v1.py`, `puntuar_deteccion.py`,
    `comparar_reentrenamiento.py`.
  - **Prerrequisito a confirmar con Mark:** ubicación exacta del dataset de «línea base
    real» del piloto (el conjunto de oro citado en `modelo-vigente.json`, notas L/M) y la
    VM con el entorno congelado (Python 3.14, scikit-learn 1.9.0, seed 20260817).
  - Salida: tabla comparativa nueva para el artículo. El modelo desplegado no cambia.
- **F6 — α=0.05.** Añadir 2–3 referencias de literatura + curva/tabla de sensibilidad de α.
  **Unificar contradicción:** `02-metodologia\metodologia-7-fases\F3-modelado-hibrido.md`
  dice que en operación el FPR sube a ~23–26 %; la ficha de cambios dice que esas cifras
  son del OCSVM viejo y no se reutilizan. Dejar una sola versión: **no presentar 4,45 %
  como FPR de operación** sin matizar. (Tarea de redacción, decidir la narrativa final.)
- **F7 — depuración de duplicados.** Cuantificar ambas depuraciones, mostrar un ejemplo de
  par duplicado y aclarar en metodología que no se elimina tráfico legítimo repetido.

---

## Orden de ejecución propuesto

1. 🅐 Alcance (frase canónica + barrido) — desbloquea F3, E2, N2, X2, F4/E3.
2. 🅓 Tiempos (unificar cifras N3).
3. 🅒 N1 (tabla de decisión a metodología/presentación).
4. 🅑 Modelo: F7 → F6 (redacción) → **F5 (re-run, el más largo)**.
5. Cierres Media: N4 (pfSense), confirmación IPv6.

Cada observación se cierra actualizando su fila (Estado / Cambio aplicado / Evidencia)
en `generar_respuesta_observaciones.py` y regenerando el xlsx.

## Estado de las observaciones

| ID | Tema | Prioridad | Estado |
|---|---|---|---|
| F3, N2, X2, E2 | Alcance | Alta | **Panel y presentación: aplicado** (frase canónica en `#s-alcance` del panel vivo + lámina 3 «Alcance» del deck). Artículo (X2 «inline», E2 traza) pendiente de que se redacte el artículo |
| F4, E3 | IPv6 | Media | Decidido: trabajo futuro (declarado en la frase de alcance del panel y del deck) |
| N3 | Tiempos | Alta | **Aplicado en lo vigente** (17-oct): diagramas VI-1/VI-3/VI-4 + `PLAN-DIAGRAMAS`, `ESTADO.md`, `PENDIENTES.md` a la cadena de 10 s (15,3 s / 41,4 s, :00/:03/:06); recorridos fechados anotados sin reescribir; docs de planificación actualizados. Falta: cifras en el artículo (sin redactar) |
| N1 | Decisión LIMIT/BLOCK | Alta | **Documento listo** (18-oct): tabla PERMIT/LIMIT/BLOCK + reglas + definición de LIMIT (limita tasa, no corta) en `N1-tabla-decision-limit-block.md`, con versión condensada para diapositiva. Falta: añadir la lámina al deck `.pptx` |
| F5 | Comparación modelos | Alta | **Volcado a tabla de artículo** (18-oct): los 7 modelos ya estaban re-ejecutados en `recongelar/` (entorno congelado); se volcó la tabla (ROC-AUC/PR-AUC/FPR/Det@FPR5% + McNemar+Holm p<0,001) y la de reemplazo OCSVM→IF en `F5-tabla-comparacion-7-modelos.md`. Cierra «ROC-AUC/significancia a medir». Modelo de producción intacto |
| F6 | α=0.05 + contradicción | Alta | Pendiente |
| F7 | Duplicados | Media | Pendiente |
| N4 | pfSense perimetral | Media | Pendiente (trabajo futuro) |
| E1 | Felicitación | — | No aplica |
