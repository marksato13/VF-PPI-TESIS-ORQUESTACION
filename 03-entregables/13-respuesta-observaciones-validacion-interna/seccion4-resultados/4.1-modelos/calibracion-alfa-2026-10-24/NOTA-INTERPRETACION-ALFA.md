# Nota de interpretación — sensibilidad de α (IF limpio, validación sin Kali)

## Compromiso detección ↔ falsas alarmas
Al subir α el umbral sube y se alerta más: aumentan TP y FP a la vez; al bajar α ocurre lo contrario.
En este conjunto, el recall por **ventanas** va de 30.95 % (α=0,005) a 70.24 % (α=0,10), y la FPR de 0.43 % a 9.31 %.
El TP por ventanas se estanca en 54 entre α=0,03 y α=0,05 (mismas 54 ventanas), mientras los FP siguen subiendo.

## Configuraciones dominadas
Una configuración está **dominada** si otra logra al menos tantos TP con no más FP y mejora estrictamente uno de los dos.
Dominadas: 0,04, 0,05.
No dominadas (frente de Pareto en TP/FP por ventana): 0,005, 0,008, 0,01, 0,02, 0,025, 0,03, 0,1.

## Qué α merece la pena incluir en la campaña A (sujeto a comprobación de cobertura)
- **α = 0,05**: es el **desplegado**; se incluye como referencia operativa (no se cambia ahora).
- **α = 0,03**: mismo TP por ventana que 0,04–0,05 (54) con **menos FP** (1 723 vs 2 299/2 955) → domina a 0,04 y 0,05 en este conjunto.
- **α = 0,01** y **α = 0,008**: menos FP, pero pierden TP por ventana; útiles para ver el extremo de baja FPR.
- **α = 0,005**: extremo de mínima FPR; mayor pérdida de TP por ventana.
Recomendación (pendiente de cobertura por episodio y detección durante el ataque, que estos datos **no** permiten
comprobar): llevar a la campaña A **al menos α ∈ {0,05 (desplegado), 0,03, 0,01}**, y opcionalmente 0,008 y 0,005
para trazar el extremo de baja FPR. La elección definitiva debe mirar cobertura por **episodio** (no por ventana),
no solo estos conteos.

## Límites de esta lectura
- Estos datos **ya se usaron** para comparar y orientar la elección de α: elegir aquí el “mejor” **no** es una validación independiente.
- El recall y los TP son **por ventana**; perder una ventana **no** es perder un ataque. No hay etiqueta de episodio en este conjunto.
- **No** se afirma que un α menor cause lentitud o inestabilidad: no hay mediciones de rendimiento aquí.
- FP/TP se ofrece como indicador complementario de falsas alarmas por detección correcta, no como criterio único.

## Archivos que requerirían actualización si luego se cambia el α seleccionado (no se tocan ahora)
- `config-campana.json` (`umbrales`, `modelo.alpha`/umbral operativo) y el umbral del motor desplegado.
- Fila del IF en la Tabla 7 (`comparacion-metodos-2026-10-25/TABLA7-*`) y la figura ROC-PR de puntos operativos.
- `figura-sensibilidad-alfa.*` y `figura-roc-pr-puntos-operativos.*` de este directorio (regenerar con los 9 α).
- Word del artículo (Tabla 6-a, Tabla 7 y texto asociado) — **no** se edita aquí.
- `calibrar_alfa.py` (lista `ALFAS` y `U_OP`) si se adopta el conjunto ampliado como canónico.

