# Etapa 4A: pendientes del cierre complementario (P1, P3, P4, P5) e integración en sombra (2026-11-06)

> **Estado actualizado (06-nov, noche, 3): guiones de traslado del paquete `902991e` corregidos (r2) y probados en
> banco. NO se ha copiado nada al laboratorio. E-carga NO ejecutada y NO programada.**
> - **Defectos de los guiones anteriores** (`evidencia/13-correccion-s14/`, ahora **sustituidos**, conservados sin
>   cambios):
>   - `op_host` terminaba con rc 0 aunque hubiera hashes, evaluador o manifiesto distintos;
>   - el principal no exigía el éxito de los tres hosts;
>   - el `SHA256SUMS` interno podía listarse a sí mismo.
> - **r2:** [`ecarga-v2-preparacion/traslado-902991e-r2/`](ecarga-v2-preparacion/traslado-902991e-r2/).
>   - Éxito global solo con bastión, Sensor1 y srv-dmz verificados (3/3).
>   - Paquete en staging oculto y marca `VERIFICADO`. El aviso, solo tras verificar.
>   - Nada se sobrescribe ni se borra.
>   - Registro por host, y recuperación definida.
> - **Banco:** r2 33/33 (65534 y root). La versión anterior oculta el fallo en 18 casos.
> - **Documento:** [`ecarga-v2-preparacion/TRASLADO-PAQUETE-902991e-r2.md`](ecarga-v2-preparacion/TRASLADO-PAQUETE-902991e-r2.md).
>   Contiene el comando de copia, marcado **NO EJECUTADO**.
> - **Pendiente:** autorizar la copia (estado 2), P0 (estado 3) y E-carga (estado 4).
>
> **Estado actualizado (06-nov, noche, 2): S14 con tiempo desconocido corregido en banco. E-carga NO ejecutada y NO
> programada.**
> - **Defecto.** `evaluar_s14` 2026-11-06.1 (`a12deae`) no contaba el hueco inmediatamente anterior a un tramo
>   saturado. CPU 100 %/PSI 50 % en [D+100, D+108) con `psi` ausente en D+100 ≤ t < D+103 daba S14 `true`, «estable
>   con carga suficiente», `habilita_condicion_3` true y rc 0.
> - **Ahora** da S14 `null`, «no demostrable», false y rc 1. La regla S/N/U (protocolo **r4** §3.6.1.1) cubre los
>   huecos antes, dentro y después, los bordes de la ventana y de la línea base, y la base dudosa. Umbrales, 8 s, 4 s y
>   99 % sin cambios.
> - **Banco.**
>   - 12 regresiones fallan con `a12deae` y pasan ahora;
>   - 85/85 en las pruebas de E-carga;
>   - suite 1 013 (65534) y 1 057 (root) sin fallos;
>   - la prueba de la GUI en el portátil es intermitente por WinError 6/50 de Windows, sin relación con el cambio.
> - **Producto `902991e`**, rama sin fusionar en `main`: `evaluar_s14` 2026-11-06.2 y `construir_entrada` 2026-11-06.3.
> - **Documentos.** [`ecarga-v2-preparacion/PREPARACION-ECARGA-v2-r3.md`](ecarga-v2-preparacion/PREPARACION-ECARGA-v2-r3.md)
>   y evidencia en `evidencia/13-correccion-s14/`. La futura ejecución va a `evidencia/14-ecarga-ejecucion/`.
> - **Pendiente.**
>   - Copiar el paquete de `902991e` a los hosts: guiones preparados y no ejecutados. `paquete-a12deae` **no se usa**.
>   - Repetir P0.
>   - La orden de Mark, que incluye aprobar la r4.
> - **Veredictos.** Corregido en banco: **sí**. Validado en vivo: **no**.

> **Estado anterior (06-nov, noche): defectos de la preparación de E-carga v2 corregidos. E-carga NO ejecutada y NO
> programada.**
> - **Qué se corrigió.** `generadores.sh` daba rc 0 tras un start fallido. `muestreo_bastion.sh` daba la parada por
>   hecha aunque fallara. `derivar_pcap.py` aprobaba S2 y S3 con observaciones incompletas (con dos PCAP de una hora
>   habilitaba la condición (3) de punta a punta). S14 no tenía regla.
> - **Resultado en banco.** Hay 13 defectos con prueba de regresión: 26 de 26 fallan con la versión anterior y 56 de 56
>   pasan con la nueva. La suite completa no tiene fallos.
> - **Producto `a12deae`.** Rama `recuperacion/etapa4a-pendientes-20261106`, sin fusionar en `main`. Ubicación canónica
>   `deploy/etapa4/ecarga/`. Evaluador 2026-11-06.4 sin cambios.
> - **En los hosts.** El paquete `~/cf-e4/paquete-a12deae` está copiado y verificado en el bastión, Sensor1 y srv-dmz.
> - **Protocolo r3.** [`PROTOCOLO-CARGA-v2.md`](PROTOCOLO-CARGA-v2.md): S14 operacional (§3.6.1), S2/S3 precisados
>   (§3.6.2) y P0 ampliado. Se publica antes de cualquier ensayo y no es retroactivo.
> - **Documentos.** Preparación r2:
>   [`ecarga-v2-preparacion/PREPARACION-ECARGA-v2-r2.md`](ecarga-v2-preparacion/PREPARACION-ECARGA-v2-r2.md). Evidencia:
>   `evidencia/12-correccion-preparacion/`. Las copias `guiones-c7f24510/` y `evaluacion-e83f4be6/` quedan selladas y
>   sustituidas.
> - **Veredictos.**
>   - Corregido en banco: **sí**.
>   - Preparación lista: **sí, a falta de la orden de Mark**, que incluye aprobar la r3.
>   - Pendiente de medir en vivo: arranque y parada con el systemd real, coste y cobertura del muestreo S14, y retención
>     del anillo con carga.

