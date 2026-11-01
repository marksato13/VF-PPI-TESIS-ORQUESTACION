# Presupuesto temporal de extremo a extremo (versión 3)

> **Qué es y qué no es.**
>
> - Son **estimaciones bajo supuestos declarados**, calculadas con `herramientas/presupuesto_e2e.py` v2 sobre los registros **de sombra** del 3B.
> - **No** es una campaña de respuesta: el tráfico se registró sin bloqueo, y la simulación no modela cómo una restricción habría cambiado el ataque, las decisiones posteriores ni el tráfico legítimo.
> - `t_apl_estimada` no es `t_apl`. `t_efecto` no se estima. En sombra, `t_apl` real y `t_efecto` valen «no aplica».
>
> Decisiones relacionadas: [DECISIONES.md](DECISIONES.md) (D2, D7, D8).

## 1. Cadena, tramos y clase de cada valor

Clases: **M** medido · **C** configurado · **S** supuesto · **D** desconocido.

| # | Tramo | Mecanismo | Valor | Clase | Referencia |
|---|---|---|---|---|---|
| 1 | **Disponibilidad de paquetes** | `tcpdump -G 15`. El motor no decide una ventana hasta que su PCAP está cerrado (`7b275b8`). | Espera B: 2,0 / 12,0 / 14,0 s (mín/med/máx, 25 episodios); paso del PCAP p50 15,0 s | C / M | `revision-3b/diagnosticos/demora.json` |
| 2 | **Evidencia suficiente para la regla** | Ventanas de 10 s con historia de 60 s; umbrales de los heurísticos evaluados al construir la ventana | Acumulación A: 0,9 / 7,9 / 23,1 s | M | demora.json |
| 3 | **Demora de evaluación** | espera de ciclo (`--step-seconds 10`) + proceso | C: 0,45 / 1,45 / 10,5 s · D: 1,2 / 2,6 / 7,0 s; ciclo p50 0,68, p99 7,0, máx 10,6 s | C / M | demora.json, ciclos.jsonl |
| — | **t_det** | `registro_escrito_en` | — | M | ciclos.jsonl |
| 4a | Publicación | timer `:x0`, AccuracySec=1s. Arranca en :x0,29; dura p50 0,598, máx 0,773 s. Punto de lectura del registro dentro de la ejecución: **D**. | — | C / M / D | journal del 3B (972 ejecuciones) |
| 4b | Distribución | relé `:x3` (bastión), doble `scp`; 1,065–1,612 s; offset de arranque **D** (cota de 1 s por AccuracySec) | — | C / M (pocas muestras) / D | `systemctl show` |
| 4c | Aplicación | agente `:x6`; p50 0,173, máx 0,564 s; offset **D** (cota de 1 s) | — | C / M / D | octubre, 76 201 ejecuciones |
| 4d | Activación nft (del commit al primer paquete descartado) | kernel | — | **D** | las reglas no tienen `counter` |
| 5 | **Efecto** (cese de las respuestas del destino mientras el generador sigue) | conexiones abiertas, retransmisiones, tasa | — | **D** | requiere SPAN + contadores (D7) |

## 2. Modelo de la cadena por timers (V0) y supuestos

Para un registro escrito en `t_det`:

1. **Publicador.** Se elige el tick `:x0` que lo incluye.
   - Escenario **favorable**: el publicador lee al **final** de su ejecución (S).
   - Escenario **alto**: lee al **arrancar** (S).
   - El punto real es desconocido.
2. **Relé.** Arranca en el primer `:x3` (+ offset) **posterior al fin de la publicación**. **Consumidor perdido:** si el publicador termina después de que arranque el relé, el relé copia el feed **anterior** y la entrada viaja en el relé siguiente (+10 s).
3. **Agente.** Arranca en el primer `:x6` (+ offset) **posterior al fin del relé**, con la misma regla de consumidor perdido.
4. `t_apl_estimada` = arranque del agente + su duración.

Los dos escenarios:

