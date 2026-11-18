# Cumplimiento de observaciones de Asin y Neemias

## Resultado de esta delegación

Se ejecutaron **cuatro frentes con agentes** y se prepararon doce entregables. Se contrastaron con los análisis OpenAI Whisper medium y con el estado documental `1e378d2c1917adb1c530b83f82c1d693c310b4ac`.

**Material preparado no significa observación aplicada, aprobación del asesor ni validación externa realizada.** Las tareas conservan la atribución Asin/Neemias y sus marcas de tiempo; los responsables y prioridades que se proponen aquí son organización del coordinador, no asignaciones pronunciadas en los audios. No se fija una fecha a partir de «hoy» o «próxima semana».

| Frente delegado | Trabajo ya preparado | Qué falta para cerrar la observación |
|---|---|---|
| 01 · Asin / instrumento | Núcleo U1/U2 de utilidad y C1/C2 de confianza percibida; intención opcional IU-O1; escala/anclajes propuestos, NE fuera de escala y tareas guiadas | Cotejar formulario real, resolver decisiones con asesor, fijar versión y aplicar con participantes reales |
| 02 · Neemias / métricas | Ficha de defensa y consulta; 10/10 matrices Tabla 7 y 5/5 Tabla 7c comprobadas; denominadores, unidades y α separados | Consulta al asesor y registro de cómo presentar el análisis; ninguna alteración del modelo o del test se da por aprobada |
| 03 · Neemias / metodología | Mapa de siete fases, doce artefactos/conectores propuestos y definición de CyberFlow para metodología/exposición | Confirmar el diagrama mostrado y su numeración, aplicar a las copias editoriales y revisar figuras al tamaño final |
| 04 · Neemias / validación | Guion de diez pasos, preflight, correspondencia ítems–evidencia, coordinación y rúbrica; mensaje listo pero no enviado | Confirmar personas, fecha, modalidad y evidencia disponible; realizar ensayo y sesión; obtener documento institucional cuando falte |

## Cómo usar el paquete ahora

### Paso 1 — Preparación paralela, ya avanzada

- Instrumento: usar `01-asin/PROPUESTA-INSTRUMENTO.md` como borrador, no como formulario aprobado.
- Consulta técnica: usar `02-metricas/CONSULTA-ASESOR.md` junto con la ficha de métricas.
- Diagramas: usar `03-metodologia/MAPA-FASES-Y-CONECTORES.md` para preparar la edición por fase; no confundir las etiquetas propuestas con documentos 1/2 identificados en el audio.
- Sesión: usar `04-validacion/GUION-DEMOSTRACION.md` y el mensaje de coordinación de `COORDINACION-Y-RUBRICA.md`.

**Estas preparaciones y la coordinación pueden avanzar en paralelo.** La grabación no establece una prohibición administrativa de preparar el TAM mientras se aclara α. Sí hace falta definir qué se mostrará y qué versión de instrumento se usará antes de recoger respuestas interpretables.

### Paso 2 — Resolver las decisiones concretas

Llevar al asesor la lista de `DECISIONES-PENDIENTES.md`, sin pedirle revisar un expediente desordenado:

1. Núcleo utilidad/confianza; intención opcional; escala, anclajes y NE.
2. Población y calibración que se presentarán como principales; significado de precisión, recall y α.
3. Denominación de CyberFlow y numeración editorial de fases/conectores.
4. Modalidad de exposición, comparación y evidencia que se pretende valorar.

Dejar registro de respuesta, fecha, versión y correcciones. No rellenar aprobación, nombre, número de expertos o puntajes por anticipado.

### Paso 3 — Aplicación editorial y ensayo

- Actualizar solo la versión de instrumento elegida y conservar el antecedente.
- En el guion, la matriz U1/U2/C1/C2 es la propuesta actual integrada. La matriz UP/FU/IU anterior está rotulada histórica; no se aplica por defecto ni se introduce facilidad de uso como dimensión aprobada para exposición única.
- La formación guiada, la observación de dificultades y las respuestas individuales son actividades distintas. Registrar ayudas y faltantes; NE no es un cero ni una respuesta negativa.
- Aplicar el mapa a figuras y manuscrito cuando corresponda y comprobar su legibilidad. En esta delegación no se editaron Word/PPTX ni se renderizaron diagramas nuevos.
- Ensayar con caso, intervalo, fuente y versión identificables; explicar hasta dónde existe evidencia. Publicar una acción no prueba que el host la haya aplicado.

Las referencias cruzadas entre N-04 y N-05 expresan coordinación entre guion e instrumento, **no un bloqueo circular**: primero se preparan ambos, luego se acuerda su correspondencia y se ejecuta la sesión.

### Paso 4 — Sesión real y cierre

Confirmar con Elías y participantes disponibilidad, cantidad, perfiles, modalidad y acceso. El borrador de mensaje está preparado, **no enviado**. Ejecutar la exposición y recoger respuestas reales. Conservar registro de qué evidencia pudo ver cada participante, versión y observaciones.

Después reconciliar manuscrito, figuras, resultados y límites; hacer lectura final y gestionar traducción de la versión identificada. Las dos semanas mencionadas en el audio no se convierten en fecha de entrega confirmada.

## Hallazgos técnicos que condicionan la demostración

- La campaña A del 29-oct tiene **25 episodios ejecutados y 0 evaluables**. Esto no significa 25 FN ni recall cero. No constituye una comparación válida de detección o rapidez.
- La equivalencia de `build_rows` en **773/773 ciclos** es una comprobación offline. No acredita despliegue ni mejora de latencia en vivo y no recupera la evaluabilidad de aquella campaña. La inundación HTTP sigue señalada como limitación en la investigación.
- El replay histórico 9/9 admitía señales hasta fin+60 s. No se reutiliza como si cumpliese la regla reciente de detección durante el ataque.
- En la evidencia de campaña A el agente estaba desactivado y se trabajó en sombra. Un antecedente de BLOCK de otra fecha no acredita aplicación en esa ejecución.
- La comparación 4.1 es por ventana y reutiliza evaluación; 54/84 es recall, no precisión. α es un cuantil de validación, no el nivel de significancia de una prueba estadística. No balancear el test ni cambiar denominadores para elevar cifras.
- El cuestionario recoge percepción, no demuestra exactitud del detector ni fiabilidad psicométrica por sí mismo.

Estas delimitaciones ya están incorporadas a las fichas y al guion. No se ejecutaron nuevas campañas, reentrenamientos ni cambios de infraestructura.

## Trazabilidad y estado local

`TAREAS.csv` y `TAREAS.json` consolidan **15 observaciones primarias y nueve subtareas metodológicas**, cada una con fuente, avance, dependencia y criterio de cierre. Los CSV de cada frente conservan el detalle original. `consolidar.py` valida IDs, campos y referencias locales, y genera el índice y los hashes de este paquete.

La auditoría local de GUI/TAM en `03-entregables/14-auditoria-gui-tam` se consultó como antecedente; no se modifica ni se certifica como despliegue. Se observó trabajo concurrente en el producto (`dashboard.py` modificado sobre `main@7b275b8`); el estado vivo requiere una comprobación distinta.

Los entregables de esta carpeta quedan **locales, sin commit ni push** en esta tarea. No se envían mensajes a terceros ni se publican transcripciones completas. La revisión independiente solicitada fue interrumpida; no se presenta como una revisión aprobada. Sí se revisaron las entregas y se integró expresamente el guion con la propuesta del frente Asin.
