# 4.2 — Aporte de los componentes del detector híbrido: antecedente, recálculo y evidencias

**Fecha:** 26-oct-2026. **Alcance:** solo datos y evidencias. No redacta el artículo, no toca el Word y no cambia
el sistema desplegado, sus reglas, sus umbrales ni sus artefactos. Todo se calculó offline sobre copias.
La configuración se registró en `config-aporte.json` **antes** de recalcular.

> **Declaración.** Los umbrales del IF salen de la misma validación de 65 553 ventanas que se usó en 4.1, y las
> métricas por ventana se calculan sobre la misma población de la Tabla 7. Reutilizar estos datos **no** aporta una
> validación independiente de la elección de α. Una reproducción offline tampoco es una prueba nueva en vivo.

## 1. Antecedente: de dónde sale «IF 6/9 · heurísticos 7/9 · híbrido 9/9»

### Evidencias

| Qué | Dónde |
|---|---|
| Tabla de la ablación | `orquestacion-limpio\02-metodologia\comparacion-cyberflow-suricata\31-ABLACION-RESULTADO.md` (6-oct) |
| Veredicto por episodio | `…\comparacion-cyberflow-suricata\26-BATERIA-N3-RESULTADOS.md` (5-oct) |
| Registro bruto del orquestador | bastión `~/orq_results.csv`, `~/orq.log`, `~/orq.sh`; copia en `antecedente/` |
| Procesamiento por episodio | Sensor1 `~/piloto/proc.sh`, `score.py`, `dedup_merge.py`; copia en `antecedente/` |
| Capturas | Sensor1 `~/piloto/{e3,e4,e1}-r{1,2,3}/`: `live-*.pcap` del anillo, `eve.json` recortado, `features.csv`. También `~/piloto/BASE/`, la línea base de esa tarde. **Se conservan.** |
| Fuerza bruta | bastión `~/brute_tiempos.txt`: `1,NA,NA,NA`. No hay ningún episodio válido. |

Corrección: `00-inventario/INVENTARIO-Y-FACTIBILIDAD.md` (23-oct) decía que los PCAP y los datos por ventana no se
habían conservado. Sí se conservaron, en `~/piloto/`, y por eso el re-procesado offline es posible.

### Configuración con la que se obtuvo el resultado histórico

- **Modelo:** `if_recalibrado_2026_09`, el modelo contaminado anterior al limpio. Archivo
  `artifacts/preliminar/if_recalibrado_desplegable.joblib`, fechado el 30-sep. Umbral `score_samples < −0,568892`
  (α 0,05), tomado de `manifest-if-recalibrado.json`. **No es el IF actual ni es α = 0,03.**
- **Heurísticos:** versión `2026-09-30.1` (commit `a6d287a` de producto-main), con el umbral DNS de nombres únicos
  forzado a 0,45 dentro de `score.py`. `port_scan` exigía `unique_dst_port_ratio_30s ≥ 0,5` y no tenía la rama de
  ráfaga.
- **Procesamiento:** `extract_multilayer_v2.py` sobre el PCAP **sin deduplicar**, con `capture-start` = T0 − 25 s.
  Solo se puntuaban las ventanas de la Kali (10.10.20.30).
- **Combinación:** modelo **o** heurístico por episodio, a partir de `t ≥ T0` (`30-metricas.py::ablacion`).

### Episodios (5-oct-2026, reloj del sensor)

El origen es siempre la Kali 10.10.20.30.

