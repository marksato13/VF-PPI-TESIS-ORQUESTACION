# Criterio E3 FIJADO para la nueva corrida de la Campaña B (11-nov-2026) — «SPAN o salida»

**Estado: VIGENTE desde el 2026-11-11, antes de lanzar la corrida. No se cambia durante ni después de ella.**
**Origen de la decisión:** instrucción de Mark en la sesión del 11-nov: «Para E3 de la nueva corrida, usa SPAN o salida del generador con hora como vías alternativas de evidencia de continuidad. Registra ambas cuando estén disponibles y deja fijados antes de lanzar la corrida el umbral, la referencia, la duración de cada bloque y cuántos bloques consecutivos se exigen. Conserva el resultado histórico de B2.» Equivale a la opción «SPAN o salida» de `CRITERIO-E3-FINAL-PARA-APROBAR.md`; **no** se eligió la alternativa «Y».
**No retroactivo:** el veredicto histórico de B2 no se recalcula ni se reemplaza (E3 fuerza bruta = verificado 2/2; E3 inundación = indeterminado 2/2, I2). Esta corrida produce un resultado nuevo, aparte.

## Parámetros fijados (los cuatro que se pidieron)
| Parámetro | Valor fijado |
|---|---|
| **Duración de cada bloque** | **1 s** (bloques consecutivos, alineados al reloj del host de medición) |
| **Bloques consecutivos exigidos** | **K = 5** en LIMIT; **K = 3** en BLOCK |
| **Referencia (línea base)** | **B0 = media de las conexiones aceptadas en los 10 bloques de 1 s anteriores a `t_apl`** (instante en que el agente aplicó la regla). Se exige **B0 ≥ 5 por s** y los 10 bloques completos; si no, E3 = indeterminado. Igual para `B0_SYN` (SYN del origen al destino y puerto del episodio) y `B0_intentos` (iteraciones del generador con hora). |
| **Umbral** | **θ = 0,5**: en LIMIT, conexiones aceptadas ≤ (1 − θ)·B0 = 0,5·B0 durante los K bloques; en BLOCK, ninguna respuesta del destino al origen durante los K bloques. Continuidad de intentos: ≥ **0,5 × B0** de la vía correspondiente. |

## Regla completa
1. **Efecto.** Existe `t_efecto ≥ t_apl` con K bloques consecutivos que cumplen el umbral de arriba, y `t_efecto + 1 s + u < t_fin_eval` (u = incertidumbre de relojes medida, mínimo 0,01 s; el 11-nov 03:15Z los cuatro hosts quedaron a ≤ 0,172 s del bastión con u ≤ 0,165 s).
2. **Continuidad de intentos: dos vías ALTERNATIVAS (basta una) y se REGISTRAN LAS DOS siempre que haya datos.**
   - **SPAN:** SYN del origen hacia el destino y puerto del episodio ≥ 0,5 × B0_SYN en esos K bloques, con el espejo sin huecos de más del 10 % en el episodio.
   - **Salida del generador con hora:** un registro por iteración (`t_inicio`, `t_fin`, `codigo_http`, `rc_curl`, `lazo`) ≥ 0,5 × B0_intentos en esos K bloques. Un total sin hora (`intentos=N`) no vale.
   - Los intentos se publican **separados** de las peticiones aceptadas por el servidor (`con_respuesta` / `sin_respuesta`).
3. **Atribución.** El contador de descartes de la regla en el host (`primer_descarte`, con el id de la regla y de la IP del origen) existe tras `t_apl`; sin él, «cumple» pasa a «indeterminado».
4. **Resultado.** cumple (1, 2 y 3 y E2 no indeterminada) · fallo (hay continuidad y el efecto no se sostiene) · indeterminado (sin continuidad por ninguna vía, sin línea base, espejo con > 10 % de huecos, menos de K bloques tras `t_apl`, sin contador del host o E2 indeterminada) · fallo del experimento (sin traza del agente en la ventana).

