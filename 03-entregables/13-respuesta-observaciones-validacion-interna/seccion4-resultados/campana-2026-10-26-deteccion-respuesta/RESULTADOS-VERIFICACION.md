# Resultados de las verificaciones SIN ataques

Verifican las **herramientas** de evaluación, no el desempeño de CyberFlow. No son resultados experimentales.

## Suite de herramientas — `tests/test_herramientas.py`

**Windows (laptop), 2026-10-28, tras tratar `ventana_no_evaluada` (#59, sobre `2612e3f`):** `212 comprobaciones
pasaron.` (**213** con `CF_ANALIZADOR_PREVIO` = analizador de `a6dc5ab`). Las 23 pruebas anteriores pasan sin cambiar
ninguna expectativa. Se añaden `test_ventanas_no_evaluadas` (22) y `test_no_evaluada_real_compatibilidad` (3); los casos
están en `CAMBIOS-2026-10-28-no-evaluadas.md`. Son fixtures de código, no resultados experimentales.
Regresión: 0 diferencias de detección/cobertura en 7 y 5 configuraciones frente a los goldens, a `2612e3f`, a
`a6dc5ab` (86 excluidas de procedencia) y a `0d40bdb`. Sin eventos, `analisis.json` solo **añade** claves.
`test_matar_grupo.py` 6/6.

**Ejecución anterior — tras conservar los registros sin la clave `threshold` (sobre `a69224c`):**
`188 comprobaciones pasaron.` con `CF_ANALIZADOR_PREVIO` = `scripts/analizar.py` de `a6dc5ab` (**187** sin la
variable). Las 22 pruebas anteriores siguen pasando sin cambiar ninguna expectativa (incluido el caso
`threshold: null`); se añade `test_umbral_registrado_ausente` (16 comprobaciones).

### Umbral registrado ausente — comprobaciones del código (registros sintéticos, NO resultados experimentales)

| Comprobación | Resultado |
|---|---|
| La línea de la alerta no contiene `threshold` (clave eliminada, no null) | ✔ |
| La alerta sigue en `emisiones_observadas`: ALERT, `IF_desplegado`, score −0,70, `logged_at` T+41, `window_end` T+40 | ✔ |
| Referencia al original: `motor:5`, línea 5, sha256 del log | ✔ |
| Incidencia `motor:5 (<archivo>): falta la clave 'threshold'…` y `incidencias_registro` en la emisión | ✔ |
| `umbral_registrado` desconocido (`clave_ausente`), configuración desconocida, sin coherencia score/umbral | ✔ |
| No es la primera alerta confirmada del IF desplegado; se cuenta como desconocida | ✔ |
| Las 7 configuraciones siguen derivadas; clasificaciones, cobertura y Tabla 8 iguales al registro completo | ✔ |
| Registro completo: confirmada, sin incidencia, latencia real 41 s | ✔ |
| `threshold: null`: estado `null`, texto distinto de la ausencia, igual de desconocido; sin latencia confirmada | ✔ |
| Sin `logged_at` / `window_end_utc` / `decision` / `entity_ip` / `packet_count_10s`: se descarta con incidencia | ✔ (5) |

**Regresión de detección/cobertura:** 0 diferencias frente a `a69224c` (7, 0 excluidas), `a6dc5ab` (7, 86 excluidas de
procedencia, como antes), `0d40bdb` (5) y los dos goldens. `analisis.json` completo frente a `a69224c` sobre los
fixtures: solo el campo nuevo `umbral_registrado_estado` (6 emisiones). Diferencia esperada en la entrada con la clave
ausente: el episodio pasa de no evaluable (8/9 anclas, registro descartado) a evaluable; sin latencia confirmada en
ambos casos. Detalle en `CAMBIOS-2026-10-28-umbral-ausente.md`.

**Ejecución anterior — tras corregir la procedencia temporal (config `2026-10-28.2`):**
`172 comprobaciones pasaron.` Las 20 pruebas anteriores siguen pasando; en 3 se **corrigió la expectativa** que
aceptaba IF 0,05 recalibrado como «emitido» (`test_analizador_basico`, `test_emitido_vs_derivado`,
`test_siete_configuraciones`) y se añaden `test_procedencia_emisiones` y `test_conteos_cobertura_7_sin_cambios`.
Ejecución con `CF_ANALIZADOR_PREVIO` apuntando al `scripts/analizar.py` de `a6dc5ab` (activa la comparación directa
con el analizador anterior). Sin esa variable la comparación directa se omite y la suite informa **171** (la
comparación con el golden de 7 configuraciones se hace igual).

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador_basico
OK  test_cobertura_una_ventana_insuficiente
OK  test_score_nulo_con_heuristico
OK  test_tabla8_evidencia_y_denominador
OK  test_ventana_previa
OK  test_emitido_vs_derivado
OK  test_integridad_backing
OK  test_integridad_informe_externo
OK  test_integridad_descriptor_ilustrativo
OK  test_integridad_gate_analizador
OK  test_integridad_e2e_no_habilita_denominador
OK  test_umbral_001_procedencia
OK  test_comparacion_estricta
OK  test_escala_anomalia
OK  test_siete_configuraciones
OK  test_no_regresion_005_003
OK  test_anidamiento_por_alfa
OK  test_procedencia_emisiones
OK  test_conteos_cobertura_7_sin_cambios
172 comprobaciones pasaron.
```

### Procedencia temporal — comprobaciones del código (registros sintéticos, NO resultados experimentales)

| Caso | Resultado |
|---|---|
| 1. ALERT real del IF desplegado (score −0,70, cruza los tres umbrales) | IF 0,05/0,03/0,01 `durante` con base `derivado(...)` y `tiempo_significado` = disponibilidad del registro; **una** emisión aparte: `IF_desplegado`, `ALERT`, `logged_at` T+41 ≠ `window_end` T+40, modelo/score/umbral registrados (umbral = desplegado → `confirmada`), `durante_actividad`, `origen+destino`, respaldo línea 5 + sha256; latencia real 41 s; no es columna de la Tabla 8 |
| 2. Score −0,56942 (entre el 0,05 desplegado y el recalibrado) con ALERT real | IF 0,05 recalibrado `sin_deteccion` (Tabla 8 = 0) **y** alerta real del desplegado registrada aparte |
| 3. IF 0,01 positivo sin ALERT | clasificación `durante` derivada; **ninguna** emisión ni latencia real inventada |
| 4. Heurístico `dns_entropy` registrado en vivo (PERMIT) | HEUR comparativo derivado; `evidencia_registrada.heuristico_registrado = dns_entropy`; evento `heuristico:dns_entropy` sin ALERT; ninguna emisión del IF |
| 5. Identificación insuficiente (ALERT sin `detector_name`; umbral null; umbral registrado = 0,05 recalibrado ≠ desplegado; config sin `modelo.detector`) | configuración `desconocida` sin rellenar (se informa el umbral **registrado** o «desconocido»); emisor `desconocido` con motivo cuando falta; sin latencia real; la clasificación comparativa no cambia |

**Conteos y cobertura sin cambios.** `tests/regresion_alfa.py --comparar <analizar.py de a6dc5ab> --configs 7` →
**0 diferencias de detección/cobertura en 7 configuraciones** (Tabla 8, evaluabilidad, cobertura, evidencia de destino,
categoría y primera señal por configuración, señales previas/observadas, solapamiento 0,05 y 0,01, control FPR,
métricas, calidad de datos). Con `0d40bdb` y 5 configuraciones, también 0. Diferencias **excluidas** y listadas
aparte (86 frente a `a6dc5ab`): solo `base` (p. ej. IF 0,05 `emitido_por_modelo_desplegado` →
`derivado(umbral_recalibrado_0.05; distinto del desplegado)`, HEUR `registrada_en_vivo` →
`derivado(componente_heuristico_registrado)`, híbridos `derivado(feed)` → `derivado(IF_α OR HEUR)`),
`tiempo_es_emision_real` (retirado), y los nuevos `tiempo_significado` y `evidencia_registrada`.

### Ejemplo de salida (fixture `fuerza_bruta_http-r1`): clasificación derivada y emisión real por separado

```
episodios.fuerza_bruta_http-r1.IF_0.05   (clasificación comparativa)
  categoria: durante · window_end 08:40:30 · logged_at 08:40:31 · score -0.6 · atribucion origen+destino
  base: derivado(umbral_recalibrado_0.05; distinto del desplegado)
  tiempo_significado: disponibilidad_del_registro(logged_at); no es latencia de emision de esta configuracion
  evidencia_registrada: decision ALERT · detector if_limpio_2026_10 · heuristico null

emisiones_observadas.registros[motor:49]  (evento real del log)
  tipo alerta_emitida · componente_emisor IF_desplegado · decision_emitida ALERT
  logged_at 08:40:31 · window_end 08:40:30 · modelo if_limpio_2026_10 · score -0.6
  configuracion_emisora: umbral_registrado -0.5693969936322356 · confirmada · coherente(score<umbral)
  episodio fuerza_bruta_http-r1 · durante_actividad · origen+destino · respaldo motor.log línea 49 + sha256

episodios.fuerza_bruta_http-r1.emisiones_observadas
  primera_alerta_IF_desplegado_confirmada_durante: motor:49, 31.0 s desde el inicio
```

### Ejecución anterior (130 comprobaciones, α 0,01, commit `a6dc5ab`)

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador_basico
OK  test_cobertura_una_ventana_insuficiente
OK  test_score_nulo_con_heuristico
OK  test_tabla8_evidencia_y_denominador
OK  test_ventana_previa
OK  test_emitido_vs_derivado
OK  test_integridad_backing
OK  test_integridad_informe_externo
OK  test_integridad_descriptor_ilustrativo
OK  test_integridad_gate_analizador
OK  test_integridad_e2e_no_habilita_denominador
OK  test_umbral_001_procedencia
OK  test_comparacion_estricta
OK  test_escala_anomalia
OK  test_siete_configuraciones
OK  test_no_regresion_005_003
OK  test_anidamiento_por_alfa

130 comprobaciones pasaron.
```

### α 0,01 — comprobaciones del código (fixtures y datos sintéticos, NO resultados experimentales)

| Comprobación | Resultado |
|---|---|
| Lectura del umbral 0,01 de `config-campana.json` | `-0.6223889502095352` exacto (`repr`), sin redondeo |
| Procedencia | igual (float exacto) a `validacion_sin_kali_65553["0.010"]` de la calibración de 4.1; 0,05 y 0,03 también; sha256 de la fuente = el declarado; un 0,01 redondeado (`-0.62238895`), ausente o de texto → el analizador **aborta** |
| Umbral desplegado | `-0.5693969936322356` conservado y distinto del 0,05 recalibrado `-0.5694578968203694` |
| Comparación estricta | `score == umbral` no da señal en ninguno de los tres α; 1 ULP por debajo, sí; un score entre el umbral completo y el redondeado a 8 decimales no da señal 0,01 |
| Escala de anomalía | `score < u ⇔ −score > −u` en 5 009 scores (con fronteras ±1 ULP); `umbral_anomalia 0,01 = 0.6223889502095352`, no el cuantil recalculado `0.6223889502095351` |
| 7 configuraciones | orden IF 0,05 · IF 0,03 · IF 0,01 · HEUR · HIB 0,05 · HIB 0,03 · HIB 0,01 en `CONFIGS`, `analisis.json`, Tabla 8 y `TABLA8.md`; HEUR una sola vez |
| Tiempos | (en `a6dc5ab`: IF 0,05 → `tiempo_es_emision_real=true`. **Corregido** en `2026-10-28.2`: era incorrecto, el 0,05 recalibrado no es el desplegado; ver la sección de procedencia temporal) |
| No-regresión 0,05/0,03 | `tests/regresion_alfa.py`: proyección de IF 0,05, IF 0,03, HEUR, HIB 0,05, HIB 0,03, compartidas 0,05, control FPR, métricas y calidad de datos sobre 5 episodios (4 evaluables) → **0 diferencias** frente al analizador anterior (golden y comparación directa con `analizar.py` de `0d40bdb`) |
| Anidamiento | 5 003 ventanas sintéticas: IF 0,01 ⊆ 0,03 ⊆ 0,05 y HIB 0,01 ⊆ 0,03 ⊆ 0,05, no triviales; umbrales invertidos → detectado |

Corrida CLI sobre `tests/fixtures.py` (con evidencia de destino completa e integridad apta, como en
`regresion_alfa.py`). El episodio `fuerza_bruta_http-r1` tiene scores −0,60 (dispara 0,05 y 0,03, no 0,01), el
umbral 0,01 exacto (no dispara: estricto) y −0,63 (dispara los tres):

| Familia | Evaluables | IF 0,05 | IF 0,03 | IF 0,01 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 | Híbrido 0,01 |
|---|---|---|---|---|---|---|---|---|
| Inundación HTTP | 2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| DNS inusual | 1 | 0/1 | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| Escaneo breve | 0 | — | — | — | — | — | — | — |
| Fuerza bruta HTTP | 1 | 1/1 | 1/1 | 1/1 | 0/1 | 1/1 | 1/1 | 1/1 |

Control (60 ventanas, denominador explícito): falsas alarmas IF 0,05 = 5, IF 0,03 = 5, IF 0,01 = 3, HEUR = 2,
HIB 0,05 = 6, HIB 0,03 = 6, HIB 0,01 = 4. En `fuerza_bruta_http-r1`: primera señal IF 0,05/0,03 en la ventana con
−0,60 y IF 0,01 en la de −0,63; `compartidas_durante_0.05` solo_IF = 3 y `compartidas_durante_0.01` solo_IF = 1
(la ventana en el umbral exacto no cuenta). Son valores de fixtures, no de CyberFlow.

### Ejecución anterior (87 comprobaciones, antes de α 0,01)

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador_basico
OK  test_cobertura_una_ventana_insuficiente
OK  test_score_nulo_con_heuristico
OK  test_tabla8_evidencia_y_denominador
OK  test_ventana_previa
OK  test_emitido_vs_derivado
OK  test_integridad_backing
OK  test_integridad_informe_externo
OK  test_integridad_descriptor_ilustrativo
OK  test_integridad_gate_analizador
OK  test_integridad_e2e_no_habilita_denominador
87 comprobaciones pasaron.
```

### Evidencia de destino y denominador de la Tabla 8 (`test_tabla8_evidencia_y_denominador`, e2e hasta `analisis.json`/`TABLA8.md`)

La evidencia de destino debe **cubrir el intervalo** (todas las ventanas del ataque). Numerador/denominador/categoría:

| Caso | ¿evaluable (denominador)? | IF 0,05 (numerador) | categoría |
|---|---|---|---|
| sin `--destinos` | no | 0 | no_evaluable |
| archivo vacío | no | 0 | no_evaluable |
| evidencia de otro episodio | no | 0 | no_evaluable |
| evidencia incompleta del episodio | no | 0 | no_evaluable |
| **completa con señal atribuible** | **sí** | **1** | durante |
| completa **sin** señal atribuible | **sí** | 0 | sin_deteccion |
| señal hacia otro destino | sí | 0 | sin_deteccion |

Evidencia ausente/incompleta → **no evaluable** (no se presenta como «sin detección»). Una ausencia solo se afirma
con evidencia **completa**. Una señal hacia otro destino no cuenta como detección y no prueba que la evidencia esté
completa.

### Integridad de fuentes — declaraciones vs verificaciones (`test_integridad_backing`, `test_integridad_informe_externo`, `test_integridad_descriptor_ilustrativo`)

`verificar_integridad.py` distingue **verificado / declarado_sin_verificar / ausente / desconocido**; solo
«verificado» cuenta, y el valor lo aporta un **respaldo accesible y correspondiente** (no un booleano del descriptor).
Casos: cobertura/continuidad declaradas sin respaldo → declarado_sin_verificar; respaldo de otro episodio o con
periodo que no cubre → ausente; hash marcador/inválido/que no coincide → ausente; relojes sin mediciones →
desconocido; reinicio sin historia → ausente / con recuperación+calentamiento → verificado; error de captura
relevante → ausente; informe externo **accesible y correspondiente** → verificado, mientras que referencia
inexistente → pendiente y referencia que no respalda / de otro episodio → ausente; descriptor sin ficheros → no apto.

**Recorrido e2e** (`test_integridad_e2e_no_habilita_denominador`): `verificar_integridad.py` (no apto) →
`integridad.json` → `analizar.py`: el episodio queda en `no_evaluables`, **fuera del denominador** y numerador 0.

### Ejemplo de salida de integridad (`EJEMPLO-integridad-salida.json`) — declarado / no apto / apto

Generado con `verificar_integridad.py --descriptor EJEMPLO-descriptor-integridad.json` desde la carpeta de la
campaña (los `EJEMPLO-fixtures/` son fixtures de la herramienta, no capturas de campaña):

```
{"aptos": ["inundacion_http-r1"], "no_aptos": ["inundacion_http-r3", "inundacion_http-r2"]}
inundacion_http-r3: apto=False | declarado_sin_verificar=8  ausente=1 (marcador de hash)   -> DECLARADO
inundacion_http-r2: apto=False | verificado=1  ausente=1 (error de captura)  desconocido=10 -> NO APTO
inundacion_http-r1: apto=True  | verificado=12                                              -> APTO
```

### Manifiesto sobre los bytes publicados (punto de hashes)

`MANIFIESTO-CAMPANA.json` se genera con `scripts/generar_manifiesto.py`, que hashea `git show :<ruta>` (los bytes
**en stage = los que se publican**, con saltos **LF**), no el fichero local (que en Windows puede tener CRLF). Tras
el commit se verifica que el sha256 de `git show HEAD:<ruta>` coincide con el manifiesto. No se declara coincidencia
«exacta» con el árbol de trabajo si solo coincide tras normalizar los saltos; la referencia son los bytes del commit.

### Terminación del grupo de procesos — `tests/test_matar_grupo.py` (función publicada)

- **Windows:** `6 comprobaciones` (casos huérfano/interrupción marcados POSIX, verificados en el sensor).
- **Sensor (Linux), contra la función publicada `correr_episodio`:**

```
OK  test_normal
OK  test_hijo_ignora_sigterm
OK  test_padre_termina_antes
OK  test_interrupcion
6 comprobaciones de terminación pasaron.
```

Ningún hijo deja testigo tras la limpieza en los cuatro casos (normal, hijo que ignora SIGTERM, padre que termina
antes, interrupción).

Cubre, además de la ronda 1 (validación, comandos sin marcadores, simulación por defecto, orden reproducible,
timeout que mata al grupo, inicio/fin separados, duplicados, control FPR): **cobertura insuficiente con una sola
ventana** (90 s → no evaluable, separando «existe señal» de «primera fiable»); **score null conservado** con señal
heurística (IF no aplicable, HEUR dispara); **atribución** con mapa vacío / clave ausente (incompleta, no confirmada) /
destino distinto (excluida) / destino correcto (confirmada); **ventana previa** emitida tras el inicio (no cuenta como
«durante», se informa aparte); **emitido vs derivado por componente** (IF por el modelo desplegado; IF 0,03 e híbridos
derivados; heurístico LIMIT registrado en vivo, no ALERT).

## Fallo seguro de sombra y restauración — `tests/test_sombra.sh` (comandos simulados)

`11 ok, 0 fallos`. Ningún caso de fallo anuncia éxito ni sale con 0:

```
OK  sombra feliz
OK  sudo denegado
OK  servicio no se detiene
OK  consulta nft falla
OK  falta --motor-verificado
OK  restaurar correcta
OK  restaurar a enmascarado
OK  escalada pendiente (sin confirmar)
OK  error de verificación
OK  restaurar sin respaldo
OK  restaurar respaldo incompleto
```

## Ruta POSIX en el entorno real — sondas en el sensor (Linux)

El generador termina el **grupo** de procesos con `killpg` (SIGTERM→SIGKILL). Verificado en el Sensor1:

```
# hijo normal
RESULTADO: OK killpg mato el grupo (hijo incluido)
# hijo que IGNORA SIGTERM y padre que termina antes
RESULTADO: OK SIGKILL al grupo mato al hijo que ignora SIGTERM
```

## Analizador — corrida CLI sobre fixtures con resultado conocido (`tests/fixtures/`)

`tests/fixtures.py` escribe marcas + motor.log con resultado conocido; `analizar.py` produce:

| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| Inundación HTTP | 2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| DNS inusual | 1 | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 |
| Escaneo breve | 0 | — | — | — | — | — |

Calidad de datos detectada en el fixture: 1 ventana duplicada (deduplicada), `escaneo_breve-r1` incompleto y sin
cobertura del motor → **no evaluable**. Coincide con el diseño del fixture: en `inundacion_http-r1` la señal es
**durante** y **emitida en vivo**; en `inundacion_http-r2` es **posterior**; en `dns_inusual-r1` solo HEUR
(derivado, no emitido) e IF **sin detección**. Métricas por ventana con etiquetas: IF 0,05 TP=1, FP=0.

## Endpoint de fuerza bruta — prueba en aislamiento (loopback)

```
sin credenciales      -> 401
credenciales inválidas-> 401
credencial de control -> 200
ruta equivocada       -> 404
```

Con registro por petición. Confirma que la auth se evalúa (el bug `return 200` de nginx está corregido).
Pendiente de comprobar en srv-dmz: que el puerto cruce el espejo y que Suricata lo parsee como HTTP.
