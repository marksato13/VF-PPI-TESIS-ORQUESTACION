# F08 · Validación operacional

| | |
|---|---|
| **Identificador** | `PHASE-08` |
| **Estado** | F6 ejecutada · despliegue **replicable** validado en 2ª VM aislada (offline) con `doctor.sh` sano · **falta pertinencia** (TAM sin aplicar) y recalibración en la 2ª red |

## Objetivo

Medir el sistema completo en operación, separando condiciones.

## Criterios de entrada

Sin esto, la fase no empieza:

- Motor y dashboard desplegados

## Criterios de salida

La fase **no está cerrada** hasta que existan los siete elementos del criterio de
finalización —configuración persistente, prueba positiva, prueba negativa,
evidencia fechada, evaluación de riesgos, documentación reproducible y commit
identificable— **y además**:

- Corridas con motor activo
- FPR offline y operativo por separado
- Prueba de aislamiento
- **Validación con usuarios**

## Procedimiento

Qué se hizo, con qué comando y qué artefacto verificable produjo:
[`../PROCEDIMIENTO.md`](../PROCEDIMIENTO.md#f08-validación-operacional).

## Evidencia

| Artefacto | Estado | Ruta o commit |
|---|---|---|
| Validación operacional F6 (58 corridas) | ACTIVO | producto: `results/f6/f6_resultados.jsonl` |
| Despliegue offline en 2ª VM (`cyberflow-sensor2`) | ACTIVO | orquestación: `04-evidencias/cyberflow/` (evidencia por fechar del 29-sep) |
| Chequeo de salud del sistema en marcha | ACTIVO | producto: `scripts/setup/doctor.sh` (commit `2dbe6f7`) |
| Pertinencia (usuarios) | PLANIFICADO | instrumento TAM preparado; sin aplicar |

## Decisiones tomadas

| ID | Decisión | Fecha |
|---|---|---|
| — | La 2ª VM se instala **offline** (bundle) para probar replicabilidad sin Internet en el sensor | 2026-09-29 |
| — | El TAM se aplica **sobre el sistema ya recalibrado**, no antes | 2026-09 |

> Una carpeta vacía **no cuenta como fase cerrada**. Pendiente: crear la evidencia
> fechada del despliegue en la 2ª VM y aplicar el TAM.
