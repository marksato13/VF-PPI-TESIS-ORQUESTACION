# Tarea activa

```
ID:     PPI-REBASE-001
Estado: READY
Fecha:  2026-09-04
Agente: Claude (inventario y auditoría) → Codex (implementación)
```

---

## TAREA: Rebaselinar tesis y producto PPI

## OBJETIVO

Auditar y reestructurar el proyecto de F00 a F09 **manteniendo separados** el
producto, la evidencia experimental y la tesis. La meta no es añadir nada nuevo,
sino que **cualquier afirmación pueda responder de dónde sale**.

## ALCANCE

**Repositorio del producto** (`VF-Sistema-Open-Source-…`), solo lectura salvo
autorización explícita:

- Documentación de fases · entregables · datasheet · model card · system card
- Plan de validación · evaluación crítica · cronograma

**Este repositorio**, escritura libre dentro del flujo:

- `trazabilidad/` · `fases/` · `auditorias/` · `evidencia/` · `informes/`

## NO MODIFICAR

```
artifacts/dataset/*.csv          artifacts/model/*.joblib
artifacts/model/manifest.json    results/ablacion/*.json
results/f6/*.jsonl               configs/campaigns/multilayer-v2-normal.json
docs/fase07-validacion-final/02-resultados-f6.md    ← fuente primaria
PCAP y EVE históricos            Secretos, tokens y credenciales
Historial Git publicado
```

## FLUJO OBLIGATORIO

1. **Claude** inventaría fases, documentos, artefactos y contradicciones.
2. **Claude** clasifica cada elemento: activo · desactualizado · duplicado ·
   histórico · no verificable · candidato a archivo.
3. **Claude** construye la matriz requisito → fase → prueba → evidencia →
   documento, en `trazabilidad/`.
4. **Codex** implementa únicamente los cambios autorizados en el handoff.
5. **Codex** ejecuta pruebas y verificaciones.
6. **Claude** revisa adversarialmente el diff.
7. **Codex** corrige únicamente los hallazgos confirmados.
8. Se actualizan informes, resultados y cronograma.
9. Se genera el resultado final con obtenido, validado y planificado separados.
10. **Sin commit ni push** sin autorización explícita.

## RESTRICCIONES

- Máximo **2 ciclos** de revisión.
- **Detenerse ante cualquier hash alterado o prueba fallida.**
- No cambiar el dataset salvo autorización explícita.
- Un bloqueo reportado es un resultado; un dato inventado no lo es.

## ACEPTACIÓN

**Comandos** (en el repositorio del producto):

```bash
.venv/bin/python3 -m pytest tests/ -q                  # esperado: 90 passed
python3 scripts/entregables/verificar_consistencia.py  # esperado: exit 0
sha256sum -c docs/dataset/SHA256SUMS                   # esperado: 13 OK
git diff --check                                       # esperado: sin salida
```

**Hashes que no deben cambiar:**

```
3846d44c0fe32ac4b4c98f022adac7c459c6add2c6b95062e6bb3237fe9b28ab  multilayer-v2-normal.csv
d115ef987cbd845118038314b7c55a7ad4e359ff4ebfd486c0e664ed3d8078c3  multilayer-v2-anomalies.csv
0a1e8c52dc3282029d9aa1c9a0adbe7cc03c28bbce48bd5b76959e46bdbf5b1b  manifest.json
af9b50c29f839037b2bda380fc197e017dea482d403c61fa7ae3df79cbff7236  ocsvm_scaled.joblib
```

**Criterios:**

- Cada requisito tiene fase, responsable y evidencia.
- **Cada cifra tiene fuente primaria.**
- No hay resultados planificados presentados como obtenidos.
- Datasheet, model card, system card y tesis son coherentes entre sí.
- Los artefactos congelados conservan sus hashes.
- Las fases tienen criterios de entrada y de salida.
- Las limitaciones operacionales aparecen en todos los documentos pertinentes.
- El cronograma tiene fechas y estados reales.
- Los documentos obsoletos quedan archivados o justificados.
- Existe un runbook reproducible para reconstruir el entorno.
- **Estado final:** `COMPLETO` · `CONDICIONADO` · `BLOQUEADO`

## SALIDA

Escribir `RESULTADO-ULTIMA-EJECUCION.md` con: cambios realizados · evidencia y
comandos con salida literal · resultados exactos · limitaciones · archivos
modificados · pendientes y cronograma actualizado.

## SKILLS APLICABLES

Declarar cuál se activa y por qué. **No activarlas todas.**

| Skill | Cuándo |
|---|---|
| `ppi-dataset-audit` | Al tocar composición, particiones o gates del dataset |
| `ppi-feature-contract-review` | Al revisar el contrato de las 28 variables |
| `ppi-leakage-validity-audit` | Al auditar fuga, pseudorreplicación o validez |
| `ppi-model-evaluation` | Al comparar modelos o recalcular métricas |
| `ppi-operational-validation` | Al contrastar métricas offline con tráfico real |
| `ppi-scientific-claim-audit` | Al verificar afirmaciones contra fuente primaria |
| `ppi-release-readiness` | Antes de publicar cualquier versión |
