# Tablas del paso 3B — campaña A repetida 2026-11-01 (generadas por resumir_3b.py)

Fuentes (sha256): `analisis-3b.json` 2da445ba6185…, `integridad.json` 1de1f455131b…, `calidad-fuentes.json` f6c7851ab6d9…

Las 7 configuraciones son clasificaciones **derivadas** de los registros (no detectores desplegados). Las emisiones reales (ALERT del IF desplegado y heurísticos registrados en vivo) van aparte.

## Tabla 8 propuesta (población principal; los episodios fuera se cuentan aparte)

| Escenario | Realizados | Población principal | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisiones reales (episodios con ≥1 oportuna) |
|---|---|---|---|---|---|---|---|---|---|---|
| Escaneo sostenido | 5 | 0 | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | 5/5 |
| Inundación HTTP | 5 | 0 | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | 5/5 |
| DNS inusual | 5 | 0 | n/a · fuera: 2 op., 0 post., 3 n/e | n/a · fuera: 2 op., 0 post., 3 n/e | n/a · fuera: 2 op., 0 post., 3 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | 5/5 |
| Escaneo breve | 5 | 1 | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 0/1 op. · fuera: 0 op., 2 post., 2 n/e | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 0/1 op. (1 post.) · fuera: 1 op., 3 post., 0 n/e | 1/5 |
| Fuerza bruta HTTP | 5 | 0 | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | n/a · fuera: 5 op., 0 post., 0 n/e | 5/5 |

Lectura: «x/n op.» = episodios de la población principal con categoría `oportuna`; «fuera:» = episodios con observación incompleta, cuyas detecciones se publican pero no entran en la tabla principal (op. = oportuna, post. = solo_posterior, n/e = no_evaluable).

## Categorías por episodio y configuración

| orden | episodio | poblacion_principal | calidad_fuente | integridad_apta | ventanas_requeridas | tardias | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | emisiones_oportunas | latencia_1a_emision_oportuna_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | escaneo_sostenido-r2 | no | completa | False | 13 | 5 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 26.56 |
| 2 | inundacion_http-r1 | no | completa | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.9 |
| 3 | dns_inusual-r3 | no | degradada | False | 15 | 5 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 8 | 20.19 |
| 4 | inundacion_http-r4 | no | degradada | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 24.2 |
| 5 | inundacion_http-r2 | no | degradada | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.43 |
| 6 | inundacion_http-r3 | no | degradada | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.36 |
| 7 | escaneo_sostenido-r4 | no | completa | False | 13 | 4 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 4 | 21.97 |
| 8 | escaneo_sostenido-r5 | no | completa | False | 12 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 35.63 |
| 9 | escaneo_breve-r5 | no | completa | False | 8 | 5 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 |  |
| 10 | fuerza_bruta_http-r3 | no | degradada | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.59 |
| 11 | fuerza_bruta_http-r5 | no | completa | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 23.68 |
| 12 | dns_inusual-r5 | no | degradada | False | 15 | 4 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 21.88 |
| 13 | escaneo_sostenido-r3 | no | completa | False | 12 | 2 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 5 | 22.01 |
| 14 | dns_inusual-r2 | no | completa | False | 15 | 5 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 7 | 25.85 |
| 15 | fuerza_bruta_http-r2 | no | degradada | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.84 |
| 16 | fuerza_bruta_http-r4 | no | completa | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 18.44 |
| 17 | dns_inusual-r1 | no | completa | False | 15 | 4 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 7 | 17.22 |
| 18 | escaneo_breve-r1 | no | completa | False | 8 | 0 | oportuna | oportuna | solo_posterior | oportuna | oportuna | oportuna | oportuna | 1 | 16.4 |
| 19 | escaneo_breve-r4 | no | degradada | False | 8 | 5 | solo_posterior | solo_posterior | no_evaluable | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 |  |
| 20 | escaneo_breve-r3 | sí | completa | True | 8 | 5 | solo_posterior | solo_posterior | ausencia_con_observacion_suficiente | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 |  |
| 21 | dns_inusual-r4 | no | completa | False | 15 | 5 | no_evaluable | no_evaluable | no_evaluable | oportuna | oportuna | oportuna | oportuna | 6 | 23.88 |
| 22 | fuerza_bruta_http-r1 | no | completa | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 8 | 25.14 |
| 23 | inundacion_http-r5 | no | completa | False | 15 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 6 | 29.32 |
| 24 | escaneo_breve-r2 | no | completa | False | 8 | 0 | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | solo_posterior | 0 |  |
| 25 | escaneo_sostenido-r1 | no | completa | False | 12 | 0 | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | oportuna | 3 | 39.61 |

## Control normal (07:32:00–08:05:00, inventario)

