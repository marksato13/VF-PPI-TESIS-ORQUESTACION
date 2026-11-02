# HTTP, confusiones entre reglas y renovaciones

## 1. Qué disparaba y sobre quién (replay de referencia de la Etapa 2)

Matriz de ventanas del atacante por escenario y regla (`resultados/http/matriz-reglas-ref.json`, con el episodio ampliado 60 s tras su fin):

| Escenario | brute_force | http_abuse | port_scan | dns_entropy | IF ALERT |
|---|---|---|---|---|---|
| inundacion_http | 0 | 75 | **9** | 0 | 50 |
| fuerza_bruta_http | 75 | 0 | **8** | 0 | 75 |
| escaneo_sostenido | **4** | **15** | 41 | 0 | 32 |
| escaneo_breve | **2** | **4** | 16 | 0 | 7 |
| dns_inusual | **1** | **6** | 0 | 72 | 19 |
| fuera de todo episodio | **34** | **23** | 0 | 0 | 34 |

Sobre legítimos: `dns_entropy` en DC1 (382) y en 10.10.20.22 (4), ver `DNS.md`; y `http_abuse` en **10.10.20.26 (6 ventanas, LIMIT)**.

## 2. Causa 1: registros HTTP tardíos de Suricata

Las peticiones HTTP de la Kali «fuera de lugar» repiten el tipo de la última inundación (`/` a :80) o fuerza bruta (`/auth` a :18081). Aparecen en dos sitios:

- en los **60 s posteriores al fin** de cada inundación o fuerza bruta;
- a los 4–6 s del **inicio del episodio siguiente**, sea DNS o escaneo.

Contraste con el cable (`resultados/http/http-kali-cable-3b.json`, y el recuento de **todas** las tramas TCP, no solo SYN):

| Intervalo | Peticiones en el EVE | Tramas TCP Kali↔puerto en el cable |
|---|---|---|
| dns_inusual-r5, 09:01:20–09:02:51 | 196 `/auth` | **0** |
| escaneo_breve-r1, 09:30:53–09:32:27 | 317 `/auth` | **0** |
| escaneo_sostenido-r5, 08:43:16–08:44:53 | 976 `/` | 0 SYN |
| cola de inundacion_http-r1, 08:14:46–08:15:50 | 71 | **0** |
| cola de fuerza_bruta_http-r3 (90–160 s) | ~420 | 0 |
| control: fuerza_bruta_http-r3, 08:51:20–08:51:30 | — | 15 116 |

Interpretación: Suricata registra las transacciones de flujos ya terminados cuando procesa su vencimiento, y les pone la marca del paquete que está tratando en ese momento. Es coherente con que los vencimientos se procesen cuando llega tráfico nuevo al hilo. **Estas peticiones no existieron en el cable en ese intervalo.**

**Corrige la conclusión C10 de la Etapa 2.** Las «40 peticiones `curl GET /auth` concurrentes al escaneo r1, de procedencia no registrada» son registros tardíos de la fuerza bruta r4. El escaneo r1 no tuvo HTTP concurrente.

**Cambio: vista HTTP de los heurísticos** (`scripts/engine/http_heuristica.py`, `VistaHttp`). Sin cambiar el IF:

- Un evento HTTP cuenta solo si **su flujo** (5-tupla, en cualquier sentido) tiene alguna trama en el cable a ≤ 2 s de la marca del evento.
- Es causal: solo usa tramas con marca ≤ fin de ventana. Una transacción real tiene su petición antes de la marca del evento.
- Copias del espejo: mismo (`flow_id`, `tx_id`, `url`).
- `brute_force` y `http_abuse` solo leen la vista (`httph_*`). Cada decisión registra `http_vista`, con los registros tardíos excluidos.

