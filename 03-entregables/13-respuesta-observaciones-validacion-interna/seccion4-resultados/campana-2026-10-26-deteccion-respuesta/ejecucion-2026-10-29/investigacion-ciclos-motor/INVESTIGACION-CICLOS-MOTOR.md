# Por qué el motor alargó sus ciclos en la campaña A (2026-10-29)

**Conclusión.** Se suman dos causas, ambas medidas:

1. **Coste del motor proporcional al tráfico de toda su historia.** En cada ciclo, `extract_multilayer_v2.build_rows`
   recorre, para cada entidad y cada ventana, la lista completa de paquetes de todas las entidades de los últimos
   230 s. El trabajo del ciclo crece linealmente con el volumen de esa historia: r = 0,949 y unos 0,6 s por MB de PCAP.
   Con tráfico normal a factor horario 1,0 ya ronda los 10 s del paso; con la inundación HTTP llega a 45 s.
2. **Tolerancia sin margen.** Los ciclos que escriben decisiones aparecen separados por 10 o 20 s incluso en reposo,
   porque el paso es de 10 s y el PCAP rota cada 15 s. La tolerancia de continuidad del analizador es de 20 s, justo
   ese hueco natural. En cuanto el ciclo pasa de unos 9,5 s, los huecos de 20 s pasan a 21–23 s y la cobertura falla.

Nada de esto altera las características ni los scores, que siguen reproduciéndose desde el PCAP (684 de 689 exactas).
Lo que se degrada es la puntualidad y la continuidad del registro.

## 1. Duración del ciclo frente a volumen

Ciclo = decisiones con el mismo `inicio_ciclo`; trabajo = `max(logged_at) − inicio_ciclo`. Datos de
`evidencia/fuentes/motor_decision.log.gz`.

| Tramo | Periodo p50 | Trabajo p50 | Trabajo p90 | Trabajo máx | pk10 por ciclo p50 |
|---|---|---|---|---|---|
| Madrugada 03–05 | 10,0 s | 1,8 s | 2,4 s | 3,4 s | 68 |
| 07–08 | 10,0 s | 1,8 s | 2,4 s | 3,1 s | 68 |
| Control 08:01–08:35 | 10,9 s | 9,5 s | 11,4 s | 12,2 s | 2888 |
| Batería 08:35–10:33 | 16,5 s | 12,7 s | 24,4 s | 45,7 s | 4745 |

El salto se produce en el control, antes de cualquier ataque: el tráfico normal de los perfiles a factor 1,0 ya
multiplica el trabajo por 5.

`scripts/correlacion_ciclo_volumen.py` → `correlacion-ciclo-volumen.txt`: los MB de PCAP archivados en los 230 s
anteriores a cada ciclo (773 ciclos con historia completa) dan Pearson r = 0,949, pendiente 0,605 s/MB y ordenada
−0,29 s.

| MB en 230 s | Ciclos | Trabajo p50 | p90 | máx |
|---|---|---|---|---|
| 0–5 | 13 | 1,4 s | 1,8 s | 1,8 s |
| 5–20 | 561 | 9,3 s | 12,0 s | 21,2 s |
| 20–40 | 148 | 19,3 s | 23,2 s | 26,1 s |
| 40–60 | 28 | 23,3 s | 32,7 s | 43,5 s |
| 60–80 | 21 | 42,2 s | 45,3 s | 45,7 s |

## 2. Qué etapa consume el tiempo

`scripts/perfilar_ciclo_motor.py` (sensor, solo lectura) rehace sin conexión siete ciclos concretos con el mismo
código desplegado (motor sha `e2b2eb53…`, extractor `7130edae…`) y cronometra cada etapa → `perfil-ciclos.csv`.
Columnas: «Real» es la duración registrada del ciclo; «Paquetes» son los paquetes atribuidos en la historia de 230 s;
las demás son tiempos de etapa en segundos.

| Ciclo | Real | Paquetes | dedup | atrib | eve_r | **build_rows** | score | Suma |
|---|---|---|---|---|---|---|---|---|
| 07:56 (reposo) | 1,6 | 14 665 | 0,03 | 0,28 | 0,03 | **0,70** | 0,66 | 1,7 |
| 08:20 (control) | 10,4 | 66 560 | 0,19 | 0,98 | 0,07 | **4,75** | 1,69 | 7,7 |
| 08:49 (DNS) | 11,5 | 72 090 | 0,21 | 1,03 | 0,12 | **5,80** | 0,53 | 7,7 |
| 09:05 (inundación) | 44,6 | 229 512 | 0,76 | 3,46 | 1,55 | **25,13** | 2,84 | 33,9 |
| 09:08 (escaneo sost.) | 19,1 | 108 602 | 0,36 | 1,91 | 0,21 | **11,01** | 0,78 | 14,4 |
| 09:17 (escaneo breve) | 15,9 | 84 947 | 0,33 | 1,26 | 1,12 | **9,88** | 0,39 | 13,1 |
| 09:22 (fuerza bruta) | 20,6 | 116 333 | 0,44 | 1,81 | 0,60 | **14,29** | 0,13 | 17,4 |

