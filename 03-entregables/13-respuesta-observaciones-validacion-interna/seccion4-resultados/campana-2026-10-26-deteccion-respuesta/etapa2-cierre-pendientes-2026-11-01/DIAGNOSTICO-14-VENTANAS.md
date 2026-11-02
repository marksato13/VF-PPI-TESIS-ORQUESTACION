# Diagnóstico individual de las 14 `ventana_no_regenerada`

## Origen

Las 14 ventanas proceden del replay completo del cierre técnico (motor `953a436`). Se reprodujeron igual en la corrida secuencial `sec-ref-953a436`, que es idéntica a la publicada en sus 12 740 claves (`resultados/comparaciones/publicado-completo-cand-vs-sec-ref-953a436.json`). Ninguna pertenece al origen del ataque ni al control (07:32–08:05).

## Método: un recálculo independiente del motor

`herramientas/diagnostico_14.py` no usa el código del motor. Lee el PCAP archivado del 3B y el segmento de EVE, y vuelve a calcular cada caso con las funciones congeladas (`deduplicar_espejo`, `attribute_packets`, `load_app_observations`). Lo hace en dos horizontes:

- **Horizonte de alta:** el que usó el motor al dar de alta la pendiente. Es el de la última ancla tratada, `corte_incorporacion`.
- **Horizonte propio de la ventana:** `[A − 230 s, …]`, el único válido para decidir la ventana A.

Para cada caso obtiene:

- las observaciones de la entidad E en (A − 60, A] en el PCAP y en el EVE;
- el propietario de esos paquetes;
- el inicio de los flujos de E;
- el estado que corresponde por la regla causal de registro: se registra (E, A) si E tiene paquetes o L7 propios en (A − 60, A] **en el horizonte propio**.

Después compara ese estado con el que escribe el motor corregido (`6b6ef82`).

**Salida:** `resultados/diagnostico/diagnostico-14.json`.
**Comando:** ver `DEPENDENCIAS-Y-COMANDOS.md`.

## Tabla individual

En la tabla, «alta» y «expiró» son las horas de la pendiente en `953a436`. El motivo de la expiración es `ventana_no_regenerada` en las 14.

| # | Entidad | Fin de ventana A | Alta (953a436) | Expiró (953a436) | Corte de alta | Corte propio (A−230) | Obs. PCAP de E en (A−60, A]: alta / propio | Obs. EVE | Propietarios, en el horizonte propio, de los paquetes de E en (A−60, A] | Cambio de propietario | Todos excluidos | Regla causal | Estado con 6b6ef82 | Coincide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10.10.50.52 | 09:24:40 | 09:23:51.187 | 09:24:41.026 | 09:20:00.000 | 09:20:50.000 | 14 / 0 | 0 | 10.10.60.10: 14 | sí | sí | no_registrable | cancelada | sí |
| 2 | 10.10.30.10 | 09:26:50 | 09:26:41.221 | 09:26:51.047 | 09:22:50.000 | 09:23:00.000 | 10 / 0 | 0 | 10.10.10.30: 396, 10.10.20.21: 362, 10.10.20.22: 7043, 10.10.20.23: 5667, 10.10.20.24: 269, 10.10.20.25: 24, 10.10.20.26: 651 | sí | no | no_registrable | cancelada | sí |
| 3 | 10.10.30.10 | 09:27:00 | 09:26:41.221 | 09:27:01.121 | 09:22:50.000 | 09:23:10.000 | 10 / 0 | 0 | 10.10.10.30: 396, 10.10.20.21: 381, 10.10.20.22: 6181, 10.10.20.23: 4281, 10.10.20.24: 230, 10.10.20.25: 22, 10.10.20.26: 619 | sí | no | no_registrable | cancelada | sí |
| 4 | 10.10.30.10 | 09:27:10 | 09:26:41.221 | 09:27:11.155 | 09:22:50.000 | 09:23:20.000 | 10 / 0 | 0 | 10.10.10.30: 398, 10.10.20.21: 349, 10.10.20.22: 7769, 10.10.20.23: 3277, 10.10.20.24: 241, 10.10.20.25: 32, 10.10.20.26: 2310 | sí | no | no_registrable | cancelada | sí |
| 5 | 10.10.30.10 | 09:27:20 | 09:26:41.221 | 09:27:21.028 | 09:22:50.000 | 09:23:30.000 | 10 / 0 | 0 | 10.10.10.30: 398, 10.10.20.21: 351, 10.10.20.22: 10107, 10.10.20.23: 3797, 10.10.20.24: 262, 10.10.20.25: 32, 10.10.20.26: 1701 | sí | no | no_registrable | cancelada | sí |
| 6 | 10.10.30.10 | 09:27:30 | 09:26:41.221 | 09:27:31.094 | 09:22:50.000 | 09:23:40.000 | 10 / 0 | 0 | 10.10.10.30: 398, 10.10.20.21: 140, 10.10.20.22: 12746, 10.10.20.23: 1906, 10.10.20.24: 275, 10.10.20.25: 34, 10.10.20.26: 1703 | sí | no | no_registrable | cancelada | sí |
| 7 | 10.10.30.10 | 09:27:40 | 09:26:41.221 | 09:27:41.080 | 09:22:50.000 | 09:23:50.000 | 5 / 0 | 0 | 10.10.10.30: 400, 10.10.20.21: 141, 10.10.20.22: 11241, 10.10.20.23: 1854, 10.10.20.24: 219, 10.10.20.25: 22, 10.10.20.26: 1705 | sí | no | no_registrable | cancelada | sí |
| 8 | 10.10.10.21 | 09:28:30 | 09:27:51.206 | 09:28:31.188 | 09:24:00.000 | 09:24:40.000 | 9 / 0 | 0 | 10.10.40.10: 2, 10.10.60.10: 9, 10.10.60.40: 2 | sí | no | no_registrable | cancelada | sí |
| 9 | 10.10.10.21 | 09:34:30 | 09:33:51.007 | 09:34:31.028 | 09:30:00.000 | 09:30:40.000 | 9 / 0 | 0 | 10.10.60.10: 9 | sí | sí | no_registrable | cancelada | sí |
| 10 | 10.10.10.21 | 09:36:00 | 09:35:11.156 | 09:36:01.015 | 09:31:20.000 | 09:32:10.000 | 14 / 0 | 0 | 10.10.60.10: 14, 10.10.60.41: 30 | sí | sí | no_registrable | cancelada | sí |
| 11 | 10.10.10.21 | 09:41:00 | 09:40:11.241 | 09:41:01.138 | 09:36:20.000 | 09:37:10.000 | 9 / 0 | 0 | 10.10.60.10: 9 | sí | sí | no_registrable | cancelada | sí |
| 12 | 10.10.10.21 | 09:46:00 | 09:45:11.135 | 09:46:01.081 | 09:41:20.000 | 09:42:10.000 | 9 / 0 | 0 | 10.10.40.10: 2, 10.10.60.10: 9, 10.10.60.40: 2 | sí | no | no_registrable | cancelada | sí |
| 13 | 10.10.10.21 | 09:56:30 | 09:55:51.122 | 09:56:31.139 | 09:52:00.000 | 09:52:40.000 | 9 / 0 | 0 | 10.10.60.10: 9 | sí | sí | no_registrable | cancelada | sí |
| 14 | 10.10.10.21 | 10:02:30 | 10:01:51.142 | 10:02:31.196 | 09:58:00.000 | 09:58:40.000 | 18 / 0 | 0 | 10.10.40.10: 2, 10.10.60.10: 18 | sí | no | no_registrable | cancelada | sí |