| Ep. | Familia | Destino | T0 (orquestador) | 1.er / último paquete de ataque | Duración | Paquetes |
|---|---|---|---|---|---|---|
| e3-r1 | DNS inusual (`dig` a nombres aleatorios, 90 s) | 10.10.10.20:53/udp | 20:26:57 | 20:26:58,0 / 20:28:27,7 | 89,7 s | 209 |
| e3-r2 | DNS inusual | 10.10.10.20:53/udp | 20:29:41 | 20:29:42,3 / 20:31:11,9 | 89,6 s | 209 |
| e3-r3 | DNS inusual | 10.10.10.20:53/udp | 20:32:26 | 20:32:27,0 / 20:33:56,6 | 89,6 s | 209 |
| e4-r1 | Inundación HTTP (`curl` en bucle, 90 s) | 10.10.30.10:80/tcp | 20:35:10 | 20:35:11,4 / 20:36:41,4 | 90,0 s | 44 705 |
| e4-r2 | Inundación HTTP | 10.10.30.10:80/tcp | 20:38:16 | 20:38:16,7 / 20:39:46,8 | 90,1 s | 3 341 |
| e4-r3 | Inundación HTTP | 10.10.30.10:80/tcp | 20:41:01 | 20:41:02,3 / 20:42:32,3 | 90,0 s | 3 296 |
| e1-r1 | Escaneo de puertos (`nmap -sT -T4 -p 1-1000`) | 10.10.30.10 tcp/1-1000 | 20:43:47 | 20:43:48,0 / 20:44:05,8 | 17,7 s | 2 021 |
| e1-r2 | Escaneo de puertos | 10.10.30.10 tcp/1-1000 | 20:45:19 | 20:45:20,1 / 20:46:03,8 | 43,8 s | 2 043 |
| e1-r3 | Escaneo de puertos | 10.10.30.10 tcp/1-1000 | 20:47:17 | 20:47:18,4 / 20:47:36,0 | 17,6 s | 2 018 |

Sobre T0 y el fin del ataque:

- `orq.sh` no guardó los instantes. T0 se recupera del `features.csv` original: `proc.sh` recibe
  `CS = T0 − 25 s`, y `CS = window_end − history_coverage_s` es único en cada archivo.
- El fin del ataque es el último paquete de ataque del PCAP deduplicado.
- e4-r1 tuvo unas 13 veces más paquetes que e4-r2 y e4-r3 con el mismo comando. Se deja como dato; no se explica aquí.

### ¿Se puede reproducir? Sí, 9/9

`evaluar_componentes.py` (paso `original`) toma los `features.csv` guardados, el joblib antiguo, su umbral y los
heurísticos `2026-09-30.1` con DNS a 0,45. Con eso obtiene exactamente lo mismo que `orq_results.csv` en los
9 episodios: las ventanas de la Kali, el número de alertas del modelo, la primera alerta y el heurístico con su
primer disparo (`resultados/reproduccion-original.csv`). El resultado histórico es 6/9 para el modelo, 7/9 para los
heurísticos (falla `port_scan` en e1-r1 y e1-r3) y 9/9 para el combinado.

No hace falta ningún archivo más para reproducirlo.

## 2. Recálculo con el IF limpio sobre los mismos episodios

### Qué se usa

- **Modelo:** `if_limpio_2026_10_desplegable.joblib` (sha256 `df547da0…`), congelado y sin reentrenar.
- **Umbrales:** recalculados y comprobados con una diferencia ≤ 2,2e-16 respecto de 4.1
  (`resultados/umbrales-verificados.json`). Son el cuantil lineal 1 − α de `−score_samples` sobre 65 553 ventanas de
  validación.
  - α = 0,05: −0,5694578968
  - α = 0,03: −0,5898535710
  - Orientación: `score_samples`, donde mayor significa más normal. Hay señal si `score_samples < umbral`, con
    desigualdad estricta, como en `motor_decision.py`.
  - No hay empates en validación.
- **Heurísticos:** `heuristicos.py` vigente, `VERSION_UMBRALES 2026-10-06.2`, sin cambios. Se añade la regla heredada
  `auth_failure_heuristic` del motor.
- **Procesamiento común, el del motor vigente:**
  1. `parse_con_contexto`.
  2. Descarte de los protocolos 112 y 240.
  3. `deduplicar_espejo`.
  4. `attribute_packets(10.10.0.0/16)`.
  5. `load_app_observations(eve)`.
  6. `build_rows` con paso de 10 s.

  El código es la copia del sensor. Sus hashes coinciden con producto-main en el extractor y en los heurísticos; en
  `motor_decision.py` solo cambia un comentario de la cabecera.
