# Criterios de la revisión del paso 3B — revisión posterior a conocer los resultados

**Naturaleza del documento.** Este documento es una **revisión posterior a conocer los resultados** del paso 3B
(ejecución 20261101T0721Z, commits `67fc1f5` y `b714492`). **No** es el protocolo original de la campaña ni una
evaluación independiente. El protocolo original congelado sigue siendo `PROTOCOLO-CAMPANA-A-REPETIDA.md` (preparación
3A) y su resultado (población principal 1/25) se conserva sin cambios en `ejecucion-3b-2026-11-01/`. Todo lo que aquí
se calcule se presenta **junto** al original, nunca en su lugar.

Se escribe y se publica en Git **antes** de ejecutar el reanálisis (commit de este fichero anterior a cualquier
resultado de `resultados/`). Fecha: 2026-11-01, 16:12 UTC. Base: `b714492`.

## 1. Lo que ya se sabía al escribir estos criterios

Se declara para que el lector pueda juzgar el sesgo posible:

- Resultado original: 25/25 episodios; población principal 1/25 (`escaneo_breve-r3`); 24 no aptos por integridad
  (`cobertura_durante` 22, `continuidad` 22, `previa` 21, `posterior` 10, `captura` 9); fuente degradada 8 (±60 s).
- La causa del 1/25: `generar_respaldos.py` mide la continuidad con los instantes de escritura (`logged_at`) de
  **todas** las decisiones con una tolerancia de 20 s (`analizar.TOL_CONTINUIDAD_S = 2·PASO_S`), y `analizar.cobertura()`
  exige lo mismo. El motor incremental escribe cada 10 s, pero un ciclo sin ventanas listas no escribe nada, y la
  ventana solo se decide cuando `marca_pcap ≥ window_end` (rotación PCAP de 15 s). Por eso aparecen huecos de escritura
  de 20,0–23,5 s también sin carga, y en el inventario no falta ninguna ventana (12 667 requeridas, 0 ausentes,
  655 tardías).
- La repetición offline coincide con el vivo en puntuación, decisión y paquetes en 12 667/12 667 claves; difiere el
  texto `motivo` del heurístico en 18 claves.
- El recálculo independiente de características difiere en 9 de 702 decisiones de la Kali. En una se comprobó ya la
  causa (selección de PCAP por la última trama en vez del último paquete decodificado).
- Suricata registró `kernel_drops` en 9 episodios (con [−120, +90]) y 8 (con ±60 s). tcpdump: 0 descartes en todo el
  proceso (SIGUSR1, 10:51:44).
- Emisiones oportunas en 21/25 episodios; FA del control IF α 0,05/0,03/0,01 = 14,94/9,61/3,14 %.

## 2. Qué NO cambia

- Modelo, escalador, características, umbrales (los tres α y el desplegado), heurísticos, escenarios, motor y
  servicios. No se repite la campaña ni se lanzan ataques.
- Mínimos de historia previa (120 s) y posterior (90 s); horizonte de 60 s; puntualidad ≤ 60 s; rejilla de 10 s.
- **La tolerancia de 20 s no se sube** (ni a 25 ni a 30 s). Simplemente deja de aplicarse a lo que no mide
  continuidad (la cadencia de escritura).
- Las comprobaciones de hashes, relojes, reinicios, ficheros PCAP ilegibles/perdidos y descartes siguen siendo
  requisitos independientes, con la misma regla que en el original.
- Captura y Suricata: en el **resultado principal revisado** se mantienen **exactamente** los criterios originales
  (integridad: `kernel_drops` > 0 en [inicio−120, fin+90] → captura no apta; calidad: ±60 s → degradada). La
  unificación de intervalos solo se presenta como **análisis adicional**, y sin elegir retrospectivamente.
- `analizar_3b.py` no se modifica: ya trata la continuidad contra el inventario y deja el hueco de escritura como
  informativo. Se corrige la cadena que alimenta su campo `integridad` (respaldos e integridad).
- `analizar.py` (primera campaña) no se modifica; se documenta que su `cobertura()` tiene el mismo defecto.

## 3. Criterios de integridad revisados (v2)

Para cada episodio con inicio `ini` y fin `fin` se definen tres intervalos:

| Intervalo | Rango | Mínimo |
|---|---|---|
| previa | [ini − 120, ini] | 120 s (sin cambios) |
| durante | [ini, fin + 60] | — |
| posterior | [fin, fin + 90] | 90 s (sin cambios) |

Cada intervalo es **verificado** solo si se cumplen a la vez los tres componentes siguientes, cada uno medido sobre
una fuente distinta:

1. **PCAP continuo.** Los ficheros `live-*.pcap` archivados cubren el intervalo: el primero empieza ≤ al inicio del
   intervalo, el último cubre su fin (inicio + 15 s ≥ fin), sin hueco entre inicios consecutivos > 16 s (15 s + 1 s,
   la misma tolerancia del original). Sin ficheros `PERDIDO` del archivador.
