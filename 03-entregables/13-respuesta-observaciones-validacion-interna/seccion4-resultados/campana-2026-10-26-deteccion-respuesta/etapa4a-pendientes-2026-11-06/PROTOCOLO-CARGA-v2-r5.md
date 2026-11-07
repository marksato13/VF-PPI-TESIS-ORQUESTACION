# Protocolo E-carga v2, revisión r5: franja del domingo 8 de noviembre (2026-11-07)

**Estado: propuesta publicada para aprobación de Mark. NO ejecutada ni programada.** Vale como protocolo solo si Mark la
aprueba en el chat antes de las 21:05 de Perú del sábado 7 de noviembre (02:05Z del domingo 8). Sin esa aprobación sigue
vigente la r4, con su franja del lunes 9 de noviembre.

**Qué es.** Esta revisión adelanta exactamente 24 horas la franja publicada en la r4 y usa en los seis perfiles la opción
existente `--forzar-laborable`, de forma temporal y reversible. La r4 se conserva sin cambios como antecedente:
[`PROTOCOLO-CARGA-v2.md`](PROTOCOLO-CARGA-v2.md), commit `034d57d`. Todo lo que este documento no cambia sigue con el texto de
la r4.

## 1. Qué cambia frente a la r4

| Punto de la r4 | r4 | r5 |
|---|---|---|
| §3.1, «Generador» | «`--intensidad` por omisión y curva `factor_horario` sin fijar» | Igual, salvo que las seis unidades añaden `--forzar-laborable`. El generador no cambia de bytes (`ae5134a7…`) |
| §3.1, «Franja» | Ventana en 23:00–08:00 UTC de un día laborable, con base 0,12 | Ventana en 23:00–08:00 UTC del domingo 8 de noviembre, con base 0,12 mantenida por la opción |
| §3.2 | Franja del lunes 9 de noviembre | Tabla de la sección 2, con los mismos desfases |
| §3.2, «otra madrugada laborable UTC» | Obligatorio para una franja nueva | Excepción de esta revisión, solo para esta franja |
| §3.3 | Fin de `salud_captura` y `obs_pcap` 2026-11-09T04:16:00Z, epoch 1794197760 | 2026-11-08T04:16:00Z, epoch 1794111360 |
| §3.4.1 | 6 tramos desde 1794194100 | 6 tramos desde 1794107700 |
| §3.5, punto 5 | `weekday()` UTC de 0 a 4 | Domingo UTC (`weekday()` 6), con la condición F2 de la sección 4 |
| §3.5, punto 7 | `fin_utc` = 2026-11-09T04:16:00Z | `fin_utc` = 2026-11-08T04:16:00Z |
| §3.5, punto 12, y §3.6.1 | Base de S14 [1794192900, 1794193200) | Base de S14 [1794106500, 1794106800) |

Todos los epochs de la r4 usados en §3 se restan 86 400 s. Nada más se mueve.

**No cambian:** K1–K5, S1–S15, sus umbrales, la duración de la ventana (3 600 s), el calentamiento (900 s), λ_diseño, el
orden de decisión de §4.1, `evaluar_ecarga.py` 2026-11-06.4, el detector, el modelo IF, las características, α, los
heurísticos, la política de respuesta y los relojes reales del laboratorio.

## 2. Franja

La referencia es T_g = 1794106800, igual a 2026-11-08T03:00:00Z. El domingo 2026-11-08 tiene `weekday()` = 6 en UTC.

| Paso | Epoch | UTC (dom 08-nov) | Perú (UTC−5) |
|---|---|---|---|
| Traslado ya verificado e inicio de la fase A | 1794103500 | 02:05:00 | sáb 07-nov 21:05:00 |
| P0, comprobación previa | 1794105000 | 02:30:00 | sáb 21:30:00 |
| Arranque de muestreadores | 1794106200 | 02:50:00 | sáb 21:50:00 |
| Límite P12 e inicio de la base de S14 | 1794106500 | 02:55:00 | sáb 21:55:00 |
| T_g, arranque de generadores | **1794106800** | 03:00:00 | sáb 22:00:00 |
| Calentamiento (no cuenta) | 1794106800–1794107700 | 03:00:00–03:15:00 | sáb 22:00:00–22:15:00 |
| **Ventana fija** | **1794107700–1794111300** | **03:15:00–04:15:00** | **sáb 22:15:00–23:15:00** |
| Fin de `obs_pcap.py` y muestreadores de Sensor1 | 1794111360 | 04:16:00 | sáb 23:16:00 |
| Parada de generadores | 1794111420 | 04:17:00 | sáb 23:17:00 |
| Fin del muestreo del bastión | 1794111480 | 04:18:00 | sáb 23:18:00 |
| Análisis de perfiles, no antes de | 1794112200 | 04:30:00 | sáb 23:30:00 |
| Lecturas posteriores y verificadores, hasta | 1794114000 | 05:00:00 | dom 00:00:00 |

## 3. Por qué esta variante sirve para evaluar estabilidad bajo carga

