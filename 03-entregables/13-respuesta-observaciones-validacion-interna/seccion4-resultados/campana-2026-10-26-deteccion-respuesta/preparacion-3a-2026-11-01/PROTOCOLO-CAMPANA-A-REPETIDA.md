# Protocolo congelado — campaña A repetida (paso 3B)

Congelado el 2026-11-01 en la preparación 3A, **antes** de ejecutar ningún episodio, control normal ni campaña B.
Lo que aquí se fija no se ajusta a la vista de los resultados. Si durante el 3B algo obliga a apartarse del
protocolo, se para, se documenta la desviación y se decide antes de seguir. No se corrige después en el análisis.

## 1. Qué no cambia

| Elemento | Valor congelado | Referencia |
|---|---|---|
| Motor | incremental, commit `24f8a80e376d89b78454fd16854d2239a1b7d278` (rama `candidato/motor-rendimiento-20261031`), en **sombra** (sin `--enforce`) | `motor_decision.py` 6c274d9e… (blob 068c025d), `motor_incremental.py` a403307a… (blob 1197907c) |
| Modelo | `if_limpio_2026_10`, escalador y 28 características | modelo df547da0…, esquema e032a1a2…, manifiesto b3ad6805… |
| Historia y paso | 230 s y 10 s, procesamiento incremental | argv del paso 2, idéntico (estado inicial 3A) |
| Umbral desplegado | −0.5693969936322356 | `config-campana-3b.json` → `umbrales.desplegado_referencia` |
| Umbrales de análisis | 0,05 = −0.5694578968203694 · 0,03 = −0.5898535710336618 · 0,01 = −0.6223889502095352 | verificados por igualdad exacta contra `4.1-modelos/calibracion-alfa-2026-10-24` (sha256 LF 26bfc6e6…) |
| Heurísticos | versión de código 2026-10-06.2 | heuristicos 10deb05d… |
| Extractores | sin cambios | 7130edae… / 5adbfbf4… |
| Escenarios | 5 escenarios × 5 repeticiones, semilla 20261026 | `escenarios/escenarios.json` 67798012… |
| Generador | `generar_campana.py` c586d813…, `esquema_campana.py` e762e604… | mismos hashes en la Kali y en el repositorio |
| Configuraciones | IF_0.05 · IF_0.03 · IF_0.01 · HEUR · HIB_0.05 · HIB_0.03 · HIB_0.01 | derivadas de los registros; no son emisiones |
| Publicador | `publicar_feed.py` f7bc4c7d…, `escalada.py` 7d80ab4a… | no se cambia su lista de excepciones |

**Procedencia del código instalado** (verificada el 2026-11-01 a las 06:23Z con el guion s11: `git hash-object` de cada
fichero desplegado en el Sensor1 comparado con el blob del commit en el clon del repositorio del producto; detalle en
`config-campana-3b.json` → `codigo`; blobs desplegados en `evidencia/salidas/out_s11_sensor_codigo.txt` y comparación
con los commits en `evidencia/salidas/out_s11b_comparacion_local.txt`. El Sensor1 no es un clon git: en la salida s11
la columna `blob_24f8a80` sale vacía y su «DISTINTO» no es una comparación; la comparación válida es la s11b):

| Fichero | Blob desplegado | Procedencia |
|---|---|---|
| `motor_decision.py`, `motor_incremental.py`, `heuristicos.py`, `feed.py`, `extract_multilayer_v2.py`, `extract_multilayer_v3.py` | 068c025d, 1197907c, ec0fe9e8, fa30b818, ec46849d, 0739e4cd | iguales al commit `24f8a80` |
| `configs/features/multilayer-v2.json` | 9560ce9e | contenido de `24f8a80`; el fichero desplegado tiene finales CRLF y, normalizado, es idéntico |
| `publicar_feed.py` | bf2b73f4 | **excepción as-deployed:** viene de `f57ca00` (instantánea del sensor del 29-oct, igual al tag `validacion-interna-2026-10-15` 6d92ff3); en `24f8a80` el blob es f73db5af |
| `escalada.py` | 7bd55de8 | **excepción as-deployed:** misma procedencia que el publicador; en `24f8a80` el blob es 8f260bd0 |
| srv-dmz `agente_enforce.py` | b769b01c | tag 6d92ff3; timer y servicio *inactive*, timer *disabled* |

