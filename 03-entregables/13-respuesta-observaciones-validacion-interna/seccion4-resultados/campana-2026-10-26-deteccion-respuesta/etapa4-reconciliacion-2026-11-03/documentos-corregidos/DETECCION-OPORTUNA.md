# Detección oportuna por familia de ataque: lo demostrado y lo que falta (2026-11-02)

> **Copia corregida (reconciliación 2026-11-03).** El original se conserva sin cambios en
> `etapa4-correcciones-2026-11-02/DETECCION-OPORTUNA.md`. Enmiendas:
> 1. Endpoint de fuerza bruta: `http://10.10.30.10:18081/auth` (servicio `ppi-brute-lab`, `PUERTO=18081`,
>    `RUTA=/auth`, leído en srv-dmz el 2026-11-04), no `/login`. El resto de la documentación y los guiones
>    (`c05`, `escenarios-4c.json`, `trafico_observado.py`) ya usaban `:18081/auth`.
> 2. Las columnas «Oportunas V/R» cuentan **cualquier** emisión (IF o cualquier regla). Se añade §3 bis con la
>    separación por componente para V (3B revisado), recalculada con `herramientas/analizar_3b.py` de la
>    reconciliación. Las categorías, la población y el recuento total son idénticos a los publicados.

> Solo se reúne lo ya publicado. **El detector no se ha tocado** para esta tabla (modelo, escalador, 28
> características, α 0,05 / 0,03 / 0,01 y reglas iguales). Ninguna cifra procede de una ejecución nueva.

## 1. Definiciones que se aplican

- **Oportuna:** hay una señal atribuible al ataque cuya **disponibilidad** (`disponible_utc`, el registro escrito
  por el ciclo del motor) es ≤ fin del episodio del generador (+ ε 0,01 s). OBJETIVOS-Y-CRITERIOS v3.
- **Referencia temporal** de la columna «1.ª»: segundos desde el **inicio del generador** (`marcas.jsonl`, reloj de
  la Kali) hasta la disponibilidad de la primera señal oportuna (reloj del Sensor1), `analizar_3b.py`
  `latencia_disponible_s`. Las duraciones de referencia son: escaneo breve ≈ 18 s; los otros cuatro, 60–120 s
  (`escenarios.json`).
- **Población principal:** episodios con observación completa (inventario, fuente, integridad, destino). Fuera de
  ella, los resultados se publican aparte y no cuentan.
- **Emisión real:** decisión emitida por el motor en vivo, separada de las 7 configuraciones derivadas.
- **Detección ≠ respuesta.** En el 3B y en el replay el sistema estaba en **sombra**: nadie aplicó nada. Una
  propuesta del publicador no es un bloqueo aplicado. Una alerta disponible después del fin **nunca** es oportuna.

## 2. Fuentes

| Id | Qué | Versión del motor | Dónde |
|---|---|---|---|
| **V** | 3B en vivo, revisado (criterios v2 fijados antes, `191b043`) | `24f8a80` (Sensor1, 1-nov) | [`revision-3b-2026-11-01/resultados/analisis-revisado/TABLA-3B.md`](../../revision-3b-2026-11-01/resultados/analisis-revisado/TABLA-3B.md), INFORME §5 |
| **R** | Replay del 3B con el motor del cierre de la Etapa 3 | `49a29db` (antecesor de `ec78ca5`; mismo motor) | [`etapa3-cierre-tecnico-2026-11-02/resultados/analisis-3b-cierre/TABLA-3B.md`](../../etapa3-cierre-tecnico-2026-11-02/resultados/analisis-3b-cierre/TABLA-3B.md) |
| **Q** | Vía rápida sobre los 5 escaneos breves grabados del 3B | `585da7b` / corrección `ec78ca5` | [`etapa3-deteccion-temprana-2026-11-02/VALIDACION.md`](../../etapa3-deteccion-temprana-2026-11-02/VALIDACION.md) §5 |
| **B** | Banco de aplicación (alternativa C), contenedor, reinyección de los escaneos | `ec78ca5` | [`etapa3-cierre-tecnico-2026-11-02/resultados/bateria-c/TABLA.md`](../../etapa3-cierre-tecnico-2026-11-02/resultados/bateria-c/TABLA.md) y `bateria-c-vlan/` |
| **A** | `auth_failure` por la vista HTTP: decisiones tardías retiradas | `ec78ca5` | [`etapa3-cierre-tecnico-2026-11-02/COMPARACION-REFERENCIA.md`](../../etapa3-cierre-tecnico-2026-11-02/COMPARACION-REFERENCIA.md) §3 |

