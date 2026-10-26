# 4.2 r2 — Aporte de los componentes: historia real, criterio temporal y Tabla 8 revisada

**Fecha:** 26-oct-2026. **Alcance:** datos y evidencias, sin redacción del artículo ni cambios en el Word.
No se toca el sistema desplegado, el modelo, el escalador, los umbrales ni los heurísticos. Todo se calcula offline
sobre copias.

**Revisa a:** `../aporte-componentes-2026-10-26/` (commits `0305589` y `efc01a7`), que se conserva intacta.

**Configuración:** `config-r2.json`, registrada y versionada (commit `d60495f`) **antes** de calcular cualquier
resultado.

**Script:** `evaluar_r2.py`, que reutiliza sin modificarlo el núcleo de la versión anterior.

> **Resultado principal en una línea.** Con la historia que realmente existe, **ninguno de los 9 episodios del 5-oct
> es evaluable** para «detección durante la ejecución». La Tabla 8 principal queda vacía (0 de 9 evaluables) y
> **no hay resultado vigente que sustituya a 6/9 · 7/9 · 9/9**. Las filas del acumulador en vivo sí tienen contexto,
> pero no son equivalentes al procesamiento vigente. Por eso solo se presentan como sensibilidad.

---

## 1. Historia real disponible (punto 1)

### Qué fuentes hay y cuáles se descartan

| Fuente | Estado | Uso |
|---|---|---|
| PCAP del anillo por episodio (`~/piloto/eX-rY/live-*.pcap`) | Conservado. Empieza entre 6,7 y 20,6 s antes del inicio del generador. | **Principal**, con su inicio real |
| `eve.json` recortado por `proc.sh` | Conservado. Recorte desde Tsf − 25 s. | Principal |
| Captura contigua entre episodios | **No existe.** Entre el fin de un PCAP y el inicio del siguiente hay huecos de **31,8 a 65,1 s** sin datos. | **No se concatena**: fabricaría continuidad |
| EVE completo de Suricata | **Perdido.** Las copias de `/var/log/suricata` empiezan el 7-oct. | — |
| `motor_decision.log` del 5-oct | **Perdido.** Rotado; el `.gz` más antiguo es del 12-oct. Una búsqueda de `2026-10-05T20:3` en todo el sensor solo encuentra el acumulador y `syslog`/`auth.log`. | — |
| Filas del acumulador en vivo (`multilayer-v3.csv`, 5-oct) | Conservadas. Contexto ≥ 60 s por construcción. | **Sensibilidad** (§1.3) |
| `publicar.log` + cron en `syslog` + `auth.log` del sensor | Conservados. | Marcas del generador y cadena de respuesta (§3, §6) |

Evidencia: `evidencia/sensor-05oct/` (extractos con sha256 de los ficheros fuente) y
`evidencia/scripts-inventario/` (los scripts que los obtuvieron).

### 1.1 Contexto por episodio (`resultados/contexto-episodios.csv`)

Se usa `capture_start = max(primera trama del PCAP, inicio del recorte EVE)`. **No se adelanta ninguna fecha.**

Una ventana es evaluable si cumple dos condiciones:

- `window_end − 60 s ≥ capture_start`: las 28 variables tienen todo su horizonte.
- `window_end ≤ última trama`: no falta el final.

Además, `in_window` usa `(window_end − w, window_end]`, así que no entra información futura.

| Ep. | Historia antes del inicio | Ventanas durante el ataque | … evaluables (replay) | … evaluables (acumulador) | Datos tras el fin |
|---|---|---|---|---|---|
| e3-r1 | 6,7 s | 9 | 3 | 9 | 21,3 s |
| e3-r2 | 20,6 s | 9 | 5 | 9 | 20,9 s |
| e3-r3 | 18,7 s | 9 | 5 | 9 | 20,7 s |
| e4-r1 | 18,4 s | 9 | 5 | 9 | 21,1 s |
| e4-r2 | 8,6 s | 9 | 4 | 9 | 20,5 s |
| e4-r3 | 9,4 s | 9 | 4 | 9 | 20,7 s |
| e1-r1 | 8,9 s | 2 | 0 | 2 | 20,5 s |
| e1-r2 | 11,1 s | 5 | 0 | 5 | 21,2 s |
| e1-r3 | 9,5 s | 2 | 0 | 2 | 21,3 s |