`build_rows` es entre el 55 % y el 75 % del tiempo reproducido. El parseo de los PCAP nuevos es incremental y cuesta
menos de 1 s.

La suma reproducida explica entre el 74 % y el 100 % de la duración real. El resto, de hasta unos 11 s en el pico,
no está atribuido: en vivo, Suricata y tcpdump comparten la máquina con el motor (4 núcleos), y el perfil no incluye
el registro ni los heurísticos.

**Por qué escala así.** En `extract_multilayer_v2.py` líneas 539–577, para cada entidad y cada ancla (≈ 23 por
entidad en 230 s) se construye `p10` y `p30` filtrando **toda** la lista `packets`, y cuatro listas L7 filtrando
**todo** `apps`. Coste ≈ filas × (2·P + 4·A), con unas 400 filas por ciclo casi constantes.

El modelo encaja con una constante de 70–105 ns por comprobación:

| Ciclo | Comprobaciones | `build_rows` |
|---|---|---|
| 08:20 | 49 M | 4,75 s |
| 09:05 | 232 M | 25,1 s |

Además, el motor reconstruye cada ciclo las ~400 ventanas de la historia aunque solo necesita las pocas nuevas;
descarta el resto después, con `scored_windows`.

## 3. Por qué basta con unos 10 s para romper la cobertura

Huecos entre ciclos que registran decisiones, redondeados al segundo:

| Tramo | 10 s | 11–13 s | 20 s | 21–23 s |
|---|---|---|---|---|
| Madrugada | 495 | — | 112 | 0 |
| Control | 67 | 45 | 27 | 14 |

En reposo ya hay huecos de 20 s exactos. Un ciclo sin ninguna ventana completa no escribe nada, y eso pasa porque
`ventana_completa` depende de `marca_pcap`, que solo avanza cuando rota un fichero, cada 15 s, mientras el paso es de
10 s. El periodo es `max(10, trabajo + 0,5)` (`time.sleep(max(0.5, step − elapsed))`). Con un trabajo por encima de
9,5 s, cada hueco natural de 20 s pasa a ser de 2 × periodo, más de 20 s. El analizador (TOL_CONTINUIDAD_S = 20)
lo declara entonces discontinuidad.

## 4. Comprobación de una corrección posible, sin desplegar nada

Ejecutar `build_rows` **entidad por entidad**, pasando a cada llamada solo las observaciones de esa entidad, es
equivalente: la función solo usa el conjunto global para comprobar `capture_start ≤ primera observación`, y el motor
ya pasa el mínimo global. Medido en los mismos 7 ciclos (`perfil-ciclos.csv`, columnas `rows_por_entidad_s` y
`filas_identicas`):

| Ciclo | build_rows actual | por entidad | filas idénticas |
|---|---|---|---|
| 07:56 | 0,70 s | 0,26 s | sí |
| 08:20 | 4,75 s | 1,51 s | sí |
| 08:49 | 5,80 s | 1,75 s | sí |
| 09:05 | 25,13 s | 5,20 s | sí |
| 09:08 | 11,01 s | 2,98 s | sí |
| 09:17 | 9,88 s | 2,38 s | sí |
| 09:22 | 14,29 s | 2,54 s | sí |

Con eso, el trabajo reproducido del control bajaría de unos 7,7 s a unos 4,5 s. El pico de inundación bajaría de
unos 34 s a unos 14 s, aún por encima de 10 s, porque la Kali concentra casi todos los paquetes y sus 23 ventanas
siguen recorriéndolos todos. Para bajar de 10 s en el pico haría falta además construir solo las ventanas pendientes
(pasar a `build_rows` las observaciones de los últimos 30/60 s antes de la ventana más antigua por decidir) o indexar
por tiempo. Eso exige otra verificación de equivalencia que **no se ha hecho**.

## 4 bis. Validación en todos los ciclos (773)