> **Estado anterior (06-nov, tarde): ejecución de E-carga v2 preparada. NO ejecutada y NO programada.**
> - **Paquete.** El de `ae2900e` está copiado y verificado en el bastión, en Sensor1 y en srv-dmz
>   (`~/cf-e4/paquete-ae2900e`):
>   - `SHA256SUMS` `41f91787…`;
>   - evaluador `53e9f7bd…`, 2026-11-06.4.
>
>   `paquete-f6dc685` lleva el evaluador con el defecto: tiene el aviso `NO-USAR-PARA-VEREDICTO` y no se usa.
> - **Guiones y herramientas versionados en los hosts:**
>   - ejecución `c7f24510`: muestreo, guardia de §3.7, muestreadores de Sensor1, generadores;
>   - evaluación `e83f4be6`: análisis posterior, derivación de los S y construcción de la entrada con trazabilidad.
> - **Comprobaciones sin carga, todas OK:**
>   - relojes;
>   - los tres verificadores con rc 0;
>   - herramientas, permisos y espacio;
>   - `obs_pcap --en-seco`;
>   - arranque y parada de los muestreadores;
>   - vía de parada de los generadores;
>   - prueba de humo de la cadena de evaluación;
>   - lecturas de S7 y S11;
>   - 14/14 y 17/17 pruebas en el banco.
>
>   Se repiten en P0.
> - **Documentos.** La construcción de la entrada por K/S, la secuencia del día, las paradas y la tabla de estado están
>   en [`ecarga-v2-preparacion/PREPARACION-ECARGA-v2.md`](ecarga-v2-preparacion/PREPARACION-ECARGA-v2.md). La
>   evidencia está en `evidencia/11-preparacion-ecarga/`.
> - **Pendiente.** Mark tiene que decidir sobre S14: «saturación nueva» no tiene umbral publicado. La otra opción es
>   aceptar S14 en `null`, con lo que el resultado sería como mucho «no demostrable».
>
>   Después hace falta la orden explícita de ejecutar en la franja publicada, que sigue sin programar.
>
> **Estado anterior (06-nov): evaluador de E-carga corregido (2026-11-06.4, producto `ae2900e`). E-carga sigue sin
> ejecutarse y sin programarse.**
> - **Defecto.** En `f6dc685`, `veredicto` daba «estable con carga suficiente» (rc 0, condición (3) habilitada) en tres
>   casos:
>   - K1 y S1 con el texto `"false"`;
>   - clase `no_evaluable` con S verdaderos;
>   - C1 a 100/M con S13 verdadero.
>
>   Está reproducido: 3 de 3 casos habilitan con f6dc685 y 0 de 3 con la corrección
>   (`evidencia/10-veredicto-contrato/`).
> - **Corrección.** Contrato de entrada estricto, y contraste de S12, S13 y la clase con las métricas de Suricata;
>   una contradicción da «no demostrable» y no se corrige ningún dato. C3 y `no_evaluable` no pueden dar «estable»
>   ([`PROTOCOLO-CARGA-v2.md`](PROTOCOLO-CARGA-v2.md) §0.1 y §4.5, revisión r2).
>   - No cambia ningún K, S ni umbral; 14,95/M exacto sigue sin cumplir.
>   - Se corrige la afirmación sobre K4b: la regla auxiliar no quedó validada como criterio decisorio, y la simulación
>     no demuestra que ninguna regla posible funcione.
> - **Pruebas.** Regresión en `ae2900e`:
>   - como root, **966 passed / 9 skipped / 0 failed**;
>   - sin root, **922 passed / 53 skipped / 0 failed**.
>
>   Las omisiones son las de antes: requieren root, `node` o el repo de documentación. Contra el evaluador de
>   `f6dc685` fallan 96 de las 129 pruebas de E-carga.
> - **Pendiente antes de P0** *(hecho después: ver el estado de arriba)*. Copiar el paquete de `ae2900e` a Sensor1
>   (protocolo §3.5, punto 9). El `paquete-f6dc685` lleva el evaluador con el defecto.
>
> **Estado anterior (06-nov, 07:30Z): E-carga v2 publicado, no ejecutado.**
> - [`PROTOCOLO-CARGA-v2.md`](PROTOCOLO-CARGA-v2.md) sustituye a la v1, que se conserva sin cambios. Su §0 enumera qué
>   cambió y por qué:
>   - las clases son las del clasificador (C1 para descartes medidos);
>   - estabilidad técnica, clase de captura, I5 y población principal se dan por separado;
>   - K4a es criterio y K4b es informativo;
>   - el alcance de las etapas queda unificado;
>   - se registran las señales de tráfico legítimo;
>   - los tiempos van en epoch;
>   - `obs_pcap.py` comprueba el fin.
> - La prueba intermitente `test_patron_antiguo_falla` ahora es **determinista**: 200 de 200 pasadas.
> - Regresión en `f6dc685`: **872 passed / 9 skipped / 0 failed** como root; **828 passed / 53 skipped / 0 failed** sin
>   root.
> - El criterio de avance no cambia: sigue faltando E-carga (§0).
>
> **Estado anterior (06-nov, 06:29Z): verificadores corregidos.**
> - `verificar_bastion.sh`, `verificar_sensor1.sh` y `verificar_srvdmz.sh` dan **rc 0** con los guiones corregidos
>   (producto `a1cea5e`, ejecución de solo lectura, §8b).
> - Los 3 FALLO antiguos eran defectos de los guiones. Se conservan tal cual en `evidencia/06-observacion/verif-post.txt`.
> - La corrección **no** relaja nada:
>   - v1 debe estar inactivo, no habilitado y sin procesos;
>   - el `motor_startup` debe ser el del proceso vigente;
>   - cualquier error de lectura es FALLO.
>
> **Sigue sin demostrarse la estabilidad con carga suficiente.**
> - O12 es «carga insuficiente» y lo sigue siendo.
> - En esa hora **no funcionaba ningún generador legítimo**:
>   - 0 flujos de 10.10.20.21–26;
>   - 0 ráfagas;
>   - 0 flujos grandes;
>   - pps máximo 391, frente a 2 426 en el ensayo del 04-nov.
> - Se propone el ensayo **E-carga** dentro de la 4A ([`PROTOCOLO-CARGA.md`](PROTOCOLO-CARGA.md)). Está publicado y
>   **no ejecutado**.
>
> **¿Se puede iniciar el control formal de la 4B? Todavía no.**
> - Queda una sola condición técnica: E-carga con resultado «estable con carga suficiente» (§0).
> - La 4B se puede seguir preparando.
> - La 4C y la campaña B **no** están autorizadas.
>
> **El veredicto original de este informe sigue debajo, sin cambios, como registro.** Las partes que esta
> actualización corrige están anotadas en §0, §4, §8 y §9.
>
> ---
>
> **Veredicto original (06-nov, 05:56Z).**
> - P1, P4 y P5 están **resueltos y verificados**.
> - P3 está **explicado, con incertidumbre declarada**.
> - El instalador quedó **corregido y probado con fallos deliberados**.
> - La integración en sombra (relé `--entrega paquete`, agente `--paquete`) funcionó toda la ventana fija de 60 min:
>   **O1–O11 cumplen**.
>
> Hay tres resultados desfavorables, que se publican tal cual:
> 1. **O12, carga insuficiente:** 587 592 paquetes frente al umbral de 596 789. La observación **no permite concluir nada
>    sobre descartes bajo carga**. Sí demuestra la medida (C0, `cero_explicito`) con la carga que hubo.
> 2. **Criterio §3 «`verificar_*.sh` sin FALLO» no cumplido tal como está escrito:** 3 FALLO en los guiones de la 4A.
>    - Dos esperan **activo** el v1 que el cierre retiró a propósito.
>    - El otro busca `motor_startup` solo en el registro actual, y la rotación diaria lo dejó en `.1`.
>    - Cada condición real se comprobó por otra vía (§8), pero el criterio no se flexibiliza.
> 3. **Un error mío en la observación:** el verificador de PCAP tenía mal calculada la hora de fin (06:11:30Z). Siguió
>    leyendo, solo lectura, después de la ventana, y lo detuve a las 05:56:25Z. No afecta a ningún dato de la ventana.
>
> **¿Está listo para iniciar el control formal de la 4B? Todavía no, por un único motivo:** el §3 sin FALLO.
> - Para cerrarlo basta corregir los dos guiones de verificación, probarlos en banco y volver a ejecutarlos (solo
>   lectura, sin reinstalar nada).
> - P1 está cerrado y la integración verificada por O1–O11.
> - La 4C y la campaña B **no** están autorizadas: I5 se seguirá exigiendo en los 30 min previos a la 4C, y la carga de
>   esta hora no sirve para eso.
>
> *(Corregido el 06-nov, 06:29Z, en §0: el §3 ya está cerrado, pero el motivo no era único. La integración no se había
> observado nunca con los perfiles legítimos activos.)*

Petición: la de Mark del 06-nov («cierra los pendientes del cierre complementario antes de la 4B»), en siete partes, y
su corrección posterior sobre la seguridad del instalador (códigos de salida, `systemd-analyze verify`, respaldo
separado de la evidencia, reversión probada con fallos deliberados). Base: [`../etapa4a-cierre-complementario-2026-11-04/`](../etapa4a-cierre-complementario-2026-11-04/README.md).
Criterios fijados **antes** de instalar y de observar: [`CRITERIOS-FIJADOS.md`](CRITERIOS-FIJADOS.md) (commit `997c8e2`).
Mark ejecutó el único paso con sudo con contraseña (bastión); nunca se pidió ni se registró la contraseña.

No se inició la 4B, la 4C ni la campaña B. No hubo ataques, generadores ni restricciones. No se cambiaron las 28
features, el modelo, los umbrales α, las reglas ni la política `if_senal`; no se reentrenó; no se tocó el Word.

Segunda petición de Mark (06-nov): continuar el cierre de la 4A sin iniciar la 4B, la 4C ni la campaña B, en seis
partes:
1. referencias;
2. verificadores corregidos;
3. pruebas que detecten fallos reales;
4. protocolo de carga;
5. conclusiones ajustadas a la evidencia;
6. publicación.

Respuesta: §0, §8b, [`PROTOCOLO-CARGA.md`](PROTOCOLO-CARGA.md) y `evidencia/07-verificadores/` y `08-carga/`.

Tampoco esta vez se reinstaló ni se reinició ningún servicio. No se arrancó ningún generador y no se cambió ninguna
configuración de captura ni de Suricata.

## 0. Conclusiones separadas y criterio único de avance (06-nov, 06:29Z)

**Referencias confirmadas** (fetch del 06-nov, 06:0xZ; `git log` de ambos repositorios):
- **Producto:** <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos>,
  rama `recuperacion/etapa4a-pendientes-20261106`.
  - No había ningún commit posterior a `b18c286`. El único posterior es el de esta corrección, **`a1cea5e`**: solo
    toca los dos verificadores, un módulo nuevo de solo lectura y sus pruebas.
  - Detector instalado: `ec78ca5`. Es ancestro de `b18c286` y de `a1cea5e`.
- **Panel:** `93f076e`, en `panel/cadena-v2-20261104`. **No** es ancestro de esta rama.
- **Demostración:** `as-deployed-sensor` `ca66db5`, etiqueta `demo-politica-AC-2026-11-03`. Va aparte y no se mezcla:
  nada de esta rama procede de ella ni se instala sobre ella.
- **Documentación:** <https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION>, `main` en `da4c3a0`, sin commits
  posteriores. El commit que publica esta actualización figura en el historial de `main`.

**Conclusiones, cada una con su propio alcance:**

