# Presupuesto temporal de extremo a extremo

**Pregunta:** ¿puede la cadena actual aplicar la respuesta en el host **antes** de `t_fin_programado`? Y si no puede, ¿qué tramo lo impide y en qué etapa se corregiría?

**Herramientas** (solo lectura):

- `herramientas/presupuesto_e2e.py`. Simula la cadena con el **código desplegado extraído literalmente**: `_verdicto_de` del publicador f7bc4c7d y `escalada.procesar` 7d80ab4a.
- `pruebas/test_presupuesto_e2e.py`, 17 comprobaciones y 0 fallos. Entre ellas, que el simulador reproduce **exactamente** el feed y el estado de escalada finales que dejó el publicador real en sombra durante el 3B.
- Resultados en `resultados/presupuesto-e2e.json` y [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md).

---

## 1. Cadena y cadencias

Clases: **M** medido · **C** configurado · **E** estimado · **D** desconocido.

| # | Tramo | Mecanismo | Valor | Clase | Referencia |
|---|---|---|---|---|---|
| A | Acumulación: del inicio al cierre de la primera ventana con señal | Ventanas de 10 s (paso) sobre historia de 60 s; umbrales de los heurísticos | 0,9 / **7,9** / 23,1 s (mín/med/máx, 25 episodios) | M | `revision-3b/diagnosticos/demora.json` |
| B | Espera de PCAP: la ventana espera a que el PCAP que la cubre esté cerrado | `tcpdump -G 15`. El motor no decide antes de cerrar el PCAP (`7b275b8`). | 2,0 / **12,0** / 14,0 s | C (−G 15) / M | demora.json; paso del PCAP p50 = 15,0 s (844 ficheros) |
| C | Espera de ciclo | `--step-seconds 10`; latido p50 10,0 s, máx 11,1 | 0,45 / **1,45** / 10,5 s | C / M | demora.json, ciclos.jsonl |
| D | Proceso del ciclo hasta la escritura | parseo del PCAP, atribución, filas y puntuación | 1,2 / **2,6** / 7,0 s (en el episodio); ciclo p50 0,68, p99 7,0, máx 10,6 s | M | demora.json |
| — | **t_det** | `registro_escrito_en` del ciclo | — | M | ciclos.jsonl |
| E | Espera del publicador | timer `*:*:00/10`, AccuracySec=1s; arranca en :x0,29 | 0–10 s más 0,29 | C / M | `deploy/enforcement/ppi-publicar-feed.timer`; journal del 3B, 972 ejecuciones |
| F | Publicación: lectura de 120 s, escalada y firma | `publicar_feed.py` | p50 0,598 · máx 0,773 s | M | journal del 3B |
| G | Relé sensor → bastión → srv | timer `*:*:03/10` en el bastión, `scp` doble | 1,065–1,612 s | C / M (pocas muestras) | `systemctl show` en el bastión |
| H | Espera del agente | timer `*:*:06/10`, AccuracySec=1s | arranque en :x6 + 0–1 s | C (offset real **D**) | `ppi-enforce-agent.timer` |
| I | Agente: verificación de firma y lote nft atómico | `agente_enforce.py --aplicar --sudo` | p50 0,173 · máx 0,564 s | M (octubre) | 76 201 ejecuciones, octubre |
| — | **t_apl** | commit nft | — | **E** en A; **D** hoy (no se registra la hora del commit) | — |
| J | Activación: del commit al primer paquete descartado | nft (kernel) | ≈ 0, no medido | D | sin `counter` en las reglas |
| K | Efecto: de la aplicación al cese de las respuestas del destino | depende del ataque (retransmisiones, keep-alive, conexiones abiertas) | — | D | requiere SPAN más contadores (Etapa 2/4) |

**Nota sobre los LIMIT.** Las conexiones TCP ya establecidas no se cortan con un `drop` por origen, salvo que sus paquetes superen la tasa. El efecto de un LIMIT es **desconocido** hasta medirlo.

### 1.1 Tramo E–I con la configuración actual (V0)

- El publicador lee el registro en su ejecución :x0. El relé copia el feed en :x3, y el agente lo aplica en :x6 (+0–1 s) más su duración. Por tanto, `t_apl − t_det` = (espera hasta el siguiente :x0) + ~6,2–7,6 s.
- **Por episodio** (25), con t_det medido:
  - `t_apl − t_det` ∈ [5,7; 14,8] s en la cota inferior y [7,9; 17,2] s en la superior.
  - Mediana de la superior: 11,1 s.
- No es una constante: depende de la fase de t_det respecto a :x0, y por eso se calcula episodio a episodio.

