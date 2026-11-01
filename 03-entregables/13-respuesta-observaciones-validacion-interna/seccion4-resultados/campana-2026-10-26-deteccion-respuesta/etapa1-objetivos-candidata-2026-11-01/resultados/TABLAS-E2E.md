# Tablas del presupuesto temporal (v3; generadas por herramientas/tablas_e2e.py)

> **Simulación sobre registros de sombra del 3B.** No es una campaña de respuesta: no modela cómo una restricción habría cambiado el ataque ni las decisiones posteriores. `t_apl_estimada` es una estimación bajo supuestos (escenarios *favorable* = p50/mínimos medidos con offsets desconocidos supuestos 0; *alto* = máximos históricos + cotas configuradas). **No son intervalos de confianza ni límites garantizados.** t_apl real y t_efecto: no aplica. «*» = bajo supuestos; además deben caber las demoras desconocidas (activación nft, efecto). «det. posterior» = t_det MEDIDO después del fin: no depende de supuestos.

Poblaciones: campaña 3B = 25 episodios ejecutados; revisión 3B = 15 admitidos (columna A). La simulación se calcula para los 25 y cada fila indica si el episodio está admitido.

## 1. Por episodio, política actual (IF → LIMIT) con el umbral desplegado

| Episodio | A | Fin eval. (s) | Fuente del fin | Primera acción · origen | t_det | V0 t_apl est. fav.–alto | Margen (alto) | V0 | V1 | V2 t_det | V2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dns_inusual-r1 | sí | 90,0 | referencia | LIMIT · modelo IF | 17,2 | 27,1–28,5 | 61,5 | antes* | antes* | 12,8 | antes* |
| dns_inusual-r2 | sí | 89,1 | observado | LIMIT · dns_entropy | 25,9 | 36,2–37,6 | 51,5 | antes* | antes* | 11,4 | antes* |
| dns_inusual-r3 | no | 90,0 | referencia | LIMIT · dns_entropy | 20,2 | 31,1–32,5 | 57,5 | antes* | antes* | 6,7 | antes* |
| dns_inusual-r4 | sí | 89,5 | observado | LIMIT · dns_entropy | 23,9 | 33,6–35,0 | 54,5 | antes* | antes* | 9,4 | antes* |
| dns_inusual-r5 | no | 90,0 | referencia | LIMIT · dns_entropy | 21,9 | 32,1–33,5 | 56,5 | antes* | antes* | 7,4 | antes* |
| escaneo_breve-r1 | sí | 17,6 | observado | BLOCK · brute_force | 16,4 | 26,8–28,2 | -10,6 | **después*** | **después*** | 11,9 | antes* |
| escaneo_breve-r2 | sí | 17,6 | referencia | BLOCK · port_scan | 26,2 | 34,1–35,5 | -17,9 | **det. posterior** | **det. posterior** | 20,6 | **det. posterior** |
| escaneo_breve-r3 | sí | 17,6 | referencia | BLOCK · port_scan | 30,7 | 41,2–42,6 | -25,0 | **det. posterior** | **det. posterior** | 16,2 | **después*** |
| escaneo_breve-r4 | no | 17,6 | referencia | BLOCK · port_scan | 28,8 | 39,2–40,6 | -23,0 | **det. posterior** | **det. posterior** | 24,3 | **det. posterior** |
| escaneo_breve-r5 | sí | 17,6 | referencia | BLOCK · port_scan | 39,5 | 49,2–50,6 | -33,0 | **det. posterior** | **det. posterior** | 25,1 | **det. posterior** |
| escaneo_sostenido-r1 | no | 65,5 | referencia | BLOCK · port_scan | 39,6 | 46,1–47,5 | 18,0 | antes* | antes* | 24,0 | antes* |
| escaneo_sostenido-r2 | sí | 65,5 | referencia | BLOCK · port_scan | 26,6 | 37,0–38,4 | 27,1 | antes* | antes* | 23,1 | antes* |
| escaneo_sostenido-r3 | sí | 65,5 | observado | LIMIT · modelo IF | 22,0 | 31,7–33,1 | 32,4 | antes* | antes* | 7,6 | antes* |
| escaneo_sostenido-r4 | sí | 65,5 | referencia | BLOCK · port_scan | 22,0 | 31,1–32,5 | 33,0 | antes* | antes* | 17,5 | antes* |
| escaneo_sostenido-r5 | sí | 65,5 | referencia | BLOCK · port_scan | 35,6 | 45,0–46,4 | 19,2 | antes* | antes* | 21,2 | antes* |
| fuerza_bruta_http-r1 | sí | 90,0 | referencia | BLOCK · brute_force | 25,1 | 34,1–35,5 | 54,5 | antes* | antes* | 10,7 | antes* |
| fuerza_bruta_http-r2 | no | 90,0 | referencia | BLOCK · brute_force | 18,8 | 27,1–28,5 | 61,5 | antes* | antes* | 4,4 | antes* |
| fuerza_bruta_http-r3 | no | 89,1 | observado | BLOCK · brute_force | 23,6 | 31,2–32,6 | 56,5 | antes* | antes* | 9,2 | antes* |
| fuerza_bruta_http-r4 | sí | 90,0 | referencia | BLOCK · brute_force | 18,4 | 27,1–28,5 | 61,5 | antes* | antes* | 4,0 | antes* |
| fuerza_bruta_http-r5 | sí | 90,0 | referencia | BLOCK · brute_force | 23,7 | 32,1–33,5 | 56,5 | antes* | antes* | 9,2 | antes* |
| inundacion_http-r1 | no | 89,6 | observado | LIMIT · modelo IF | 24,9 | 30,7–42,1 | 47,5 | antes* | antes* | 11,4 | antes* |
| inundacion_http-r2 | no | 90,0 | observado | LIMIT · modelo IF | 25,4 | 31,1–42,5 | 47,5 | antes* | antes* | 11,9 | antes* |
| inundacion_http-r3 | no | 90,0 | referencia | LIMIT · modelo IF | 25,4 | 31,1–42,5 | 47,5 | antes* | antes* | 11,8 | antes* |
| inundacion_http-r4 | no | 89,8 | observado | LIMIT · modelo IF | 24,2 | 30,9–32,3 | 57,5 | antes* | antes* | 10,7 | antes* |
| inundacion_http-r5 | sí | 90,0 | observado | LIMIT · modelo IF | 29,3 | 44,1–45,5 | 44,5 | antes* | antes* | 14,8 | antes* |