**Cambio de propietario.** En el horizonte de alta, E abre algunos de sus flujos con el primer paquete. En el horizonte propio, ese paquete inicial ha quedado fuera y la atribución congelada asigna el resto del flujo al otro extremo:

| # | Entidad | A | Inicio del flujo más antiguo de E: alta → propio | E es primer emisor de algún flujo: alta / propio |
|---|---|---|---|---|
| 1 | 10.10.50.52 | 09:24:40 | 09:20:09.647 → 09:20:50.000 | sí / no |
| 2 | 10.10.30.10 | 09:26:50 | 09:22:50.010 → 09:25:50.630 | sí / no |
| 3 | 10.10.30.10 | 09:27:00 | 09:22:50.010 → 09:26:00.628 | sí / no |
| 4 | 10.10.30.10 | 09:27:10 | 09:22:50.010 → 09:26:10.171 | sí / no |
| 5 | 10.10.30.10 | 09:27:20 | 09:22:50.010 → 09:26:20.222 | sí / no |
| 6 | 10.10.30.10 | 09:27:30 | 09:22:50.010 → 09:26:30.170 | sí / no |
| 7 | 10.10.30.10 | 09:27:40 | 09:22:50.010 → 09:26:39.998 | sí / no |
| 8 | 10.10.10.21 | 09:28:30 | 09:24:08.045 → 09:24:40.006 | sí / no |
| 9 | 10.10.10.21 | 09:34:30 | 09:30:08.064 → 09:30:40.035 | sí / no |
| 10 | 10.10.10.21 | 09:36:00 | 09:31:28.016 → 09:32:10.001 | sí / no |
| 11 | 10.10.10.21 | 09:41:00 | 09:36:28.100 → 09:37:10.011 | sí / no |
| 12 | 10.10.10.21 | 09:46:00 | 09:41:28.070 → 09:42:10.021 | sí / no |
| 13 | 10.10.10.21 | 09:56:30 | 09:52:08.180 → 09:52:48.116 | sí / no |
| 14 | 10.10.10.21 | 10:02:30 | 09:58:08.171 → 09:58:48.148 | sí / no |

## Causa demostrada

