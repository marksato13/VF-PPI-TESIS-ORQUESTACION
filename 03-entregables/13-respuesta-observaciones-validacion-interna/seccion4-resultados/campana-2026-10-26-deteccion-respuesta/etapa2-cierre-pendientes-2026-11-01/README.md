# Etapa 2: resolución de los dos pendientes del cierre técnico (1–2 nov 2026)

## Punto de partida comprobado

- **Código:** `953a436`, rama `candidato/etapa2-20261101`.
- **Documentación:** `fb394a3`, en `main`.
- No hubo cambios posteriores en ninguna de las dos ramas.
- El cierre técnico (`../etapa2-cierre-tecnico-2026-11-01/`) se conserva sin cambios como antecedente.

## Resultado en breve

| Pendiente | Resultado | Dónde |
|---|---|---|
| 1. Las 14 `ventana_no_regenerada` | **Resuelto offline.** Eran pendientes creadas incorrectamente. En su propio horizonte, las 14 ventanas no son registrables: el flujo cambia de propietario al salir el paquete inicial y E no tiene contenido en (A − 60, A]. Ahora se cancelan de forma explícita (`pendiente_cancelada`, con la evidencia). No se convierten en PERMIT ni se borran. Las regresiones fallan sobre la versión anterior | `DIAGNOSTICO-14-VENTANAS.md` |
| 2. Rendimiento sin competencia | **Resuelto offline, en el portátil.** Con el criterio fijado antes de medir: la referencia `953a436` **no** lo cumplía (r2), ni tampoco la corrección `862404e` (r3, r5). La optimizada `6b6ef82` cumple R1–R4 en todos los segmentos, con resultados idénticos (0 vectores, scores o decisiones distintos). **Pendiente en el Sensor1** | `RENDIMIENTO-SECUENCIAL.md` |
| 25 episodios y control | Mismas categorías que la referencia; población principal 15/25; control 2622, con 395/254/83 y 92. Denominador del inventario 12 223 → 12 209 (las 14 canceladas, explícitas) | `VALIDACION-25-EPISODIOS-Y-CONTROL.md` |

Matriz con la evidencia: `MATRIZ.md`. Hashes: `REFERENCIAS.md`. Comandos: `DEPENDENCIAS-Y-COMANDOS.md`.

## Qué está resuelto offline y qué no

- **Resuelto offline** (replay sobre las entradas congeladas del 3B; pruebas en el banco y en Windows):
  - la contabilidad de las pendientes;
  - el registro explícito de las ventanas no evaluables;
  - la equivalencia de la optimización;
  - el cumplimiento de R1–R4 en el portátil.
- **Requiere comprobación en el Sensor1:**
  - R1–R4 en vivo, con Suricata y tcpdump concurrentes y otro hardware;
  - el comportamiento con la rotación real.

  No se ha instalado, desplegado ni reiniciado nada.
- **Etapa 3, no iniciada:**
  - detectar el **escaneo breve** y aplicar una respuesta efectiva durante su actividad. No se declara imposible y no se alargó ningún ataque. La señal HEUR de `escaneo_breve-r3` queda disponible entre 0,17 y 0,65 s antes del fin en los replays secuenciales, frente a 0,23 s después en el publicado. **No** se presenta como detección resuelta: es un margen del reloj del replay en el portátil;
  - los paquetes que pasan a propietarios excluidos en el horizonte propio;
  - la diferencia de horizonte frente al entrenamiento (4b).

## Restricciones

- No se ha desplegado, instalado ni reiniciado ningún servicio.
- No se ha activado el enforcement.
- No se han ejecutado ataques ni campañas.
- No se ha editado el Word.
- No se ha reentrenado ni recalibrado.
- No se han cambiado los criterios de admisión ni las 28 características, las anclas, el horizonte, el modelo, los umbrales o las reglas.
- α = 0,05 / 0,03 / 0,01 sigue sin elegir.

## Contenido

- `CRITERIO-ACEPTACION-RENDIMIENTO.md`: fijado y publicado antes de medir (`baa6e92`).
- `DIAGNOSTICO-14-VENTANAS.md`, `RENDIMIENTO-SECUENCIAL.md`, `VALIDACION-25-EPISODIOS-Y-CONTROL.md`, `MATRIZ.md`, `REFERENCIAS.md`, `DEPENDENCIAS-Y-COMANDOS.md`.
- `herramientas/`: rendimiento, comparación, diagnóstico y tablas.
- `guiones/`: corridas secuenciales, análisis y ensamblado.
- `resultados/`:
  - `replays/`: 6 corridas, comprimidas con gzip;
  - `rendimiento/`, `comparaciones/`, `diagnostico/`, `pruebas/`;
  - `analisis-3b-*`.
- `MANIFIESTO.sha256`.
