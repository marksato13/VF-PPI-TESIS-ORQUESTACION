# Registro de cambios — corrección de la procedencia temporal (2026-10-28)

**Alcance:** corrección puntual del analizador, sus pruebas y documentación, sobre el commit `a6dc5ab`. Config
`2026-10-28.2` (solo textos y versión). **No se ejecutó ningún ataque ni se inició ninguna campaña.** No se tocó Word,
modelo, umbrales, heurísticos, servicios, configuración desplegada, generador, escenarios, captura, modo sombra ni
restauración, y no se copió nada a ninguna máquina.

## 1. El problema

En `a6dc5ab`, `senales()` asignaba a IF 0,05 la base `emitido_por_modelo_desplegado` cuando el registro era un ALERT
del modelo, y `clasificar()` derivaba de ella `tiempo_es_emision_real=true`. Pero son configuraciones distintas:

| | Umbral | Validación |
|---|---|---|
| Umbral operativo desplegado (el motor en vivo) | `-0.5693969936322356` | 65 633 ventanas |
| IF 0,05 recalibrado (análisis) | `-0.5694578968203694` | 65 553 ventanas sin Kali |

Que un ALERT real coincida con la clasificación recalibrada no demuestra que la configuración recalibrada emitiera.
Además, un ALERT **sin** `detector_name` se trataba como emisión del modelo.

## 2. Qué es cada cosa (definiciones que ahora usan código y documentos)

- **Señal realmente emitida:** lo que el motor escribió en `motor_decision.log` como `ALERT` (o como señal heurística
  registrada), con emisor y umbral **registrados**. Va en `emisiones_observadas`, **no** en la Tabla 8.
- **Clasificación comparativa derivada:** cada una de las 7 configuraciones (IF 0,05 · IF 0,03 · IF 0,01 · HEUR ·
  HIB 0,05 · HIB 0,03 · HIB 0,01), calculada sobre los registros. Es análisis de componentes y umbrales, no una
  emisión, tampoco IF 0,05.
- **Tiempos:**
  - **Latencia real de emisión:** solo a partir de una alerta con `componente_emisor = IF_desplegado`, umbral
    registrado igual a `desplegado_referencia` (`configuracion_emisora.estado = confirmada`), durante el ataque y con
    atribución confirmada: `logged_at − inicio del generador`
    (`episodios.<id>.emisiones_observadas.primera_alerta_IF_desplegado_confirmada_durante`).
  - **Disponibilidad del registro:** en las configuraciones derivadas, `logged_at` indica cuándo quedó registrada la
    evidencia usada (`tiempo_significado`). No es una latencia de emisión de esa configuración.
  - `window_end_utc` es el cierre de la ventana y nunca es hora de emisión.

## 3. Cambios en `scripts/analizar.py`

| Antes (`a6dc5ab`) | Ahora (`2026-10-28.2`) |
|---|---|
| `base` IF_0.05 = `emitido_por_modelo_desplegado` si había ALERT | siempre `derivado(umbral_recalibrado_0.05; distinto del desplegado)` |
| `base` HEUR = `emitido_ALERT(auth_heredada)` / `registrada_en_vivo` / `-` | `derivado(componente_heuristico_registrado)`; lo observado pasa a `evidencia_registrada` |
| `base` HIB = `derivado(feed)` | `derivado(IF_α OR HEUR)` |
| `tiempo_es_emision_real` (bool) | **retirado**; `tiempo_significado` = disponibilidad del registro |
| `senales()` devolvía `modelo_emitio_alert`, `auth_emitio_alert` | retirados; `evidencia_registrada` = {decisión, detector, heurístico, ALERT auth heredada} |
| — | `emisiones_observadas` (global) y `episodios.<id>.emisiones_observadas` (resumen) |
| `clasificacion_por`: «logged_at (emisión real)» | «logged_at (instante en que quedó registrada la evidencia usada)», más el bloque `tiempos` |
| `TABLA8.md` | igual, más una sección **aparte** «Emisiones observadas» (no es una columna) |

**Campos de cada emisión observada:** `registro_id` (`decision_id`/`id` del registro si existe; si no, `motor:<línea>`),
`tipo` (`alerta_emitida` / `senal_heuristica_registrada(sin_ALERT)`), `componente_emisor` (`IF_desplegado`,
`heuristico_auth_heredado`, `heuristico:<nombre>` o `desconocido` + motivo), `decision_emitida`,
`accion_heuristica_registrada`, `logged_at_utc` y `window_end_utc`, `entity_ip`, `modelo_registrado`,
`score_registrado`, `configuracion_emisora` (`umbral_registrado`, `estado` confirmada/identificada/desconocida,
`motivo`, `coherencia_score_umbral`), relación con el episodio (`episodio_id`, `relacion_temporal`, `atribucion`,
`atribucion_confirmada`, tiempos) y `respaldo` (archivo, sha256 del log, línea).

