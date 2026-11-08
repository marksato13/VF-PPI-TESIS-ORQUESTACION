# 28 · Franja r8, T_g a las 11:00Z del domingo 8 (06:00 de Perú)

**Preparado y validado en seco.** No se arrancó ningún muestreador ni generador y no se copió nada a los hosts. E-carga r8 no se ha ejecutado ni
programado. Protocolo: [`PROTOCOLO-CARGA-v2-r8.md`](../../PROTOCOLO-CARGA-v2-r8.md), commit `3f204553d8b057e3279c81ddbb3a116816767001`. Procedimiento:
[`PROCEDIMIENTO-ECARGA-v2-VARIANTE-r8.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r8.md).

## 1. Por qué existe

La r7 (T_g 09:30Z) pasó la fase A y el P0 conformes, pero la orden de arranque llegó a las 09:23Z, tras el límite de las 09:20Z, y no arrancó
(`evidencia/27-ecarga-r7-ejecucion/`). La franja no se desplaza sin protocolo nuevo: la r8 repite la r7 con todos los epochs +5 400 s. Mark eligió
las 11:00Z como la franja más próxima viable y aceptó que entren en la ventana tareas del sistema (protocolo r8 §3).

## 2. Quién usa cada hora

| Elemento | Dónde vive la hora | Resultado |
|---|---|---|
| P0 | `p0-r3y/p0_r3.sh` y `bloques/sensor1_r3.sh` | Franja 1794133800–1794142800, fin 1794140160 (12:16Z). P5c sigue exigiendo domingo UTC |
| P8 | `herramientas/comprobar_p8_r8.sh` | Exige la tabla de la r8 en `3f20455` y que las de la r4 y la r5 sigan intactas |
| P12 | `herramientas/comprobar_p12*.sh` | Límite 1794135300 (10:55Z) y carpeta `…20261108T1100Z` |
| Fase A | `lanzadores/lanzar_a1.sh` y `lanzar_a2.sh`, solo `r8` | A1 desde 1794132300 (10:05Z), P0 desde 1794133800 (10:30Z), puerta antes de 1794135000 (10:50Z) |
| Guardia, parada, arranque | `muestreo_bastion.sh`, `arrancar_c1.sh` | Sin horas fijas. Reciben FIN, PARADA y T_g por argumento |
| Generador | `factor_horario` de `clientes_lab.py` `ae5134a7…` | 1,0 con la opción de 11:00 a 12:17Z (banda 8–13Z) |

## 3. Pruebas en banco, sin red

| Corrida | Resultado | Fichero en `banco/` |
|---|---|---|
| P0 r3y, contenedor sin red, 65534 y root | 67 pasan en cada usuario | `p0r3y-*.txt` |
| P12, contenedor sin red, 65534 y root | 0 fallos | `p12-*.txt` |
| Lanzadores r8, con reloj, ssh y herramientas simulados | 15 casos, 0 fallos | `lanzadores-gitbash.txt` |

## 4. Lecturas reales, sin cambios en los hosts

| Lectura | Resultado | En `lecturas/` |
|---|---|---|
| P8 r8 sobre lo publicado, 09:30Z | rc 0, `REQ P8 CUMPLE`, push de `3f20455` a las 09:29:37Z | `p8r8-prueba-20261108/` |
| P0 r3y anticipado, 09:32Z | rc 0, 9/9 bloques, 51/51 anticipables. P5b, P8 y P12 no evaluables a esa hora | `p0-r3y-anticipado-20261108/` |

## 5. Herramientas

- Derivadas de la 26 (r7): lanzadores, `leer_temporizadores.sh`, `comprobar_p12*.sh`, y `banco_lanzadores.sh`, con las horas de la r8.
- Derivadas de la evidencia 24: P0 (`p0-r3y`) y P8 (`comprobar_p8_r8.sh`).
- Derivada de la 25: `00_referencias.sh` 2026-11-08.8, que exige además `e8fbd00`, `0446555` y `3f20455`, y verifica las evidencias 18 a 26 y 28.
- Sin cambios: traslado y variante de la evidencia 24. El drop-in `10-forzar-laborable-r5.conf` aplicado en la r7 se mantiene.