- **Historia:** las variables solo usan el pasado disponible en el PCAP, que empieza en T0 − 20 s. No se usa
  información futura. Se fija `capture_start` = primera observación − 60 s para que las ventanas sean evaluables, como
  en el motor en marcha (allí la cobertura cuenta desde el arranque del proceso).
- **Guarda del motor:** si `packet_count_10s == 0`, el IF no se puntúa.

### Cómo se combinan las señales (verificado en el código)

1. `motor_decision.py` registra por cada ventana elegible:
   - `decision`: ALERT si el modelo da `score < threshold` con paquetes en los últimos 10 s, o si dispara la regla
     heredada de fuerza bruta. Si no, PERMIT.
   - Un campo **aditivo** `heuristico`, con el veredicto de `heuristicos.evaluar`.
2. `publicar_feed.py::_verdicto_de` toma como candidatos LIMIT, cuando hay ALERT del modelo, y la acción del
   heurístico. Se queda con el **más severo** (BLOCK > LIMIT).
3. Después el feed agrega por IP, aplica la escalera de `escalada.py`, excluye `NUNCA_BLOQUEAR` (bastión, sensor,
   puertas de enlace y 10.10.10.20) y lo aplica el agente del host.

Por tanto la **señal de detección** del híbrido es «IF o heurístico» en la misma ventana. **LIMIT o BLOCK es la
decisión**, no la detección, y la **aplicación** (nftables) no se reproduce offline.

### Criterio de atribución

Una señal es atribuible si cumple dos condiciones:

- La entidad de la ventana es la fuente del ataque, 10.10.20.30.
- `window_end` está en [T0, último paquete de ataque + 60 s]. Los 60 s son el horizonte de la variable más larga.

Un episodio está detectado si tiene al menos una señal atribuible. Las señales en otras entidades se listan aparte y
**no** cuentan.

## 3. Tabla 8 (recalculada offline)

| Familia | Episodios evaluados | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual | 3 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| Inundación HTTP | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Escaneo de puertos | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| **Total** | **9** | **6/9** | **6/9** | **9/9** | **9/9** | **9/9** |
| Fuerza bruta HTTP | 0 | no evaluado | no evaluado | no evaluado | no evaluado | no evaluado |

**Complementariedad por episodio (igual con α 0,05 y 0,03):**

- Ambos componentes: 6 (e4-r1/r2/r3 y e1-r1/r2/r3).
- Solo IF: 0.
- Solo heurísticos: 3 (e3-r1/r2/r3).
- Sin detectar: 0.

**Primera señal atribuible.** Latencia desde T0 en s; detalle completo en `resultados/episodios-registro.csv`.

| Ep. | IF 0,05 | IF 0,03 | Heurístico | Híbrido 0,05 / 0,03 (componente, acción) |
|---|---|---|---|---|
| e3-r1 | — | — | 13 `dns_entropy` | 13 (heurístico, LIMIT) |
| e3-r2 | — | — | 9 `dns_entropy` | 9 (heurístico, LIMIT) |
| e3-r3 | — | — | 14 `dns_entropy` | 14 (heurístico, LIMIT) |
| e4-r1 | 10 | 10 | 10 `http_abuse` | 10 (IF + heurístico, LIMIT) |
| e4-r2 | 14 | 14 | 14 `http_abuse` | 14 (IF + heurístico, LIMIT) |
| e4-r3 | 9 | 9 | 19 `http_abuse` | 9 (IF, LIMIT) |
| e1-r1 | 23 | 23 | 23 `port_scan` | 23 (IF + heurístico, BLOCK) |
| e1-r2 | 21 | 21 | 21 `port_scan` | 21 (IF + heurístico, BLOCK) |
| e1-r3 | 23 | 23 | 23 `port_scan` | 23 (IF + heurístico, BLOCK) |

