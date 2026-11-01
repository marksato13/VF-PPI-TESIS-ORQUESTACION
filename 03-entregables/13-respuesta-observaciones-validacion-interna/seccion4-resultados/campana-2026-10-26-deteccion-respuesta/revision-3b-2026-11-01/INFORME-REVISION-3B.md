# Informe de la revisión del paso 3B

**Revisión posterior a conocer los resultados.** No es el protocolo original ni una evaluación independiente. Los
criterios se escribieron y publicaron antes del reanálisis (`CRITERIOS-REVISION.md`, commit `191b043`).

El resultado original no se toca y sigue en `../ejecucion-3b-2026-11-01/`, con sus fuentes, informe, tablas y
manifiesto. Aquí se presenta **junto** a él.

No se han lanzado ataques ni repetido la campaña, y no se ha modificado el motor, los servicios, el modelo, el
escalador, las características, los umbrales, los heurísticos, los escenarios ni la configuración de captura. El
Word no se ha editado.

## 0. Conclusión en lenguaje sencillo

1. **Qué estaba mal.**
   - La herramienta de evaluación medía la «continuidad» con los instantes en que el motor escribe en su registro y
     exigía que no pasaran más de 20 s entre escrituras. El motor incremental no escribe cuando no tiene ventanas
     listas, así que había pausas de 20–23 s sin que se perdiera nada. Eso dejaba fuera 24 de 25 episodios.
   - La herramienta de recálculo de características elegía mal los ficheros PCAP: excluía los que terminan en tramas
     que el motor no decodifica. Por eso 9 reconstrucciones no coincidían.
   - Ninguno de los dos fallos era del motor.
2. **Qué está respaldado.**
   - El motor decidió en vivo **todas** las ventanas que la repetición offline considera necesarias (12 667 de 12 667),
     y con las mismas puntuaciones y decisiones.
   - Con la continuidad medida sobre las fuentes (PCAP y EVE) y frente al inventario, la población principal pasa de
     1 a **15 de 25** episodios.
   - En esos 15 hay emisiones reales oportunas en 12. Los 3 restantes son escaneos breves de unos 18 s, que el sistema
     detecta, pero después de que terminen.
   - En el control, las falsas alarmas no cambian: IF 14,94 / 9,61 / 3,14 %, HEUR 3,48 % y HIB 17,62 / 12,71 / 6,47 %.
   - El recálculo corregido reproduce exactamente **702 de 702** decisiones de la Kali (antes 693).
3. **Qué problemas persisten.**
   - Suricata perdió paquetes (`kernel_drops`) en 9 episodios, y esos episodios siguen fuera. La causa no está
     demostrada: no la explican el volumen, las ráfagas ni la CPU por sí solos.
   - Un episodio (`escaneo_sostenido-r1`) queda fuera porque su intervalo posterior acaba 5,8 s después del final del
     inventario.
   - Los escaneos breves no pueden ser oportunos con las características y umbrales actuales: en 3 de 4, la primera
     ventana con señal cierra después de que termine el ataque.
   - El heurístico DNS da 88 falsas alarmas en el control, todas sobre el propio servidor DNS (10.10.10.20).
4. **¿Hay que modificar el producto?** No para que lo medido sea válido. Para bajar la latencia hay dos cambios
   opcionales: rotación PCAP de 5 s y un ciclo disparado por la rotación. Restarían unos 7–8 s, pero no arreglan los
   escaneos breves. Se describen con riesgos, pruebas y reversión en `PROPUESTA-Y-PLAN-VALIDACION.md`. No se ha
   desplegado nada.
5. **¿Basta una validación acotada o hace falta una campaña nueva?**
   - Para corregir el análisis del 3B basta lo hecho aquí: pruebas, ejecución en un directorio nuevo y comparación
     con el original.
   - Para **confirmar** las tasas hace falta la campaña B, con los criterios v2 congelados y precedida de una prueba
     con tráfico normal nuevo (plan, §3).
   - El paso de 1 a 15 episodios no es motivo para cerrar: es la consecuencia de corregir una medida, no un objetivo.

