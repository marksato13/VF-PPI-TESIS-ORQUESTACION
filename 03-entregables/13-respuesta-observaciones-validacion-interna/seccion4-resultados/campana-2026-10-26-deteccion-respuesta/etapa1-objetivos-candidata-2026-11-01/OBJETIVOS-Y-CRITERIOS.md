# Etapa 1 · Objetivos y criterios de la candidata

**Fecha:** 1-nov-2026.
**Alcance:** solo criterios, diseño de evaluación y documentación. No se implementó ninguna mejora, no se desplegó nada, no se lanzaron ataques ni controles y no se activó el enforcement.
**Datos usados:** solo los registros ya publicados de la campaña A (3A y 3B) y su revisión (`f16b673`). Las referencias exactas están en [REFERENCIAS.md](REFERENCIAS.md).

> **Estado del protocolo: NO CONGELADO.** Quedan decisiones esenciales abiertas (§7). Los criterios marcados **provisional** no se aplicarán como regla de aprobación mientras Mark no los confirme por escrito **antes** de ver datos nuevos.

---

## 1. Objetivo operativo

Detectar el ataque y **aplicar una respuesta efectiva mientras el ataque sigue activo**.

Una señal, o una restricción, que llega después del fin del ataque **no cumple** el objetivo, aunque sea correcta. En sombra, en cambio, puede contar como detección tardía.

Este objetivo se descompone en tres preguntas. Cada una se responde por separado y ninguna sustituye a otra:

| # | Pregunta | Se responde con | Campaña |
|---|---|---|---|
| Q1 | ¿El detector produce, **antes del fin**, una señal atribuible con la acción prevista? | t_det frente a t_fin_programado | A (sombra), repetida con la candidata congelada |
| Q2 | ¿La cadena **aplica** esa acción en el host protegido antes del fin? | t_apl frente a t_fin_programado | B (respuesta) |
| Q3 | ¿La acción **produce efecto** sobre el ataque, sin dañar el tráfico legítimo? | t_efecto y transacciones de control | B (respuesta) |

### 1.1 Separación entre la campaña A y la campaña B

- **Campaña A (sombra).** El agente está inactivo y nadie corta tráfico. Sirve para **comparar detectores** (IF a tres α, heurísticos e híbrido) con el ataque completo a la vista. Es la única que permite medir falsos negativos y la latencia de detección sin que la respuesta altere lo observado.
- **Campaña B (respuesta).** El agente está activo. Sirve para medir t_apl, t_efecto y el daño colateral.
  - Un bloqueo corta el tráfico, de modo que después del corte el detector deja de ver el ataque completo. Por eso **la campaña B no sustituye la comparación de detectores**, y sus ventanas posteriores al corte no se usan para evaluar detectores.
- Los resultados anteriores **se conservan tal cual**: 3A (`1b35bf6`), 3B (`67fc1f5`, `b714492`), criterios v2 (`191b043`) y revisión (`f16b673`). Esta etapa no reescribe ninguna cifra publicada.
  - El presupuesto temporal y el de falsas alarmas **reutilizan** esos registros como material de desarrollo.

---

## 2. Marcas temporales

Todas las marcas están en UTC y en el reloj de cada host. La incertidumbre de relojes se trata en §2.3.

| Marca | Definición | Fuente | En sombra (A) |
|---|---|---|---|
| `t_inicio` | El generador lanza el primer intento del episodio | `marcas.jsonl` (Kali), evento `inicio`, `reloj.pared_utc` | se mide |
| `t_fin_programado` | Fin del ataque fijado **antes** de ejecutarlo. En los bucles de 90 s (DNS, HTTP, fuerza bruta) es `t_inicio + 90 s`. En nmap, que termina de forma natural, es `t_inicio + D_ref(familia)` (§2.2). | configuración congelada | se calcula |
| `t_fin_observado` | El generador termina, con su código de salida | `marcas.jsonl`, evento `fin` | se mide |
| `t_det` | La señal con veredicto (LIMIT/BLOCK, según `_verdicto_de` del publicador desplegado) queda **disponible para consumidores**: el ciclo del motor ha escrito el registro en `motor_decision.log` (`registro_escrito_en` del ciclo; si no se puede enlazar, `logged_at`, declarándolo). | `motor_decision.log` + `ciclos.jsonl` | se mide |
| `t_apl` | La regla nft que restringe al origen está **cargada en el host protegido** (commit nft correcto). | registro del agente + `nft list set` con marca de tiempo (Etapa 2/4) | **no aplica** |
| `t_efecto` | Primer instante desde el que el tráfico del ataque deja de producir efecto en el destino: sin respuestas del servicio, o con la tasa limitada. | SPAN/PCAP + EVE (respuestas del destino) + contadores nft | **no aplica** |

