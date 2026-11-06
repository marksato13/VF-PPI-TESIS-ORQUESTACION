# Protocolo E-carga v2: estabilidad de la integración en sombra con carga suficiente (2026-11-06)

**Estado: publicado. NO ejecutado.** No se ha arrancado ningún generador ni se ha abierto ninguna observación. La
ejecución necesita una orden posterior y explícita de Mark.

**Identificador:** **E-carga v2 (2026-11-06)**. Sustituye a E-carga v1
([`PROTOCOLO-CARGA.md`](PROTOCOLO-CARGA.md), publicado en `36a3739`). La v1 se conserva **sin modificar** para que
siga siendo identificable; la v1 no se llegó a ejecutar.

**Base de la medida.** La observación del 06-nov (O12) sigue siendo **«carga insuficiente»**. Ni la v1 ni la v2 la
sustituyen ni la reevalúan.

**Revisión vigente: r2 (06-nov).** La r1 es el texto publicado en `8f17273`, que sigue identificable en el historial
y por su sha256 en `evidencia/10-veredicto-contrato/protocolo-v2-r1.sha256`. La r2 no cambia ningún criterio ni
umbral; los cambios están en §0.1.

**Herramientas.** Producto **`ae2900e`** (rama `recuperacion/etapa4a-pendientes-20261106`):
- `evaluar_ecarga.py` **2026-11-06.4**: blob `06b84134…`, sha256 `53e9f7bd…`. Contrato de entrada estricto y contraste
  de coherencia en `veredicto` (§4.5).
- `obs_pcap.py` 2026-11-06.2, sin cambios desde `f6dc685`.

El paquete `~/cf-e4/paquete-f6dc685` (tgz `beb70c79…`, `SHA256SUMS` interno `7828f0a4…`) ya está copiado en los tres
hosts, sin instalar nada, pero lleva el evaluador **2026-11-06.3**, que tiene el defecto de §0.1. **No sirve para
E-carga.** Antes de P0 hay que copiar el paquete de `ae2900e` (§3.5, punto 9).

> **Nota de estado (06-nov, tarde). No es una revisión: no cambia ningún criterio, umbral, franja ni condición.**
>
> El paquete de `ae2900e` ya está copiado y verificado en `~/cf-e4/paquete-ae2900e`, en el bastión, en Sensor1 y en
> srv-dmz:
> - tgz `09ab20c8…`;
> - `SHA256SUMS` interno `41f91787…`;
> - evaluador `53e9f7bd…`, `VERSION` 2026-11-06.4.
>
> Junto a `paquete-f6dc685` hay un aviso `NO-USAR-PARA-VEREDICTO`.
>
> Las comprobaciones previas y en seco de §3.5 (puntos 1–7 y 9) se hicieron sin carga y **se repiten en P0**.
>
> E-carga sigue **sin ejecutar y sin programar**. La preparación, la construcción de la entrada y la secuencia del día
> están en [`ecarga-v2-preparacion/PREPARACION-ECARGA-v2.md`](ecarga-v2-preparacion/PREPARACION-ECARGA-v2.md). Ese
> documento deja pendiente una decisión: la definición operacional de «saturación nueva» de S14 (§4.4).

## 0. Qué cambia respecto a la v1 y por qué

| # | Dónde (v1) | Cambio | Por qué |
|---|---|---|---|
| 1 | §3.6, resultado «estable»: «puede ser C0, o C3 si hubo descartes por debajo de S13» | Se elimina. La clase es **la del clasificador vigente, tal cual** (§4.2): descartes de Suricata medidos con cobertura completa son **C1**, no C3. Se separan cuatro dimensiones: estabilidad técnica, clase de captura, I5 y población principal (§4) | Contradecía el clasificador (`salud_captura.clasificar`: `descartes` → C1) y mezclaba el límite técnico S13 con la calidad de captura |
| 2 | §3.4, K4 | Se divide en **K4a**, presencia de los seis perfiles (criterio), y **K4b**, ráfaga del perfil errático (**solo informativo**), con una regla operacional fijada antes de medir (§3.4) | «3 × la mediana» no significa nada con mediana 0 (el caso nocturno). La regla auxiliar fijada para K4b **no quedó validada como criterio decisorio**: en la simulación del diseño del generador da demasiadas detecciones en horas sin ráfaga real (§3.4.2). Esa simulación **no demuestra que ninguna regla posible pueda funcionar**; solo que esta no basta *(r2: corregido; la r1 afirmaba lo contrario)* |
| 3 | §4 y README §0: aplicación real ligada a «4C/campaña B» | Alcance unificado: 4A sombra + E-carga · 4B control normal formal · 4C campaña A en sombra **sin aplicar** · campaña B **posterior**, con respuesta aplicada (§2.1) | La 4C no aplica restricciones; solo la campaña B lo hace |
| 4 | §4: «el feed no tendrá medidas» | Puede haber **señales o propuestas** producidas por tráfico legítimo. Se registran y no se suprimen. La condición operativa es que **no se aplique ninguna restricción** (S10) | No hay base para afirmar que el feed estará vacío: el detector puede reaccionar a tráfico legítimo |
| 5 | §3.2, tiempos relativos | Tiempos en **epoch**, con UTC y Perú, de una franja comprobada contra el calendario y la zona horaria real del generador (§3.2) | La v1 dejaba la hora sin fijar |
| 6 | §3.3, `obs_pcap.py` «hora de fin como epoch explícito» | `obs_pcap.py` 2026-11-06.2 exige el fin en epoch **y** en ISO UTC, que deben coincidir al segundo (si no, rc 2), y tiene un modo `--en-seco`, ya ejecutado (§3.5) | El 06-nov el fin estaba mal calculado (06:11:30Z en vez de 05:51:30Z) |
| 7 | Herramienta de K4a (defecto propio, hallado en la referencia de desarrollo) | Los tramos de 600 s son completos y el resto se suma al último | En la ventana base de 3 606 s creaba un 7.º tramo de 6 s vacío y K4a fallaba por construcción. Se corrigió con una prueba de regresión (`f6dc685`) antes de congelar |