## 1. Entradas, versiones y hashes

- **Manifiesto 3B:** 0 fallos (425 ficheros). Manifiesto 3A: 73 ficheros OK.
- **Herramientas originales:** coinciden con `REFERENCIAS-Y-HASHES.md`. Son `analizar_3b` `27e67fd1…`, `analizar`
  `71674908…`, `generar_respaldos` `159d7736…`, `verificar_integridad` `1de46d03…`, `calidad_fuentes` `d63ca6e9…`,
  `recalcular_caracteristicas` `573fe0f1…`, `poblacion` `7b140ae4…`, `extraer_evidencia_destino` `48d13aba…` y
  `config-campana-3b.json` `cbf72fbb…`. Se comprobó también en el sensor (`resultados/sensor/sha256-herramientas.txt`).
- **Entradas en el sensor** (`resultados/sensor/sha256-entradas.txt`):
  - `motor_decision.log` `bf51f308…`;
  - replay `4b93caa4…`;
  - `eve-segmento.json` `b7bf61a2…`;
  - `ciclos.jsonl` `5eefbdf4…`;
  - `marcas.jsonl` `276314a8…`;
  - `caracteristicas.jsonl` (v1) `a79d1c8b…`.

  Las copias locales descomprimidas tienen los mismos hashes.
- **Herramientas nuevas:** véanse sus hashes en `REFERENCIAS.md`. Las v2 que se ejecutaron en el sensor coinciden
  byte a byte con las publicadas.
- **Reproducción del original:** `analizar_3b.py` (sin modificar), ejecutado en local con las entradas originales,
  produce un `analisis-3b.json` idéntico al publicado salvo la ruta del inventario.

## 2. La contradicción de los 20 s, corregida en toda la cadena

**Dónde estaba.**

- `generar_respaldos.py` calculaba `continuidad(tlog, ini, fin+60, TOL=20)` sobre `logged_at` de **todas** las
  decisiones.
- `analizar.cobertura()` (llamada para `durante_completa`) exige ese mismo hueco ≤ 20 s.
- `verificar_integridad.py` leía `previa_s`, `posterior_s`, `durante_completa` y `continuidad_sin_huecos` derivados
  de ahí.
- `analizar_3b.py` ya trataba bien la continuidad (contra el inventario, con el hueco de escritura como
  informativo), pero recibía `integridad = no apta`.

**Por qué es un artefacto.**

- Los ciclos del motor son de 10,00 s (mediana del latido 10,000 s, máximo 11,11 s).
- La ventana solo se decide cuando `marca_pcap ≥ window_end`, y la rotación PCAP es de 15 s. Un ciclo sin ventanas
  listas no escribe nada, y el siguiente escribe dos ventanas juntas.
- El inventario no tiene ninguna ausente.

**Qué hace la v2** (`herramientas/generar_respaldos_v2.py` y `verificar_integridad_v2.py`):

- **Sin subir la tolerancia**, mide por intervalo (previa [ini−120, ini], durante [ini, fin+60], posterior
  [fin, fin+90]) y por componentes independientes:
  - PCAP continuo (hueco entre inicios ≤ 16 s);
  - pulso `stats` del EVE sin hueco ≥ 16 s (`stats.interval: 8`, leído en `/etc/suricata/suricata.yaml`);
  - todas las ventanas requeridas por el inventario (todas las entidades) decididas en vivo, sin ausentes ni no
    evaluadas, con `marca_pcap` y `marca_eve` ≥ `window_end`. Fuera del inventario se marca como no verificado;
  - en durante, además, las anclas de la Kali.
- El hueco de escritura pasa a `informativo`.
- Hashes, faltantes, captura (incluidos los `kernel_drops` de Suricata), reinicios y relojes se comprueban igual que
  en la v1, que se importa sin modificar.
- Un respaldo sin desglose por componente no verifica.

**Pruebas** (`pruebas/test_revision_3b.py`: 36 comprobaciones, 9 funciones de pytest):