### 1.2 Advertencias del código que afectan al presupuesto

1. **Ventana del publicador: 120 s.** Una decisión escrita más de 120 s después de su `logged_at` no se publica. No afecta a la primera señal (se publica en ≤ 10 s), pero sí a las **tardías**: en el 3B hubo 655 en el inventario, todas ventanas de 0 paquetes.
2. **Escalada persistente.** El origen estaba en **nivel 3** desde las pruebas de la madrugada (03:51–03:57). Véase la §5.
3. **Etiqueta de umbrales.** El servicio pasa `--umbrales 2026-10-06.1` y el código es la `.2`. Gana el código y se emite un aviso en el journal. No altera los tiempos; se corrige en la Etapa 2.
4. **Comentario desfasado** en `relay-feed.sh` («cada 60 s»). El timer real es de 10 s.

---

## 2. Presupuesto por episodio (3B, estimado)

La tabla completa está en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) §1. Resumen por escenario, como distribución de los **totales por episodio**:

| Escenario | `t_fin_prog` (s) | t_det − t_inicio, mín/med/máx | t_apl − t_inicio (cota sup.), mín/med/máx | V0: antes/indet./después | Margen mínimo (s) |
|---|---|---|---|---|---|
| Escaneo sostenido | 65,5–66,3 (natural) | 22,0 / 26,6 / 39,6 | 32,5 / 38,4 / 47,5 | 5/0/0 | 18,3 |
| Fuerza bruta HTTP | 90 | 18,4 / 23,6 / 25,1 | 28,5 / 32,6 / 35,5 | 5/0/0 | 54,5 |
| Inundación HTTP | 90 | 24,2 / 25,4 / 29,3 | 32,3 / 42,5 / 45,5 | 5/0/0 | 44,5 |
| DNS inusual | 90 | 17,2 / 21,9 / 25,9 | 28,5 / 33,5 / 37,6 | 5/0/0 (**sin punto de aplicación**) | 52,4 |
| **Escaneo breve** | **17,6–18,0** | 16,4 / 28,8 / 39,5 | **28,2 / 40,6 / 50,6** | **0/0/5** | **−32,7 a −10,6** |

**Lectura:**

- En las familias de 66–90 s, la cadena actual cabe en el presupuesto con margen. Los cuellos de botella son la **aplicación real** (agente inactivo, D7) y el **efecto** (desconocido).
- En el **escaneo breve no cabe**: incluso t_det (mediana 28,8 s) es posterior al fin (17,6–18,0 s) en 4 de 5 episodios.
- En la estimación del 3B, el fin de nmap es el natural de cada episodio. Con el `D_ref` mínimo propuesto (65,52 / 17,59 s), las conclusiones no cambian.

---

## 3. Variantes: qué arreglaría cada mejora

Las variantes son **estimaciones**, recalculadas por episodio con los mismos registros:

- **V0:** la cadena actual.
- **V1:** cadena por eventos. Publicador, relé y agente se encadenan al escribirse el ciclo, sin esperar timers: `t_apl − t_det` ∈ [1,8; 2,9] s, con las duraciones medidas de F, G e I.
- **V2:** V1 más la decisión **inmediata al cierre de la ventana** (B = C = 0), con la duración medida del ciclo que la decidió. Es la cota inferior con **las mismas ventanas y los mismos heurísticos**.

| Escenario | V0 antes del fin | V1 antes del fin | V2 antes del fin | Ventana con señal cierra antes del fin |
|---|---|---|---|---|
| Escaneo sostenido | 5/5 | 5/5 | 5/5 | 5/5 |
| Fuerza bruta HTTP | 5/5 | 5/5 | 5/5 | 5/5 |
| Inundación HTTP | 5/5 | 5/5 | 5/5 | 5/5 |
| DNS inusual | 5/5 | 5/5 | 5/5 | 5/5 |
| **Escaneo breve** | **0/5** | **0/5** | **1/5** | 3/5 |

En el escaneo breve, el único caso de V2 que llega (r1) lo provoca una señal `brute_force` («5 req HTTP»), **no** `port_scan`. Esa señal está mal atribuida al tipo de ataque, y no se debe contar como acierto del detector previsto.

### 3.1 ¿Bastaría rotar el PCAP a 5 s (`-G 5`)?

**No.** Cota del peor caso en el escaneo breve, sumando los tramos **del mismo episodio** (no medianas):