Las dos excepciones afectan solo a la respuesta (propuestas del feed), no a la detección. Se conservan tal cual: no se
despliega nada nuevo para el 3B.

**Lo histórico.** La configuración heredada de la primera campaña A (motor por lotes, `precondicion_critica` con el
enforcement activo) se conserva en `config-campana-3b.json` bajo `codigo_historico_primera_A` y
`campanas.historico_primera_A`, marcada como HISTÓRICA. No describe el 3B.

La primera campaña A (`ejecucion-2026-10-29/`) no se modifica. Su re-análisis con el analizador nuevo está en
`reanalisis-campana-A-2026-10-29/` y está marcado como re-análisis. La Tabla 8 histórica sigue siendo la publicada.

## 2. Orden y duración

El plan efectivo sin tráfico (`plan-sin-trafico/`) reproduce el orden de la primera campaña A: 25 episodios con la
misma semilla, calentamiento de 60 s, 120 s de contexto antes de cada episodio y 90 s de observación después. Duración de
los comandos en la primera A:

| Escenario | Duración del comando |
|---|---|
| Inundación HTTP, DNS inusual, fuerza bruta HTTP | ~90 s |
| Escaneo sostenido | ~66 s |
| Escaneo breve | ~18 s |

**No se prolonga el escaneo breve.** Con unos 18 s de actividad y una disponibilidad típica de 20 a 40 s tras
`window_end`, es esperable que sus detecciones sean **solo posteriores**. Esto se declara aquí, antes de ejecutar. No
es un defecto que se vaya a corregir después.

## 3. Entorno durante el 3B

- **Estado operativo** (igual que `config-campana-3b.json` → `estado_operativo_3b`):
  - **durante:** sombra. El publicador sigue escribiendo propuestas cada 10 s y nadie las aplica;
  - **antes de empezar se verifica:**
    - en el Sensor1, `ppi-motor` activo, con `NRestarts` anotado y sin `--enforce` ni en `/proc/<pid>/cmdline` ni en la unidad;
    - los sha256 de `codigo.ficheros_sensor` y del modelo, iguales a la config;
    - en srv-dmz, `ppi-enforce-agent.timer` y `.service` *inactive*, el timer *disabled* y `sudo nft list tables` sin `inet cyberflow`;
    - copia con sha256 de `feed.json`, `feed.sig` y `estado.json`;
  - **escalada:** se conserva como esté (la Kali llega con `bloqueos: 3` de propuestas en sombra). **No** se restablece ni se edita (sección 8);
  - **al terminar:** se **permanece en sombra**. No se ejecuta `restaurar_enforcement.sh` ni se arranca el agente. Se repiten las verificaciones anteriores y la copia con hash;
  - **activar la respuesta** (estado inicial de la escalada, restauración del enforcement y su verificación) pertenece a la **preparación de la campaña B**, con autorización explícita. No forma parte del 3B.
- **Clientes legítimos:**
  - los seis perfiles con factor horario 1,0, mediante el envoltorio `clientes_factor1.py` (69d79937…), que no modifica `clientes_lab.py` (ae5134a7…);
  - el mecanismo se comprobó en el 3A sin arrancarlo.
  - Se arranca y se para como en el paso 2, y se restaura la curva horaria al terminar.
- **`ppi-brute-lab`:**
  - activo en srv-dmz desde el 3A (`systemctl start`), **no habilitado** al arranque;
  - **riesgo:** si srv-dmz se reinicia, el endpoint queda parado y la fuerza bruta HTTP recibiría 000/conexión rechazada;
  - **comprobación obligatoria** antes del primer episodio de fuerza bruta: `systemctl is-active ppi-brute-lab` y una petición sin credencial que dé 401;
  - **reversión** al terminar el 3B: `sudo systemctl stop ppi-brute-lab`.
