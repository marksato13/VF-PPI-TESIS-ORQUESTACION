# Cambios 2026-10-28 — `ventana_no_evaluada` en el analizador (#59)

> **Corrección posterior (#60, #61; ver `CAMBIOS-2026-10-28-cobertura.md`).** Dos cosas de este documento quedaron
> corregidas:
> - `cobertura_etiquetadas` excluía del denominador las etiquetadas sin registro. Se sustituye por
>   `conjunto_etiquetado` (`cobertura_total` = con decisión / claves esperadas, y `cobertura_entre_registradas`).
> - El control seleccionaba las decisiones por `logged_at`. Ahora decisiones y no evaluadas van por `window_end` en
>   `[desde, hasta]`; `cobertura_evaluada` pasa a llamarse `cobertura_entre_registradas` y
>   `ventanas_no_evaluadas_criterio` pasa a `seleccion`.
>
> Los nombres y cifras de abajo describen 719bf3a. El ejemplo `EJEMPLO-no-evaluadas/` está regenerado con los nombres
> nuevos.

Sobre el commit `2612e3f` (preparación tras el preflight bloqueado). Cambio de **código del analizador, tests y
documentación**; `config-campana.json` pasa a `2026-10-28.3` **solo en textos**. **No se ejecutó ningún ataque ni se
inició la campaña A.** No se tocaron Word, modelo, escalador, umbrales, características, heurísticos, escenarios, el
motor desplegado ni el estado operativo del laboratorio (sombra, perfiles y motor siguen como los dejó la preparación).

## Problema

El motor corregido (producto `7b275b8`, desplegado en sombra el 28-oct a las 08:44:50) escribe
`{"event": "ventana_no_evaluada", ...}` cuando una ventana pendiente caduca sin decisión. Hay dos motivos:

- `pcap_incompleto`: los PCAP cerrados no la cubrieron;
- `ventana_no_regenerada`: los PCAP la cubrían, pero `build_rows` ya no la generaba porque la historia se había podado.

`leer_motor()` solo lee `event == "decision"`, así que estos eventos se descartaban **en silencio**. Una ventana del
ataque sin decisión aparecía como «ancla faltante (pérdida de datos)», sin distinguir si el motor la había declarado
no evaluada. Además, `config-campana.json` citaba `motor_decision.py:601` para `logged_at`, un número de línea que
ya no corresponde a `7b275b8`.

## Qué cambia

| Pieza | Cambio |
|---|---|
| `leer_no_evaluadas()` (nuevo) | **Conservación.** Lee los eventos aparte de las decisiones y los conserva con entidad, `window_end_utc`, `logged_at`, motivo, `motivo_estado` (`reconocido` / `no_reconocido` / `ausente`), campos de disponibilidad (`pendiente_desde`, `inicio_ciclo`, `marca_pcap`, `marca_eve`, `pcaps_ilegibles`) y respaldo (archivo, sha256, línea). No crea score, decisión, etiqueta ni señal.<br>**Validación.** Sin `logged_at`, `entity_ip` o `window_end_utc`, o con un valor inválido, el evento no se cuenta y queda una incidencia `motor:<línea>`. Un motivo desconocido o ausente, o un campo de disponibilidad no numérico, se conserva con su diagnóstico. |
| Duplicados y conflictos | **Duplicado** (misma clave `entity_ip\|window_end`): se cuenta una vez y se listan todos los registros con sus motivos.<br>**Conflicto con una decisión de la misma clave:** prevalece la decisión y el evento queda en `conflictos`, sin contarse. Ambos casos generan incidencia. |
| `cobertura()` | Un evento **no** es un ancla observada. Si faltan anclas del ataque, el motivo separa `N registradas como ventana_no_evaluada (motivos)` de `M sin registro (pérdida de datos)` y añade `anclas_no_evaluadas` / `anclas_sin_registro`. **Sin eventos, la salida es idéntica.** La continuidad del motor se sigue midiendo con las decisiones. |
| Episodio: `ventanas_no_evaluadas` | **Relación.** Se decide por el **intervalo** `(window_end−60, window_end]`, no por `logged_at`, que se informa aparte (`escrito`, `escrito_tras_fin_s`):<br>– `ventana_del_ataque` (`window_end` en (inicio, fin]);<br>– `ventana_posterior_solapa` (en (fin, fin+60));<br>– sin relación.<br>**Efecto por configuración**, en este orden: IF 0,05 / 0,03 / 0,01, HEUR, HIB 0,05 / 0,03 / 0,01. Los estados posibles son `deteccion_confirmada_visible`, `ausencia_no_establecible` y `posterior_incompleta`. |
| Bloque `ventanas_no_evaluadas` (nuevo) | Definición, `contadas`, `por_motivo`, registros con `estado_en_analisis` y `relacion_episodios`, incidencias, duplicados, conflictos, reglas y `detecciones_confirmadas_en_episodios_no_evaluables`. |
| `fpr_control()` | Añade `ventanas_no_evaluadas`, la distribución por motivo, el criterio de selección, `cobertura_evaluada` = evaluadas / (evaluadas + no evaluadas) y `denominador_significado`. Las tasas siguen calculándose sobre las ventanas con decisión. |
| `metricas_por_ventana()` | Añade `etiquetadas_no_evaluadas`, `etiquetadas_sin_registro`, `cobertura_etiquetadas` y `denominador_significado`. Una ventana etiquetada sin decisión no es TP, FP, TN ni FN. |
| `calidad_datos` / `TABLA8.md` | `calidad_datos` incluye el resumen `ventanas_no_evaluadas`. `TABLA8.md` gana una sección nueva con los episodios afectados, las detecciones confirmadas que quedan fuera de la comparación y la cobertura del control y de las métricas. |
| `config-campana.json` | Versión `2026-10-28.3`, **solo textos**:<br>– referencia estable de `logged_at`: «producto `scripts/engine/motor_decision.py`, función `main()`, campo `logged_at` de los registros `decision` y `ventana_no_evaluada`, commit `7b275b8`», sin número de línea;<br>– nota `ventana_no_evaluada` en `emision_vs_window_end`.<br>Umbrales y valores sin cambios. |

## Reglas de evaluabilidad (lo que **no** se hace)

**Lo que no es un evento:**
- No es PERMIT, ni TN/FN, ni FP, ni alerta, ni emisión observada.
- Tampoco es una exclusión automática: su efecto se justifica por el intervalo afectado.

**Efecto sobre la Tabla 8:**
- La tabla no gana columna y su denominador común no cambia en silencio.
- Un ancla del ataque sin decisión ya dejaba el episodio **no evaluable** antes de #59, como pérdida de datos. Con un evento, el episodio sigue no evaluable; lo nuevo es que el motivo dice por qué.
- Una ventana que solo solapa el final (cierra después de `fin`) no puede dar una detección «durante», porque su `logged_at` > fin. Por eso no excluye el episodio y solo deja incompleta la relación «posterior».

**Efecto por componente en una ventana no evaluada del ataque:**

| Componente | Efecto |
|---|---|
| IF | No es evaluable en esa ventana para ningún α. |
| HEUR | Desconocido: no se supone que no disparó. |
| HIB | Solo un positivo confirmado prueba detección; la parte desconocida no prueba ausencia. |

**Detecciones y ausencias:**
- Una **detección confirmada** se mantiene visible en el episodio (`deteccion_confirmada_visible`) y en `detecciones_confirmadas_en_episodios_no_evaluables`. No entra en el numerador de la Tabla 8, porque el episodio no tiene cobertura común.
- Cuando no se puede establecer la ausencia, la categoría es `no_evaluable`, nunca `sin_deteccion`.

**Control y métricas:** las tasas se calculan sobre las ventanas evaluadas, están rotuladas así y van acompañadas de su cobertura. Las no evaluadas del control se seleccionan por `window_end` en el rango, y las decisiones por `logged_at`, como antes.

## Ejemplo de salida (FIXTURE DE CÓDIGO, no resultado de la campaña)

`EJEMPLO-no-evaluadas/` (lo regenera `generar_ejemplo.py`) contiene `motor.log` sintético, `analisis-extracto.json` y `TABLA8.md`. El escenario:

- Episodio `inundacion_http-r1` en [T, T+90]. Hay un ALERT del IF en T+40 (detección confirmada), pero la ventana T+70 no tiene decisión y figura como `ventana_no_evaluada` `pcap_incompleto`, escrita en T+85.
- En el control, el perfil legítimo 10.10.20.21 tiene 2 ventanas no evaluadas (`ventana_no_regenerada` y `pcap_incompleto`).

Efecto en el **episodio**:
- Cobertura insuficiente: «faltan 1 de 9 anclas de la Kali durante el ataque: 1 registradas como ventana_no_evaluada (pcap_incompleto) y 0 sin registro (pérdida de datos)».
- No evaluable; la Tabla 8 de la familia queda en 0 evaluables, igual que si el ancla se hubiera perdido sin registro.
- IF y HIB (los tres α): `deteccion_confirmada_visible`. HEUR: `ausencia_no_establecible`.
- El episodio aparece en `detecciones_confirmadas_en_episodios_no_evaluables` con IF_0.05, IF_0.03, IF_0.01, HIB_0.05, HIB_0.03 y HIB_0.01.

Efecto en el **control** `[T+95, T+200]`:
- `ventanas` = `denominador` = 8 evaluadas y `ventanas_no_evaluadas` = 2, así que `cobertura_evaluada` = 0,8.
- Falsas alarmas 0/8 por configuración, rotuladas como tasa sobre las 8 evaluadas.

Efecto en las **métricas** (etiquetas T+40=1, T+70=1, T+60=0):
- Denominador 2 y `etiquetadas_no_evaluadas` = 1, así que `cobertura_etiquetadas` = 0,666667.
- IF_0.05: TP 1, TN 1, FN 0. La ventana positiva no evaluada **no** es FN.
- HEUR: FN 1, que corresponde a T+40 (con decisión y sin heurístico), no a T+70.

## Compatibilidad con el evento real de la preparación

`preparacion-2026-10-28/salidas/out_p38_sensor_noevaluada.txt` contiene el evento que escribió la instancia
**candidata** el 28-oct: 10.10.20.23, `window_end` 07:57:30 UTC, `pcap_incompleto`. `test_no_evaluada_real_compatibilidad`
lo lee sin incidencias, con los 5 campos de disponibilidad, una espera de 172,6 s y `marca_pcap − window_end` = +163,3 s.

Es solo una comprobación de lectura. No se le asigna etiqueta, atribución ni efecto experimental. El motivo es el que
registró el candidato antes del cambio de etiqueta, aunque la marca PCAP indica que la ventana estaba cubierta
(ver `PREPARACION-2026-10-28.md`).

Sigue vigente la aclaración de la preparación: la comparación 07:53–08:23 UTC cruza el cambio de intensidad de las
08:00 UTC (0,12 → 1,0), así que **no** es carga constante.

## Comprobaciones (código, sin ataques)

- `tests/test_herramientas.py`: **212** comprobaciones (**213** con `CF_ANALIZADOR_PREVIO` = analizador de `a6dc5ab`). Antes eran 187/188.
  - Las 23 pruebas anteriores pasan sin cambiar ninguna expectativa.
  - Se añaden `test_ventanas_no_evaluadas` (22) y `test_no_evaluada_real_compatibilidad` (3). Cubren:
    - motivos conocido, no reconocido y ausente;
    - un evento escrito tras el ataque con ventana que lo solapa;
    - un evento fuera del periodo;
    - una ventana que solo solapa el final;
    - un episodio sin detección y con cobertura insuficiente;
    - una detección confirmada más otra ventana no evaluada;
    - un control con no evaluadas que no son TN;
    - una etiquetada no evaluada que no es FN;
    - duplicados y conflicto con decisión;
    - campos ausentes o inválidos;
    - el orden de las 7 configuraciones;
    - la neutralidad sin eventos;
    - el evento real.
- `tests/regresion_alfa.py`: 0 diferencias de detección/cobertura (7 y 5 configuraciones) frente a los goldens, `2612e3f` (0 excluidas), `a6dc5ab` (86 excluidas de procedencia, como antes) y `0d40bdb` (5).
  - Excluye explícitamente las claves nuevas de cobertura (`CLAVES_NO_EVALUADAS`) en el control, las métricas y `calidad_datos`. La suite comprueba aparte que, sin eventos, valen 0 / 1,0.
- `analisis.json` completo frente a `2612e3f` sobre los fixtures, sin eventos: solo **claves añadidas**: `calidad_datos.ventanas_no_evaluadas`, 5 en el control, 4 en las métricas, `episodios.*.ventanas_no_evaluadas` y el bloque `ventanas_no_evaluadas`. Ningún valor existente cambia.
- `tests/test_matar_grupo.py`: 6/6.

## Qué cambia en coberturas y denominadores con eventos reales

| Lugar | Cambio |
|---|---|
| **Tabla 8** | Mismos evaluables y mismo numerador que tratando el evento como pérdida. Solo cambia el texto del motivo y aparecen los bloques nuevos. |
| **Control** | `ventanas` y `denominador` no cambian, porque cuentan decisiones. Se añade la cobertura (< 1 si hay eventos); la tasa se lee «sobre N evaluadas, cobertura c». |
| **Métricas** | `denominador` no cambia. Las etiquetadas no evaluadas salen del recall/FPR y se informan en `cobertura_etiquetadas`. Antes simplemente no aparecían, sin aviso. |