### 1b. Primera señal de la REGLA PREVISTA (dns_entropy / http_abuse / port_scan / brute_force)

Una señal de otra regla (p. ej. brute_force durante un escaneo) no valida la regla prevista.

| Episodio | A | Regla prevista: acción · t_det | V0 | Primera señal de cualquier regla | ¿Coinciden? |
|---|---|---|---|---|---|
| dns_inusual-r1 | sí | LIMIT · 17,2 | antes* | modelo IF (17,2) | sí |
| dns_inusual-r2 | sí | LIMIT · 25,9 | antes* | dns_entropy (25,9) | sí |
| dns_inusual-r3 | no | LIMIT · 20,2 | antes* | dns_entropy (20,2) | sí |
| dns_inusual-r4 | sí | LIMIT · 23,9 | antes* | dns_entropy (23,9) | sí |
| dns_inusual-r5 | no | LIMIT · 21,9 | antes* | dns_entropy (21,9) | sí |
| escaneo_breve-r1 | sí | BLOCK · 36,4 | **det. posterior** | brute_force (16,4) | no |
| escaneo_breve-r2 | sí | BLOCK · 26,2 | **det. posterior** | port_scan (26,2) | sí |
| escaneo_breve-r3 | sí | BLOCK · 30,7 | **det. posterior** | port_scan (30,7) | sí |
| escaneo_breve-r4 | no | BLOCK · 28,8 | **det. posterior** | port_scan (28,8) | sí |
| escaneo_breve-r5 | sí | BLOCK · 39,5 | **det. posterior** | port_scan (39,5) | sí |
| escaneo_sostenido-r1 | no | BLOCK · 39,6 | antes* | port_scan (39,6) | sí |
| escaneo_sostenido-r2 | sí | BLOCK · 26,6 | antes* | port_scan (26,6) | sí |
| escaneo_sostenido-r3 | sí | BLOCK · 74,3 | **det. posterior** | modelo IF (22,0) | no |
| escaneo_sostenido-r4 | sí | BLOCK · 22,0 | antes* | port_scan (22,0) | sí |
| escaneo_sostenido-r5 | sí | BLOCK · 35,6 | antes* | port_scan (35,6) | sí |
| fuerza_bruta_http-r1 | sí | BLOCK · 25,1 | antes* | brute_force (25,1) | sí |
| fuerza_bruta_http-r2 | no | BLOCK · 18,8 | antes* | brute_force (18,8) | sí |
| fuerza_bruta_http-r3 | no | BLOCK · 23,6 | antes* | brute_force (23,6) | sí |
| fuerza_bruta_http-r4 | sí | BLOCK · 18,4 | antes* | brute_force (18,4) | sí |
| fuerza_bruta_http-r5 | sí | BLOCK · 23,7 | antes* | brute_force (23,7) | sí |
| inundacion_http-r1 | no | LIMIT · 24,9 | antes* | modelo IF (24,9) | sí |
| inundacion_http-r2 | no | LIMIT · 25,4 | antes* | modelo IF (25,4) | sí |
| inundacion_http-r3 | no | LIMIT · 25,4 | antes* | modelo IF (25,4) | sí |
| inundacion_http-r4 | no | LIMIT · 24,2 | antes* | modelo IF (24,2) | sí |
| inundacion_http-r5 | sí | LIMIT · 29,3 | antes* | modelo IF (29,3) | sí |

