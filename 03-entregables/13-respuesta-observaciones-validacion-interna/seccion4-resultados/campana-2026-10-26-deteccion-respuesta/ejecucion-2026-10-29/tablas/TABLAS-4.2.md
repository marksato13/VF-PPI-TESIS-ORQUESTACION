# Campaña A: tablas para la sección 4.2 (generadas por resumir_campana.py)

Las categorías y la evaluabilidad salen de `analisis.json` sin cambios. Las siete configuraciones son clasificaciones comparativas derivadas sobre las mismas ventanas; no son siete detectores desplegados.

## Registro de episodios

| n | episodio_id | inicio_utc | duracion_comando_s | estado_generador | codigo_salida | intentos_bucle | pcap_paquetes_hacia_destino | pcap_syn_hacia_destino | servidor_auth_401 | evaluable |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | escaneo_sostenido-r2 | 08:38:10.554 | 65.671 | completo | 0 |  | 65657 | 65573 |  | False |
| 2 | inundacion_http-r1 | 08:42:46.227 | 89.813 | completo | 0 | 13960 | 97689 | 13956 |  | False |
| 3 | dns_inusual-r3 | 08:47:46.042 | 90.076 | completo | 0 | 209 | 209 | 0 |  | False |
| 4 | inundacion_http-r4 | 08:52:46.121 | 89.939 | completo | 0 | 13868 | 97076 | 13868 |  | False |
| 5 | inundacion_http-r2 | 08:57:46.062 | 89.995 | completo | 0 | 14116 | 98813 | 14116 |  | False |
| 6 | inundacion_http-r3 | 09:02:46.059 | 89.989 | completo | 0 | 14073 | 98489 | 14070 |  | False |
| 7 | escaneo_sostenido-r4 | 09:07:46.050 | 66.204 | completo | 0 |  | 65657 | 65573 |  | False |
| 8 | escaneo_sostenido-r5 | 09:12:22.256 | 66.064 | completo | 0 |  | 65657 | 65573 |  | False |
| 9 | escaneo_breve-r5 | 09:16:58.323 | 17.588 | completo | 0 |  | 2027 | 2013 |  | False |
| 10 | fuerza_bruta_http-r3 | 09:20:45.912 | 89.102 | completo | 0 | 6077 | 32295 | 6076 | 6077 | False |
| 11 | fuerza_bruta_http-r5 | 09:25:45.016 | 90.009 | completo | 0 | 6206 | 32767 | 6205 | 6206 | False |
| 12 | dns_inusual-r5 | 09:30:45.027 | 90.132 | completo | 0 | 209 | 209 | 0 |  | False |
| 13 | escaneo_sostenido-r3 | 09:35:45.162 | 65.706 | completo | 0 |  | 65657 | 65573 |  | False |
| 14 | dns_inusual-r2 | 09:40:20.870 | 89.218 | completo | 0 | 207 | 207 | 0 |  | False |
| 15 | fuerza_bruta_http-r2 | 09:45:20.090 | 89.959 | completo | 0 | 6172 | 32162 | 6172 | 6172 | False |
| 16 | fuerza_bruta_http-r4 | 09:50:20.051 | 89.964 | completo | 0 | 6031 | 31552 | 6030 | 6031 | False |
| 17 | dns_inusual-r1 | 09:55:20.017 | 90.371 | completo | 0 | 209 | 209 | 0 |  | False |
| 18 | escaneo_breve-r1 | 10:00:20.390 | 17.991 | completo | 0 |  | 2023 | 2011 |  | False |
| 19 | escaneo_breve-r4 | 10:04:08.383 | 17.985 | completo | 0 |  | 2023 | 2011 |  | False |
| 20 | escaneo_breve-r3 | 10:07:56.370 | 17.691 | completo | 0 |  | 2022 | 2010 |  | False |
| 21 | dns_inusual-r4 | 10:11:44.064 | 90.227 | completo | 0 | 209 | 209 | 0 |  | False |
| 22 | fuerza_bruta_http-r1 | 10:16:44.293 | 89.758 | completo | 0 | 6196 | 32437 | 6196 | 6196 | False |
| 23 | inundacion_http-r5 | 10:21:44.052 | 90.03 | completo | 0 | 14118 | 98826 | 14118 |  | False |
| 24 | escaneo_breve-r2 | 10:26:44.085 | 17.584 | completo | 0 |  | 2027 | 2013 |  | False |
| 25 | escaneo_sostenido-r1 | 10:30:31.671 | 65.763 | completo | 0 |  | 65656 | 65570 |  | False |

## Tabla 8 propuesta (detección durante / evaluables)

| escenario | realizados | evaluables | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 |
|---|---|---|---|---|---|---|---|---|---|
| Escaneo sostenido | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Inundación HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| DNS inusual | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Escaneo breve | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Fuerza bruta HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| TOTAL (misma población evaluable) | 25 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Falsas alarmas del control normal

Población: window_end en [2026-10-29T08:01:00+00:00, 2026-10-29T08:35:00+00:00]; 2526 ventanas evaluadas, 0 no evaluadas explícitas; cobertura entre registradas 1.0 (sin inventario independiente).

| configuracion | falsas_alarmas | denominador_ventanas | tasa |
|---|---|---|---|
| IF_0.05 | 355 | 2526 | 0.140538 |
| IF_0.03 | 231 | 2526 | 0.091449 |
| IF_0.01 | 85 | 2526 | 0.03365 |
| HEUR | 75 | 2526 | 0.029691 |
| HIB_0.05 | 423 | 2526 | 0.167458 |
| HIB_0.03 | 304 | 2526 | 0.120348 |
| HIB_0.01 | 160 | 2526 | 0.063341 |

## Compartidas y exclusivas IF / heurísticos

| alfa | nivel | ambos | solo_IF | solo_HEUR | ninguno |
|---|---|---|---|---|---|
| 0.05 | episodio evaluable (detección durante) |  |  |  |  |
| 0.05 | ventana con atribución confirmada, escrita durante el ataque |  |  |  |  |
| 0.03 | episodio evaluable (detección durante) |  |  |  |  |
| 0.03 | ventana con atribución confirmada, escrita durante el ataque |  |  |  |  |
| 0.01 | episodio evaluable (detección durante) |  |  |  |  |
| 0.01 | ventana con atribución confirmada, escrita durante el ataque |  |  |  |  |