## DECISIÓN DE MARK (11-nov, antes de lanzar): fuente de continuidad por acción
| Acción | Episodios de esta corrida | Fuente de continuidad de intentos |
|---|---|---|
| **LIMIT** | dns_inusual, inundacion_http (10) | **SPAN o salida del generador con hora** (vías alternativas; se registran ambas). La salida con hora existe solo para la inundación (instrumentada). |
| **BLOCK** | escaneo_breve, escaneo_sostenido, fuerza_bruta_http (**15**) | **SPAN, ÚNICA fuente.** K = 3 bloques de 1 s, **0 respuestas** del destino al origen y **≥ 1 intento (SYN) por bloque**. **Si SPAN no permite verificar la continuidad, E3 = `indeterminado`** (no se suple con otra fuente). |
Implementado como `BLOCK_ADMITE_SALIDA = False` en `instrumentacion\analizar_b_instrumentado.py`: en BLOCK `e3_v2` delega exactamente en `analizar_b.e3` aunque exista `intentos_salida`. **B2 se conserva** (E3 fuerza bruta = verificado 2/2; E3 inundación = indeterminado 2/2).

## Rama BLOCK (aclaración del 11-nov, escrita ANTES de lanzar; no cambia ningún valor de la tabla de arriba)
**Nota:** el párrafo siguiente describe la regla de BLOCK; la parte «o salida con hora» y la rama BLOCK+salida de `e3_v2` quedan **implementadas pero DESACTIVADAS** por la decisión de arriba.
El texto anterior fijaba la referencia B0 y el umbral 0,5 × B0 para LIMIT. En **BLOCK** (escaneo_breve, escaneo_sostenido, fuerza_bruta_http: 15 de los 25 episodios) la regla que ya aplicaba `analizar_b` y que produjo el veredicto histórico de B2 es **absoluta**, y se mantiene con las mismas dos vías alternativas: durante **K = 3 bloques consecutivos de 1 s** tras `t_apl` el destino **no responde al origen** (0 respuestas) y el generador **siguió intentando**, demostrado por **al menos una** vía: **SPAN** (≥ 1 SYN del origen al destino y puerto en cada bloque) o **salida con hora** (≥ 1 iteración registrada con hora en cada bloque). Se registran ambas siempre que haya datos. Atribución (`primer_descarte`) y resultado: igual que arriba. Implementado y verificado en `instrumentacion\analizar_b_instrumentado.py::e3_v2` (9 pruebas BLOCK, 4 mutaciones eliminadas); sin `intentos_salida` delega exactamente en `analizar_b.e3`.
**Disponibilidad de la vía salida en BLOCK:** hoy solo existe salida con hora para `inundacion_http` (LIMIT). nmap no tiene bucle y el `curl` de `fuerza_bruta_http` no está instrumentado: en los 15 episodios BLOCK la continuidad solo se demuestra por SPAN, como en B2. **Decisión tomada por Mark el 11-nov: SPAN única fuente; no se instrumenta `fuerza_bruta_http`.**

## D5 de la nueva corrida
Limpieza **sin reinicio**, **una sola solicitud por episodio** a **fin de episodio + 75 s** (`--espera-fin 75`, opción A del Hallazgo 2), solo sobre 10.10.20.30. Una decisión posterior a fin + 75 s bloquea la puerta (seguro; reanudación manual registrada). Las solicitudes nuevas tras un fallo son decisión manual.

## Implementación
`instrumentacion\analizar_b_instrumentado.py::e3_v2` (ambas vías, sin modificar `analizar_b.py`; sin registro de salida devuelve exactamente el resultado histórico de B2). Los valores coinciden con las constantes de `herramientas\analizar_b.py` (`K_LIMIT = 5`, `K_BLOCK = 3`, `THETA = 0.5`, `N_BASE = 10`, `BASE_MIN = 5.0`, `INTENTO_MIN = 0.5`, `HUECOS_MAX = 0.10`), verificado el 11-nov. **Actualización 11-nov:** `e3_v2` cubre ahora LIMIT y BLOCK (ver «Rama BLOCK»); antes solo cubría LIMIT. El analizador se ejecuta **después** de la corrida con estos parámetros; ninguno se ajusta a los datos.
