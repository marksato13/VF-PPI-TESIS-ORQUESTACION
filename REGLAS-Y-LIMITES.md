# Reglas y límites

Estables: no cambian entre tareas. La tarea concreta vive en
[`TASK-ACTUAL.md`](TASK-ACTUAL.md).

## Reparto de responsabilidades

| Agente | Función | Nunca hace |
|---|---|---|
| **Claude** | Revisor adversarial: audita, señala inconsistencias, revisa diffs | Implementar sin encargo explícito |
| **Codex** | Implementador y operador del laboratorio | Autoaprobarse su propio trabajo |
| **Hermes** | Orquestación, planificación y estados | Tocar artefactos congelados |
| **Herdr** | Persistencia de procesos y recuperación | Decidir contenido |

El objetivo no es que Claude y Codex coincidan, sino **encontrar errores antes
de la defensa** mediante revisión cruzada.

## Prohibiciones absolutas

1. **Nunca `git commit` ni `git push`** sin autorización explícita del usuario en
   esa misma conversación.
2. **Nunca `push --force`, `reset --hard` ni reescritura de historial publicado.**
3. **Nunca modificar artefactos congelados.** Ver la lista en `TASK-ACTUAL.md`.
4. **Nunca inventar una cifra.** Si un dato no tiene fuente primaria se reporta
   como pendiente. **Un bloqueo reportado es un resultado válido; un dato
   inventado no lo es.**
5. **Nunca `git add -A`** sin revisar antes `git status`: otro agente puede tener
   trabajo sin commitear.
6. **Nunca firmar como el asesor** ni atribuirle una revisión que no hizo.

## Los tres estados de una afirmación

Todo texto debe distinguirlos, siempre:

| Estado | Qué significa |
|---|---|
| **OBTENIDO** | Medido en una ejecución, con artefacto verificable |
| **VALIDADO** | Confirmado con prueba positiva **y** negativa reproducibles |
| **PLANIFICADO** | No ejecutado. **Nunca se escribe en pasado** |

Existir un documento que lo describa **no lo convierte en validado**.

## Formato obligatorio de un hallazgo

1. Identificador y título
2. Severidad: crítica · alta · media · baja
3. **Hecho observado**, con evidencia reproducible
4. **Inferencias, separadas de los hechos**
5. Riesgo para seguridad, funcionamiento o validez científica
6. Prueba reproducible para confirmarlo o refutarlo
7. Corrección propuesta y efectos secundarios
8. Estado: pendiente · confirmada · rechazada · corregida

No presentar preferencias de estilo como fallos técnicos. **No aceptar
afirmaciones de otro agente sin comprobarlas.**

## Clasificación documental antes de borrar

Ningún documento se elimina sin pasar por esta clasificación:

| Estado | Qué hacer |
|---|---|
| **ACTIVO** | Se mantiene y se cita |
| **DESACTUALIZADO** | Se corrige o se marca con fecha y motivo |
| **DUPLICADO** | Se fusiona; queda uno solo |
| **HISTÓRICO** | Se archiva; describe un estado pasado que fue cierto |
| **NO VERIFICABLE** | Se marca; no se cita como evidencia |
| **CANDIDATO A ARCHIVO** | Se propone, no se ejecuta sin autorización |

Antes de eliminar se conserva: **hash, ubicación original, motivo y reemplazo.**

## Trampas conocidas

Todas costaron tiempo real. Están aquí para que no vuelvan a costarlo.

1. El verificador de consistencia del PPI declara **21 excepciones legítimas**.
   No son errores. Su salida correcta es `RASTROS OBSOLETOS: 0` con `exit 0`.
2. Los `.docx` y `.xlsx` **se regeneran con marca de tiempo distinta aunque el
   texto sea idéntico**. Comparar el texto extraído, nunca el binario.
3. `python-docx` y `openpyxl` viven **solo en `.venv/bin/python3`**.
4. **`openpyxl` no interpreta Markdown**: escribir `**texto**` en una celda
   muestra los asteriscos. Usar `CellRichText`.
5. Los generadores de Word **solo entendían `**negrita**`**; `*cursiva*` y
   `` `código` `` salían literales. Verificar con un contador de caracteres.
6. **Un `.docx` puede no generarse desde su `.md`.** Comprobarlo antes de asumir
   que corregir el Markdown basta.
7. **Iterar un `set` de Python no es determinista** entre ejecuciones. Ordenarlo
   antes, o el artefacto cambia sin que cambie ningún dato.
8. Scopus, SCImago, DOAJ y Springer **bloquean el acceso automatizado**.
   Declarar el bloqueo, jamás rellenar con un agregador.

## Criterio de finalización

Una fase solo está terminada con: configuración persistente · prueba positiva ·
prueba negativa · evidencia fechada · evaluación de riesgos · documentación
reproducible · commit identificable sin secretos.
