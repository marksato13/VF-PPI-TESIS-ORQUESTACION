# Etapa 1 · Objetivos y criterios de la candidata (versión 3)

**Fecha:** 1-nov-2026.

**Consolida** la entrega `c1de49d` (versión 2, que corregía `2482a40`). Los cambios están en [CAMBIOS-RESPECTO-c1de49d.md](CAMBIOS-RESPECTO-c1de49d.md) y [CAMBIOS-RESPECTO-2482a40.md](CAMBIOS-RESPECTO-2482a40.md).

**Decisiones:** véase la [matriz única D1–D8](DECISIONES.md).

**Alcance:** solo criterios, diseño de la evaluación, simulador offline y documentación. No se modificó el producto desplegado ni ningún servicio, modelo, umbral o regla. No hubo controles, ataques ni campañas, y el agente sigue inactivo.

> **Estado del protocolo de evaluación: NO CONGELADO.** D1 tiene resuelto el punto de aplicación (DC1), pero faltan sus comprobaciones técnicas. D3 está adoptada pero sin implementar en la candidata. Los valores de LIMIT de D6 están pendientes de confirmar ([DECISIONES.md](DECISIONES.md)).

---

## 1. Objetivo

**Objetivo del usuario:** mejorar el producto para detectar los ataques y aplicar una respuesta efectiva **mientras siguen activos**, con las menos falsas alarmas posibles y preservando el tráfico legítimo.

**Objetivo de desarrollo:** disponer de evidencia completa y lograr detección y respuesta oportunas en los **25 episodios** de cada campaña.

- Es una **meta que hay que comprobar**, no un resultado que se pueda garantizar.
- Todos los fallos, exclusiones y resultados tardíos se conservan y se publican.
- Los criterios deben reconocer un fallo real; no se ajustan para llegar a 25/25.

Una señal o una restricción posterior al fin del ataque **no cumple** el objetivo.

### 1.1 Poblaciones (no se mezclan)

| Población | Qué es | n | Uso |
|---|---|---|---|
| **Campaña 3B original** | Campaña A repetida en sombra, ejecutada el 1-nov (`67fc1f5`, `b714492`) | 25 episodios ejecutados | evidencia histórica, sin cambios |
| **Revisión del 3B** | Reanálisis con los criterios v2 (`191b043`, `f16b673`) | 15 episodios admitidos de los 25 | evidencia histórica, sin cambios |
| **Simulación de la Etapa 1** | La cadena de respuesta simulada sobre los registros de los 25 episodios (cada fila indica si el episodio está admitido) y sobre el control normal | 25 episodios + control de 33 min | **desarrollo**: dimensiona riesgos bajo supuestos. No es una campaña de respuesta. |
| **Evaluación independiente de la candidata** | Una campaña A nueva y una campaña B nueva, con la candidata congelada | **25 episodios nuevos por campaña** (5 por escenario) | prueba |

**Unidades distintas, que no se confunden:**

- **Entidad:** una dirección IP.
- **Ventana:** un registro entidad × window_end de 10 s, con 60 s de historia. Las ventanas se solapan y **no son ensayos independientes**.
- **Episodio:** una ejecución del generador. Es la **unidad de ensayo**.
- **Restricción:** una entrada nft con caducidad. En sombra, **hipotética**.

Por ejemplo, las «3–9 entidades legítimas restringidas» son entidades del **control normal**, no episodios de ataque, y sus restricciones son **hipotéticas** (simuladas, nunca aplicadas).

### 1.2 Campañas A y B

- **Campaña A (sombra):** compara IF, heurísticos e híbrido sobre ataques **completos** y mide la detección oportuna. 25 episodios.
- **Campaña B (respuesta):** comprueba la aplicación y el efecto de las medidas sobre el tráfico real. 25 episodios.
  - Un bloqueo corta el ataque, así que **B no sustituye a A** en la comparación de detectores.
  - Las ventanas posteriores a t_apl no se usan para comparar detectores.

---

## 2. Marcas temporales y métricas