2. **EVE continuo.** El pulso de eventos `stats` del EVE (`stats.interval` = 8 s en `suricata.yaml`) cubre el
   intervalo sin un hueco ≥ 16 s (2 × el intervalo configurado). Esto demuestra que Suricata siguió escribiendo; **no**
   demuestra ausencia de descartes, que se juzga aparte (captura/calidad).
3. **Procesamiento completo contra el inventario.** Todas las ventanas requeridas por el inventario (repetición
   offline; claves con decisión o no evaluadas, **de todas las entidades**) cuyo `window_end` cae en el intervalo
   tienen decisión en vivo. Ninguna puede estar `ausente` ni `no_evaluada`. Cada decisión tiene `marca_pcap ≥
   window_end` y `marca_eve ≥ window_end`, que es la prueba de que se decidió con las fuentes ya disponibles hasta el
   final de la ventana. Si alguna parte del intervalo cae fuera del rango del inventario, el intervalo es **no
   verificado** (no se puede saber si faltan ventanas). Coincidir con la repetición **no** sustituye a los
   componentes 1 y 2: una fuente degradada no pasa a completa por coincidir con el replay.

Además, para **durante**: todas las anclas de la Kali (rejilla de 10 s, `window_end` en (ini, fin+60)) decididas en
vivo. Es el mismo conjunto que `analizar_3b.ventanas_esperadas_episodio`.

**Continuidad (requisito propio)** = componentes 1, 2 y 3 sobre todo el periodo [ini − 120, fin + 90]. **No** usa la
cadencia de escritura.

**Informativo (no clasifica):** hueco máximo entre escrituras del registro, ciclos sin decisiones, latido de los
ciclos y duración de los ciclos. Se publican en el respaldo con la etiqueta `informativo`.

**Faltantes, captura, reinicios, relojes, hashes:** igual que en el original. En particular, `paquetes_descartados`
de tcpdump = 0 con su alcance (contador acumulado del proceso, sin medir pérdidas aguas arriba del SPAN), y
`kernel_drops` de Suricata > 0 en el periodo → captura no apta.

`verificar_integridad_v2` exige que el respaldo de cobertura traiga el **desglose por componente** (pcap, eve,
procesamiento) de cada intervalo. Un respaldo que solo traiga `previa_s`/`continuidad_sin_huecos` sin desglose es
**no verificado**: el valor agregado no basta.

**Población principal revisada** = la de `analizar_3b.py` (inventario que cubre todas las anclas, todas decididas en
vivo, fuente `completa` con el criterio ±60 s original, evidencia de destino) con `integridad` tomada de
`verificar_integridad_v2`. No se exige un número mínimo de episodios y no se ajusta nada para aumentarla.

## 4. Pruebas obligatorias antes de ejecutar sobre los datos reales

1. Dos ventanas presentes escritas con 20,2 s de diferencia no cuentan como perdidas.
2. Una ventana requerida ausente sigue detectándose (intervalo no verificado).
3. Una ventana no evaluada no sale del denominador (cuenta como no decidida).
4. Se detecta la falta de historia previa o de cobertura posterior (PCAP, EVE o ventanas).
5. Un inventario truncado no permite observación completa.
6. Una fuente degradada no pasa a completa por coincidir con el replay.

Además se ejecutan las pruebas existentes aplicables (`tests/test_analizar_3b.py`, `tests/test_herramientas.py`,
`tests/regresion_alfa.py`) sin modificarlas.

## 5. Reconstrucción de características

- Se distingue: **exacta** (las 28 características coinciden con tolerancia relativa 1e-6 y la puntuación también),
  **puntuación distinta**, y **sin puntuación** (fila con 0 paquetes: el recálculo no puntúa; `null` ≠ 0).
- Si la diferencia es de la herramienta de recálculo, se corrige en la carpeta de la revisión, se prueba y se
  vuelve a ejecutar en un directorio nuevo del sensor. Si es del motor, se documenta y se propone aparte sin
  modificarlo.
- Para cada diferencia se informa el efecto sobre las señales IF a los tres α, sobre la primera señal y sobre la
  categoría del episodio. El reanálisis usa los **registros en vivo** (lo que el motor decidió), no el recálculo.

## 6. Reanálisis

- Tres α (0,05 / 0,03 / 0,01) y las siete configuraciones, con los umbrales congelados.
- Original frente a revisado, episodio a episodio, con los motivos de admisión y exclusión.
- `oportuna` y `solo_posterior` por separado. Emisiones reales separadas de las configuraciones derivadas.
- Falsas alarmas del control con numerador, denominador y cobertura.
- Población común a las siete configuraciones (la misma lista de episodios).
- **No se elige α** y nada de esto se presenta como confirmación independiente.

## 7. Diagnóstico de la demora y propuesta

- Descomposición por episodio con lo registrado (marcas de la Kali, `window_end`, nombres y mtime de PCAP,
  `inicio_ciclo`, `marca_pcap`, `registro_escrito_en`). Lo no registrado se declara como incertidumbre.
- Las alternativas de cambio se describen con su efecto, riesgos, efecto sobre características, calibración y
  comparabilidad, y cómo probarlas y revertirlas. **No se despliega nada.** Si se propone modificar el producto: versión
  candidata, criterios congelados y validación con tráfico independiente antes de la campaña B.