## 3. Tabla

Episodios de la población principal (15 de 25 en V y en R; los mismos 15).

| Familia | Señal real del ataque | Principal | Oportunas V (emisión real) | Oportunas R (emisión real) | 1.ª (s) V / R | Aplicación o efecto | Falta confirmar |
|---|---|---|---|---|---|---|---|
| **DNS inusual** | Ráfaga de consultas del origen al DNS `10.10.10.20` (Suricata `dns`) | r1, r2, r4 | **3/3** (HEUR/HIB; IF solo r1) | **3/3** (HEUR/HIB; IF solo r1) | r1 17,2 / 12,8; r2 25,9 / 22,0; r4 23,9 / 19,0 | **Solo detección.** LIMIT DNS **no aplicado** en ningún sitio; banco del LIMIT: 734/1 044 consultas del atacante recortadas, 0/428 legítimas (OBSERVACION-DNS §1), **no** es efecto en el laboratorio | Detección con `ec78ca5` en vivo (4C); observación DNS de 7 días antes de cualquier LIMIT; efecto real solo en campaña B |
| **Inundación HTTP** | Peticiones HTTP masivas a `10.10.30.10` | r5 (r1–r4 fuera por fuente degradada/integridad) | **1/1** | **1/1** | 29,3 / 10,3 | **Solo detección** (sombra) | Población principal con más de un episodio (4C, con salud C0); aplicación y efecto en campaña B |
| **Escaneo breve** (≈ 18 s) | SYN sin ACK del origen a varios puertos de `10.10.30.10` | r1, r2, r3, r5 | **1/4** (r1); r2, r3, r5 solo posteriores | **2/4** en emisión real (r1, r3); r2, r5 solo posteriores; depende de la configuración | r1 16,4 / 12,0; r3 — / 16,4 | Q: la vía rápida tiene evidencia a 13,2 s del inicio, **4,4–4,75 s antes del fin**, en 5/5 (también r4). B: regla aplicada **antes del último SYN** en 60/60 (p50 aplicada 0,8–1,5 s; margen mín. 2,9 s), pero **90–99 % de los SYN llegan después de aplicar**: el banco **no prueba que el escaneo se detenga** ni que la respuesta tenga efecto | Vía rápida **en vivo** (4C, medida aparte); referencia contra la ráfaga observada (PROTOCOLO-4C §4); efecto real solo en campaña B |
| **Escaneo sostenido** | SYN del origen a muchos puertos durante 60–120 s | r2, r3, r4, r5 | **4/4** | **4/4** | r2 26,6 / 23,2; r3 22,0 / 7,4; r4 22,0 / 16,6; r5 35,6 / 20,5 | **Solo detección** (sombra) | Repetir con `ec78ca5` en vivo (4C); aplicación y efecto en campaña B |
| **Fuerza bruta HTTP** | Peticiones con 401 a `http://10.10.30.10:18081/auth` del endpoint `ppi-brute-lab` (vista HTTP con tramas en el cable) | r1, r4, r5 | **3/3** | **3/3** | r1 25,1 / 9,8; r4 18,4 / 2,5; r5 23,7 / 8,2 | **Solo detección.** Se separan las decisiones: (a) **durante** el ataque, con evidencia HTTP válida → las de esta tabla; (b) en el replay con la referencia de la Etapa 3 (`585da7b`) había **36 decisiones tardías** de `auth_failure_heuristic` (la mayoría 61–118 s después del fin, 0 peticiones válidas, registro tardío de Suricata) y **8 renovaciones** del bloqueo sin evidencia: `ec78ca5` las **retira** (A §3.1–3.2) y ninguna contaba como oportuna; (c) **5 renovaciones** que se conservan a 31–38 s del fin, con evidencia válida en su ventana, son **posteriores**: no cuentan como oportunas | Que el registro en vivo traiga `decision_if` y `auth_failure` (Sensor1 corre `24f8a80`); aplicación y efecto en campaña B |