## 2. Resumen por escenario (política actual; distribuciones de valores POR EPISODIO)

| Escenario | Ejecutados (admitidos) | Detección disponible antes del fin | t_det mín/med/máx | V0 t_apl est. alto mín/med/máx | V0 antes*/indet./después*/det. post. | V1 | V2 |
|---|---|---|---|---|---|---|---|
| dns_inusual | 5 (3) | 5/5 | 17,2/21,9/25,9 | 28,5/33,5/37,6 | 5/0/0/0 | 5/0/0/0 | 5/0/0/0 |
| escaneo_breve | 5 (4) | 1/5 | 16,4/28,8/39,5 | 28,2/40,6/50,6 | 0/0/1/4 | 0/0/1/4 | 1/0/1/3 |
| escaneo_sostenido | 5 (4) | 5/5 | 22,0/26,6/39,6 | 32,5/38,4/47,5 | 5/0/0/0 | 5/0/0/0 | 5/0/0/0 |
| fuerza_bruta_http | 5 (3) | 5/5 | 18,4/23,6/25,1 | 28,5/32,6/35,5 | 5/0/0/0 | 5/0/0/0 | 5/0/0/0 |
| inundacion_http | 5 (1) | 5/5 | 24,2/25,4/29,3 | 32,3/42,5/45,5 | 5/0/0/0 | 5/0/0/0 | 5/0/0/0 |

## 3. Políticas para D3 (acción del IF) × umbral: episodios y control normal (33 min)

Restricciones **hipotéticas** (simuladas sobre el control de sombra; ninguna se aplicó). Entidades = direcciones IP del control; ventanas = registros entidad×window_end; intervalos = restricciones fusionadas por entidad; renovaciones = ampliaciones del mismo intervalo.