**Lo que falta en todos los episodios:**

- Las ventanas de los primeros 40–54 s del ataque. En los escaneos falta el ataque completo.
- Las ventanas posteriores a fin + 21 s, porque el PCAP termina ahí.

**Consecuencia:** con el replay ningún episodio cumple la condición de evaluable, y ninguno puede clasificarse como
«sin detección».

### 1.2 Qué no puede reconstruirse de forma equivalente a la operación

1. **Las primeras ventanas de cada ataque.** La operación las puntuó con la historia previa del motor (110 s de
   buffer). El PCAP no la tiene. Esto afecta a:
   - la latencia;
   - la detección durante los escaneos (17–44 s, todos dentro de la zona sin contexto).
2. **La propiedad de los flujos** (`attribute_packets`). Depende del primer paquete visto, que puede ser anterior a
   60 s. Una ventana con 60 s de contexto puede seguir difiriendo de la operación.
   - Se comprobó: `flow_duration_mean_30s` difiere hasta 430 s y `flow_attempt_rate_10s` hasta 2,4 entre el replay y
     el acumulador en las mismas ventanas.
3. **El instante de emisión.** El motor puntúa cada ventana una vez, al aparecer, con ficheros de 15 s cerrados, y a
   veces con la ventana parcial. Sin `motor_decision.log` no se sabe cuándo se emitió cada decisión del 5-oct.
4. **Las ventanas tras fin + 21 s.** No hay datos.

### 1.3 Acumulador: versión de extracción y equivalencia

- **Versión.** Las filas las escribió `acumular_v3.py` con `extract_multilayer_v2.py` tal como estaban el 5-oct. El
  primer registro en git es el snapshot `a6d287a` (6-oct 05:27 UTC, posterior a la batería; blob `51fb157`).
  - **Es una inferencia razonable, no una prueba**: no hay registro git anterior.
  - El extractor vigente (`2d854a9`, blob `ec46849`) solo difiere en que acota a 1,0 `dns_nxdomain_ratio_60s` y
    `unique_dns_name_ratio_60s`. Esa transformación se aplicó a las filas y es exacta.
- **Repuntuar no es reconstruir.** Se compararon las 28 variables en las ventanas comunes evaluables de 10.10.20.30
  (`resultados/equivalencia-acumulador.json`):
  - **0 de 35 ventanas comunes son idénticas.**
  - Las diferencias están en las variables de flujo y en las razones de destinos y puertos únicos.
  - La señal coincide en casi todas las ventanas, salvo en el **IF 0,05 del DNS**: coincide en 3 de 6 ventanas
    (e3-r2) y en 3 de 7 (e3-r3). Justo ahí la versión anterior ya señalaba fragilidad.
- **Decisión** (preregistrada): el acumulador **no es equivalente**. Se presenta solo como sensibilidad y **no se
  publica la tabla combinada** replay + acumulador.
  - La variante de mayor cobertura no es la principal.
  - La variante anterior, con `capture_start` adelantado, no se recalcula como resultado.

---

## 2. Configuraciones (punto 2)

### Modelo y umbrales

- **IF limpio** `if_limpio_2026_10`: escalador y modelo congelados (sha256 `df547da0…fd60`), sin reentrenar.
- **Umbrales** recalculados sobre las 65 553 ventanas de validación; coinciden con 4.1 con una diferencia
  ≤ 2,2e-16 (`resultados/umbrales-verificados.json`):
  - α 0,05 → −0,5694578968
  - α 0,03 → −0,5898535710
- **Regla:** `score_samples < umbral`. Sin paquetes en 10 s no se puntúa.

### Heurísticos

- Versión `2026-10-06.2`, sin cambios, más la regla heredada `auth_failure_heuristic`.
- **Se ajustaron con esta misma batería**:
  - `a7fc7ea`: unicidad 0,45, «Validado: port_scan 3/3».
  - `9e7513f`: rama de ráfaga.
- Su resultado aquí **no es independiente**.

### Combinación real (`publicar_feed._verdicto_de`)