`scripts/validar_build_rows_por_entidad.py` (sensor, solo lectura, 2 trabajadores con `nice`) repite la comparación en
**todos los ciclos con historia PCAP completa en el archivo**, de 07:19 a 10:39 UTC. Exige igualdad exacta de la lista
de filas: orden, claves y valores float. El agregado lo hace `scripts/resumir_validacion_por_entidad.py` →
`validacion-por-ciclo.csv` y `validacion-resumen.csv`.

| Tramo | Ciclos | Idénticos | Filas comparadas | Aceleración de build_rows (p50) | Trabajo real p50 / máx | Estimado por entidad p50 / p90 / máx | Ciclos > 9,5 s real → estimado |
|---|---|---|---|---|---|---|---|
| Previo 07:19–08:01 | 208 | 208 | 70 727 | 3,1× | 1,8 / 3,1 s | 1,2 / 1,6 / 2,1 s | 0 → 0 |
| Control | 155 | 155 | 57 165 | 3,9× | 9,5 / 12,2 s | 4,4 / 5,4 / 5,9 s | 76 → 0 |
| Batería | 387 | 387 | 153 712 | 4,4× | 12,7 / 45,7 s | 6,3 / 12,1 / 23,1 s | 369 → 97 |
| Posterior | 23 | 23 | 8 866 | 4,0× | 11,1 / 22,3 s | 5,6 / 9,9 / 11,4 s | 23 → 4 |
| **Total** | **773** | **773** | **290 470** | | | | |

**Equivalencia:** 773 de 773 ciclos idénticos, sin ninguna diferencia.

**Cómo se estima la duración.** El trabajo estimado es el real menos el ahorro medido en `build_rows`. Es una
estimación, no una medición en vivo: supone que el ahorro sin conexión se traslada tal cual y no corrige la parte del
ciclo que el perfil no reproduce.

**Batería, ciclos que seguirían por encima de 9,5 s, por escenario.** Un ciclo se asigna a un escenario si cae dentro
del episodio o en los 60 s siguientes.

| Escenario | Ciclos | Estimado > 9,5 s | Máx estimado |
|---|---|---|---|
| Inundación HTTP | 26 | 25 | 23,1 s |
| Fuerza bruta HTTP | 44 | 9 | 12,2 s |
| Escaneo sostenido | 36 | 7 | 11,5 s |
| DNS inusual | 53 | 1 | 11,6 s |
| Escaneo breve | 28 | 1 | 10,5 s |
| Pausas | 200 | 54 | 23,1 s |

Los ciclos de pausa por encima del límite son los que aún llevan la inundación anterior dentro de su historia de 230 s.

**Lectura:**
- **Lo que resuelve:** la partición por entidad devolvería el control y el tráfico normal a unos 4–6 s por ciclo,
  con margen frente al paso de 10 s, y dejaría casi todos los ataques por debajo del límite.
- **Lo que no resuelve:** la inundación HTTP, ni la cola de 230 s que deja detrás. Con ella la Kali sola concentra
  la mayoría de los ~230 k paquetes de la historia, y sus ~23 ventanas los recorren todos.
- **Para bajar de 10 s ahí** haría falta además la opción (b) de la sección 5, construir solo las ventanas
  pendientes, o indexar por tiempo dentro del extractor.

## 4 ter. «Solo ventanas pendientes»: validación en los 773 ciclos

`scripts/validar_build_rows_pendientes.py` (sensor, solo lectura) aplica la variante sin tocar el extractor:

- **Ventana mínima por entidad e:** `A_min(e)` es la primera ancla del rango de e (de su primera a su última
  observación, igual que `build_rows`) que no está en `scored_windows`. El motor dispone de ese conjunto; aquí se
  emula con las decisiones del registro anteriores al ciclo.
- **Entrada:** se pasan solo las observaciones posteriores a `A_min−30` (paquetes) o `A_min−60` (L7), más la primera
  y la última de la entidad.
- **Salida:** las filas con ventana ≥ `A_min`.

Se compara contra el `build_rows` global original:

- **Filas idénticas:** igualdad exacta, entidad a entidad, para ventanas ≥ `A_min`.
- **Cobertura:** toda ventana que el motor decidió en ese ciclo cae en ≥ `A_min`.

Agregado: `scripts/resumir_validacion_pendientes.py` → `pendientes-por-ciclo.csv` y `pendientes-resumen.csv`.

Una primera regla (`A_min` = última ventana registrada + 10 s) se descartó porque no cubría las ventanas que nacen
por detrás de la última decidida. La evidencia está en `pendientes-regla-ultima-descartada/`.

**Resultado:** 773 de 773 ciclos con filas idénticas y 773 de 773 con cobertura completa.