| Conclusión | ¿Demostrada? | Alcance exacto y evidencia |
|---|---|---|
| **C0: calidad de la fuente en el periodo medido** | **Sí, solo en esa ventana** | 04:50–05:50Z del 06-nov: anillo C0, vía rápida C0 y Suricata `cero_explicito`, con 587 592 paquetes (§8, O5). Con esa carga, sin ráfagas ni flujos grandes. No se extiende a otras horas ni a otra carga |
| **Estabilidad de la integración** | **Sí, sin carga controlada** | O1–O11 en la misma ventana: servicios continuos, 180 entregas = 180 aceptadas en orden, 0 `firma_invalida`/`paquete_invalido`, rulesets iguales y hashes iguales. Los verificadores corregidos dan rc 0 (§8b) |
| **Estabilidad con carga suficiente** | **No demostrada** | O12 «carga insuficiente». No había generadores legítimos y la intensidad fue mucho menor que en la referencia (`PROTOCOLO-CARGA.md` §1). Pendiente de E-carga |
| **Detección oportuna** | **No evaluada** | Sin ataques. Esta etapa no la mide |
| **Aplicación de una restricción** | **No evaluada** | En sombra: 0 eventos `aplicacion`, sin `--aplicar`/`--enforce`. Los feeds tenían `entradas: []` |
| **Efecto real sobre el ataque y sobre el tráfico legítimo** | **No evaluado** | Requiere respuesta aplicada, que solo existe en la **campaña B** (posterior a la 4C y no autorizada). La 4C es la campaña A **en sombra**, sin aplicar restricciones. *(Corregido el 06-nov a las 07:30Z: antes decía «4C/campaña B».)* |

**Lo que prueban las 180 entregas aceptadas.**
- Prueban el **transporte del feed firmado** (paquete `feed.par`, firma ed25519, secuencia e idempotencia) desde
  Sensor1 hasta srv-dmz durante esa ventana.
- **No** prueban eficacia frente a ataques ni la aplicación de restricciones: el sistema estaba en sombra y los feeds
  no llevaban medidas.

**`rx_dropped` (P3).**
- Las tramas 802.3/LLC dentro de VLAN examinadas aparecen en los PCAP.
- Los contadores de descarte del driver y de softnet no subieron.
- La tasa de esas tramas coincide con la de `rx_dropped`.
- **No se comprobó cada incremento del contador por separado.** Por tanto no se afirma la ausencia universal de
  pérdida, solo que no hay evidencia de pérdida en lo examinado (§4).

**C3 histórico.** La ventana del ensayo del 04-nov **sigue siendo C3**. La medida retrospectiva con la herramienta
nueva (§3) no la reclasifica.

**I5.** Las lecturas «cumple» del 06-nov son **informativas** y **no autorizan** la 4C, ni ahora ni más adelante. I5 se
vuelve a comprobar, con una lectura propia, en los 30 min previos al inicio real de la 4C.

**Criterio único de avance** (sustituye a la respuesta «por un único motivo» del veredicto original; vale para todo
este informe):

| Paso | Condiciones, todas necesarias | Estado |
|---|---|---|
| **Control formal de la 4B** | (1) `verificar_*.sh` sin FALLO, con los guiones corregidos | **Cumple** (`a1cea5e`, rc 0 en los tres, §8b) |
| | (2) O1–O11 de la integración en sombra | **Cumple** (§8) |
| | (3) E-carga con resultado «estable con carga suficiente» ([`PROTOCOLO-CARGA-v2.md`](PROTOCOLO-CARGA-v2.md) §4.1; desde las 07:30Z la versión vigente es la v2, y la v1 queda como registro) | **Pendiente**: publicado, no ejecutado. Necesita una orden de Mark |
| **4C: campaña A en sombra, sin aplicar restricciones** | Lo anterior, el resultado de la 4B y **I5** en los 30 min previos al inicio real de la 4C. La población principal sigue siendo **C0** | **No autorizada** |
| **Campaña B** (posterior): respuesta aplicada y medición de su efecto | La 4C cerrada, y sus propias condiciones, que se fijarán antes | **No autorizada** |

**Lo que E-carga habilita y lo que no.**
- «Estable con carga suficiente» cumple la condición (3) y nada más.
- La **clase de captura** de E-carga se publica aparte. Un C1 conserva su limitación: no es captura sin pérdidas.
- S13 (< 14,95 descartes por millón) es un límite técnico. **No** demuestra C0 ni satisface I5.
- I5 solo se evalúa antes de la 4C (`PROTOCOLO-CARGA-v2.md` §4).

Mientras falte (3), la 4B **puede prepararse, pero no iniciarse**.

## 1. Versiones y hashes

| Qué | Valor |
|---|---|
| Código congelado de la 4A (Sensor1) | `ec78ca5`, `SHA256SUMS` OK antes y después |
| Modelo / manifiesto / esquema de features | `df547da0…` / `b3ad6805…` / `e032a1a2…` (iguales antes y después, §8 O11) |
| `suricata.yaml` | `0962ce68…` (`ring-size: 16384`, sin cambios) |
| Rama de pendientes (producto) | `recuperacion/etapa4a-pendientes-20261106`: `313f8f8` (P1, P4, P5) → **`b18c286`** (instaladores endurecidos) sobre `ce353ef` |
| Instalador | `p4-instalador 2026-11-06.2` (`p4_comun.sh` `d0073ec9…`, `bastion_p4.sh` `c26e21b6…`, `srvdmz_p4.sh` `e4a5fc11…`) |
| Paquete instalado | `~/cf-e4/paquete-b18c286` en bastión, srv-dmz y Sensor1: tgz `520b7bc5…`, `SHA256SUMS` interno `e0e72e23…`, verificado en los tres |
| Herramientas de medida en Sensor1 (sin sudo) | `~/cyberflow-e4/herramientas-20261106`: `salud_captura.py` `274b4d61…` (VERSION `2026-11-06.1`), `clasificar_periodo.py` `65af5e53…`, `vigia_4c.py` `2fe00200…`, `evidencia.sh` `ead0eab0…` (del paquete `313f8f8`; `b18c286` no las cambia) |
| Bastión instalado | `relay_eventos.py` `d21a3da2…`, `feed.py` `c41be50e…`, `pub.pem` `7ce39571…`, unidad `e7f89e15…` (`--entrega paquete`) |
| srv-dmz instalado | `agente_enforce_v2.py` `7884a6ba…`, `feed.py` `c41be50e…`, `pub.pem` `7ce39571…`, `cf-feed-ssh.sh` `c5701056…`, `cf-nft-helper` `3ba6374f…` (sin cambios), unidad `80e9aa62…` (`--paquete`) |
| Verificadores corregidos (06-nov, 06:29Z) | **`a1cea5e`** sobre `b18c286`. Cambia solo `verificar_bastion.sh`, `verificar_sensor1.sh`, el nuevo `comun/verif_estado.py` (VERSION `2026-11-06.1`) y `tests/test_etapa4_verificadores.py`. Paquete `~/cf-e4/paquete-a1cea5e` en los tres hosts: tgz `103d39ff…`, `SHA256SUMS` interno `d08a7d1f…`, verificado. **Se copió; no se instaló ni se reinició nada** |

## 2. Matriz: pendiente → corrección → prueba → resultado → evidencia

| # | Pendiente (cierre 4A §11) | Corrección | Prueba | Resultado | Evidencia |
|---|---|---|---|---|---|
| **P1** | I5/C0 no demostrables: Suricata 7 omite los ceros en `stats.log` | `salud_captura` 2026-11-06.1 mide Suricata con los eventos `stats` de EVE (cero explícito / descartes / ausente / desactualizada / error / cobertura insuficiente; reinicio por identidad `t − uptime`; rotación .1/.gz; huecos). Integrada en `clasificar_periodo` (`--suricata-eve`), `vigia_4c` e I5 | 34 casos en banco (`test_etapa4_salud_eve.py`), 2 551 muestras reales del 04-nov; observación fija (§8) | **Resuelto**: la herramienta da estados medidos y no convierte una ausencia en cero. En vivo: ventana de observación **C0** (`cero_explicito`, 587 592 paquetes, 452 muestras, sin reinicio); I5 informativo **cumple** | §3, `evidencia/04-p1-medida/`, `evidencia/06-observacion/` |
| P3 | `rx_dropped` ≈ 14/s sin causa demostrada | Ninguna (diagnóstico, solo lectura) | Contadores separados del driver, del núcleo y de softnet; recuento de tramas en los PCAP | **Explicado con incertidumbre declarada**: contador del núcleo, no del driver; compatible con tramas 802.3/LLC dentro de VLAN sin manejador, que aparecen en los PCAP examinados; no se comprobó cada incremento (§0, §4) | §4, `evidencia/01-rx_dropped/` |
| **P4** | `firma_invalida` transitorio en el agente v2 | Entrega en un solo fichero `feed.par` (feed + firma + sha256), publicado con **un** `rename`; el agente lo lee con `--paquete`. Firma, secuencia e idempotencia sin cambios | Reproducción determinista en banco; cadena completa; interrupciones; concurrencia; laboratorio | **Resuelto en banco y en la observación**: 180 entregas en modo paquete, 180 aceptadas en orden, 0 `firma_invalida`, 0 `paquete_invalido` | §5, `evidencia/02-firma_invalida/`, `evidencia/03-banco/` |
| P5 | `SHA256SUMS` de `salida.txt` calculado antes de la última línea | `evidencia.sh`: `ev_sellar` cierra el `tee`, espera, comprueba 1 s sin cambios y solo entonces sella y verifica | 3 casos en banco (incluido un escritor que sigue escribiendo: «PARADA», no sella) | **Resuelto**: todas las carpetas de evidencia de hoy verifican | §6 |
| Instalador | (revisión de Mark de `313f8f8`) rc no comprobados, `verify` decidido por texto, evidencia dentro del respaldo | `p4_comun.sh`: cada paso con rc real; respaldo inmutable separado; reversión automática verificada (rc 20) o parada manual (rc 30) | 33 casos con errores deliberados en cada paso crítico | **Resuelto**: ningún falso OK; respaldo verificable; recuperación correcta; sombra conservada | §7, `evidencia/03-banco/regresion-instaladores.txt` |
| Verificadores (§3) | 3 FALLO falsos en `verif-post.txt` | `verif_estado.py`: v1 retirado (unidades y procesos) y arranque del proceso vigente; los errores se propagan (`a1cea5e`) | 52 casos (50 como root y 2 de permisos sin root); regresión de los 3 FALLO con los valores reales | **Resuelto**: rc 0 en bastión, Sensor1 y srv-dmz, solo lectura | §8b, `evidencia/07-verificadores/` |