| Capa | Qué es aquí | De dónde sale |
|---|---|---|
| **Señal** | IF o heurístico en la ventana | Offline, IF limpio y heurísticos `2026-10-06.2` |
| **Acción propuesta** | LIMIT por el IF; la del heurístico si existe; gana la más severa | Offline |
| **Acción aplicada** | Solo el recuento por minuto de `publicar.log` del 5-oct, que salió del **motor de entonces** (modelo recalibrado y heurísticos `2026-09-30.1`), no del IF limpio | `evidencia/sensor-05oct/` |
| **Efecto** | Lo observable en el PCAP | `resultados/respuesta-05oct-por-episodio.csv` |

**No se atribuye ROC-AUC ni AP al híbrido**: no existe una puntuación combinada.

---

## 3. Marcas temporales y criterio (punto 3)

Todas las marcas están en el **reloj del sensor**: PCAP, `auth.log` y `syslog`. No se mezclan relojes. Hoy el sensor
va unos 47 s por detrás del bastión, pero eso no afecta a estas marcas.

| Marca | Fuente |
|---|---|
| Inicio del generador | SYN de la sesión SSH de control bastión → Kali:22 que lanza el comando de `orq.sh` (PCAP) |
| Fin del generador | FIN del bastión en esa sesión: el bucle de 90 s o el `nmap` terminó (PCAP) |
| Corroboración | Tsf de `features.csv` (`capture_start + 25`) y las sesiones `date` del bastión en `auth.log`, todas a < 1 s |
| Primer y último paquete | Kali → destino en el PCAP deduplicado |

Tres observaciones:

- **El último paquete de ataque está a ≤ 0,41 s del fin del generador** en los 9 episodios. Incluso con respuesta
  activa el generador paró cuando el paquete dejó de verse. El sensor ve el tráfico antes de que el host lo filtre, así
  que una caída en el destino no ocultaría paquetes de la Kali.
- **`window_end` no es el instante de emisión.** Es una cota inferior: la decisión real sale después, por los ficheros
  de 15 s y el proceso.
- **Margen posterior de 60 s:** es el horizonte de la variable más larga. Una ventana que termina más tarde ya no
  contiene paquetes del ataque.

### Categorías (`resultados/categorias-episodio.csv`)

| Cat. | Significado |
|---|---|
| **D** | Señal de 10.10.20.30 en una ventana evaluable con `window_end` entre el inicio y el fin del generador |
| **P** | Sin D, todas las ventanas durante el ataque evaluables, y primera señal en (fin, fin + 60 s] |
| **N** | Ni D ni P, y todas las ventanas de [inicio, fin + 60 s] evaluables |
| **NE** | El resto: falta contexto para afirmar la ausencia |

Una señal en una ventana evaluable cuenta como D aunque el episodio tenga ventanas sin contexto. En cambio, «no
detectado» exige que **todas** las ventanas sean evaluables.

---

## 4. Tabla 8 revisada (punto 4) — `resultados/TABLA8-r2.md`

**Celda:** episodios con D sobre episodios evaluables. Un episodio es evaluable si todas sus ventanas durante el ataque
lo son.

### Principal: replay con historia real

| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual | 0 de 3 | — | — | — | — | — |
| Inundación HTTP | 0 de 3 | — | — | — | — | — |
| Escaneo de puertos | 0 de 3 | — | — | — | — | — |
| **Total** | **0 de 9** | — | — | — | — | — |
| Fuerza bruta HTTP | 0 (no ejecutada) | — | — | — | — | — |

### Episodios no evaluables y lo que sí se observa en sus ventanas evaluables (replay)

| Ep. | IF 0,05 | IF 0,03 | Heur. | Híb. 0,05 | Híb. 0,03 | Lectura |
|---|---|---|---|---|---|---|
| e3-r1/r2/r3 | NE | NE | D a 62,5 / 48,2 / 43,6 s (`dns_entropy`) | igual | igual | El IF no da señal en las 3–5 ventanas evaluables. **No permite concluir** que no detecte. |
| e4-r1/r2/r3 | D a 49,0 / 53,9 / 58,1 s | ídem | D (`http_abuse`), misma ventana | D (IF + `http_abuse`, LIMIT) | ídem | Detección durante el ataque, pero en la **primera ventana evaluable**. La latencia no es medible. |
| e1-r1, e1-r3 | NE | NE | NE | NE | NE | El escaneo (18 s) cae entero en la zona sin contexto |
| e1-r2 | NE (señal a +6 s del fin) | NE | NE (señal a +6 y +16 s) | NE | NE | Solo hay señales posteriores, en ventanas evaluables, pero las del durante no lo son |