1. Dos ventanas escritas juntas cada 20,2 s y presentes → verificado. Con la v1, el mismo registro superaba la
   tolerancia.
2. Una ausente (de otra entidad, en la previa, o un ancla de la Kali) → no verificado.
3. Una no evaluada → el denominador no cambia y el intervalo no verifica. `analizar_3b` la mantiene requerida.
4. Falta de PCAP en la previa, corte del EVE antes de fin+90, hueco de 24 s del EVE, ventanas posteriores no
   decididas o `marca_pcap < window_end` → no verificado.
5. Inventario truncado → posterior y durante no verificadas, y `analizar_3b` no da observación completa.
6. EVE degradado con el procesamiento idéntico al replay → no verificado. Calidad degradada → observación
   incompleta. `kernel_drops` > 0 → no apto aunque la continuidad verifique.

Extras: formato v1 sin desglose → no verificado; extremo a extremo con ficheros; selección PCAP del recálculo.

**Resultado** (`resultados/sensor/integridad-v2.json`): **15 aptos**, frente a 1 en el original. Los 10 no aptos son:

- 9 por `captura_sin_errores_relevantes` (`kernel_drops` de Suricata en [ini−120, fin+90], criterio sin cambios);
- `escaneo_sostenido-r1` por `cobertura_posterior` y `continuidad`: su fin+90 = 10:03:35,8 sale del inventario
  (hasta 10:03:30). Es «no verificado», no «perdido».

`analizar.py` (primera campaña A) tiene el mismo defecto en `cobertura()`. No se modifica, y se deja documentado.

## 3. Calidad de fuentes y Suricata

**Los dos criterios, con sus intervalos exactos** (tabla completa en `resultados/comparacion/TABLAS-REVISION.md` §4):

- **Calidad** (`calidad_fuentes.py`, ±60 s): delta entre la última muestra ≤ ini−60 y la primera ≥ fin+60. Hay 8
  degradados.
- **Integridad** (`generar_respaldos.py`, [ini−120, fin+90]): delta entre la primera y la última muestra dentro del
  periodo. Hay 9 con descartes. La diferencia es `inundacion_http-r1`: +11 descartes a las 08:12:02, 73 s antes del
  inicio y fuera de ±60 s.
- El resultado principal revisado mantiene **los dos**, como en el original.
- **Análisis adicional (no elegido):** con un solo intervalo ±60 s para ambos, 16/25 (entra `inundacion_http-r1`).
  Con [−120, +90] para ambos, 15/25.

**Investigación de los descartes** (`diagnosticos/suricata-descartes.json`, `resultados/sensor/rafagas-por-intervalo.json`).

*Volumen:* 3232 descartes de 9 436 692 paquetes (0,034 %), en 21 de 1431 intervalos de 8 s.

*Demostrado:*

- Aparecen también con el sensor casi en reposo: a las 07:28:57 y 09:15:46 la CPU total es 0,09, y a las 07:28:57
  load1 = 0,08 (antes del control).
- No los explica el volumen: hay intervalos sin descartes con hasta 45 918 paquetes; el máximo con descartes es
  42 909.
- No los explican las ráfagas: en 1153 de 1410 intervalos sin descartes, la ráfaga máxima de 10 ms es mayor o igual
  que la menor de los intervalos con descartes.
- Los intervalos con descartes tienen, en mediana, más paquetes (10 098 frente a 4471), más CPU (0,37 frente a 0,22)
  y menos memoria disponible (5,1 frente a 6,0 GB), pero los rangos se solapan.
- El mayor episodio, de 08:34:02 a 08:34:42 (1146 descartes con ±60 s, 1483 con [−120, +90]), coincide con el motor
  usando el 95 % de una CPU y el ciclo de 10,06 s. Sin embargo, el otro ciclo de más de 10 s (09:53, de 10,61 s, en
  `inundacion_http-r5`) no tuvo descartes.

*Hipótesis (no demostradas):*