| configuracion | falsas_alarmas | decididas | requeridas_inventario | sin_decision | cobertura | tasa | cota_min | cota_max |
|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 395 | 2644 | 2644 | 0 | 1.0 | 0.149395 | 0.149395 | 0.149395 |
| IF_0.03 | 254 | 2644 | 2644 | 0 | 1.0 | 0.096067 | 0.096067 | 0.096067 |
| IF_0.01 | 83 | 2644 | 2644 | 0 | 1.0 | 0.031392 | 0.031392 | 0.031392 |
| HEUR | 92 | 2644 | 2644 | 0 | 1.0 | 0.034796 | 0.034796 | 0.034796 |
| HIB_0.05 | 466 | 2644 | 2644 | 0 | 1.0 | 0.176248 | 0.176248 | 0.176248 |
| HIB_0.03 | 336 | 2644 | 2644 | 0 | 1.0 | 0.12708 | 0.12708 | 0.12708 |
| HIB_0.01 | 171 | 2644 | 2644 | 0 | 1.0 | 0.064675 | 0.064675 | 0.064675 |

Inventario completo de la ejecución: 12667 ventanas requeridas, cobertura 1.0, a tiempo 12012, tardías 655, no evaluadas 0, ausentes 0; retraso de disponibilidad p50 15.957 s, p95 65.664 s, máx 238.7 s.

### Control por entidad

| entidad | ventanas | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | excepcion_respuesta |
|---|---|---|---|---|---|---|---|---|---|
| 10.10.10.1 | 75 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.10.20 | 199 | 26 | 10 | 1 | 88 | 97 | 92 | 88 | True |
| 10.10.10.21 | 199 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | False |
| 10.10.10.51 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.20.20 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.20.21 | 199 | 17 | 4 | 0 | 0 | 17 | 4 | 0 | False |
| 10.10.20.22 | 199 | 171 | 128 | 50 | 0 | 171 | 128 | 50 | False |
| 10.10.20.23 | 199 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | False |
| 10.10.20.24 | 199 | 124 | 74 | 9 | 0 | 124 | 74 | 9 | False |
| 10.10.20.25 | 199 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.20.26 | 199 | 46 | 36 | 23 | 4 | 46 | 36 | 24 | False |
| 10.10.20.30 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.30.10 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.40.10 | 199 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | False |
| 10.10.50.51 | 199 | 4 | 1 | 0 | 0 | 4 | 1 | 0 | False |
| 10.10.50.52 | 199 | 3 | 0 | 0 | 0 | 3 | 0 | 0 | False |
| 10.10.60.12 | 199 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.99.10 | 37 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.99.2 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.99.5 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.99.7 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |
| 10.10.99.8 | 31 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | False |

### Informativo: control sin el DNS 10.10.10.20 (no sustituye a la tabla anterior)

| configuracion | falsas_alarmas_sin_DNS | decididas_sin_DNS | tasa_sin_DNS | nota |
|---|---|---|---|---|
| IF_0.05 | 369 | 2445 | 0.15092 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| IF_0.03 | 244 | 2445 | 0.099796 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| IF_0.01 | 82 | 2445 | 0.033538 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| HEUR | 4 | 2445 | 0.001636 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| HIB_0.05 | 369 | 2445 | 0.15092 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| HIB_0.03 | 244 | 2445 | 0.099796 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |
| HIB_0.01 | 83 | 2445 | 0.033947 | INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población) |

## Comparación de α (mismo tráfico)

| configuracion | alfa | umbral | umbral_igual_a_calibracion_sin_kali | pp_oportuna | pp_solo_posterior | pp_ausencia_obs_suficiente | todos_oportuna | todos_solo_posterior | todos_no_evaluable | mediana_disponibilidad_1a_senal_oportuna_s | control_falsas_alarmas | control_tasa | control_cobertura | control_decididas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IF_0.05 | 0.05 | -0.5694578968203694 | True | 0/1 | 1 | 0 | 18/25 | 4 | 3 | 23.95 | 395 | 0.149395 | 1.0 | 2644 |
| HIB_0.05 | 0.05 | -0.5694578968203694 | True | 0/1 | 1 | 0 | 21/25 | 4 | 0 | 23.9 | 466 | 0.176248 | 1.0 | 2644 |
| IF_0.03 | 0.03 | -0.5898535710336618 | True | 0/1 | 1 | 0 | 18/25 | 4 | 3 | 24.55 | 254 | 0.096067 | 1.0 | 2644 |
| HIB_0.03 | 0.03 | -0.5898535710336618 | True | 0/1 | 1 | 0 | 21/25 | 4 | 0 | 23.9 | 336 | 0.12708 | 1.0 | 2644 |
| IF_0.01 | 0.01 | -0.6223889502095352 | True | 0/1 | 0 | 1 | 17/25 | 2 | 5 | 24.9 | 83 | 0.031392 | 1.0 | 2644 |
| HIB_0.01 | 0.01 | -0.6223889502095352 | True | 0/1 | 1 | 0 | 21/25 | 4 | 0 | 23.9 | 171 | 0.064675 | 1.0 | 2644 |