**Totales de la población principal:** V 12/15 con emisión real oportuna; R 13/15. Las diferencias están en el
escaneo breve (r3) y en las latencias (R es un replay con el motor del cierre y disparo por eventos; V fue en
vivo con `24f8a80`). No se atribuye la diferencia a una causa concreta. Fuera de la población hay 9 de 10 oportunas en V; la que falta es `escaneo_breve-r4`.

## 3 bis. Separación por componente en V (reconciliación 2026-11-03)

Población principal de V (15 episodios). Un episodio cuenta en una columna si tiene al menos una emisión oportuna
y atribuible de ese componente. Fuente: `evidencia/reanalisis-3b-etiquetas/ETIQUETAS-3B-REVISADO.md`.

| Familia | Episodios | Cualquier emisión (cifra publicada) | Señal IF | Regla prevista | Regla prevista |
|---|---|---|---|---|---|
| DNS inusual | 3 | 3 | 1 | 3 | `dns_entropy` |
| Escaneo breve | 4 | 1 | 1 | **0** | `port_scan` |
| Escaneo sostenido | 4 | 4 | 4 | **3** (r3 solo `brute_force`) | `port_scan` |
| Fuerza bruta HTTP | 3 | 3 | 3 | 3 | `brute_force` / `auth_failure_heuristic` |
| Inundación HTTP | 1 | 1 | 1 | 1 | `http_abuse` |
| **Total** | 15 | **12** | **10** | **10** | |

Lectura:

- La única emisión oportuna del escaneo breve (r1) es una ventana con la **señal del IF** y la regla `brute_force`,
  no `port_scan` (C10 de la Etapa 2). Con la política de la candidata (`if_senal`), esa ventana **no** autorizaría
  una restricción por escaneo.
- Límite: los registros de V son de `24f8a80`, que guardan solo la regla de mayor prioridad (`heuristico`), no la
  lista completa (`heuristicos`, desde la Etapa 2). Una `port_scan` simultánea con `brute_force` (prioridad mayor)
  no queda registrada, así que «regla prevista» en V es una **cota inferior**. En la 4C (ec78ca5) se registra la
  lista completa.
- R (replay con el motor del cierre) no se ha recalculado con las etiquetas: sus cifras siguen siendo «cualquier
  emisión».

## 4. Lo que esta tabla no demuestra

1. **Ninguna respuesta aplicada en el laboratorio.** Todo fue en sombra; las propuestas del publicador v2 no se
   aplicaron. B es un banco en contenedor con tráfico reinyectado.
2. **Ningún efecto** (que el ataque se detenga o se degrade). En B la mayoría de los SYN llega tras aplicar.
3. **El motor de la 4C en vivo.** R usa el mismo motor que `ec78ca5`, pero sobre el replay; el Sensor1 corre
   `24f8a80` con la cadena v1. La 4C es la primera medida en vivo de `ec78ca5`.
4. **La vía rápida en vivo.** Q y B son offline.
5. **Inundación HTTP** con un único episodio en la población principal: no es base para una tasa.
6. **DNS** solo por heurísticos/híbridos en 2 de 3 (el IF solo en r1); el LIMIT no está aprobado.

La respuesta oportuna **efectiva** (aplicada y con efecto antes de que termine el ataque) se demuestra, si se
demuestra, en la **campaña B** (Etapa 5), después de 4A → 4B → 4C.
