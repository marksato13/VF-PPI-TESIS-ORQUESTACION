# Planificación

**Versión 1 · 4 de septiembre de 2026**

---

## 1. Diagnóstico

El proyecto **no tiene falta de trabajo técnico**. Tiene infraestructura
virtualizada, captura con Suricata, dataset congelado, extractor de variables
L3/L4/L7, modelo OCSVM, motor de detección y bloqueo desplegado, dashboard,
validación operativa, datasheet, model card, system card, tests y revisiones
adversariales.

Lo que falta es **el sistema que conecta todo eso**:

```
Requisito de tesis → Fase → Decisión técnica → Implementación
                                                     ↓
Entregable ← Afirmación científica ← Evidencia ← Prueba
```

### Riesgos observados, con evidencia de esta sesión

Ninguno es hipotético. Los seis se manifestaron y costaron tiempo:

| # | Riesgo | Cómo se manifestó |
|---|---|---|
| 1 | Documentos que envejecen respecto a los artefactos | El informe de validación declaraba «no abordado» algo que **ya se había ejecutado** |
| 2 | Un formato desincronizado de otro | El `.docx` no se generaba desde su `.md`: decía cifras distintas |
| 3 | La misma cifra escrita de varias formas | `25,8 %` · `25,81 %` · `23,0 %` · `22,97 %` para dos mediciones |
| 4 | Etiquetas de trazabilidad mal puestas | El juicio experto figuraba como si cerrara P-3, y solo lo refuerza |
| 5 | Artefactos no deterministas | Un `set` de Python cambiaba el orden del Excel entre ejecuciones |
| 6 | Confundir marcos conceptuales | Reproducibilidad presentada como si fuera replicabilidad |

**Ninguno era un error de código.** Todos eran fallos de trazabilidad, y por eso
la capa que falta es esta.

### Clasificación antes de borrar

Ningún documento se elimina sin pasar por: **ACTIVO · DESACTUALIZADO ·
DUPLICADO · HISTÓRICO · NO VERIFICABLE · CANDIDATO A ARCHIVO**, conservando
hash, ubicación original, motivo y reemplazo.

---

## 2. Arquitectura propuesta

### Capa de virtualización

Una VM Ubuntu Server 24.04 basta para empezar.

| Recurso | Recomendado |
|---|---|
| CPU | 8 vCPU |
| RAM | 16 GB |
| Disco sistema | 80 GB |
| Disco datos y evidencias | 150 GB |
| GPU | No necesaria |

**La VM no debe ser un punto único de fallo.** Backup externo y **prueba
periódica de restauración**: un backup que nunca se restauró no es un backup.

### Servicios nativos

| Servicio | Función |
|---|---|
| Hermes Agent | Coordinación, planificación y disparo de tareas |
| Herdr | Supervisor de terminales, procesos y agentes |
| OpenCode | Implementación de código y documentación |
| Python + uv | Scripts y entornos reproducibles |
| Tailscale | Acceso privado entre equipos |
| Restic | Backups cifrados |

Hermes y Herdr con **usuario Unix dedicado, servicio systemd, permisos mínimos,
logs separados, healthcheck y límites de CPU y memoria**.

### Servicios en Docker Compose

| Servicio | Función | Límite explícito |
|---|---|---|
| PostgreSQL | Metadatos, estados y trazabilidad | **No sustituye a Git ni a los artefactos** |
| pgvector | Búsqueda semántica de documentos | Índice, no fuente |
| Gitea | Repositorio privado e issues | Espejo, no origen |
| JupyterLab | Análisis exploratorio | **Ningún resultado nace en un notebook**: cada uno produce salida versionada por script |

### Documentación científica

Quarto para informes reproducibles · Pandoc para conversión · LaTeX para el PDF
final · Mermaid y Graphviz para diagramas · JSON y YAML para manifiestos.

### Seguridad y operación

UFW o nftables · Tailscale para administración · **SOPS + age** o systemd
credentials para secretos · restic a almacenamiento externo · healthchecks ·
rotación de logs · inventario de versiones · SBOM · **escaneo de secretos antes
de cada publicación** · prueba de restauración.

> **El Quick Tunnel de Cloudflare no es infraestructura de producción.** La URL
> cambia y no tiene garantía de disponibilidad. Sirve para pruebas remotas
> puntuales y nada más.

---

## 3. Sistema de trazabilidad

Identificador permanente por elemento:

| Prefijo | Qué identifica |
|---|---|
| `REQ-nnn` | Requisito de tesis o del jurado |
| `PHASE-nn` | Fase del proyecto |
| `DEC-nnn` | Decisión técnica |
| `EXP-nnn` | Experimento |
| `ART-nnn` | Artefacto producido |
| `TEST-nnn` | Prueba |
| `RISK-nnn` | Riesgo |
| `CLAIM-nnn` | Afirmación científica |
| `DOC-nnn` | Entregable |