Las latencias se miden desde el inicio del generador hasta el `window_end` de la primera señal.

### Sensibilidad: filas del acumulador en vivo (no equivalentes; **no** son el resultado principal)

| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual | 3 de 3 | 2/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| Inundación HTTP | 3 de 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Escaneo de puertos | 3 de 3 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 |

**Detecciones posteriores (P) en esta fuente:**

- e1-r1 y e1-r3, en todas las configuraciones.
- La primera ventana con el barrido termina **4,1 s y 3,9 s después** del fin del `nmap`.
- El barrido real (≈ 1 470 SYN) ocurre en los últimos 5 s de un ataque de 18 s. La ventana que lo contiene cierra
  después del fin.

**IF 0,05 en DNS:** detecta e3-r2 (58,2 s) y e3-r3 (33,6 s) con puntuaciones de −0,5755 y −0,5749. Están a ≈ 0,006 del
umbral y en ventanas donde el replay no da señal. **Frágil.**

### Primeras marcas en el acumulador (`resultados/categorias-episodio.csv`)

| Ep. | IF 0,05 | IF 0,03 | Heurístico | Híbrido (componente, acción propuesta) |
|---|---|---|---|---|
| e3-r1 | N | N | D 12,5 s `dns_entropy` | D 12,5 s (heur., LIMIT) |
| e3-r2 | D 58,2 s | N | D 8,2 s | D 8,2 s (heur., LIMIT) |
| e3-r3 | D 33,6 s | N | D 13,6 s | D 13,6 s (heur., LIMIT) |
| e4-r1 | D 9,0 s | D 9,0 s | D 9,0 s `http_abuse` | D 9,0 s (IF + heur., LIMIT) |
| e4-r2 | D 3,9 s | D 3,9 s | D 13,9 s | D 3,9 s (IF, LIMIT) |
| e4-r3 | D 8,1 s | D 8,1 s | D 18,1 s | D 8,1 s (IF, LIMIT) |
| e1-r1 | P +4,1 s | P +4,1 s | P +4,1 s `port_scan` | P (IF + heur., BLOCK) |
| e1-r2 | D 20,5 s | D 20,5 s | D 20,5 s | D 20,5 s (IF + heur., BLOCK) |
| e1-r3 | P +3,9 s | P +3,9 s | P +3,9 s | P (IF + heur., BLOCK) |

### Señales compartidas y exclusivas durante el ataque (`resultados/senales-compartidas-durante.csv`)

**Acumulador**, en ventanas evaluables con fila de 10.10.20.30:

| Familia | Ventanas con IF y heurístico | Solo IF | Solo heurístico | Ninguno |
|---|---|---|---|---|
| e3 | α 0,05: 7 · α 0,03: 0 | 0 | 18 / 25 | 2 |
| e4 | 25 | 2 | 0 | 0 |
| e1 | 1 | 0 | 2 | 6 |

En el **replay**, en sus pocas ventanas evaluables: e3 solo heurístico (13 de 13) y e4 ambos (13 de 13).

### Lo que esto permite y no permite decir

- No hay ningún resultado episódico de esta batería que sea a la vez evaluable y equivalente a la operación.
- El replay solo dice algo de la segunda mitad de los ataques de 90 s. Ahí:
  - en HTTP, IF y heurístico coinciden;
  - en DNS solo dispara el heurístico.
- **No se reutiliza 6/9 · 7/9 · 9/9** ni el 6/9 · 9/9 · 9/9 de la versión anterior, porque dependía de la historia
  simulada.

---

## 5. Métricas por ventana (punto 5) — `resultados/ventanas-verificacion-r2.json`

**Población:** la misma de la Tabla 7, 65 421 normales + 84 de ataque.

**Verificación:** TP, FP, TN, FN, precisión, recall, F1 y FPR se recalcularon desde `ventanas-predicciones.csv.gz`.
Coinciden **exactamente** con la versión anterior, y el IF coincide con la Tabla 7.

