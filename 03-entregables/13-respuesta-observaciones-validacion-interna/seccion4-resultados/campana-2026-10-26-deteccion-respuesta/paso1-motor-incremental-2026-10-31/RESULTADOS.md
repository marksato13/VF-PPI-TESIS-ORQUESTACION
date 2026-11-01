# Paso 1 — resultados de las corridas offline (generado por tablas_p1.py)

Tiempos medidos **offline** con el arnés de replay sobre la evidencia congelada de la campaña A, en el
Sensor1 (4 núcleos, `nice -n 15`, con el motor desplegado en sombra activo). No son latencias de
detección en vivo ni garantizan el funcionamiento en vivo: eso se mide en el paso 2.

## 1. Equivalencia de registros

| A (referencia) | B (candidato) | registros A / B | claves comunes | solo A | solo B | duplicados A / B | campos distintos | mismo orden | arranques A / B | equivalente |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| r1-ref-perfil | r2-cand-verif | 16069 / 16069 | 16068 | 0 | 0 | 0 / 0 | ninguno | sí | 1 / 1 | **sí** |
| r1-ref-perfil | r3-cand | 16069 / 16069 | 16068 | 0 | 0 | 0 / 0 | ninguno | sí | 1 / 1 | **sí** |
| r2-cand-verif | r3-cand | 16069 / 16069 | 16068 | 0 | 0 | 0 / 0 | ninguno | sí | 1 / 1 | **sí** |
| r4-ref-reinicio | r4-cand-reinicio | 2302 / 2302 | 2300 | 0 | 0 | 0 / 0 | ninguno | sí | 2 / 2 | **sí** |
| r4-ref-reinicio | r4-cand-reinicio-9b4cf2b | 2302 / 2302 | 2300 | 0 | 0 | 0 / 0 | ninguno | sí | 2 / 2 | **sí** |
| r4-ref-reinicio | r5-cand-reinicio-tiempos | 2302 / 2302 | 2300 | 0 | 0 | 0 / 0 | ninguno | sí | 2 / 2 | **sí** |

Campos excluidos de la comparación: `decidido_en` (solo existe en el candidato desde 9b4cf2b). Todos los demás campos, `logged_at` incluido, se comparan.

- r2-cand-verif: decisiones {'PERMIT': 14081, 'ALERT': 1986}; ventanas no evaluadas {'ventana_no_regenerada': 1}; score nulo 4965; con `pendiente_desde` 9089; `decidido_en` > `logged_at`: 0 de 0.
- r3-cand: decisiones {'PERMIT': 14081, 'ALERT': 1986}; ventanas no evaluadas {'ventana_no_regenerada': 1}; score nulo 4965; con `pendiente_desde` 9089; `decidido_en` > `logged_at`: 0 de 16068.
- r3-cand: decisiones {'PERMIT': 14081, 'ALERT': 1986}; ventanas no evaluadas {'ventana_no_regenerada': 1}; score nulo 4965; con `pendiente_desde` 9089; `decidido_en` > `logged_at`: 0 de 16068.
- r4-cand-reinicio: decisiones {'PERMIT': 1976, 'ALERT': 324}; ventanas no evaluadas 0; score nulo 629; con `pendiente_desde` 1238; `decidido_en` > `logged_at`: 0 de 0.
- r4-cand-reinicio-9b4cf2b: decisiones {'PERMIT': 1976, 'ALERT': 324}; ventanas no evaluadas 0; score nulo 629; con `pendiente_desde` 1238; `decidido_en` > `logged_at`: 0 de 2300.
- r5-cand-reinicio-tiempos: decisiones {'PERMIT': 1976, 'ALERT': 324}; ventanas no evaluadas 0; score nulo 629; con `pendiente_desde` 1238; `decidido_en` > `logged_at`: 0 de 2300.

## 2. Verificación etapa por etapa (`--verificar-equivalencia`)

| Corrida | ciclos verificados | ciclos con alguna diferencia | fallos por comprobación | filas necesarias | filas candidatas | filas puntuadas en lote |
|---|---:|---:|---|---:|---:|---:|
| r2-cand-verif | 1225 | 0 | ninguno | 36248 | 38049 | 20297 |
| r4-cand-reinicio | 151 | 0 | ninguno | 5431 | 6502 | 3020 |
| r4-cand-reinicio-9b4cf2b | 151 | 0 | ninguno | 5431 | 6502 | 3020 |