### Ejemplo con datos reales del proyecto

```
REQ-014   Demostrar detección temprana de tráfico anómalo
PHASE-06  Motor de decisión en tiempo real
TEST-032  Bloqueo inline con tráfico controlado (F6, 58 corridas)
ART-087   results/f6/f6_resultados.jsonl + manifest + hash
CLAIM-009 «Bloqueo en mediana de 8,0 s, rango 6,1–13,7, n = 8»   [OBTENIDO]
DOC-004   Informe de evaluación crítica, sección 1
```

Cada afirmación lleva su estado: **OBTENIDO · VALIDADO · PLANIFICADO**.
Nunca «validado» solo porque exista un documento que lo diga.

---

## 4. Fases

Cada una con criterio de entrada, salida y evidencia exigida.

| Fase | Objetivo | Estado en el producto |
|---|---|---|
| **F00** Gobernanza | Separar producto, experimento y tesis; congelar reglas | Pendiente |
| **F01** Infraestructura | VM, red, servicios, backups y **restauración probada** | Validada |
| **F02** Diseño experimental | Qué se prueba y qué no; preflight, drops, NTP, ledger | Validada |
| **F03** Contrato de variables | Fórmula, ventana, denominador, ceros, coste, riesgo de fuga | 28 definidas, 27 observables |
| **F04** Dataset | Composición, episodios, particiones, duplicados, sesgos, SHA-256 | Congelado |
| **F05** Modelado | Baselines, selección, umbral, evaluación bloqueada, intervalos | OCSVM congelado |
| **F06** Motor tiempo real | Latencia, lead-time, bloqueo, expiración, carga, disponibilidad | Desplegado |
| **F07** Dashboard | Salud, umbral y alertas **leídos del manifiesto, no hardcodeados** | Desplegado |
| **F08** Validación operacional | Offline, laboratorio, legítimo, anómalo, adversarial | F6 ejecutada |
| **F09** Tesis y publicación | Evaluación, plan, cronograma, cards, artículo, defensa | 3 entregables cerrados |

---

## 5. Agentes

| Componente | Responsabilidad |
|---|---|
| **Claude** | Auditoría adversarial, coherencia científica, cifras y limitaciones |
| **Codex** | Implementación, pruebas, scripts, operación |
| **Hermes** | Orquestación, planificación y estados |
| **Herdr** | Persistencia de procesos y recuperación |
| **PostgreSQL** | Índice de trazabilidad y búsqueda |
| **Gitea** | Revisión interna e issues |

> **La sesión interactiva de Claude no es memoria compartida.** La interfaz
> oficial entre agentes son cuatro archivos: `TASK-ACTUAL.md`,
> `HANDOFF-CLAUDE.md`, `REVIEW-ADVERSARIAL.md` y
> `RESULTADO-ULTIMA-EJECUCION.md`. Todo lo demás se pierde al cerrar la terminal.

---

## 6. Orden de ejecución

**No se empieza reescribiendo la tesis.**

| # | Paso | Sale en |
|---|---|---|
| 1 | Inventario completo | `evidencia/inventarios/` |
| 2 | Matriz de requisitos | `trazabilidad/requisitos.md` |
| 3 | Mapa de evidencias | `trazabilidad/requisitos-a-evidencias.csv` |
| 4 | Auditoría de afirmaciones | `trazabilidad/afirmaciones-cientificas.md` |
| 5 | Reconciliación de fases | `fases/` |
| 6 | Reestructuración documental | producto |
| 7 | Auditoría del producto | `auditorias/` |
| 8 | Mejoras priorizadas | `TASK-ACTUAL.md` |
| 9 | Pruebas nuevas | producto |
| 10 | Actualización de tesis y cronograma | `informes/` |
| 11 | Revisión adversarial | `auditorias/claude/` |
| 12 | Revisión humana antes de publicar | — |

### La meta

No es «añadir más IA». Es que **cualquier afirmación responda en menos de un
minuto**:

¿De dónde sale? · ¿Qué comando la produjo? · ¿Qué artefacto la demuestra? ·
¿Qué versión estaba activa? · ¿Obtenida, validada o planificada? · ¿Qué
limitación tiene? · ¿En qué entregable aparece?

---

## 7. Riesgos de esta planificación

Declarados por honestidad, no por trámite:

| Riesgo | Mitigación |
|---|---|
| **La orquestación consume el tiempo de la tesis** | La defensa es el 24 de octubre. Los pasos 1–4 dan valor inmediato; **5–12 son opcionales si el calendario aprieta** |
| **Duplicar información entre repositorios** | Aquí solo van **referencias con hash**, jamás copias |
| **Montar servicios que nadie usa** | PostgreSQL, Gitea y Jupyter solo si un paso concreto los necesita. **Un servicio sin usuario es deuda** |
| **La estructura vacía da falsa sensación de avance** | Una carpeta sin contenido verificado **no cuenta como fase cerrada** |