| Configuración | TP | FP | TN | FN | Precisión | Recall | F1 | FPR |
|---|---|---|---|---|---|---|---|---|
| IF 0,05 | 54 | 2 955 | 62 466 | 30 | 0,0179 | 0,6429 | 0,0349 | 4,52 % |
| IF 0,03 | 54 | 1 723 | 63 698 | 30 | 0,0304 | 0,6429 | 0,0580 | 2,63 % |
| Heurísticos | 47 | 472 | 64 949 | 37 | 0,0906 | 0,5595 | 0,1559 | 0,72 % |
| Híbrido 0,05 | 54 | 3 417 | 62 004 | 30 | 0,0156 | 0,6429 | 0,0304 | 5,22 % |
| Híbrido 0,03 | 54 | 2 192 | 63 229 | 30 | 0,0240 | 0,6429 | 0,0464 | 3,35 % |

**Análisis operativo**, con las reglas del motor (las ventanas sin paquetes no se puntúan):

| Configuración | FPR |
|---|---|
| IF 0,05 | 4,33 % |
| IF 0,03 | 2,58 % |
| Heurísticos | 0,72 % |
| Híbrido 0,05 | 5,04 % |
| Híbrido 0,03 | 3,30 % |

Los TP no cambian.

**Ventanas de normalidad incierta** (74 de 10.10.20.30): ninguna configuración da falsa alarma en ellas.

### El híbrido no añade TP

Los 47 aciertos de los heurísticos ya los marca el IF. Combinarlos deja el recall igual y suma:

- 462 falsas alarmas con α 0,05;
- 469 falsas alarmas con α 0,03.

### Señal falsa frente a medida aplicada

| Configuración | FP sobre entidades en `NUNCA_BLOQUEAR` (señal sin medida) | FP sobre entidades accionables |
|---|---|---|
| IF 0,05 | 10 | 2 945 |
| IF 0,03 | 1 | 1 722 |
| Heurísticos | 470 (`dns_entropy` sobre 10.10.10.20) | 2 |
| Híbrido 0,05 | 472 | 2 945 |
| Híbrido 0,03 | 470 | 1 722 |

- La exclusión de respuesta (`NUNCA_BLOQUEAR`, `--excluir`) **no elimina la señal falsa**: solo impide la medida.
- La métrica por ventana cuenta la señal y por eso incluye esas FP.
- «Accionable» significa que el feed **publicaría** LIMIT o BLOCK para esa IP. Que se aplique depende de que exista
  un agente en el host destino; hoy solo hay uno, en srv-dmz.

---

## 6. Evidencia del 5-oct para la cadena de respuesta (no es 4.4)

`resultados/respuesta-05oct-por-episodio.csv` y `resultados/feed-05oct-por-minuto.csv`.

### Alineación de `publicar.log` con el cron

`publicar.log` no lleva hora; se alinea con las ejecuciones del cron del `syslog`:

- Hay 3 312 ejecuciones y 3 311 líneas.
- La línea 2630 empieza con bytes NUL: se perdió la cola del 2-oct.
- Por tanto, desde esa línea, la línea L corresponde a la ejecución L + 1. Lo confirma el `mtime` (6-oct 06:14 = última
  ejecución).

### Lo que publicó el feed (motor de entonces, no el IF limpio)

| Publicaciones | Contenido |
|---|---|
| 20:26–20:35 | 0 entradas: los tres DNS no generaron entrada |
| 20:36:01–20:45:01 | 1 LIMIT |
| 20:46:01 y 20:47:01 | 1 BLOCK de 10.10.20.30 con `revisar_humano` (3.ª ofensa del día → 3 600 s) |
| 20:48 y 20:49 | LIMIT |

El relay del bastión leyó el feed a :37–:39 de cada minuto (sesiones SSH en `auth.log`).

### Efecto observable en el PCAP