- un anillo AF_PACKET por defecto (`ring-size`, `tpacket-v3`/`use-mmap` comentados en `suricata.yaml`) que no
  absorbe ráfagas cortas combinadas con la planificación de CPU;
- competencia con el motor en los ciclos pesados;
- tras la campaña (10:25–10:31), competencia con la repetición offline.

*Recursos:* 4 CPU y 7,9 GB; memoria disponible mínima de 3,84 GB en la batería.

**tcpdump:** 0 descartes. El alcance es el contador acumulado del proceso tcpdump (PID 1375) hasta las 10:51:44
(SIGUSR1); no mide pérdidas aguas arriba del SPAN.

No se ha cambiado ninguna configuración.

## 4. Las 9 reconstrucciones no exactas

**Causa, demostrada en `dns_inusual-r3` 08:18:50.**

- El motor fija `marca_pcap = max(pk.packet.timestamp for pk in nuevos)` sobre los paquetes decodificados (todos los
  protocolos) y lee todos los PCAP cerrados (`files[:-1]`).
- `recalcular_caracteristicas.py` (v1) seleccionaba los ficheros con «última **trama** ≤ `marca_pcap`».
- `live-20261101081847.pcap` termina con 2 tramas no decodificables hasta 1141,948, después del último paquete
  decodificado (1141,691678 = `marca_pcap`). La v1 lo excluía aunque el motor lo había leído.

**Corrección** (`herramientas/recalcular_caracteristicas_v2.py`, función `seleccionar`, con su prueba): seleccionar
y podar por el último paquete **decodificado**. Es un fallo de la herramienta, no del motor.

**Resultado de la v2:** **702/702 exactas** (v1: 693/702). Las 9 pasan a exactas en pk10 y en score, y no aparece ninguna diferencia nueva. `caracteristicas-v2.jsonl` sha256 `a58e0ee7…`, rc 0, ejecutado en `~/cf-3b-revision-20261101`.

**Tabla** (`diagnosticos/recalculo-v1-v2.json`):

| Episodio | Ventana | pk10 reg. / v1 / v2 | Score reg. / v1 / v2 | Tipo v1 → v2 | Características v1≠v2 | Señales de la ventana (registro) | Efecto hipotético con v1 |
|---|---|---|---|---|---|---|---|
| dns_inusual-r3 | 08:18:50 | 46 / 32 / 46 | -0,5444 / -0,5428 / -0,5444 | puntuacion_distinta → exacta | 6 (packet_rate_10s, byte_rate_10s, unique_dst_ip_ratio_30s…) | HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| dns_inusual-r3 | 08:19:00 | 48 / 0 / 48 | -0,5460 / null / -0,5460 | sin_puntuacion → exacta | 9 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| dns_inusual-r3 | 08:19:10 | 46 / 8 / 46 | -0,5444 / -0,5031 / -0,5444 | puntuacion_distinta → exacta | 6 (packet_rate_10s, byte_rate_10s, unique_dst_ip_ratio_30s…) | HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| inundacion_http-r4 | 08:24:40 | 18832 / 3318 / 18832 | -0,6691 / -0,6658 / -0,6691 | puntuacion_distinta → exacta | 11 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| escaneo_sostenido-r5 | 08:43:00 | 13 / 0 / 13 | -0,5589 / null / -0,5589 | sin_puntuacion → exacta | 14 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | — | ninguno |
| escaneo_sostenido-r5 | 08:43:10 | 3670 / 2 / 3670 | -0,6341 / -0,4595 / -0,6341 | puntuacion_distinta → exacta | 12 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | pierde IF a 0,05/0,03/0,01; era la primera señal IF del episodio |
| fuerza_bruta_http-r5 | 08:57:40 | 7525 / 2275 / 7525 | -0,7263 / -0,7182 / -0,7263 | puntuacion_distinta → exacta | 12 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| dns_inusual-r1 | 09:26:20 | 46 / 40 / 46 | -0,6730 / -0,6727 / -0,6730 | puntuacion_distinta → exacta | 6 (packet_rate_10s, byte_rate_10s, unique_dst_ip_ratio_30s…) | IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | ninguno |
| dns_inusual-r1 | 09:26:30 | 48 / 0 / 48 | -0,6726 / null / -0,6726 | sin_puntuacion → exacta | 8 (packet_rate_10s, byte_rate_10s, mean_ip_len_10s…) | IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03, HIB_0.01 | pierde IF a 0,05/0,03/0,01 |

