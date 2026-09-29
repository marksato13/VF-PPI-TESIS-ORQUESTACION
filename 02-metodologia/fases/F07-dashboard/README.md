# F07 · Dashboard

| | |
|---|---|
| **Identificador** | `PHASE-07` |
| **Estado** | Desplegado (8788). Panel de solo lectura con auth + TLS + rol y visualización ampliada: fila de KPIs, topología con recorrido y nodo «Cómo decide» (score vs umbral), variables por capa, mini-barra de score en decisiones, actividad con tooltip, asistente guiado y modo demo. |

## Objetivo

Mostrar salud, umbral y alertas leídos del manifiesto, nunca hardcodeados.

## Criterios de entrada

Sin esto, la fase no empieza:

- Motor desplegado

## Criterios de salida

La fase **no está cerrada** hasta que existan los siete elementos del criterio de
finalización —configuración persistente, prueba positiva, prueba negativa,
evidencia fechada, evaluación de riesgos, documentación reproducible y commit
identificable— **y además**:

- Umbral leído del manifest
- Fuente de cada dato declarada
- Solo lectura, sin acciones

## Procedimiento

Qué se hizo, con qué comando y qué artefacto verificable produjo:
[`../PROCEDIMIENTO.md`](../PROCEDIMIENTO.md#f07-dashboard).

## Evidencia

Referencias al repo de producto (no se copian aquí):

| Artefacto | Estado | Ruta o commit (producto) |
|---|---|---|
| Panel (servidor, auth/rol, KPIs, topología, variables, decisiones) | ACTIVO | `scripts/engine/dashboard.py` |
| Nodo «Cómo decide» (score vs umbral) | ACTIVO | commit `2d237c7` |
| Paleta categórica por capa | ACTIVO | commit `8596527` |
| Asistente guiado (tour) | ACTIVO | commit `4f0cdf2` |
| Modo demo (`scripts/demo.sh`) | ACTIVO | commit `1d607fb` |
| Pruebas del panel (auth, variables, escenarios, artefactos) | ACTIVO | `tests/test_panel_*.py`, `tests/test_dashboard_*.py` |

## Decisiones tomadas

| ID | Decisión | Fecha |
|---|---|---|
| — | Panel de **solo lectura** (no ejecuta acciones); escenarios en modo «copiar comando» | 2026-09 |
| — | Login con **rol** aplicado en el servidor + TLS (la contraseña cruza el troncal espejado) | 2026-09 |

> Una carpeta vacía **no cuenta como fase cerrada**.
