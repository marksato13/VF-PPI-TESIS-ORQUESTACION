# Tablas de la revisión 3B (revisión posterior a conocer los resultados)

OP oportuna · SP solo_posterior · AU ausencia_con_observacion_suficiente · NE no_evaluable. Las 7 configuraciones son clasificaciones DERIVADAS de los registros; las emisiones reales van aparte.

Población principal: original 1/25 → revisada 15/25.

## 1. Episodios: original frente a revisado

| Episodio | Principal orig. | Principal rev. | Requisitos no verificados (rev.) | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisión real oportuna (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| escaneo_sostenido-r2 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 26.56 |
| inundacion_http-r1 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 24.9 |
| dns_inusual-r3 | no | no | captura_sin_errores_relevantes | NE | NE | NE | OP | OP | OP | OP | 20.19 |
| inundacion_http-r4 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 24.2 |
| inundacion_http-r2 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 25.43 |
| inundacion_http-r3 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 25.36 |
| escaneo_sostenido-r4 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 21.97 |
| escaneo_sostenido-r5 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 35.63 |
| escaneo_breve-r5 | no | sí | — | SP | SP | NE→AU | SP | SP | SP | SP | no |
| fuerza_bruta_http-r3 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 23.59 |
| fuerza_bruta_http-r5 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 23.68 |
| dns_inusual-r5 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 21.88 |
| escaneo_sostenido-r3 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 22.01 |
| dns_inusual-r2 | no | sí | — | NE→AU | NE→AU | NE→AU | OP | OP | OP | OP | 25.85 |
| fuerza_bruta_http-r2 | no | no | captura_sin_errores_relevantes | OP | OP | OP | OP | OP | OP | OP | 18.84 |
| fuerza_bruta_http-r4 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 18.44 |
| dns_inusual-r1 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 17.22 |
| escaneo_breve-r1 | no | sí | — | OP | OP | SP | OP | OP | OP | OP | 16.4 |
| escaneo_breve-r4 | no | no | captura_sin_errores_relevantes | SP | SP | NE | SP | SP | SP | SP | no |
| escaneo_breve-r3 | sí | sí | — | SP | SP | AU | SP | SP | SP | SP | no |
| dns_inusual-r4 | no | sí | — | NE→AU | NE→AU | NE→AU | OP | OP | OP | OP | 23.88 |
| fuerza_bruta_http-r1 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 25.14 |
| inundacion_http-r5 | no | sí | — | OP | OP | OP | OP | OP | OP | OP | 29.32 |
| escaneo_breve-r2 | no | sí | — | SP | SP | SP | SP | SP | SP | SP | no |
| escaneo_sostenido-r1 | no | no | cobertura_posterior, continuidad | OP | OP | OP | OP | OP | OP | OP | 39.61 |

Señales, primeras señales y emisiones idénticas entre original y revisado en todos los episodios: sí

## 2. Tabla 8 revisada (población principal revisada, por familia)

| Familia | Episodios | IF_0.05 | IF_0.03 | IF_0.01 | HEUR | HIB_0.05 | HIB_0.03 | HIB_0.01 | Emisión real oportuna |
|---|---|---|---|---|---|---|---|---|---|
| DNS inusual | 3 | OP1 AU2 | OP1 AU2 | OP1 AU2 | OP3 | OP3 | OP3 | OP3 | 3/3 |
| Escaneo breve | 4 | OP1 SP3 | OP1 SP3 | SP2 AU2 | OP1 SP3 | OP1 SP3 | OP1 SP3 | OP1 SP3 | 1/4 |
| Escaneo sostenido | 4 | OP4 | OP4 | OP4 | OP4 | OP4 | OP4 | OP4 | 4/4 |
| Fuerza bruta HTTP | 3 | OP3 | OP3 | OP3 | OP3 | OP3 | OP3 | OP3 | 3/3 |
| Inundación HTTP | 1 | OP1 | OP1 | OP1 | OP1 | OP1 | OP1 | OP1 | 1/1 |

Tabla 8 original (1 episodio):

- Escaneo breve: 1 episodio(s); IF_0.05 SP1; IF_0.03 SP1; IF_0.01 AU1; HEUR SP1; HIB_0.05 SP1; HIB_0.03 SP1; HIB_0.01 SP1

## 3. Control normal (sin cambios entre original y revisado: idéntico)

Tramo 2026-11-01T07:32:00+00:00 – 2026-11-01T08:05:00+00:00; requeridas 2644, decididas 2644, cobertura 1.0.

| Configuración | Falsas alarmas | Tasa entre decididas | Cotas sobre requeridas |
|---|---|---|---|
| IF_0.05 | 395 / 2644 | 14.94 % | [14.94, 14.94] % |
| IF_0.03 | 254 / 2644 | 9.61 % | [9.61, 9.61] % |
| IF_0.01 | 83 / 2644 | 3.14 % | [3.14, 3.14] % |
| HEUR | 92 / 2644 | 3.48 % | [3.48, 3.48] % |
| HIB_0.05 | 466 / 2644 | 17.62 % | [17.62, 17.62] % |
| HIB_0.03 | 336 / 2644 | 12.71 % | [12.71, 12.71] % |
| HIB_0.01 | 171 / 2644 | 6.47 % | [6.47, 6.47] % |

Solapamiento IF/HEUR en el control (HIB = IF ∪ HEUR):

| α | IF | HEUR | IF y HEUR | HEUR sin IF (lo que añade HIB) | HIB |
|---|---|---|---|---|---|
| 0.05 | 395 | 92 | 21 | 71 | 466 |
| 0.03 | 254 | 92 | 10 | 82 | 336 |
| 0.01 | 83 | 92 | 4 | 88 | 171 |

HEUR por tipo: {'dns_entropy': 88, 'http_abuse': 4}; por entidad: {'10.10.10.20': 88, '10.10.20.26': 4}

## 4. Suricata: los dos criterios (sin elegir)

| Episodio | Calidad ±60 s: estado | drops ±60 | Integridad [−120, +90]: drops | Periodo integridad |
|---|---|---|---|---|
| escaneo_sostenido-r2 | completa | 0 | 0 | 08:06:39–08:11:15 |
| inundacion_http-r1 | completa | 0 | 11 | 08:11:15–08:16:15 |
| dns_inusual-r3 | degradada | 28 | 28 | 08:16:15–08:21:15 |
| inundacion_http-r4 | degradada | 182 | 182 | 08:21:15–08:26:15 |
| inundacion_http-r2 | degradada | 111 | 111 | 08:26:15–08:31:15 |
| inundacion_http-r3 | degradada | 1146 | 1483 | 08:31:15–08:36:15 |
| escaneo_sostenido-r4 | completa | 0 | 0 | 08:36:15–08:40:51 |
| escaneo_sostenido-r5 | completa | 0 | 0 | 08:40:51–08:45:26 |
| escaneo_breve-r5 | completa | 0 | 0 | 08:45:26–08:49:14 |
| fuerza_bruta_http-r3 | degradada | 61 | 61 | 08:49:14–08:54:14 |
| fuerza_bruta_http-r5 | completa | 0 | 0 | 08:54:14–08:59:14 |
| dns_inusual-r5 | degradada | 100 | 100 | 08:59:14–09:04:14 |
| escaneo_sostenido-r3 | completa | 0 | 0 | 09:04:14–09:08:49 |
| dns_inusual-r2 | completa | 0 | 0 | 09:08:49–09:13:49 |
| fuerza_bruta_http-r2 | degradada | 97 | 97 | 09:13:49–09:18:49 |
| fuerza_bruta_http-r4 | completa | 0 | 0 | 09:18:49–09:23:49 |
| dns_inusual-r1 | completa | 0 | 0 | 09:23:49–09:28:49 |
| escaneo_breve-r1 | completa | 0 | 0 | 09:28:49–09:32:36 |
| escaneo_breve-r4 | degradada | 58 | 58 | 09:32:36–09:36:24 |
| escaneo_breve-r3 | completa | 0 | 0 | 09:36:24–09:40:12 |
| dns_inusual-r4 | completa | 0 | 0 | 09:40:12–09:45:12 |
| fuerza_bruta_http-r1 | completa | 0 | 0 | 09:45:12–09:50:12 |
| inundacion_http-r5 | completa | 0 | 0 | 09:50:12–09:55:12 |
| escaneo_breve-r2 | completa | 0 | 0 | 09:55:12–09:59:00 |
| escaneo_sostenido-r1 | completa | 0 | 0 | 09:59:00–10:03:35 |

Análisis adicional (no sustituye al principal): un solo intervalo para calidad e integridad → ±60 s: 16/25; [−120, +90]: 15/25; principal: 15/25.
Diferencia ±60 frente a principal: ['inundacion_http-r1'].