**El requisito de día laborable era un medio, no un fin.** La r4 lo pide para que `factor_horario` dé la base 0,12 del ensayo
del anillo. En domingo, sin la opción, la base cae a 0,036 (0,12 × 0,3).

| Cálculo con `clientes_lab.py` `ae5134a7…` | Base 03:00–04:17Z | Acciones de ligero por tramo de 600 s | P(algún tramo vacío, K4a) |
|---|---:|---:|---:|
| Lunes de la r4 | 0,12 | ≈ 6 | ≈ 1,5 % (r4 §3.4.1) |
| Domingo sin la opción | 0,036 | ≈ 1,8 | ≈ 66 % |
| Domingo con `--forzar-laborable` | 0,12 | ≈ 6 | ≈ 1,5 % |

Sin la opción, el ensayo fallaría casi seguro por falta de carga generada, sin decir nada sobre la estabilidad.

**E-carga es una prueba de estrés, y ese es el uso que el generador admite.** Su propia documentación limita la opción a
«llenar el anillo y estresar la cadena antes de una captura de verdad». E-carga no entrena ni calibra.

**La carga total no se presume.** La opción solo devuelve la base a los seis perfiles. El tráfico de fondo (Wazuh, AAA,
pfSense, CARP) sigue en su régimen real de fin de semana, y la mezcla resultante no es la de un día laborable. Por eso la
equivalencia no se afirma por cálculo: la deciden K1, K2, K3, K4a y K5, sin cambiar ningún umbral. Si no se alcanzan, el
resultado es «carga insuficiente».

**Lectura previa, informativa.** Sin generadores, Suricata contó 552 367 paquetes entre las 03:15 y las 04:15Z del sábado 7
de noviembre, con 0 `kernel_drops`. La medida O12 del viernes contó 587 592 entre las 04:50 y las 05:50Z. Son horas y días
distintos, no sustituyen a K1 y no predicen el resultado. Solo muestran que el fondo de fin de semana no es despreciable.

## 4. Condiciones para contar como E-carga formal y abrir la 4B

Esta variante cuenta como E-carga formal **solo si se cumplen todas**:

| # | Condición | Evidencia |
|---|---|---|
| F1 | Mark aprueba esta r5 en el chat, y su commit llega a main antes de T_g | Orden del chat, y P8 r5 con el registro de pushes de GitHub |
| F2 | Las seis unidades tienen exactamente el argv de la variante antes del P0 | `comprobar_forzar.sh con`: argv exacto, drop-in único y `clientes_lab.py` `ae5134a7…` |
| F3 | Los seis procesos corren con ese argv tras T_g | `comprobar_forzar.sh vivo`, durante el calentamiento |
| F4 | Se cumplen sin cambios P0, P8, P12, puerta G, C1, ventana y parada | Mismas evidencias del procedimiento |
| F5 | El veredicto sale de `evaluar_ecarga.py veredicto` sin tocar ningún dato ni umbral | `veredicto.json`, `trazabilidad.json` |
| F6 | Relojes reales. Sin `faketime`, sin cambiar la zona horaria y sin tocar NTP | Lecturas de P0 y `eventos.log` |
| F7 | La opción se retira antes de la 4B y la retirada se comprueba | `comprobar_forzar.sh sin`, antes de pedir la 4B |
| F8 | Nada de esta franja se usa para entrenar, calibrar ni fijar umbrales | Declaración en la publicación |
| F9 | La publicación dice «variante r5, domingo con factor de laborable forzado en los seis perfiles» | README de la evidencia |

**Qué abre.** Con F1–F9 y el veredicto «estable con carga suficiente», se cumple la condición (3) del criterio de avance.
No inicia la 4B: sigue haciendo falta la petición expresa de Mark.

**Qué no abre.** Si falla alguna de F1–F9, la franja se conserva y se publica como **ensayo técnico**, no como E-carga formal:
no cumple la condición (3) y no abre la 4B. Un fallo de F2 o F3 antes de la ventana detiene la ejecución.

**Un veredicto adverso cuenta.** La r4 §5 sigue aplicando: un resultado desfavorable se publica tal cual, y repetir exige una
orden nueva y otra versión del protocolo, sin bajar ningún umbral.

## 5. Lo que esta variante no demuestra

Además de lo declarado en la r4 §6:
- no demuestra estabilidad con el tráfico de fondo de un día laborable;
- no compara directamente con el ensayo del anillo, que tuvo fondo de miércoles;
- no demuestra el comportamiento en domingo sin la opción, que no se mide;
- la estabilidad queda demostrada, si sale, para esta franja y esta carga medida.

## 6. Aplicación y reversión

La opción se aplica con drop-ins de systemd, sin editar las unidades ni el generador. Hace falta contraseña de sudo, porque
`adminclientes` no tiene `daemon-reload` sin contraseña, así que lo ejecuta Mark. La retirada borra esos drop-ins y nada más. Los
comandos están en el procedimiento de la variante:
[`ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r5.md`](ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r5.md).
