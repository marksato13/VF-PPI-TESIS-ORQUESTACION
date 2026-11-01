# Diseño de la validación independiente (versión 2)

**Principio:**

- Los registros anteriores (paso 2, 3A, 3B, su revisión y esta simulación) sirven para **desarrollo**. **No** son prueba independiente de una candidata ajustada con ellos.
- La prueba se hace con **tráfico normal nuevo** y **dos campañas nuevas de 25 episodios cada una** (5 por escenario, [D4](DECISIONES.md)) con la candidata congelada.

**Reglas de todas las etapas:**

- No se cambian criterios para aprobar.
- Los fallos del experimento y los del detector se tratan según [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) §5.
- Ningún despliegue, sudo ni cambio en hosts sin decisión de Mark. Los comandos con sudo los prepara Claude y los ejecuta Mark.

## Recorrido

| # | Paso | Etapa | Entrada | Salida | Parada | Reversión |
|---|---|---|---|---|---|---|
| 1 | **Diagnóstico y desarrollo de mejoras de captura y cadena** | 2 | Etapa 1 publicada | Causa de los `kernel_drops` identificada con evidencia y propuesta de configuración. Prototipo offline de captura incremental y cadena por eventos. Instrumentación (D7) en la rama candidata. Presupuesto **por episodio** recalculado con los PCAP del 3B. | El prototipo rompe la equivalencia de las 28 características o de las decisiones | Rama candidata; nada desplegado |
| 2 | **Mejora de heurísticos**: escaneo breve temprano, atribución DNS al cliente, separación del abuso HTTP; política del IF (D3) | 3 | Paso 1 (los datos de entrada de las reglas dependen de la captura) | Reglas nuevas con sus umbrales **escritos antes** de probarlas; casos de atribución errónea del 3B convertidos en regresiones | Una mejora necesita la IP, los horarios o los identificadores del generador | Rama candidata |
| 3 | **Pruebas offline y regresiones por cambio** | 2–3 | Pasos 1 y 2 | Por cada cambio: prueba unitaria, regresión con los casos del 3B y comparación de las 28 características. Simulador actualizado con el código candidato. **Ninguna cifra se presenta como validación.** | Una regresión empeora otra familia | Revertir el commit |
| 4 | **Congelación de la candidata** | fin de la 3 | D1, D3 y D6 resueltas; D5, D7 y D8 confirmadas | Commit y hashes de cada fichero, umbrales, α (si interviene), protocolo de evaluación **congelado** y fechado | Falta una decisión esencial | — |
| 5 | **Tráfico normal nuevo y campaña A nueva, en sombra** | 4 | Candidata instalada en sombra con el procedimiento del paso 2 (decisión y sudo de Mark) | Control ≥ 2 h (P1–P5 con M3 hipotética); **25 episodios** con una semilla nueva publicada antes; E1 por episodio; clases C0–C3; planificados, ejecutados, admitidos y excluidos | Más de 20 % de los ejecutados en C2 o C3: el problema es de captura y se vuelve al paso 1 (parada por evidencia, no por resultado) | Retirar la candidata y volver al motor desplegado |
| 6 | **Campaña B de respuesta** | 5 | Paso 5 publicado. Agente (o agentes, por D1) instrumentado y **autorizado** por Mark. Limpieza D5 probada. | **25 episodios**; E1–E5 por episodio; M3 y M4 reales; intentos del generador después del corte | Cualquier BLOCK a un legítimo o a la gestión, una regla sin caducidad o una restricción fuera del origen: retirar las reglas y volver a sombra | Desactivar el timer del agente, `nft delete table inet cyberflow` y retirar la política de DC1 (sudo y administración de Mark) |

## Trabajo offline que puede empezar ya en la Etapa 2 (sin esperar D1, D3 ni D6)

Todo se hace en la **rama candidata** o en herramientas de análisis, sin desplegar nada.

| Trabajo | Depende de | Por qué no espera |
|---|---|---|
| a. Correlacionar los `kernel_drops` (21 intervalos del 3B, `revision-3b/diagnosticos/suricata-descartes.json`) con CPU, hilos, ring de af-packet y tipo de tráfico; proponer la configuración | — | Diagnóstico sobre datos existentes. **Aplicar** la configuración sí requiere a Mark. |
| b. Prototipo de **lectura incremental del PCAP** (o rotación corta) con la misma regla de «paquetes decodificados», y ciclo por eventos (inotify); replay sobre los PCAP del 3B comparando las **28 características** y las decisiones | — | Es la base temporal de todo lo demás |
| c. **Cadena por eventos** (publicación → distribución → aplicación) e **instrumentación** de t_pub, t_relay, t_apl y `counter` (D7, solo código y pruebas unitarias) | — | Preparar no es activar; el agente sigue inactivo |
| d. Medir con b y c el tiempo **hasta la evidencia suficiente** y hasta `t_apl_estimada` por episodio para el escaneo breve, con la regla actual, para separar lo que aporta la captura de lo que debe aportar la regla | b, c | Cuantifica el reparto entre la Etapa 2 y la 3 |
| e. Diseño y pruebas unitarias de la **regla temprana de escaneo** (decisión al cruzar el umbral con evidencia parcial) | b (para el replay realista); el diseño puede empezar ya | El objetivo está decidido (D2) |
| f. **Atribución DNS al cliente** (el resolvedor no debe heredar las señales) y **separación del abuso HTTP del escaneo**, con regresiones de los casos del 3B | — | No dependen de D1 ni de D3 |
| g. Procedimiento escrito de **limpieza verificada** del origen (D5), ensayado **en seco** sobre copias del estado | — | Solo documentación y herramienta de verificación |
| h. Esbozo técnico del agente de DC1 (D1, opción A1) **solo como análisis**: verificación de firma, alta y baja de la política, registro de t_apl | **D1** para implementarlo | Un análisis no compromete el alcance |

**Dependencias reales:**

- e depende de b para el replay temporal realista.
- d depende de b y c.
- La implementación del agente de DC1 depende de D1.
- Aplicar la política del IF en la candidata depende de D3.
- Fijar el presupuesto de falsas alarmas para congelar depende de D6.
- Nada se despliega sin Mark.

## Separación entre las campañas

| | Campaña A (paso 5) | Campaña B (paso 6) |
|---|---|---|
| Episodios | 25 (5 × 5) | 25 (5 × 5) |
| Agente | inactivo | activo (autorizado) |
| Responde a | E1: detectores comparados (IF a cada α, heurísticos, híbrido) con el ataque completo | E1–E5: aplicación, efecto, tráfico legítimo, retirada |
| Ventanas tras la señal | se usan | solo hasta t_apl para la detección; después, solo para el efecto |
| Falsas alarmas | M1, M2 medidas; M3 hipotética | M3, M4 medidas |
| Sustituye a la otra | no | no |