| Política · umbral | Ventanas con veredicto (%) | Incidentes de señal (sin NUNCA) | Entidades con restricción hipotética | Intervalos | Renovaciones | Entidades > 50 % del control | BLOCK | V0 antes* por familia (dns/breve/sost./fb/inund.) |
|---|---|---|---|---|---|---|---|---|
| actual · desplegado | 467 (17,7 %) | 23 | 9 | 15 | 734 | 5 | 0 | 5/0/5/5/5 |
| actual · IF_0.05 | 466 (17,6 %) | 23 | 9 | 15 | 734 | 5 | 0 | 5/0/5/5/5 |
| actual · IF_0.03 | 336 (12,7 %) | 11 | 7 | 11 | 558 | 4 | 0 | 5/0/5/5/5 |
| actual · IF_0.01 | 171 (6,5 %) | 14 | 3 | 7 | 355 | 3 | 0 | 5/0/5/5/5 |
| if_senal · desplegado | 92 (3,5 %) | 1 | 1 | 1 | 14 | 0 | 0 | 5/0/5/5/5 |
| persist_2 · desplegado | 360 (13,6 %) | 8 | 4 | 6 | 506 | 3 | 0 | 5/0/5/5/5 |
| persist_2 · IF_0.05 | 359 (13,6 %) | 8 | 4 | 6 | 506 | 3 | 0 | 5/0/5/5/5 |
| persist_2 · IF_0.03 | 226 (8,6 %) | 13 | 3 | 6 | 405 | 3 | 0 | 5/0/5/5/5 |
| persist_2 · IF_0.01 | 122 (4,6 %) | 9 | 2 | 5 | 188 | 2 | 0 | 5/0/5/5/5 |
| persist_3 · desplegado | 304 (11,5 %) | 11 | 3 | 5 | 458 | 3 | 0 | 5/0/5/5/5 |
| persist_3 · IF_0.05 | 303 (11,5 %) | 12 | 3 | 5 | 458 | 3 | 0 | 5/0/5/5/5 |
| persist_3 · IF_0.03 | 180 (6,8 %) | 13 | 3 | 6 | 314 | 3 | 0 | 5/0/5/5/5 |
| persist_3 · IF_0.01 | 105 (4,0 %) | 7 | 2 | 5 | 111 | 1 | 0 | 5/0/5/5/5 |

Detalle por entidad (restricción hipotética; fracción del control):

- **actual · desplegado**: 10.10.10.21 40,8 % (2 int., 22 renov.); 10.10.20.21 97,7 % (1 int., 124 renov.); 10.10.20.22 99,7 % (1 int., 198 renov.); 10.10.20.23 40,8 % (2 int., 22 renov.); 10.10.20.24 99,7 % (1 int., 198 renov.); 10.10.20.26 94,5 % (3 int., 99 renov.); 10.10.40.10 14,8 % (1 int., 11 renov.); 10.10.50.51 59,5 % (2 int., 38 renov.); 10.10.50.52 40,8 % (2 int., 22 renov.)
- **actual · IF_0.01**: 10.10.20.22 99,7 % (1 int., 187 renov.); 10.10.20.24 80,4 % (3 int., 80 renov.); 10.10.20.26 90,5 % (3 int., 88 renov.)
- **persist_3 · desplegado**: 10.10.20.22 99,7 % (1 int., 198 renov.); 10.10.20.24 93,1 % (1 int., 171 renov.); 10.10.20.26 92,0 % (3 int., 89 renov.)
- **if_senal · desplegado**: 10.10.20.26 21,9 % (1 int., 14 renov.)

## 4. Simulación secuencial (política actual): restricción hipotética vigente al empezar

> Riesgo bajo supuestos: con bloqueo real, los ataques y decisiones posteriores habrían sido otros.

