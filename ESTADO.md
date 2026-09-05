# Estado

**Actualizado:** 4 de septiembre de 2026

| | |
|---|---|
| **Tarea activa** | `PPI-REBASE-001` — ver [`TASK-ACTUAL.md`](TASK-ACTUAL.md) |
| **Estado** | `READY` — estructura creada, inventario pendiente |
| **Siguiente agente** | **Claude**: paso 1 del flujo (inventario) |

## El ciclo

```
Claude audita  →  handoffs/HANDOFF-CLAUDE.md
                        ↓
Codex implementa  →  RESULTADO-ULTIMA-EJECUCION.md
                        ↓
Claude revisa el diff  →  auditorias/claude/REVIEW-Rnn.md
                        ↓
Codex corrige solo lo confirmado
                        ↓
El usuario revisa y autoriza el commit
```

**Ningún agente commitea.** El commit lo autoriza el usuario.

## Cómo disparar la ejecución

Ningún agente lee estos archivos por su cuenta:

```
Lee TASK-ACTUAL.md de VF-PPI-TESIS-ORQUESTACION y ejecuta el flujo completo.
Usa el contexto de REGLAS-Y-LIMITES.md y CONTEXTO-PROYECTO.md.
No pidas confirmación intermedia salvo condición de bloqueo.
```

## Progreso por fase

| Fase | Estado en el producto | Auditada aquí |
|---|---|---|
| F00 · Gobernanza | — | ⏳ |
| F01 · Infraestructura | Validada | ⏳ |
| F02 · Diseño experimental | Validada | ⏳ |
| F03 · Features | 28 definidas, 27 observables | ⏳ |
| F04 · Dataset | Congelado con hashes | ⏳ |
| F05 · Modelado | OCSVM congelado | ⏳ |
| F06 · Motor tiempo real | Desplegado en VM02 | ⏳ |
| F07 · Dashboard | Desplegado, puerto 8788 | ⏳ |
| F08 · Validación operacional | F6 ejecutada, 58 corridas | ⏳ |
| F09 · Tesis y publicación | 3 entregables cerrados | ⏳ |

## Lo que bloquea el cierre

| ID | Pendiente | Fecha |
|---|---|---|
| **P-3** | Sesión SUS con 5–8 evaluadores | **9 sep 2026** |
| **P-5** | Escenarios legítimos faltantes | 19 sep 2026 |
| — | Envío del artículo a IJIES | 28 sep 2026 |
| **P-1** | Recalibrar con tráfico pesado | 10 oct 2026 |
| **P-2 · P-4** | Jornada nueva como holdout externo | 24 oct 2026 |