- **DNS `lab-ppi`, HTTP y HTTPS:** se comprueban desde el bastión antes de empezar (`dig @10.10.10.20 x.lab-ppi` → 10.10.30.10; códigos 200).
- **SSH de administración bastión → Kali:**
  - genera paquetes de la entidad Kali (10.10.20.30 → 10.10.10.30);
  - durante la campaña **no** se abre SSH a la Kali salvo para lanzar el generador o pararlo por una condición de parada;
  - cualquier acceso queda registrado con su hora UTC;
  - el analizador **no** atribuye esas ventanas al ataque: exige paquetes hacia el destino del episodio dentro de [inicio, fin].
- **Relojes:** no se cambian ni se programa el inicio. Se registran antes y después, como en la primera A.

## 3 bis. Extremos del archivo PCAP/EVE y cierre

**Marcas** (las tres se anotan en el informe del 3B, con su fuente):

| Marca | Fuente |
|---|---|
| `inicio_archivo` | inicio (nombre `live-YYYYmmddHHMMSS.pcap`) del **primer** PCAP con línea `OK` en `archivar.log` |
| `fin_ultimo` | evento `fin` del último episodio en `marcas.jsonl` (reloj de pared, UTC) |
| `cierre_archivo` | inicio del **último** PCAP con línea `OK` en `archivar.log` + 15 s |

**Cálculo del cierre mínimo.** La última ventana requerida de un episodio tiene `window_end` < fin + 60 (sección 6).
El inventario solo es utilizable hasta `cierre_archivo − 120` (la repetición no ve los últimos PCAP cerrados). Por
tanto el archivo debe conservarse hasta:

```
cierre_archivo ≥ fin_ultimo + 60 + 120 = fin_ultimo + 180 s
```

**Es un mínimo, no una duración fija.** El archivo se mantiene **después** de esos 180 s y solo se cierra cuando se ha
verificado todo lo siguiente:

1. `archivar.log` tiene un PCAP con `OK` cuyo inicio + 15 ≥ `fin_ultimo + 180`;
2. `archivar.log` no tiene ninguna línea `FALLO` y su `FIN OK` dice `vistos = archivados`;
3. el EVE archivado contiene eventos con marca posterior a `fin_ultimo + 180`;
4. el `motor_decision.log` en vivo tiene decisiones con `window_end` ≥ `fin_ultimo + 60` (las ventanas del último episodio ya se han escrito);
5. la repetición offline (`replay_motor.py`) termina con rc = 0 y su rango cubre `window_end` hasta `fin_ultimo + 60` como mínimo.

Si alguna falla, el archivo sigue abierto y se repite la comprobación. Si no se puede cumplir, el último episodio
queda fuera de la población principal por inventario incompleto (el analizador lo marca como «el inventario no cubre
X/N ventanas requeridas»). No se recorta nada a mano.

**Entre episodios no hay cierre.** Los 90 s de observación tras cada episodio y los 120 s de contexto antes del
siguiente (sección 2) son parte de la campaña y el archivo sigue grabando. El cierre de 180 s se aplica **solo** tras el
último episodio (o tras el control normal, si va después: entonces `fin_ultimo` es el `hasta` del control y se usa el mismo mínimo de 180 s, que es conservador).

**Inicio.** El inventario empieza en `inicio_archivo + 230` (historia del motor). Por eso el control normal
(sección 4) y el primer episodio deben empezar después de ese instante.

**Comprobación con el paso 2** (evidencia de `paso2-validacion-en-vivo-2026-11-01/evidencia/`):