**No cambian:**
- K1, K2, K3 y K5;
- S1–S15;
- el umbral **S13 < 14,95 descartes por millón**;
- las condiciones de parada, la franja horaria del generador, la duración de la ventana y el calentamiento.

No se cambia **ningún umbral**.

### 0.1 Revisión r2 (06-nov): evaluador 2026-11-06.4, sin cambio de criterios

**Defecto reproducido** en `evaluar_ecarga.py` 2026-11-06.3 (`f6dc685`). `veredicto` declaraba «estable con carga
suficiente», con rc 0 y la condición (3) habilitada, en estos tres casos:
1. K1 y S1 con el texto `"false"` en vez del booleano;
2. clase `no_evaluable` con los S marcados como verdaderos;
3. clase C1 con 100 descartes por millón y S13 marcado como verdadero.

El evaluador se fiaba de los indicadores ya preparados y no los contrastaba. Reproducción:
`evidencia/10-veredicto-contrato/reproduccion-f6dc685.txt` (3 de 3 habilitan) frente a 0 de 3 con 2026-11-06.4.

| # | Cambio en r2 | Por qué | ¿Cambia un criterio? |
|---|---|---|---|
| 1 | Contrato de entrada estricto (§4.5): K y S solo `true`, `false` o `null`; métricas numéricas, finitas y ≥ 0; bloque `suricata` obligatorio; entrada inválida → rc 2 sin habilitar nada | Fallo 1, y que un dato ausente no pase por cero | No |
| 2 | Contraste de S12 y S13 con las métricas y de la clase con la medida de Suricata. Una contradicción se lista y da «no demostrable», sin corregir ningún dato | Fallo 3. §4.1 ya decía «no demostrable» si la clase no cuadra con los descartes medidos; ahora también se comprueban los indicadores | No: S13 sigue siendo < 14,95/M, y el valor exacto 14,95 no cumple |
| 3 | C3 y `no_evaluable` no pueden dar «estable con carga suficiente»: pasan a «no demostrable». Un S que falla con C3 sigue siendo «no estable» | Fallo 2. Una captura no evaluable no demuestra estabilidad | Precisa §4.1, que no contemplaba este caso. No baja ni sube ningún umbral |
| 4 | §0, fila 2, y §3.4.2: se corrige la afirmación sobre K4b | La simulación no demuestra que ninguna regla posible funcione; solo que la regla fijada no quedó validada como criterio decisorio | No: K4b sigue siendo informativo |

## 1. Por qué hace falta (sin cambios respecto a la v1 §1)

En la ventana del 06-nov no funcionaba ningún generador legítimo:
- 0 flujos de 10.10.20.21–26;
- 0 ráfagas ≥ 5 000 paquetes por 8 s;
- 0 flujos ≥ 1 000 paquetes;
- pps máximo 391, frente a 2 426 en el ensayo del anillo.

Un volumen del 49 % no equivale a la misma demanda. Detalle: [`PROTOCOLO-CARGA.md`](PROTOCOLO-CARGA.md) §1 y
`evidencia/08-carga/`.

## 2. Decisión y alcance

**E-carga es un ensayo técnico adicional dentro de la 4A.** Las razones son las de la v1 §2: es una pregunta de
aceptación de la integración, la 4B usará esa cadena como instrumento y así no se mezclan atribuciones.

### 2.1 Alcance de las etapas (vale para este protocolo, el README y el criterio de avance)