Regresión completa del producto en banco Linux (Docker, sin red, repo de solo lectura): **786 passed, 7 skipped** en
`b18c286` (los 7 omitidos son los de siempre: compuerta sin el repo de docs montado y la prueba JS sin `node`).

En `a1cea5e`: **835 passed, 9 skipped, 1 failed** (`evidencia/07-verificadores/regresion-a1cea5e.txt`).
- **Omitidos:** los 7 de siempre y 2 casos de permisos que como root no aplican. Esos 2 pasan sin root
  (`banco-verificadores-noroot.txt`: 52/52).
- **El fallo** es `test_etapa4_evidencia_sellado.py::test_patron_antiguo_falla`. Esa prueba reproduce el defecto
  **antiguo** de sellado provocando una carrera entre `tee` y `find`, así que su resultado depende del orden de
  ejecución: falló 1 de cada 10 repeticiones, sin cambiar el código.
- **No guarda relación con esta corrección:** `a1cea5e` no toca ni `evidencia.sh` ni esa prueba (`git diff --stat
  b18c286 a1cea5e`: 4 ficheros, los de §1).
- Se declara aquí y no se oculta. Convertirla en determinista queda pendiente (§12).

## 3. P1: medida de Suricata por EVE `stats`

**Qué cambia.** `stats.log` de Suricata 7 no escribe los contadores que valen 0, así que «no aparece `kernel_drops`»
podía ser cero o falta de dato. Los eventos `stats` de EVE (cada 8 s) llevan `capture.kernel_packets`,
`capture.kernel_drops` y `uptime` **explícitos**. La versión nueva mide sobre ellos con los criterios de
`CRITERIOS-FIJADOS.md` §1: una ausencia nunca se convierte en cero; un reinicio se detecta por la identidad del proceso
(`t − uptime` estable ±3 s); hueco > 20 s o borde sin muestra a ≤ 10 s = `cobertura_insuficiente`.

**Medida retrospectiva del ensayo del 04-nov (rotulada como tal; NO reclasifica).** Sobre la ventana 06:26:55–07:26:55
la herramienta nueva da `cero_explicito` con **1 201 704** paquetes. **La clase oficial de esa ventana sigue siendo C3**
(se clasificó con las herramientas congeladas; criterio publicado: no se reclasifica).

**Por qué 1 201 704 y no 1 193 578.** Las dos cifras salen de las mismas muestras EVE; cambia qué muestras acotan los
extremos (`evidencia/04-p1-medida/bordes.py` → `bordes.txt`):

| Medida | Muestra inicial | Muestra final | Cobertura | Paquetes |
|---|---|---|---|---|
| Comparador del cierre 4A (`comparar_suricata.py`): primera y última muestra **dentro** de la ventana | 06:26:55,135 (`kernel_packets` 180 418) | 07:26:47,545 (1 373 996) | 3 592,4 s (450 muestras) | **1 193 578** |
| `salud_captura` 2026-11-06.1: muestras que **acotan** la ventana desde fuera (≤ desde, ≥ hasta, a ≤ 10 s) | 06:26:47,134 (174 661), 7,87 s antes | 07:26:55,546 (1 376 365), 0,55 s después | 3 608,41 s | **1 201 704** |

Diferencia: **8 126 paquetes = 5 757** (06:26:47,134 → 06:26:55,135) **+ 2 369** (07:26:47,545 → 07:26:55,546).
El comparador deja fuera ≈ 7,6 s de la ventana; la herramienta nueva la cubre entera a costa de incluir ≈ 8,4 s de
fuera. Ninguna de las dos tiene descartes (0 y 0). Para cubrir el periodo completo, la cota conservadora es la de la
herramienta nueva; por eso es la que se usa para I5. El umbral O12 (596 789 = 50 % de 1 193 578) se fijó con la cifra
del comparador antes de la observación y no se cambia.

**Lo que la herramienta ve en los datos reales del 04-nov** (2 551 muestras, 02:00–07:40, banco): descartes en tres
tramos (198 a las 02:08:27; 7 a las 03:05:47; 13 a las 03:53:56) y el reinicio de Suricata de las 06:16:5x detectado
por identidad de proceso (el incremento que lo cruza no se usa).

**I5.** Sin cambios de criterio: 0 `kernel_drops` en los 30 min previos al inicio de la 4C, terminando en la última
muestra (≤ 20 s de antigüedad). Lecturas informativas (no inician nada):
- 06-nov, antes de instalar: `cumple`, con 403 528 paquetes en 30 min.
- 06-nov 05:54Z, después de la observación: `cumple`, `cero_explicito`, con 304 391 paquetes y 226 muestras entre
  05:24:07 y 05:54:07Z (`evidencia/06-observacion/verif-post.txt`).

Estas lecturas solo comprueban que la medida funciona en vivo. **No son una autorización, y menos una permanente.**
I5 se evalúa de nuevo, con una lectura propia, en los 30 min previos al inicio real de la 4C, no antes. Además, la
carga de esas lecturas fue la de una red sin generadores legítimos (§0).

## 4. P3: `rx_dropped` de la NIC de captura (ens37), solo lectura

Cada contador por separado (`evidencia/01-rx_dropped/nic.txt`, dos lecturas a 60 s):

| Contador | Incremento en 60,1 s | Qué es |
|---|---|---|
| `rx_dropped` (sysfs / `ip -s`) | +842 (14,02/s) | Suma del núcleo |
| `drv dropped rx total` (vmxnet3, 4 colas) | **+0** | Descartes del driver |
| `rx_missed_errors` / `rx_fifo_errors` / `rx_over_errors` | +0 / +0 / +0 | Hardware |
| `rx_nohandler` | +0 | |
| `pkts rx OOB` (cola 0) | +0 (5 094 fijo) | El driver 6.8 no lo suma a `rx_dropped` |
| softnet `dropped` (4 CPU) | +0 | Backlog del núcleo |
| `otherhost` | +8 547 (142/s) | Tramas para otros MAC (puerto espejo); **se cuenta aparte**, no es descarte |

**Explicación.** En el núcleo 6.8, `__netif_receive_skb_core` entrega la trama a los *taps* AF_PACKET (Suricata,
tcpdump) **antes** de buscar manejador; una trama con etiqueta VLAN para la que el host no tiene interfaz VLAN y cuyo
protocolo interno no tiene manejador termina en `dev_core_stats_rx_dropped_inc` (`SKB_DROP_REASON_UNHANDLED_PROTO`).
Recuento en los PCAP del anillo (`nic_pcap.txt`, 60 s): tramas 802.3/LLC dentro de VLAN ≈ 1,03/s en cada una de 14
VLAN = **14,50/s**, frente a `rx_dropped` **14,03/s** en el mismo intervalo. **Esas tramas están en los PCAP**: no se
pierde tráfico capturado.

> **Precisión (06-nov, 06:29Z).** La frase anterior dice más de lo que se comprobó.
> - Las tramas de ese tipo **examinadas** aparecen en los PCAP.
> - Los contadores de descarte del driver y de softnet no subieron.
> - Las tasas coinciden.
> - Pero **no se comprobó cada incremento de `rx_dropped` por separado**.
>
> Lo demostrado es esto: no hay evidencia de pérdida de captura en lo examinado. No se afirma la ausencia universal de
> pérdida.

**Incertidumbre declarada.** (1) La lectura del código es sobre el núcleo 6.8 de upstream, no sobre las fuentes de
Ubuntu `6.8.0-53-generic`. (2) La coincidencia 14,50/s ↔ 14,03/s es una correspondencia de tasas en un intervalo, no
una traza trama a trama (no se usó `dropwatch`/`perf`, que requieren privilegios y cambiarían el host). (3) Por eso el
texto del cierre 4A «tramas sin manejador» se corrige: no estaba demostrado entonces y `rx_nohandler` es 0 (§10).
Offloads: `rx-vlan-offload on`, GRO/LRO off.

## 5. P4: `firma_invalida` transitorio

