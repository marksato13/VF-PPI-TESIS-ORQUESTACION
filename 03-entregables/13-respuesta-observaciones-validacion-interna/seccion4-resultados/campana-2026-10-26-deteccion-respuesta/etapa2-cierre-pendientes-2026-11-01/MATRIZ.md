# Matriz de los dos pendientes del cierre técnico

**Código:** rama `candidato/etapa2-20261101`, desde `953a436` hasta `6b6ef82`:

- `862404e`: corrección de las pendientes;
- `4694e38`: arnés de medición;
- `6b6ef82`: optimización.

**Estados:**

- **Resuelto offline:** hay corrección, prueba y evidencia de replay sobre las entradas congeladas.
- **Pendiente en Sensor1:** solo se puede comprobar en vivo, y este encargo no permite instalar nada.
- **Etapa 3:** fuera del alcance.

| # | Pendiente | Causa | Corrección | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|---|
| P1 | 14 `ventana_no_regenerada` | Pendientes dadas de alta con la atribución de la última ancla. En el horizonte propio, el flujo cambia de propietario y E no tiene contenido en (A − 60, A]: no son registrables | `pendiente_cancelada` (motivo `sin_contenido_en_su_horizonte`, con evidencia); `ventana_no_evaluada` explícita para las registrables no decidibles (`fila_no_generada`, `no_elegible`) | `ContabilidadPendientes` (cambio de atribución, límites temporales, ventanas sin actividad reciente; 2 configuraciones), `ResolucionPendientesUnidad`, `ExtremoAExtremo`. Fallan sobre `953a436` (4 fallos) | `DIAGNOSTICO-14-VENTANAS.md`: recálculo independiente de las 14, las 14 son no registrables y el motor coincide en las 14. Completo: 14 → canceladas, 0 vectores, scores ni decisiones distintos | **Resuelto offline** |
| P1a | Ventanas registrables que no se podían decidir y se omitían en silencio | Una observación justo en la ancla no genera la fila; ventanas no elegibles | Registro inmediato como `ventana_no_evaluada` con motivo | Regresión con paquetes justo en la retícula | 33 `no_elegible` de arranque (07:21), explícitas | **Resuelto offline** |
| P1b | Paquetes que pasan a propietarios excluidos (10.10.60.10) | Atribución congelada + lista de exclusión | No se cambia | — | 5 de los 14 casos, todos sus paquetes; 3, en parte | **Etapa 3** (junto con la observación 4b) |
| P2 | Rendimiento en las inundaciones HTTP | Construcción por ancla sobre todo el horizonte; deduplicación y atribución recorriendo el horizonte entero en cada ciclo | `fila_de_ancla` (solo lo que lee la fila), `Deduplicador/Atribuidor.deslizar` (por diferencias), bisección | Equivalencia: `test_fila_de_ancla_igual_a_build_rows_global_del_horizonte` (80 semillas), `test_deslizar_igual_a_la_global_con_atribucion` (40 semillas); las dos detectan mutaciones. Replay completo: 0 diferencias | `RENDIMIENTO-SECUENCIAL.md`: criterio fijado antes (`baa6e92`). `953a436` NO cumple (r2); `862404e` NO cumple (r3, r5); `6b6ef82` cumple R1–R4 en los 11 segmentos (máx. 6,15 s; retraso máx. 7,27 s) | **Resuelto offline (portátil)** |
| P2a | Rendimiento en el Sensor1 | Otro hardware, Suricata y tcpdump concurrentes | — | Mismo criterio R1–R4 en vivo | — | **Pendiente en Sensor1** |
| V | 25 episodios y control con la corrección | — | — | `analizar_3b.py` sin modificar | 0 diferencias de categoría entre la referencia y la corregida (ambas secuenciales); población principal 15/25; control 2622, con 395/254/83 y 92 | **Resuelto offline** |
| V1 | `escaneo_breve-r3`, HEUR/HIB: `solo_posterior` (publicado) frente a `oportuna` (secuencial) | El reloj de coste del replay: disponible 0,23 s después del fin en paralelo y 0,17–0,65 s antes en secuencial | No se corrige: no es lógica | — | `VALIDACION-25-EPISODIOS-Y-CONTROL.md` | No se reclama detección. **Etapa 3**: detectar el escaneo breve y responder durante su actividad |
| T | Pruebas | — | — | Suite completa en el banco `cyberflow-etapa2-banco:2` y pruebas del motor en Windows | `resultados/pruebas/pytest-completo-v-6b6ef82.txt`: 580 pasadas, 1 omitida (sin node); `pytest-motor-windows-6b6ef82.txt`: 22 pasadas, 2 subtests | Resuelto (no prueba el laboratorio) |

## No repetido, porque no lo afectan los cambios

Siguen vigentes los resultados del cierre técnico sobre:

- el relé y su SSH (2.1–2.3);
- el perfil del helper (3);
- LIMIT y los descartes (7);
- el procedimiento de instalación (8);
- el reinicio (5).

Los cambios de este encargo solo tocan `motor_decision.py`, `motor_incremental.py`, el arnés `replay_motor.py` y sus pruebas. La suite completa, que incluye las pruebas de esos puntos, se volvió a ejecutar y pasa.

## Restricciones respetadas

- No se ha desplegado, instalado ni reiniciado nada.
- No se ha activado el enforcement.
- No se han ejecutado ataques ni campañas.
- No se ha editado el Word.
- No se ha avanzado a la Etapa 3.
- No se ha reentrenado ni recalibrado.
- α sigue sin elegir.