| Marca | Valor |
|---|---|
| `inicio_archivo` | 2026-11-01T02:44:54Z (`live-20261101024454.pcap`, primer `OK`) |
| `inicio_archivo + 230` | 02:48:44Z; el control empezó a las 03:23:50Z → cumple |
| `fin_ultimo` | 2026-11-01T04:04:22.04Z (`inundacion_http-rT3`) |
| `fin_ultimo + 180` | 04:07:22Z |
| `cierre_archivo` | 04:18:16 + 15 s = 04:18:31Z → margen de 669 s |
| `archivar.log` | sin `FALLO`; `FIN OK: vistos=374 archivados=374` |

## 4. Control normal

- Intervalo de **≥ 30 min** sin episodios, con los seis perfiles a factor 1,0, declarado antes de empezar (desde, hasta), igual que en la primera A.
- **Requisito temporal:** `desde ≥ inicio_archivo + 230 s` y `hasta ≤ cierre_archivo − 120 s` (sección 3 bis), para que todo el control quede dentro del inventario.
- **Tramo cubierto:** [desde, hasta] ∩ rango del inventario. Su población son las ventanas **requeridas** (sección 5); las cotas se calculan sobre ellas. Si una parte del control queda fuera del inventario, se presenta **aparte** como tramo sin inventario, con cobertura «no determinable», y el control se declara **parcialmente cubierto**. Las dos partes no se suman.
- **Población:**
  - todas las entidades con ventanas en el intervalo (selección por `window_end_utc` en [desde, hasta], ambos extremos incluidos);
  - el DNS 10.10.10.20 **está dentro**: es una excepción de **respuesta**, no de población;
  - `exclusiones_poblacion` está vacía; añadir una exige justificación escrita **antes** de analizar.
- **Medidas:**
  - la tasa por configuración se publica con su cobertura por inventario;
  - las cotas mínima y máxima suponen que las ventanas sin decisión son todas negativas o todas positivas;
  - se publica un desglose por entidad.
- **Umbral de cobertura:** no se adopta ninguno automático (por ejemplo, 90 %). Si la cobertura no es total, se publica tal cual con sus cotas.

## 5. Cobertura y puntualidad

| Término | Definición |
|---|---|
| Inventario | Lo que registra `replay_motor.py` con el **mismo motor** sobre el PCAP y el EVE **archivados** de la campaña, con `window_end` en [inicio_archivo + 230 s, cierre_archivo − 120 s] (sección 3 bis). |
| Ventanas requeridas | Toda clave `entity_ip\|window_end` del rango que la repetición registró **con decisión o como `ventana_no_evaluada`**. Una ventana no evaluada en la referencia **sigue siendo requerida**: no se descarta del denominador. |
| Estado en la referencia | `decision` · `no_evaluada` · `sin_registro` (la repetición no la registró; solo puede ocurrir en las ventanas de episodio de la sección 6) · `sin_inventario`. Se informa por ventana, junto al estado en vivo. |
| Estado en vivo | decidida (a tiempo o tardía) · `no_evaluada` (evento explícito en vivo) · `ausente` (requerida sin ningún registro en vivo). Son tres situaciones distintas y se cuentan por separado. |
| Cobertura total | decididas en vivo / requeridas. Las `solo_en_vivo` se informan **fuera** del denominador. |
| Alcance del inventario | Detecta ventanas que el motor en vivo no decidió. No detecta pérdidas del SPAN, de tcpdump ni de Suricata, porque la repetición usa los mismos datos (sección 7). Coincidir con la repetición no prueba que una fuente degradada no tuviera efecto. |
| Disponibilidad | `registro_escrito_en` del ciclo que decidió la ventana (`ciclos.jsonl`, enlazado por `inicio_ciclo`). Si no se puede enlazar, `logged_at`, y se declara. |
| A tiempo / tardía | Disponibilidad − `window_end` ≤ 60 s / > 60 s. Una ventana tardía **está decidida**: cuenta para la cobertura, no para la puntualidad. |
| Estados de ventana | `decidida_a_tiempo` · `decidida_tardia` · `no_evaluada` (evento explícito en vivo) · `ausente` (requerida sin registro en vivo) · `solo_en_vivo` · `evidencia_insuficiente` (fuera del inventario o sin él) |
| Ciclo sin decisiones / hueco > 20 s entre escrituras | Se informa. **No prueba pérdida**: la pérdida solo se establece contra el inventario (`ausente`). |
| Falta de datos | No es FN, ni TN, ni latencia 0. |