- **Puntuación distinta frente a sin puntuación.** Las 3 filas sin puntuación de la v1 tenían 0 paquetes, y un null
  no es 0.
- **Efecto real sobre el análisis:** ninguno. Las señales, categorías y latencias se calculan con el registro en
  vivo.
- **Efecto hipotético si se hubiera usado la v1:** `escaneo_sostenido-r5` 08:43:10 y `dns_inusual-r1` 09:26:30
  perderían la señal IF a los tres α. En r5 era la primera señal IF del episodio, así que su primera señal pasaría a una ventana posterior. No ocurre, porque el análisis no usa el recálculo.

**Replay frente a vivo** (`diagnosticos/replay-vs-vivo.json`):

- Hay 12 667 claves comunes, 0 solo en vivo, 0 solo en el replay y 0 duplicados. Puntuación, decisión y
  `packet_count_10s` son idénticos en todas.
- Las 18 diferencias del heurístico son solo de `motivo` (por ejemplo, «54 consultas DNS/60s» en vivo frente a «70»
  en el replay). El tipo y la acción coinciden.
- **Todas** son ventanas de la Kali con 0 paquetes y puntuación null en ambos. Su fila solo tiene datos L7 del EVE,
  que dependen de la fase del ciclo: en vivo, x3,5/x4,5 s; en el replay, rejilla x0,0 s y una línea se da por
  escrita cuando el reloj alcanza su marca de tiempo.
- El replay coincide porque ejecuta el `main()` real del motor, con su lectura de PCAP. El recálculo v1 usaba otra
  regla.

## 5. Reanálisis (tres α, siete configuraciones)

**Comparación** (`resultados/comparacion/TABLAS-REVISION.md`, episodio a episodio con motivos):

- Población principal: original 1/25 (`escaneo_breve-r3`) → revisada 15/25. Los 10 excluidos siguen visibles con
  su motivo.
- Las señales, primeras señales, latencias y emisiones son **idénticas** en todos los episodios: la corrección solo
  cambia la admisión.
- El único cambio de categoría es el paso de `no_evaluable` a `ausencia_con_observacion_suficiente`, en los episodios
  admitidos sin señal atribuible:
  - IF de `dns_inusual-r2` y `-r4` a los tres α;
  - IF_0.01 de `escaneo_breve-r5`.

**Tabla 8 revisada** (15 episodios; OP oportuna, SP solo posterior, AU ausencia):

| Familia | n | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 | Emisión real oportuna |
|---|---|---|---|---|---|---|---|---|---|
| DNS inusual | 3 | OP1 AU2 | OP1 AU2 | OP1 AU2 | OP3 | OP3 | OP3 | OP3 | 3/3 |
| Escaneo breve | 4 | OP1 SP3 | OP1 SP3 | SP2 AU2 | OP1 SP3 | OP1 SP3 | OP1 SP3 | OP1 SP3 | 1/4 |
| Escaneo sostenido | 4 | OP4 | OP4 | OP4 | OP4 | OP4 | OP4 | OP4 | 4/4 |
| Fuerza bruta HTTP | 3 | OP3 | OP3 | OP3 | OP3 | OP3 | OP3 | OP3 | 3/3 |
| Inundación HTTP | 1 | OP1 | OP1 | OP1 | OP1 | OP1 | OP1 | OP1 | 1/1 |

- **Totales en la población común** (los mismos 15 episodios para las 7 configuraciones):
  - IF 0,05 y 0,03: OP 10, SP 3, AU 2;
  - IF 0,01: OP 9, SP 2, AU 4;
  - HEUR y HIB (los tres α): OP 12, SP 3.
