# Paso 2 — criterios definitivos de evaluación

Fijados el 2026-11-01 a las ~03:45 UTC, **antes de la primera inundación (T1)**. Complementan
`PROTOCOLO-PASO2.md` (sha256 `39286779…`, 03:17:20 UTC), que se conserva sin cambios. Este fichero se guarda
como solo lectura en el sensor y su sha256 queda registrado antes de T1. No se modificará después para que las
pruebas pasen. Si algún criterio resulta inaplicable, se informará como tal sin sustituirlo.

## Cambios respecto al protocolo, con su justificación

Los cambios se basan solo en el comportamiento del intervalo normal observado hasta las 03:40. Ninguno se basa en
datos de una inundación.

1. **«Pendientes sin crecer» para iniciar un episodio.**
   - **Protocolo:** el valor del último ciclo no supera el máximo de los 6 anteriores.
   - **Definitivo:** la media de `ventanas_pendientes` de los 6 últimos ciclos es menor o igual que el p95 del
     intervalo normal.
   - **Por qué:** en régimen estable el valor oscila ciclo a ciclo entre 4 y 21 sin tendencia, así que la regla
     original bloquearía por ruido.
2. **Retraso.**
   - **Criterio:** se evalúa con p50 y p95 por condición. El máximo se informa siempre, con su causa.
   - **Por qué:** las ventanas sin paquetes (`packet_count_10s = 0`) dentro del rango de una entidad con tráfico
     esporádico (10.10.10.1, .25, 10.10.30.10) solo se deciden cuando un paquete posterior amplía ese rango, a
     veces hasta ~230 s después. Es el mismo diseño de `build_rows` que en 7b275b8, no una acumulación.
   - **Datos de 03:18 a 03:40:** p50 14,7 s, p95 25,8 s, p99 114,6 s, máximo 234,6 s.
3. **Preparación.** Las tres peticiones de 03:15:43 (agente `cf-preparacion-paso2-…`) y su `ALERT` de la Kali
   pertenecen a la preparación y no cuentan en ninguna condición evaluada.

## Criterios de rendimiento (aceptación en el alcance probado)

Condiciones evaluadas: **normal**, **inundación Tk** y **recuperación Tk** (definidas en el protocolo). El
calentamiento tras el reinicio se informa aparte. No forma parte de la aceptación, pero en él no puede fallar
ningún servicio.

| # | Criterio | Umbral |
|---|---|---|
| C1 | Duración del ciclo | **Todos** los ciclos de las condiciones evaluadas < 10 s. Se listan todos los > 9,5 s con su hora; se informan el p95 y el margen mínimo (10 − máximo). |
| C2 | Fallos | `ppi-motor`, captura y Suricata activos, sin reinicios nuevos (`NRestarts` sin cambios). 0 trazas en el journal del motor. Archivador sin fallos ni pérdidas. |
| C3 | Duplicados | 0 claves `(entity_ip, window_end_utc)` duplicadas introducidas tras la instalación (registro vigente y, si existe, rotado). |
| C4 | Ventanas omitidas | 0 ventanas «ausentes» sin explicar frente a la repetición offline, para `window_end` ∈ [03:23:50, cierre − 120 s]. Toda diferencia (ausente, solo en vivo, decisión distinta) se clasifica con su mecanismo. «Ausente» sin mecanismo demostrado = fallo. |
| C5 | Sin acumulación | En cada recuperación Tk: (a) la media de pendientes de su último tercio ≤ p95 del normal; (b) el p50 del retraso `decidido_en − window_end` ≤ p50 del normal + 10 s; (c) los 6 últimos ciclos antes del siguiente episodio < 9,5 s. |
| C6 | Memoria | Memoria disponible mínima > 1 GB; `pswpout` sin incrementos y swap usado sin crecer en todas las condiciones. |
| C7 | Evidencia y tiempo | Archivo PCAP continuo desde 03:20 hasta el cierre (vistos = archivados, 0 perdidos); segmento EVE del mismo inodo; marcas de inicio y fin de cada Tk; `decidido_en ≤ logged_at ≤ registro_escrito_en` en todas las decisiones evaluadas. |

**Fuentes.** Los descartes de captura (`capture.kernel_drops` de Suricata y `rx_drop` de ens37) se informan por
condición. Si hay descartes en una condición evaluada, se señalan como degradación de la fuente y se comprueba
si afectan a las ventanas de la Kali. No se ocultan ni se atribuyen al motor sin comprobarlo.

**Carga.** Si durante una inundación aparece un bloqueo real (motor caído, ciclos > 30 s sostenidos, memoria
disponible < 500 MB o swap activo), se detiene la carga de forma ordenada y se informa. No se reduce la intensidad
ni se repite para aprobar.

## Detección (separada de la aceptación)

Para cada Tk se informa:

- **Emisiones en vivo** del motor para 10.10.20.30: `ALERT` del modelo desplegado (umbral registrado −0,5693969936)
  o un heurístico registrado, con `window_end`, `decidido_en`, `logged_at` y `registro_escrito_en`, y su fase:
  antes, durante (window_end en [inicio, fin + 10 s]), posterior (hasta + 60 s) o cola.
- **Clasificaciones derivadas**, no emitidas: IF_0.05, IF_0.03, IF_0.01, HEUR y HIB_* sobre las mismas
  puntuaciones, con los umbrales de `config-campana.json`. No se elige α.
- **Atribución:** origen 10.10.20.30 y destino 10.10.30.10:80 confirmados en el EVE dentro del intervalo, sin
  otra actividad de la Kali en ese tramo.
- **Si no hay señal:** se analizan la disponibilidad de datos, la puntuación y los heurísticos. No se prolonga ni se
  ajusta nada.

La latencia se informa como `logged_at − inicio real`, con `registro_escrito_en − inicio real` como cota superior
de disponibilidad. **La duración del ciclo no es una latencia de detección.**
