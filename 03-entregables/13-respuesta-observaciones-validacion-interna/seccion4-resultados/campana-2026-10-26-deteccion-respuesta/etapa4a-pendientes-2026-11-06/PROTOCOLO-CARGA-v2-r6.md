# Protocolo E-carga v2, revisión r6: franja de las 20:00 de Perú del sábado 7 de noviembre (2026-11-07)

**Estado: propuesta publicada para aprobación de Mark. NO ejecutada ni programada.** Vale como protocolo solo si Mark la
aprueba en el chat antes de las 19:05 de Perú del sábado 7 de noviembre (00:05Z del domingo 8). Hasta esa aprobación sigue
activa la [r5](PROTOCOLO-CARGA-v2-r5.md), aprobada por Mark, con T_g a las 22:00 de Perú. Con la aprobación, la r6 reemplaza a la
r5 y queda una sola franja activa.

**Qué es.** Esta revisión adelanta exactamente 2 horas la franja de la r5. Mantiene la opción `--forzar-laborable`, ya aplicada
en los seis perfiles, y las condiciones de la r5. La r4 y la r5 se conservan sin cambios como antecedentes. Todo lo que este
documento no cambia sigue con el texto de la r5 y, por debajo, de la r4.

## 1. Qué cambia frente a la r5

| Punto | r5 | r6 |
|---|---|---|
| Franja | T_g 1794106800, 03:00Z | T_g 1794099600, 01:00Z. Todos los epochs restan 7 200 s |
| §3.3 de la r4, fin de `salud_captura` y `obs_pcap` | 2026-11-08T04:16:00Z, epoch 1794111360 | 2026-11-08T02:16:00Z, epoch 1794104160 |
| §3.4.1 de la r4 | 6 tramos desde 1794107700 | 6 tramos desde 1794100500 |
| §3.5, punto 7, `fin_utc` | 2026-11-08T04:16:00Z | 2026-11-08T02:16:00Z |
| §3.5, punto 12, y §3.6.1, base de S14 | [1794106500, 1794106800) | [1794099300, 1794099600) |
| Verificaciones nuevas | No había | Antes del P0: rotación terminada y `eve.json` con eventos nuevos. Antes de la puerta G: reentrenamiento nocturno terminado |
| Condiciones | F1–F9 | F1–F9 referidas a la r6, más F10 y F11 de la sección 4 |

**No cambian:** K1–K5, S1–S15, sus umbrales, la duración de la ventana (3 600 s), el calentamiento (900 s), λ_diseño, el orden de
decisión de §4.1, `evaluar_ecarga.py` 2026-11-06.4, el detector, el modelo IF, las características, α, los heurísticos, la política
de respuesta, los relojes reales, la rotación de las 00:00Z y el reentrenamiento nocturno.

**Lo ya hecho sigue valiendo.** El paquete `0a794f4` y los drop-ins no dependen de la franja: los guiones del paquete reciben los
epochs por argumento y los drop-ins solo añaden `--forzar-laborable`. Se comprueban otra vez en la fase A.

## 2. Franja

La referencia es T_g = 1794099600, igual a 2026-11-08T01:00:00Z. El domingo 2026-11-08 tiene `weekday()` = 6 en UTC.

| Paso | Epoch | UTC (dom 08-nov) | Perú (UTC−5) |
|---|---|---|---|
| Traslado ya verificado, rotación confirmada e inicio de la fase A | 1794096300 | 00:05:00 | sáb 07-nov 19:05:00 |
| P0, comprobación previa | 1794097800 | 00:30:00 | sáb 19:30:00 |
| Arranque de muestreadores | 1794099000 | 00:50:00 | sáb 19:50:00 |
| Límite P12 e inicio de la base de S14 | 1794099300 | 00:55:00 | sáb 19:55:00 |
| T_g, arranque de generadores | **1794099600** | 01:00:00 | sáb 20:00:00 |
| Calentamiento (no cuenta) | 1794099600–1794100500 | 01:00:00–01:15:00 | sáb 20:00:00–20:15:00 |
| **Ventana fija** | **1794100500–1794104100** | **01:15:00–02:15:00** | **sáb 20:15:00–21:15:00** |
| Fin de `obs_pcap.py` y muestreadores de Sensor1 | 1794104160 | 02:16:00 | sáb 21:16:00 |
| Parada de generadores | 1794104220 | 02:17:00 | sáb 21:17:00 |
| Fin del muestreo del bastión | 1794104280 | 02:18:00 | sáb 21:18:00 |
| Análisis de perfiles, no antes de | 1794105000 | 02:30:00 | sáb 21:30:00 |
| Lecturas posteriores y verificadores, hasta | 1794106800 | 03:00:00 | sáb 22:00:00 |

