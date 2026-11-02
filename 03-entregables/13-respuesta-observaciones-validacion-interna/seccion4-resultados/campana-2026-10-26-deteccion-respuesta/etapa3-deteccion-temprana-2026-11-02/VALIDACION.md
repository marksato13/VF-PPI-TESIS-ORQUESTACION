# Validación: 25 episodios, control, reglas y rendimiento

> **Datos de desarrollo.** Los 25 episodios del 3B se han usado para diseñar los cambios de esta etapa. Sirven para comprobar que los cambios hacen lo que dicen y que no rompen nada, **no** como confirmación independiente. No se elige α con ellos.

## 1. Qué se ejecutó

- **Replay completo** del 3B (07:24:40–10:05:40) con la candidata (`b1ee393`; los commits posteriores no tocan el motor salvo un comentario). Entradas, arnés (`4694e38`), modelo, horizonte de 230 s, paso de 10 s, anillo de 5 s, disparo por eventos y reloj `coste`: **idénticos** a la referencia `sec-opt-6b6ef82` de la Etapa 2. Una sola corrida en el portátil, sin otros replays en paralelo.
- **Analizador:** `analizar_3b.py` **sin modificar**, con los mismos argumentos: inventario 07:24:40–10:05:30, control 07:32–08:05, mismas marcas, configuración, destinos, integridad v2 y calidad de fuentes. No se cambia el criterio temporal ni de admisión, y no se recupera ningún episodio excluido.
- **Vía rápida:** se añade **aparte** (`scripts/etapa3/via_rapida_episodios.py`), sin tocar el analizador ni su salida.
- Guion: `guiones/analizar_e3.sh`.

## 2. El IF no cambia

Comparación clave a clave `sec-opt-6b6ef82` → Etapa 3 (`resultados/comparaciones/sec-opt-6b6ef82-vs-e3.json`):

| | |
|---|---|
| Claves | 12 773 en ambas |
| Estados (decisión / no elegible / cancelada) | 12 726 / 33 / 14 en ambas; 0 transiciones |
| Vectores distintos | **0** de 9 607 |
| Scores distintos | **0** |
| Decisiones del IF distintas | **0** de 12 726 |
| Claves con reglas distintas | 677 (esperado: es lo que cambia) |

Las 28 características, el escalador, el modelo y los tres α son los mismos.

## 3. Reglas: matriz por escenario

Ventanas del atacante con cada regla, con el episodio ampliado 60 s (`matriz_reglas.py`):

| Escenario | brute_force | http_abuse | port_scan | dns_entropy | IF ALERT |
|---|---|---|---|---|---|
| inundacion_http | 0 | 75 | **9 → 0** | 0 | 50 |
| fuerza_bruta_http | 75 | 0 | **8 → 0** | 0 | 75 |
| escaneo_sostenido | **4 → 0** | **15 → 0** | 41 | 0 | 32 |
| escaneo_breve | **2 → 0** | **4 → 0** | 16 | 0 | 7 |
| dns_inusual | **1 → 0** | **6 → 0** | 0 | 72 → 62 | 19 |
| fuera de todo episodio | **34 → 0** | **23 → 0** | 0 | 0 | 34 |

- Se conservan todas las detecciones propias: brute_force 75, http_abuse 75 y las colas de port_scan de los escaneos (16 y 41, sin cambio).
- dns_entropy baja de 72 a 62 ventanas por el umbral de 30: arranca unos 10 s más tarde, pero detecta los 5 episodios.
- Las 34 ALERT del IF fuera de episodio **siguen**: son del modelo y, en parte, de los registros HTTP tardíos en las características L7 (contrato del modelo, sin cambiar; ver `HTTP-CONFUSIONES-Y-RENOVACIONES.md` §2).

**Reglas sobre entidades que no son el atacante, en todo el replay:**

| | Etapa 2 (`6b6ef82`) | Etapa 3 |
|---|---|---|
| DC1 (10.10.10.20), dns_entropy → LIMIT | 382 | **0** |
| 10.10.20.22, dns_entropy → LIMIT | 4 | **0** |
| 10.10.20.26, http_abuse → LIMIT | 6 | **0** |
| **Total de ventanas con disparos heurísticos sobre legítimos** | **392** | **0** |

Las cifras son **ventanas** de decisión (entidad × ventana de 10 s) en las que una regla heurística disparó sobre un equipo que no es el atacante. **No** son equipos distintos (son 3: DC1, 10.10.20.22 y 10.10.20.26) ni bloqueos aplicados: en el replay no hay agentes ni nft, y el publicador agruparía ventanas consecutivas en una misma restricción. *Redacción corregida en el cierre técnico (antes: «restricciones heurísticas a legítimos»).*

## 4. Control (07:32–08:05; 2 622 ventanas; cobertura 1,0)

| Configuración | Etapa 2 | Etapa 3 |
|---|---|---|
| IF α 0,05 / 0,03 / 0,01 | 395 / 254 / 83 | 395 / 254 / 83 |
| HEUR | 92 | **0** |
| HIB α 0,05 / 0,03 / 0,01 | 466 / 336 / 171 | **395 / 254 / 83** |
| Vía rápida | — | **0** señales |