En `953a436`, las pendientes se daban de alta con `packets_pendientes`, que es la atribución de la **última ancla tratada**, no la del horizonte propio de cada ventana.

En los 14 casos, la entidad tenía paquetes propios en (A − 60, A] según el horizonte de alta, que empieza antes. Esos paquetes pertenecen a flujos que E abrió antes del corte propio, A − 230.

Al regenerar la ventana con su horizonte, el paquete inicial queda fuera del horizonte. La función congelada `attribute_packets` asigna entonces el flujo al otro extremo, y E se queda sin paquetes ni L7 propios en (A − 60, A]. Tampoco hay observaciones de E en el EVE de esa ventana.

Por la regla causal de registro (`REGISTRO_S = 60`), esas ventanas **no son registrables**. La pendiente nunca debió existir. El motor la mantenía hasta que expiraba y escribía `ventana_no_regenerada`.

**Las 14 son pendientes creadas incorrectamente. Ninguna es una ventana que debiera evaluarse y se perdiera.**

## Corrección aplicada (`862404e`, conservada en `6b6ef82`)

1. **Cancelación explícita.** Al tratar cada ancla, una pendiente cuya entidad no tiene contenido en el horizonte propio de su ventana se **cancela** con el evento `pendiente_cancelada`, motivo `sin_contenido_en_su_horizonte`.
   - El evento guarda la evidencia: `corte_incorporacion`, `obs_pcap/eve_incorporacion`, `corte_propio`, `obs_pcap_propio`, `obs_eve_propio` y `paquetes_atribuidos_a`.
   - No se convierte en PERMIT, no se borra y queda en el log.
2. **Ventanas registrables no decididas.** Si una ventana es registrable pero no se puede decidir, se escribe en el momento como `ventana_no_evaluada`, con motivo `fila_no_generada` o `no_elegible`, `horizonte_s` e `historial_completo`. Antes podía omitirse en silencio. Este caso lo encontró la regresión.
3. **Expiración.** La expiración conserva `ventana_no_regenerada` y `pcap_incompleto`, para las pérdidas reales, y añade `corte_incorporacion`.

**Nota sobre `obs_pcap_incorporacion`.** En el evento del motor vale 3–10. En la tabla, la columna de alta da 5–18. La diferencia es esperada: el motor cuenta lo que había llegado **en el momento del alta** (p. ej. 09:23:51 para A = 09:24:40). El diagnóstico cuenta todo (A − 60, A] con el horizonte de alta.

## Regresiones

Las regresiones están en `tests/test_motor_incremental.py`.

- **`ContabilidadPendientes`.** Escenario sintético, ejecutado en dos configuraciones: eventos con retraso 3, y periódico. Cubre tres casos:
  - **Cambio de atribución:** el flujo largo de 10.10.20.22 pasa a 10.10.30.11 al podar el SYN.
  - **Límites temporales:** paquetes justo en la retícula, t0+200 y t0+300.
  - **Ventanas sin actividad reciente:** una ráfaga de 10.10.20.27 seguida de silencio.

  Las comprobaciones son independientes y usan `attribute_packets` congelado:
  - toda cancelación es no registrable en su horizonte propio y registrable en el de alta;
  - toda ventana registrable está decidida o es una `ventana_no_evaluada` explícita;
  - no aparece nada más allá del último paquete + 60 s.
- **`ResolucionPendientesUnidad`.** Límites de `anclas_con_contenido` y `con_contenido`, y `registro_cancelacion`.
- **`ExtremoAExtremo`.** Ninguna `ventana_no_regenerada`; hay canceladas con 0/0 observaciones, y las cancelaciones se cuentan en `registros_escritos`.

**Sobre `953a436` estas regresiones fallan (4 fallos).** Ver `resultados/pruebas/regresiones-sobre-953a436.txt`. Es decir, no se limitan a comprobar que los dos replays comparten el mismo comportamiento: detectan el fallo anterior.

## Observaciones que no se ocultan

- **Propietarios excluidos.** En 5 casos (n.º 1, 9, 10, 11 y 13), **todos** los paquetes de E en (A − 60, A] pasan, en el horizonte propio, a propietarios excluidos de la evaluación (sobre todo 10.10.60.10, VLAN de gestión). En otros 3 casos (8, 12 y 14), una parte. Ese tráfico no lo evalúa ninguna entidad en esa ventana.
  - Es la consecuencia de la atribución congelada y de la lista de exclusión. No es una pérdida del motor.
  - Se deja **anotado para la Etapa 3**, junto con la diferencia de horizonte de la observación 4b (230 s en el motor frente a hasta 15–20 min en el entrenamiento). No se cambia ni la atribución ni la exclusión.
- **10.10.30.10 (srv-dmz).** En sus 6 ventanas, los paquetes de E en (A − 60, A] pasan a los clientes que lo contactan (10.10.20.21–26 y el bastión). Esas entidades **sí** se evalúan con su propio contenido.