## 3. Por qué esta franja sirve igual que la r5

**El factor no cambia.** 01:00–02:17Z sigue en el tramo de madrugada de `factor_horario`: 0,12 con la opción y 0,036 sin ella.
Se comprobó minuto a minuto. El razonamiento de la r5 §3 sobre el generador se mantiene sin cambios.

**La carga total sigue sin presumirse.** La deciden K1, K2, K3, K4a y K5, sin cambiar ningún umbral. Si no se alcanzan, el resultado
es «carga insuficiente».

**Lectura previa, informativa.** Sin generadores, Suricata contó 549 476 paquetes entre las 01:15 y las 02:15Z del sábado 7 de
noviembre, con 0 `kernel_drops`. La lectura equivalente para la franja de la r5 dio 552 367. No sustituye a K1 y no predice el
resultado.

**Qué ocurre alrededor de la nueva franja en Sensor1.**

| Hora | Tarea | Lectura de días anteriores | Tratamiento |
|---|---|---|---|
| 00:00Z | `logrotate`: rota `eve.json` con `copytruncate` y envía HUP a Suricata | Arrancó a las 00:00:00 y terminó en 2–24 s del 2 al 7 de noviembre, salvo el día 5, cuando arrancó a las 23:57. El temporizador admite hasta 1 h de retraso (`AccuracySec=1h`) | No se toca. Paso A0b |
| 00:30Z | `cyberflow-aprendizaje`: prepara y evalúa un candidato. No cambia el modelo en uso, con `Nice=19` | Arrancó hacia las 00:31 y duró de 75 a 97 s los días 4, 6 y 7 | No se toca. Coincide con el P0, que es de solo lectura. Paso A7b |
| 03:10Z | `e2scrub_all`, semanal | Próxima ejecución en Sensor1: domingo 8, 03:10:23Z | Con la r6 queda fuera de la franja. Con la r5 cae durante el calentamiento |

Ninguna de estas tareas cae dentro de la ventana fija. Sí hay tareas pequeñas de los demás hosts en horas aleatorias, igual
que en la r5; las recoge la observación ordinaria.

## 4. Condiciones para contar como E-carga formal y abrir la 4B

Valen F1–F9 de la [r5 §4](PROTOCOLO-CARGA-v2-r5.md), con estos cambios:

| # | Condición | Evidencia |
|---|---|---|
| F1 | Mark aprueba esta r6 en el chat, y su commit llega a main antes de T_g | Orden del chat, y P8 r6 con el registro de pushes de GitHub |
| F9 | La publicación dice «variante r6, domingo con factor de laborable forzado en los seis perfiles» | README de la evidencia |
| F10 | Antes del P0, la rotación de las 00:00Z terminó bien y `eve.json` recibe eventos nuevos | `comprobar_rotacion.sh rotacion`, paso A0b |
| F11 | Antes de la puerta G, el reentrenamiento nocturno terminó bien | `comprobar_rotacion.sh aprendizaje`, paso A7b |

F2–F8 quedan igual. Lo que la r5 dice de ellas se aplica a la franja de la r6. La regla de la r5 también sigue: si falla alguna
condición, la franja se conserva y se publica como **ensayo técnico**, no cumple la condición (3) y no abre la 4B. Un veredicto
adverso cuenta, y repetir exige una orden nueva y otra versión del protocolo, sin bajar ningún umbral.

## 5. Respaldo y paso entre franjas

- **Sin aprobación antes de las 19:05 de Perú**, o si A0b no se cumple a tiempo: la r6 no se ejecuta y sigue la r5 a las 22:00.
- **La r5 no se reescribe.** Su procedimiento sigue vigente con un solo cambio mecánico: el paso A1 usa `00_referencias.sh` 2026-11-07.6 de
  [`evidencia/25-franja-r6-20h/`](evidencia/25-franja-r6-20h/README.md), porque el 2026-11-07.5 rechaza cualquier commit posterior a su procedimiento. Lo comprobado
  por A1 no se reduce.
- **Con aprobación:** se cancela el aviso de la r5 y se lanza el de la r6. Solo queda una franja activa.
- **Si la r6 arranca generadores**, ya no se vuelve a la r5 esa noche: una repetición exige orden nueva y otra versión.

## 6. Lo que esta variante no demuestra

Lo mismo que la r5 §5. Además, la lectura de la r5 sobre el fondo de 03:15–04:15Z no se aplica a esta franja, que tiene la suya
propia. El resultado vale para esta franja y esta carga medida.

## 7. Aplicación y reversión

Los drop-ins ya están aplicados. La retirada no cambia: la hace Mark con sudo después de confirmar la parada, y la comprobación es
`comprobar_forzar.sh sin`. Los comandos están en
[`ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r6.md`](ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r6.md).