| Etapa | Qué es | Restricciones aplicadas |
|---|---|---|
| **4A** | Instalación y aceptación técnica en sombra, **incluido E-carga** | Ninguna |
| **4B** | Control normal formal | Ninguna |
| **4C** | Campaña A en sombra | **Ninguna**: no se aplican restricciones |
| **Campaña B** (posterior) | Respuesta aplicada y medición de su efecto | Sí, es la única etapa con aplicación |

En E-carga solo hay tráfico legítimo, pero el detector **puede** producir decisiones anómalas, señales de la vía
rápida o entradas del feed (propuestas).
- Se registran tal cual: número, entidad, instante y origen.
- **No se suprimen** y **no son motivo de fallo** por sí mismas.
- Se publican como posibles falsas alarmas sobre tráfico legítimo, sin valor de tasa: es una sola hora.
- La condición operativa es **S10: ninguna restricción aplicada**.

## 3. Diseño, fijado antes de ejecutar

### 3.1 Perfiles legítimos y configuración (sin cambios)

- **Generador:** `~/laboratorio/clientes_lab.py`, sha256 `ae5134a7…`. Seis perfiles, uno por IP de 10.10.20.21 a .26,
  arrancados por `cyberflow-lab.target`.
  - `--intensidad` por omisión y curva `factor_horario` **sin fijar**.
  - El generador, su intensidad y su curva **no se modifican**.
- **Zona horaria real:** `Etc/UTC` en el host de clientes (`evidencia/08-carga/clientes_ro3.txt`) y en Sensor1
  (`evidencia/09-ecarga-v2/referencia_dev_f6dc685.txt`). `factor_horario` usa la hora local, que es UTC.
- **Franja:** la ventana cae entera en 23:00–08:00 UTC de un día laborable según UTC. Ahí `base` = 0,12, la misma que
  en el ensayo del anillo (miércoles 06:26–07:26 UTC).

### 3.2 Tiempos (franja propuesta; **no programada**)

El calendario está comprobado: el lunes 2026-11-09 tiene `weekday()` = 0 en UTC.

| Paso | Epoch | UTC | Perú (UTC−5) |
|---|---|---|---|
| P0, comprobación previa | 1794191400 | lun 09-nov 02:30:00 | dom 08-nov 21:30:00 |
| T_g, arranque de generadores | **1794193200** | lun 09-nov 03:00:00 | dom 08-nov 22:00:00 |
| Calentamiento (no cuenta) | 1794193200–1794194100 | 03:00:00–03:15:00 | 22:00:00–22:15:00 |
| **Ventana fija** | **1794194100–1794197700** | **03:15:00–04:15:00** | **22:15:00–23:15:00** |
| Fin de `obs_pcap.py` (ventana + 60 s; deja de leer a +30 s y hace una pasada final) | 1794197760 | 04:16:00 | 23:16:00 |
| Parada de generadores | 1794197820 | 04:17:00 | 23:17:00 |
| Análisis de perfiles, no antes de | 1794198600 | 04:30:00 | 23:30:00 |
| Lecturas posteriores y verificadores, hasta | 1794200400 | 05:00:00 | 00:00:00 (lun) |

- La ventana no se corta, no se mueve y no se prolonga.
- Si no se puede empezar exactamente en T_g, **no se desplaza en silencio**:
  - se fija una franja nueva con los mismos desfases;
  - se publica en `evidencia/` antes de arrancar;
  - debe caer en otra madrugada laborable UTC.
- **Por qué el análisis empieza a las 04:30.** Suricata escribe el evento `flow` al expirar el flujo. Sus
  `flow-timeouts` reales (`suricata.yaml` `0962ce68…`) son TCP `established` 600 s y `closed` 60 s; UDP e ICMP
  `established` 300 s. Un flujo con su último paquete en la ventana aparece en EVE como muy tarde ≈ 660 s después.
  Las 04:30 dejan 900 s.

### 3.3 Instrumentación (solo lectura)

Todo sale del paquete de **`ae2900e`** (`~/cf-e4/paquete-ae2900e`, copiado y verificado el 06-nov; §3.5, punto 9)
salvo lo indicado. El paquete `paquete-f6dc685` no se usa para el veredicto.

**Bastión**
- `obs_muestreo.sh` cada 30 s (`evidencia/06-observacion/`). Incluye Sensor1 y srv-dmz por ssh: PID, `NRestarts`,
  entregas, aceptaciones, rulesets, panel 401 y procesos con `--aplicar`/`--enforce`.

**Sensor1**
- `salud_captura.py muestrear --intervalo 10 --hasta 2026-11-09T04:16:00Z` (`~/cyberflow-e4/herramientas-20261106`,
  VERSION 2026-11-06.1).
