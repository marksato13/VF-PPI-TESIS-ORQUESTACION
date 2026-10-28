# Registro de cambios — umbral registrado ausente (2026-10-28)

**Alcance:** corrección puntual del lector de registros del motor (`scripts/analizar.py`), sus pruebas y la
documentación, sobre el commit `a69224c`. `config-campana.json` no cambia (sigue en `2026-10-28.2`). **No se ejecutó
ningún ataque ni campaña** y no se desplegó nada en las máquinas. No se tocó Word, modelos, umbrales, heurísticos,
escenarios, servicios, captura, modo sombra, restauración ni configuración desplegada.

## 1. El problema

`leer_motor()` exigía `threshold` en `REQ_MOTOR`. Un registro de decisión con `"threshold": null` se conservaba como
emisión con configuración desconocida, pero uno **sin la clave** se descartaba entero (`faltan claves ['threshold']`).
Se perdía así una alerta registrada que debía conservarse como evidencia incompleta.

## 2. La corrección

- `REQ_MOTOR` = `logged_at`, `entity_ip`, `window_end_utc`, `decision`, `packet_count_10s`: lo imprescindible para
  leer y ubicar el registro en el tiempo. Si falta cualquiera de ellos, el registro **se sigue descartando** con
  incidencia (comprobado para los cinco).
- Sin la clave `threshold`, el registro se conserva y se anota:
  - en `calidad_datos.incidencias_motor`:
    `motor:<línea> (<archivo>): falta la clave 'threshold'; registro conservado, umbral registrado desconocido`;
  - en la emisión: `incidencias_registro: ["falta la clave 'threshold'"]`.
- `configuracion_emisora.umbral_registrado_estado` distingue el diagnóstico (la incertidumbre es la misma):

  | Estado | `umbral_registrado` |
  |---|---|
  | `clave_ausente` | `desconocido (el registro no contiene la clave threshold)` |
  | `null` | `desconocido (threshold registrado como null)` |
  | `no_numerico` | `desconocido (threshold registrado no numérico)` |
  | `numerico` | el valor registrado, tal cual |

- En los tres primeros: `estado = desconocida`, sin `configuracion`, `coherencia_score_umbral = null`. El umbral
  **no** se sustituye por el configurado, el esperado ni uno calculado, y la alerta **no** puede ser la
  `primera_alerta_IF_desplegado_confirmada_durante` (exige `estado = confirmada`). Se cuenta en
  `eventos_con_emisor_o_configuracion_desconocida`.
- Se conservan decisión, emisor (`detector_name` registrado), score, `logged_at`/`window_end`, relación con el
  episodio y el respaldo (archivo, sha256, línea).
- **Umbral registrado ≠ umbral de comparación.** Las 7 configuraciones derivadas comparan el score con los umbrales
  de análisis de la config, como antes; `threshold` nunca intervino en ellas.

## 3. Diferencia esperada en el caso incompleto (sin ocultar)

Misma entrada (episodio `inundacion_http-r1`, alerta en T+40 con la clave eliminada), analizador `a69224c` frente al
actual:

| | `a69224c` | Ahora |
|---|---|---|
| Registro de la línea 5 | descartado (`faltan claves ['threshold']`) | conservado, con incidencia |
| Cobertura | 8 de 9 anclas → **no evaluable** | 9 de 9 → evaluable |
| Tabla 8 (IF 0,05/0,03/0,01, HIB) | 0 (no evaluable) | 1/1 |
| `emisiones_observadas` | vacía | 1 alerta, umbral y configuración desconocidos |
| Latencia confirmada del IF desplegado | ninguna | **ninguna** (se mantiene) |

La regla de cobertura no cambia: la ventana estaba registrada y antes se perdía por un campo que ninguna
clasificación comparativa usa. Con el registro completo (`threshold` presente), el resultado es idéntico al de antes.

## 4. Otras diferencias de salida (registros completos)

`analisis.json` **completo** de `a69224c` frente al actual sobre los fixtures de regresión, sin proyección ni
exclusiones (rutas temporales aparte): solo cambia `configuracion_emisora.umbral_registrado_estado` (campo nuevo,
6 emisiones, todas `numerico`). Además, el texto de `umbral_registrado` para null pasa de «desconocido (no registrado
o no numérico)» a «desconocido (threshold registrado como null)», y el `motivo` añade el estado entre paréntesis. La
incidencia de clave ausente incluye ahora el archivo.

## 5. Pruebas (registros sintéticos: comprobaciones del código, no resultados experimentales)

- Nueva `test_umbral_registrado_ausente` (16 comprobaciones). Elimina **de verdad** la clave del JSON y comprueba:
  - que la alerta sigue en `emisiones_observadas`, con su incidencia y su referencia;
  - que umbral y configuración quedan desconocidos y no hay primera alerta confirmada;
  - que las 7 configuraciones siguen siendo derivadas y que clasificaciones, cobertura y Tabla 8 son iguales a las
    del registro completo;
  - que el registro completo queda confirmado, sin incidencia y con 41 s;
  - que null se distingue de la ausencia;
  - que la falta de cualquiera de los otros cinco campos sigue descartando el registro.
- Se conserva el caso `threshold: null` de `test_procedencia_emisiones`.
- `tests/test_herramientas.py`: **188 comprobaciones** con `CF_ANALIZADOR_PREVIO` = analizador de `a6dc5ab`, o
  **187** sin esa variable.
- Regresión de detección y cobertura: **0 diferencias** frente a `a69224c` y `a6dc5ab` (7 configuraciones), frente a
  `0d40bdb` (5) y frente a los dos goldens. Frente a `a69224c`, 0 diferencias excluidas.

## 6. Archivos

`scripts/analizar.py`, `tests/test_herramientas.py`, `MATRIZ-OBSERVACIONES.md` (fila 56), `RESULTADOS-VERIFICACION.md`,
`README.md`, `PLAN-CAMPANA.md`, este registro y `MANIFIESTO-CAMPANA.json` (regenerado).