**Causa (reproducida).** El relé entregaba en dos `mv` sucesivos (firma, luego feed). Si el agente leía entre los dos,
veía una firma nueva con un feed viejo → `firma_invalida`; medio segundo después leía la pareja completa y la aceptaba.

**Las 14 incidencias del laboratorio** (`evidencia/02-firma_invalida/`, correlación de las trazas del relé y del
agente; relojes por NTP): todas ocurrieron **dentro** de una entrega del relé en modo **pareja**, entre 1 y 10 ms antes
de `entregado_en`, y la **misma secuencia** se aceptó 0,509–0,513 s después. Las 13 iniciales (04-nov 06:26 → 06-nov
02:14 UTC) son las del informe; la **14.ª** (seq 4380, 06-nov 04:00:55Z) apareció después del diagnóstico, con el
relé aún en pareja (antes del cambio de las 04:39). **Ninguna ocurrió en modo paquete.** La lista completa, con
secuencia, entrega y aceptación posterior, está en `evidencia/06-observacion/obs-post-p4.txt`.

La traza del agente tiene otros dos motivos, ambos fuera de la ventana y propios del diseño:
- **`feed_caducado`** (seq 3654, 06-nov 00:00:29Z): tras el arranque, el agente leyó el feed del 04-nov que había
  quedado en disco y lo rechazó por caducado.
- **`misma_secuencia`** (seq 4351, 03:51:29Z): es una recepción `repetido`, no un rechazo. El agente releyó la misma
  secuencia al reiniciarse en la fase A, lo que muestra que la idempotencia funciona.

**Corrección.** Paquete `feed.par` (`cyberflow-feed-paquete/1`: feed y firma en base64 + sha256 de cada uno),
escrito en `.feed.par.tmp` y publicado con **un** `rename` (SSH forzado `cf-feed-ssh.sh` o `os.replace` local). El
agente `--paquete` abre el fichero una vez; un paquete dañado es `paquete_invalido` (distinto de `firma_invalida`). La
verificación ed25519, la protección de secuencia y la idempotencia no cambian.

**Banco.** Cadena completa (publicador → relé → agente `--seguir`), 400 generaciones por corrida con 3 ms entre los dos
`mv` (`p4-cadena*.txt`): pareja 3, 0 y 5 rechazos `firma_invalida` (recuperación 0,51 s); paquete **0** en todas. Retraso
publicación → aceptación p50 ≈ 0,07 s en ambos modos.

**Hueco de secuencias 3654 → 3713 (no es de P4).** La traza del relé salta del 04-nov 22:31:53Z (seq 3654) al 06-nov
00:18:21Z (seq 3713); esa primera línea empieza con 219 bytes NUL (escritura cortada por una parada no limpia del
host; el bastión arrancó el 06-nov 00:00:08Z). En ese intervalo el relé no entregó nada; el agente aceptó la secuencia
siguiente, como está previsto (`hueco_seq.txt`).

## 6. P5: manifiestos sobre ficheros finalizados

`deploy/etapa4/comun/evidencia.sh`: `ev_abrir` redirige la salida a `tee`; `ev_sellar` devuelve la salida al
terminal, **cierra** la tubería, **espera** a `tee`, comprueba que nada cambia durante 1 s y solo entonces escribe
`SHA256SUMS` y lo verifica; si algo sigue cambiando dice «PARADA» y no sella. Lo usan los instaladores y la
herramienta de Sensor1. Todas las carpetas de evidencia de hoy verifican (bastión, srv-dmz fase A/C, Sensor1).

El `MANIFIESTO.sha256` de esta carpeta se calcula sobre los bytes **publicados** (`git archive` del commit) y se
verifica contra esa copia (§12).

## 7. Instalador `p4-instalador 2026-11-06.2` (corrección pedida tras revisar `313f8f8`)

| Requisito de Mark | Cómo queda |
|---|---|
| Código de salida de cada operación crítica | Todas pasan por `paso`: copia del respaldo, `install`, `daemon-reload`, `systemd-analyze verify`, reinicio, `is-active`, cmdline, entrega/recepción, hashes, sombra. Tras un fallo **nunca** se escribe «RESULTADO: OK» |
| `systemd-analyze verify` | Se decide por su **rc**; el texto solo se registra. Se verifica la unidad nueva **antes** de instalarla y la instalada después. En el laboratorio, rc 0 en bastión y srv-dmz |
| Respaldo inmutable separado | `~/respaldos-etapa4/<host>-p4-…/`: ficheros, `modos.txt`, `instalados-antes.sha256`, `SHA256SUMS`; solo lectura y **verificado en modo estricto** (mismo conjunto de ficheros que el manifiesto) **antes** del primer cambio. La evidencia va a `~/evidencia-etapa4/…`, fuera |
| Fallos antes / después de cambiar | rc **10** «PARADA SIN CAMBIOS»; rc **20** «REVERTIDO AUTOMÁTICAMENTE» (ficheros con su modo y dueño, `daemon-reload`, reinicio, activo, hashes = respaldo, sin `--aplicar`, ruleset igual), y **no** se sigue a la fase siguiente ni a la observación; rc **30** «REVERSIÓN AUTOMÁTICA FALLIDA — INTERVENCIÓN MANUAL», con lo que falta |
| Automática ≠ manual | Automática solo desde `p4_fallo`. Manual: `bastion_p4.sh revertir R` (Mark), `srvdmz_p4.sh revertir R`, y `srvdmz_p4.sh revertir-heredado R0` para el respaldo de la versión .1 (que contiene su evidencia de fase A: se verifican los ficheros listados y se informa lo no listado). Si la fase C de srv-dmz se revierte sola, el relé sigue en paquete: el instalador lo dice y pide revertir el bastión a mano |

**Pruebas con errores deliberados** (`tests/test_etapa4_p4_instaladores.py`, 33 casos, los guiones reales con órdenes
falsas `sudo`/`systemctl`/`systemd-analyze`/`nft`/`ssh` que fallan donde se les pide):
- Bastión, antes del cambio (rc 10): paquete corrupto, `cp` del respaldo, ssh a srv-dmz, `verify` de la unidad nueva
  con rc≠0 y **sin texto**, relé inactivo.
- Bastión, después (rc 20): `install` de los `.py`, `install` de la unidad, `daemon-reload`, `verify` de la instalada
  (solo rc), reinicio, `is-active` tras reiniciar, sin entrega en modo paquete.
- srv-dmz fase C, antes (rc 10): sin fase A, `feed.par` ausente o viejo, `cp`, `nft` ilegible, `verify` nueva.
- srv-dmz fase C, después (rc 20): `install`, `daemon-reload`, `verify` instalada, reinicio, `is-active`, sin recepción.
- Reversión que también falla (rc 30) en ambos; **ruleset alterado** tras reiniciar → rc 30 (restaurar ficheros no lo
  deshace; nunca se da por revertido); respaldo manipulado → la reversión manual se niega (rc 30) sin tocar nada.
- `verify` que imprime avisos con rc 0 → OK (no se decide por texto).
- Éxito y reversión manual en ambos; `revertir-heredado` con el formato de la versión .1.
- En cada caso: rc esperado; «RESULTADO: OK» si y solo si rc 0; respaldo estricto y sin evidencia; tras rc 10/20
  hashes, modos y servicio como antes; sin `--aplicar`; `nft` solo con `list ruleset`; evidencia sellada y fuera.

Dos defectos que encontraron estas pruebas y se corrigieron antes de publicar: la fase C solo comprobaba **después**
de cambiar que el código de la fase A estuviera instalado (ahora es precondición, rc 10), y la reversión de srv-dmz
contaba como fallo la falta de recepción cuando el relé seguía en paquete (ahora es un aviso explícito).

## 8. Integración en sombra y observación fija

**Instalación** (`evidencia/05-instalacion/`):

| Hora (UTC) | Paso | Quién | rc | Respaldo / evidencia |
|---|---|---|---|---|
| 03:51 | srv-dmz fase A (versión .1: `cf-feed-ssh.sh` admite pareja **y** paquete; código nuevo; unidad sin cambios) | Claude | OK | `/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-20261106T035127Z` (13 ficheros sellados; contiene la evidencia de la fase A: defecto de la .1) |
| 04:38:48–04:39:07 | Bastión `bastion_p4.sh instalar` (.2): relé `--entrega paquete` | **Mark** (sudo con contraseña) | **0** | `/home/gadmin/respaldos-etapa4/bastion-p4-20261106T043848Z` (estricto, solo lectura) · `/home/gadmin/evidencia-etapa4/bastion-p4-20261106T043848Z` |
| 04:39:44–04:39:49 | srv-dmz `srvdmz_p4.sh fase-c` (.2): agente `--paquete` | Claude | **0** | `/home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z` · `/home/adminsrvdmz/evidencia-etapa4/srvdmz-p4-fase-c-20261106T043944Z` |

Verificado después: respaldo y evidencia del bastión verifican; relé PID 70246, `NRestarts` 0, entregas
`"entrega": "paquete"`; agente con `--paquete`, sin `--aplicar`; ruleset de srv-dmz vacío (`e3b0c442…`); v1 inactivos.