**Distinciones obligatorias:**

1. **Decisión interna ≠ disponibilidad.** El motor decide en memoria durante el ciclo y la decisión solo existe para el publicador cuando se escribe. t_det es la escritura (`registro_escrito_en`), no `inicio_ciclo` ni `window_end`.
2. **Escritura ≠ aplicación.** Que el feed contenga la IP no prueba nada en el host. t_apl exige evidencia del host: el código de retorno del commit nft y la lectura del set con su `expires`.
   - Hoy el agente no registra la hora del commit con precisión suficiente: es trabajo de la Etapa 2.
3. **Aplicación ≠ efecto.** Una regla cargada puede no afectar al ataque. Le ocurre a un LIMIT de 100 pps frente a un flujo menor, o a un LIMIT en srv-dmz frente a un ataque DNS dirigido a DC1.
   - t_efecto se mide en el tráfico, no en la configuración.

### 2.1 Métricas

| Métrica | Fórmula | Unidad |
|---|---|---|
| Latencia de detección | `t_det − t_inicio` | s |
| Latencia de la cadena | `t_apl − t_det` | s |
| Latencia de respuesta | `t_apl − t_inicio` | s |
| **Margen de actuación** | `t_fin_programado − t_apl`. Si es positivo, la respuesta llega con el ataque activo. | s |
| Tiempo hasta el efecto | `t_efecto − t_inicio` (y `t_efecto − t_apl`) | s |

- Cada métrica se calcula **por episodio**. Las distribuciones se construyen con los totales de cada episodio: **nunca sumando medianas de tramos**.
- En sombra, `t_apl` y `t_efecto` valen «no aplica», nunca 0 ni vacío. Cualquier t_apl de la campaña A es una **estimación** y se publica marcada como tal.

### 2.2 El fin no se redefine por el corte

- En la campaña B, un BLOCK hace que nmap espere *timeouts*, y el generador puede tardar **más** en terminar. Si el fin se tomara del generador, una respuesta tardía parecería oportuna.
- Por eso el éxito se mide **siempre contra `t_fin_programado`**, que se fija antes de ejecutar:
  - **Bucles de 90 s:** `t_inicio + 90 s` (configurado en `escenarios.json`).
  - **nmap:** `D_ref(familia)` = **duración natural mínima** observada en la campaña A (3B).
    - Escaneo breve: 17,59 s (observados 17,59 / 17,59 / 17,99 / 17,99 / 17,99).
    - Escaneo sostenido: 65,52 s (observados 65,52 / 65,72 / 65,77 / 66,12 / 66,31).
    - Se elige la mínima porque es la más exigente. **Estado: provisional.** Alternativas: la mediana, o la duración de la misma repetición en una pasada en sombra.
- `t_fin_observado` se publica junto al programado, con la **evidencia de intentos continuados** después del corte: SYN del origen en el SPAN sin respuesta del destino, y salida del generador.
- Un episodio cuyo generador termina **antes** de `t_fin_programado` por un fallo propio (código de salida ≠ 0, herramienta ausente) es un **fallo del experimento**, no del detector (§6).

### 2.3 Incertidumbre de relojes

- **Medida en el 3B** (`relojes-3b.log`): |desfase| ≤ 0,0036 s ± 0,0006 s en el sensor, la Kali, srv-dmz y los clientes, frente al bastión con NTP. Las comparaciones usan ε = 0,01 s.
- **Regla:** cuando |t_fin_programado − t_apl| ≤ ε + la incertidumbre de la propia marca, el episodio es **indeterminado**.
  - En la campaña A, la incertidumbre de t_apl es el intervalo [inferior, superior] de la estimación (fase del publicador y arranque del agente). Si ese intervalo contiene el fin, el caso es **indeterminado**.
  - Un indeterminado no cuenta como éxito ni como fallo y se publica en una fila propia.
- **Requisito previo de cada sesión:** medición de relojes **antes y después**, con un límite de 1 s (criterio vigente desde el 3A). Un episodio fuera de ese límite se excluye por evidencia, no por resultado.

---

## 3. Calidad de la evidencia (criterios previos al análisis)