Lectura. En esta batería, el híbrido no detecta ningún episodio que no detecten ya los heurísticos solos. El IF
aporta dos cosas:

- **Antelación** en e4-r3: 9 s frente a 19 s.
- **Redundancia** en el flujo HTTP y en el escaneo.

El IF no detecta el DNS de esta intensidad (unas 2,3 consultas/s): la puntuación mínima de la Kali en el intervalo
es −0,546 a −0,558, por encima de ambos umbrales.

### Lo que hay que declarar sobre los heurísticos

Los cambios de umbral que permiten el 9/9 heurístico se hicieron **después y a la vista de esta misma batería**:

- `2026-10-06.1` bajó la unicidad de 0,5/0,9 a 0,45. El commit `a7fc7ea` dice «Validado: port_scan 3/3».
- `2026-10-06.2` añadió la rama de ráfaga de `port_scan` para corregir el «1/3» de la nota 26.

En e1-r1 y e1-r3 el ratio de puertos únicos vale 0,499 tras deduplicar: con el 0,5 antiguo no disparaba y con 0,45
sí. Por tanto, **el resultado heurístico en el escaneo no es independiente** de estos episodios.

El IF limpio, en cambio, se entrenó, validó y probó con datos del 27 al 29 de septiembre. Ninguna ventana del 5-oct
está en `particionado-limpio.csv`, `oro.csv` ni `ataques-nota-M.csv` (comprobado en el sensor).

### Sensibilidades (no cambian la Tabla 8; se informan)

1. **Historia truncada y regla de elegibilidad del motor.** Con `capture_start` = primera observación, las ventanas con
   menos de 60 s de cobertura no se evalúan. Resultado: IF 3/9 (solo HTTP), heurísticos 7/9 e híbrido 7/9; se pierden
   e1-r1 y e1-r3, cuya única ventana con señal (T0 + 23 s) tenía menos de 60 s de cobertura. Es un efecto de la captura recortada (el PCAP
   empieza en T0 − 20 s), no del sistema en marcha.
2. **Ventanas del acumulador en vivo del 5-oct** (`multilayer-v3.csv`, escrito en vivo con historia completa y el
   código de esa fecha):
   - Igual que el replay en HTTP, escaneo y heurísticos.
   - El **IF 0,05 detecta e3-r2 (a 59 s) y e3-r3 (a 34 s)**, con puntuaciones de −0,5755 y −0,5749 frente al umbral
     de −0,5695. Con 0,03 sigue en 0/3.
   - Las variables difieren poco del replay: `flow_attempt_count_30s` hasta ±2 en DNS y hasta 92 en HTTP;
     `packet_count_10s` es idéntico.
   - Conclusión: **el 0/3 del IF en DNS con α 0,05 es frágil**, porque depende del procesamiento y está a unas
     milésimas del umbral. Con α 0,03 es estable (`resultados/contraste-acumulador-vivo.json`).
3. **Umbral desplegado** (−0,5693969936, α 0,05 sobre 65 633): no cambia ningún episodio.

### Señales no atribuibles durante los episodios

En total hay 52 ventanas (`resultados/episodios-senales-no-atribuibles.csv`):

- **10.10.10.20 (DNS/AD)** durante los tres episodios DNS:
  - `dns_entropy` en 29 ventanas.
  - IF 0,05 en 28 ventanas e IF 0,03 en 26.
  - Es el reenvío de los nombres aleatorios hacia arriba. 10.10.10.20 está en `NUNCA_BLOQUEAR`: el feed no actuaría
    sobre él, pero la señal existe.
- **10.10.10.30 (bastión):** el SSH del propio orquestador. El motor lo excluye (`--excluir`) y no lo evaluaría.

## 4. Métricas por ventana sobre la población de la Tabla 7

**Población:** 65 421 ventanas normales de `oro.csv` y 84 de ataque de `ataques-nota-M.csv`, 65 505 en total.

**Auditoría:**