**Observación.** Último reinicio de la instalación 04:39:49Z → ventana fija **04:50:00Z–05:50:00Z** (epoch
1793940600–1793944200), fijada a las 04:41 antes de empezar. Sin ninguna acción sobre el laboratorio. Lecturas:
bastión cada 30 s (`obs_muestreo.sh`, también Sensor1 y srv-dmz por ssh), Sensor1 cada 10 s
(`salud_captura muestrear`) y lectura de cada PCAP del anillo en cuanto se cierra (`obs_pcap.py`: el anillo guarda
≈ 17 min, así que O2 no podía medirse al final).

| # | Criterio (fijado antes) | Resultado | ¿Cumple? |
|---|---|---|---|
| O1 | Sin cambio de PID ni de `NRestarts` en los 7 servicios | 121 muestras en la ventana (125 con ±60 s), intervalo máx. 30 s. PID constantes: motor 1384, captura 1355, vía rápida 1387, suricata 1351, publicador 1386, relé 70246, agente 15020; todos con `NRestarts` 0 y activos | **Sí** |
| O2 | PCAP del anillo legibles, incluido el primero | 717 ficheros empiezan en la ventana (primero `live-20261106045002.pcap`, último `…054955`), **0 errores de formato**, 585 151 registros completos, 0 vacíos | **Sí** |
| O3 | Salto del anillo ≤ 7 s; rotación de `eve.json` | Salto máximo entre ficheros: **6,0 s**; hueco máximo entre el último paquete de un fichero y el primero del siguiente: 0,496 s. `eve.json` no rotó (última rotación 05-nov 23:59:57) | **Sí** |
| O4 | EVE sin hueco > 20 s y un solo proceso | 452 muestras, acotadas a 0,99 s antes y 7,43 s después; sin reinicios (arranque estimado 05-nov 23:59:00Z); sin repetidas ni parciales | **Sí** |
| O5 | `clasificar_periodo --suricata-eve`; clase tal cual; estado de Suricata medido | **C0** (anillo C0, vía rápida C0), `suricata_reinicios_dentro` 0; Suricata `cero_explicito` | **Sí** |
| O6 | `/home` libre ≥ 2 GB; carga y memoria | `/home` libre ≥ 12,16 GB; carga a 1 min con máximo 1,10 y mediana 0,18; `MemAvailable` ≥ 5,78 GB | **Sí** |
| O7 | Entregadas = aceptadas, en orden; publicador sin retroceso | 180 entregas en modo **paquete** (seq 4527–4706, sin huecos) y 180 aceptadas en orden; 0 entregadas sin aceptar. Publicador 4524 → 4709 sin retroceso. Retraso entre la generación y la aceptación: p50 0,83 s, p95 1,41 s, máximo 1,60 s (incluye el sondeo de 1 s del relé) | **Sí** |
| O8 | 0 `firma_invalida`, 0 `paquete_invalido` | 0 y 0 en la ventana; los acumulados (14 y 0) no cambiaron | **Sí** |
| O9 | Panel HTTPS 401 desde el bastión; agente verificado en srv-dmz | 401 en 125/125 muestras. Agente comprobado directamente en srv-dmz: activo, mismo PID y 180 aceptaciones | **Sí** |
| O10 | 0 aplicaciones; rulesets iguales; sin `--aplicar`/`--enforce`; v1 inactivos | 0 eventos `aplicacion`. Ruleset de Sensor1 `24c320e3…` y de srv-dmz `e3b0c442…` (sin tablas), iguales en todas las muestras y antes/después. 0 procesos con `--aplicar`/`--enforce`; v1 inactivos | **Sí** |
| O11 | Hashes congelados iguales antes y después | Ninguna diferencia entre `obs-antes-*` y `obs-despues-*`: modelo `df547da0…`, manifiesto `b3ad6805…`, esquema `e032a1a2…`, `ec78ca5` `SHA256SUMS` OK, `suricata.yaml` `0962ce68…`, instalados de bastión y srv-dmz | **Sí** |
| O12 | **Comparable** si hay ≥ 596 789 paquetes | **587 592** (98,5 % del umbral; 49,2 % de la hora del ensayo). **Carga insuficiente**: no se concluye nada sobre descartes bajo carga | **No** |

**Aceptación de la instalación (criterio §3, después de instalar).** Se cumple todo menos `verificar_*.sh` sin FALLO
(`evidencia/06-observacion/verif-post.txt`):

| Guion | Resultado | FALLO | Por qué; comprobación independiente |
|---|---|---|---|
| `verificar_srvdmz.sh` (`CON_SUDO=1`, respaldo de la fase C) | **OK**: sombra demostrada, feed.par < 60 s, helper rechaza un perfil ajeno | — | — |
| `verificar_bastion.sh` | **1 FALLO** | «relé v1 sigue activo e intacto» | Comprueba `is-active ppi-relay-feed.timer`, de cuando v1 seguía activo. El cierre 4A retiró v1 a propósito y ahora está `disabled/inactive`, que es el estado exigido en O10 |
| `verificar_sensor1.sh` | **2 FALLO** | «ppi-publicar-feed.timer activo» | Mismo defecto: espera activo el v1 retirado (`disabled/inactive`) |
| | | «motor_startup del candidato» | El guion busca el evento en `motor_decision.log`, pero el arranque (05-nov 23:59:01Z) quedó en `motor_decision.log.1` por la rotación diaria de las 23:59:03. En ese `.1`: `disparo: eventos`, `if_limpio_2026_10` y el umbral del manifiesto `-0.5693969936322356` (`motor_startup.txt`) |

Los tres son defectos de los guiones, no del sistema. Aun así el criterio está escrito como «sin FALLO» y **no se
cumple**. Corrección propuesta, no aplicada: v1 retirado debe esperarse inactivo, y `motor_startup` debe buscarse
también en el registro rotado. Después, prueba en banco y nueva ejecución de solo lectura.

> **Resuelto el 06-nov a las 06:29Z (§8b).** Los guiones se corrigieron, se probaron y se ejecutaron en solo lectura:
> rc 0 en los tres. Esta tabla y `verif-post.txt` se conservan como estaban.

## 8b. Verificadores corregidos (`a1cea5e`)

**Qué comprueba ahora cada guion.** El cálculo está en `deploy/etapa4/comun/verif_estado.py`, es solo de lectura y
no necesita sudo. Un error nunca cuenta como prueba.

- **v1 retirado** (`v1-retirado`). Se lee `systemctl show` de cada unidad.
  - El timer debe estar `inactive` y `disabled`/`masked`.
  - El servicio debe estar `inactive`. Si es `static`, solo cuenta cuando su timer está demostrado como retirado: un
    `static` solo lo arranca su timer o una orden manual, y lo segundo lo cubre la búsqueda de procesos.
  - **No debe haber ningún proceso** con un argumento cuyo nombre sea `publicar_feed.py` (Sensor1) o `relay-feed.sh`
    (bastión). `publicar_feed_v2.py` no cuenta.
  - Si `systemctl` falla, si faltan propiedades, si `/proc` está montado con `hidepid` o es ilegible, o si una línea
    de órdenes no se puede leer, el resultado es FALLO «no demostrable».
- **Arranque del proceso vigente** (`motor-arranque`):
  1. Se toman el `MainPID` de `ppi-motor` y su inicio real (`btime` + `starttime` de `/proc`).
  2. Se lee el registro actual y cada rotado (`.N` o `.N.gz`) cuya fecha de modificación no sea anterior a ese inicio.
     Un rotado anterior no puede contener el arranque, y se informa cuántos se descartan.
  3. Hace falta **exactamente un** `motor_startup` entre el inicio −1,5 s y el inicio +60 s, y ninguno posterior.
  4. Ese evento debe coincidir con la **línea de ejecución** del PID en 11 opciones: modelo, manifiesto, detector,
     disparo, EVE, captura, red, paso, historia, excluidas y protocolos.
  5. Además debe tener `procesamiento: incremental` y un umbral igual al del **manifiesto** (leído del detector de la
     línea de ejecución) y al **congelado** −0,5693969936322356.
  - Si solo hay un arranque antiguo, es FALLO «solo hay arranques anteriores al proceso vigente», aunque su
    configuración sea correcta.
  - Si un registro está ausente, ilegible o corrupto, o si una línea de arranque está dañada, es FALLO «no demostrable».
- **Guiones.** La nueva función `bloque()` marca FALLO cuando un bloque de comprobaciones termina con rc≠0 o no imprime
  ningún OK. Antes, si el Python de la traza del relé fallaba, no salía ningún FALLO.
  - El bastión comprueba además que el relé v2 usa `--entrega paquete`.
  - «Sin dc1» ya no da OK cuando `systemctl cat` falla.
  - Todas las demás comprobaciones siguen como estaban, entre ellas: candidato `ec78ca5` con `--disparo eventos` y sin
    `--enforce`, `-G 5`, `SHA256SUMS`, importaciones, decisiones con `decision_if`/`auth_failure`/`http_vista`/`dns_vista`,
    vía rápida, feed v2 < 60 s y firma, SIGUSR1, NTP y logrotate.
