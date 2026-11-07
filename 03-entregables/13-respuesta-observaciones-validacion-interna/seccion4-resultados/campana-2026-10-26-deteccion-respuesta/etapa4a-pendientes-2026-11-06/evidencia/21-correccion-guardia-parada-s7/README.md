# 21 · Corrección de C1, parada al salir del muestreo y S7 (07-nov)

**Validado solo con dobles y reloj simulado, en un contenedor sin red.** No se contactó con ningún host, no se trasladó nada y
no se arrancó ningún muestreador ni generador. E-carga sigue sin ejecutarse ni programarse. Los hosts siguen con `902991e`.

Base: documentación `55f560a`, producto `975e715`. Sin commits posteriores a esas referencias al empezar. Código en la rama
`recuperacion/etapa4a-pendientes-20261106`, commit `27bcd460399ccc7f27c7bf829ab7f24f7cf61c94`. main del producto no se ha tocado.

| Ruta | Qué es |
|---|---|
| `reproducciones/antes-975e715.txt` | Los tres fallos con los bytes de `975e715` y el bloque C1 literal publicado |
| `reproducciones/despues-27bcd46.txt` | Los mismos casos con la corrección |
| `banco/nueva-65534.txt`, `banco/nueva-root.txt` | Pruebas de E-carga, sin red: 222 pasaron en la repetición; primera pasada: 221 pasaron y 1 falló por cobertura (se conserva) como 65534, 222 pasaron en la repetición; primera pasada: 221 pasaron y 1 falló por cruce temporal (se conserva) como root |
| `banco/regresion-975e715-65534.txt` | `-k regresion` contra `975e715`: 8 failed, 42 passed, 172 deselected (8 fallos esperados). Las 8 fallas nuevas son las esperadas: son las regresiones de esta corrección |
| `banco/suite-completa-65534.txt` | Suite completa del producto: 1142 passed, 53 skipped, 2 deselected |
| `banco/banco_traslado.sh`, `banco/banco-traslado-*.txt` | Instalador sin transporte: 11 casos, 0 fallos como 65534; 11 casos, 0 fallos como root |
| `traslado/trasladar_bastion.sh`, `instalar_bastion_host.sh` | Fase T del procedimiento. **Sin ejecutar `copiar` ni `verificar`** |
| `traslado/preparar-27bcd46.txt` | Salida real de `preparar`: solo local, desde el commit publicado |
| `herramientas/00_referencias.sh` | Paso A1, versión 2026-11-07.3 |
| `guiones.sha256` | sha256 de cada guion del producto en `27bcd46` |

## Qué se validó con dobles y qué queda para el ensayo

| Validado con dobles | Queda por comprobar en una ejecución futura |
|---|---|
| Orden y decisión de C1, cerrojo y solicitud persistente | `flock` y `/proc` en el bastión real; `systemctl` real |
| Cruce con start lento, parcial, ssh cortado y start tardío, con `systemd` simulado | Cómo se comporta `systemctl stop` real con un `start` en curso |
| Parada al salir y reintentos, con reloj simulado | Un salto de reloj real; duración real de una muestra frente al límite de 60 s |
| S7 con trazas sintéticas y con la traza real del 06-nov, que da los mismos 180 entregados y aceptados que `obs-post-p4.txt` | S7 con la cadena bajo carga |
| Instalador en un contenedor | Transporte `scp` y `ssh` y fases T y A3b contra el bastión |

## Límites

- La vigilancia tras una parada dura hasta FIN. Un arranque remoto más tardío que FIN no se detectaría.
- `arrancar_c1.sh` espera, como mucho, a `CF_T_ARRANQUE` (90 s) antes de que la parada de la guardia pueda ejecutarse.
- El recorrido completo usa los epoch publicados, a 15 s simulados por segundo real. Sus K y S14 son sintéticos: no es una medida.
- A 25 s simulados por segundo real, una pasada como 65534 falló: una muestra lenta del contenedor abrió un hueco de 61 s
  simulados y S7 salió `null` por cobertura (`banco/recorrido-25x-fallo-cobertura-65534.txt`). La herramienta hizo lo correcto;
  el artefacto es la aceleración del reloj. Se bajó a 15×, se repitió (`banco/recorrido-repeticion*.txt`) y no se cambió ningún
  criterio. Este banco sigue dependiendo de la velocidad del equipo.
- A 15×, la primera suite como 65534 falló por cobertura; la primera repetición aislada midió un hueco de 62 s simulados y la segunda pasó. La suite completa repetida pasó. La primera suite como root falló al coincidir la parada con el arranque; la repetición completa pasó. Todas las salidas están conservadas en `banco/`. No se cambió el límite de 60 s.