Cada ciclo recalcula por la vía global de 7b275b8 y compara: deduplicación (mismos objetos y orden),
atribución, observaciones EVE, filas (valores de las 28 características incluidos), cobertura de las
ventanas que el original habría decidido y puntuación en lote frente a una llamada por fila (bit a bit).

## 3. Duración del ciclo completo por condición

### Referencia 7b275b8 (R1, con perfil por función)

| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |
|---|---:|---:|---:|---:|---:|---:|
| Control normal (08:01–08:35) | 205 | 7,74 | 9,69 | 10,13 | 13 | 6 |
| Normal fuera de episodios | 657 | 8,26 | 18,98 | 20,80 | 242 | 218 |
| Otros escenarios (escaneos, DNS, fuerza bruta) | 176 | 10,61 | 17,96 | 20,60 | 117 | 104 |
| Inundación HTTP | 60 | 24,10 | 33,38 | 34,46 | 60 | 60 |
| Recuperación tras inundación (230 s) | 105 | 33,67 | 36,77 | 37,98 | 103 | 102 |
| Todo el funcionamiento estable | 1203 | 9,00 | 33,40 | 37,98 | 535 | 490 |
| Calentamiento (230 s tras arrancar o reiniciar) | 22 | 0,57 | 1,40 | 1,51 | 0 | 0 |
| Primer ciclo tras arrancar | 1 | 1,60 | 1,60 | 1,60 | 0 | 0 |

### Candidato sin verificación (R3)

| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |
|---|---:|---:|---:|---:|---:|---:|
| Control normal (08:01–08:35) | 205 | 1,07 | 1,70 | 2,35 | 0 | 0 |
| Normal fuera de episodios | 657 | 0,88 | 2,01 | 2,88 | 0 | 0 |
| Otros escenarios (escaneos, DNS, fuerza bruta) | 176 | 1,57 | 3,90 | 5,23 | 0 | 0 |
| Inundación HTTP | 60 | 4,92 | 8,26 | 9,20 | 0 | 0 |
| Recuperación tras inundación (230 s) | 105 | 2,45 | 3,42 | 4,22 | 0 | 0 |
| Todo el funcionamiento estable | 1203 | 1,23 | 3,55 | 9,20 | 0 | 0 |
| Calentamiento (230 s tras arrancar o reiniciar) | 22 | 0,15 | 0,31 | 0,42 | 0 | 0 |
| Primer ciclo tras arrancar | 1 | 1,61 | 1,61 | 1,61 | 0 | 0 |

Duración = tiempo real entre el inicio del ciclo y su `sleep`, medido por el arnés. Presupuesto: paso de 10 s
(se informa también > 9,5 s). Condición asignada por la hora simulada del ciclo con las marcas de la campaña;
inundación = [inicio, fin + 30 s) de cada `inundacion_http`, recuperación = los 230 s siguientes.

## 4. Etapas (mediana / p95 / máx, en s)

### Referencia (R1): funciones envueltas por el arnés

| Etapa | Control normal | Normal fuera de episodios | Otros escenarios | Inundación HTTP | Recuperación tras inundación | Calentamiento | Primer ciclo tras arrancar |
|---|---:|---:|---:|---:|---:|---:|---:|
| `atribucion_s` | 0,95 / 1,19 / 1,43 | 0,95 / 2,07 / 2,45 | 1,12 / 2,02 / 2,35 | 2,51 / 3,59 / 3,87 | 3,27 / 3,82 / 4,06 | 0,09 / 0,16 / 0,17 | — |
| `cola_eve_lectura_s` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,03 | 0,00 / 0,01 / 0,02 | 0,01 / 0,01 / 0,02 | 0,00 / 0,00 / 0,01 | 0,00 / 0,00 / 0,00 | — |
| `deduplicacion_s` | 0,18 / 0,23 / 0,26 | 0,19 / 0,35 / 0,40 | 0,22 / 0,36 / 0,38 | 0,50 / 0,71 / 0,73 | 0,67 / 0,73 / 0,76 | 0,01 / 0,03 / 0,03 | 0,00 / 0,00 / 0,00 |
| `eve_observaciones_s` | 0,07 / 0,08 / 0,09 | 0,10 / 1,11 / 1,33 | 0,20 / 1,07 / 1,16 | 1,05 / 1,38 / 1,42 | 1,46 / 1,57 / 1,73 | 0,01 / 0,03 / 0,03 | — |
| `filas_s` | 5,61 / 6,91 / 7,39 | 6,19 / 14,56 / 15,92 | 7,80 / 13,94 / 15,54 | 17,78 / 25,91 / 26,93 | 27,23 / 29,59 / 31,45 | 0,16 / 0,50 / 0,58 | — |
| `heuristicos_s` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | — |
| `pcap_parseo_s` | 0,24 / 0,47 / 0,64 | 0,15 / 0,39 / 0,53 | 0,37 / 0,94 / 1,18 | 1,66 / 1,99 / 2,05 | 0,25 / 0,51 / 0,57 | 0,05 / 0,10 / 0,12 | — |
| `puntuacion_s` | 1,02 / 1,37 / 1,47 | 0,71 / 1,34 / 1,54 | 0,96 / 1,47 / 1,54 | 0,93 / 1,48 / 1,67 | 1,09 / 1,42 / 1,53 | 0,64 / 0,89 / 0,96 | — |

