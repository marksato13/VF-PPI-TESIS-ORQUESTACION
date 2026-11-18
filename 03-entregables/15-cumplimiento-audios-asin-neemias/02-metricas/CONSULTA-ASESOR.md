# Consulta técnica al asesor — N-01 / N-02

**Estado:** preparada, no enviada ni aprobada. Corte: 31-oct-2026, HEAD documental `1e378d2c1917adb1c530b83f82c1d693c310b4ac`. Persona a consultar: asesor/profesor; el nombre «Ferdinand» requiere confirmación. Responsable y fecha límite no asignados expresamente en el audio.

## Hechos para abrir la consulta

- La unidad de 4.1 es ventana de 10 s por entidad: 65 421 normales + 84 ataques. TP/84 es recall, no precisión. Con IF analítico 0,03: TP=54, FP=1 723, precisión=3,04 %, recall=64,29 %, FPR=2,63 %.
- El operativo documentado usa α=0,05 sobre 65 633 ventanas; la comparación analítica usa 65 553. α designa un cuantil de validación, no una prueba de significancia. La selección de 0,03 es posterior a examinar la evaluación.
- Campaña A del 29-oct: 25 episodios ejecutados y cero evaluables. Las 773/773 equivalencias de `build_rows` son comprobaciones offline; no validan detección ni un despliegue nuevo.
- El replay de nueve episodios admitía señal hasta fin+60 s. La regla reciente exige detección durante y cobertura; no se puede trasladar su 9/9 como resultado actual bajo el criterio nuevo.

## Preguntas breves y resolubles

1. **N-01, presentación:** ¿aceptamos presentar precisión, recall y FPR juntas, todas en %, con matriz y denominadores explícitos, conservando las cifras bajas? «En función de los 84» quedaría rotulado como recall. La definición matemática no requiere redefinirse; se consulta su presentación.
2. **N-01, población:** ¿cómo documentar la normalidad no confirmada de las 74 ventanas Kali del test y las 80 de validación? **Propuesta:** mantener la evaluación canónica y sus límites; cualquier revisión de etiquetas o sensibilidad se acuerda con criterio explícito y se informa por separado. No se propone rebalancear retrospectivamente el test.
3. **N-02, fila principal:** ¿la exposición mostrará como referencia operativa α=0,05/65 633 y, aparte, la comparación analítica α=0,05/65 553? **Propuesta:** distinguir ambas y conservar 0,03 y 0,01 como sensibilidades; no llamarlos configuraciones aprobadas ni óptimos.
4. **N-02, criterio de elección:** ¿qué coste tolerable de FP/FN y qué población objetivo justificarían una selección futura? **Propuesta:** fijar el criterio antes de otra evaluación; no elegir por la cifra más alta de precisión. El control de A informa falsas alarmas, pero no el lado de detección.
5. **Incertidumbre:** ¿se necesita una estimación adicional para la defensa? **Propuesta sujeta a acuerdo:** definir primero unidad de remuestreo y dependencia temporal; no tratar automáticamente 84 ventanas como 84 episodios independientes ni declarar significancia usando α del cuantil.
6. **Evidencia operativa:** ¿se acepta informar A como 0/25 evaluables, conservando la descripción complementaria, y reservar cualquier validación de detección para un protocolo futuro? Una eventual corrección del motor, cambio prospectivo de tolerancia o campaña requerirá decisión separada; la equivalencia 773/773 no autoriza esas acciones.

## Cuadro de decisiones pendientes

| Asunto | Evidencia comprobada | Propuesta para resolver la consulta | Decisión pendiente / quién decide | Criterio de cierre |
|---|---|---|---|---|
| N-01: denominadores y forma de análisis | CSV/JSON concordantes; 54/84=64,29 % recall, 54/1 777=3,04 % precisión | Mostrar matriz y tres métricas en % con límites | Método de presentación aceptado por asesor y autores; sin aprobación registrada | Respuesta identificable con presentación/método aceptado y referencia de población |
| N-01: datos y desbalance | Test canónico no balanceado; normalidad de 74 ventanas incierta | Conservar resultados; documentar incertidumbre; revisión de etiquetas solo si se acuerda | Alcance de revisión y evidencia necesaria, asesor/autores | Criterio y respuesta registrados; si hay análisis nuevo, protocolo y versión separados |
| N-02: calibración principal | Operativa 65 633 frente a analítica 65 553 | Diferenciar filas; 0,03/0,01 como sensibilidades | Qué fila será principal en defensa, asesor/autores | α, población, umbral, motivo y carácter original/posterior documentados |
| N-02: elección futura | Menos FP con α menor; con 0,01 se pierden cuatro TP frente a 0,03 en referencia | Preregistrar compromiso FP/FN; ninguna recomendación de despliegue automática | Criterio de aceptación futuro, asesor/autores | Acuerdo explícito previo a selección; no confundirlo con autorización operativa |
| A y regla durante | 25 ejecutados, 0 evaluables; 773/773 offline; inundación aún sobre límite estimado | Informar n/a; no rescatar episodios cambiando criterio después | Corrección, tolerancia futura o repetición: Mark; validez metodológica: asesor/autores | Decisión separada y, si se autoriza otra evaluación, evidencia nueva suficiente |
| Cambio de modelo/balanceo/reentrenamiento | Audio los plantea, no los aprueba | Tratar como posibilidades para discutir, sin ejecución | Necesidad y diseño de experimento: asesor/autores; ejecución requiere autorización de Mark | Autorización y protocolo explícitos; no es requisito tácito para cerrar esta revisión |

No hay decisión técnica final nueva en este documento. Los nombres de responsables anteriores describen ámbitos de decisión para la consulta, no asignaciones aprobadas en el audio. Fecha de consulta: pendiente; respuesta: pendiente.

## Material de apoyo y fuentes

Ficha completa con índice de rutas S01–S12, commits, hashes, fórmulas y límites:

`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\15-cumplimiento-audios-asin-neemias\02-metricas\FICHA-METRICAS-Y-ALFA.md`

Fuente de la petición: `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\ANALISIS-NEEMIAS-MEDIUM.md`, N-01 N2 00:01:43–00:04:34 y N-02 N2 00:12:51–00:14:02. TXT cotejado: `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\WhatsApp Ptt 2026-10-28 at 3.59.06 PM.txt`.

Evidencia principal de cálculo: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\TABLA7-comparacion-completa.csv`, commit `028de214fb2ddc809f6eb4876574ada647b3dafb`.

Evidencia posterior: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\INFORME-CAMPANA-A-2026-10-29.md`, commit `e06805af03282b447cee620b84c240bd4c2fb493`; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\investigacion-ciclos-motor\INVESTIGACION-CICLOS-MOTOR.md`, validación pendientes `9a5577ad93217b85d48218552b6cbbe34852b594`, manifiesto HEAD `1e378d2c1917adb1c530b83f82c1d693c310b4ac`.
