# 23 · C1 relee T_g antes de emitir y estabilidad del banco (07-nov)

**Validado solo con dobles y reloj simulado, en contenedores sin red.** No se contactó con ningún host, no se trasladó nada y
no se arrancó ningún muestreador ni generador. E-carga sigue sin ejecutarse ni programarse. Los hosts siguen con `902991e`.

| Qué | Commit (rama `recuperacion/etapa4a-pendientes-20261106`) |
|---|---|
| Código: `arrancar_c1.sh` 2026-11-07.2 y su `SHA256SUMS` | `f24c9221dc99b6f716a27d5ce55f9ea0dfa795cc` |
| Pruebas: `1209564`, `2bc1ea8`, `70ce96a` y `ea3f356` | `ea3f3561cac20021cfcefed338600e7c938e93a6` |

Después de `f24c922` solo cambian pruebas. main del producto no se ha tocado. Base de los hosts: `902991e`, sin cambios.

## Caso corregido

C1 comprobaba T_g al entrar y luego esperaba. Si el reloj superaba T_g durante esa espera, o mientras se evaluaba la puerta,
emitía la orden igualmente. Ahora relee la hora dentro del cerrojo, después de la puerta y justo antes de emitir. Sin tolerancia:
la comparación es en segundos enteros, como la del resto del guion. La comprobación inicial se conserva.

| Caso (`reproducciones/`) | Antes, `27bcd46` | Después, `ea3f356` |
|---|---|---|
| Salto en la espera a T_g + 45 y a T_g + 1 | rc 0, 1 orden, 6 vivos | rc 2, 0 órdenes, 0 vivos |
| Salto al evaluar la puerta a T_g + 45 y a T_g + 1 | rc 0, 1 orden, 6 vivos | rc 2, 0 órdenes, 0 vivos |
| Control: llega exactamente a T_g | rc 0, 1 orden | rc 0, 1 orden |

## Corridas y versión de cada una

Una tanda cada vez, sin otra prueba Docker en paralelo.

**Tanda final, sobre `ea3f356`** (es la versión publicada):

| Salida | Resultado |
|---|---|
| `banco/final-completa-65534.txt` | 227 passed in 1000.46s (0:16:40) |
| `banco/final-completa-root.txt` | 227 passed in 997.92s (0:16:37) |
| `banco/final-sinrecorrido-65534.txt` | 226 passed, 1 deselected in 367.31s (0:06:07) |
| `banco/final-sinrecorrido-root.txt` | 226 passed, 1 deselected in 327.62s (0:05:27) |
| `banco/final-recorrido-1.txt` | 1 passed, 226 deselected in 608.50s (0:10:08) |
| `banco/final-recorrido-2.txt` | 1 passed, 226 deselected in 608.91s (0:10:08) |
| `banco/final-recorrido-3.txt` | 1 passed, 226 deselected in 609.01s (0:10:09) |
| `banco/final-recorrido-4.txt` | 1 passed, 226 deselected in 608.85s (0:10:08) |
| `banco/final-h2-s7-detalle-65534.txt` | ====================== 34 passed, 52 deselected in 31.14s ====================== |
| `banco/final-regresion-975e715-65534.txt` | 12 failed, 42 passed, 173 deselected in 101.19s (0:01:41) |
| `banco/final-regresion-27bcd46-65534.txt` | 4 failed, 50 passed, 173 deselected in 107.23s (0:01:47) |
| `banco/final-suite-65534.txt` | 1147 passed, 53 skipped, 2 deselected in 385.22s (0:06:25) |
| `banco/final-traslado-65534.txt` | casos=11 fallos=0 |
| `banco/final-traslado-root.txt` | casos=11 fallos=0 |

`final-regresion-975e715` falla en las 8 regresiones anteriores y en las 4 nuevas. `final-regresion-27bcd46` falla solo en las 4
nuevas: son las que demuestran el defecto. Esos fallos son los esperados. `final-recorrido-1` y `-3` corren como 65534; `-2` y `-4`,
como root. La exclusión de `final-sinrecorrido-*` y las 2 deseleccionadas de la suite salen de `-k "not recorrido"`; el
recorrido está en `final-completa-*` y `final-recorrido-*`. Las 53 omisiones de la suite son las que lista su salida: requieren
root, nft, node o el repositorio de documentación. `final-h2-s7-detalle` lista por nombre las pruebas de parada y S7.

`banco/puntual-*.txt`: regresiones puntuales previas a la tanda, con `ea3f356` y contra `27bcd46`.

**Antecedentes: no aprueban esta versión.** Se conservan como historia.