### Candidato (R3): etapas que registra el propio motor en `ciclos.jsonl`

| Etapa | Control normal | Normal fuera de episodios | Otros escenarios | Inundación HTTP | Recuperación tras inundación | Calentamiento | Primer ciclo tras arrancar |
|---|---:|---:|---:|---:|---:|---:|---:|
| `atribucion` | 0,21 / 0,36 / 0,47 | 0,16 / 0,40 / 0,81 | 0,28 / 0,85 / 1,31 | 0,78 / 1,32 / 1,92 | 0,50 / 0,74 / 1,11 | 0,03 / 0,07 / 0,08 | — |
| `decision_y_registro` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | — |
| `deduplicacion` | 0,30 / 0,40 / 0,51 | 0,31 / 0,57 / 0,96 | 0,41 / 0,68 / 0,76 | 1,01 / 1,41 / 1,56 | 0,95 / 1,09 / 1,13 | 0,02 / 0,03 / 0,04 | 0,00 / 0,00 / 0,00 |
| `eve_lectura` | 0,01 / 0,01 / 0,01 | 0,01 / 0,06 / 0,94 | 0,01 / 0,19 / 0,39 | 0,26 / 0,37 / 0,57 | 0,01 / 0,11 / 0,12 | 0,00 / 0,01 / 0,01 | 0,00 / 0,00 / 0,00 |
| `eve_observaciones` | 0,00 / 0,00 / 0,00 | 0,00 / 0,02 / 0,02 | 0,00 / 0,02 / 0,02 | 0,02 / 0,03 / 0,03 | 0,03 / 0,03 / 0,03 | 0,00 / 0,00 / 0,00 | — |
| `eve_poda` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,01 | 0,00 / 0,00 / 0,01 | 0,00 / 0,00 / 0,01 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `expiracion_y_escritura` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `filas` | 0,27 / 0,44 / 0,67 | 0,22 / 0,45 / 0,87 | 0,42 / 1,56 / 2,33 | 1,78 / 3,34 / 3,54 | 0,48 / 0,75 / 1,91 | 0,03 / 0,08 / 0,08 | — |
| `filtro_plano_control` | 0,02 / 0,02 / 0,02 | 0,02 / 0,03 / 0,03 | 0,02 / 0,03 / 0,03 | 0,04 / 0,05 / 0,06 | 0,05 / 0,06 / 0,06 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `pcap_parseo` | 0,16 / 0,43 / 0,67 | 0,05 / 0,40 / 0,73 | 0,23 / 0,89 / 1,17 | 1,12 / 2,14 / 2,31 | 0,18 / 0,49 / 0,89 | 0,04 / 0,08 / 0,18 | 0,00 / 0,00 / 0,00 |
| `pcap_poda` | 0,08 / 0,10 / 0,11 | 0,04 / 0,15 / 0,17 | 0,10 / 0,14 / 0,16 | 0,17 / 0,23 / 0,24 | 0,21 / 0,25 / 0,27 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `puntuacion` | 0,06 / 0,06 / 0,07 | 0,06 / 0,06 / 0,07 | 0,06 / 0,06 / 0,07 | 0,06 / 0,06 / 0,07 | 0,06 / 0,06 / 0,06 | 0,03 / 0,06 / 0,07 | — |
| `seleccion` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | — |
| `ciclo_completo_motor` | 1,07 / 1,70 / 2,35 | 0,88 / 2,01 / 2,88 | 1,57 / 3,90 / 5,23 | 4,92 / 8,26 / 9,20 | 2,45 / 3,42 / 4,22 | 0,15 / 0,31 / 0,42 | 0,00 / 0,00 / 0,00 |

