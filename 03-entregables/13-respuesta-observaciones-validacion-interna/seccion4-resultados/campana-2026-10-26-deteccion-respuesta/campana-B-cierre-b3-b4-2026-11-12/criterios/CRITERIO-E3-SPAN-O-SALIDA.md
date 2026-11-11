# Criterio de continuidad de E3 («SPAN o salida») — texto para fijar ANTES de una nueva corrida (propuesta; requiere la aprobación de Mark)

Fecha de redacción: 10-nov-2026. Estado: **PROPUESTO, no vigente hasta que Mark lo apruebe.** Los resultados históricos de B2 **no se recalculan** con esta regla: siguen siendo los publicados (E3 inundación = indeterminado, I2).

## 1. Referencias (la discrepancia que se resuelve)
| Fuente | Texto |
|---|---|
| `etapa1-objetivos-candidata-2026-11-01\OBJETIVOS-Y-CRITERIOS.md`, tabla E1–E5, fila E3 | «…**y** consta que el generador siguió intentándolo después de `t_apl` (**SPAN o salida**)» |
| `campana-B-protocolo-2026-11-10\PROTOCOLO-CAMPANA-B-BORRADOR-V3-NO-APROBADO.md`, línea 37 (E3 en LIMIT) | «Hay que comprobar que el generador siguió intentando (SYN del origen ≥ 50 % de B0, **y** salida de los `curl`)» |
| `herramientas\analizar_b.py`, `e3()` | solo la vía SPAN: `INTENTO_MIN = 0,5` × B0 de SYN durante `K_LIMIT = 5` (LIMIT) o `K_BLOCK = 3` bloques de 1 s; sin la vía «salida» |
Las tres no coinciden: el criterio de objetivos dice **O**, el borrador del protocolo dice **Y**, y el analizador implementa solo SPAN. El protocolo v3 está marcado «NO APROBADO».

## 2. Regla propuesta (la de OBJETIVOS-Y-CRITERIOS: «SPAN **o** salida»)
«Siguió intentando» se cumple si, durante **K bloques consecutivos de 1 s** tras `t_apl` (K = 5 en LIMIT, 3 en BLOCK; mismos que `analizar_b`), se cumple **al menos una** de:
- **Vía SPAN:** SYN de la Kali al destino ≥ 0,5 × B0_SYN (B0_SYN = media de los 10 bloques anteriores a `t_apl`; es el cálculo vigente de `analizar_b`).
- **Vía salida:** intentos del generador **con hora** (un registro por iteración, `inundacion_instrumentada.sh`) ≥ 0,5 × B0_intentos (media de los 10 bloques anteriores a `t_apl` del mismo registro).
Sin registro de salida con hora, **solo cuenta la vía SPAN** (así B2 sigue siendo indeterminado). Un total sin hora (`intentos=N`) **no** es salida válida.
Lo demás no cambia: el **efecto** (aceptadas ≤ (1 − θ)·B0 con θ = 0,5, sostenido K bloques), la exigencia del **contador de descartes del host** para «cumple», las condiciones de indeterminación I1, I3 y I5, y el tope por E2. Implementación (extensión, sin modificar `analizar_b`): `instrumentacion\analizar_b_instrumentado.py::e3_v2`; sin `intentos_salida` devuelve exactamente lo que `analizar_b.e3`.

## 3. Por qué «O» y no «Y» (la razón, no una preferencia)
- Es el texto del documento de objetivos, que gobierna el criterio; el borrador del protocolo no está aprobado.
- Con el generador actual (bucle síncrono de `curl --max-time 2`), el propio límite reduce los SYN/s: en B2 los SYN cayeron de ≈ 313 a ≈ 38 por s con las aceptadas −90 %. «Y» o «solo SPAN» exigirían un umbral que ese diseño no puede alcanzar aunque el generador siga intentando; el resultado sería siempre indeterminado.
- «O» no es laxo: la vía salida exige el mismo 50 % de B0 con registro continuo con hora, y el efecto sigue exigiendo el contador del host.
**Alternativa (si Mark prefiere «Y»):** exigir ambas vías; implica que E3 de inundación solo pueda ser «cumple» si los SYN del SPAN también superan el umbral, con el generador actual muy improbable.