| Episodio | BLOCK hipotético vigente | Restante (s) | Nivel de escalada previo |
|---|---|---|---|
| escaneo_sostenido-r2 | no | 0,0 | 3 |
| inundacion_http-r1 | sí | 3524,5 | 3 |
| dns_inusual-r3 | sí | 3544,9 | 3 |
| inundacion_http-r4 | sí | 3244,8 | 3 |
| inundacion_http-r2 | sí | 3544,9 | 3 |
| inundacion_http-r3 | sí | 3545,0 | 3 |
| escaneo_sostenido-r4 | sí | 3524,9 | 3 |
| escaneo_sostenido-r5 | sí | 3538,8 | 3 |
| escaneo_breve-r5 | sí | 3543,1 | 3 |
| fuerza_bruta_http-r3 | sí | 3525,1 | 3 |
| fuerza_bruta_http-r5 | sí | 3586,0 | 3 |
| dns_inusual-r5 | sí | 3586,0 | 3 |
| escaneo_sostenido-r3 | sí | 3415,6 | 3 |
| dns_inusual-r2 | sí | 3540,0 | 3 |
| fuerza_bruta_http-r2 | sí | 3421,0 | 3 |
| fuerza_bruta_http-r4 | sí | 3590,9 | 3 |
| dns_inusual-r1 | sí | 3590,9 | 3 |
| escaneo_breve-r1 | sí | 3420,6 | 3 |
| escaneo_breve-r4 | sí | 3543,0 | 3 |
| escaneo_breve-r3 | sí | 3515,0 | 3 |
| dns_inusual-r4 | sí | 3527,4 | 3 |
| fuerza_bruta_http-r1 | sí | 3417,9 | 3 |
| inundacion_http-r5 | sí | 3587,9 | 3 |
| escaneo_breve-r2 | sí | 3547,9 | 3 |
| escaneo_sostenido-r1 | sí | 3540,0 | 3 |

## 5. D3: tres resultados separados por episodio (política if_senal)

> 1) **Anomalía del IF**: primera ventana atribuible con ALERT del IF a cada umbral; el IF no clasifica familias y no se le exige producir `port_scan`. 2) **Heurístico previsto** (la regla del escenario). 3) **Respuesta** con `if_senal`: primera acción (solo heurísticos) y su clase V0 bajo supuestos. `!` = disponible después del fin; `—` = sin señal. En DNS no hay agente: el punto de aplicación propuesto es DC1 (D1). Simulación en sombra: no es aplicación real.

