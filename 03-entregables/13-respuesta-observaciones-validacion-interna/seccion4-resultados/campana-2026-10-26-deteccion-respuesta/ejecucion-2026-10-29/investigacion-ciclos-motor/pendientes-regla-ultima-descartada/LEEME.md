# Regla descartada para «solo ventanas pendientes» (A_min = última ventana registrada + 10 s)

Corrida interrumpida de `scripts/validar_build_rows_pendientes.py` con la primera regla, hoy `--regla ultima`. Se
conserva porque documenta por qué esa regla no vale. Se ejecutó el 29-oct de 14:30 a 14:42 UTC, con 230 ciclos
evaluados.

**Resultado:** las filas fueron idénticas en todos los ciclos evaluados, pero en 2 ciclos la regla dejaba fuera
ventanas que el motor sí registró.

| Ciclo | Entidad | Ventana fuera de la regla | Causa |
|---|---|---|---|
| 07:28:40 | 10.10.20.25 | 07:25:50 | `ventana_no_evaluada` que salió de la lista de pendientes. No la genera `build_rows`, así que no hace falta cubrirla. |
| 08:47:47 | 10.10.30.10 | 08:44:00–08:44:40 | Ventanas nacidas por detrás de la última decidida (08:44:50) al llegar observaciones más antiguas. Este es un fallo real de la regla. |

**Regla que la sustituye** (`--regla no_puntuada`, por defecto): la primera ancla del rango de la entidad que no está
en `scored_windows`. Con ella, los dos ciclos salen idénticos y cubiertos (`prueba-44` y `prueba-399` en el sensor).
La comprobación de cobertura cuenta solo las decisiones.

Ficheros:

| Fichero | Contenido |
|---|---|
| `trabajador0.jsonl` | ciclos desde las 07:19 |
| `trabajador1.jsonl` | ciclos desde las 08:41 |
| `prueba.jsonl` | prueba corta inicial |