Por entidad, las 88 de HEUR sobre DC1 pasan a 0. Las falsas alarmas del IF (sobre todo 10.10.20.22 y 10.10.20.24, generadores con tráfico confundible) no cambian: son del modelo y **solo emiten señal, no restringen** (política `if_senal`).

## 5. Los 25 episodios

Población principal: **15/25**, con las mismas exclusiones que la Etapa 2.

Categorías (`oportuna` = alguna señal disponible antes del fin del episodio; es **detección**, no respuesta):

| Configuración | Población principal: oportuna / solo posterior / ausencia | Cambio respecto a la Etapa 2 |
|---|---|---|
| IF 0,05 | igual | 0 |
| IF 0,03 | igual | 0 |
| IF 0,01 | igual | 0 |
| HEUR | 12 / 3 / 0 | escaneo_breve-r1: oportuna → solo posterior |
| HIB 0,05 | 13 / 2 / 0 | 0 |
| HIB 0,03 | 13 / 2 / 0 | 0 |
| HIB 0,01 | 12 / 3 / 0 | escaneo_breve-r1: oportuna → solo posterior |
| **HEUR + vía rápida** | **15 / 0 / 0** (y 10/10 fuera de la población) | — |
| **HIB α + vía rápida** (los 3 α) | **15 / 0 / 0** | — |
| Vía rápida sola | 8 oportunas (los 8 escaneos en población); 7 sin señal (no son escaneos) | — |

**escaneo_breve-r1 empeora en HEUR, y es correcto.** En la Etapa 2 su «oportuna» venía de `brute_force` con registros HTTP tardíos de la fuerza bruta anterior, que no existían en el cable. Con la vista HTTP desaparece. La 1.ª señal propia (port_scan) llega a 22,5 s, después del fin.

**Escaneos breves** (`resultados/via-rapida/via-rapida-episodios-e3.json`):

| Episodio | Población | HEUR (ventanas) | Vía rápida: evidencia desde el inicio | Antes del fin | HEUR + R |
|---|---|---|---|---|---|
| r1 | sí | solo posterior | 13,23 s | 4,36 s | oportuna |
| r2 | sí | solo posterior | 13,25 s | 4,74 s | oportuna |
| r3 | sí | oportuna (16,5 s, por décimas; ver Etapa 2) | 13,23 s | 4,36 s | oportuna |
| r4 | no | solo posterior | 13,24 s | 4,75 s | oportuna |
| r5 | sí | solo posterior | 13,24 s | 4,75 s | oportuna |

Los 13,2 s desde el inicio corresponden a la fase de descubrimiento y la resolución inversa de nmap. La evidencia llega 0,10 s después de la ráfaga.

**Qué no dice esta tabla.** Mide la **evidencia** en tiempo de datos, como el analizador mide la disponibilidad del registro. No incluye publicación, entrega ni aplicación: eso está en el presupuesto del banco (`VIA-RAPIDA-ESCANEO.md` §6.4): 120/120 ejecuciones aplicadas antes del último SYN, con margen mínimo de 1,77 s (2,98 s con la alternativa C bajo carga). No prueba que el escaneo se detenga.

**DNS:** los 5 episodios siguen siendo oportunos en HEUR, con la 1.ª señal a 16,8–22,7 s (antes 7,5–13,2 s). Los episodios duran unos 90 s.

## 6. Rendimiento (R1–R4, criterio de la Etapa 2 sin cambiar)

`herramientas/rendimiento_secuencial.py` de la Etapa 2, sin modificar (`resultados/rendimiento/`):

| Segmento | `6b6ef82`: pared p95 / máx (s) | Etapa 3: pared p95 / máx (s) | R1–R4 |
|---|---|---|---|
| normal | 1,15 / 1,60 | 0,60 / 0,87 | cumple |
| inundación r1–r5 | 5,41–6,15 | 2,59–3,11 | cumple |
| recuperación r1–r5 | 2,80–3,37 / ≤ 3,97 | 1,41–1,62 / ≤ 2,03 | cumple |

**Cumple todo** en todos los segmentos. 0 ciclos > 10 s y 0 canceladas nuevas. Pendientes máximas y finales iguales. RSS máximo ~1,15 GB (igual).

Que la Etapa 3 salga **más rápida** no se atribuye al código: añade trabajo (dos vistas) y no quita nada. Las condiciones del portátil no eran las mismas (CPU del sistema p50: 22,5 % frente a 36,2 %). La conclusión válida es solo que **las vistas no rompen R1–R4 en el portátil**. El Sensor1 no se ha medido.

**Vía rápida** (`det-resumen`, banco): CPU máxima por bloque de 0,02–0,07 s en ficheros (A1/A2). En flujo (C) llega a 1,3 s sin carga y 5,5 s con carga, acumulada a lo largo del ensayo, con un tic de 20 ms. El coste en el Sensor1 está pendiente (`PROCEDIMIENTO-ETAPA4.md` §1).

## 7. Lo que queda abierto

1. Presupuesto en el laboratorio real (espejo, SSH, CPU de Sensor1): `VIA-RAPIDA-ESCANEO.md` §6.5.
2. Confirmación con **episodios nuevos** (campaña B, no autorizada): elegir α, respuesta efectiva al escaneo breve y efecto del LIMIT DNS.
3. Las características L7 del IF y los registros tardíos (contrato del modelo).
4. Suricata offline con reglas ET (comparador): el sistema lo terminó por memoria; no se ha relanzado.
