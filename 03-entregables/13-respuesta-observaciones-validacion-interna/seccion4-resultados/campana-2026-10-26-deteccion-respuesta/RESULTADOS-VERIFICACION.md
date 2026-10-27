# Resultados de las verificaciones SIN ataques

Verifican las **herramientas** de evaluación, no el desempeño de CyberFlow. No son resultados experimentales.

## Suite de herramientas — `tests/test_herramientas.py`

**Windows (laptop):** `44 comprobaciones pasaron.`

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador_basico
OK  test_cobertura_una_ventana_insuficiente
OK  test_score_nulo_con_heuristico
OK  test_atribucion
OK  test_ventana_previa
OK  test_emitido_vs_derivado
44 comprobaciones pasaron.
```

Cubre, además de la ronda 1 (validación, comandos sin marcadores, simulación por defecto, orden reproducible,
timeout que mata al grupo, inicio/fin separados, duplicados, control FPR): **cobertura insuficiente con una sola
ventana** (90 s → no evaluable, separando «existe señal» de «primera fiable»); **score null conservado** con señal
heurística (IF no aplicable, HEUR dispara); **atribución** con mapa vacío / clave ausente (incompleta, no confirmada) /
destino distinto (excluida) / destino correcto (confirmada); **ventana previa** emitida tras el inicio (no cuenta como
«durante», se informa aparte); **emitido vs derivado por componente** (IF por el modelo desplegado; IF 0,03 e híbridos
derivados; heurístico LIMIT registrado en vivo, no ALERT).

## Fallo seguro de sombra — `tests/test_sombra.sh` (comandos simulados)

`7 ok, 0 fallos`. Ningún caso de fallo anuncia éxito ni sale con 0:

```
OK  sombra feliz
OK  sudo denegado
OK  servicio no se detiene
OK  consulta nft falla
OK  falta --motor-verificado
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
