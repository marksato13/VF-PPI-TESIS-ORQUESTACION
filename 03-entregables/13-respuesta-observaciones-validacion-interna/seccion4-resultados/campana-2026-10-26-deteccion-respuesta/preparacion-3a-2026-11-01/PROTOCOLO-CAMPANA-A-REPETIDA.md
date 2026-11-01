# Protocolo congelado — campaña A repetida (paso 3B)

Congelado el 2026-11-01 en la preparación 3A, **antes** de ejecutar ningún episodio, control normal ni campaña B.
Lo que aquí se fija no se ajusta a la vista de los resultados. Si durante el 3B algo obliga a apartarse del
protocolo, se para, se documenta la desviación y se decide antes de seguir. No se corrige después en el análisis.

## 1. Qué no cambia

| Elemento | Valor congelado | Referencia |
|---|---|---|
| Motor | candidato `24f8a80` (rama `candidato/motor-rendimiento-20261031`), en **sombra** (sin `--enforce`) | `motor_decision.py` 6c274d9e…, `motor_incremental.py` a403307a… |
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

- **Motor:** en sombra. El agente de enforcement de srv-dmz sigue desactivado, sin tabla `inet cyberflow`.
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

## 4. Control normal

- Intervalo de **≥ 30 min** sin episodios, con los seis perfiles a factor 1,0, declarado antes de empezar (desde, hasta), igual que en la primera A.
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
| Inventario | Ventanas decididas por `replay_motor.py` con el **mismo motor** sobre el PCAP y el EVE **archivados** de la campaña, con `window_end` en [inicio del archivo + 230 s, cierre − 120 s]. |
| Alcance del inventario | Detecta ventanas que el motor en vivo no decidió. No detecta pérdidas del SPAN, de tcpdump ni de Suricata, porque la repetición usa los mismos datos (sección 7). Coincidir con la repetición no prueba que una fuente degradada no tuviera efecto. |
| Disponibilidad | `registro_escrito_en` del ciclo que decidió la ventana (`ciclos.jsonl`, enlazado por `inicio_ciclo`). Si no se puede enlazar, `logged_at`, y se declara. |
| A tiempo / tardía | Disponibilidad − `window_end` ≤ 60 s / > 60 s. Una ventana tardía **está decidida**: cuenta para la cobertura, no para la puntualidad. |
| Estados de ventana | `decidida_a_tiempo` · `decidida_tardia` · `no_evaluada` (evento explícito) · `ausente` (esperada sin registro en vivo) · `solo_en_vivo` · `evidencia_insuficiente` (fuera del inventario o sin él) |
| Ciclo sin decisiones / hueco > 20 s entre escrituras | Se informa. **No prueba pérdida**: la pérdida solo se establece contra el inventario (`ausente`). |
| Falta de datos | No es FN, ni TN, ni latencia 0. |

## 6. Detección durante el ataque

**Ventanas del episodio.** Son las de la Kali con `window_end` en (inicio, fin + 60), es decir, aquellas cuyo intervalo
(w − 60, w] se solapa con [inicio, fin]. Se toman del inventario.

**Observación completa** (define la **población principal**, independientemente del resultado). Se cumple cuando:

- todas las ventanas esperadas están decididas en vivo;
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
(`reanalisis-paso2/`). En cada uno de los tres episodios hay:

- 15 ventanas esperadas, todas decididas a tiempo;
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
- **Durante el 3B:** no se toca `estado.json`. Se copia con hash al empezar y al terminar.
- **Estado inicial de la campaña B:**
  - se define en la preparación del B, no ahora;
  - plan: copiar `feed.json`, `feed.sig` y `estado.json` con sha256;
  - si el B exige partir de contador 0, restablecer `estado.json` de forma documentada (copia previa, comando exacto y hash después), con autorización explícita;
  - nada se restablece en silencio.

## 9. Ejecución del análisis del 3B

```
python3 scripts/analizar_3b.py --marcas marcas.jsonl --motor motor_decision.log \
  --config preparacion-3a-2026-11-01/config-campana-3b.json --ciclos ciclos.jsonl \
  --inventario replay_motor_decision.log --inventario-rango "<inicio archivo>,<cierre>" \
  --destinos destinos-3b.csv --integridad integridad.json --calidad-fuentes calidad-fuentes.json \
  --control "<desde>,<hasta>" --etiqueta "campaña A repetida (3B)" --salida analisis-3b
```

**Antes de analizar** se verifican los hashes de:

- `analizar_3b.py`, `analizar.py`, `poblacion.py`, `calidad_fuentes.py` y `extraer_evidencia_destino.py`;
- `config-campana-3b.json`.

Los valores están en `REFERENCIAS-Y-HASHES.md`. Un hash distinto detiene el análisis.