| Tramo | Ciclos | Aceleración vs global (p50) | Real p50 / máx | Por entidad p50 / máx | Solo pendientes p50 / p90 / máx | > 9,5 s: real → entidad → pendientes |
|---|---|---|---|---|---|---|
| Previo | 208 | 4,3× | 1,8 / 3,1 s | 1,2 / 2,2 s | 1,1 / 1,5 / 2,1 s | 0 → 0 → 0 |
| Control | 155 | 14,8× | 9,5 / 12,2 s | 3,3 / 5,7 s | 2,0 / 3,1 / 4,4 s | 76 → 0 → 0 |
| Batería | 387 | 17,5× | 12,7 / 45,7 s | 5,2 / 22,9 s | 3,7 / 8,3 / 20,3 s | 369 → 52 → 32 |
| Posterior | 23 | 17,5× | 11,1 / 22,3 s | 4,8 / 10,0 s | 3,3 / 6,3 / 7,3 s | 23 → 2 → 0 |
| **Total** | **773** | 14,0× | 10,4 / 45,7 s | 3,7 / 22,9 s | 2,2 / 6,2 / 20,3 s | 468 → 54 → 32 |

**Batería por escenario**, solo pendientes, con estimado > 9,5 s:

| Escenario | Ciclos | Estimado > 9,5 s | Máx estimado |
|---|---|---|---|
| DNS inusual | 53 | 0 | 6,9 s |
| Escaneo breve | 28 | 0 | 6,3 s |
| Escaneo sostenido | 36 | 0 | 8,9 s |
| Fuerza bruta HTTP | 44 | 0 | 8,3 s |
| Inundación HTTP | 26 | 19 | 20,3 s |
| Pausas | 200 | 13 | 17,2 s |

Las pausas por encima del límite arrastran la inundación anterior en su historia de 230 s.

**Lectura:**
- **Con las dos correcciones,** todos los escenarios salvo la inundación HTTP quedan por debajo de 9,5 s en todos sus
  ciclos, y el control baja a unos 2 s.
- **En la inundación** `build_rows` deja de ser el problema: queda en menos de 1 s. Lo que manda pasa a ser:
  - el resto del ciclo: `attribute_packets`, de unos 3,5 s en el pico;
  - deduplicación y EVE;
  - la parte que el perfil no reproduce.

  Todo eso crece con el volumen de los 230 s de historia y no se toca con estas variantes.

**Límites de la estimación:**
- **Qué se estima.** El trabajo estimado es el real menos el ahorro medido sin conexión. Las mediciones de tiempo
  varían entre corridas por la carga de la máquina: la partición por entidad dio 97 ciclos de batería por encima de
  9,5 s en la sección 4 bis y 52 en esta corrida.
- **Qué falta.** La cifra que vale es la que se mida en vivo con el motor corregido.
- **Cómo se emula `scored_windows`.** Se usa el registro; el motor real además marca como puntuadas las ventanas de
  entidades excluidas sin registrarlas. Aquí esas entidades se calculan completas, lo que hace la estimación de
  tiempo conservadora y no afecta a la igualdad.

## 5. Qué no se ha hecho y qué decide Mark

- **No se ha tocado nada desplegado.** Motor, extractor y servicios siguen iguales, en modo sombra. Todo lo anterior
  se reprodujo sin conexión sobre el PCAP archivado y las fuentes congeladas.
- **Opciones, sin recomendar todavía ninguna como definitiva:**
  - **(a)** Corregir el motor con la partición por entidad, validada como equivalente en 773 de 773 ciclos
    (sección 4 bis). Basta para el tráfico normal, pero no para la inundación. Una campaña A repetida usaría entonces una versión de motor distinta; las
    características no cambian, pero el cambio debe declararse.
  - **(b)** Además de lo anterior, limitar `build_rows` a las ventanas pendientes, con la regla de la primera ancla
    no puntuada. Está validada como equivalente en 773 de 773 ciclos (sección 4 ter). Resuelve todo salvo la
    inundación HTTP, que necesitaría además aligerar `attribute_packets` o la historia de 230 s.
  - **(c)** Para una campaña futura, preregistrar una tolerancia de continuidad justificada por la cadencia
    estructural de 10/20 s, antes de ejecutarla. Aplicarla a la campaña del 29-oct solo valdría como análisis de
    sensibilidad no preregistrado.
- **Sin determinar:**
  - la parte de la duración real que el perfil no reproduce (hasta unos 11 s en el pico);
  - si el tráfico de los perfiles a factor 1,0 es representativo de la carga a la que el motor debe resistir.
