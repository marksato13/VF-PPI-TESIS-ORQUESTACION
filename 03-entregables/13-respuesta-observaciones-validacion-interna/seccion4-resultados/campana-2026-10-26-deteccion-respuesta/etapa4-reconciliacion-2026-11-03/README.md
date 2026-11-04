# Reconciliación investigación ↔ demostración antes de la 4A (2026-11-03)

> **Estado vigente (actualizado el 2026-11-04).** La **base de recuperación está preparada y verificada offline**.
> **La P0 está hecha.** La evidencia [p0-srvdmz-2026-11-04.md](evidencia/laboratorio/p0-srvdmz-2026-11-04.md)
> confirma que, a las 01:39 UTC del 04-nov, el agente v1 de srv-dmz estaba desactivado (timer `disabled`/`inactive`,
> servicio `inactive`) y su tabla `inet cyberflow` retirada, con el volcado guardado. La petición escrita de la 4A
> (B2) llegó el 04-nov y su ejecución se documenta en `../etapa4a-instalacion-2026-11-04/`.
> **Esta carpeta no instaló nada.** El estado del laboratorio en cada momento se comprueba con lecturas nuevas
> antes de actuar: una lectura histórica no garantiza el estado actual.
>
> *Antecedente, veredicto original del 2026-11-03 (se conserva):* la base de recuperación preparada y verificada
> offline; laboratorio NO recuperado; 4A bloqueada porque el agente v1 de srv-dmz aplicaba restricciones de verdad
> (`--aplicar`) desde la demo, con un LIMIT sobre un cliente legítimo (10.10.20.21) a las 01:04 UTC del 04-nov.

## 1. Tres versiones que no deben confundirse

| Nombre | Qué es | Referencia |
|---|---|---|
| **Histórica desplegada** | Lo que corría en el Sensor1 antes de la demo: motor **24f8a80** con la cadena v1 del snapshot as-deployed **f57ca00** (lectura del 2-nov). El agente v1 de srv-dmz estaba disabled/inactive | `etapa4-preparacion-2026-11-02/ESTADO-OBSERVADO-LABORATORIO.md` |
| **Candidata de investigación** | `candidato/etapa3-20261102` @ **3a9f26b**. El código que se instala es **ec78ca5** (cierre de la Etapa 3) y las herramientas y pruebas son posteriores (117d47d, acc6588, f9cf801, 02735b3, 3a9f26b). Política **`if_senal`**: el IF puntúa y da señal; las reglas autorizan | documentación 902f25b (`etapa4-preparacion-2026-11-02/`, `etapa4-correcciones-2026-11-02/`) |
| **Demostración** | Commits de as-deployed del 2-nov 19:56 al 3-nov 18:44: `6d560d8` … `866ebbf`, `04e8b99`, `4ea1c68` … `3f1bd9c` y la vuelta atrás `ca66db5`. Etiqueta `demo-politica-AC-2026-11-03` = 3f1bd9c | rama `as-deployed-sensor-20261006` |

**Vigencia de las referencias** (comprobada en git, no en notas): 3a9f26b sigue siendo la punta de
`origin/candidato/etapa3-20261102` y nadie la ha tocado desde el 2-nov. ec78ca5 es su antecesor. 902f25b es
antecesor de `main` en la documentación, y el único commit posterior (ce8050b) solo toca el PPTX de la
presentación. Las dos carpetas existen y están intactas. **No ha habido avances posteriores en la candidata:**
todos los cambios del 2 y 3 de noviembre fueron a as-deployed. `main` del producto (7b275b8) no es la candidata
ni el sistema desplegado (el Sensor1 corre 24f8a80) y tiene un cambio local sin confirmar en `dashboard.py`.

## 2. Qué cambió de verdad durante la preparación de la presentación

Detalle por componente en [COMPARACION-COMPONENTES.md](COMPARACION-COMPONENTES.md). En resumen:

| Componente | Cambio de la demo | ¿Sigue en el laboratorio? |
|---|---|---|
| Reglas (`heuristicos.py`) | 866ebbf: ráfaga con ratio de puertos 0,2, `http_abuse` 200. 4ea1c68: `icmp_flood` → BLOCK | **No**: ca66db5 las retiró. El Sensor1 tiene la versión anterior a la demo (`ec0fe9e`, 2026-10-06.2) |
| Publicador v1 | 866ebbf: margen 0,05 y 3 ventanas. 4ea1c68: el modelo solo no publica (política A). ca66db5: vuelta a que el modelo actúe (margen 0, 1 ventana), conservando la liberación «Preparar demo» por el feed firmado y el desempate a favor de la regla | **Sí**, la de ca66db5 (`8d368d9`) |
| Agente v1 srv-dmz | alcance `nunca`/`solo` (.30 y .21), liberación humana, gracia, acuse | **Sí**, y además **activado**: timer enabled/active desde el 03-nov 02:50 UTC con `--aplicar` |
| Relé v1 | devuelve el acuse (e41480a) | Sí |
| Panel | recorte, Escenario en vivo, acuse, Preparar demo, panel ligero, contadores, G1–G3 | Sí (`9604d11` = ca66db5) |
| Pruebas | `tests/conftest.py` omite 16 pruebas de la política de la demo | Solo en as-deployed. Otra prueba de la misma política (n.º 17) falla sin omitir ([PRUEBAS-Y-OMISIONES §3](PRUEBAS-Y-OMISIONES.md#3-las-16-omisiones-de-testsconftestpy-rama-as-deployed-ca66db5)) |

## 3. Qué permaneció intacto

Comprobado por hash en el laboratorio y en todas las referencias:

- las 28 características, sus fórmulas (extractores con el mismo blob en todas las referencias) y su orden;
- el modelo (pipeline IF con el escalador dentro, sha256 `df547da0…a2fd60`, igual al `model_sha256` del manifiesto);
- el manifiesto (`b3ad6805…aa2a9e7`) y el umbral desplegado (−0,5693969936);
- las exclusiones del motor, el motor 24f8a80 del Sensor1 y el relé de transporte;
- toda la rama candidata (3a9f26b) y las evidencias anteriores: ninguna carpeta previa se ha modificado.

No cambiaron ni las características ni el modelo: se comprobó con los bytes, no se dedujo.

## 4. Base que se recomienda recuperar y por qué

**Rama `recuperacion/etapa4a-20261103` @ b2f2994**: es 3a9f26b más una corrección del instalador de srv-dmz.
El código que se instala sigue siendo **ec78ca5**: `paquete_candidata.sh` para si difiere, y el paquete
reconstruido tiene exactamente los mismos hashes de código que el del 2-nov. Las razones:

1. Es lo que validó la investigación: replays del 3B, banco de la vía rápida y retirada de las 36 decisiones
   tardías de `auth_failure` y de las 8 renovaciones sin evidencia.
2. Su política (`if_senal` + reglas que autorizan) separa por diseño la anomalía de la medida. La política A de la
   demo se parecía, pero sin señales separadas, sin `evento_id` y con umbrales de reglas ajustados a ojo.
3. ca66db5 **no** puede ser la base: su motor (7b275b8) no es el que corre, su publicador mezcla la política de las
   campañas con funciones de la demo, y su suite tiene un fallo sin omitir.

**Correcciones de la demo, con su destino:**

| Corrección | Propósito | Pruebas | Compatibilidad | Recomendación |
|---|---|---|---|---|
| Ratio de ráfaga 0,2 / `http_abuse` 200 | quitar los FP de los clientes en la demo | 3 pruebas de la demo | La candidata resuelve lo mismo con ratio 0,1 y vistas HTTP | **No** trasladar |
| `icmp_flood` | bloquear el flood ICMP de la demo | 2 pruebas | No existe en la candidata: con `if_senal`, un flood ICMP solo da señal del IF | Propuesta aparte (escenario, control y umbral propios). Fuera de 4A–4C |
| Política A (el modelo solo no actúa) | sin FP del modelo en la demo | 4 + 6 pruebas | Equivale en espíritu a `if_senal` | No se porta: ya está en la candidata, mejor resuelta |
| Alcance `nunca`/`solo`, liberación humana, gracia, acuse | operar la respuesta activa con seguridad | sin suite propia en la candidata | Agente v1. El v2 tiene `NUNCA_BLOQUEAR` y perfiles, no liberación ni acuse | **Útil para la campaña B.** Portarla al v2 en una rama aparte, con pruebas, antes de la campaña B. No hace falta para 4A–4C (sombra) |
| Panel G1–G3 y mejoras visuales | presentación | pruebas del panel | Lee el log con la política v1; no ve el feed v2 | Se conservan en as-deployed. Integrarlas exige leer señales, traza del publicador v2 y traza del agente v2, y separar anomalía, decisión, medida publicada, aplicación confirmada y efecto observado |

## 5. Correcciones offline hechas y cómo se verificaron

| # | Pendiente | Estado al empezar | Corrección | Verificación |
|---|---|---|---|---|
| 1 | `g01` contaba su propio shell con `pgrep -fc 'generar_campana.py --config'` (línea 56) y listaba el envoltorio (línea 83) | **seguía**: paraba siempre con «ya hay un generador» | `guiones/g01_lanzar_bateria_e4.sh`: `gen_pids` lee el argv real (python + `generar_campana.py` + `--config` como argumentos separados); bloques remotos por `bash -s`; para si el generador no arranca | Banco con SSH simulado, órdenes inofensivas y contenedor desechable (`banco-g01/ensayo_g01.sh`): A el original falla, B lanza con 1 PID correcto, C detecta un generador vivo, D ignora los señuelos. **A–D OK**. El original se conserva |
| 2 | C0 frente a C0/C1 | **seguía**: PROTOCOLO-4C §6 y §8 admitían C1, contra SALUD-CAPTURA §3/§4.3 | `documentos-corregidos/PROTOCOLO-4C-CAMPANA-A.md`: solo C0 en la población principal; C1 aparte con `fuera:` | revisión cruzada: `C1` no aparece como admitido en ningún documento corregido |
| 3 | Tráfico SSH de gestión a la Kali | **seguía**: canal persistente en la batería y ninguno en el control 4B ni en el control de 30 min | `guiones/k20_canal_control_simulado.sh` (mismo ControlMaster, keepalive 30 s, una sesión por minuto con un JSON del tamaño del permiso, sin lanzar nada); PROTOCOLO-4B §4b/§5 y 4C §5.4/§5.5 corregidos, con la medida del volumen por ventana en los tres tramos | `banco-g01/ensayo_k20.sh` **8/8** |
| 4 | Etiquetas de detección oportuna | **seguía**: las «emisiones oportunas» sumaban IF y cualquier regla (el C10 contaba `brute_force` como detección de un escaneo) | `herramientas/analizar_3b.py` y `referencia_trafico_4c.py` (2026-11-03.1): etiquetas `senal_if` / `regla_prevista` / `regla_no_prevista`; medida publicada con «regla prevista sí/no»; aplicación y efecto **null = no medido**. PROTOCOLO-4C §7 corregido | 26 pruebas: 6 nuevas y las 20 originales contra la versión nueva. Reanálisis del 3B revisado: categorías, población y total **idénticos**; por componente, IF oportuno en 10/15, regla prevista en 10/15 (cota inferior en 24f8a80), «cualquiera» en 12/15 |
| 5 | Endpoint de fuerza bruta | **seguía** en `DETECCION-OPORTUNA.md` (`/login`) | copia corregida: `http://10.10.30.10:18081/auth` (leído en la unidad `ppi-brute-lab` de srv-dmz: `PUERTO=18081`, `RUTA=/auth`). `c05`, `escenarios-4c.json`, `trafico_observado.py` y FICHAS ya lo tenían bien | búsqueda de `1808x`, `/auth` y `/login` en todo el árbol de la campaña |
| 6 | (nuevo) El instalador de srv-dmz suponía el v1 disabled/inactive | falso desde el 03-nov | producto b2f2994: condición previa que para con el v1 activo o habilitado, con el servicio en ejecución, con la tabla v1 o sin lectura de nft | `deploy/etapa4/banco/ensayo_precondicion_v1.sh` **7/7**; suite Linux **709 passed, 1 skipped** |

Las pruebas y las 16 omisiones, una a una, están en [PRUEBAS-Y-OMISIONES.md](PRUEBAS-Y-OMISIONES.md). No se cambió
ninguna expectativa ni se desactivó ninguna prueba.

## 6. Qué falta antes de instalar la candidata

Detalle y procedimiento en [PROCEDIMIENTO-4A-RECONCILIADO.md](PROCEDIMIENTO-4A-RECONCILIADO.md) (conjunto exacto
con hashes, dependencias, respaldo, instalación, comprobaciones, sombra, diagnóstico de descartes y reversión).

**Bloqueos:**

- **B1. Fase P0 (Mark, con autorización):** respaldo del estado de la demo, `disable --now` del timer v1, retirar
  la tabla `inet cyberflow` (lo que quita el LIMIT a .21) y nuevo respaldo base.
  **Actualización 2026-11-04 01:39 UTC:** Mark ya desactivó el v1 y retiró la tabla. Comprobado: timer
  `disabled`/`inactive`, sin tablas nft, respaldo de la tabla guardado. Queda el respaldo base, que se hace al empezar
  la 4A. Detalle en [evidencia/laboratorio/p0-srvdmz-2026-11-04.md](evidencia/laboratorio/p0-srvdmz-2026-11-04.md).
- **B2. Petición escrita de la 4A.**
- **B3. `sudo -n journalctl` para m4rk** (lecturas SIGUSR1).

**Pendientes que no bloquean la 4A, pero sí la 4B o la 4C:**

- **B4.** Aceptación del canal SSH con la Kali, también en el control.
- **B5.** Copiar `scripts-4c` a la Kali.
- **B6.** Coste del vigía.
- **B7.** El panel no corresponde al feed v2: decidir si se adapta o si la evidencia sale solo de los ficheros.
- **B8.** Causa de los descartes de Suricata. Es un diagnóstico, no una excepción: **I5 sigue siendo condición
  de inicio de la 4C** (0 `kernel_drops` en los 30 min previos); ver PROCEDIMIENTO-4A-RECONCILIADO §5.2.

## 7. ¿Listo para preparar la 4A?

**Conclusión vigente (2026-11-04).** La rama, el paquete, los guiones, las herramientas y los protocolos
corregidos están verificados offline. Los pasos 2 y 3 de P0 (B1) están hechos y comprobados: el agente v1 no aplica
y su tabla está retirada. B2 está resuelta con la petición del 04-nov. Queda el paso 4 de P0 (respaldo base
completo de srv-dmz) y B3, que forman parte de la ejecución de la 4A (`../etapa4a-instalacion-2026-11-04/`).
Esta carpeta no declara el laboratorio recuperado: eso solo puede hacerlo la 4A con sus lecturas.

*Antecedentes con fecha (se conservan):*

- *2026-11-03, conclusión original:* «Listo para preparar, bloqueado para instalar». La instalación no podía
  empezar mientras el v1 aplicara (B1) y sin la petición escrita (B2). Laboratorio en el estado de ca66db5
  (motor 24f8a80, publicador y panel de ca66db5, agente v1 aplicando).
- *2026-11-04 01:38 UTC:* el agente v1 dejó de aplicar (P0, paso 2).

## 8. Estado git conservado

`evidencia/git/instantanea-git.txt` (2026-11-03 19:52 −05:00) recoge ramas, etiquetas, worktrees, cambios y stash de
los dos repositorios: ocho worktrees del producto y dos clones de la documentación. Después se añadió el worktree
`producto-recuperacion` (rama de recuperación). Los cambios locales se conservan sin sobrescribir:

- `producto-main/scripts/engine/dashboard.py` (336+/39−, sin confirmar): sigue en su worktree. Además, una copia
  del diff en el portátil, **no publicada** porque es trabajo sin confirmar de Mark:
  `respaldo-reconciliacion-2026-11-03/preservado-producto-main-dashboard.patch`, sha256 `9f938d72…3248d9f`;
- clon antiguo `orquestacion` @ 44327a8 (`ESTADO.md` y `README.md` modificados, `04-evidencias/` sin seguimiento):
  sigue en su sitio, con copia local `preservado-orquestacion-44327a8.patch`, sha256 `528dffcc…cbab2d62f7`;
- `testsprite_tests/tmp/` en as-deployed y tres carpetas sin seguimiento en `orquestacion-limpio`: no se han tocado
  ni se incluyen en este commit.

No se ejecutó `reset --hard`, `git clean`, `force-push` ni ningún borrado de respaldos o evidencias.

## 9. Contenido de esta carpeta

| Ruta | Qué es |
|---|---|
| `COMPARACION-COMPONENTES.md` | tabla por componente (antes de la demo / candidata / publicada / laboratorio / diferencia / efecto / recomendación) |
| `PROCEDIMIENTO-4A-RECONCILIADO.md` | P0, conjunto exacto con hashes, instalación, sombra, descartes, reversión, bloqueos |
| `PRUEBAS-Y-OMISIONES.md` | resultados y las 16 omisiones una a una |
| `documentos-corregidos/` | PROTOCOLO-4C, PROTOCOLO-4B y DETECCION-OPORTUNA corregidos (los originales siguen intactos) |
| `guiones/` | `g01` corregido, `k20` nuevo, copia idéntica de `r4.sh` |
| `banco-g01/` | bancos de `g01` y `k20` |
| `herramientas/` | `analizar_3b.py`, `referencia_trafico_4c.py`, sus pruebas y el nuevo `herramientas-e4.sha256` |
| `evidencia/` | lecturas del laboratorio (sin secretos) y los guiones que las hicieron, instantánea git, pruebas, reanálisis del 3B y `SHA256SUMS` del paquete |