Se reutiliza **la cadena v2** (`191b043`, herramientas en `revision-3b-2026-11-01/herramientas/`). No se cambia ninguna tolerancia para aprobar.

| Elemento | Criterio | Clasificación posible |
|---|---|---|
| PCAP | Cada fichero existe, es legible y su hash coincide. Selección por la **regla del motor** (último paquete decodificado), no por la última trama. | verificado / no verificado |
| EVE | Existe, el hash coincide y el pulso de `stats` es continuo (intervalo 8 s) | verificado / no verificado |
| Integridad del episodio | Los requisitos de `verificar_integridad_v2.py` | apto / no apto, con un motivo por requisito |
| Relojes | Antes y después de la sesión, \|desfase\| ≤ 1 s | dentro / fuera |
| Reinicios | Sin reinicio del motor, de Suricata, de tcpdump ni del agente dentro de [inicio − 230 s, fin + 90 s] (journal) | sin reinicio / con reinicio |
| Ventanas | Contra el **inventario**: `decidida_a_tiempo`, `decidida_tardia`, `no_evaluada` (evento explícito), `ausente` | conteos por estado |
| Descartes de Suricata | `kernel_drops` por intervalo de stats que solapa el episodio | **ver §3.1** |
| Descartes de tcpdump | `dropped by kernel` / `dropped by interface` (SIGUSR1 y cierre) | 0 / > 0 |
| Cobertura previa | 230 s de historia antes del inicio, dentro del inventario | cubre / no |
| Cobertura posterior | fin + 90 s dentro del inventario | cubre / no |
| Reconstrucción | El replay reproduce score, decisión y paquetes. **No** demuestra las 28 características, que no se registran (§3.2). | exacta / difiere, con el campo |

**El hueco > 20 s entre escrituras del motor es solo informativo.** Con el motor incremental, la cadencia de escritura ronda los 20 s incluso sin carga (revisión 3B). La pérdida solo se establece contra el inventario (`ausente`).

### 3.1 «Informar descartes» no equivale a «fuente completa»

Cada episodio con descartes se clasifica, y la clase limita lo que se puede afirmar:

| Clase | Condición | Afirmaciones permitidas |
|---|---|---|
| **C0 completa** | 0 descartes de Suricata y de tcpdump en el periodo | todas |
| **C1 degradada, solo L7** | Hay kernel_drops de Suricata y tcpdump tiene 0, con el PCAP verificado | detección por IF (PCAP) y tiempos de cadena. **No** se afirma ausencia de señal de heurísticos L7 (DNS, HTTP, auth) ni tasa L7 completa. |
| **C2 degradada, paquetes** | Descartes de tcpdump > 0 | solo afirmaciones positivas («se detectó en t»). Ninguna afirmación de ausencia ni de latencia mínima. |
| **C3 no evaluable** | Hay hueco de inventario, reinicio o relojes fuera de límite | ninguna sobre el detector. El episodio cuenta como **fallo del experimento**. |

Solo los episodios **C0** forman la población principal. C1 y C2 se publican aparte, con su clase.

### 3.2 Igualdad de score y paquetes ≠ igualdad de características

- La reconstrucción del 3B comparó score, decisión y `packet_count_10s` en 12 667 claves, y 702/702 decisiones de ataque se recalcularon exactas con la v2. Las 28 características **no se registran** en el motor.
- Esa igualdad es compatible con diferencias en características que no muevan el score.
- **Para la candidata:** si una mejora de la Etapa 3 altera la extracción, la prueba offline debe comparar **las 28 características** (volcadas por la herramienta de recálculo), no solo el score.

### 3.3 Contabilidad obligatoria de episodios

Se publican siempre cuatro cifras con sus motivos: **planificados, ejecutados, admitidos y excluidos**. En el 3B (referencia):

| | n | Detalle |
|---|---|---|
| Planificados | 25 | 5 escenarios × 5 repeticiones, semilla 20261026 |
| Ejecutados | 25 | 25 con estado `completo` |
| Admitidos (v2) | 15 | dns r1, r2, r4 · breve r1, r2, r3, r5 · sostenido r2, r3, r4, r5 · fuerza bruta r1, r4, r5 · inundación r5 |
| Excluidos | 10 | 9 por kernel_drops de Suricata: inund. r1 +11, r2 +111, r3 +1483, r4 +182 · dns r3 +28, r5 +100 · fuerza bruta r2 +97, r3 +61 · breve r4 +58. Y sostenido r1, porque fin + 90 s sale del inventario por 5,8 s. |

