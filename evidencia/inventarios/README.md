# Inventario del producto

**2026-09-05** · 639 archivos versionados de `vf-sistema-final`

Generado por `stack/bin/ppi-inventario` desde el repositorio, no
redactado a mano. Datos completos en [`inventario-2026-09-05.csv`](inventario-2026-09-05.csv).

**No se ha borrado ni movido nada.** Este documento clasifica y
explica; la decision es de una persona.

| Categoria | N | Que significa |
|---|---:|---|
| `ACTIVO` | 269 | algo lo referencia, o es codigo, configuracion o artefacto en uso |
| `HISTORICO` | 349 | registro fechado; no se actualiza por disenho |
| `DUPLICADO` | 4 | otro archivo tiene exactamente el mismo contenido |
| `DESACTUALIZADO` | 9 | enlaza o cita documentos que ya no existen |
| `NO_VERIFICABLE` | 0 | sin contenido comprobable |
| `CANDIDATO_ARCHIVO` | 8 | nadie lo referencia y no es registro ni codigo |

---

## DESACTUALIZADO (9)

| Archivo | Motivo | Ultimo commit |
|---|---|---|
| `.agent/RESULTADO-ULTIMA-EJECUCION.md` | cita 1 documento(s) inexistente(s): plan-de-validacion.md | 2026-09-02 |
| `.agent/TASK-ACTUAL.md` | cita 1 documento(s) inexistente(s): 07-plan-de-validacion/plan-de-validacion.md | 2026-09-02 |
| `docs/entregables/08-validacion-usuarios/README.md` | cita 1 documento(s) inexistente(s): resultados-sus.md | 2026-09-02 |
| `docs/fase01-diseno-experimental/18-congelamiento-protocolo-R04-R05.md` | cita 2 documento(s) inexistente(s): 03-protocolo-modelado-F1-v2.md | 2026-08-18 |
| `docs/fase01-diseno-experimental/README.md` | cita 1 documento(s) inexistente(s): ../F4-modelado/03-protocolo-modelado-F1-v2.md | 2026-08-18 |
| `docs/fase02-features-multicapa/01-diccionario-multicapa-G5.md` | cita 1 documento(s) inexistente(s): 03-protocolo-modelado-F1-v2.md | 2026-08-18 |
| `docs/fase04-modelado/06-modelo-final-congelado-ocsvm.md` | cita 2 documento(s) inexistente(s): 07-resultado-calibracion-multilayer-v2-v1.md | 2026-09-02 |
| `docs/fase05-motor-tiempo-real/01-diseno-motor-tiempo-real.md` | cita 1 documento(s) inexistente(s): 08-modelo-final-congelado-ocsvm.md | 2026-08-18 |
| `docs/fase06-dashboard/01-diseno-dashboard-motor.md` | cita 2 documento(s) inexistente(s): 09-diseno-motor-tiempo-real.md | 2026-08-18 |

---

## DUPLICADO (4)

| Archivo | Motivo | Ultimo commit |
|---|---|---|
| `artifacts/model/candidates/if_exact_collapsed.joblib` | contenido identico a artifacts/model/candidates/if_uniform.joblib | 2026-08-25 |
| `artifacts/model/candidates/if_uniform.joblib` | contenido identico a artifacts/model/candidates/if_exact_collapsed.joblib | 2026-08-25 |
| `artifacts/model/candidates/ocsvm_scaled.joblib` | contenido identico a artifacts/model/ocsvm_scaled.joblib | 2026-08-25 |
| `artifacts/model/ocsvm_scaled.joblib` | contenido identico a artifacts/model/candidates/ocsvm_scaled.joblib | 2026-08-25 |

---

## CANDIDATO_ARCHIVO (8)

| Archivo | Motivo | Ultimo commit |
|---|---|---|
| `docs/agent-context/catalogo-skills-data-science.md` | ningun documento lo referencia | 2026-08-26 |
| `docs/entregables/03-auditoria-comparativa/auditoria-comparativa-mvp-vs-version-final.md` | ningun documento lo referencia | 2026-09-02 |
| `docs/entregables/diagramas/topologia-laboratorio.drawio` | ningun documento lo referencia | 2026-08-19 |
| `docs/fase01-diseno-experimental/02-procedimiento-operativo.md` | ningun documento lo referencia | 2026-08-18 |
| `docs/fase01-diseno-experimental/03-plantilla-evidencia-F0.md` | ningun documento lo referencia | 2026-08-18 |
| `docs/fase01-diseno-experimental/04-auditoria-G0-2026-07-20.md` | ningun documento lo referencia | 2026-08-18 |
| `docs/fase01-diseno-experimental/05-evidencia-F0-piloto-2026-07-20.md` | ningun documento lo referencia | 2026-08-18 |
| `docs/fase01-diseno-experimental/06-servicios-servidor-y-calibracion.md` | ningun documento lo referencia | 2026-08-18 |

