# Balance de B3 (corrida parcial de 6 episodios, 11-nov-2026) — versión corregida

**B3 se reporta por separado de B4.** ID de corrida B3: `4c-20261111T051928Z-2eb2f728a738` (g01c, 05:19:41Z; cancelada a las 06:08:28Z por decisión de Mark tras el bloqueo de la puerta D5 en el episodio 6). **El episodio 7 (`fuerza_bruta_http-r1`) no arrancó.** Los 19 restantes se ejecutarán, si se autoriza, como **B4**, una corrida nueva con ID nuevo (enmienda aprobada el 11-nov: la campaña cancelada no se reanuda). Veredictos de B2 y B3 sin cambios. Evidencia: `corrida-2026-11-11\` y `~/cf-e4/4c-B3-parcial-6ep-20261111T0620Z` (Sensor1, bastión, clientes), `~/cf-e4-4c-B3-parcial-6ep-20261111T0620Z` (Kali); análisis `corrida-2026-11-11\analisis\resultado-b3.json` (`f2fed429…`).

**CORRECCIÓN (11-nov):** el balance entregado en el chat decía que la salida con hora del generador «baja a unos 4 intentos/s». Esa cifra era la **cota teórica** 8 lazos ÷ 2 s (`--max-time 2`), no una medida. **La medida es 16,5 intentos/s** en ambos episodios de inundación (ver «E3 de la inundación»). El veredicto E3 = indeterminado no cambia.

## Resultados por episodio (los 6, todos `completo` y C0 en captura y vía rápida)
| Episodio | E1 | E2 (regla aplicada) | E3 | E4 | E5 |
|---|---|---|---|---|---|
| `inundacion_http-r4` | verificado (señal `http_abuse` a +17,7 s) | cumple, confirmada a +18,7 s | **indeterminado** (I2) | cumple | cumple, retirada explícita (+106 s tras el fin) |
| `fuerza_bruta_http-r4` | verificado (+11,6 s) | cumple, +13,2 s | cumple (SPAN) | cumple | cumple, retirada explícita (+102 s) |
| `dns_inusual-r1` | verificado (+25,2 s) | no aplica (DC1 sin punto de aplicación) | no aplica | cumple | no aplica |
| `fuerza_bruta_http-r3` | verificado (+8,3 s) | cumple, +9,8 s | cumple (SPAN) | cumple | cumple, retirada explícita (+96 s) |
| `dns_inusual-r3` | verificado (+27,9 s) | no aplica | no aplica | cumple | no aplica |
| `inundacion_http-r3` | verificado (+16,0 s) | cumple, +17,6 s | **indeterminado** (I2) | cumple | cumple, retirada explícita (+97 s) |
E4: ≈ 460–540 transacciones de clientes por ventana, ninguna atribuible a la restricción. E3 BLOCK (fuerza bruta): efecto sostenido en 3 bloques, 0 respuestas, ≥ 1 SYN por bloque (SPAN única fuente, decisión de Mark), contador de descartes del host confirmado. No evaluable / no lanzado: 19 episodios (B4). Casos indeterminados: las 2 inundaciones en E3.

## E3 de la inundación (indeterminado, I2) — con la cifra medida
Criterio fijado (`CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md`): LIMIT = SPAN o salida con hora; continuidad ≥ 0,5 × B0 en 5 bloques consecutivos de 1 s tras `t_apl`.
| | `inundacion_http-r4` | `inundacion_http-r3` |
|---|---|---|
| Conexiones aceptadas por s (SPAN), 10 s antes → después de la regla | 311,6 → 32,6 (−89,5 %) | 312,2 → 32,6 (−89,6 %) |
| **Intentos por s del generador (salida con hora), antes de la regla** | 2.911 en 18,7 s = **155,6** | 2.742 en 17,6 s = **155,9** |
| **Intentos por s, medidos tras la regla** | 1.181 en 71,4 s = **16,5** | 1.205 en 73,0 s = **16,5** |
| SYN por s (SPAN) tras la regla / umbral 0,5 × B0 | 38,2 / 155,8 | 37,9 / 156,1 |
| Umbral de continuidad de la salida (0,5 × B0 de intentos) | 78,0 | 78,0 |
Cómo se calcula la cifra medida: iteraciones registradas en `intentos-<episodio>.tsv` con inicio ≥ `t_apl`, divididas por `t_fin − t_apl` (ventanas 71,4 s y 73,0 s). Ni 16,5 ni la cota 4 alcanzan el umbral de 78 it/s: **el veredicto no depende de la cifra citada**. Causa: bucle síncrono (la latencia, 0,48 s de media tras la limitación, frena los intentos): `LIMITACION-GENERADOR-E3-INUNDACION.md`.

## Cobertura por familia: dos tramos (B3 + B4), NO una corrida continua
| Familia (planificados) | B3 ejecutados | B3 pendientes → B4 | B4 ejecutados |
|---|---|---|---|
| inundación HTTP (5) | 2 (r4, r3) | 3 (r2, r1, r5) | pendiente |
| fuerza bruta HTTP (5) | 2 (r4, r3) | 3 (r1, r5, r2) | pendiente |
| DNS inusual (5) | 2 (r1, r3) | 3 (r4, r2, r5) | pendiente |
| escaneo breve (5) | **0** | 5 (r4, r2, r5, r3, r1) | pendiente |
| escaneo sostenido (5) | **0** | 5 (r5, r2, r3, r1, r4) | pendiente |
| **Total (25)** | **6** | **19** | **pendiente** |
Esta tabla suma conteos de dos corridas distintas (controles, relojes y ventanas horarias propios; X1/P5 por corrida; orden de la semilla cortado 6/19, con los 10 escaneos solo en B4): no es una corrida continua y los intervalos de Clopper–Pearson sobre el agregado son descriptivos.