| Salida | Versión | Resultado |
|---|---|---|
| `evidencia/21-correccion-guardia-parada-s7/banco/*-primera-*`, `recorrido-*` | `27bcd46` | fallos por cobertura de S7 y por parada durante el arranque |
| `evidencia/22-banco-temporizacion-8x-pendiente/` | `27bcd46` + diff de 4 líneas de pruebas (8×) | 1 fallo como 65534 y 1 como root |
| `banco/diag-margen-tg.txt` | `27bcd46`, solo el guion | carrera de T_g medida |
| `banco/antecedentes/1209564/estable-1-65534.txt` | `1209564` | 222 passed in 981.79s (0:16:21) |
| `banco/antecedentes/1209564/estable-1-root.txt` | `1209564` | 1 failed, 221 passed in 968.23s (0:16:08) |
| `banco/antecedentes/1209564/estable-2-65534.txt` | `1209564` | 1 failed, 221 passed in 965.81s (0:16:05) |
| `banco/antecedentes/1209564/estable-2-root.txt` | `1209564` | 222 passed in 988.10s (0:16:28) |
| `banco/antecedentes/2bc1ea8/final-completa-65534.txt` | `2bc1ea8` | 222 passed in 982.80s (0:16:22) |
| `banco/antecedentes/2bc1ea8/final-completa-root.txt` | `2bc1ea8` | 222 passed in 984.10s (0:16:24) |
| `banco/antecedentes/2bc1ea8/final-suite-65534.txt` | `2bc1ea8` | 1142 passed, 53 skipped, 2 deselected in 467.01s (0:07:47) |
| `banco/antecedentes/70ce96a/final-completa-65534.txt` | `70ce96a` | 227 passed in 986.39s (0:16:26) |
| `banco/antecedentes/70ce96a/final-completa-root.txt` | `70ce96a` | 227 passed in 993.50s (0:16:33) |
| `banco/antecedentes/70ce96a/final-suite-65534.txt` | `70ce96a` | 1147 passed, 53 skipped, 2 deselected in 484.66s (0:08:04) |
| `banco/antecedentes/70ce96a/fallo-recorrido-tg-acelerado-65534.txt` | `70ce96a` | =================== 1 failed, 85 passed in 292.44s (0:04:52) =================== |

La evidencia 22 se publica tal como quedó: su frase «sin publicación» describe el estado del 07-nov a las 01:44 (−05:00).

## Causas de los fallos intermitentes

| Fallo | Causa | Estado |
|---|---|---|
| `test_puerta_solicitud_previa[PARADA-NO-CONFIRMADA]`, «T_g ya pasó al llegar a C1» | La prueba fijaba `T_g = int(now) + 1`: margen casi nulo al final de un segundo | **Demostrada**: 18/40 a fracción ,985; 0/40 a ,900 y a ,050; 0/12 con la corrección |
| `test_regresion_cruce_arranque_parcial`, rc 2 en vez de 3 | Compatible con la misma causa | **No demostrada**: esa salida no registró el motivo. La prueba ahora lo imprime |
| `test_cruce_parada_no_confirmada_exige_intervencion`, «cerrojo ocupado» (`1209564`, 2 de 4 tandas) | Efecto de la primera corrección: T_g se acercó a una parada fijada a 3 s | Corregida en `2bc1ea8` y con más margen en `ea3f356`. El guion denegó sin emitir órdenes |
| `test_recorrido_completo_con_reloj_simulado`, rc 2 «T_g ya pasó antes de emitir» (`70ce96a`) | A 8×, un segundo simulado son 125 ms reales y la puerta cruzó a T_g + 1. Lo destapó la nueva comprobación | **Demostrada por el motivo registrado**. En `ea3f356` el reloj se retiene dentro del segundo de T_g hasta emitir, sin depender de la velocidad. El guion hizo lo correcto |
| S7 `null` en el recorrido a 25× y 15× | Una muestra lenta abrió huecos de 61–62 s simulados. Artefacto de la aceleración; el recorrido va a 8× | El límite de 60 s no cambia |

Ningún fallo se debió a un guion de producción. El caso de esta entrega sí es un defecto del guion, y no era intermitente:
se reproduce siempre con reloj controlado.

## Qué se validó con dobles y qué queda para el laboratorio

| Validado con dobles | Queda por comprobar |
|---|---|
| Orden de decisión de C1 y relectura de la hora, con reloj y ssh simulados | Traslado real y `flock` en el bastión (T y A3b) |
| Parada al salir del muestreo y S7 (`null`, `true`, `false`), reproducciones H2 y H3 | Un salto de reloj real y S7 con la cadena bajo carga |
| Instalador del paquete nuevo, sin transporte | `scp` y `ssh` reales; `systemctl` real con un `start` en curso |

## Límites

- Sin tolerancia, el margen real entre detectar T_g y emitir es lo que queda de ese segundo: unos 0,8 s, porque la espera sondea
  cada 0,2 s. Si la puerta tarda más en el bastión, C1 da rc 2 y el ensayo no arranca. Es el lado seguro, pero perdería la
  franja. **El tiempo de la puerta en el bastión no se ha medido**; haría falta una franja nueva.
- Los casos con reloj real tienen márgenes de segundos. Las tandas reducen la intermitencia, pero no demuestran inmunidad ante un
  equipo muy cargado. El recorrido a 8× sigue dependiendo de la velocidad del equipo.

## Herramientas y traslado

- `herramientas/00_referencias.sh` 2026-11-07.4: pasos A1 y T1. Fija la rama en `ea3f356` y exige `deploy/` idéntico a `f24c922`.
- `traslado/trasladar_bastion.sh` 2026-11-07.2 e `instalar_bastion_host.sh`: bytes de `f24c922`, `SHA256SUMS` `439ccc0f34730af26245ac8b060dbca658e1146fb31fc2e3807b8fb16750466e`, tgz `3cc7aa3fd424fbdb253ada8b8d840d046e83e7e629fac1221a7a2aa02acada9a`.
  **Sin ejecutar `copiar` ni `verificar`.** `traslado/preparar-f24c922.txt` es la salida real de `preparar`, solo local.
- Respecto a `27bcd46`, de los 8 ficheros solo cambia `arrancar_c1.sh`.
- Las herramientas de la evidencia 21 quedan como historia: `ecarga-bastion-27bcd46` ya no se traslada.