---

## Lo ACTIVO e HISTORICO, por carpeta

| Carpeta | Activo | Historico | Otros |
|---|---:|---:|---:|
| `docs/fase03-dataset` | 0 | 182 | 0 |
| `docs/revisiones-claude` | 0 | 167 | 0 |
| `docs/entregables` | 43 | 0 | 3 |
| `docs/fase01-diseno-experimental` | 12 | 0 | 7 |
| `scripts/entregables` | 15 | 0 | 0 |
| `tests` | 13 | 0 | 0 |
| `docs/fase04-modelado` | 10 | 0 | 1 |
| `.agents/skills` | 10 | 0 | 0 |
| `.claude/skills` | 10 | 0 | 0 |
| `ansible/playbooks` | 10 | 0 | 0 |
| `configs/sensor` | 10 | 0 | 0 |
| `artifacts/model` | 5 | 0 | 4 |
| `scripts/modeling` | 9 | 0 | 0 |
| `(raiz)` | 8 | 0 | 0 |
| `configs/server` | 8 | 0 | 0 |
| `scripts/campaign` | 7 | 0 | 0 |
| `scripts/dataset` | 7 | 0 | 0 |
| `scripts/f1` | 7 | 0 | 0 |
| `docs/dataset` | 5 | 0 | 0 |
| `scripts/features` | 5 | 0 | 0 |
| `.agent` | 2 | 0 | 2 |
| `ansible` | 4 | 0 | 0 |
| `artifacts/dataset` | 4 | 0 | 0 |
| `configs/campaigns` | 4 | 0 | 0 |
| `docs/fase00-infraestructura` | 4 | 0 | 0 |
| `results/ablacion` | 4 | 0 | 0 |
| `scripts/analysis` | 4 | 0 | 0 |
| `configs/suricata` | 3 | 0 | 0 |
| `docs/fase02-features-multicapa` | 2 | 0 | 1 |
| `ansible/inventories` | 2 | 0 | 0 |
| `configs/features` | 2 | 0 | 0 |
| `configs/time` | 2 | 0 | 0 |
| `dashboard` | 2 | 0 | 0 |
| `docs/07-mejoras-futuras` | 2 | 0 | 0 |
| `docs/agent-context` | 1 | 0 | 1 |
| `docs/articulo` | 2 | 0 | 0 |
| `docs/fase05-motor-tiempo-real` | 1 | 0 | 1 |
| `docs/fase06-dashboard` | 1 | 0 | 1 |
| `docs/fase07-validacion-final` | 2 | 0 | 0 |
| `mcp-servers/mendeley` | 2 | 0 | 0 |
| `results/f6` | 2 | 0 | 0 |
| `scripts/articulo` | 2 | 0 | 0 |
| `scripts/engine` | 2 | 0 | 0 |
| `scripts/f6` | 2 | 0 | 0 |
| `.codex` | 1 | 0 | 0 |
| `agent-skills/ppi-dataset-audit` | 1 | 0 | 0 |
| `agent-skills/ppi-datasheet-builder` | 1 | 0 | 0 |
| `agent-skills/ppi-experiment-freezer` | 1 | 0 | 0 |
| `agent-skills/ppi-feature-contract-review` | 1 | 0 | 0 |
| `agent-skills/ppi-leakage-validity-audit` | 1 | 0 | 0 |
| `agent-skills/ppi-model-evaluation` | 1 | 0 | 0 |
| `agent-skills/ppi-operational-validation` | 1 | 0 | 0 |
| `agent-skills/ppi-release-readiness` | 1 | 0 | 0 |
| `agent-skills/ppi-scientific-claim-audit` | 1 | 0 | 0 |
| `agent-skills/ppi-scientific-figures` | 1 | 0 | 0 |
| `ansible/scripts` | 1 | 0 | 0 |
| `configs/storage` | 1 | 0 | 0 |
| `docs/auditorias` | 1 | 0 | 0 |
| `docs/requisitos-jurado` | 1 | 0 | 0 |
| `scripts/kali` | 1 | 0 | 0 |
| `scripts/storage` | 1 | 0 | 0 |
