# Cierre verificable de pendientes — 23 de octubre de 2026

## Trabajo ejecutado

1. Corregidas las regresiones del merge de historiales: agente de enforcement sin vaciar sets, caducidad conservada, reincidencia por episodio, partición con intervalos, puntuador compatible y pruebas autenticadas aisladas del perfil de despliegue.
2. Restituida la cadena de timers a 10 s (:00/:03/:06) y el contrato `.gitattributes` que preserva los hashes de los datasets publicados.
3. Suite completa en Linux: CPython 3.14.4, scikit-learn 1.9.0, **443 pruebas sin fallos ni errores, una omitida**. Tras la corrección del panel: 35 pruebas de dashboard (una omitida) y 11 de autenticación E2E aprobadas. El CI remoto se registra en el manifiesto de este cierre.
4. Panel alineado con Tabla 6/7 y límites de 4.1: IF limpio, precisión 1,79 %, FPR 4,53 %, recall 54/84; retirada Det@FPR5% calculada sobre test; ablación del predecesor identificada como histórica.
5. Word publicado como **borrador revisado de 4.1**, con resumen corregido, notas en tablas 3/5, explicación de Eq. 7 restaurada, definiciones de Eq. 8 reubicadas, tablas 6/7 y figura. Sensibilidad y auditoría de ventanas sin actividad incorporadas. Validación OOXML aprobada y renderización con LibreOffice.
6. Sensor1 comprobado por SSH en solo lectura: motor, panel y publicador activos; IF limpio en los units y modelo con SHA-256 `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60`. Evidencia en `VERIFICACION-SENSOR-2026-10-23.txt`. No se actualizó el código desplegado.
7. Replay **realmente ejecutado** en la comparadora, sin sudo, sobre el PCAP archivado de 9 470 paquetes. Suricata 7.0.3 cargó 53 013 reglas ET Open, cero fallidas. Resultado: **55 alertas: 54 STREAM y una ET INFO por curl**, no detección confirmada de flood. EVE, log, resumen y hashes están en `seccion4-resultados/_campana/resultados-2026-10-23/replay43/etopen-20261023/`.
8. `PENDIENTES.md`, `ESTADO.md` y el plan de observaciones tienen un corte vigente que sustituye estados históricos.

## Entregables principales (rutas absolutas)

- Word: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\Articulo-IJIES-espanol_MARK_4.1-revisado.docx`
- PDF de revisión: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\Articulo-IJIES-espanol_MARK_4.1-revisado.pdf`
- Pendientes vigentes: `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\PENDIENTES.md`
- Todas las rutas creadas/modificadas y sus hashes se enumeran en `MANIFIESTO-CIERRE-PENDIENTES-2026-10-23.json` (campo `files`, rutas absolutas). No se enumeran archivos temporales de previsualización como entregables.

## Lo que sigue abierto

- Campaña final N≥3 consistente (escaneo con camino abierto y volumen HTTP suficiente), Nikto incluido dentro de captura. El runbook estima 90–110 min; **no se ejecutó una nueva batería en este cierre**.
- Tabla 9 final por episodio; declarar criterio para alertas STREAM/INFO y el alcance de HOME_NET. La falta de ejecución de ET Open sobre el PCAP archivado sí queda cerrada.
- Tiempos t0–t5, verificación de caducidad/reversión y figura de evidencia para el modelo limpio.
- Despliegue de los últimos cambios de código con verificación de hashes y rollback. Git y servicios remotos son estados distintos.
- QA visual en Sensor1 por rol; el E2E automatizado no sustituye capturas fechadas de la VM.
- Completar artículo: título/alcance, 4.2–4.4, conclusiones y consolidación de las dos listas de referencias heredadas. La copia Word no se declara lista para enviar.
- Bibliografía del procedimiento α, auditoría cuantitativa F7, datos independientes para reentrenamiento y test ciego.
- TAM y juicio de expertos con respuestas reales; DOI y cierre de credenciales cuando corresponda.

No se reentrenó ni se promocionó un modelo, ni se generaron respuestas de validadores o resultados de campañas no ejecutadas.