## Emisiones reales por episodio

| episodio | escenario | poblacion_principal | emisiones | atribuibles | oportunas | latencia_1a_oportuna_s | 1a_oportuna_componente | 1a_oportuna_window_end_utc |
|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | Escaneo sostenido | no | 8 | 8 | 4 | 26.56 | IF_desplegado | 2026-11-01T08:09:00+00:00 |
| inundacion_http-r1 | Inundación HTTP | no | 15 | 15 | 8 | 24.9 | IF_desplegado | 2026-11-01T08:13:20+00:00 |
| dns_inusual-r3 | DNS inusual | no | 15 | 15 | 8 | 20.19 | heuristico:dns_entropy | 2026-11-01T08:18:20+00:00 |
| inundacion_http-r4 | Inundación HTTP | no | 15 | 15 | 8 | 24.2 | IF_desplegado | 2026-11-01T08:23:20+00:00 |
| inundacion_http-r2 | Inundación HTTP | no | 15 | 15 | 8 | 25.43 | IF_desplegado | 2026-11-01T08:28:20+00:00 |
| inundacion_http-r3 | Inundación HTTP | no | 15 | 15 | 8 | 25.36 | IF_desplegado | 2026-11-01T08:33:20+00:00 |
| escaneo_sostenido-r4 | Escaneo sostenido | no | 9 | 9 | 4 | 21.97 | IF_desplegado | 2026-11-01T08:38:30+00:00 |
| escaneo_sostenido-r5 | Escaneo sostenido | no | 11 | 11 | 3 | 35.63 | IF_desplegado | 2026-11-01T08:43:10+00:00 |
| escaneo_breve-r5 | Escaneo breve | no | 3 | 3 | 0 |  |  |  |
| fuerza_bruta_http-r3 | Fuerza bruta HTTP | no | 15 | 15 | 8 | 23.59 | IF_desplegado | 2026-11-01T08:51:20+00:00 |
| fuerza_bruta_http-r5 | Fuerza bruta HTTP | no | 15 | 15 | 8 | 23.68 | IF_desplegado | 2026-11-01T08:56:20+00:00 |
| dns_inusual-r5 | DNS inusual | no | 15 | 15 | 8 | 21.88 | heuristico:dns_entropy | 2026-11-01T09:01:20+00:00 |
| escaneo_sostenido-r3 | Escaneo sostenido | no | 12 | 12 | 5 | 22.01 | IF_desplegado | 2026-11-01T09:06:20+00:00 |
| dns_inusual-r2 | DNS inusual | no | 14 | 14 | 7 | 25.85 | heuristico:dns_entropy | 2026-11-01T09:11:00+00:00 |
| fuerza_bruta_http-r2 | Fuerza bruta HTTP | no | 15 | 15 | 8 | 18.84 | IF_desplegado | 2026-11-01T09:15:50+00:00 |
| fuerza_bruta_http-r4 | Fuerza bruta HTTP | no | 15 | 15 | 8 | 18.44 | IF_desplegado | 2026-11-01T09:20:50+00:00 |
| dns_inusual-r1 | DNS inusual | no | 14 | 14 | 7 | 17.22 | IF_desplegado | 2026-11-01T09:26:00+00:00 |
| escaneo_breve-r1 | Escaneo breve | no | 7 | 7 | 1 | 16.4 | IF_desplegado | 2026-11-01T09:31:00+00:00 |
| escaneo_breve-r4 | Escaneo breve | no | 3 | 3 | 0 |  |  |  |
| escaneo_breve-r3 | Escaneo breve | sí | 4 | 4 | 0 |  |  |  |
| dns_inusual-r4 | DNS inusual | no | 14 | 14 | 6 | 23.88 | heuristico:dns_entropy | 2026-11-01T09:42:20+00:00 |
| fuerza_bruta_http-r1 | Fuerza bruta HTTP | no | 15 | 15 | 8 | 25.14 | IF_desplegado | 2026-11-01T09:47:20+00:00 |
| inundacion_http-r5 | Inundación HTTP | no | 15 | 15 | 6 | 29.32 | IF_desplegado | 2026-11-01T09:52:20+00:00 |
| escaneo_breve-r2 | Escaneo breve | no | 3 | 3 | 0 |  |  |  |
| escaneo_sostenido-r1 | Escaneo sostenido | no | 10 | 10 | 3 | 39.61 | IF_desplegado | 2026-11-01T10:01:20+00:00 |

## Calidad de fuentes y descartes de Suricata (por separado)