- `obs_pcap.py --dir /var/lib/ppi-motor-capture --salida DIR --hasta-epoch 1794197760 --hasta-iso 2026-11-09T04:16:00Z`.
- `muestreo_fino.py` a 1 s.
- Después de la ventana:
  - `comparar_suricata.py --stats-eve --eve` (K1–K3);
  - `clasificar_periodo.py --suricata-eve` (clase);
  - `evaluar_ecarga.py perfiles` (K4a/K4b);
  - `evaluar_ecarga.py veredicto` (§4).

**Señales y propuestas** (§2.1)
- Decisiones del motor con anomalía;
- `senales-rapidas.jsonl`;
- `entradas` y `nuevos` de la traza del publicador v2;
- eventos de la traza del agente.

**Verificadores** antes y después: `verificar_bastion.sh`, `verificar_sensor1.sh` y `verificar_srvdmz.sh` (los de
`a1cea5e`, incluidos sin cambios en `f6dc685`). También los hashes congelados de O11.

### 3.4 Carga requerida («carga suficiente»)

La carga es suficiente solo si se cumplen **todas** estas condiciones; ninguna compensa a otra:

| # | Dimensión | Umbral | Origen (no cambia) |
|---|---|---|---|
| K1 | Volumen | ≥ **596 789** paquetes de Suricata en la ventana (eventos `stats` de EVE) | O12 |
| K2 | Ráfagas de red | ≥ **9** intervalos de 8 s con ≥ 5 000 paquetes | Ensayo del anillo |
| K3 | Flujos grandes | ≥ **50** flujos de ≥ 1 000 paquetes | Ensayo del anillo |
| **K4a** | Presencia de los seis perfiles | Cada IP 10.10.20.21–26 con **≥ 1 flujo en cada uno de los 6 tramos** de 600 s (§3.4.1) | Cobertura de perfiles (v1 K4, primera parte) |
| K5 | Cobertura de la medida | `stats` de EVE sin hueco > 20 s, bordes a ≤ 10 s, un solo proceso de Suricata | `CRITERIOS-FIJADOS.md` §1 |
| K4b | Ráfaga del perfil errático | **Informativo; no decide** (§3.4.2) | — |

#### 3.4.1 K4a: definición operacional

- **Flujo:** evento EVE con `event_type` = `flow` y `src_ip` igual a la IP del perfil, de cualquier protocolo.
- **Asignación temporal:** por `flow.start`, no por el instante en que se emite el evento. Cuenta si
  `desde ≤ flow.start < hasta`.
- **Tramos:** 6 tramos de 600 s desde 1794194100. Un resto de menos de 600 s se sumaría al último; no ocurre con
  3 600 s.
- **Errores de lectura:** un fichero ilegible, una línea de flujo corrupta o un `flow.start` que no se puede leer dan
  **error (rc 2)**. Nunca cuentan como ausencia.

**Riesgo por azar, declarado antes de medir.**
- El perfil más lento es ligero: ritmo 12 s, de madrugada ≈ 100 s entre acciones, ≈ 6 acciones por tramo.
- La probabilidad de que un tramo quede vacío es ≈ e⁻⁶ ≈ 0,25 %, y la de que falle alguno de los 6 tramos, ≈ 1,5 %.
- En la referencia de desarrollo, el mínimo de ligero en un tramo fue de 2 flujos.

#### 3.4.2 K4b: regla, justificación y por qué queda informativo

**Regla, congelada en `evaluar_ecarga.py` 2026-11-06.3** (`f6dc685`; la regla del errático no cambia desde `38ee91d` y sigue igual en 2026-11-06.4, `ae2900e`):
- **Intervalos:** de 8 s desde el inicio de la ventana, **todos**, también los que no tienen actividad: n = 450.
- **Tasa de referencia:** λ_ref = max(media de flujos por intervalo con los ceros incluidos, λ_diseño), con
  λ_diseño = 8 × 0,12 / 5 = 0,192, del ritmo del errático y la curva nocturna.
  - **No se usa la mediana:** de madrugada es 0, y en las referencias de desarrollo también fue 0.
- **Ráfaga:** 5 intervalos consecutivos (40 s) cuya suma sea ≥ T = max(6, ⌈3 × λ_ref × 5⌉) y en los que **al menos 3
  intervalos** tengan actividad.
  - La segunda condición distingue una ráfaga de una actividad aislada, es decir, muchos flujos en un solo intervalo.
  - Las ventanas solapadas que cumplen se funden en un episodio.
- **Estados:** `sin_trafico`, `sin_rafaga_detectable` o `rafaga_detectada`.

**Diseño del generador** (`clientes_lab.py`, sin modificar):
- Fuera de una ráfaga, cada acción abre una con probabilidad 0,02.
- Una ráfaga dura U(20, 90) s y multiplica el ritmo por 6.
- De madrugada hay ≈ 86 acciones por hora.