- 65 505 claves únicas, sin duplicados y sin solape entre normales y ataques.
- Claves y etiquetas iguales a las de la Tabla 7.
- Puntuaciones iguales a las de 4.1, con diferencia ≤ 1,1e-16.
- Hay predicción para todas las ventanas.
- No se quitó ninguna ventana: ni las 45 558 normales sin paquetes en 10 s ni las 74 de 10.10.20.30.

Son ventanas de otra campaña (30-sep). **No se mezclan con los episodios.**

| Configuración | TP | FP | TN | FN | Precisión | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF 0,05 | 54 | 2 955 | 62 466 | 30 | 0,0179 | 0,6429 | 0,0349 | 4,52 % |
| IF 0,03 | 54 | 1 723 | 63 698 | 30 | 0,0304 | 0,6429 | 0,0580 | 2,63 % |
| Heurísticos | 47 | 472 | 64 949 | 37 | 0,0906 | 0,5595 | 0,1559 | 0,72 % |
| Híbrido 0,05 | 54 | 3 417 | 62 004 | 30 | 0,0156 | 0,6429 | 0,0304 | 5,22 % |
| Híbrido 0,03 | 54 | 2 192 | 63 229 | 30 | 0,0240 | 0,6429 | 0,0464 | 3,35 % |

Las filas del IF coinciden con la Tabla 7.

**Complementariedad en los 84 ataques:**

- Los heurísticos (`port_scan` 20, `http_abuse` 27) solo aciertan ventanas que el IF ya marca. Ambos: 47; solo IF: 7;
  solo heurísticos: 0; ninguno: 30.
- El híbrido no sube el recall. Añade 462 falsas alarmas con α 0,05 y 469 con α 0,03.

**Falsas alarmas de los heurísticos:**

- 470 de las 472 son `dns_entropy` sobre 10.10.10.20. Ese servidor está en `NUNCA_BLOQUEAR`: hay señal, pero el feed
  no actúa sobre él.
- Las falsas alarmas del IF se reparten entre los clientes de la VLAN 20 y 10.10.40.10.
- Ninguna configuración da falsas alarmas en las 74 ventanas inciertas de 10.10.20.30.

**Población operativa (aparte, `VENTANAS-metricas.md`):**

- Con las reglas del motor no queda ninguna ventana no elegible. Las ventanas sin paquetes no se puntúan con el IF.
- FPR: IF 0,05 4,33 %, IF 0,03 2,58 %, híbrido 0,05 5,04 %, híbrido 0,03 3,30 %. Los TP no cambian.

**ROC-AUC y AP:** solo el IF las tiene (Tabla 7: 0,9247 y 0,1858). No se atribuyen al híbrido ni se inventa una
puntuación combinada.

## 5. Control normal con el mismo procesamiento de los episodios

Se usa la línea base del 5-oct (`~/piloto/BASE`), de 19:45:30 a 19:50:24 UTC, es decir 294,8 s de PCAP:

- 61 ventanas elegibles, de 4 entidades no excluidas.
- Criterio de ventana: `window_end` en [primer paquete + 60 s, último paquete].
- Falsa alarma: cualquier señal del componente.
- Resultado: **0 en las cinco configuraciones**.

Es un control pequeño y **no es comparable** con la Tabla 7. Solo muestra que el procesamiento del replay no genera
señales espurias en tráfico normal de esa tarde.

## 6. Qué falta

- **Fuerza bruta HTTP:** no hay episodios. El intento de esa batería quedó en `NA` y no hay endpoint con 401
  instrumentado. Para presentarla por separado hay que ejecutarla.
- **N = 3 por familia:** sin intervalos útiles.
- **Validación en vivo con el IF limpio:** esto es una reproducción offline. La campaña en vivo del 23-oct
  (`_campana/resultados-2026-10-23/`) es otra fuente, con otros episodios, y no se mezcla aquí.
- **Heurísticos:** para medirlos de forma independiente hacen falta episodios nuevos, porque sus umbrales actuales se
  fijaron con estos.
</content>
</invoke>