- **Favorable:** duraciones p50 o mínimas medidas y offsets desconocidos supuestos en 0.
- **Alto:** máximos **históricos** medidos más las cotas configuradas de 1 s.

**No son intervalos de confianza ni límites garantizados.** Un máximo histórico no es el peor caso futuro: un publicador o un relé más lentos podrían perder el consumidor siguiente y sumar 10 s. Las pruebas ensayan ese caso (`pruebas/`, publicador de 4,0 s y relé de 3,5 s).

Con los valores del 3B no se pierde ningún consumidor en ningún episodio. `t_apl_estimada − t_det` por episodio:

- **favorable:** 5,7–14,8 s;
- **alto:** 7,9–17,2 s (mediana 11,1 s).

**Clasificación por episodio** (frente a `t_fin_eval`, ε = 0,01 s):

| Clase | Condición | Depende de supuestos |
|---|---|---|
| `deteccion_posterior` | t_det **medido** > t_fin_eval | **no** |
| `despues_del_fin_bajo_supuestos` | incluso la estimación favorable es posterior al fin | sí |
| `indeterminado` | el fin cae entre la estimación favorable y la alta | sí |
| `antes_del_fin_bajo_supuestos` | la estimación alta es anterior al fin. **Además** deben caber la activación nft y el efecto, que son desconocidos. | sí: **no certifica oportunidad** |

Las demoras desconocidas **no se suman como cero**. Cada estimación lleva la lista `demoras_desconocidas_no_incluidas`.

**Variantes** (todas estimadas):

- **V1:** cadena por eventos. Publicador, relé y agente se encadenan al escribirse el registro, sin timers, con las mismas duraciones.
- **V2:** V1 más la decisión inmediata al cierre de la ventana: `t_det = window_end + duración medida del ciclo` (esperas 1 y 3 a cero). Es la mejor cifra posible **con las mismas ventanas y reglas**.

## 3. Resultados por escenario (política actual, α desplegado)

> La política **desplegada** (IF → LIMIT) es la que generó los registros. Con la política **adoptada** `if_senal` (D3), la primera acción de la regla prevista llega en las mismas ventanas en los 25 episodios. La separación entre anomalía del IF, heurístico previsto y respuesta está en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) §5.

Tabla por episodio en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md) §1 y §1b. Las distribuciones son **por episodio**.

| Escenario | Ejecutados (admitidos v2) | Regla prevista: t_det − t_inicio, mín–máx | V0 con la regla prevista | Primera señal de cualquier regla: V0 / V1 / V2 (antes\*) |
|---|---|---|---|---|
| Escaneo sostenido | 5 (4) | 22,0–74,3 s | antes\* 4 · det. posterior 1 (r3) | 5 / 5 / 5 |
| Fuerza bruta HTTP | 5 (3) | 18,4–25,1 s | antes\* 5 | 5 / 5 / 5 |
| Inundación HTTP | 5 (1) | 24,2–29,3 s | antes\* 5 (efecto **desconocido**) | 5 / 5 / 5 |
| DNS inusual | 5 (3) | 17,2–25,9 s | antes\* 5 (hoy **sin agente**; con D1, en DC1 y bajo el supuesto de la misma cadencia de relé y agente) | 5 / 5 / 5 |
| **Escaneo breve** | 5 (4) | **26,2–39,5 s** (fin a 17,6 s) | **det. posterior 5/5** | 0 / 0 / 1 (el 1 lo da `brute_force` mal atribuido) |

«antes\*» = antes del fin bajo supuestos (§2).

## 4. Escaneo breve: limitaciones de la configuración actual

El objetivo está **decidido** ([D2](DECISIONES.md)): detectar y aplicar una respuesta efectiva mientras el escaneo sigue activo, **sin prolongarlo**.

Lo que sigue describe por qué **esta configuración** no lo consigue con los registros del 3B. **No** afirma que detectar escaneos breves sea imposible en general.

Desglose por episodio con la regla prevista (`port_scan`), en segundos desde `t_inicio`; fin evaluado a 17,6 s:

| Episodio | (2) Cierre de la ventana donde la regla tiene evidencia suficiente | (1)+(3) Paquetes disponibles + evaluación, hasta t_det | t_det | (4) Cadena V0 (alto) | t_apl_estimada (alto) | V2: t_apl_estimada (favorable–alto) |
|---|---|---|---|---|---|---|
| r1 | 20,6 | +15,8 | 36,4 | +11,7 | 48,2 | 23,8–24,9 |
| r2 | 18,0 | +8,3 | 26,2 | +9,3 | 35,5 | 22,4–23,6 |
| r3 | 15,0 | +15,7 | 30,7 | +11,9 | 42,6 | 18,1–19,2 |
| r4 | 23,0 | +5,8 | 28,8 | +11,8 | 40,6 | 26,1–27,3 |
| r5 | 23,1 | +16,5 | 39,5 | +11,1 | 50,6 | 26,9–28,1 |

**Lectura:**

1. **Evidencia suficiente para la regla (tramo 2).**
   - En 4/5 episodios, la ventana en la que `port_scan` se cumple **cierra después del fin** (18,0–23,1 s).
   - En r3 cierra a 15,0 s, y aun con esperas nulas (V2) la aplicación estimada (18,1 s) llega después de 17,6 s.
   - La primera ventana, que contiene entre 0,6 y 8 s de ataque, nunca dio señal.
   - nmap -T4 hace unos 55 puertos/s, así que la ráfaga de ≥ 200 intentos/30 s se alcanza en pocos segundos. El retraso nace de **cuándo se construye y se decide la ventana**, no del volumen.
2. **Disponibilidad de paquetes y evaluación (tramos 1 y 3).** Añaden 5,8–16,5 s: espera al cierre del PCAP de 15 s, espera al ciclo de 10 s y proceso.
3. **Publicación, distribución y aplicación (tramo 4).** Añaden 9,3–11,9 s con timers (alto) y unos 1,8–2,9 s por eventos.
4. **Efecto (tramo 5).** Desconocido.
5. **Señal de otra regla.** El `brute_force` de r1 a 16,4 s **no** valida `port_scan`. Hay que comprobar la atribución y el comportamiento que lo originó (MATRIZ, errores de atribución).

**Por qué rotar el PCAP más rápido no basta:**

- `-G 5` solo reduce el tramo 1.
- Aunque los tramos 1, 3 y 4 fueran casi nulos (V2), la regla actual tiene la evidencia en ventanas que cierran tarde.
- Hacen falta las dos cosas a la vez:
  - **captura y cadena** (Etapa 2): lectura incremental o rotación corta conservando la regla de paquetes decodificados, ciclo por eventos, y publicación, distribución y aplicación por eventos;
  - **regla temprana** (Etapa 3): `port_scan` evaluado en cuanto el contador supera el umbral con la evidencia parcial disponible, sin esperar al cierre de la ventana y sin usar la IP del generador.

**Comprobación de la Etapa 2:** con los PCAP del 3B, medir por episodio el tiempo hasta la evidencia suficiente y hasta `t_apl_estimada` con el prototipo, frente a 17,59 s y con margen para las demoras desconocidas. Hasta entonces, la viabilidad es **desconocida**.

## 5. Contaminación entre episodios (simulación secuencial, bajo supuestos)

Con la política actual y el estado real de escalada (nivel 3 previo del origen), 24/25 episodios habrían empezado con un **BLOCK hipotético** vigente de unos 3600 s ([TABLAS](resultados/TABLAS-E2E.md) §4).

Es un **riesgo bajo supuestos**: con un bloqueo real, los ataques y las decisiones posteriores habrían sido distintos. Basta para exigir la limpieza verificada de [D5](DECISIONES.md).

## 6. Otras advertencias del código

- La ventana de lectura del publicador es de 120 s: las decisiones tardías de más de 120 s no se publican.
- El servicio pasa `--umbrales 2026-10-06.1` frente al código `.2`; gana el código y se emite un aviso.
- El comentario de `relay-feed.sh` dice «cada 60 s» y el timer es de 10 s.
- Todo se corrige en la Etapa 2, en la rama candidata.