| Marca | Definición | Fuente | En sombra |
|---|---|---|---|
| `t_inicio` | primer intento del generador | `marcas.jsonl` (evento `inicio`) | medida |
| `t_fin_ref` | horizonte fijado antes de ejecutar: bucles `t_inicio + 90 s`; nmap `t_inicio + D_ref` ([D8](DECISIONES.md)) | configuración | calculada |
| `t_fin_observado` | fin del generador, con su código de salida | `marcas.jsonl` (evento `fin`) | medida |
| **`t_fin_eval`** | **`min(t_fin_ref, t_fin_observado)`**. Una referencia fija no convierte en oportuna una actuación posterior al final real. | — | calculada |
| `t_det` | el registro con veredicto queda **disponible para consumidores** (`registro_escrito_en` del ciclo; si no se puede enlazar, `logged_at`, declarándolo) | motor | medida |
| `t_apl` | regla cargada en el host (hora y retorno del commit nft, más lectura del set) | agente instrumentado ([D7](DECISIONES.md)) | **no aplica** (en la Etapa 1 solo hay `t_apl_estimada`) |
| `t_efecto` | primer instante en que el destino deja de responder al origen o la tasa queda limitada, **mientras el generador sigue intentando** | SPAN/EVE, contadores nft y salida del generador | **no aplica** |

Hay que distinguir siempre: **decisión interna**, **disponibilidad** (t_det), **aplicación estimada**, **aplicación real** (t_apl) y **efecto** (t_efecto). La escritura en el feed no prueba la aplicación, y la aplicación no prueba el efecto.

**Métricas por episodio:**

- `t_det − t_inicio`;
- `t_apl − t_det`;
- `t_apl − t_inicio`;
- margen `t_fin_eval − t_apl`;
- `t_efecto − t_inicio`.

Las distribuciones se forman con los **totales de cada episodio**, nunca sumando medianas.

**Incertidumbre temporal:**

- relojes medidos en el 3B: |desfase| ≤ 0,0036 s ± 0,0006 s. Se usa ε = 0,01 s, y una sesión con desfase > 1 s se excluye;
- más la incertidumbre propia de cada marca.

Si la marca, con su incertidumbre, no permite ordenar el suceso frente a `t_fin_eval`, el caso es **indeterminado** y se publica como tal. No cuenta como éxito ni como fallo.

---

## 3. Qué significa cumplir el objetivo en un episodio

Las cinco condiciones se evalúan **por separado** y se publican todas. El episodio **cumple** solo si se cumplen todas las que aplican a su campaña.

| # | Condición | Se cumple si | En A (sombra) | En B (respuesta) |
|---|---|---|---|---|
| E1 | **Detección correcta y disponible durante el ataque** | Hay una señal atribuible (paquetes del origen al destino del episodio dentro de la ventana y de [inicio, fin]) **de la regla prevista** ([MATRIZ-ESCENARIOS.md](MATRIZ-ESCENARIOS.md)) con `t_det + ε < t_fin_eval`. Una señal de otra regla (p. ej. `brute_force` durante un escaneo) **no** valida la prevista: se publica aparte como «detección por otra regla», con la comprobación del comportamiento que la originó. | se evalúa | se evalúa (hasta t_apl) |
| E2 | **Restricción prevista aplicada** | `t_apl` real (evidencia del host) `+ ε < t_fin_eval`, con la acción prevista y limitada al origen | **no aplica** | se evalúa |
| E3 | **Efecto comprobado mientras el generador sigue intentando** | Desde `t_efecto < t_fin_eval`, las respuestas del destino al origen cesan (BLOCK o denegación DNS) o se reducen según el criterio de la familia (LIMIT), **y** consta que el generador siguió intentándolo después de `t_apl` (SPAN o salida) | **no aplica** | se evalúa |
| E4 | **Tráfico legítimo de control funcionando** | 0 fallos de transacciones de control atribuibles a una restricción en [t_inicio − 60 s, t_fin_eval + 90 s] | se registra (línea base) | se evalúa |
| E5 | **Caducidad o retirada verificada** | La restricción caduca o se retira y se verifica que el set no contiene al origen antes del siguiente episodio ([D5](DECISIONES.md)) | **no aplica** | se evalúa |

**E1 separa tres resultados** ([D3](DECISIONES.md)), que se publican por separado:

1. **anomalía del IF** a cada α (0,05, 0,03 y 0,01): ventana atribuible con ALERT del IF. El IF no clasifica familias y no se le exige `port_scan`;
2. **identificación por el heurístico previsto**: es la condición E1 de respuesta;
3. **decisión y aplicación de la respuesta**: E2 y E3.

