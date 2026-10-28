# Resultados de las verificaciones SIN ataques

Verifican las **herramientas** de evaluación, no el desempeño de CyberFlow. No son resultados experimentales.

## Suite de herramientas — `tests/test_herramientas.py`

**Windows (laptop), 2026-10-28, tras añadir α 0,01:** `130 comprobaciones pasaron.` (87 previas + 43 de α 0,01;
las 14 pruebas previas siguen pasando con las mismas expectativas).

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
| Tiempos | IF 0,05 emitido por el modelo → `tiempo_es_emision_real=true`; IF 0,01/0,03 e híbridos → `false` (disponibilidad derivada, no latencia de emisión) |
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