| episodio | calidad_fuente(±60s) | suricata_kernel_drops(±60s) | suricata_kernel_packets(±60s) | suricata_kernel_drops(-120/+90s,integridad) | tcpdump_descartes | tcpdump_alcance | ens37_rx_dropped(±60s,sin clasificar) | pcap_continuo | pcap_ficheros | hueco_registro_motor_max_s |
|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | completa | 0 | 195410 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2696 | True | 13 | 20.76 |
| inundacion_http-r1 | completa | 0 | 493854 | 11 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2975 | True | 15 | 20.77 |
| dns_inusual-r3 | degradada | 28 | 110979 | 28 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2978 | True | 15 | 20.44 |
| inundacion_http-r4 | degradada | 182 | 482648 | 182 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3059 | True | 15 | 20.52 |
| inundacion_http-r2 | degradada | 111 | 500407 | 111 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3056 | True | 15 | 20.7 |
| inundacion_http-r3 | degradada | 1146 | 497276 | 1483 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2976 | True | 15 | 21.78 |
| escaneo_sostenido-r4 | completa | 0 | 157320 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2701 | True | 14 | 21.13 |
| escaneo_sostenido-r5 | completa | 0 | 150289 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2632 | True | 13 | 21.13 |
| escaneo_breve-r5 | completa | 0 | 99707 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 1993 | True | 10 | 19.98 |
| fuerza_bruta_http-r3 | degradada | 61 | 310514 | 61 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3038 | True | 15 | 21.11 |
| fuerza_bruta_http-r5 | completa | 0 | 278437 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3060 | True | 15 | 20.82 |
| dns_inusual-r5 | degradada | 100 | 120988 | 100 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2975 | True | 15 | 20.01 |
| escaneo_sostenido-r3 | completa | 0 | 175284 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2695 | True | 14 | 20.96 |
| dns_inusual-r2 | completa | 0 | 114868 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3060 | True | 16 | 20.25 |
| fuerza_bruta_http-r2 | degradada | 97 | 280189 | 97 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2976 | True | 16 | 20.13 |
| fuerza_bruta_http-r4 | completa | 0 | 266332 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2998 | True | 16 | 20.5 |
| dns_inusual-r1 | completa | 0 | 122484 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3056 | True | 16 | 20.17 |
| escaneo_breve-r1 | completa | 0 | 49278 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2055 | True | 11 | 20.02 |
| escaneo_breve-r4 | degradada | 58 | 83944 | 58 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2072 | True | 10 | 20.07 |
| escaneo_breve-r3 | completa | 0 | 92591 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2072 | True | 10 | 19.9 |
| dns_inusual-r4 | completa | 0 | 146758 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 3059 | True | 15 | 20.61 |
| fuerza_bruta_http-r1 | completa | 0 | 227488 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2976 | True | 15 | 20.51 |
| inundacion_http-r5 | completa | 0 | 462488 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2981 | True | 15 | 21.26 |
| escaneo_breve-r2 | completa | 0 | 117879 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 1987 | True | 10 | 11.66 |
| escaneo_sostenido-r1 | completa | 0 | 165150 | 0 | 0 | medido: contador acumulado del proceso tcpdump = 0 al final | 2695 | True | 14 | 20.03 |

## Ciclos del motor y huecos entre escrituras por tramo

| tramo | desde | hasta | ciclos | ciclo_dur_p50_s | ciclo_dur_p95_s | ciclo_dur_max_s | instantes_escritura_decisiones | hueco_escritura_p50_s | hueco_escritura_p95_s | hueco_escritura_max_s | huecos_escritura_>20s(analizador) | huecos_>20s_max_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| previo (motor activo, antes del control) | 2026-11-01T03:14:01Z | 2026-11-01T07:32:00Z | 1548 | 0.28 | 2.23 | 9.38 | 1195 | 10.03 | 20.07 | 23.54 | 208 | 23.5 |
| control normal | 2026-11-01T07:32:00Z | 2026-11-01T08:05:00Z | 198 | 1.17 | 1.87 | 2.3 | 154 | 10.22 | 20.39 | 20.83 | 21 | 20.8 |
| entre control y batería | 2026-11-01T08:05:00Z | 2026-11-01T08:08:39Z | 22 | 1.28 | 2.05 | 2.1 | 17 | 10.47 | 20.2 | 20.89 | 1 | 20.9 |
| batería (1.er inicio - último fin) | 2026-11-01T08:08:39Z | 2026-11-01T10:02:05.818Z | 681 | 1.65 | 5.06 | 10.61 | 514 | 10.55 | 20.41 | 21.78 | 79 | 21.8 |
| cierre (fin + espera, hasta el último ciclo copiado) | 2026-11-01T10:02:05.818Z | 2026-11-01T10:40:00Z | 206 | 1.16 | 1.91 | 4.13 | 157 | 10.32 | 20.27 | 20.97 | 24 | 21.0 |
