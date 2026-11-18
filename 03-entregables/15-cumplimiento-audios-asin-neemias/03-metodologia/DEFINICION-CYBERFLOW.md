# Definición propuesta de CyberFlow — N-06

**Estado:** propuesta de redacción, no manuscrito aplicado. Corte documental 31-oct-2026. Revisión local de producto `main@7b275b8bab1c8343e55f40a103ee980dc497620b` y documentación `1e378d2c1917adb1c530b83f82c1d693c310b4ac`. La operación se describe con evidencia archivada fechada; no se certifica el estado remoto de hoy.

## 1. Bloque breve propuesto para metodología

> **CyberFlow** es el nombre del producto desarrollado y del marco metodológico implementado para observar comportamientos anómalos en una red de datos y vincular su detección con una política de respuesta distribuida. En el despliegue documentado, el sensor recibe una copia pasiva del tráfico mediante SPAN y utiliza capturas PCAP y eventos de aplicación de Suricata para construir variables por IP iniciadora y fin de ventana. El contrato de puntuación comprende 28 variables L3/L4/L7 con horizontes de 10, 30 y 60 segundos. La detección integra la puntuación de un modelo Isolation Forest congelado con heurísticos deterministas; el publicador deriva las acciones PERMIT, LIMIT o BLOCK según las señales, las exclusiones y la política de caducidad. Las acciones que corresponden se distribuyen mediante un feed firmado, que un agente del host protegido verifica antes de aplicar reglas nftables. Por tanto, el sensor SPAN observa y el host protegido es el punto de aplicación. El aporte de la propuesta es la integración y trazabilidad de adquisición, preprocesamiento, detección, decisión, respuesta y evaluación en el entorno estudiado; no la creación de un algoritmo nuevo de aprendizaje automático. La aplicación efectiva de una respuesta debe comprobarse en el host y no se deduce únicamente de una alerta o de la publicación del feed.

Ubicación sugerida: inicio de la sección metodológica, antes de desarrollar las fases. La identificación concreta del IF y su calibración se explica en F3; configuración y versiones, en F6; resultados y madurez de la respuesta, en evaluación/resultados. No cargar la definición con métricas de distintas campañas.

### Frase de alcance para acompañar el bloque

> La evaluación distingue capacidad implementada, configuración desplegada y resultado observado. La campaña A del 29 de octubre de 2026 se realizó en modo sombra con el agente de respuesta desactivado, y sus 25 episodios no superaron los criterios de continuidad para la comparación de detección; esto no elimina la implementación de respuesta ni constituye una validación de su eficacia en esa campaña.

## 2. Versión breve para exposición

> CyberFlow es nuestro producto y marco de trabajo para conectar observación de red, detección y respuesta verificable. El sensor observa una copia SPAN; combina un Isolation Forest con reglas explícitas y publica las respuestas mediante un feed firmado. La limitación o el bloqueo se aplican en el host protegido, no sobre el tráfico copiado en el sensor. Nuestro aporte está en integrar y evaluar esa cadena en el entorno estudiado, no en inventar un algoritmo de aprendizaje. Una alerta, una acción publicada y una acción aplicada son evidencias diferentes.

Si se muestra la campaña A, añadir oralmente: «Esta ejecución fue en sombra; sus episodios no fueron evaluables con el criterio de continuidad establecido. No la presentamos como una demostración de bloqueo».

## 3. Producto, método y framework: precisión terminológica

| Término | Uso defendible | Límite |
|---|---|---|
| Producto | Implementación concreta: captura, extractor, motor, publicador, agente y observabilidad | No equivale a plataforma universal lista para cualquier red o protocolo. |
| Método / marco metodológico implementado | Procedimiento documentado para construir variables, calibrar/evaluar, integrar señales y trazar respuesta | No significa un algoritmo matemático nuevo; el nombre no prueba novedad científica por sí mismo. |
| Framework | Puede emplearse como «marco de integración y procedimiento implementado» si el autor lo define así | No afirmar arquitectura de plugins, sustitución arbitraria de modelos ni compatibilidad automática: no se verificaron. |
| Híbrido | Coexistencia de modelo de anomalía y reglas complementarias explícitas | No prueba que el híbrido siempre mejore recall/FPR ni que las reglas sean aprendidas. |
| Detección | Score y señales registradas por entidad/ventana | Anomalía no equivale a ataque confirmado. |
| Decisión de respuesta | Política que deriva acción, severidad, exclusiones y caducidad | No toda decisión ALERT acaba en una acción publicada; no confundir PERMIT del registro con ausencia de regla aditiva. |
| Aplicación | Consumo/verificación y modificación efectiva en el host | Feed o GUI no acreditan por sí solos el estado nftables remoto. |

## 4. Trazabilidad de cada afirmación