**Simulación del diseño** (`deploy/etapa4/banco/simular_k4b.py`, semilla 20261106, 4 000 horas; salida en
`evidencia/09-ecarga-v2/simular_k4b.txt`):

| Flujos por acción | Flujos/h simulados | P(hay ráfaga real en la hora) | P(detectada \| hay ráfaga) | P(detectada \| no hay) | Episodios falsos/h |
|---|---|---|---|---|---|
| 1,0 | 98,7 | 0,82 | 0,893 | 0,107 | 0,106 |
| 1,5 | 148,1 | 0,82 | 0,998 | **0,926** | **2,28** |

**Referencia de desarrollo** (identificada: Sensor1, `eve.json.1-2026110600.backup`, 04-nov, generadores activos,
misma franja de madrugada). Se leyó **después** de fijar la regla, y no la ajusta:

| Ventana | Flujos del errático | Media/8 s | Mediana | Estado K4b | Episodios |
|---|---|---|---|---|---|
| Base 4A, 02:19:45–03:19:51 | 139 | 0,308 | 0 | `rafaga_detectada` | 4 |
| Ensayo del anillo, 06:26:55–07:26:55 | 130 | 0,289 | 0 | `rafaga_detectada` | 3 |

**Conclusión.** El generador no fija cuántos flujos produce cada acción, y no registra cuándo está en ráfaga.
- Con la tasa observada en desarrollo (130–139 flujos/h, entre los dos supuestos simulados y más cerca de 1,5), la
  regla daría «ráfaga» en la mayoría de las horas **sin** ráfaga real.
- Además, ≈ 18 % de las horas no tienen ninguna ráfaga real, solo por azar del generador.

**La regla fijada no quedó validada como criterio decisorio** *(r2; la r1 decía «no se puede justificar una regla
fiable»)*. La simulación prueba **esta** regla con dos supuestos de flujos por acción. No demuestra que ninguna regla
posible pueda funcionar: no se han probado otras reglas ni se ha medido cuántos flujos genera cada acción. Por eso:
- **K4b no decide el resultado.** Se mide y se publica con su estado, como dato descriptivo.
- **Alternativa adoptada:** la exigencia de demanda a ráfagas recae en **K2** (≥ 9 ráfagas de red de ≥ 5 000 paquetes
  por 8 s) y en **K3** (≥ 50 flujos grandes). Ambas miden lo que importa a la estabilidad de captura y ya estaban
  fijadas. Sus umbrales no cambian.
- **Alternativa no adoptada:** hacer K4b decisorio exigiría observar el estado de ráfaga del generador o validar
  cuántos flujos genera cada acción. Lo primero obliga a modificar el generador, y eso no está permitido. Queda
  descartada para esta versión.
- **Cambio respecto a la v1.** El errático con ráfaga visible deja de ser condición de «carga suficiente». Lo
  declaro como cambio de criterio: la v1 exigía algo para lo que no hay una regla de medida validada.

### 3.5 Comprobación previa P0 (solo lectura; si algo falla, no se arranca nada)

1. Los tres verificadores con **rc 0**.
2. Hashes congelados iguales a O11: modelo `df547da0…`, manifiesto `b3ad6805…`, esquema `e032a1a2…`, `ec78ca5`
   `SHA256SUMS` y `suricata.yaml` `0962ce68…`. Este último fija también los `flow-timeouts` de §3.2.
3. Sin `--aplicar` ni `--enforce`. Rulesets de Sensor1 (`24c320e3…`) y de srv-dmz (`e3b0c442…`) iguales a los del
   06-nov.
4. Generador con hash `ae5134a7…`. Los seis servicios inactivos y sin procesos de perfiles vivos.
5. Zona horaria `Etc/UTC` en clientes y Sensor1. `date -u` dentro de la franja. `weekday()` UTC de 0 a 4.
6. `/home` de Sensor1 ≥ 2 GB y `MemAvailable` ≥ 1 GiB.
7. **`obs_pcap.py --en-seco`** con los dos fines (epoch e ISO): rc 0 y `fin_utc` = 2026-11-09T04:16:00Z.
   - Ya se ejecutó el 06-nov a las 07:15Z con rc 0.
   - Con el valor erróneo del 06-nov da rc 2.
   - Ver `evidencia/09-ecarga-v2/referencia_dev_f6dc685.txt`.
8. Ventana fijada en epoch y publicada, con su commit, **antes** de T_g.
9. *(r2)* Paquete de **`ae2900e`** copiado en Sensor1, sin instalar nada:
   - `SHA256SUMS` interno verificado;
   - `evaluar_ecarga.py` con sha256 `53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f` y `VERSION`
     2026-11-06.4.
   Con el 2026-11-06.3 no se emite el veredicto.

