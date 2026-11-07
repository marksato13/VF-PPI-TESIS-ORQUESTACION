# 20 · Procedimiento final de E-carga v2: herramientas y evidencia (07-nov)

Sin ejecución en el laboratorio: en esta entrega no se contactó con ningún host. E-carga NO ejecutada ni programada.

El procedimiento está en
[`../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-FINAL.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-FINAL.md).

| Ruta | Qué es |
|---|---|
| `herramientas/00_referencias.sh` | Paso A1: referencias, manifiestos y copia publicada. Solo lectura |
| `herramientas/comprobar_p8.sh` | P8 documental: commit, tabla §3.2 y registro de pushes de GitHub. Solo lectura |
| `herramientas/comprobar_p12.sh`, `comprobar_p12_host.sh` | P12 con las marcas reales del arranque. Solo lectura. El sha del guion del host es `b45e950b9ad60fb3a9a1319705a3822de5ca034d94f5cf1eb9d81202c2459d5b` |
| `banco/banco_p12.sh` | Banco con marcas simuladas; no arranca nada |
| `banco/banco-p12-65534.txt` | Docker sin red, 65534: 15 casos, fallos=0 |
| `banco/banco-p12-root.txt` | Docker sin red, root: 14 casos y 1 omitido (`chmod 000`, sin efecto como root), fallos=0 |
| `banco/referencias-primera-pasada-rc1.txt` | Salida de `00_referencias.sh` 2026-11-07.1 sobre `ea9ebcd`: rc 1 por el límite de ruta de `git.exe`, corregido en la .2 |
| `p8-verificacion-20261107T020848Z/` | Salida real de `comprobar_p8.sh`: `REQ P8 CUMPLE`, rc 0 |

Límites:
- `comprobar_p12.sh`, la parte que viaja por ssh, no se ha probado contra Sensor1.
- `00_referencias.sh` se ejecuta contra lo publicado después del commit; su salida se informa en la respuesta de cierre.
- P8 se repite en el paso A5. P5b y P12 siguen sin observar.