La anomalía del IF cuenta como **detección del IF** en la comparación de detectores (campaña A), pero no sustituye al heurístico previsto en E1 ni produce respuesta con `if_senal`.

**Punto de aplicación por escenario:**

- srv-dmz (10.10.30.10) para HTTP y los escaneos;
- **DC1 (10.10.10.20)** para el DNS ([D1](D1-VIABILIDAD-DC1.md)). En DC1, E2 y E3 se refieren solo al puerto 53 del origen.

**Resultados posibles por episodio:**

- **cumple**;
- **fallo** (se publica qué condición falla);
- **indeterminado**;
- **fallo del experimento** (§5).

Una detección posterior al fin **no** cuenta como oportuna. En sombra, E2, E3 y E5 valen «no aplica»: no se inventan ni se convierten en resultados reales.

---

## 4. Diseño de 25 episodios ([D4](DECISIONES.md), decidida)

| Escenario | Episodios por campaña |
|---|---|
| DNS inusual | 5 |
| Inundación HTTP | 5 |
| Escaneo breve | 5 |
| Escaneo sostenido | 5 |
| Fuerza bruta HTTP | 5 |
| **Total** | **25** (campaña A) + **25** (campaña B) |

- **No** se aumentan automáticamente las repeticiones por familia.
- La meta es cumplir los 25 episodios de cada campaña según su propósito.
- **Con 5 por escenario se describe, no se garantiza.** Se publica la proporción de cada familia con su intervalo exacto de Clopper-Pearson **bilateral al 95 %** como medida de la incertidumbre:

| Cumplen / 5 | Intervalo 95 % |
|---|---|
| 5/5 | 0,478 – 1 |
| 4/5 | 0,284 – 0,995 |
| 3/5 | 0,147 – 0,947 |
| 2/5 | 0,053 – 0,853 |
| 1/5 | 0,005 – 0,716 |
| 0/5 | 0 – 0,522 |

- Para el total de 25 se puede dar el agregado (25/25 → 0,863 – 1; 24/25 → 0,796 – 0,999), **advirtiendo** que las familias son heterogéneas y que el agregado no describe a ninguna en particular.
- **No** se afirma una garantía poblacional del 90 % ni ninguna otra que la muestra no respalde.

*Antecedente estadístico, no adoptado:* la versión `2482a40` calculó que demostrar una proporción ≥ 0,80 al 95 % exigiría 14 episodios sin fallo, o 22 con uno, por familia. Esa propuesta **no se adopta** (D4).

**Contabilidad obligatoria por campaña:** planificados, ejecutados, admitidos y excluidos, con un motivo por episodio. Referencia 3B (histórica):

| Planificados | Ejecutados | Admitidos (v2) | Excluidos |
|---|---|---|---|
| 25 | 25 | 15 | 10 |

Los excluidos son 9 por `kernel_drops` de Suricata (inund. r1 +11, r2 +111, r3 +1483, r4 +182; dns r3 +28, r5 +100; fuerza bruta r2 +97, r3 +61; breve r4 +58) y escaneo_sostenido-r1, cuyo fin + 90 s sale del inventario por 5,8 s.

---

## 5. Fallos del experimento y fallos del detector

| Tipo | Ejemplos | Tratamiento (fijado de antemano) |
|---|---|---|
| **Fallo del experimento** | generador con código ≠ 0 o que termina antes por un fallo propio; herramienta ausente; destino caído antes del inicio; relojes > 1 s; reinicio de un componente en [inicio − 230 s, fin + 90 s]; hueco de inventario; fuente de clase C2 o C3 (§6); restricción del origen vigente al inicio ([D5](DECISIONES.md)) | El original **se conserva** y se publica con su motivo. Se permite **una** repetición con identificador nuevo (`rN-bis`), en la misma posición del orden aleatorio, y ambos se publican. Si la repetición también falla por el experimento, el escenario queda con menos de 5 admitidos, y así se publica. |
| **Fallo del detector o de la cadena** | episodio admitido en el que no se cumple E1–E5 | **cuenta como fallo y no se repite.** No se sustituye por un éxito. |

La lista de causas de fallo del experimento es **cerrada**: no se añaden causas después de ver resultados.

