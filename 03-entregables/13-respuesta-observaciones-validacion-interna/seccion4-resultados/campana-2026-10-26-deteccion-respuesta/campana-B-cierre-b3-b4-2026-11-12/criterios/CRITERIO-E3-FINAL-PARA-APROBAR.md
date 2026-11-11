# Criterio E3 — TEXTO FINAL PARA APROBAR antes de otra corrida (11-nov-2026)

**Estado: PROPUESTO. No es vigente hasta que Mark lo apruebe.** Una vez aprobado no se cambia durante ni después de la corrida. **No es retroactivo:** el veredicto histórico de B2 (E3 inundación = indeterminado, I2; fuerza bruta = verificado) no se recalcula. Fundamento, referencias y la explicación de la discrepancia: `CRITERIO-E3-SPAN-O-SALIDA.md` (§1, §3, §6, §7).

## Texto
**E3 — Efecto comprobado mientras el generador sigue intentando.** Para un episodio con punto de aplicación y con `t_apl` (instante en que el agente aplicó la regla) y `t_fin_eval` (fin del episodio, o la observación anterior si es menor):

1. **Efecto.** Existe `t_efecto` ≥ `t_apl` tal que, durante **K bloques consecutivos de 1 s** (K = 5 en LIMIT; K = 3 en BLOCK), las respuestas del destino al origen cumplen: en LIMIT, conexiones aceptadas ≤ (1 − θ)·B0 con θ = 0,5; en BLOCK, ninguna respuesta. B0 = media de las conexiones aceptadas en los **10 bloques anteriores** a `t_apl` (se exige B0 ≥ 5 por s y 10 bloques de línea base). Debe cumplirse `t_efecto + 1 s + u < t_fin_eval` (u = incertidumbre de relojes medida, mínimo 0,01 s).
2. **Continuidad de intentos («SPAN o salida»).** En esos mismos K bloques consecutivos consta que el generador **siguió intentando**, demostrado por **al menos una** de las dos vías:
   - **SPAN:** SYN del origen hacia el destino y puerto del episodio ≥ 0,5 × B0_SYN (B0_SYN = media de los 10 bloques previos a `t_apl`), con el espejo sin huecos de más del 10 % en el episodio.
   - **Salida:** iteraciones del generador **con hora** (un registro por iteración: `t_inicio`, `t_fin`, `codigo_http`, `rc_curl`, `lazo`) ≥ 0,5 × B0_intentos (media de los 10 bloques previos a `t_apl` del mismo registro). Un total sin hora (`intentos=N`) **no** es una vía válida.
   Ambas vías se **registran siempre** que haya datos, aunque una baste, y los intentos se publican **separados** de las peticiones que el servidor aceptó (`con_respuesta` / `sin_respuesta`).
3. **Atribución.** El contador de paquetes descartados de la regla en el propio host (`primer_descarte`, con el id de la regla y de la IP del origen) existe tras `t_apl`. Sin él, «cumple» pasa a «indeterminado».
4. **Resultado.**
   - **cumple:** 1, 2 y 3 se satisfacen y E2 no es indeterminada.
   - **fallo:** hay continuidad demostrada (2) y el efecto (1) no se sostiene.
   - **indeterminado:** no hay continuidad por ninguna vía; o falta la línea base, el espejo tiene más del 10 % de huecos, hay menos de K bloques tras `t_apl`, falta el contador del host o E2 es indeterminada.
   - **fallo del experimento:** sin traza del agente en la ventana.

## Qué cambia respecto del criterio de OBJETIVOS-Y-CRITERIOS y de `analizar_b.py`
- Coincide con la fila E3 de `OBJETIVOS-Y-CRITERIOS.md` («SPAN o salida»).
- `analizar_b.py` solo implementa la vía SPAN: la extensión `instrumentacion\analizar_b_instrumentado.py::e3_v2` añade la vía salida **sin modificarlo** y, sin registro de salida, devuelve exactamente el mismo resultado (por eso B2 no cambia).
- El borrador del protocolo v3 («SYN ≥ 50 % de B0 **y** salida») queda sustituido por este texto.

## Alternativa que Mark puede elegir
«**Y**»: exigir ambas vías. Con el generador actual (bucle síncrono de `curl --max-time 2`) el propio límite reduce los SYN por segundo, de modo que E3 de inundación solo podría ser «cumple» si el SPAN también supera el umbral, algo muy improbable (en B2: 38 SYN/s frente a 156 requeridos con −90 % de aceptadas).

## Decisión que se pide
Aprobar este texto («SPAN o salida») o elegir «Y». Hasta entonces la instrumentación puede instalarse, pero la **evaluación** de E3 de inundación no se declara.
