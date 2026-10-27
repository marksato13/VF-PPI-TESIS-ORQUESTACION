# Resultados de las verificaciones SIN ataques

Verifican las **herramientas** de evaluación, no el desempeño de CyberFlow. No son resultados experimentales.

## Suite de herramientas — `tests/test_herramientas.py`

**Windows (laptop):** `33 comprobaciones pasaron.`

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador
33 comprobaciones pasaron.
```

Cubre: validación de config (válida/ inválida, `timeout_s` de texto, marcador `<ZONA_LAB>`, destino fuera de la
lista blanca, `brute_puerto` nulo, `contexto_antes<120`); comandos de los 5 escenarios sin marcadores; simulación por
defecto (no crea salidas de procesos) y orden reproducible por semilla; **timeout que mata al grupo de procesos
(hijo incluido)** y registra inicio/fin por separado; clasificación temporal por `logged_at` (durante/posterior/
sin_deteccion/no_evaluable); separación emitido/derivado (HEUR LIMIT en DNS no se emite como ALERT; IF sí);
IF 0,05 vs 0,03 sobre un score intermedio; detección de duplicados; métricas por ventana solo con etiquetas
(TP=1/FP=0 con etiquetas conocidas); control FPR con denominador explícito.

## Ruta POSIX en el entorno real — sonda en el sensor (Linux)

El árbol de procesos del generador se termina con `killpg` en POSIX. Verificado en el Sensor1:

```
estado_padre_terminado: True
hijo_sobrevivio(testigo): False
RESULTADO: OK killpg mato el grupo (hijo incluido)
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
