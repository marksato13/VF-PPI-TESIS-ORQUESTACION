# Resultados de las verificaciones SIN ataques

Verifican las **herramientas** de evaluación, no el desempeño de CyberFlow. No son resultados experimentales.

## Suite de herramientas — `tests/test_herramientas.py`

**Windows (laptop):** `51 comprobaciones pasaron.`

```
OK  test_validacion
OK  test_generador_simulacion
OK  test_generador_timeout_mata_hijos
OK  test_analizador_basico
OK  test_cobertura_una_ventana_insuficiente
OK  test_score_nulo_con_heuristico
OK  test_tabla8_excluye_no_confirmadas
OK  test_ventana_previa
OK  test_emitido_vs_derivado
OK  test_integridad_gate
51 comprobaciones pasaron.
```

### La Tabla 8 excluye señales no confirmadas (`test_tabla8_excluye_no_confirmadas`, recorrido hasta el fichero)

Mismo episodio con una señal IF durante el ataque; solo cambia la evidencia de destino. Numerador IF 0,05 en la
Tabla 8 generada por `analizar.py`:

| Evidencia de destino | IF 0,05 en Tabla 8 |
|---|---|
| sin `--destinos` | 0 (no evaluable) |
| mapa vacío | 0 |
| clave de ventana ausente | 0 |
| destino incorrecto | 0 |
| **destino correcto** | **1** (evaluable, confirmada) |

### Integridad de fuentes (`test_integridad_gate`)

`verificar_integridad.py`: un episodio con motor continuo pero **PCAP ausente + historia <120 s** → **no apto**;
EVE=0 con Suricata activo y tráfico → **fallo de telemetría**; campos sin evidencia → **desconocido** (no apto).
`analizar.py` con integridad no apta → episodio **no evaluable** (aunque el motor sea continuo).

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
