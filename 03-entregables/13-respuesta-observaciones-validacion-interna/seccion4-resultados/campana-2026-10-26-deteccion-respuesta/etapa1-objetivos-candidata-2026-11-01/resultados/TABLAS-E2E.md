# Tablas del presupuesto temporal (generadas por herramientas/tablas_e2e.py)

Fuente: `resultados/presupuesto-e2e.json`. Tiempos en segundos desde `t_inicio` del episodio. t_det = disponibilidad del registro (medido). t_apl = **estimado** (en sombra el agente no aplicó). Intervalo inf–sup por la fase del publicador y el arranque del agente (AccuracySec=1s). P = episodio en la población principal v2.

## 1. Primera señal atribuible con veredicto (cualquier acción) y primer BLOCK

| Episodio | P | Dur. obs. | Acción · motivo | t_det | V0 t_apl | V0 margen | V0 | V1 | V2 t_apl | V2 | 1.er BLOCK V0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dns_inusual-r1 | P | 90,3 | LIMIT · modelo IF | 17,2 | 27,1–28,5 | 61,5–62,9 | antes | antes | 14,6–15,7 | antes | 317,1–318,5 (**después**) |
| dns_inusual-r2 | P | 89,1 | LIMIT · dns_entropy | 25,9 | 36,2–37,6 | 52,4–53,8 | antes | antes | 13,2–14,3 | antes | — |
| dns_inusual-r3 |  | 90,2 | LIMIT · dns_entropy | 20,2 | 31,1–32,5 | 57,5–58,9 | antes | antes | 8,5–9,6 | antes | — |
| dns_inusual-r4 | P | 89,5 | LIMIT · dns_entropy | 23,9 | 33,6–35,0 | 55,0–56,4 | antes | antes | 11,2–12,3 | antes | — |
| dns_inusual-r5 |  | 90,4 | LIMIT · dns_entropy | 21,9 | 32,1–33,5 | 56,5–57,9 | antes | antes | 9,3–10,4 | antes | — |
| escaneo_breve-r1 | P | 17,6 | BLOCK · brute_force | 16,4 | 26,8–28,2 | -10,6–-9,2 | **después** | **después** | 13,8–14,9 | antes | 26,8–28,2 (**después**) |
| escaneo_breve-r2 | P | 18,0 | BLOCK · port_scan | 26,2 | 34,1–35,5 | -17,5–-16,1 | **después** | **después** | 22,4–23,6 | **después** | 34,1–35,5 (**después**) |
| escaneo_breve-r3 | P | 17,6 | BLOCK · port_scan | 30,7 | 41,2–42,6 | -25,0–-23,6 | **después** | **después** | 18,1–19,2 | **después** | 41,2–42,6 (**después**) |
| escaneo_breve-r4 |  | 18,0 | BLOCK · port_scan | 28,8 | 39,2–40,6 | -22,6–-21,2 | **después** | **después** | 26,1–27,2 | **después** | 39,2–40,6 (**después**) |
| escaneo_breve-r5 | P | 18,0 | BLOCK · port_scan | 39,5 | 49,2–50,6 | -32,6–-31,3 | **después** | **después** | 26,9–28,1 | **después** | 49,2–50,6 (**después**) |
| escaneo_sostenido-r1 |  | 65,8 | BLOCK · port_scan | 39,6 | 46,1–47,5 | 18,2–19,6 | antes | antes | 25,8–26,9 | antes | 46,1–47,5 (antes) |
| escaneo_sostenido-r2 | P | 66,3 | BLOCK · port_scan | 26,6 | 37,0–38,4 | 27,9–29,3 | antes | antes | 24,9–26,0 | antes | 37,0–38,4 (antes) |
| escaneo_sostenido-r3 | P | 65,5 | LIMIT · modelo IF | 22,0 | 31,7–33,1 | 32,4–33,8 | antes | antes | 9,4–10,5 | antes | 31,7–33,1 (antes) |
| escaneo_sostenido-r4 | P | 66,1 | BLOCK · port_scan | 22,0 | 31,1–32,5 | 33,6–35,0 | antes | antes | 19,4–20,5 | antes | 31,1–32,5 (antes) |
| escaneo_sostenido-r5 | P | 65,7 | BLOCK · port_scan | 35,6 | 45,0–46,4 | 19,4–20,8 | antes | antes | 23,0–24,1 | antes | 45,0–46,4 (antes) |
| fuerza_bruta_http-r1 | P | 90,0 | BLOCK · brute_force | 25,1 | 34,1–35,5 | 54,5–55,9 | antes | antes | 12,5–13,6 | antes | 34,1–35,5 (antes) |
| fuerza_bruta_http-r2 |  | 90,0 | BLOCK · brute_force | 18,8 | 27,1–28,5 | 61,5–62,9 | antes | antes | 6,2–7,3 | antes | 27,1–28,5 (antes) |
| fuerza_bruta_http-r3 |  | 89,1 | BLOCK · brute_force | 23,6 | 31,2–32,6 | 57,4–58,8 | antes | antes | 11,0–12,1 | antes | 31,2–32,6 (antes) |
| fuerza_bruta_http-r4 | P | 90,0 | BLOCK · brute_force | 18,4 | 27,1–28,5 | 61,5–62,9 | antes | antes | 5,8–6,9 | antes | 27,1–28,5 (antes) |
| fuerza_bruta_http-r5 | P | 90,0 | BLOCK · brute_force | 23,7 | 32,1–33,5 | 56,5–57,9 | antes | antes | 11,1–12,2 | antes | 32,1–33,5 (antes) |
| inundacion_http-r1 |  | 89,6 | LIMIT · modelo IF | 24,9 | 30,7–42,1 | 47,9–59,3 | antes | antes | 13,2–14,3 | antes | 120,7–122,1 (**después**) |
| inundacion_http-r2 |  | 90,0 | LIMIT · modelo IF | 25,4 | 31,1–42,5 | 47,5–58,9 | antes | antes | 13,7–14,8 | antes | 121,1–122,5 (**después**) |
| inundacion_http-r3 |  | 90,0 | LIMIT · modelo IF | 25,4 | 31,1–42,5 | 47,5–58,9 | antes | antes | 13,7–14,8 | antes | 121,1–122,5 (**después**) |
| inundacion_http-r4 |  | 89,8 | LIMIT · modelo IF | 24,2 | 30,9–32,3 | 57,7–59,1 | antes | antes | 12,5–13,6 | antes | 120,9–122,3 (**después**) |
| inundacion_http-r5 | P | 90,0 | LIMIT · modelo IF | 29,3 | 44,1–45,5 | 44,5–45,9 | antes | antes | 16,7–17,8 | antes | 124,1–125,5 (**después**) |