### 3.6 Criterios de estabilidad técnica (sin cambios de valor)

| # | Criterio |
|---|---|
| S1–S11 | Los O1–O11 de `CRITERIOS-FIJADOS.md` aplicados a la ventana nueva. S10 = 0 eventos `aplicacion`, rulesets iguales, sin `--aplicar`/`--enforce` y v1 inactivos |
| S12 | Descartes de Suricata **medidos**: `cero_explicito` o `descartes` con su valor. Una ausencia **no** cuenta como cero |
| S13 | Descartes por millón **< 14,95** (2 × la base 4A) |
| S14 | Sin saturación nueva de CPU, softirq, disco ni memoria; softnet `dropped` = 0 |
| S15 | Verificadores con rc 0 después de la ventana |

### 3.7 Parada anticipada (sin cambios)

Se paran los generadores, se conserva todo lo medido y el resultado es «no estable» o «no demostrable» si ocurre
cualquiera de estas cosas:
- `MemAvailable` < 1 GiB, o `/home` < 2 GB;
- `--aplicar` o `--enforce`, o un cambio de ruleset;
- se reinicia un servicio de la cadena;
- `firma_invalida` o `paquete_invalido` sostenidos más de 60 s;
- EVE parado más de 60 s.

Una señal o una entrada del feed **no** es motivo de parada (§2.1). Una **aplicación** sí lo es.

## 4. Resultado: cuatro dimensiones separadas

`evaluar_ecarga.py veredicto` las calcula por separado, y ninguna se deduce de otra.

### 4.1 Estabilidad técnica (K1–K5 y S1–S15)

| Resultado | Condición | Qué permite concluir | Qué habilita |
|---|---|---|---|
| **estable con carga suficiente** | K1–K5 y S1–S15 se cumplen | La integración en sombra se mantuvo estable una hora con carga comparable a la de referencia | La **condición (3)** del criterio único (README §0) para el control formal de la 4B |
| **no estable** | K1–K5 se cumplen y falla algún S | Hubo un fallo técnico con carga | Nada. Diagnóstico y, en su caso, otro E-carga con identificador nuevo |
| **carga insuficiente** | Falla algún K | Nada sobre la estabilidad con carga. Los S que fallen se publican igualmente como hallazgos | Nada |
| **no demostrable** | Falta una lectura; la clase no cuadra con los descartes medidos; *(r2)* un indicador contradice las métricas o la clase (§4.5); o *(r2)* la clase es C3 o `no_evaluable` con todos los K y S cumplidos | Nada | Nada |

*(r2)* Orden de decisión:
1. Falla algún K → «carga insuficiente». Las contradicciones se listan igualmente.
2. Si no, falta algún K o S → «no demostrable».
3. Si no, falla algún S → «no estable».
4. Si no → «estable».

Después:
- una contradicción convierte «no estable» y «estable» en «no demostrable»;
- C3 o `no_evaluable` convierte «estable» en «no demostrable», pero un S que falla con C3 sigue siendo «no estable».

La condición (3) se habilita **solo** con `habilita_condicion_3 = true`, que exige las tres cosas: «estable», ninguna
contradicción y una clase C0, C1 o C2. El rc 0 equivale exactamente a eso.

### 4.2 Clase de calidad de captura (clasificador vigente, tal cual)

El clasificador es `salud_captura.clasificar` 2026-11-06.1 con `--suricata-eve`, a través de `clasificar_periodo.py`
2026-11-06.1. Las definiciones son las de `OBJETIVOS-Y-CRITERIOS.md` §6.1.

**Precedencia dentro de cada captura:** C3 > C2 > C1 > C0. Se informan **todos** los motivos.
**Clase del periodo:** la peor de las dos capturas (anillo y vía rápida); `no_evaluable` domina a todas.

| Clase | Condición exacta en el código | Qué se puede afirmar |
|---|---|---|
| **C0** | Ningún motivo de C3, C2 ni C1. Suricata `cero_explicito` y tcpdump sin descartes del kernel, con cobertura completa | Condición de calidad de la población principal, en esta ventana |
| **C1** (EVE degradado) | Suricata `descartes` (medida completa con descartes > 0), sin motivos de C2 ni de C3 | Solo detecciones observadas, con su limitación. **No** es captura sin pérdidas; **no** autoriza la evaluación completa del IF |
| **C2** (paquetes degradados) | tcpdump con descartes del kernel, sin motivos de C3 | Igual que C1, y además afecta a las características L3/L4 |
| **C3** (no evaluable) | Cualquiera de estos: tramo sin muestra > máximo; reinicio o parada de un componente; Suricata (EVE) en estado `ausente`, `desactualizada`, `error_lectura` o `cobertura_insuficiente`, o medida de otro periodo; salto del anillo > rotación + tolerancia, o anillo sin medida; archivador sin medida o con FALLO/PERDIDO; tcpdump sin cobertura SIGUSR1 completa | Nada sobre el detector |
| **no_evaluable** (periodo) | Muestras que no acotan el periodo (`insuficiente`), menos de dos muestras, periodo fuera de la cobertura, o journal no exportado o sin lecturas SIGUSR1 | Nada |

