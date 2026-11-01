# Diseño de la validación independiente (versión 3)

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
| 2 | **Mejora de heurísticos**: escaneo breve temprano, atribución DNS al cliente, separación del abuso HTTP; política `if_senal` (D3, adoptada) | 3 | Paso 1 (los datos de entrada de las reglas dependen de la captura) | Reglas nuevas con sus umbrales **escritos antes** de probarlas; casos de atribución errónea del 3B convertidos en regresiones | Una mejora necesita la IP, los horarios o los identificadores del generador | Rama candidata |
| 3 | **Pruebas offline y regresiones por cambio** | 2–3 | Pasos 1 y 2 | Por cada cambio: prueba unitaria, regresión con los casos del 3B y comparación de las 28 características. Simulador actualizado con el código candidato. **Ninguna cifra se presenta como validación.** | Una regresión empeora otra familia | Revertir el commit |
| 4 | **Congelación de la candidata** | fin de la 3 | D1 con sus comprobaciones técnicas hechas; D3 implementada; valores de LIMIT de D6 confirmados; D5, D7 y D8 confirmadas | Commit y hashes de cada fichero, umbrales, α (si interviene), protocolo de evaluación **congelado** y fechado | Falta una decisión esencial | — |
| 5 | **Tráfico normal nuevo y campaña A nueva, en sombra** | 4 | Candidata instalada en sombra con el procedimiento del paso 2 (decisión y sudo de Mark) | Control ≥ 2 h (P1–P5 con M3 hipotética); **25 episodios** con una semilla nueva publicada antes; E1 por episodio; clases C0–C3; planificados, ejecutados, admitidos y excluidos | Más de 20 % de los ejecutados en C2 o C3: el problema es de captura y se vuelve al paso 1 (parada por evidencia, no por resultado) | Retirar la candidata y volver al motor desplegado |
| 6 | **Campaña B de respuesta** | 5 | Paso 5 publicado. Agente (o agentes, por D1) instrumentado y **autorizado** por Mark. Limpieza D5 probada. | **25 episodios**; E1–E5 por episodio; M3 y M4 reales; intentos del generador después del corte | Cualquier BLOCK a un legítimo o a la gestión, una regla sin caducidad o una restricción fuera del origen: retirar las reglas y volver a sombra | Desactivar los timers de los agentes; `nft delete table inet cyberflow` (srv-dmz) y `nft delete table inet cyberflow_dns` (DC1) (sudo de Mark) |

## Trabajo offline de la Etapa 2, en orden

Todo se hace en la **rama candidata** o en herramientas de análisis, sin desplegar, sin tocar hosts y sin generar tráfico. Ningún punto espera a DC1, salvo los marcados con «D1».

| # | Trabajo | Entregable | Depende de | Criterio de terminado |
|---|---|---|---|---|
| 1 | **Diagnóstico de los descartes de Suricata**: correlacionar los 21 intervalos con `kernel_drops` del 3B (`revision-3b/diagnosticos/suricata-descartes.json`) con CPU, hilos, ring de af-packet y tipo de tráfico | informe + configuración propuesta (aplicarla la autoriza Mark) | — | causa con evidencia, o lista de hipótesis descartadas |
| 2 | **Prototipo de captura más rápida y evaluación por eventos**: lectura incremental del PCAP (o rotación corta) con la misma regla de «paquetes decodificados», y ciclo por eventos (inotify) | prototipo + replay sobre los PCAP del 3B | — | las **28 entradas del IF** coinciden en las **mismas ventanas y con los mismos datos disponibles**; las diferencias, explicadas (OBJETIVOS §6.2) |
| 3 | **Instrumentación** de publicación, distribución y aplicación (D7): t_pub, t_relay, t_apl (commit nft, código de retorno, relectura del set) y `counter`, para el agente de srv-dmz y el de DC1 | código + pruebas unitarias | — | el registro permite calcular E2 sin inferencias |
| 4 | **Presupuesto completo del escaneo breve** con 2 y 3: tiempo hasta la evidencia suficiente, hasta t_det y hasta t_apl estimada, por episodio | tabla por tramos | 2, 3 | se separa lo que aporta la captura de lo que debe aportar la regla (Etapa 3) |
| 5 | **Regresiones de atribución**: DNS atribuido al cliente (el resolvedor no hereda las señales) y separación del abuso HTTP del escaneo (`brute_force` en escaneos, `port_scan` en la inundación); los casos del 3B se convierten en pruebas | casos de regresión que hoy fallan | — | cada error de atribución del 3B tiene su prueba |
| 6 | **Limpieza D5 ensayada en seco**: procedimiento y herramienta de verificación sobre **copias** del estado de escalada y de los sets (srv-dmz y DC1) | procedimiento + salida del ensayo | — | retira solo 10.10.20.30 y conserva copias con hash |
| 7 | D1 · **ensayo del conjunto de reglas nft de DC1 fuera de DC1** (espacio de nombres de red o VM Debian 13, nft 1.1.3): denegar y limitar por origen solo en el puerto 53, `timeout`, contadores y relectura | guion + salida | — | el DNS deja de responder solo al origen del set |
| 8 | D1 · **agente de DC1 en la rama candidata**: filtro por `alcance = "dns"`, plan nft de [D1-VIABILIDAD-DC1.md](D1-VIABILIDAD-DC1.md) §3, registro D7; cambio del publicador (`alcance` por regla, 10.10.10.21 en NUNCA_BLOQUEAR) | código + pruebas del plan (sin ejecutar nft) | 7 | pruebas unitarias en verde |
| 9 | D3 · **`if_senal` en el publicador** de la rama candidata (Etapa 3, puede empezar ya) | código + pruebas de equivalencia con el simulador | — | el feed candidato no contiene LIMIT «modelo:» |

**Regla de equivalencia (2 y 9):**

- **Conservar** las 28 entradas del IF significa misma extracción con los mismos datos.
- **Añadir** señales heurísticas tempranas (Etapa 3) es una mejora deliberada: se exige que sean correctas y sin regresiones, **no** idénticas a las antiguas.
- Las 3 características L2 del esquema ampliado no se incorporan.

**Dependencias reales:**

- 4 depende de 2 y 3; 8 depende de 7.
- La instalación en DC1 depende de la autorización de Mark.
- La congelación depende de D1 (comprobaciones técnicas), D3 (implementada) y D6 (valores de LIMIT confirmados).
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