| Familia | Respuestas observadas | Lectura |
|---|---|---|
| e3 | 209 de 209 consultas respondidas | 10.10.10.20 está en `NUNCA_BLOQUEAR` y no tiene agente |
| e4 | SYN-ACK en el 100 % de las conexiones (6 386, 412, 411) | Ninguna caída visible. El LIMIT (100 paq/s) llegó al relay a las 20:36:38, 3 s antes del fin de e4-r1; e4-r2 y e4-r3 van muy por debajo de 100 paq/s |
| e1 | 3–5 SYN-ACK de 2 011–2 033 SYN y 0 RST | Los puertos cerrados estaban filtrados por el cortafuegos (nota O del 1-oct: «998 filtrados»). La ausencia de respuesta es la línea base, no un efecto. |

Sobre el escaneo y el BLOCK:

- El BLOCK publicado a las 20:46:01 llegó al relay después de que terminara e1-r2 (20:46:03,9).
- En e1-r3 (20:47:18–36) srv-dmz **siguió respondiendo** SYN-ACK a la Kali. Eso **no es compatible** con un BLOCK
  efectivo en ese momento.
- No hay registro del agente de srv-dmz para saber por qué.
- La cola lenta de e1-r2 (20:45:40–20:46:03, unos 10 SYN/s sin respuesta) **no se puede atribuir** a la respuesta
  activa: r1 y r3 corrieron con el mismo feed LIMIT y no la muestran.

### Conclusión

El 5-oct hay señal, acción propuesta y acción publicada. **No hay evidencia de acción aplicada ni de efecto.**

---

## 7. Lo que está listo, lo que se puede afirmar y lo que falta

### Listo para redactar

- **Métricas por ventana** sobre la población de la Tabla 7 (§5): cinco configuraciones, verificadas desde las
  predicciones, con la separación entre señal falsa y medida aplicable.
- **Estado de la batería del 5-oct como evidencia episódica** (§1, §4): por qué no es evaluable con la historia
  disponible y qué se observa en sus ventanas evaluables.
- **Combinación real del híbrido** (§2) y criterio temporal (§3).

### Afirmaciones que la evidencia permite

1. **Por ventana**, sobre la población de la Tabla 7, el híbrido no añade aciertos al IF y aumenta las falsas alarmas.
   - FPR 4,52 → 5,22 % con α 0,05.
   - FPR 2,63 → 3,35 % con α 0,03.
   - Casi todo el aumento son señales `dns_entropy` sobre el DNS/AD: el feed no las ejecutaría, pero existen.
2. Los heurísticos tienen una FPR por ventana del 0,72 %, pero sus umbrales se ajustaron con la batería del 5-oct.
3. En las ventanas evaluables de los episodios del 5-oct:
   - en la inundación HTTP, IF y heurístico dan señal en las mismas ventanas;
   - en el DNS de baja intensidad (≈ 2,3 consultas/s) solo da señal el heurístico.
   - Esto es descriptivo (N = 3, segunda mitad del ataque), no una tasa de detección.
4. La señal del IF en DNS con α 0,05 depende del procesamiento: aparece en las filas del acumulador y no en el replay,
   a ≈ 0,006 del umbral. Con α 0,03 no aparece en ninguna fuente.
5. En escaneos cortos (18 s) la primera ventana que contiene el barrido cierra **después** del fin del ataque (acumulador,
   +3,9 / +4,1 s). La detección de ese tipo de ataque es, como mucho, posterior.

### Afirmaciones que la evidencia **no** permite

- Ninguna tasa de detección episódica (x/9) para el IF limpio, los heurísticos o el híbrido en la batería del 5-oct.
- Ninguna latencia de detección operativa del 5-oct.
- Que la respuesta activa del 5-oct tuviera efecto.
- Que el híbrido aporte detecciones que los heurísticos solos no logran.
- Rendimiento independiente de los heurísticos.

### Pruebas que faltan

Están en `PROTOCOLO-ENSAYOS-NUEVOS.md` (punto 7):

- **Episodios nuevos con historia continua** (≥ 120 s antes de cada ataque) para la Tabla 8 por familia.
- **Fuerza bruta HTTP**, que no tiene ningún episodio.
- **Heurísticos sobre episodios no usados para fijar sus umbrales.**
- **Ensayos de respuesta activa separados**, con registro del agente y de nftables.
- **Medir el instante de emisión** desde `motor_decision.log` en lugar de `window_end`.

No se ajusta ningún parámetro ni se propone sustituir el IF para mejorar retrospectivamente estos resultados.
