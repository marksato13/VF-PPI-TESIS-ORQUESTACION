# 24 · C1 sin escrituras antes del envío y franja del domingo 8 de noviembre (07-nov)

**Preparado y validado en seco.** No se trasladó nada, no se cambió ninguna configuración y no se arrancó ningún muestreador ni
generador. E-carga sigue sin ejecutarse ni programarse. Los hosts siguen con `902991e`. Las únicas conexiones fueron de solo
lectura y están indicadas más abajo.

| Qué | Commit |
|---|---|
| Código: `arrancar_c1.sh` 2026-11-07.3, su README y `SHA256SUMS` | `0a794f4d06ecf795c4fb991b858eeab3ed64ca98` |
| Pruebas: doble de `date`, casos nuevos y reproductor | `f3de3fc6c7cbe08700575b22a2d47167cf606584` |
| Protocolo r5, propuesta | `70b945bd3fd3b07c5bfb379e4928e2b291186ef2` |

Después de `0a794f4` solo cambian pruebas. main del producto sigue en `7b275b8`.

## 1. Caso corregido

La última comparación con T_g iba antes de `date … | tee`. Un salto de reloj o un disco lento durante esa escritura dejaba pasar la
orden fuera de hora con rc 0. Ahora el registro va antes de la última comprobación, y entre esa comprobación y el ssh no se escribe
nada. Esa comprobación también vuelve a mirar la solicitud de parada. Queda un hueco sin escrituras, inevitable: lanzar `timeout` y
`ssh` después de leer la hora.

`RESULTADO-C1` separa tres campos:
- `orden_enviada`: el ssh se lanzó;
- `t_envio`: la hora leída en la última comprobación;
- `arranque_confirmado`: `generadores.sh arrancar` devolvió rc 0.

| Caso, reloj y ssh simulados (`reproducciones/`) | Antes, `f24c922` | Después, `f3de3fc` |
|---|---|---|
| Cruce a T_g + 1 durante el registro | rc 0, `ARRANCADO`, 1 orden | **rc 2, `NO_AUTORIZADO`, 0 órdenes** |
| Cruce a T_g + 45 durante el registro | rc 0, `ARRANCADO`, 1 orden | **rc 2, `NO_AUTORIZADO`, 0 órdenes** |
| Control: registro a T_g + 0,9 s, guardia válida | rc 0, 1 orden | rc 0, 1 orden |
| Control: llega exactamente a T_g | rc 0, 1 orden | rc 0, 1 orden |
| Salto en la espera o en la puerta, a + 1 y + 45 | rc 2, 0 órdenes | rc 2, 0 órdenes |
| Parada confirmada antes de T_g | rc 2, 0 órdenes | rc 2, 0 órdenes |
| Solicitud de parada durante el registro | se emitía | rc 2, 0 órdenes |
| Solicitud de parada durante el arranque | rc 3, parada confirmada | rc 3, parada confirmada, `orden_enviada` true |
| ssh cortado tras enviar | sin separar | `orden_enviada` true, `arranque_confirmado` false |

## 2. Qué corrió sobre qué

**Sobre el commit final `f3de3fc`, una tanda cada vez y sin Docker en paralelo:**

| Corrida | Resultado | Fichero en `banco/` |
|---|---|---|
| Etapa 4A completa, 65534 | 233 pasan | `final-completa-65534.txt` |
| Etapa 4A completa, root | 233 pasan | `final-completa-root.txt` |
| Etapa 4A completa con la franja desplazada 24 h | 233 pasan | `final-franja-desplazada-65534.txt` |
| Suite del producto, sin el recorrido acelerado | 1153 pasan, 53 omitidas | `final-suite-65534.txt` |
| Regresión contra `f24c922` | 4 fallan, como se esperaba; 53 pasan | `final-regresion-f24c922-65534.txt` |
| Regresión contra `975e715` | 15 fallan, como se esperaba; 42 pasan | `final-regresion-975e715-65534.txt` |

Las corridas completas incluyen el recorrido acelerado, H2 y S7. Las cuatro regresiones que fallan contra `f24c922` son los dos cruces del
registro, la solicitud durante el registro y la que pide los campos nuevos.

**Sobre las herramientas de esta carpeta:**

| Corrida | Resultado |
|---|---|
| Variante: curva, aplicar, revertir y comprobador estricto, 65534 y root | 14 pasan en cada usuario |
| P0 r3v, derivado del P0 r3, 65534 y root | 67 pasan en cada usuario |
| P12 con los nuevos epochs, 65534 y root | 0 fallos |
| Traslado del paquete `0a794f4`, 65534 y root | 11 casos, 0 fallos |

**Lecturas reales, sin cambios en los hosts:**