| Afirmación del bloque | Fuente absoluta y líneas | Fuerza y alcance de evidencia |
|---|---|---|
| El nombre corresponde al producto y debe explicarse en metodología | `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\WhatsApp Ptt 2026-10-28 at 3.59.06 PM.txt`, 535–559, N2 19:45–20:40 | Petición oral explícita; «framework/método» es denominación discutida, no validación de algoritmo nuevo. |
| Sensor pasivo SPAN; aplicación distribuida en host | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\docs\FICHA-TECNICA-DESPLIEGUE-VIGENTE.md`, 32–41 | Arquitectura documentada; la modalidad inline es histórica. |
| Perfil local declara IF limpio y fuentes/rutas de despliegue | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\configs\cyberflow.local.toml`, 16–37, 69–102 | Configuración inspeccionada; manifiesto/joblib referenciados no presentes en esa ruta local. No sustituye verificación remota. |
| 28 variables, IP iniciadora, causalidad y 10/30/60 s | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\configs\features\multilayer-v2.json`, 2–35 | Contrato verificable. No atribuye scoring de L2/IPv6. |
| PCAP/EVE se transforman en filas y se comprueba disponibilidad | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\motor_decision.py`, 503–579 | Implementación de filtrado, dedup, atribución y guarda. |
| Puntuación y heurísticos son señales distintas | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\motor_decision.py`, 614–688 | IF con `score_samples`; modelo no puntuado sin paquetes L3/L4 puede coexistir con señal L7; el campo de reglas es aditivo. |
| Reglas explícitas, no algoritmo aprendido nuevo | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\heuristicos.py`, 2–21, 28–78, 148–165 | Umbrales por criterio razonado y versión; no calibración estadística de esos heurísticos. |
| Política de respuesta y feed firmado | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\publicar_feed.py`, 42–105, 125–174 | Deriva LIMIT/BLOCK, lista protegida, agregación por IP, escalada y firma. PERMIT sin señal no crea entrada. |
| Aplicación en nftables exige agente y modo de aplicación | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\enforce\agente_enforce.py`, 49–51, 81–129, 172–221 | Verificación, reglas y dry-run/aplicación diferenciados. No confirma un host activo hoy. |
| Modelo congelado del corte y evaluación no independiente | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\NOTA-COMPARACION.md`, 3–23, 29–47, 90–95 | IF limpio no reentrenado en esa comparación; cinco métodos offline sobre datos conocidos. No acredita modelo intercambiable. |
| Aporte de integración y trazabilidad | Fuentes de captura/contrato/motor/publicador/agente anteriores; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\INFORME-CAMPANA-A-2026-10-29.md`, 29–35, 181–195, 251–263 | Síntesis técnica propuesta basada en componentes y evidencias existentes. No es una prueba bibliográfica de originalidad universal. |
| Campaña A en sombra, 0/25 evaluables y agente detenido | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\INFORME-CAMPANA-A-2026-10-29.md`, 3–9, 78–87, 222–249 | Evidencia archivada de ese ensayo; n/a no significa cero detecciones ni 25 FN. |
| Feed/panel no equivalen a aplicación remota acreditada | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\14-auditoria-gui-tam\01-hallazgos-agentes\HALLAZGOS-A-UTILIDAD.md`, 3, 30–35, 54–58 | Auditoría ajena estática, leída como advertencia de trazabilidad; no prueba de una GUI remota corregida. |

## 5. Afirmaciones que esta definición no debe incorporar

- **«Nuevo algoritmo» / «el único sistema que responde»:** se integran técnicas conocidas; no se realizó demostración de prioridad científica. Los textos de fases que comparan quince artículos no bastan para esa afirmación universal.
- **«Aprende y se actualiza automáticamente»:** hay procedimiento de preparación/evaluación de candidatos con promoción humana, no autodespliegue. Fuente: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\docs\APRENDIZAJE.md`, líneas 3–5, 80–106. La configuración `activo=true` no acredita ejecuciones nocturnas efectivas.
- **«Se puede cambiar cualquier modelo sin adaptación»:** una comparación offline de IF/OCSVM/LOF/EE/PCA no demuestra contrato universal de sustitución en el motor. Antes se deben verificar escala, esquema, manifiesto, calibración y equivalencia.
- **«Detecta mejor que Suricata / 9 de 9»:** no pertenece a la definición. El antecedente y el recálculo usan versiones/configuraciones diferentes y datos reutilizados. Fuente: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\NOTA-APORTE-COMPONENTES.md`, líneas 7–9, 27–37, 62–100.
- **«El híbrido necesita necesariamente ambos componentes para todos los episodios»:** la coexistencia técnica no demuestra beneficio incremental general. Evaluar IF, reglas y combinación con poblaciones y versiones declaradas.
- **«El sensor bloquea en línea» / «bloquea en pfSense»:** el corte descrito es sensor SPAN y agente nftables en host. No extrapolar al perímetro ni al laboratorio inline.
- **«Todos los protocolos/capas están cubiertos»:** el contrato de scoring es L3/L4/L7; no afirmar inspección IPv6/L2 en el modelo ni visibilidad de contenido cifrado que no esté documentada.
- **«Validación externa terminada»:** contar con instrumentos no son respuestas TAM. Fuente: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\PENDIENTES.md`, líneas 35–37.

## 6. Decisiones editoriales y verificaciones restantes

1. Aprobar «producto y marco metodológico implementado» o definir expresamente el sentido restringido de framework; confirmar consistencia con título y objetivo del artículo.
2. Incorporar la definición y las siete láminas en el manuscrito autorizado; esta tarea solo entrega el texto propuesto y la especificación de continuidad.
3. Mantener separados construcción offline, inferencia, derivación de respuesta y aplicación. La lámina metodológica general no debe parecer una cadena donde la evaluación experimental produce la orden de bloqueo.
4. Fijar fecha/versión y modo de la demostración. El último corte operativo leído conserva sombra; una capacidad implementada no es estado activo demostrado hoy.
5. La investigación posterior validó variantes de extracción en 773/773 ciclos offline, sin despliegue ni solución completa a inundación. Fuente: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\investigacion-ciclos-motor\INVESTIGACION-CICLOS-MOTOR.md`, líneas 162–241. No presentarlas como optimizaciones ya operativas.

Responsable nominal y plazo de cierre: no fijados en el audio. Se requiere decisión del autor/asesor; no se inventan acuerdos.