---

## 6. Calidad de la evidencia

Se usa la **cadena v2** (`191b043`) sin flexibilizar ninguna tolerancia para admitir 25 episodios. Hay tres dimensiones distintas, que se publican por separado:

1. **Continuidad de las fuentes:** los PCAP se suceden sin hueco; el pulso de stats del EVE es continuo.
2. **Cobertura del procesamiento:** ventanas requeridas frente al inventario (`decidida_a_tiempo`, `decidida_tardia`, `no_evaluada`, `ausente`), con 230 s de historia previa y fin + 90 s posteriores.
3. **Calidad de los datos:** descartes de Suricata (`kernel_drops`) y de tcpdump.

El hueco de más de 20 s entre escrituras del motor es **solo informativo**. La pérdida se establece contra el inventario.

### 6.1 Clases por descartes (corregidas)

**El IF depende también del EVE.** Contrato verificado ([CONTRATO-CARACTERISTICAS.md](CONTRATO-CARACTERISTICAS.md)): de sus **28** características, **9 son L3 y 8 son L4** (las 17 del PCAP), y **11 son L7 del EVE**:

- `http_error_ratio_60s`, `dns_nxdomain_ratio_60s`, `tls_session_rate_60s` (orden 12–14);
- `http_request_rate_60s`, `http_method_entropy_60s`, `http_auth_failure_ratio_60s`, `dns_query_rate_60s`, `unique_dns_name_ratio_60s`, `tls_handshake_failure_ratio_60s`, `tls_version_ratio_60s`, `http_status_5xx_ratio_60s` (orden 21–28).

La versión 2 decía «12 L7»: era un error de conteo y la lista ya tenía 11 nombres. Corregirlo no cambia las entradas del modelo.

Los descartes de Suricata pueden alterar las entradas del IF, además de las de los heurísticos L7.

| Clase | Condición | Qué se puede afirmar | Qué NO |
|---|---|---|---|
| **C0 completa** | 0 descartes de Suricata y de tcpdump en el periodo que afecta al episodio | todo lo que permitan las demás dimensiones | — |
| **C1 EVE degradado** | `kernel_drops` > 0 y tcpdump = 0 | Una **detección observada** se conserva con su limitación («se observó una señal en t con el EVE degradado»). | Ausencia de ataque o de señal; sensibilidad completa; latencia mínima; evaluación completa del IF o de los heurísticos L7; tasas completas de falsas alarmas. **C1 no autoriza la evaluación completa del IF.** |
| **C2 paquetes degradados** | descartes de tcpdump > 0 | solo las detecciones observadas, con su limitación | todo lo anterior, también para las características L3/L4 |
| **C3 no evaluable** | hueco de inventario, reinicio o relojes fuera de límite | nada sobre el detector (es un fallo del experimento) | — |

**Afirmaciones sobre características no afectadas:** solo con una justificación **específica**. Por ejemplo, demostrar que ningún intervalo de stats con descartes solapa los 60 s de historia de **esa** ventana. No se generalizan.

**Coincidir con un replay que usa las mismas fuentes no demuestra ausencia de pérdidas:** el replay hereda la pérdida.

**Población principal** de cada campaña: episodios C0 con integridad v2 apta. C1 y C2 se publican aparte, con su clase.

### 6.2 Igualdad de score frente a igualdad de características

El 3B comparó score, decisión y `packet_count_10s`, pero las 28 características no se registran. Cualquier cambio de **captura o extracción** de las Etapas 2 y 3 debe comparar **las 28 entradas del IF** en la prueba offline, **en las mismas ventanas y con los mismos datos disponibles**. Una diferencia solo es admisible si se explica por datos que antes no estaban disponibles y se documenta.

Esto **no** se aplica a las **señales heurísticas nuevas** (por ejemplo, la regla temprana de escaneo): son una mejora deliberada, y se les exige corrección y ausencia de regresiones, no identidad con las señales antiguas. Las 3 características L2 del esquema ampliado **no** se incorporan al IF.

---

## 7. Restricciones de este encargo

- No se edita el Word.
- No se sobrescribe ninguna evidencia histórica: 3A, 3B, la revisión y `2482a40` se conservan en Git.
- No se cambia el sistema desplegado, no se genera tráfico de ataque y no se activan bloqueos.
