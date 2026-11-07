# Cronograma hasta la campaña B (07-nov)

**Es un cálculo, no una autorización.** Supone que E-carga corre hoy y sale conforme. Las horas son de Perú (UTC−5). Las
duraciones de protocolo son fijas; las marcadas «estimada» salen de la campaña 3B y no se han medido con el motor actual.

## 1. Conclusión

- **La 4B y la campaña A caben el domingo**, aunque el orden importa por una restricción nueva: la rotación diaria de
  `eve.json` a las 19:00.
- **La 4B de día (7:00–15:00) empuja la campaña A hasta cerca de la medianoche y deja fuera la campaña B.**
- **Para que B tenga sitio, la 4B debe empezar esta misma madrugada, hacia la 1:20.**
- **La campaña B hoy no se puede ejecutar como formal:** no tiene protocolo ni condiciones fijadas. Es lo primero que queda
  fuera con cualquier retraso.

## 2. Lo que condiciona el calendario

| Restricción | Origen | Efecto |
|---|---|---|
| Rotación de `eve.json` a las 00:00Z, 19:00 en Perú | `logrotate.timer`, lectura de hoy, y protocolos 4B §2 y 4C §2 | Ningún archivo puede cruzar las 19:00. Si lo cruza, `s30` se detiene |
| 4B de 8 h seguidas | Protocolo 4B §2 | Si dura menos, se publica, pero **P2 no se afirma** |
| 4B con 30 min de lecturas previas I1–I8 | SALUD-CAPTURA §4.1 | No se puede declarar al instante |
| 4C exige el resultado de la 4B e I5 en los 30 min previos | Criterio único de avance | La campaña A no se solapa con el cierre de la 4B |
| 4C ≈ 2 h 45 min – 3 h con el archivo abierto | Protocolo 4C §2 | El archivo debe abrirse antes de las 15:55 o después de las 19:05 |
| Repetición offline ≈ 0,18 × el tiempo archivado (estimada) | 3B: 2 h 41 min en 28 min 34 s | ≈ 1 h 30 min en la 4B y ≈ 30 min en la 4C |
| Disco de Sensor1, 12 GB libres | Lectura de hoy, y 3B: 1,27 GB en 2 h 41 min | Unos 3,8 GB en la 4B y 1,4 GB en la 4C (estimado): cabe, con I7 ≥ 2 GB |

## 3. Tramo común: E-carga de hoy

| Hora | Duración | Paso | Quién |
|---|---:|---|---|
| Antes de 21:05 | 15 min | Apruebas la r5 y das la orden de traslado | Mark |
| Antes de 21:05 | 10 min | Fases T y F. F2 necesita tu sudo | Claude y Mark |
| 21:05–21:30 | 25 min | Fase A | Claude |
| 21:30–21:45 | 15 min | P0 inmediato y comparación | Claude |
| Antes de 21:45 | 1 min | Orden de ejecución, si la puerta G pasa | Mark |
| 21:50–22:00 | 10 min | Muestreadores, P12 y muestreo del bastión | Claude |
| 22:00 | | T_g y C1 | Claude |
| 22:00–22:15 | 15 min | Calentamiento y C1b | Claude |
| 22:15–23:15 | 60 min | Ventana fija | Automático |
| 23:17 | | Parada | Automático |
| 23:30–00:00 | 30 min | Análisis y lecturas posteriores | Claude |
| 00:00–00:20 | 20 min | Veredicto, evidencia y publicación | Claude |
| 00:20 | 10 min | Retirada de la opción (R) y decisión sobre la 4B | Mark |

## 4. Plan recomendado: 4B de madrugada

Es el único que deja sitio a B. Te obliga a estar disponible hacia las 00:20 y hacia las 12:00.