**Reglas:** el emisor sale del `detector_name` registrado comparado con `modelo.detector` de la config, nunca del
score. ALERT sin `detector_name`, con un detector distinto, o con una config sin `modelo.detector` → `desconocido`.
Umbral ausente o no numérico → `desconocido`; umbral registrado distinto del desplegado → `desconocida`, informando el
valor **registrado**. Nunca se rellena con el valor esperado. Un score que cruza un umbral sin ALERT ni heurístico
registrado **no** aparece como emisión.

**Sin cambios:** umbrales, comparación estricta, señales IF/HEUR/HIB por ventana, Tabla 8, categorías, cobertura,
evidencia de destino, integridad, solapamiento, control normal, denominadores, falsas alarmas, métricas por ventana,
combinación IF OR heurísticos.

## 4. Pruebas (comprobaciones del código con fixtures/registros sintéticos, no resultados experimentales)

`python tests/test_herramientas.py` → **172 comprobaciones pasaron** (130 → 172) con `CF_ANALIZADOR_PREVIO` =
`scripts/analizar.py` de `a6dc5ab` (`git show a6dc5ab:<ruta>`); sin esa variable se omite la comparación directa y
salen **171** (el golden de 7 configuraciones se compara igual).

- **Expectativas corregidas** (aceptaban IF 0,05 recalibrado como emitido): `test_analizador_basico`,
  `test_emitido_vs_derivado`, `test_siete_configuraciones`.
- **Nuevas:** `test_procedencia_emisiones` (5 casos: ALERT real que cruza los tres umbrales; score entre el desplegado
  y el recalibrado; positivo alternativo sin emisión; heurístico registrado en vivo; identificación insuficiente en 4
  variantes) y `test_conteos_cobertura_7_sin_cambios`.
- **Regresión:** `tests/regresion_alfa.py` compara detección y cobertura con los analizadores de `0d40bdb`
  (5 configuraciones) y `a6dc5ab` (7 configuraciones; nuevo `tests/golden-7config-fixtures.json`). Excluye **solo**
  `base`, `tiempo_es_emision_real`, `tiempo_significado` y `evidencia_registrada`, y con `--comparar` las lista aparte.
  Resultado: **0 diferencias** de detección/cobertura en ambos casos; 86 diferencias excluidas frente a `a6dc5ab`, todas
  de esas claves.
- **Fixtures:** el campo `threshold` registrado pasa a ser el desplegado (como lo escribe el motor real; antes era el
  recalibrado) y la config del fixture declara `modelo.detector`. Ninguno de los dos interviene en la detección; las
  comparaciones con los goldens lo confirman.

## 5. Archivos

| Archivo | Cambio |
|---|---|
| `scripts/analizar.py` | etiquetas derivadas, `tiempo_significado`, `evidencia_registrada`, `emisor_de`, `configuracion_emisora`, `emisiones_observadas`, bloque `tiempos`, sección aparte en `TABLA8.md` |
| `config-campana.json` | versión `2026-10-28.2`; textos de emitidas/derivadas, `latencia_real`, `cambio_de_campos_2026_10_28_2` (umbrales sin cambios) |
| `tests/test_herramientas.py` · `tests/fixtures.py` | expectativas corregidas, 2 pruebas nuevas, `threshold` desplegado y `modelo.detector` en el fixture |
| `tests/regresion_alfa.py` · `tests/golden-7config-fixtures.json` | proyección de detección/cobertura con exclusión explícita de las claves de procedencia; golden nuevo de `a6dc5ab` |
| `PLAN-CAMPANA.md` · `README.md` · `MATRIZ-OBSERVACIONES.md` · `RESULTADOS-VERIFICACION.md` · `CAMBIOS-2026-10-28-alfa001.md` | definiciones, filas 51–55, resultados, nota de corrección |
| `MANIFIESTO-CAMPANA.json` | regenerado sobre los bytes publicados |

**No se tocó:** generador (`generar_campana.py`), escenarios, esquema, archivador, captura, sombra/restauración,
verificador de integridad, endpoint, ni nada fuera de esta carpeta. No se copió nada a ninguna máquina.
