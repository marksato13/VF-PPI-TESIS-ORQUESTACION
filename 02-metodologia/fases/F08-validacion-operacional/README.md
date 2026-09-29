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
| Ciclo llave-en-mano en 2ª VM (desinstalar → reinstalar → doctor) | ACTIVO | orquestación: `04-evidencias/cyberflow/K-despliegue-turnkey-sensor2-2026-09-29.md` |
| Chequeo de salud del sistema en marcha | ACTIVO | producto: `scripts/setup/doctor.sh` (commit `2dbe6f7`) |
| Fix hallado en la prueba: panel sin auth = AVISO, no FALLO | ACTIVO | producto: `scripts/setup/instalar.sh` (commit `131ac27`) |
| Fix: timers a `OnCalendar` (no quedan sin próximo disparo tras reinstalar/reiniciar) | ACTIVO | producto: `scripts/setup/cyberflow_config.py` (commit `56c01e8`) |
| Fix: `doctor.sh` cuenta bien los avisos | ACTIVO | producto: `scripts/setup/doctor.sh` (commit `f7d0fe8`) |
| Instalador offline-aware (Suricata por `dpkg` desde el bundle si no hay red) | ACTIVO | producto: `scripts/setup/instalar.sh` (commit `da43aa8`) |
| Asistente con menú de escenarios de despliegue (1/2/3) | ACTIVO | producto: `scripts/setup/configurar.sh` (commit `73d292c`) |
| Pertinencia (usuarios) | PLANIFICADO | instrumento TAM preparado; sin aplicar |

## Decisiones tomadas

| ID | Decisión | Fecha |
|---|---|---|
| — | La 2ª VM se instala **offline** (bundle) para probar replicabilidad sin Internet en el sensor | 2026-09-29 |
| — | El TAM se aplica **sobre el sistema ya recalibrado**, no antes | 2026-09 |

> Una carpeta vacía **no cuenta como fase cerrada**. La evidencia fechada del
> despliegue en la 2ª VM ya existe (`K-…-2026-09-29.md`). Pendiente para cerrar:
> aplicar el TAM y recalibrar (ambas gobernadas por decisiones abiertas del
> `ESTADO.md`, no por herramienta).