## 4. Comprobaciones hechas (banco, datos sintéticos; `instrumentacion\evidencia\pruebas-instrumentacion.txt`: 12 pruebas pasan)
Sin serie de salida `e3_v2` ≡ `analizar_b.e3`; salida continua + efecto = cumple (vía salida); salida también baja = indeterminado; siguió intentando sin efecto = fallo; sin contador del host = indeterminado; vía SPAN sigue valiendo; la racha exige K bloques consecutivos (4 de 5 no basta).

## 5. Decisión que se pide
Aprobar **«SPAN o salida»** tal como se redacta (o elegir «Y»), **antes** de ordenar una corrida; una vez aprobada no se cambia durante ni después de la corrida.

## 6. Evidencia que exige cada vía para demostrar continuidad después de la aplicación (añadido 11-nov)
| | Vía SPAN | Vía salida |
|---|---|---|
| Qué demuestra | La Kali siguió enviando SYN al destino tras `t_apl` | El generador siguió iterando tras `t_apl` |
| Fuente exigida | PCAP/serie del espejo por bloques de 1 s, con la IP origen y el destino/puerto del episodio | Registro **por iteración** con hora (`inundacion_instrumentada.sh`: `t_inicio`, `t_fin`, `codigo_http`, `rc_curl`, `lazo`), local en la Kali, fusionado y con sha256 al cierre |
| Línea base | B0_SYN = media de los 10 bloques anteriores a `t_apl` | B0_intentos = media de los 10 bloques anteriores a `t_apl` (mismo registro) |
| Umbral | ≥ 0,5 × B0_SYN durante K bloques consecutivos | ≥ 0,5 × B0_intentos durante K bloques consecutivos |
| Condiciones de validez | huecos del espejo ≤ 10 % (I3); ≥ 10 bloques de línea base (I5); B0 ≥ 5 conexiones/s | todos los lazos presentes (los bloques sin registro cuentan 0 intentos: el registro es continuo y local); reloj de la Kali con desfase ≤ `u` (medición al inicio y al final) |
| No vale | un total sin hora (`intentos=N`, B2) | las peticiones que el servidor aceptó: `con_respuesta` y `sin_respuesta` se registran aparte para que no se confundan con los intentos |
| Qué se registra siempre | `continuidad.span` y `b0_syn` | `continuidad.salida` y `b0_intentos_salida`; **ambas se registran aunque el efecto ya se haya encontrado** (`e3_v2`; prueba `test_ambas_vias_de_continuidad_se_registran_siempre…`) |
El efecto (aceptadas ≤ 50 % de B0) y el contador de descartes del host se exigen igual con cualquiera de las dos vías. El veredicto del episodio solo depende de «alguna de las dos» (regla O); el informe publica **las dos** para que se vea cuál sostuvo la continuidad.

## 7. Por qué hay discrepancia entre los documentos y el analizador (explicación)
`OBJETIVOS-Y-CRITERIOS` (cuya tabla E3 dice «SPAN o salida») es anterior a `analizar_b.py`; el analizador se escribió con los datos entonces disponibles (el SPAN) y la frase del protocolo v3 («SYN ≥ 50 % de B0, y salida») mezcló las dos fuentes en una conjunción al redactar la comprobación operativa, sin que `analizar_b` tuviera nunca entrada de «salida». Ninguno de los tres es una versión aprobada de la regla de continuidad con ambas vías. **Efecto práctico en B2:** el analizador y los PCAP dan I2; con la regla O y los datos de B2 (salida sin hora) el veredicto **sigue siendo indeterminado** por la misma razón (no hay registro de salida con hora), así que el veredicto histórico no cambia.