| Episodio | A | 1. IF desplegado | 1. IF α 0,05 | 1. IF α 0,03 | 1. IF α 0,01 | 2. Heurístico previsto | 3. Respuesta if_senal | 3. ¿Regla prevista? | 3. V0 |
|---|---|---|---|---|---|---|---|---|---|
| dns_inusual-r1 | sí | 17,2 | 17,2 | 17,2 | 17,2 | 17,2 | LIMIT · dns_entropy (17,2) | sí | antes* |
| dns_inusual-r2 | sí | — | — | — | — | 25,9 | LIMIT · dns_entropy (25,9) | sí | antes* |
| dns_inusual-r3 | no | — | — | — | — | 20,2 | LIMIT · dns_entropy (20,2) | sí | antes* |
| dns_inusual-r4 | sí | — | — | — | — | 23,9 | LIMIT · dns_entropy (23,9) | sí | antes* |
| dns_inusual-r5 | no | 21,9 | 21,9 | 21,9 | 21,9 | 21,9 | LIMIT · dns_entropy (21,9) | sí | antes* |
| escaneo_breve-r1 | sí | 16,4 | 16,4 | 16,4 | 36,4 ! | 36,4 ! | BLOCK · brute_force (16,4) | **no** | **después*** |
| escaneo_breve-r2 | sí | 26,2 ! | 26,2 ! | 26,2 ! | 26,2 ! | 26,2 ! | BLOCK · port_scan (26,2) | sí | **det. posterior** |
| escaneo_breve-r3 | sí | 41,0 ! | 41,0 ! | 41,0 ! | — | 30,7 ! | BLOCK · port_scan (30,7) | sí | **det. posterior** |
| escaneo_breve-r4 | no | 28,8 ! | 28,8 ! | 28,8 ! | — | 28,8 ! | BLOCK · port_scan (28,8) | sí | **det. posterior** |
| escaneo_breve-r5 | sí | 39,5 ! | 39,5 ! | 39,5 ! | — | 39,5 ! | BLOCK · port_scan (39,5) | sí | **det. posterior** |
| escaneo_sostenido-r1 | no | 39,6 | 39,6 | 39,6 | 39,6 | 39,6 | BLOCK · port_scan (39,6) | sí | antes* |
| escaneo_sostenido-r2 | sí | 26,6 | 26,6 | 26,6 | 26,6 | 26,6 | BLOCK · port_scan (26,6) | sí | antes* |
| escaneo_sostenido-r3 | sí | 22,0 | 22,0 | 22,0 | 22,0 | 74,3 ! | BLOCK · brute_force (22,0) | **no** | antes* |
| escaneo_sostenido-r4 | sí | 22,0 | 22,0 | 42,8 | 42,8 | 22,0 | BLOCK · port_scan (22,0) | sí | antes* |
| escaneo_sostenido-r5 | sí | 35,6 | 35,6 | 35,6 | 35,6 | 35,6 | BLOCK · port_scan (35,6) | sí | antes* |
| fuerza_bruta_http-r1 | sí | 25,1 | 25,1 | 25,1 | 25,1 | 25,1 | BLOCK · brute_force (25,1) | sí | antes* |
| fuerza_bruta_http-r2 | no | 18,8 | 18,8 | 18,8 | 18,8 | 18,8 | BLOCK · brute_force (18,8) | sí | antes* |
| fuerza_bruta_http-r3 | no | 23,6 | 23,6 | 23,6 | 23,6 | 23,6 | BLOCK · brute_force (23,6) | sí | antes* |
| fuerza_bruta_http-r4 | sí | 18,4 | 18,4 | 18,4 | 18,4 | 18,4 | BLOCK · brute_force (18,4) | sí | antes* |
| fuerza_bruta_http-r5 | sí | 23,7 | 23,7 | 23,7 | 23,7 | 23,7 | BLOCK · brute_force (23,7) | sí | antes* |
| inundacion_http-r1 | no | 24,9 | 24,9 | 24,9 | 24,9 | 24,9 | LIMIT · http_abuse (24,9) | sí | antes* |
| inundacion_http-r2 | no | 25,4 | 25,4 | 25,4 | 25,4 | 25,4 | LIMIT · http_abuse (25,4) | sí | antes* |
| inundacion_http-r3 | no | 25,4 | 25,4 | 25,4 | 25,4 | 25,4 | LIMIT · http_abuse (25,4) | sí | antes* |
| inundacion_http-r4 | no | 24,2 | 24,2 | 24,2 | 24,2 | 24,2 | LIMIT · http_abuse (24,2) | sí | antes* |
| inundacion_http-r5 | sí | 29,3 | 29,3 | 29,3 | 29,3 | 29,3 | LIMIT · http_abuse (29,3) | sí | antes* |

**Resumen por escenario** (episodios con el resultado disponible antes del fin; respuesta: regla prevista y aplicación estimada antes del fin bajo supuestos):

| Escenario | n | 1. IF desplegado / 0,05 / 0,03 / 0,01 | 2. Heurístico previsto | 3. Respuesta prevista antes* | Señal solo del IF, sin respuesta |
|---|---|---|---|---|---|
| dns_inusual | 5 | 2 / 2 / 2 / 2 | 5 | 5 | 0 |
| escaneo_breve | 5 | 1 / 1 / 1 / 0 | 0 | 0 | 0 |
| escaneo_sostenido | 5 | 5 / 5 / 5 / 5 | 4 | 4 | 0 |
| fuerza_bruta_http | 5 | 5 / 5 / 5 / 5 | 5 | 5 | 0 |
| inundacion_http | 5 | 5 / 5 / 5 / 5 | 5 | 5 | 0 |