| Tramo | Hoy | Con `-G 5` | Con `-G 5` + ciclo por inotify + V1 |
|---|---|---|---|
| Cierre de la primera ventana que contiene el inicio (rejilla de 10 s) | 0–10 s | 0–10 s | 0–10 s |
| Espera de PCAP | 0–15 s | 0–5 s | 0–5 s |
| Espera de ciclo | 0–10 s | 0–10 s | ~0 s |
| Proceso del ciclo (M; p99) | ≤ 7,0 s | ≤ 7,0 s | ≤ 7,0 s |
| Cadena E–I | 5,7–17,2 s | 5,7–17,2 s | 1,8–2,9 s |
| **Peor caso** | **≈ 59 s** | **≈ 49 s** | **≈ 25 s** |
| Fin del escaneo breve | 17,6 s | 17,6 s | 17,6 s |

**Además, todo lo anterior supone que la primera ventana ya dispara `port_scan`.** En el 3B **no** ocurrió en ningún episodio:

- La primera ventana (que contiene entre 0,6 y 8 s de ataque) nunca dio señal.
- La primera señal salió de la **2.ª** ventana en 3/5 episodios (r1, r2, r3; en r1 era `brute_force`) y de la **3.ª** en 2/5 (r4, r5). En estos dos últimos, la ventana cerró 23 s después del inicio, es decir, después del fin.

- Las ráfagas ≥ 200 intentos/30 s se alcanzan en pocos segundos (nmap -T4 hace ~55 puertos/s). La señal se retrasa por **cómo se construyen y deciden las ventanas** (paso de 10 s, historia de 60 s, completitud SYN calculada al cierre) y por la espera a que el PCAP se cierre.

**Incompatibilidad declarada:** con ventanas de 10 s decididas solo tras el cierre del PCAP y una cadena por timers, **no es posible** responder a un escaneo de ~18 s antes de que termine. Mejorarlo exige las tres cosas a la vez:

1. **Etapa 2 (captura y cadena):**
   - rotación más corta, o lectura incremental del PCAP abierto con la misma regla de «paquetes decodificados» del motor;
   - ciclo disparado por eventos (inotify) en lugar de por paso fijo;
   - publicador, relé y agente encadenados por eventos, con push firmado en lugar de tres timers desfasados.
2. **Etapa 3 (heurísticos):** una regla de escaneo que decida con **evidencia parcial**: un umbral de ráfaga sobre los primeros segundos, evaluado en cuanto el contador lo supera y no al cierre de la ventana. Y siempre sin usar la IP del generador.
3. **Comprobación:** con 1 y 2, la cota del peor caso debe quedar por debajo de 17,59 − margen. La Etapa 2 debe medir el nuevo presupuesto **por episodio** y no con medianas.

Si D2 se resolviera redefiniendo el objetivo como contención de la **reincidencia**, el escaneo breve saldría del objetivo operativo, y así se declararía.

---

## 4. Requisitos de medición para que t_apl y t_efecto dejen de ser estimaciones (Etapa 2)

| Marca | Qué falta | Dónde |
|---|---|---|
| t_det | nada: `registro_escrito_en` ya existe | motor |
| t_pub | hora de lectura y de escritura del feed, con la lista de IPs y la versión | journal del publicador (hoy solo la duración) |
| t_relay | hora de llegada del feed a srv | relé (hoy, journal no legible para gadmin) |
| **t_apl** | hora del commit nft con su código de retorno, el **lote aplicado** y una lectura posterior del set con `expires` | agente (hoy solo «aplicado») |
| **t_efecto** | contadores por regla (`counter`) más la desaparición de respuestas del destino en el SPAN | reglas nft (D7) + herramienta de análisis |

---

## 5. Contaminación entre episodios (consecuencia directa del presupuesto)

- La simulación secuencial (tabla 3 de TABLAS-E2E) muestra que, con el agente activo y el estado real, **24/25 episodios del 3B habrían empezado con el origen ya bloqueado**: BLOCK de 3600 s, nivel 3 y revisión humana marcada.
  - El primer episodio empezó sin BLOCK vigente, pero ya en nivel 3.
- El origen había alcanzado el nivel 3 en las pruebas de la madrugada (03:51–03:57): `port_scan` → BLOCK al final de una inundación HTTP. Este es otro síntoma del problema de separación de la Etapa 3.
- En la campaña B, sin limpieza verificada del estado y de los sets entre episodios (D5), **no se mediría nada**. Las restricciones heredadas de un episodio anterior convierten el siguiente en un **fallo del experimento**.
- La separación actual entre episodios (90 s de observación + 120 s de contexto = 210 s) es menor que el LIMIT de 300 s y que cualquier BLOCK.
