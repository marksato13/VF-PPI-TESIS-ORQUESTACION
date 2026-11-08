# 29 · E-carga v2-2, variante r8: domingo diurno (T_g 11:00Z del 08-nov), factor de laborable forzado en los seis perfiles

**Variante r8, domingo diurno (T_g 11:00Z = 06:00 de Perú) con factor de laborable forzado en los seis perfiles** (`--forzar-laborable`, F9).
Protocolo: [`PROTOCOLO-CARGA-v2-r8.md`](../../PROTOCOLO-CARGA-v2-r8.md), commit `3f204553d8b057e3279c81ddbb3a116816767001`. Procedimiento:
[`PROCEDIMIENTO-ECARGA-v2-VARIANTE-r8.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r8.md). Herramientas: [`../28-franja-r8-1100z/`](../28-franja-r8-1100z/).
Antecedentes: r5 (`evidencia/14-ecarga-ejecucion/`, «carga insuficiente», sin cambios) y r7 (`evidencia/27-ecarga-r7-ejecucion/`, fase A conforme, sin arranque).

## 1. Veredicto, tal como sale de `evaluar_ecarga.py veredicto` (2026-11-06.4)

| Campo | Valor |
|---|---|
| `estabilidad_tecnica` | **estable con carga suficiente** |
| `habilita_condicion_3` | true |
| K1–K5 | las cinco `true` (K4a incluida) |
| S1–S15 | las quince `true` |
| `K_no_cumplen`, `K_sin_medida`, `S_no_cumplen`, `S_sin_medida`, `limitaciones`, `incoherencias` | todas vacías |
| Clase de captura | C0, sin motivos |
| Suricata | `cero_explicito`: 2 042 668 paquetes, 0 descartes (0,0 por millón) |
| I5 | no evaluado (se mide en los 30 min previos a la 4C) |

Cifras de K3 en la ventana (`comparar_suricata.py`, sin cambios): 2 037 174 paquetes, 164 ráfagas ≥ umbral, **383 flujos grandes** (umbral 50; la r5 dio 37). K4a: seis tramos de 600 s con
flujos en los seis perfiles. S2: 716 ficheros PCAP leídos sin error; S3: cadena continua de 717 ficheros, salto máximo 6,0 s; S14: sin tramos fuera ni sin medida; S7: 180 entregas
aceptadas en orden, 125 lecturas del publicador sin retroceso.

Esto cumple la condición (3) del criterio de avance. **No inicia la 4B**: sigue haciendo falta la petición expresa de Mark.

## 2. Qué se ejecutó

| Fase | Resultado |
|---|---|
| F1, F3 | Copia de `forzar_laborable.sh` = publicada (`19f07ea1…`); F3 `REQ FORZAR.con CUMPLE`. F2 lo aplicó Mark (sudo) durante la r7 y no se repitió |
| A0–A8 | Todos rc 0 (10:06–10:31Z); P0 r3y inmediato 9/9 y 51/51, P5b `CUMPLE`; paquete idéntico; `A8 CONFORME` |
| B1–B5 | Muestreadores a las 10:50:01Z (4 vivos); **P12 `CUMPLE`** con 293 s de margen; muestreo y guardia del bastión vivos |
| C1 | `ARRANCADO`, orden a las 11:00:00,09Z; seis unidades `running` |
| C1b | `REQ FORZAR.vivo CUMPLE` (seis procesos con la opción) |
| Ventana | 11:15–12:15Z (1794136500–1794140100), sin parada de la guardia |
| Parada | Automática a las 12:17Z (`fin previsto`): solicitada 12:17:04Z, confirmada 12:17:06Z, intento 1; `RESULTADO-PARADA` confirmada, rc 0, `intervencion_necesaria` false; C5 `PARADO_CONFIRMADO` |
| D | `sensor1_post` rc 0; S7 `true`; S11 `true` (hashes idénticos, dos líneas `ec78ca5 SHA256SUMS OK`); S15 `true` (P1 de los tres hosts `CUMPLE`); veredicto rc 0 |
| E | Copia del bastión verificada (`bastion-X/`, SHA256SUMS rc 0); `E2` paquete `IDENTICAS` en los tres hosts |
| R | `forzar_laborable.sh revertir` (Mark, sudo): `rc=0`, seis unidades. `R2-forzar-sin/` = `REQ FORZAR.sin CUMPLE` |

## 3. Incidencias y observaciones

- **R-forzar-sin/ (13:14:34Z) da `NO_CUMPLE`** y **R2-forzar-sin/ (13:16:43Z) da `CUMPLE`.** La primera lectura se hizo con los drop-ins todavía presentes; la segunda, tras la reversión
  de Mark. Se conservan las dos. La retirada queda comprobada por la segunda.
- **`lanzar_a1.sh r8` se detuvo a las 10:05Z** sin tocar ningún host: los lanzadores publicados apuntaban a `27-ecarga-r8-ejecucion` (error de sustitución, hallazgo 24 del procedimiento).
  Se corrigió y republicó (`c132913`) antes de ejecutar la fase A. Salida en `../28-franja-r8-1100z/lecturas/lanzar-a1-intento1-carpeta-erronea.txt`.
- **La orden de arranque de la r7 llegó tarde** (09:23Z, tras el límite de las 09:20Z) y no se arrancó nada: ver `evidencia/27-ecarga-r7-ejecucion/`.
- **D2 (lectura posterior del P0 r3y) da P5b `NO_CUMPLE`** porque se ejecutó a las 13:17Z, después del fin de la franja del P0 (13:00Z). Es de momento, no de ejecución; el P5b de la fase A (`A6`) fue `CUMPLE`. Sus 51/51 anticipables
  y los verificadores P1 sí valen para S15 y S11.
- **C5**: la primera lectura (12:18:29Z) ocurrió 12 s antes de que existiera `RESULTADO-PARADA`; se releyó a las 12:18:41Z (`C5b-relectura-resultado-parada.txt`).
- **Tareas del sistema dentro de la ventana**, declaradas en el protocolo r8 §3 y aceptadas por Mark (`francos-exportar-red`, `cron.daily`, `motd-news`, `apt-daily`, `man-db`, `cron.weekly`, `apt-daily-upgrade`).
  No se midió su efecto por separado; ningún criterio quedó afectado (todos `true`).
- **`eventos.log` del bastión** no existió durante la medición (solo se crea con eventos de parada): la guardia registró 147+ muestras con `parar: false`.

## 4. Declaraciones

- F8: nada de esta franja se usa para entrenar, calibrar ni fijar umbrales. No se cambió ningún K, S, umbral, el evaluador, el detector, el modelo IF, las características, α, los heurísticos ni la política de respuesta.
- La estabilidad queda demostrada para **esta franja, esta carga medida y un domingo por la mañana con la opción de laborable forzada**; no para la base nocturna 0,12 ni para el fondo de un día laborable (protocolo r8 §5).
- Relojes reales (F6), sin `faketime` ni cambios de zona horaria o de NTP.