**Pendiente (fuera del alcance de los heurísticos).** Las características L7 del IF (`http_request_rate_60s`, `http_auth_failure_ratio_60s`…) y el `auth_failure_heuristic` interno del motor, que convierte PERMIT en ALERT, **siguen** contando los registros tardíos. Son parte del contrato del modelo. Explica parte de las 34 ventanas ALERT del atacante fuera de episodio.

## 3. Causa 2: http_abuse sobre el cliente legítimo

Picos de peticiones HTTP en 60 s, sin copias (`resultados/http/picos-http-3b.json`):

| Origen | Máximo en 60 s |
|---|---|
| Kali en inundación (5 episodios) | 17 595 – 18 386 |
| Kali en fuerza bruta (5 episodios) | 7 919 – 8 189 (> 99 % 401) |
| 10.10.20.26 (legítimo, `/api/ok`, `/estatico/*`, 200) | **117** |
| 10.10.20.24 / .22 / .21 / .23 / .25 | 88 / 85 / 50 / 34 / 16 |

Con el umbral de 100, el generador legítimo recibía LIMIT. **Nuevo umbral: 600/60 s** (5,1 veces el pico legítimo). Una inundación lo alcanza en unos 2 s (unas 300 peticiones/s). Igual que en DNS, es un solo día del mismo laboratorio.

## 4. Causa 3: inundación y fuerza bruta → port_scan

Las 17 ventanas son **posteriores** al fin (`packet_count_10s = 0`). Sin SYN en los últimos 10 s, `syn_completion_ratio_10s` vale 0 por la división segura, y los miles de intentos al puerto 80 o 18081 de los 30 s anteriores cumplían la rama «ráfaga» (≥ 200 intentos con ≤ 10 % completados), que no miraba los puertos.

**Cambio:** la rama de ráfaga exige `unique_dst_port_ratio_30s ≥ 0,1`. Un escaneo breve da 0,499 (tope del espejo) y uno sostenido 0,99–1,0. Una inundación o fuerza bruta a un puerto da ≈ 0. Las 37 ventanas `port_scan` del atacante con vector volcado (puntuadas, con paquetes) cumplen la condición. Las otras 37 son ventanas sin paquetes, sin vector en el volcado: colas de escaneos y las 17 de inundación o fuerza bruta. El replay de la candidata muestra cuáles se conservan (`VALIDACION.md`). Detalle en `resultados/http/rasgos-port-scan.txt`.

## 5. Fuerza bruta frente a escaneo

No hay `port_scan` durante la fuerza bruta activa: las 8 ventanas eran de la cola posterior (causa 3). Hay `brute_force` durante los escaneos, pero es la causa 1: registros tardíos de la fuerza bruta anterior.

## 6. Renovaciones

Implementado en `publicar_feed_v2.py` (integración con la vía rápida en `VIA-RAPIDA-ESCANEO.md` §4). Cada acción lleva su intervalo de evidencia:

- reglas por ventanas: (A − retrospectiva, A], con 30 s para port_scan y 60 s para el resto;
- vía rápida: (primer intento, disparo].

Con una restricción vigente para el mismo (IP, destino, alcance):

- **escalada** si la acción nueva es más severa;
- **renovada** solo si la evidencia empieza cuando acaba la de la vigente (`evidencia_desde ≥ evidencia_hasta` previa), es decir, evidencia **nueva**;
- **mantenida** en otro caso: no amplía la caducidad, no llama a la escalada y queda registrada con su motivo.

`score != None` ya no se usa como sustituto de evidencia. Releer el registro no extiende nada.

## 7. ¿Se conservan las detecciones?

Pruebas unitarias (`tests/test_etapa3_http.py`, 10 pruebas):

- fuerza bruta (7 900 peticiones, 100 % 401) → brute_force;
- inundación (18 000) → http_abuse;
- pico legítimo (117) → nada;
- umbral justo;
- solo registros tardíos → nada;
- cola de inundación → no es port_scan;
- escaneo breve y sostenido → port_scan;
- causalidad y copias de la vista HTTP.

La confirmación sobre los 25 episodios está en `VALIDACION.md`.