## 2. Resumen por escenario (distribución de valores por episodio; no se suman medianas)

| Escenario | n (P) | Dur. obs. mediana | t_det mín/med/máx | V0 t_apl sup mín/med/máx | V0 antes/indet/después | V1 | V2 | Ventana con señal cierra antes del fin |
|---|---|---|---|---|---|---|---|---|
| dns_inusual | 5 (3) | 90,2 | 17,2/21,9/25,9 | 28,5/33,5/37,6 | 5/0/0 | 5/0/0 | 5/0/0 | 5/5 |
| escaneo_breve | 5 (4) | 18,0 | 16,4/28,8/39,5 | 28,2/40,6/50,6 | 0/0/5 | 0/0/5 | 1/0/4 | 3/5 |
| escaneo_sostenido | 5 (4) | 65,8 | 22,0/26,6/39,6 | 32,5/38,4/47,5 | 5/0/0 | 5/0/0 | 5/0/0 | 5/5 |
| fuerza_bruta_http | 5 (3) | 90,0 | 18,4/23,6/25,1 | 28,5/32,6/35,5 | 5/0/0 | 5/0/0 | 5/0/0 | 5/5 |
| inundacion_http | 5 (1) | 90,0 | 24,2/25,4/29,3 | 32,3/42,5/45,5 | 5/0/0 | 5/0/0 | 5/0/0 | 5/5 |

## 3. Simulación secuencial: restricción ya vigente al empezar cada episodio

| Episodio | BLOCK vigente al inicio | Restante (s) | Nivel de escalada previo |
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

## 4. Control normal (33 min): señales y restricciones que se habrían aplicado

| Configuración | Umbral IF | Ventanas con veredicto / 2644 | Señales por componente | Entidades restringidas / en control | Incidentes (por hora) | Entidades restringidas > 50 % del control |
|---|---|---|---|---|---|---|
| desplegado | -0.5694 | 467 (17,7 %) | LIMIT_modelo 396, LIMIT_heuristico:dns_entropy 88, LIMIT_heuristico:http_abuse 4 | 9 / 22 | 15 (27,3) | 10.10.20.21, 10.10.20.22, 10.10.20.24, 10.10.20.26, 10.10.50.51 |
| IF_0.05 | -0.5695 | 466 (17,6 %) | LIMIT_modelo 395, LIMIT_heuristico:dns_entropy 88, LIMIT_heuristico:http_abuse 4 | 9 / 22 | 15 (27,3) | 10.10.20.21, 10.10.20.22, 10.10.20.24, 10.10.20.26, 10.10.50.51 |
| IF_0.03 | -0.5899 | 336 (12,7 %) | LIMIT_modelo 254, LIMIT_heuristico:dns_entropy 88, LIMIT_heuristico:http_abuse 4 | 7 / 22 | 11 (20,0) | 10.10.20.21, 10.10.20.22, 10.10.20.24, 10.10.20.26 |
| IF_0.01 | -0.6224 | 171 (6,5 %) | LIMIT_modelo 83, LIMIT_heuristico:dns_entropy 88, LIMIT_heuristico:http_abuse 4 | 3 / 22 | 7 (12,7) | 10.10.20.22, 10.10.20.24, 10.10.20.26 |

Detalle por entidad (desplegado): fracción del control con restricción aplicada.

| Entidad | Incidentes | Segundos | Fracción | BLOCK |
|---|---|---|---|---|
| 10.10.10.21 | 2 | 807,7 | 0,4 | 0 |
| 10.10.20.21 | 1 | 1933,8 | 1,0 | 0 |
| 10.10.20.22 | 1 | 1973,8 | 1,0 | 0 |
| 10.10.20.23 | 2 | 807,7 | 0,4 | 0 |
| 10.10.20.24 | 1 | 1973,8 | 1,0 | 0 |
| 10.10.20.26 | 3 | 1871,5 | 0,9 | 0 |
| 10.10.40.10 | 1 | 293,8 | 0,1 | 0 |
| 10.10.50.51 | 2 | 1177,7 | 0,6 | 0 |
| 10.10.50.52 | 2 | 807,7 | 0,4 | 0 |