- **Sin cambios** en el detector, el modelo, las 28 features, los umbrales, las reglas, la política `if_senal`, la
  captura y Suricata.

**Los 3 FALLO antiguos y su resolución:**

| Guion · FALLO antiguo (`verif-post.txt`) | Causa | Comprobación nueva | Resultado nuevo (`verif-nuevo-a1cea5e.txt`) | Regresión en banco |
|---|---|---|---|---|
| `verificar_bastion.sh` · «relé v1 sigue activo e intacto» | Exigía `is-active ppi-relay-feed.timer`, el estado anterior al cierre que retiró v1 | `v1-retirado` del timer y del servicio, más la búsqueda de procesos `relay-feed.sh` | OK: timer `disabled/inactive`, servicio `static/inactive`, sin procesos | `test_bastion_estado_real_ok_y_regresion_v1`: con el estado real, el criterio antiguo da rc≠0 y el nuevo, OK |
| `verificar_sensor1.sh` · «ppi-publicar-feed.timer activo» | Mismo defecto con el publicador v1 | `v1-retirado` del timer y del servicio, más la búsqueda de procesos `publicar_feed.py` | OK, igual que arriba | `test_v1_retirado_correctamente_sensor1` |
| `verificar_sensor1.sh` · «motor_startup del candidato» | Solo leía `motor_decision.log`, y el arranque estaba en `.1` por la rotación de las 23:59:03. Además, cualquier arranque antiguo con ese umbral habría dado OK | `motor-arranque`: registro actual y rotados, y atribución al PID vigente | OK: PID 1384, inicio 1793923142,37, evento +1,47 s en `motor_decision.log.1`, 11 opciones coinciden y umbral = manifiesto = congelado | `test_arranque_vigente_en_registro_rotado_estado_real`, con los valores reales: actual sin arranques, `.1` con el vigente y `.2.gz` con dos antiguos |

**Pruebas** (`tests/test_etapa4_verificadores.py`, 52 casos). Usan los guiones reales con un `systemctl` falso, una raíz
`/proc` falsa (mountinfo, btime, stat y cmdline) y registros actuales, `.1` y `.N.gz`.

| Caso pedido | Pruebas | Resultado esperado y obtenido |
|---|---|---|
| v1 retirado correctamente | Sensor1, bastión y unidades no instaladas | OK (rc 0) |
| Timer o servicio v1 reactivado | Timer activo y habilitado, solo habilitado o arrancado a mano; servicio activo o habilitado; bastión completo con el timer activo | FALLO (rc 1). Con el timer no retirado, el servicio `static` tampoco pasa |
| Proceso v1 residual con el timer apagado | `publicar_feed.py` vivo; `relay-feed.sh` vivo | FALLO con su PID; las unidades salen OK |
| Fallo al consultar el estado | `systemctl` con rc 1, salida vacía o inexistente; `hidepid`; `/proc` sin mountinfo; cmdline ilegible (sin root) | FALLO «no demostrable», nunca OK |
| Cadena v2 parada | Relé v2 `inactive` (guion del bastión completo); motor `inactive`; relé v2 sin `--entrega paquete` | FALLO |
| Arranque vigente en el registro actual | Evento +1,47 s en `motor_decision.log` | OK |
| Arranque vigente en un registro rotado | En `.1` (estado real) y en `.2.gz` | OK |
| Solo un arranque antiguo, correcto pero ajeno | Los dos antiguos reales en `.1`; solo en un `.2.gz` anterior al inicio | FALLO |
| Arranque con configuración incorrecta | Umbral, disparo, procesamiento, detector, paso, historia, modelo, excluidas, protocolos o EVE distintos de la ejecución; ejecución con otro disparo; manifiesto con otro umbral | FALLO «configuración distinta» o «≠ congelado» |
| Registro ausente, ilegible o insuficiente | Actual ausente; `.gz` corrupto; `.1` sin permiso (sin root); línea de arranque corrupta; arranque sin marca de tiempo; dos arranques compatibles (ambiguo); arranque posterior; arranque > 60 s después; `stat` del PID ausente; `btime` ausente; manifiesto ilegible | FALLO «no demostrable» |
| Propagación en los guiones | `bloque()` con rc≠0 o sin OK; traza del relé ausente | FALLO |

- **Como root:** 50 passed y 2 skipped. Los dos omitidos se justifican porque con root `chmod 000` no impide leer.
- **Sin root (uid 65534):** 52 passed.
- Salidas: `evidencia/07-verificadores/banco-verificadores-{root,noroot}.txt`.

**Ejecución en el laboratorio** (06-nov, 06:29:11–06:29:18Z; `verif_nuevo.sh`, salida `verif-nuevo-a1cea5e.txt`):

| Host | Guion | rc | Resumen |
|---|---|---|---|
| Bastión (gadmin, sin sudo) | `verificar_bastion.sh` | **0** | Relé v2 activo, sin dc1 y en paquete. v1 retirado, sin procesos. Entrega hace 17,7 s; 4 742 entregas, p50 0,062 s. NTP |
| Sensor1 (m4rk, sin sudo) | `verificar_sensor1.sh` | **0** | 6 servicios activos. v1 retirado, sin procesos. Arranque del proceso vigente demostrado. 1 995 decisiones con los campos nuevos. Vía rápida avanza. Feed v2 < 60 s y firma válida. SIGUSR1, NTP y logrotate. `NRestarts` 0/0/0 |
| srv-dmz (`CON_SUDO=1`, solo lecturas) | `verificar_srvdmz.sh` (sin cambios) | **0** | Sombra demostrada (`con_aplicar=0`, `tablas_cyberflow=0`, `eventos_aplicacion=0`). feed.par < 60 s. El helper rechaza un perfil ajeno |

No se reinstaló ni se reinició nada. El paquete solo se copió y se verificó.

## 9. Veredicto por componente

| Componente | Veredicto |
|---|---|
| P1: medida de Suricata por EVE `stats` (`salud_captura` 2026-11-06.1, `clasificar_periodo`, `vigia_4c`, I5) | **Cerrado.** Probado en banco y en vivo: C0 y `cero_explicito` medidos, I5 informativo `cumple`. La ventana del ensayo del 04-nov sigue siendo C3 |
| P3: `rx_dropped` | **Explicado con incertidumbre declarada.** Contador del núcleo, no del driver. Las tramas examinadas están en los PCAP, pero no se comprobó cada incremento: no se afirma la ausencia universal de pérdida. Faltan una traza trama a trama y las fuentes de Ubuntu (§0, §4) |
| P4: entrega `feed.par` | **Cerrado.** Reproducido, corregido, sin rechazos en banco ni en 180 entregas reales, firma y secuencia intactas |
| P5: sellado de evidencia | **Cerrado.** Todas las carpetas de hoy verifican, también en la copia del repo |
| Instalador `p4-instalador 2026-11-06.2` | **Correcto.** 33 casos con fallos deliberados; en el laboratorio, rc 0 en bastión y en srv-dmz, con respaldos estrictos fuera de la evidencia |
| Integración en sombra (relé paquete + agente paquete) | **Verificada en O1–O11**, sin aplicaciones ni cambios de ruleset, **con la carga de fondo de una red sin generadores**. Demuestra el transporte del feed firmado, no la eficacia (§0) |
| Carga de la observación (O12) | **Insuficiente.** No se concluye nada sobre descartes bajo carga. No había generadores legítimos: 0 ráfagas y 0 flujos grandes (`PROTOCOLO-CARGA.md` §1) |
| Aceptación §3 (`verificar_*.sh` sin FALLO) | ~~No cumplida tal como está escrita: 3 FALLO por defectos de los guiones (§8)~~ → **Cumplida el 06-nov a las 06:29Z** con los guiones corregidos `a1cea5e`: rc 0 en los tres (§8b) |
| Estabilidad con carga suficiente | **No demostrada.** Protocolo E-carga publicado y no ejecutado |
| Panel | Responde 401 sin sesión; sigue sin ver al agente (P6 del cierre, conocido) |
| 4B, control formal | **Todavía no:** falta E-carga (criterio único, §0). Puede seguir preparándose |
| 4C (campaña A en sombra) y campaña B (respuesta aplicada, posterior) | **No autorizadas** |

## 10. Correcciones al cierre complementario

En `../etapa4a-cierre-complementario-2026-11-04/README.md` se añaden notas marcadas «**Corrección (pendientes 4A,
06-nov)**», sin borrar el texto original:
- **§6.3, `rx_dropped`:** «tramas sin manejador» no estaba demostrado entonces y `rx_nohandler` es 0. Diagnóstico y su
  incertidumbre: §4 de este informe.
- **Veredicto y §11, criterio de avance unificado:** la 4B **puede prepararse**; su **control formal** espera a que
  P1 esté cerrado y la integración verificada; la 4C y la campaña B **no** están autorizadas. (El cierre decía en un
  sitio «no iniciar la 4B hasta resolver P1» y en otro solo «no iniciar la 4C».)
