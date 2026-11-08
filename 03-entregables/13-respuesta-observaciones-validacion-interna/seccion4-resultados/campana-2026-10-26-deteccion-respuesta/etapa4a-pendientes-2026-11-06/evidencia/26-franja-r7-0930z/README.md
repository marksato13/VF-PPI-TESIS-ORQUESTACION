# 26 · Franja r7, T_g a las 09:30Z del domingo 8 (04:30 de Perú)

**Preparado y validado en seco.** No se arrancó ningún muestreador ni generador, no se cambió ninguna configuración y no se
copió nada a los hosts. E-carga r7 no se ha ejecutado ni programado. Protocolo:
[`PROTOCOLO-CARGA-v2-r7.md`](../../PROTOCOLO-CARGA-v2-r7.md), commit `04465555434ea67ec2a40fd61451e70291dc3480`. Procedimiento:
[`PROCEDIMIENTO-ECARGA-v2-VARIANTE-r7.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r7.md). El veredicto de la
r5 («carga insuficiente», `evidencia/14-ecarga-ejecucion/`, `e8fbd00`) se conserva sin cambios.

## 1. Por qué las 09:30Z y no las 08:00Z

Mark priorizó un arranque a las 03:00 de Perú (T_g 08:00Z, fase A a las 02:05). A las 00:50 de Perú, preparar, publicar y
verificar la r7 con todas las comprobaciones, y dejar margen para la aprobación y el sudo de F2, no cabía antes de las 02:05.
La primera franja viable con base 1,0 durante toda la medida es T_g 09:30Z.

## 2. Quién usa cada hora

| Elemento | Dónde vive la hora | Resultado |
|---|---|---|
| P0 | Constantes de `p0-r3x/p0_r3.sh` y `bloques/sensor1_r3.sh` | Franja 1794128400–1794137400, fin 1794134760 (10:46Z). P5c sigue exigiendo domingo UTC |
| P8 | `herramientas/comprobar_p8_r7.sh` | Exige la tabla de la r7 en `0446555`, y que las de la r4 y la r5 sigan intactas |
| P12 | `herramientas/comprobar_p12*.sh` | Límite 1794129900 (09:25Z) y carpeta `…20261108T0930Z` |
| Fase A | `lanzadores/lanzar_a1.sh` y `lanzar_a2.sh`, solo `r7` | A1 desde 1794126900, P0 desde 1794128400, puerta antes de 1794129600 |
| Guardia, parada, arranque | `muestreo_bastion.sh`, `arrancar_c1.sh` | Sin horas fijas. Reciben FIN, PARADA y T_g por argumento |
| Muestreadores y análisis | Paquete `902991e` y `0a794f4` | Sin horas fijas (búsqueda hecha para la r6, sin cambios desde entonces) |
| Generador | `factor_horario` de `clientes_lab.py` `ae5134a7…` | 1,0 con la opción de 09:30 a 10:47Z (banda 8–13Z); 0,3 sin ella |

Todos los epochs se obtienen sumando 23 400 s a los de la r5, con el mismo generador que la r6 (`build26.py`, conservado en el
scratchpad de la sesión). Ningún epoch de la r5 queda sin desplazar en el procedimiento.

## 3. Pruebas en banco, sin red

| Corrida | Resultado | Fichero en `banco/` |
|---|---|---|
| P0 r3x, contenedor sin red, 65534 y root | 67 pasan en cada usuario | `p0r3x-*.txt` |
| P12, contenedor sin red, 65534 y root | 0 fallos | `p12-*.txt` |
| Lanzadores r7, con reloj, ssh y herramientas simulados | 15 casos, 0 fallos | `lanzadores-gitbash.txt` |

Los lanzadores se niegan a empezar antes de las 08:35Z, sin F3 conforme o con F3 `NO_CUMPLE`, sobre un `A0.txt` existente y a
la hora del P0; A2 se niega antes de las 09:00Z y desde las 09:20Z; P0 rc 5 detiene antes de A7 y A8; A8 exige ssh rc 0 y
`LIBRE` y consulta la carpeta `…T0930Z`. Escriben en `evidencia/27-ecarga-r7-ejecucion/` y no tocan la 14.

No se repitió la batería de 233 pruebas del producto con la franja desplazada: el producto no tiene horas fijas y no ha
cambiado desde la r6 (`f3de3fc`).

## 4. Lecturas reales, sin cambios en los hosts

| Lectura | Resultado | En `lecturas/` |
|---|---|---|
| Temporizadores y cron de los cuatro hosts, 05:56Z | Ninguna tarea entre 09:20 y 10:48Z. `apt-daily` de clientes a las 09:03:51Z (P0); `francos-exportar-red` del bastión hacia 11:15–11:20Z y `motd-news`/`cron.daily` a las 11:25Z (lecturas). Detalle en el protocolo §3 | `temporizadores-20261108/` |
| Copia de `forzar_laborable.sh` en clientes, 05:56Z | sha256 `19f07ea1…`, igual al publicado; sin drop-ins aplicados | `temporizadores-20261108/clientes-y-variante.txt` |
| P8 r7 sobre lo publicado, 06:04Z | rc 0, `REQ P8 CUMPLE`, push de `0446555` a las 06:04:08Z | `p8r7-prueba-20261108/` |
| P0 r3x anticipado, 06:04Z | rc 0, 9/9 bloques, 51/51 anticipables. P5b, P8 y P12 no evaluables a esa hora | `p0-r3x-anticipado-20261108/` |

## 5. Herramientas

- Nuevas: `herramientas/leer_temporizadores.sh` (A0c, informativo, solo lectura) y los lanzadores r7.
- Derivadas de la evidencia 24, solo con horas, versión y referencias: P0 (`p0-r3x`), P8 (`comprobar_p8_r7.sh`) y P12.
- Derivada de la evidencia 25: `00_referencias.sh` 2026-11-08.7, que exige además `e8fbd00` y `0446555` y verifica la 26.
- Sin cambios: traslado y variante de la evidencia 24. La carpeta `variante-r5` y el drop-in `10-forzar-laborable-r5.conf` conservan su nombre.