### Candidato (R3): contadores máximos por condición

```json
{
 "arranque": {
  "decididas": 0,
  "entidades": 0,
  "filas_construidas": 0,
  "flujos_recalculados": 0,
  "no_evaluadas": 0,
  "paquetes_anillo": 0,
  "puntuadas": 0,
  "ventanas_pendientes": 0
 },
 "calentamiento": {
  "decididas": 25,
  "entidades": 19,
  "filas_construidas": 203,
  "flujos_recalculados": 49,
  "no_evaluadas": 0,
  "paquetes_anillo": 31283,
  "puntuadas": 15,
  "ventanas_pendientes": 11
 },
 "control": {
  "decididas": 31,
  "entidades": 23,
  "filas_construidas": 40,
  "flujos_recalculados": 144,
  "no_evaluadas": 0,
  "paquetes_anillo": 184950,
  "puntuadas": 23,
  "ventanas_pendientes": 20
 },
 "inundacion": {
  "decididas": 42,
  "entidades": 24,
  "filas_construidas": 50,
  "flujos_recalculados": 2573,
  "no_evaluadas": 0,
  "paquetes_anillo": 505508,
  "puntuadas": 26,
  "ventanas_pendientes": 21
 },
 "normal": {
  "decididas": 47,
  "entidades": 25,
  "filas_construidas": 217,
  "flujos_recalculados": 520,
  "no_evaluadas": 1,
  "paquetes_anillo": 289698,
  "puntuadas": 24,
  "ventanas_pendientes": 22
 },
 "otros_ataques": {
  "decididas": 50,
  "entidades": 25,
  "filas_construidas": 60,
  "flujos_recalculados": 23167,
  "no_evaluadas": 0,
  "paquetes_anillo": 272514,
  "puntuadas": 24,
  "ventanas_pendientes": 23
 },
 "recuperacion": {
  "decididas": 56,
  "entidades": 24,
  "filas_construidas": 65,
  "flujos_recalculados": 13904,
  "no_evaluadas": 0,
  "paquetes_anillo": 531829,
  "puntuadas": 24,
  "ventanas_pendientes": 21
 }
}
```

### Candidato (R3): ciclos > 9,5 s

Ninguno.

### Reinicio a las 09:05 — referencia (R4, concurrente con R2: solo orientativo)

| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |
|---|---:|---:|---:|---:|---:|---:|
| Normal fuera de episodios | 50 | 17,42 | 19,08 | 19,95 | 41 | 40 |
| Otros escenarios (escaneos, DNS, fuerza bruta) | 18 | 15,51 | 17,46 | 18,66 | 18 | 18 |
| Inundación HTTP | 18 | 29,79 | 33,28 | 34,66 | 18 | 18 |
| Recuperación tras inundación (230 s) | 19 | 34,05 | 36,57 | 36,91 | 19 | 19 |
| Todo el funcionamiento estable | 105 | 17,98 | 35,05 | 36,91 | 96 | 95 |
| Calentamiento (230 s tras arrancar o reiniciar) | 44 | 23,93 | 29,12 | 29,58 | 44 | 44 |
| Primer ciclo tras arrancar | 2 | 39,52 | 44,44 | 44,98 | 2 | 2 |

### Reinicio a las 09:05 — candidato 9b4cf2b con verificación (fase C, incluye el recálculo global)

| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |
|---|---:|---:|---:|---:|---:|---:|
| Normal fuera de episodios | 50 | 18,03 | 20,56 | 21,32 | 44 | 44 |
| Otros escenarios (escaneos, DNS, fuerza bruta) | 18 | 16,58 | 20,42 | 21,11 | 18 | 18 |
| Inundación HTTP | 18 | 31,06 | 35,97 | 36,12 | 18 | 18 |
| Recuperación tras inundación (230 s) | 19 | 31,20 | 33,50 | 33,64 | 19 | 19 |
| Todo el funcionamiento estable | 105 | 19,26 | 33,44 | 36,12 | 99 | 99 |
| Calentamiento (230 s tras arrancar o reiniciar) | 44 | 24,04 | 27,42 | 29,25 | 44 | 44 |
| Primer ciclo tras arrancar | 2 | 54,38 | 62,58 | 63,49 | 2 | 2 |

### Reinicio a las 09:05 — candidato 9b4cf2b solo, sin verificación (R5)

| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |
|---|---:|---:|---:|---:|---:|---:|
| Normal fuera de episodios | 50 | 1,66 | 2,26 | 2,79 | 0 | 0 |
| Otros escenarios (escaneos, DNS, fuerza bruta) | 18 | 2,12 | 4,20 | 4,68 | 0 | 0 |
| Inundación HTTP | 18 | 5,18 | 8,20 | 8,50 | 0 | 0 |
| Recuperación tras inundación (230 s) | 19 | 2,63 | 3,31 | 3,64 | 0 | 0 |
| Todo el funcionamiento estable | 105 | 1,96 | 7,09 | 8,50 | 0 | 0 |
| Calentamiento (230 s tras arrancar o reiniciar) | 44 | 2,37 | 5,39 | 7,28 | 0 | 0 |
| Primer ciclo tras arrancar | 2 | 25,82 | 28,07 | 28,32 | 2 | 2 |

### R5: etapas del candidato tras el reinicio

| Etapa | Normal fuera de episodios | Otros escenarios | Inundación HTTP | Recuperación tras inundación | Calentamiento | Primer ciclo tras arrancar |
|---|---:|---:|---:|---:|---:|---:|
| `atribucion` | 0,31 / 0,47 / 0,55 | 0,39 / 0,90 / 1,02 | 0,80 / 1,39 / 1,48 | 0,53 / 0,77 / 0,88 | 0,47 / 0,97 / 1,29 | 4,91 / 5,12 / 5,15 |
| `decision_y_registro` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `deduplicacion` | 0,45 / 0,55 / 0,56 | 0,48 / 0,70 / 0,70 | 1,07 / 1,37 / 1,50 | 0,98 / 1,06 / 1,13 | 0,87 / 1,07 / 1,08 | 4,55 / 4,72 / 4,74 |
| `eve_lectura` | 0,01 / 0,54 / 0,84 | 0,01 / 0,32 / 0,35 | 0,26 / 0,36 / 0,37 | 0,01 / 0,11 / 0,12 | 0,01 / 0,26 / 0,36 | 0,00 / 0,00 / 0,00 |
| `eve_observaciones` | 0,02 / 0,02 / 0,02 | 0,01 / 0,02 / 0,02 | 0,02 / 0,03 / 0,03 | 0,03 / 0,03 / 0,03 | 0,00 / 0,01 / 0,02 | 0,00 / 0,00 / 0,00 |
| `eve_poda` | 0,00 / 0,01 / 0,01 | 0,00 / 0,01 / 0,01 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `expiracion_y_escritura` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,01 / 0,01 |
| `filas` | 0,33 / 0,54 / 0,74 | 0,51 / 2,03 / 2,08 | 2,18 / 3,46 / 3,49 | 0,49 / 1,27 / 1,28 | 0,44 / 2,02 / 2,84 | 1,97 / 3,40 / 3,56 |
| `filtro_plano_control` | 0,02 / 0,02 / 0,03 | 0,02 / 0,02 / 0,02 | 0,04 / 0,05 / 0,05 | 0,05 / 0,05 / 0,05 | 0,04 / 0,05 / 0,05 | 0,04 / 0,04 / 0,04 |
| `pcap_parseo` | 0,20 / 0,35 / 0,43 | 0,29 / 0,92 / 1,01 | 1,11 / 1,80 / 2,13 | 0,24 / 0,41 / 0,46 | 0,18 / 1,56 / 1,87 | 13,19 / 13,34 / 13,36 |
| `pcap_poda` | 0,10 / 0,13 / 0,14 | 0,11 / 0,14 / 0,14 | 0,18 / 0,22 / 0,23 | 0,20 / 0,23 / 0,26 | 0,15 / 0,19 / 0,19 | 0,15 / 0,16 / 0,16 |
| `puntuacion` | 0,06 / 0,06 / 0,07 | 0,06 / 0,06 / 0,06 | 0,06 / 0,06 / 0,06 | 0,06 / 0,06 / 0,06 | 0,06 / 0,06 / 0,07 | 0,08 / 0,09 / 0,09 |
| `seleccion` | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| `ciclo_completo_motor` | 1,65 / 2,26 / 2,79 | 2,12 / 4,20 / 4,68 | 5,18 / 8,20 / 8,50 | 2,63 / 3,31 / 3,64 | 2,37 / 5,39 / 7,28 | 24,90 / 26,54 / 26,72 |

R5, ciclos > 9,5 s: 08:55:00 (28,32 s), 09:05:00 (23,33 s).