**S13 y la clase son cosas distintas.** Con, por ejemplo, 3 descartes por millón y medida completa, S13 se cumple
(< 14,95) y la clase es **C1**. Ese resultado sería «estable con carga suficiente, clase C1».
- La limitación C1 se conserva en todo uso posterior.
- Nunca se presenta como captura sin pérdidas.
- No demuestra C0.

### 4.3 I5

**No se evalúa en E-carga.** I5 exige 0 `kernel_drops` en los 30 min previos al **inicio real de la 4C**, terminando
en la última muestra (≤ 20 s de antigüedad), con una lectura propia en ese momento.
- Ningún resultado de E-carga lo satisface, tampoco C0.
- S13 no sustituye a I5.

### 4.4 Admisión en la población principal

La población principal la forman los episodios C0 con integridad v2 apta. **E-carga no produce episodios**, así que no
admite ninguno.
- Su clase solo dice si la captura con carga cumplió la condición de calidad.
  - C0: sí.
  - C1 y C2: no; se publican aparte con su clase.
  - C3 y `no_evaluable`: no evaluable.
- Un C1 en E-carga avisa de que, con esa carga, los episodios de la 4C podrían quedar fuera de la población principal.

### 4.5 Contrato de entrada de `veredicto` y tratamiento de contradicciones (r2, `evaluar_ecarga.py` 2026-11-06.4)

**Entrada:** un objeto JSON con exactamente estos cinco campos, sin campos de más y sin claves duplicadas.

| Campo | Tipo admitido | Notas |
|---|---|---|
| `K` | objeto con exactamente `K1`, `K2`, `K3`, `K4a`, `K5` | Cada valor `true`, `false` o `null`. `null` = **sin medida**. K4b no entra (es informativo) |
| `S` | objeto con exactamente `S1` … `S15` | Igual que `K` |
| `clasificacion` | `{"clase_periodo": C0\|C1\|C2\|C3\|no_evaluable, "motivos": [texto, …]}` | Copiados de `clasificar_periodo.py`, sin reinterpretar |
| `suricata` | `{"estado", "paquetes", "descartes"}` | `estado` es uno de los seis de `medida_suricata_eve`: `cero_explicito`, `descartes`, `ausente`, `desactualizada`, `error_lectura`, `cobertura_insuficiente`. Contadores **enteros ≥ 0**, obligatorios si el estado es una medida (`cero_explicito` o `descartes`); `null` solo si no lo es |
| `descartes_por_millon` | número real finito ≥ 0 | Obligatorio si hay medida; `null` solo si no la hay |

**Lo que se rechaza** (rc 2, JSON con `error`, `campo` y `habilita_condicion_3: false`, sin `estabilidad_tecnica`):
- cualquier conversión implícita a booleano: `"false"`, `"true"`, `"null"`, `""`, `0`, `1`, `0.0`, listas u objetos;
- en las métricas: `true`/`false` usados como números, NaN, ±∞ (también como literales `NaN` o `Infinity` en el
  JSON), negativos, textos y contadores no enteros (también `2.0`);
- un campo ausente, uno no reconocido o una clave duplicada;
- un fichero ilegible o un JSON mal formado.

Un dato ausente nunca se toma por cero ni por cumplimiento.

**Contradicciones.** Se contrastan con las métricas y nunca se corrigen.

| Comprobación | Contradicción si… |
|---|---|
| S12 (descartes medidos) | Es `true` sin medida, o no es `true` con medida |
| S13 (< 14,95/M) | No coincide con `descartes × 10⁶ / paquetes < 14,95`, calculado con enteros (`descartes × 10⁸ < 1 495 × paquetes`). **14,95 exacto no cumple.** Sin medida, o con 0 paquetes, S13 = `true` es contradicción |
| `descartes_por_millon` | Difiere más de 0,01 de `descartes × 10⁶ / paquetes`, o lleva valor sin medida |
| Estado de Suricata | `cero_explicito` con descartes > 0, o `descartes` con 0 descartes |
| C0 | El estado no es `cero_explicito`, hay descartes, o hay motivos (C0 exige evidencia completa sin motivos) |
| C1 | El estado no es `descartes`, los descartes son 0, o no hay motivos |
| C2 y C3 | No hay motivos. Además, C2 sin medida de Suricata (el clasificador daría C3) |

Cada contradicción aparece en `incoherencias` y el resultado pasa a «no demostrable» (salvo «carga insuficiente»).
`descartes_por_millon`, la clase y los indicadores se publican **tal como llegaron**.