La población admitida de la inundación HTTP es **1/5**. Ninguna afirmación sobre esa familia es posible sin corregir antes la captura (Etapa 2).

---

## 4. Criterios cuantitativos por familia

### 4.1 Objetivo deseado y evidencia mínima

- **Objetivo deseado** (lo que se busca): la candidata responde **antes del fin** en ≥ 90 % de los episodios de cada familia con punto de aplicación, sin restricciones sobre tráfico legítimo atribuibles a la respuesta.
- **Evidencia mínima** (lo que basta para afirmarlo): la **cota inferior unilateral de Clopper-Pearson al 95 %** de la proporción de éxitos debe ser **≥ 0,80**.
  - Se elige 0,80, y no 0,90, porque demostrar 0,90 exige ≥ 29 episodios por familia sin fallos (145 en total) y no cabe en una campaña de laboratorio.
  - El 0,80 se fija **ahora, antes de medir**. **Estado: provisional, pendiente de Mark (D4).**

Cota inferior (95 %, unilateral) según el número de repeticiones n y de fallos f. Valores calculados, no supuestos:

| n | f = 0 | f = 1 | f = 2 |
|---|---|---|---|
| 5 | 0,549 | 0,343 | 0,189 |
| 10 | 0,741 | 0,606 | 0,493 |
| 14 | **0,807** | 0,703 | 0,615 |
| 15 | 0,819 | 0,721 | 0,637 |
| 20 | 0,861 | 0,784 | 0,717 |
| 22 | 0,873 | **0,802** | 0,741 |
| 29 | **0,902** | 0,847 | 0,798 |

**Consecuencia:**

- Con las **5 repeticiones** del diseño actual no se puede demostrar nada mejor que el 55 % ni siquiera con 5/5. Por eso el 3B no confirma la eficacia: solo la describe.
- **Propuesta (provisional, D4):**
  - **n = 14** episodios admitidos (C0) por familia. Con 14/14 éxitos queda demostrado ≥ 0,80.
  - Con un fallo, el criterio no se cumple con 14. Ampliar después de ver el fallo sería cambiar el criterio para aprobar, y está prohibido.
  - Un diseño en dos etapas («si hay 1 fallo en 14, ejecutar 8 más y exigir ≤ 1 en 22») **se descarta**. Si la proporción real fuera 0,80, aprobaría con probabilidad 0,044 + 0,154 × 0,168 = **0,070**, por encima del 0,05 nominal.
  - **Alternativa equivalente:** n = 22 fijo con ≤ 1 fallo, que aprobaría con probabilidad **0,048** si la proporción real fuera 0,80. Cuesta 8 episodios más por familia y tolera un fallo. Mark elige una de las dos **antes** de la campaña (D4).
- **Episodios ejecutados frente a admitidos.** Con la tasa de exclusión del 3B (10/25), 14 admitidos podrían exigir ~23 ejecutados por familia. La Etapa 2 debe bajar los descartes; si no, la campaña B no es viable en una sesión.

### 4.2 Criterio por familia (resumen; detalle en [MATRIZ-ESCENARIOS.md](MATRIZ-ESCENARIOS.md))

| Familia | Éxito | Fallo | Indeterminado | Estado |
|---|---|---|---|---|
| Escaneo sostenido | BLOCK aplicado con margen > 0 y efecto (sin SYN-ACK del destino al origen) antes de `t_fin_programado` | t_apl o t_efecto ≥ t_fin, o no hay acción | intervalo o ε cruzan el fin | definido (falta n, D4) |
| Fuerza bruta HTTP | BLOCK aplicado y sin respuestas 401/200 del servicio al origen antes del fin | ídem | ídem | definido (falta n, D4) |
| Inundación HTTP | Restricción aplicada y tasa de respuestas HTTP al origen reducida ≥ 50 % frente a los 10 s previos, antes del fin | ídem | ídem | **provisional**: falta decidir la acción (D3) y el umbral de efecto |
| Escaneo breve | Igual que el sostenido | ídem | ídem | **provisional**: con la arquitectura actual es imposible (§5 del presupuesto). Objetivo pendiente (D2). |
| DNS inusual | No hay punto de aplicación (el ataque va a DC1 y el agente está en srv-dmz) | — | — | **pendiente (D1)**. Hasta decidirlo, solo detección (Q1). |

