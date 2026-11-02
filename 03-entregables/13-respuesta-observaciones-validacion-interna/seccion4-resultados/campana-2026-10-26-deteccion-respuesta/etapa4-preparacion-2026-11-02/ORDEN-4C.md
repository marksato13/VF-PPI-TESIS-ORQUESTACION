# Orden de la campaña A nueva (4C) — publicado antes de ejecutar

> **Estado: preparado, no ejecutado.** Este orden se fija y se publica **antes** de la 4C. No se cambia la
> semilla a la vista del orden ni de los resultados. Si el orden cambiara, la 4C sería otra campaña y se
> publicaría como tal.

## 1. Regla y procedencia

| Elemento | Valor |
|---|---|
| Semilla | `20261102` (regla fijada antes de calcular el orden: la fecha de la preparación; el 3B usó `20261026`) |
| Configuración | [`escenarios-4c.json`](escenarios-4c.json), sha256 (bytes LF, los mismos de GitHub) `73c0b204d1e6f8844f23d6ec3c8c30732b5084f2fea3df96d26a2c2a7927aacd` |
| Diferencia con el 3B | solo `semilla`, `_campana` y `_nota_4c`. Escenarios, parámetros, origen `10.10.20.30`, lista blanca y tiempos 60/120/90 son los de `escenarios/escenarios.json` (sha256 `67798012…`) |
| Cálculo del orden | `generar_campana.plan_orden` (sha256 `c586d813…`; la función es idéntica en el generador con compuerta `scripts-4c/generar_campana.py`, `99e6bdae…`, que es el que ejecuta la Kali en la 4C: el orden no cambia), por [`evidencia/lectura-laboratorio/orden_4c.py`](evidencia/lectura-laboratorio/orden_4c.py) |
| Configuración de análisis | [`config-campana-4c.json`](config-campana-4c.json), sha256 `f177d9bb18c2b9c93f3829f6ffd60a65a81e42d598d3b587719f0d3a1f2da5f9` |
| Diseño | 5 escenarios × 5 repeticiones = 25 episodios; 7 configuraciones derivadas (IF a α 0,05 / 0,03 / 0,01, HEUR, HIB a los tres α) y la vía rápida **aparte** |

## 2. Orden y horario estimado

Tiempos relativos al lanzamiento del generador (`t = 0`): 60 s de calentamiento, 120 s de contexto antes de cada
episodio y 90 s de observación después. Las duraciones son las **medias reales del 3B** por escenario (mismos
parámetros); los escaneos no tienen duración objetivo, se registra la del comando.

| # | Episodio | Inicio est. (s) | Fin est. (s) | # | Episodio | Inicio est. (s) | Fin est. (s) |
|---|---|---|---|---|---|---|---|
| 1 | inundacion_http-r4 | 180 | 270 | 14 | dns_inusual-r4 | 3 886 | 3 976 |
| 2 | fuerza_bruta_http-r4 | 480 | 570 | 15 | escaneo_breve-r5 | 4 186 | 4 204 |
| 3 | dns_inusual-r1 | 780 | 870 | 16 | inundacion_http-r2 | 4 414 | 4 504 |
| 4 | fuerza_bruta_http-r3 | 1 080 | 1 169 | 17 | inundacion_http-r1 | 4 714 | 4 804 |
| 5 | dns_inusual-r3 | 1 379 | 1 469 | 18 | escaneo_sostenido-r3 | 5 014 | 5 079 |
| 6 | inundacion_http-r3 | 1 679 | 1 769 | 19 | escaneo_sostenido-r1 | 5 289 | 5 355 |
| 7 | fuerza_bruta_http-r1 | 1 979 | 2 069 | 20 | dns_inusual-r2 | 5 565 | 5 655 |
| 8 | escaneo_breve-r4 | 2 279 | 2 297 | 21 | inundacion_http-r5 | 5 865 | 5 955 |
| 9 | escaneo_sostenido-r5 | 2 507 | 2 573 | 22 | dns_inusual-r5 | 6 165 | 6 255 |
| 10 | fuerza_bruta_http-r5 | 2 783 | 2 873 | 23 | escaneo_breve-r3 | 6 465 | 6 483 |
| 11 | escaneo_breve-r2 | 3 083 | 3 100 | 24 | escaneo_breve-r1 | 6 693 | 6 711 |
| 12 | fuerza_bruta_http-r2 | 3 310 | 3 400 | 25 | escaneo_sostenido-r4 | 6 921 | 6 986 |
| 13 | escaneo_sostenido-r2 | 3 610 | 3 676 | | | | |

Duraciones medias del 3B (n = 5 cada una): DNS 89,9 s; escaneo breve 17,8 s; escaneo sostenido 65,9 s; fuerza
bruta 89,8 s; inundación 89,9 s. Fuente: [`evidencia/lectura-laboratorio/estimar_duracion_4c.txt`](evidencia/lectura-laboratorio/estimar_duracion_4c.txt)
(generado por `estimar_duracion_4c.py` sobre `ejecucion-3b-2026-11-01/evidencia/sensor/copias/marcas.jsonl`).

## 3. Duración total estimada

| Tramo | Duración |
|---|---|
| Archivo abierto antes del control | ≥ 10 min (≥ 230 s exigidos por `b01`; 10 min de margen para el calentamiento del motor y del factor) |
| Control normal declarado | 30 min (`b01 4c`, mínimo 1 800 s) |
| Batería | ≈ 6 987 s ≈ **1 h 56 min** (el 3B real duró 6 986,7 s) |
| Margen de cierre | ≥ 300 s tras `fin_ultimo` + repetición (`s30`) |
| **Total con el archivo abierto** | ≈ **2 h 45 min – 3 h** |

El intervalo completo debe quedar **fuera** de la hora del `logrotate` diario de `eve.json` (copytruncate): una
rotación durante la 4C detiene `s30` (PROTOCOLO-4C §2).

## 4. Qué no se hace

- No se reordena, no se repiten episodios sueltos y no se sustituyen episodios fallidos: un episodio que falla se
  publica como `ejecutado` con su estado y queda en la contabilidad (PROTOCOLO-4C §8).
- No se elige α a la vista de la 4C: las tres se publican.