**Caso previsto, que sigue siendo válido:** clase C1, estado `descartes`, por ejemplo 2 de 625 000 (3,2/M), S12 y S13
`true` y todo lo demás cumplido. Da «estable con carga suficiente» y habilita la condición (3), con dos limitaciones
que conserva:
- «No es captura sin pérdidas»;
- «S13 … no demuestra C0 ni I5».

I5 sigue «no evaluado» y la población principal sigue «NO apta» para C1.

**Pruebas de §4** (`tests/test_etapa4_ecarga.py`, con el clasificador **sin modificar**):
- cero descartes → C0;
- descartes con cobertura completa → C1;
- evidencia insuficiente (4 estados de Suricata) → C3, y sin muestras que acoten → `insuficiente`;
- concurrencia de motivos:
  - descartes + reinicio → C3;
  - descartes + hueco del anillo → C3;
  - descartes + tcpdump → C2;
  - tcpdump + reinicio → C3;
  - Suricata ausente + tcpdump → C3;
  - en todos los casos se informan todos los motivos;
- veredicto:
  - estable C1, que conserva la limitación y no es C0 ni I5;
  - S13 superado → no estable;
  - carga insuficiente con hallazgos de S;
  - lecturas que faltan → no demostrable;
  - incoherencia entre clase y descartes → no demostrable;
  - entrada incompleta → error.
- *(r2, `ae2900e`, 129 casos en el fichero)*:
  - los tres fallos reproducidos;
  - `true`, `false` y `null` válidos, y 12 tipos incorrectos en K y en S;
  - métricas ausentes, negativas, booleanas, NaN, infinitas, de texto o no enteras;
  - NaN e Infinity como literales del JSON;
  - dpm que no cuadra con los contadores; 0 paquetes; números con Suricata sin medida;
  - C0 coherente, C0 con descartes y C0 con motivos;
  - C1 a 14,94/M, a 14,95/M exacto (S13 `true` → contradicción; `false` → no estable) y a 100/M; C1 bajo el límite
    con S13 `false` (contradicción);
  - C3 y `no_evaluable` con S verdaderos, y C3 con un S que falla → no estable;
  - C2 coherente;
  - carga insuficiente con contradicciones; K y S sin medida;
  - recorrido completo de la CLI: rc 0, 1 y 2; JSON raíz no objeto; JSON mal formado o vacío; campo de más; clave
    duplicada; fichero inexistente. Ningún error habilita.
  - Contra el evaluador de `f6dc685` fallan 96 de los 129. Las pruebas de los tres fallos fallan por el defecto mismo
    (rc 0 en vez de 2 o 1); muchas otras, porque el campo `habilita_condicion_3` es nuevo
    (`evidencia/10-veredicto-contrato/regresion-contra-f6dc685.txt`).

## 5. Resultados desfavorables y conservación (sin cambios de fondo)

- **Una ejecución es una medida.** Identificador `E-carga-v2-<n>`, carpeta propia, `SHA256SUMS` sellado (P5) y
  publicación de su resultado, sea cual sea.
- **No se repiten ventanas hasta obtener una favorable.**
  - Un nuevo intento exige una orden nueva de Mark y una versión nueva del protocolo publicada antes.
  - Esa versión no puede bajar ningún umbral de K1–K5 ni de S1–S15.
  - Ninguna ventana sustituye a otra. El informe enumera todas, incluidas O12 y las desfavorables.
- **No estable:** se diagnostica en solo lectura y se publica. Una corrección es un cambio nuevo con su banco y sus
  criterios, seguido de otro E-carga.
- **Recursos y ejecución:**
  - P0, instrumentación, análisis y publicación: Claude, en solo lectura.
  - Arranque y parada de `cyberflow-lab.target` (`[CLIENTES adminclientes]`, `sudo -n`): Claude, **solo tras la orden
    de Mark**. Si pidiera contraseña, lo ejecuta Mark.
  - No hace falta ningún sudo con contraseña en Sensor1, el bastión ni srv-dmz.

## 6. Lo que E-carga no demostrará aunque salga «estable con carga suficiente»

- **Detección oportuna:** no hay ataques. Se mide en la 4C, en sombra.
- **Aplicación de restricciones y su efecto** sobre el ataque y sobre el tráfico legítimo: solo en la campaña B.
- **I5**, ni C0 en ninguna otra ventana.
- **Una tasa de falsas alarmas:** las señales de una hora son anecdóticas.
- **Que haya ráfagas del perfil errático:** K4b es informativo.
- **La causa de los descartes antiguos** del 03/04-nov.
- **La carga de producción:** la referencia es la del laboratorio, no la red de Francos.
- **La estabilidad más allá de una hora**, o en otra franja horaria.
