# Cambios 2026-10-28 — cobertura del conjunto etiquetado y población del control (#60, #61)

Sobre el commit `719bf3a` (#59, `ventana_no_evaluada`). Solo cambian el código del analizador, los tests, los
ejemplos y la documentación. **No se ejecutó ningún ataque ni se inició la campaña A.**

No se tocaron:
- Word, modelos, umbrales, heurísticos, escenarios ni servicios;
- el motor desplegado ni el estado del laboratorio;
- `config-campana.json`.

Siguen sin cambios:
- las clasificaciones por score;
- la cobertura por episodio;
- la Tabla 8.

Ninguna de estas tres piezas depende de `fpr_control()` ni de `metricas_por_ventana()`.

## #60 — Cobertura del conjunto etiquetado

**Defecto (719bf3a).** `cobertura_etiquetadas` = con decisión / (con decisión + no evaluadas). Las etiquetadas sin
decisión ni evento (`etiquetadas_sin_registro`) se informaban, pero quedaban fuera del denominador. Con dos claves
etiquetadas y una sola decisión, la cobertura salía en 100 %.

**Corrección.** `conjunto_etiquetado()` trabaja sobre claves únicas `entity_ip|window_end` del fichero de etiquetas y
las reparte en tres categorías **excluyentes que suman el total**:

| Campo | Numerador / significado |
|---|---|
| `claves_esperadas` | Claves únicas etiquetadas. Es el **denominador total**. |
| `con_decision` | Claves con decisión registrada. Si la misma clave tiene además `ventana_no_evaluada`, prevalece la decisión (regla de conflicto de #59). **Son las únicas que entran en TP/FP/TN/FN.** |
| `no_evaluadas` | Claves sin decisión, con evento `ventana_no_evaluada`. |
| `sin_registro` | Claves sin decisión ni evento. |
| `cobertura_total` | `con_decision / claves_esperadas`. Es `None` con `cobertura_total_motivo` si no hay etiquetas: nunca 100 % por defecto. |
| `cobertura_entre_registradas` | `con_decision / (con_decision + no_evaluadas)`. Está limitada a las claves que dejaron algún registro y **no** es la cobertura total. Es el antiguo indicador, con un nombre que describe su población. |

Las métricas (`denominador`, TP/FP/TN/FN, precisión, recall y FPR) siguen calculándose solo sobre `con_decision`. Las
claves no evaluadas o sin registro no se convierten en TN, FP ni FN.

Claves de 719bf3a sustituidas:
- `etiquetadas_no_evaluadas` → `conjunto_etiquetado.no_evaluadas`;
- `etiquetadas_sin_registro` → `conjunto_etiquetado.sin_registro`;
- `cobertura_etiquetadas` → `conjunto_etiquetado.cobertura_entre_registradas`, y se añade `cobertura_total`.

## #61 — Población temporal del control normal

**Defecto (719bf3a).** `fpr_control()` seleccionaba las decisiones por `logged_at` y las no evaluadas por
`window_end`. Cerca de los límites del control eran dos poblaciones distintas. El motor corregido escribe unos 25 s
(mediana) tras `window_end`, y la `ventana_no_evaluada` unos 170 s después.

**Corrección.** Una sola población por ventana:
- Decisiones y no evaluadas por `window_end_utc` en `[desde, hasta]`, con **ambos extremos incluidos**.
- Las mismas exclusiones (`NUNCA_BLOQUEAR`).
- Claves únicas: las decisiones duplicadas se deduplican en `leer_motor`, la no evaluada duplicada se cuenta una vez y, en conflicto, prevalece la decisión.

Una decisión cuya ventana pertenece al control cuenta aunque se escribiera después de `hasta`. Su `logged_at` no se
altera, y el recuento se informa en `decisiones_escritas_tras_hasta`.

| Campo | Significado |
|---|---|
| `ventanas` = `denominador` | Decisiones evaluadas de la población (numerador y denominador de las tasas de falsas alarmas) |
| `ventanas_no_evaluadas` (+ `_por_motivo`) | Eventos `ventana_no_evaluada` de la misma población |
| `cobertura_entre_registradas` | `ventanas / (ventanas + ventanas_no_evaluadas)`. **No** garantiza que no falten registros |
| `inventario_esperado` | «no disponible»: sin inventario independiente de ventanas esperadas no se informan claves sin registro ni cobertura total del control |
| `seleccion`, `denominador_significado`, `cobertura_entre_registradas_significado` | Convención y definiciones, en el propio JSON |

Claves de 719bf3a sustituidas:
- `cobertura_evaluada` → `cobertura_entre_registradas`;
- `ventanas_no_evaluadas_criterio` → `seleccion`.

No se añadió un recuento de alertas por hora de emisión. Las emisiones reales siguen en `emisiones_observadas`, aparte
de las clasificaciones derivadas y de los denominadores por ventana.

### Cambios esperados frente a 719bf3a cuando las marcas cruzan los límites

| Registro | Antes (por `logged_at`) | Ahora (por `window_end`) |
|---|---|---|
| Decisión con `window_end` ≤ `hasta` y `logged_at` > `hasta` (ventanas finales, ~25 s) | fuera | **dentro** |
| Decisión con `window_end` < `desde` y `logged_at` ≥ `desde` (ventanas iniciales) | dentro | **fuera** |
| `ventana_no_evaluada` | por `window_end` | igual |

En un control de 30 min hay 180 ventanas por entidad. El cambio afecta a unas 2–3 ventanas por entidad y extremo,
según el retraso de escritura. Las tasas pueden variar en esa proporción. Es el comportamiento corregido, no una
regresión.

## Ejemplos (FIXTURES DE CÓDIGO, no resultados de la campaña)

El directorio `EJEMPLO-cobertura/` se regenera con `generar_ejemplo.py` y contiene `analisis-extracto.json`,
`TABLA8-caso-1_3-y-control.md` y `motor-caso-1_3-y-control.log`.

| Caso | Claves | Resultado |
|---|---|---|
| 50 % | T+40 con decisión (ALERT) · T+150 sin registro | `claves_esperadas` 2 = 1 + 0 + 1. `cobertura_total` **0,5** (en 719bf3a: 1,0). `denominador` 1: IF_0.05 TP 1, sin FN por T+150 |
| 1/3 | T+40 con decisión · T+50 `ventana_no_evaluada` · T+150 sin registro | 3 = 1 + 1 + 1. `cobertura_total` **0,333333** y `cobertura_entre_registradas` 0,5 (en 719bf3a: `cobertura_etiquetadas` 0,5) |

**Control `[T+100, T+200]` con una decisión registrada tarde:**
- La decisión del perfil 10.10.20.21 con `window_end` T+200 se escribió en T+230, 30 s después de `hasta`, con score −0,70.
  - **Cuenta** en el control.
  - Es la única falsa alarma: IF_0.05 1/8 = 0,125.
  - `decisiones_escritas_tras_hasta` = 1.
  - Su `logged_at` sigue en T+230.
- La decisión con `window_end` T+90, escrita en T+101 (dentro del rango de escritura) y con score −0,70, **no** cuenta.
- En 719bf3a habría sido al revés: T+90 dentro y T+200 fuera.
- La población queda en 8 evaluadas + 1 no evaluada explícita, con `cobertura_entre_registradas` 0,888889.

`EJEMPLO-no-evaluadas/` (#59) se regeneró con los nombres nuevos. Ahora informa, por ejemplo, «3 claves esperadas =
2 con decisión + 1 no evaluadas + 0 sin registro; cobertura total 0.666667».

## Comprobaciones

- `tests/test_herramientas.py`: **222** comprobaciones (**223** con `CF_ANALIZADOR_PREVIO` = analizador de `a6dc5ab`).
  - En `test_ventanas_no_evaluadas` se renombraron los indicadores (mismos valores).
  - Nueva `test_cobertura_etiquetado_y_control` (10). Cubre:
    - 50 %, 1/3, todas evaluadas, ninguna evaluada y etiquetado vacío (indefinida con motivo);
    - categorías que suman el total y conflicto contado con decisión;
    - TP+FP+TN+FN = claves con decisión, de modo que las no evaluadas y sin registro positivas no son FN;
    - control: decisión escrita tras `hasta` incluida, decisión con ventana fuera excluida aunque se escribiera dentro, y no evaluada escrita tras el control incluida;
    - ambos extremos incluidos para decisiones y no evaluadas (al estrecharlos salen a la vez);
    - duplicados, conflicto y entidad excluida sin doble conteo;
    - `logged_at` conservado.
- `tests/regresion_alfa.py`: 0 diferencias de detección/cobertura en 7 y 5 configuraciones frente a los goldens, `719bf3a`, `2612e3f`, `a6dc5ab` (86 excluidas de procedencia) y `0d40bdb`.
  - En los fixtures de regresión ninguna ventana cruza los límites del control (`[T, T+4200]`). Por eso `ventanas`, `denominador` y las falsas alarmas (60 ventanas) son iguales que antes.
  - El conjunto etiquetado de los fixtures es 2 = 2 + 0 + 0, con cobertura total 1,0.
  - `CLAVES_NO_EVALUADAS` incluye los nombres nuevos y los sustituidos.
- `analisis.json` completo frente a `719bf3a` sobre los fixtures: solo se renombran o añaden claves de cobertura en el control y las métricas, y cambia el texto de `denominador_significado` de las métricas. Ningún conteo cambia.