- `oportuna` y `solo_posterior` van separadas, y ningún `solo_posterior` cuenta como oportuna.
- **Emisiones reales** (separadas de las configuraciones derivadas): oportunas en 12 de 15, con latencias de la
  primera entre 16,4 y 35,6 s. Fuera de la población hay 9 de 10 oportunas; la que falta es `escaneo_breve-r4`.

**HEUR y HIB tienen la misma categoría en los 15 episodios.** Como HIB = IF ∪ HEUR, su primera señal es la anterior
de las dos. En esta población la primera señal del heurístico nunca llega después que la del IF: llega en la misma
ventana o antes, como en `escaneo_breve-r3`, 30,7 s frente a 40,9 s.

**Qué añade HIB frente al IF:**

- *Detecciones:* `dns_inusual-r2` y `-r4` (dns_entropy) a los tres α, y además `escaneo_breve-r1` a α 0,01.
- *Falsas alarmas en el control:* 71 / 82 / 88 ventanas (HEUR sin IF a α 0,05 / 0,03 / 0,01). De las 92 de HEUR,
  88 son `dns_entropy` sobre 10.10.10.20 (el resolvedor DNS) y 4 son `http_abuse` sobre 10.10.20.26.

**Control normal** (idéntico al original): 07:32–08:05, 2644 ventanas requeridas, 2644 decididas, cobertura 1,0.

| | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 |
|---|---|---|---|---|---|---|---|
| Falsas alarmas / 2644 | 395 | 254 | 83 | 92 | 466 | 336 | 171 |
| Tasa | 14,94 % | 9,61 % | 3,14 % | 3,48 % | 17,62 % | 12,71 % | 6,47 % |

**No se elige α.** Nada de esto es una confirmación independiente: es el mismo conjunto de datos, reanalizado con
criterios escritos después de ver los resultados.

## 6. Demora

Véase `PROPUESTA-Y-PLAN-VALIDACION.md` §1 y `diagnosticos/demora.json`.

- **Descomposición de la mediana de 24,9 s** (todas las sumas comprobadas):
  - A, acumulación: 7,9 s;
  - B, espera PCAP: 12,0 s;
  - C, espera de ciclo: 1,5 s;
  - D, proceso: 2,6 s.
- **Los 4 escaneos breves no oportunos:** en r2, r4 y r5 la primera ventana con señal cierra después del fin del
  ataque, así que ningún cambio de la cadena los haría oportunos. En r3 haría falta B + C ≤ 1,3 s.
- **Ciclos de más de 10 s:** son 2 (10,06 y 10,61 s), con unos 445 000 paquetes en el anillo. Alargan D (≈ 7 s en las
  inundaciones) y el latido (11,1 s), pero no cambian ninguna categoría.
- **Tardías:** las 49 de los episodios (y las 655 del inventario) son ventanas con 0 paquetes de la Kali. Se deciden
  cuando la entidad reaparece.

## 7. Contenido de la carpeta

- `CRITERIOS-REVISION.md` (antes del reanálisis), este informe, `PROPUESTA-Y-PLAN-VALIDACION.md`, `COMANDOS.md`,
  `REFERENCIAS.md` y `MANIFIESTO.sha256`.
- `herramientas/`:
  - `generar_respaldos_v2.py`, `verificar_integridad_v2.py` y `recalcular_caracteristicas_v2.py`;
  - `comparar_original_revisado.py`, `diagnostico_demora.py`, `diagnostico_recalculo.py`,
    `diagnostico_suricata.py` y `diagnostico_heuristico_replay.py`.
- `pruebas/test_revision_3b.py`.
- `guiones/`: s69, s70 y s71 del sensor.
- `resultados/`:
  - `sensor/`: respaldos v2, integridad v2, recálculo v2, ráfagas y hashes;
  - `analisis-revisado/`;
  - `comparacion/`.
- `diagnosticos/`.
