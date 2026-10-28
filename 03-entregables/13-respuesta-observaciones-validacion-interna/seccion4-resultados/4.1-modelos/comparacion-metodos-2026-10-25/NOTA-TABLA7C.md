# Nota — Tabla 7-c (α = 0,01): detección frente a falsas alarmas

## Procedencia
Mismos datos, modelos, escalador y puntuaciones que las Tablas 7-a/7-b (`salidas/puntuaciones-*.csv.gz`, hashes verificados contra `MANIFIESTO-COMPARACION.json`). Solo cambia el umbral: cuantil 0,99 de la puntuación de validación de **cada** modelo (no se aplica el umbral del IF a los demás). No se reentrena, no se re-puntúa, no se tocan 7-a/7-b, figuras, Word, servicios ni configuración desplegada.

## Lectura (sin anticipar un ganador)
Bajar α a 0,01 sube el umbral y reduce las alertas: respecto a 0,03/0,05 caen los FP y, en la mayoría de modelos, también algún TP. ROC-AUC y AP **no cambian** (no dependen del umbral), así que el orden por capacidad de ranking es el mismo que en 7-a/7-b; lo que cambia es el punto de operación.
Los conteos son **por ventana**, no por episodio: perder una ventana no equivale a perder un ataque completo. La cobertura por episodio y la detección durante el ataque **no** se pueden comprobar con estos datos (el conjunto de ataques no trae escenario/episodio) y quedan pendientes de la campaña A.
No se afirma que el IF sea el mejor; cada modelo se reporta con sus TP/FP y sus AUC/AP, incluidos los desfavorables (p. ej. AP muy baja de LOF pese a su recall alto).

## Límite de interpretación
Estos datos ya se usaron para **orientar** la elección de α; por tanto, elegir aquí el “mejor” punto **no** es una confirmación independiente. La decisión operativa de α no se cambia en este entregable.