- **§7 y §8:** «C3, no evaluable» significa que **faltaba la medida**, no que hubiera evidencia de descartes; la medida
  retrospectiva (cero explícito) está en §3 de este informe y no reclasifica la ventana.
- **§11 P5:** resuelto (§6).

Su `MANIFIESTO.sha256` se regenera porque cambia el README; las líneas de `evidencia/` no cambian.

**06-nov, 06:29Z.** La nota del §6.3 sobre `rx_dropped` decía «que **sí** están en los PCAP». Recibe una precisión
anotada en el mismo sitio: lo comprobado son las tramas examinadas, no cada incremento del contador. El manifiesto de
esa carpeta se regenera otra vez; `evidencia/` sigue sin cambios.

El informe de la instalación 4A (`../etapa4a-instalacion-2026-11-04/README.md`, línea «no es pérdida de captura»)
no se modifica. En lo que respecta a `rx_dropped`, prevalecen §0 y §4 de este informe.

## 11. Procedimientos

**Reversión manual** (ninguna se ha necesitado):
- `[BASTIÓN gadmin] → lo ejecutas tú (sudo con contraseña)`:
  `bash ~/cf-e4/paquete-b18c286/deploy/etapa4/pendientes/bastion_p4.sh revertir /home/gadmin/respaldos-etapa4/bastion-p4-20261106T043848Z`
  → relé por pareja.
- `[SRV-DMZ adminsrvdmz] → lo ejecuto yo (sudo -n)`, **después** del bastión:
  `bash ~/cf-e4/paquete-b18c286/deploy/etapa4/pendientes/srvdmz_p4.sh revertir /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z`
  → agente con `--feed/--firma` (código de la fase A, que admite ambos modos).
- Para volver al estado previo a la fase A: `srvdmz_p4.sh revertir-heredado /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-20261106T035127Z`.
- Códigos: 0 OK · 30 reversión fallida (se detiene y dice qué falta). La reversión nunca arranca v1 ni usa `--aplicar`.

**Medidas repetibles:** `evidencia/06-observacion/obs_sensor_post.sh` y `obs_p4_post.sh` (aceptan `desde hasta`).

## 12. Limitaciones

- **Carga.** La hora observada tuvo menos carga que el umbral comparable (O12). No dice nada sobre descartes con
  ráfagas ni sobre P2 (anillo de Suricata con carga real).
  - **Causa (hallada el 06-nov, 06:30Z):** los seis generadores legítimos estaban parados desde el reinicio del host
    de clientes (05-nov 23:58Z; las unidades están `disabled`).
  - La observación se planificó sin comprobar que funcionaran. Fue un fallo del protocolo de la observación, y por
    eso P0 de E-carga lo comprueba antes de empezar.
- **Los verificadores corregidos** atribuyen el arranque al proceso vigente por tiempo, línea de ejecución y umbral.
  El evento `motor_startup` no lleva PID: si dos procesos con la misma configuración arrancaran en el mismo intervalo
  de 61,5 s, la atribución sería ambigua. En ese caso el guion da FALLO «ambiguo»; no elige uno.
- **Una prueba de regresión no determinista** (`test_patron_antiguo_falla`, ajena a esta corrección): falla en
  ≈ 1 de cada 10 ejecuciones (§2). Queda pendiente hacerla determinista.
  - **Resuelto en `38ee91d`.** Un escritor controlado por barreras (tuberías) mantiene `salida.txt` abierto:
    1. el fichero existe y está en el manifiesto antes de calcularlo;
    2. la línea final se escribe solo por orden explícita, después del hash;
    3. `sha256sum -c` da `./salida.txt: FAILED`.
  - Hay una prueba separada que comprueba que el sellado nuevo produce hashes válidos sobre ficheros finalizados.
  - Sin pausas, sin `skip` ni `xfail`: 200 de 200 en `f6dc685` (`evidencia/09-ecarga-v2/regresion-f6dc685-root.txt`).
- **No es una prueba de eficacia.** Sin ataques ni generadores, el feed no tuvo entradas. La cadena se demostró con
  feeds firmados reales, pero vacíos; la aplicación de restricciones no se probó, porque no estaba autorizada.
- **P3.** La explicación se apoya en el código de upstream 6.8 y en una correspondencia de tasas (§4).
- **Fase A con la versión .1.** Su respaldo contiene su propia evidencia. Por eso existe `revertir-heredado`, que
  solo usa los ficheros del manifiesto.
- **Verificador de PCAP** (`obs_pcap.py`): la hora de fin estaba mal calculada (06:11:30Z en vez de 05:51:30Z).
  Siguió leyendo, solo lectura, hasta que lo detuve a las 05:56:25Z (`sensor1/incidencias.txt`). Los ficheros de la
  ventana ya estaban leídos.
- **`pgrep` en el sellado.** Los dos primeros intentos de sellar se pararon solos, porque el patrón coincidía con la
  propia orden. No se selló nada a medias: el guion que funcionó compara el ejecutable exacto (`sellar_s1.sh`).
- **Los relojes** de los tres hosts se sincronizan por NTP (los `verificar_*.sh` dan «reloj sincronizado»). Las
  correlaciones relé ↔ agente dependen de ello.

## 13. Evidencia

```
README.md                    este informe
CRITERIOS-FIJADOS.md         criterios publicados antes de instalar y de observar (997c8e2, sin cambios)
PROTOCOLO-CARGA.md           E-carga v1 (36a3739): sustituida por la v2, se conserva sin cambios; nunca ejecutada
PROTOCOLO-CARGA-v2.md        E-carga v2: versión vigente (publicada, NO ejecutada)
MANIFIESTO.sha256            sha256 de cada fichero (bytes publicados), dos espacios, orden LC_ALL=C sort -f
ecarga-v2-preparacion/       preparación de E-carga v2 (NO ejecutada ni programada)
  PREPARACION-ECARGA-v2.md   paquete, fuente de cada K/S, secuencia del día, paradas, conservación, estado, orden
  guiones-c7f24510/          guiones de ejecución tal como están en los hosts (con SHA256SUMS)
  evaluacion-e83f4be6/       herramientas de evaluación tal como están en los hosts (con SHA256SUMS)
  *.PLANTILLA-SIN-RESULTADOS.json   forma de la entrada y de la trazabilidad; ningún valor medido
evidencia/
  01-rx_dropped/             contadores NIC/driver/softnet y recuento de tramas en los PCAP (P3)
  02-firma_invalida/         correlación relé ↔ agente de cada rechazo; hueco de secuencias
  03-banco/                  cadena P4 pareja/paquete; regresiones (313f8f8 y b18c286)
  04-p1-medida/              extracción de EVE stats y explicación de 1 193 578 / 1 201 704
  05-instalacion/            verify de systemd, fase A, bastión (salida de Mark), fase C
  06-observacion/            guiones, estado antes/después, análisis posteriores, verificar_*.sh, motor_startup, O6
    bastion/                 muestras cada 30 s y copias de las trazas del relé y del agente (con su SHA256SUMS)
    sensor1/                 muestras de salud_captura, lectura de cada PCAP, clasificación final y prueba en seco,
                             incidencias.txt (con su SHA256SUMS; ambos verificados en esta copia)
                             verif-post.txt = salidas ANTIGUAS con los 3 FALLO (se conservan)
  07-verificadores/          verif_nuevo.sh y verif-nuevo-a1cea5e.txt (salidas NUEVAS con rc), banco de los
                             verificadores como root y sin root, regresión completa de a1cea5e
  08-carga/                  estado de los generadores (clientes_ro*), flujos de los perfiles en EVE e intensidad
                             de la ventana del 06-nov con el método del ensayo (intensidad_obs)
  09-ecarga-v2/              referencia de desarrollo K4a/K4b (38ee91d, con el defecto del tramo residual, y
                             f6dc685, corregida), flow-timeouts, obs_pcap en seco, calendario en epoch,
                             simulación de K4b, regresiones 38ee91d y f6dc685 como root y sin root
  10-veredicto-contrato/     evaluador 2026-11-06.4 (ae2900e): reproducción de los tres fallos con f6dc685 y con
                             la corrección, pruebas nuevas contra f6dc685 con el motivo de cada fallo, regresiones
                             completas de ae2900e como root y sin root, sha256 de la r1 del protocolo v2 (8f17273)
  11-preparacion-ecarga/     copia y verificación del paquete ae2900e en los hosts, copia de guiones y evaluación,
                             comprobación previa y en seco, prueba de la vía de parada, prueba de humo (PRUEBA, sin
                             valor de medida), lecturas en seco de S7 y S11, pruebas en banco y rechazo de la plantilla
```

Respaldos e instalaciones en los hosts (no se copian aquí; se citan en §8 y §11). Los guiones de producto están en la
rama `recuperacion/etapa4a-pendientes-20261106`:
- instaladores en `b18c286`;
- verificadores corregidos en **`a1cea5e`**;
- herramientas de E-carga v2 en `f6dc685`;
- evaluador `evaluar_ecarga.py` 2026-11-06.4 en **`ae2900e`**.
