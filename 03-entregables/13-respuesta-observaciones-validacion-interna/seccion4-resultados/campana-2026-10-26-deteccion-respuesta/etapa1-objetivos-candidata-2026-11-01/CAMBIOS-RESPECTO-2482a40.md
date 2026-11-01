# Cambios respecto a `2482a40` (Etapa 1, versión 2)

La versión 1 se conserva en Git (`2482a4024c730564574c6cc819b0afd02a2a66f7`). Aquí se registra cada observación del usuario, su corrección y dónde comprobarla.

| # | Observación | Corrección | Evidencia |
|---|---|---|---|
| 1 | Mantener 25 episodios (5 por escenario); no adoptar 14 ni 22 | D4 registrada como **decidida**. La elección 14/22 sale de las decisiones; sus cálculos quedan como antecedente separado. La incertidumbre con 5 se describe con intervalos bilaterales al 95 %, sin garantías poblacionales. | [DECISIONES.md](DECISIONES.md) D4; [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) §4 |
| 2 | Distinguir las poblaciones y las unidades | Tabla de poblaciones (3B 25 ejecutados / revisión 15 admitidos / simulación / evaluación futura 25 + 25). Unidades definidas: entidad, ventana, episodio, restricción. Las «3–9 entidades» se presentan como entidades del control con restricciones **hipotéticas**. | OBJETIVOS §1.1; PRESUPUESTO-FALSAS-ALARMAS §2, obs. 5; las tablas llevan la columna «admitido» |
| 3 | La clase C1 sobrestimaba lo que se puede afirmar del IF | C1 ya no autoriza la evaluación completa del IF: 11 de sus 28 características son L7 del EVE (`multilayer-v2.json`; la versión 2 decía 12 por error de conteo, corregido en la versión 3, véase CAMBIOS-RESPECTO-c1de49d.md). Se conservan las detecciones observadas con su limitación; no se afirman ausencia, sensibilidad completa ni latencia mínima. Coincidir con el replay no prueba ausencia de pérdidas. Continuidad, cobertura y calidad, por separado. | OBJETIVOS §6, §6.1 |
| 4 | El simulador usaba medianas y máximos como si fueran límites | Escenarios **favorable** y **alto** declarados como supuestos, sin llamarlos intervalos de confianza ni peor caso. Parámetros con su clase (medido / configurado / supuesto / desconocido). | `herramientas/presupuesto_e2e.py` (PARAM, ESCENARIOS); PRESUPUESTO-TEMPORAL §1–§2 |
| 5 | Publicador o relé que terminan después de que arranque el siguiente consumidor | Regla de **consumidor perdido** (+10 s), probada con un publicador de 4,0 s y un relé de 3,5 s | `aplicar_desde_tick`; pruebas «publicador lento» y «relé lento» |
| 6 | No sustituir una demora desconocida por cero | Activación nft y efecto: **desconocidos**, listados en cada estimación. Las clases favorables llevan el sufijo «bajo supuestos»; solo `deteccion_posterior` (t_det medido) no depende de supuestos. | `DESCONOCIDAS`, `clasificar`; prueba «activación nft y efecto» |
| 7 | Distinguir aplicación estimada, real y efecto | Campos `t_apl_estimada`, `t_apl_real = no aplica` y `t_efecto = no aplica`; E2 y E3 separados | JSON `episodios_meta`; OBJETIVOS §2–§3 |
| 8 | La afirmación de que el simulador «reproduce exactamente» el feed y la escalada era imprecisa | Se enumeran los campos comparados. **Feed final:** IP, acción, hasta, alcance, motivo, detector, nivel y revisar_humano. **Estado:** conjunto de IPs, bloqueos y ultimo_evento_block exactos, y ultimo_visto con 0,2 s de tolerancia. No se comparan feeds intermedios (no existen), la firma ni el agente. La comparación se amplió de 2 campos a 8 en el feed y a las 11 IPs del estado. | docstring de `pruebas/test_presupuesto_e2e.py`; bloque 3 de las pruebas |
| 9 | La simulación secuencial no es una campaña de respuesta | Advertencia en el JSON, las tablas y los documentos: es un riesgo bajo supuestos y no modela el cambio del ataque | `secuencial.nota`; PRESUPUESTO-TEMPORAL §5; TABLAS §4 |
| 10 | Escaneo breve: D2 decidida; no afirmar imposibilidad universal; separar tramos | D2 decidida. Desglose por episodio: evidencia suficiente (cierre de la ventana) / paquetes y evaluación / cadena / efecto. Las limitaciones son **de esta configuración**. | PRESUPUESTO-TEMPORAL §4 |
| 11 | Una señal `brute_force` durante un escaneo no valida `port_scan` | Nueva «primera señal de la **regla prevista**». E1 exige la regla prevista; las demás se publican como «detección por otra regla». Nuevo resultado: en escaneo_sostenido-r3, `port_scan` llega a los 74,3 s (después del fin). | `REGLA_PREVISTA`; TABLAS §1b; pruebas de breve-r1 y sostenido-r3; MATRIZ (errores de atribución) |
| 12 | D8: una referencia fija no debe convertir en oportuno lo que llega tarde | `t_fin_eval = min(t_fin_ref, t_fin_observado)` en todos los escenarios. Ejemplo: dns_inusual-r2 terminó a 89,08 s. En la campaña B, el corte se distingue del fin natural. | `main()` del simulador; pruebas t_fin_eval y dns-r2; DECISIONES D8 |
| 13 | Matriz única de decisiones con recomendaciones | [DECISIONES.md](DECISIONES.md): estado, recomendación, fundamento, consecuencias y etapa. D1 con comparación de puntos de aplicación (recomendado DC1). D3 con simulación de 4 políticas × α. Todos los documentos la referencian. | DECISIONES.md; TABLAS §3 |
| 14 | D3: explicar ALERT → LIMIT y comparar señal, corroboración y persistencia, incluida la rapidez | Políticas `actual`, `if_senal`, `persist_2` y `persist_3` simuladas con 3–4 umbrales. `if_senal` reduce las entidades con restricción hipotética de 9 a 1 **sin retrasar** la primera acción en los 25 episodios. | DECISIONES §D3; prueba «persist_2 no usa información futura» |
| 15 | D6: el tiempo restringido no se deduce del número de incidentes | Medido sobre la unión de intervalos **con renovaciones** (734 renovaciones en 15 intervalos con la política actual). P2 y P3 son independientes. | PRESUPUESTO-FALSAS-ALARMAS §1, §3 |
| 16 | Definir el cumplimiento por episodio | Condiciones E1–E5 (detección correcta y disponible; aplicación; efecto mientras el generador sigue; tráfico legítimo; caducidad o retirada) con indeterminado y «no aplica» en sombra | OBJETIVOS §3 |
| 17 | Fallos del experimento: identificador nuevo y tratamiento previo | Lista cerrada de causas; una repetición `rN-bis`; ambos se publican; un fallo del detector no se repite | OBJETIVOS §5 |
| 18 | Preparar la Etapa 2 con dependencias reales | Recorrido de 6 pasos y lista de trabajo offline que no espera a D1, D3 ni D6 | DISENO-VALIDACION.md |

## Cifras que cambian respecto a la versión 1

| Cifra | v1 | v2 | Motivo |
|---|---|---|---|
| Escaneo breve, V2 | «1/5 antes del fin» | primera señal de cualquier regla: 1/5 antes\* (r1, `brute_force`); **regla prevista: 0/5** (5/5 det. posterior en V0) | regla prevista; t_fin_eval |
| Escaneo sostenido, V0 | 5/5 antes del fin | primera señal: 5/5 antes\*; **regla prevista: 4/5** (r3 det. posterior) | regla prevista |
| Clases | antes / indeterminado / después | antes\*bajo supuestos / indeterminado / después\*bajo supuestos / **det. posterior** | supuestos y demoras desconocidas |
| Intervalo de t_apl | «inf–sup» | «favorable–alto», sin valor de límite | definición de los escenarios |
| Fin de nmap en la simulación | observado de cada episodio | min(D_ref mínima, observado) | D8 |
| Restricciones del control | «restringidas» | «hipotéticas», con renovaciones y por política | D3 y D6 |
| Pruebas | 17 | 31 | lógica nueva |