| Lectura | Resultado | Fichero |
|---|---|---|
| P0 r3v anticipado, 16:35Z | rc 0, 9/9 bloques, 51/51 anticipables, paquete intacto. P5b, P8 y P12 no evaluables a esa hora | `p0-r3v/lectura-anticipada-20261107/` |
| `comprobar_forzar.sh sin`, 15:36Z | rc 0: las seis unidades, argv original y sin drop-in | `variante/lectura-real-sin-20261107/` |
| Unidades y generador, 15:23Z | `clientes_lab.py` `ae5134a7…` con la opción; `sudo -n` sin `daemon-reload` | README, sección 3 |
| Python en el bastión, 15:23Z | arranque de 0,035 a 0,042 s | Falta medir la puerta completa |
| `logrotate.timer`, 15:23Z | próxima rotación, 00:00Z | `CRONOGRAMA-HASTA-CAMPANA-B.md` |

**Evidencia previa de componentes idénticos.** `generadores.sh`, `guardia.py`, `muestreo_bastion.sh`, `puerta_c1.py`, `s7_post.sh`,
`derivar_s7.py` y `construir_entrada.py` no cambiaron desde `f24c922`. Lo que su evidencia dejó probado en `evidencia/21` y `evidencia/23` sigue
valiendo, y además volvieron a pasar en la tanda final.

**Sigue sin observarse:** C1, la puerta, el cerrojo y el traslado en el bastión real; el drop-in aplicado en systemd; `comprobar_forzar.sh con` y
`vivo` contra los hosts; P5b, P8 r5 con registro de GitHub en la franja, y P12. Un fallo de cualquiera detiene o deniega.

## 3. Variante del domingo

La revisión está en [`PROTOCOLO-CARGA-v2-r5.md`](../../PROTOCOLO-CARGA-v2-r5.md) y la secuencia en
[`PROCEDIMIENTO-ECARGA-v2-VARIANTE-r5.md`](../../ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r5.md).

| Comprobación | Resultado |
|---|---|
| `--forzar-laborable` en el generador desplegado | Existe, y el hash coincide con el del repositorio |
| Factor del domingo 03:00–04:17Z | 0,036 sin la opción; 0,12 con ella; 0,12 el lunes |
| Quién puede aplicarla | Solo Mark: `adminclientes` no tiene `daemon-reload` sin contraseña |
| Efecto en P0, P8, P12 y análisis | P0, P8, P12 y sus bancos se derivaron con la franja nueva. Los guiones del paquete reciben los epochs por argumento |
| `generadores.sh configuracion` | Acepta la variante, pero no la exige. Por eso existe `comprobar_forzar.sh` |
| AVISO de `clientes_lab.py` | No sirve de evidencia, porque las unidades llevan `StandardOutput=null` |

Las herramientas derivadas difieren de las originales solo en los valores de la franja, en el día de P5c y en la versión.

## 4. Paquete

| Qué | Valor |
|---|---|
| Carpeta | `ecarga-bastion-0a794f4`, 8 ficheros de `0a794f4` |
| `SHA256SUMS` | `fa9b4c7b661677fc2ab7d434017d67cafd85e5e77a08ea56d6b89aa4b571cf89` |
| tgz | `08b8bea3ffb7a6104a1dd0a43af52d827a4e77e2f03f2ece8e8238fd5955dfd6` |
| `ecarga/SHA256SUMS` | `8606fae185d90129282d296e76969e168248cf6d522cd40fe47dc435ed4fdff7` |

**Entorno del traslado.** Laptop, Git Bash, GNU tar 1.35, gzip 1.15 (`traslado/paquete-entorno-gitbash.txt`).

**Causa de la diferencia anterior.** La receta dejaba al entorno el formato y los permisos del tar. La versión 2026-11-07.3 fija `--format=ustar` y
`--mode=0644`. Con eso, Linux (GNU tar 1.35, gzip 1.13) reproduce el mismo tgz byte a byte
(`banco/paquete-linux-comparacion.txt`). No se reconstruyó el paquete de `f24c922`, de modo que la causa exacta de aquel hash distinto sigue sin demostrar.

Solo cambia `arrancar_c1.sh` respecto al paquete anterior. El paquete `ecarga-bastion-f24c922` nunca se trasladó.

## 5. Ficheros

- `herramientas/`: `00_referencias.sh` 2026-11-07.5, `comprobar_p8_r5.sh` y P12 de la franja nueva.
- `traslado/`: traslado 2026-11-07.3 e instalador sin cambios.
- `variante/`: aplicar, revertir, comprobador estricto y su banco.
- `p0-r3v/`: P0 de la franja nueva, sus pruebas y la lectura anticipada.
- `banco/` y `reproducciones/`: salidas de esta entrega.