---

## 5. Falsas alarmas y daño colateral

Véase [PRESUPUESTO-FALSAS-ALARMAS.md](PRESUPUESTO-FALSAS-ALARMAS.md). Resumen de criterios:

- Se publican **cuatro medidas separadas**:
  1. señales sobre tráfico normal;
  2. propuestas LIMIT/BLOCK del publicador;
  3. restricciones aplicadas a entidades legítimas (t_apl en el host);
  4. fallos de transacciones legítimas de control.
- El DNS (10.10.10.20) **sigue en el denominador** de las señales, aunque el publicador nunca lo restrinja.
- Los tres α (0,05 / 0,03 / 0,01) siguen siendo **candidatos sin elegir**. Elegir α no corrige los heurísticos: las 88 señales `dns_entropy` sobre el resolvedor no dependen de α.

---

## 6. Fallos del experimento frente a fallos del detector

| Tipo | Ejemplos | Tratamiento |
|---|---|---|
| **Fallo del experimento** | Generador con código ≠ 0 o que termina antes de lo programado; herramienta ausente; servicio destino caído antes del inicio; relojes fuera de límite; reinicio de un componente; hueco de inventario; descartes C2/C3; restricción **previa** vigente al inicio (§6.1) | El episodio se **excluye** con su motivo y se **repite** con un identificador nuevo (rN-bis), sin borrar el original. No cuenta en el éxito ni en el fallo. |
| **Fallo del detector o de la cadena** | Episodio C0 sin señal antes del fin; señal sin publicar; publicada sin aplicar; aplicada sin efecto antes del fin | Cuenta como **fallo**. No se repite para sustituirlo. |

Las reglas de exclusión de esta tabla son **las únicas** y no se añaden después de ver resultados.

### 6.1 Contaminación entre episodios: hallazgo del presupuesto

- La simulación secuencial del 3B con el código desplegado reproduce exactamente el feed y el estado de escalada reales (`pruebas/test_presupuesto_e2e.py`). Muestra que el origen 10.10.20.30 ya estaba en **nivel 3** de escalada antes del primer episodio, por las pruebas previas del día.
- Con el agente activo, **24 de los 25 episodios habrían empezado con un BLOCK de 3600 s ya aplicado** (tabla 3 de [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md)). En la campaña B no se mediría nada.
- **Requisito de diseño** (decisión D5): entre episodios, el estado de escalada del origen y los sets nft de srv-dmz deben quedar **vacíos y verificados** antes de `t_inicio`.
  - Opciones: un procedimiento de retirada humana documentado, o un origen distinto por episodio. **No** vale usar la IP del generador como atajo de detección.
  - Si al inicio hay una restricción vigente, el episodio es un **fallo del experimento**.

---

## 7. Decisiones pendientes (impiden congelar el protocolo)

| Id | Decisión | Opciones | Quién |
|---|---|---|---|
| **D1** | Punto de aplicación para el DNS inusual | (a) agente en DC1 (Windows: requiere otro agente, fuera del alcance actual); (b) respuesta en el pfSense, que contradice la norma de no tocar el cortafuegos; (c) la familia queda **solo de detección** en la campaña B | Mark |
| **D2** | Objetivo del escaneo breve (≈ 18 s) | (a) mantener «antes del fin» y aceptar que exige cambios de arquitectura (Etapas 2 y 3); (b) redefinirlo como contención de la **reincidencia** (fuera del objetivo operativo, se declararía como tal) | Mark |
| **D3** | Acción ante la anomalía del IF | (a) LIMIT como hoy, incompatible con cualquier presupuesto de falsas alarmas razonable (§ presupuesto FA); (b) el IF solo señala y la respuesta queda en los heurísticos; (c) LIMIT por persistencia (k de n ventanas) | Mark |
| **D4** | Evidencia mínima y n | 0,80 al 95 % con n = 14 y ampliación a 22 (propuesta) u otra | Mark |
| **D5** | Limpieza entre episodios | retirada humana verificada / otro diseño | Mark |
| **D6** | Presupuesto operativo de falsas alarmas | propuesta provisional en PRESUPUESTO-FALSAS-ALARMAS.md | Mark |
| **D7** | Activar el agente para la campaña B y añadir `counter` a las reglas nft (medir el efecto) | cambio de producto y de host: sudo de Mark | Mark |
| **D8** | `D_ref` de nmap: mínima (propuesta) / mediana | — | Mark |
