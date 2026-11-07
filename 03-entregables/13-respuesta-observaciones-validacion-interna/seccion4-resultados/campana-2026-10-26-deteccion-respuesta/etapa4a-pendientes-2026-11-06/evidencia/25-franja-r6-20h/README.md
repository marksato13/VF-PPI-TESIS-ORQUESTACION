# 25 · Franja r6, T_g a las 20:00 de Perú (07-nov)

**Preparado y validado en seco.** No se arrancó ningún muestreador ni generador, no se cambió ninguna configuración y no se trasladó nada nuevo.
E-carga sigue sin ejecutarse ni programarse. Protocolo: [`PROTOCOLO-CARGA-v2-r6.md`](../../PROTOCOLO-CARGA-v2-r6.md), commit `eca1faee70daa87d98c84a24103d82fe14269121`. Procedimiento:
[`PROCEDIMIENTO-ECARGA-v2-VARIANTE-r6.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r6.md). La r5 sigue activa a las 22:00 hasta que Mark apruebe la r6.

## 1. Quién usa cada hora

| Elemento | Dónde vive la hora | Resultado |
|---|---|---|
| P0 | Constantes de `p0-r3w/p0_r3.sh` y `bloques/sensor1_r3.sh` | Derivadas: franja 1794097800–1794106800, fin 1794104160 |
| P8 | `herramientas/comprobar_p8_r6.sh` | Exige la tabla de la r6, y que la r4 y la r5 sigan intactas |
| P12 | `herramientas/comprobar_p12*.sh` | Límite 1794099300 y carpeta `…20261108T0100Z` |
| Guardia, parada, arranque | `muestreo_bastion.sh`, `arrancar_c1.sh` | Sin horas fijas. Reciben FIN, PARADA y T_g por argumento |
| Muestreadores y análisis | Paquete `902991e` y `0a794f4` | Sin horas fijas. Búsqueda de epochs y fechas en los dos: nada. Reciben ventana y base por argumento |
| Generador | `factor_horario` | 0,12 con la opción en los 78 minutos de 01:00 a 02:17Z. 0,036 sin ella |

## 2. Pruebas en banco, sin red

| Corrida | Resultado | Fichero en `banco/` |
|---|---|---|
| Pruebas de E-carga del commit `f3de3fc` con la franja desplazada 26 h | 233 passed in 933.17s (0:15:33) | `franja-26h-65534.txt` |
| P0 r3w, 65534 y root | 67 pasan en cada usuario | `p0r3w-*.txt` |
| P12, 65534 y root | 0 fallos | `p12-*.txt` |
| Rotación y reentrenamiento, 13 casos, 65534 y root | 0 fallos | `rotacion-*.txt` |
| Curva, cada minuto | 0,12 y 0,036 | `curva-65534.txt` |

**Primer intento fallido, conservado.** `franja-26h-intento1-defecto-del-banco-65534.txt`: 1 fallo y 229 pasan, sin montar `OBS06`. Lo causó el banco: `banco_franja_r6.py` no desplazó el
prefijo literal `2026-11-09T03:00:0` de una aserción. El valor observado era el correcto para la franja nueva, `2026-11-08T01:00:00`. Se corrigió el banco, no el producto, y se repitió la corrida completa.

## 3. Lecturas reales, sin cambios en los hosts

| Lectura | Resultado | Carpeta en `lecturas/` |
|---|---|---|
| Traslado, 07-nov 19:43Z | rc 0, `ESTADO_FINAL=VERIFICADO` | `traslado-verificar-20261107.txt` |
| Opción, 19:43Z | rc 0, `REQ FORZAR.con CUMPLE` | `forzar-con-20261107/` |
| Rotación del día 7 con el comprobador nuevo | rc 0, `eve.json` crece y tiene eventos recientes | `rotacion-seco-20261107/` |
| Reentrenamiento del día 7 | rc 0 | `aprendizaje-seco-20261107/` |
| P0 r3w anticipado, 20:03Z | rc 0, 9/9, 51/51. P5b, P8 y P12 no evaluables a esa hora | `p0-r3w-anticipado-20261107/` |

La rotación real de esta noche no se ha observado todavía: el paso A0b la exige a las 00:05Z.

## 4. Herramientas

- Nuevas: `herramientas/comprobar_rotacion.sh` y `comprobar_rotacion_host.sh`, de solo lectura.
- Derivadas de la evidencia 24, solo con horas, versión y referencias: P0, P8, P12 y `00_referencias.sh` 2026-11-07.6.
- Sin cambios: traslado y variante de la evidencia 24. El nombre `variante-r5` y el drop-in `10-forzar-laborable-r5.conf` se mantienen, porque ya están aplicados.

`00_referencias.sh` 2026-11-07.6 sirve también para la r5 de respaldo: el 2026-11-07.5 rechazaría el commit de esta revisión.

## 5. Lanzadores de la fase A

Publicados después de la primera versión de esta carpeta, a raíz de la revisión de Mark. Son `lanzadores/lanzar_a1.sh`, `lanzar_a2.sh` y `rearmar_r5.sh`.

| Comportamiento | Banco con reloj, ssh y herramientas simulados |
|---|---|
| A0b distinto de rc 0: rc 10 y ningún paso posterior | OK |
| Cualquier otro paso con fallo: se detiene ahí | OK |
| A7b espera a las 00:35Z, también si el P0 acaba antes | OK, lanzado en 1794098110 con mínimo 1794098100 |
| `rearmar_r5.sh` mueve los A* a `intento-r6-20h/` y comprueba sus hashes después de mover | OK |
| Se niega a repetir sobre un A0.txt existente | OK |
| Se niega a rearmar si la r6 pasó de la fase A, si su carpeta existe en los hosts, o a la hora de la r5 | OK |
| La r5 corre después del rearme, y la evidencia r6 sigue intacta | OK |

19 casos, 0 fallos (`banco/lanzadores-gitbash.txt`). El primer intento se colgó en el banco, no en los lanzadores: un caso dejaba el reloj simulado parado dentro de la espera de A7b. Se conserva su salida parcial, en `banco/lanzadores-intento1-colgado-defecto-del-banco.txt`.
Todo con dobles: los lanzadores no se han ejecutado contra los hosts.