## 6. Detección durante el ataque

**Ventanas del episodio.** Son **todas** las anclas de la rejilla de 10 s de la Kali con `window_end` en
(inicio, fin + 60), abierto en ambos extremos: aquellas cuyo intervalo (w − 60, w] se solapa con [inicio, fin]. No
dependen de lo que la repetición haya decidido; todas son requeridas. No hay exclusiones definidas.

**Cobertura del inventario.** El rango del inventario debe contener **todas** esas anclas. Si no las contiene (por
ejemplo, porque el archivo se cerró antes de `fin + 180`), el episodio no tiene observación completa y el motivo dice
cuántas ventanas quedan fuera. Antes de la corrección 3A-1 se aceptaba un inventario truncado si el rango llegaba
hasta `hasta + 60`, aunque no cubriera las ventanas.

**Observación completa** (define la **población principal**, independientemente del resultado). Se cumple cuando:

- el rango del inventario contiene todas las ventanas requeridas del episodio;
- todas las ventanas requeridas están decididas en vivo (una no evaluada o ausente lo impide, también si la referencia tampoco la evaluó);
- la fuente es `completa` (sección 7);
- la integridad es apta (`verificar_integridad.py`);
- cada ventana decidida tiene una fila de destino (`extraer_evidencia_destino.py --formato 3b`, que deja también constancia de las ventanas sin paquetes).

**Señal atribuible.** La configuración da señal en la ventana **y** la evidencia de destino muestra paquetes del origen
hacia el destino del episodio dentro de la ventana **y** dentro de [inicio, fin] (`paquetes_en_intervalo_ataque` > 0).
Una señal hacia otro destino (por ejemplo, el SSH de administración) o sin actividad del ataque en el intervalo se
informa como no atribuible.

**Categorías** por configuración y episodio:

| Categoría | Condición |
|---|---|
| `oportuna` | Hay una señal atribuible con disponibilidad ≤ fin. |
| `solo_posterior` | Hay señal atribuible, pero toda disponible después del fin. |
| `ausencia_con_observacion_suficiente` | Ninguna señal atribuible y observación completa. |
| `no_evaluable` | Ninguna señal atribuible y observación incompleta. |

Las detecciones de episodios **fuera** de la población principal se siguen publicando, con el prefijo `fuera:`. Una
fuente degradada no anula una señal observada; solo impide concluir una ausencia.

**Emisiones reales.** Son las decisiones `ALERT` y los heurísticos registrados en vivo. Se cuentan **aparte** de las
7 configuraciones: número de emisiones oportunas por episodio y latencia de la primera (disponibilidad − inicio).
Las configuraciones derivadas **no** son emisiones. Su tiempo es la disponibilidad del registro usado.

**Comprobación con el paso 2.** Se reanalizó la evidencia del paso 2 con este analizador
(`reanalisis-paso2/analisis/` con la versión de e0ba9e0; `reanalisis-paso2/analisis-corregido/` con la corregida). En
cada uno de los tres episodios hay:

- 15 ventanas requeridas, todas dentro del inventario y decididas a tiempo;
- 10 ventanas con `window_end` en [inicio, fin + 10];
- de ellas, 6 disponibles antes del fin;
- primera emisión oportuna a los 28,66 / 34,45 / 37,21 s.

Coincide con el informe del paso 2.

## 7. Calidad de fuentes

`calidad_fuentes.py` separa cuatro fuentes por episodio, sobre [inicio − 60, fin + 60]:

| Fuente | Medida | Efecto |
|---|---|---|
| Archivo PCAP | Continuidad de los ficheros de 15 s en `archivar.log` (sin fallos, sin huecos > 17 s, cubre ambos extremos) | Si falla, la fuente es `insuficiente`. |
| Socket de tcpdump | No medible por intervalo: tcpdump solo informa sus descartes al terminar | Incertidumbre residual declarada; no clasifica. |
| Suricata | Delta de `capture.kernel_drops` en `stats.log`, entre la última muestra ≤ desde y la primera ≥ hasta (cota conservadora) | Sin muestras, `insuficiente`; > 0, **`degradada`**. |
| Interfaz ens37 | `rx_dropped` | Se informa sin clasificar: su significado en este laboratorio no está determinado. |

**Criterios:**

- solo `completa` entra en la población principal;
- `degradada` e `insuficiente` quedan fuera, con sus detecciones visibles;
- **no** se afirma que una degradación no tuvo efecto porque el motor en vivo coincida con la repetición offline.

## 7 bis. Excepciones de respuesta y población

`poblacion.py` separa dos listas que antes estaban mezcladas en `NUNCA_BLOQUEAR`:

- **`excepciones_respuesta`:** política de respuesta. No sacan a la entidad de la población ni borran sus señales.
- **`exclusiones_poblacion`:** quedan fuera del denominador y cada una exige justificación.

**Validación:**

- las IP deben ser direcciones o redes CIDR estrictas, sin anotaciones;
- una entrada mal formada aborta el análisis;
- declarar los dos formatos a la vez también aborta.

**Lista del publicador.** Su propia lista en el sensor **no** se cambia.

## 8. Feed y escalada (respuesta, no detección)

- El motor **no** lee `estado.json`: solo lo leen y escriben `publicar_feed.py` (cada 10 s) y `escalada.py`. El estado de escalada **no afecta a la detección** del 3B, solo a las acciones que el publicador **propone**.
- `bloqueos: 3` de la Kali en `estado.json` significa:
  - que el publicador, en sombra, contó al menos tres eventos BLOCK separados (> 120 s) dentro de la ventana de reincidencia (el contador se acota en 3);
  - son **propuestas en sombra**, no bloqueos aplicados (agente desactivado, sin tabla nft);
  - el nivel 3 propone 3600 s y la marca de revisión humana.
- **Decaimiento** (verificado en `escalada.py`):
  - el contador se reinicia si `ahora − ultimo_visto` > 24 h;
  - `ultimo_visto` se actualiza con **cualquier** propuesta (también LIMIT);
  - por tanto, esperar 24 h no lo reinicia si la Kali vuelve a aparecer, y el propio 3B lo renueva;
  - no se impone ninguna espera de 24 h.
- **Durante el 3B:** sombra; no se toca `estado.json`. Se copia con hash al empezar y al terminar. Al terminar se sigue en sombra (sección 3, estado operativo).
- **Estado inicial de la campaña B:**
  - se define en la preparación del B, no ahora;
  - plan: copiar `feed.json`, `feed.sig` y `estado.json` con sha256;
  - si el B exige partir de contador 0, restablecer `estado.json` de forma documentada (copia previa, comando exacto y hash después), con autorización explícita;
  - nada se restablece en silencio.

## 9. Ejecución del análisis del 3B

```
python3 scripts/analizar_3b.py --marcas marcas.jsonl --motor motor_decision.log \
  --config preparacion-3a-2026-11-01/config-campana-3b.json --ciclos ciclos.jsonl \
  --inventario replay_motor_decision.log --inventario-rango "<inicio_archivo>,<cierre_archivo>" \
  --destinos destinos-3b.csv --integridad integridad.json --calidad-fuentes calidad-fuentes.json \
  --control "<desde>,<hasta>" --etiqueta "campaña A repetida (3B)" --salida analisis-3b
```

**Antes de analizar** se verifican los hashes de:

- `analizar_3b.py`, `analizar.py`, `poblacion.py`, `calidad_fuentes.py` y `extraer_evidencia_destino.py`;
- `config-campana-3b.json`.

Los valores están en `REFERENCIAS-Y-HASHES.md`. Un hash distinto detiene el análisis.