| Hora, dom 08-nov | Duración | Paso | Quién |
|---|---:|---|---|
| 00:30–01:05 | 35 min | Herramientas, archivo, muestreo y lecturas I1–I8. Incluye `CON_SUDO=1 verificar_srvdmz.sh` | Claude y Mark |
| 01:05–01:20 | 15 min | Clientes a factor 1,0, declaración y canal simulado | Claude |
| **01:20–09:20** | **8 h** | **Control 4B** | Automático, con lectura cada 30–60 min |
| 09:25–11:00 | 1 h 35 min | Cierre y repetición offline (estimada) | Claude |
| 11:00–11:40 | 40 min | `s40`, restauración y análisis (estimada) | Claude |
| 11:40–12:00 | 20 min | Publicación y decisión sobre la 4C | Claude y Mark |
| 12:00–12:45 | 45 min | Escenarios, endpoint de fuerza bruta, I1–I8 e I5 | Claude y Mark |
| 12:45–12:55 | 10 min | Archivo y clientes | Claude |
| 12:55–13:25 | 30 min | Control normal de la 4C | Automático |
| **13:25–15:21** | **1 h 56 min** | **Batería, 25 episodios** | Automático, con lectura cada 10 min |
| 15:26–16:00 | 34 min | Cierre y repetición offline (estimada) | Claude |
| 16:00–16:40 | 40 min | `s40`, restauración y análisis (estimada) | Claude |
| 16:40–17:10 | 30 min | Publicación y decisión | Claude y Mark |
| 17:10–19:05 | 1 h 55 min | Preparación de B, solo si ya existen sus condiciones | Claude y Mark |
| 19:05–22:05 | ≈ 3 h | Campaña B, si su diseño dura como la batería A (sin definir) | Sin fijar |
| 22:05–23:30 | ≈ 1 h 25 min | Cierre y análisis de B (estimada) | Claude |

**Margen de la campaña A.** El archivo puede abrirse hasta las 15:55. Respecto a las 12:45 hay unas 3 h de margen.

## 5. Plan pedido: 4B durante el día

| Hora, dom 08-nov | Duración | Paso |
|---|---:|---|
| 06:30–07:10 | 40 min | Lecturas I1–I8, clientes y declaración |
| **07:10–15:10** | **8 h** | **Control 4B** |
| 15:15–16:50 | 1 h 35 min | Cierre y repetición (estimada) |
| 16:50–17:50 | 60 min | Análisis, publicación y decisión |
| 18:15–19:05 | 50 min | Preparación de la 4C y espera a que pase la rotación |
| 19:05–19:45 | 40 min | Archivo, clientes y control de 30 min |
| **19:45–21:41** | **1 h 56 min** | **Batería** |
| 21:46–23:00 | 1 h 15 min | Cierre, repetición y análisis (estimada) |
| 23:00–23:30 | 30 min | Publicación |

Con este plan, A termina hacia las 23:30 y **B no cabe**. La batería no puede adelantarse: cualquier archivo abierto después de
las 15:55 cruza las 19:00, y la 4B no ha terminado todavía.

## 6. Qué queda fuera primero

| Orden | Qué cae | Cuándo | Consecuencia |
|---|---|---|---|
| 1 | **Campaña B** | Si a las 17:00 no hay protocolo y condiciones aprobados, o si la 4C termina después | Se deja para después del lunes. No afecta a la validez de A |
| 2 | **4B en el plan recomendado se pasa al de día** | Si no das la orden hacia la 1:00 | A acaba hacia las 23:30. B fuera |
| 3 | **Las 8 h de la 4B** | Solo si hace falta salvar la campaña A | El protocolo publica lo cubierto (mínimo 2 h) y P2 no se afirma |
| 4 | **Campaña A** | Si la 4B no se cierra el domingo | Sin resultado de la 4B no se autoriza la 4C |

Un veredicto de E-carga distinto de «estable con carga suficiente», o una condición F1–F9 sin cumplir, detiene toda la cadena.

## 7. Decisiones que siguen siendo tuyas

- Aprobar la r5 o quedarte con la franja del lunes.
- Elegir el plan de la 4B.
- Dar la petición expresa de la 4B y de la 4C.
- Aceptar el canal de control simulado de `k20` en la 4B y la 4C.
- Cerrar o declarar compatible `piloto-con-dns` (protocolo 4C §5.1).
- Fijar las condiciones de la campaña B antes de ejecutarla.
