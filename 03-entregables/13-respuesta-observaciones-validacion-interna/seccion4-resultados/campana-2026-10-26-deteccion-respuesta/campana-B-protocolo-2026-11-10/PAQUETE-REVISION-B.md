# PAQUETE DE REVISIÓN — Campaña B (versión 3, 11-nov-2026): D5 sin reinicio con OpenSSH real, lanzador del bastión, guiones por host, instrumentación y criterios

**Estado: PREPARADO EN BANCO Y COPIAS LOCALES. NO desplegado. Sin orden de corrida.** Nada de este paquete se instaló en ningún host. C3 vigente; los resultados históricos de B2 y la primera corrida (X3) siguen intactos y separados. Este documento no autoriza nada: lista lo que Mark debe decidir y lo que se haría después.
Sustituye a las versiones 1 y 2 (**v3.1: revisada contra los hosts reales con lecturas y modo seco, §13**). Cambios respecto a la v2: transporte probado con **OpenSSH real** en un banco aislado (§2b), **copia de banco del lanzador del bastión** probada contra la puerta integrada (§2c), prueba omitida identificada (§2d), **guiones concretos de instalación, aceptación y reversión por host** ensayados sobre árboles falsos (§8), hashes finales (§7) y estimación rehecha (§12).

## 1. Estado de verificación (todo en banco; lo que NO se verificó está en §11)
| Componente | Estado | Evidencia (carpeta `propuestas\d5-sin-reinicio\` salvo indicación) |
|---|---|---|
| Publicador derivado, adaptador, auditoría rotable, integración de D5 con bloqueo persistente | verificado (10-nov y re-ejecutado 11-nov) | `evidencia-systemd\`, `evidencia-logrotate\`, `evidencia-integracion\`, `evidencia-integracion-v2\` |
| **Transporte distribuido bastión ↔ Sensor1** (subcomando de Sensor1, envoltorio, id conservado, corte de SSH) | **verificado en banco**: 14 pruebas, 12/12 mutaciones | `evidencia-transporte\pruebas-transporte.txt`, `mutaciones-transporte.txt` |
| Espera de 75 s (Hallazgo 2, opción A) | verificada **a escala 1/60**: 3 pruebas | `evidencia-transporte\pruebas-espera-75.txt` |
| Instrumentación (intentos con hora, transacciones, muestreador, `e3_v2`) | verificada con datos sintéticos: 13 pruebas; script de la inundación probado en loopback | `instrumentacion\evidencia\` |
| Suite completa sin privilegios | **66 pasan, 3 omitidas** (las 3 son módulos que exigen root; ver §2d) | `evidencia-ssh-real\suite-no-root-v2.txt` |
| **OpenSSH real** (comando forzado, `restrict`, lista permitida, huésped fijado, corte tras recibir, reconexión) | **verificado en banco**: 5 pruebas (incluye un control negativo) | `evidencia-ssh-real\` |
| **Lanzador del bastión** (copia de banco) → puerta integrada, con OpenSSH real y srv-dmz sintético | **verificado en banco**: 2 pruebas | `evidencia-ssh-real\pruebas-ssh-real-y-lanzador.txt` |
| **Guiones por host** (instalar/aceptar/revertir) sobre árboles falsos | **ensayados**: 10 pruebas | `paquete-despliegue-evidencia\pruebas-guiones.txt` |
| Criterio «SPAN o salida» | redactado, **pendiente de aprobación** | `CRITERIO-E3-SPAN-O-SALIDA.md` |
| Hallazgo 2 | propuesta A recomendada, **decisión explícita** | `PROPUESTA-HALLAZGO-2.md` |

## 2. Transporte distribuido (lo nuevo)
**Diseño.** La puerta corre en el bastión; el publicador y su canal de control están en el Sensor1. Se añade al Sensor1 un subcomando local (`sensor_control_d5.py`, usuario `m4rk`) y en el bastión un cliente (`transporte_bastion.py`) que habla con él por SSH.
- **Quién puede solicitar y consultar.** Solo quien posea una clave SSH **dedicada** del bastión (cuenta `gadmin`, **solo desde 10.10.10.30**: `from=`), instalada en `~m4rk/.ssh/authorized_keys` con comando forzado y `restrict` (mismo patrón que la clave `cyberflow-feed-v2-rele` ya existente en el Sensor1); sin shell, sin reenvíos. Línea propuesta (a instalar, no instalada):
  `from="10.10.10.30",command="/usr/bin/python3 -I /home/m4rk/cf-b/herramientas/sensor_control_d5.py --base /home/m4rk/feed-v2/d5/control --feed /home/m4rk/feed-v2/feed.json --estado /home/m4rk/feed-v2/estado.json --traza /home/m4rk/feed-v2/traza.jsonl --auditoria /home/m4rk/feed-v2/d5/auditoria/d5-auditoria.jsonl --ssh-original",restrict ssh-ed25519 <clave-publica-nueva> cf-bastion-d5`
  Las rutas las fija ese comando: el cliente no puede cambiarlas. Lista blanca estricta (verificada con 9 comandos rechazados, incluido `…; rm -rf /` y otro origen): `solicitar --id <32 hex> --origen 10.10.20.30`, `resultado --id <32 hex>`, `cancelar --id <32 hex>`, `feed --desde <epoch>`. `solicitar` y `cancelar` solo actúan sobre el origen del experimento y sobre ese id; `resultado` y `feed` son de solo lectura.
- **Conservación del id.** El bastión genera el id (UUID de 32 hex), lo **guarda con fsync en `limpieza-pendiente.json` antes de pedir nada** y usa siempre ese mismo id para solicitar y consultar. En el Sensor1 queda `solicitudes/<id>.json` (registro persistente, escrito **antes** del control), el control, el acuse con el mismo id y las líneas `consumido`/`publicado` de la auditoría. Prueba: el mismo id aparece en los cinco sitios.
- **Corte de SSH tras recibir.** El Sensor1 recibe y consume la solicitud, la conexión se pierde y SSH sigue caído: el cliente intenta consultar **ese mismo id**, no lo logra → resultado **incierto** (`sin_transporte`), la puerta queda **bloqueada** y el pendiente se **conserva**. Tres invocaciones nuevas con SSH caído: bloqueadas, **0 llamadas de red**. SSH vuelve: sigue bloqueada (el bloqueo no se borra solo). Tras la **reanudación manual registrada** (quién y por qué), la siguiente invocación **solo consulta** el id pendiente (`resultado`), obtiene el acuse y continúa; **una sola limpieza** (un `consumido`, un registro de solicitud, una orden `solicitar`).
- **Id desconocido** (la orden nunca llegó): el cliente **no la reenvía con el mismo id**; queda incierto y bloqueado; solo un **descarte manual registrado** del pendiente (`descartar_pendiente(quien, motivo)`, que archiva el caso) permite emitir un id nuevo.
- **Idempotencia en el Sensor1:** repetir `solicitar` con el mismo id = `ya_recibida` (una sola limpieza); un id distinto con un control pendiente = `pendiente_previa` (no se acumula ni se sobrescribe); `cancelar` solo retira el control de **su** id (un id viejo no puede retirar el de otro: prueba y mutación).
- **Separación probada:** el publicador es un proceso del uid del Sensor1 y el árbol del Sensor1 es 0700; el uid del bastión recibe `PermissionError` al leer o anexar el acuse, la auditoría y el control (6 de 6).
- **Límites del banco (§2 con SSH simulado):** el «SSH» era una función; ahora se repite con OpenSSH real (§2b). Los usuarios del banco son uids 1001/1002; el real del Sensor1 es **uid 1000** `m4rk` con `python` del venv. **La clave dedicada y el `sshd` reales del laboratorio no se han ejercido.**

## 2b. OpenSSH real en banco aislado (lo nuevo)
**Banco:** contenedor `--network none` (solo loopback 127.0.0.1), OpenSSH_10.0p2 Debian-7+deb13u4 (cliente y `sshd` reales); **claves de huésped y de usuario generadas dentro del banco, exclusivas de prueba**; ninguna clave, `known_hosts` ni conexión del laboratorio entra en el banco (solo se conservan como evidencia las claves **públicas** de prueba). Bastión = usuario `gadmin` (uid 1002, ejecuta el cliente `ssh`); Sensor1 = usuario `m4rk` (uid 1001, árbol 0700, publicador como proceso suyo). Dos `sshd` (puertos 2222 y 2223, claves de huésped distintas) para probar la identidad del servidor.
| Límite de SSH | Resultado (5 pruebas; `evidencia-ssh-real\pruebas-ssh-real-y-lanzador.txt`) |
|---|---|
| Comando forzado y lista permitida | `resultado`, `feed`, `solicitar`, `cancelar` funcionan por `ssh` real; `cat /etc/passwd`, `id`, otro origen, `…; id`, `bash -c`, un id con `../` y la sesión **sin orden** se rechazan (rc 2, JSON `rechazada`), sin crear ningún registro ni control |
| `restrict` | sin pty; **reenvío remoto denegado** (con `ExitOnForwardFailure` la conexión muere, rc 255); subsistema `sftp` sustituido por la orden forzada y rechazado; agente y X11 no habilitan nada. **Control negativo:** con la misma clave y comando pero **sin `restrict`** el reenvío **sí** se concede (la comprobación discrimina) |
| Identidad del servidor fijada | clave de huésped fijada en `known_hosts` → conecta; **servidor suplantado** (otra clave de huésped en 2223 con la de 2222 fijada) → `Host key verification failed` **antes de ejecutar nada** (sin registro en el Sensor1 y sin autenticación en el servidor suplantado); `known_hosts` vacío con `StrictHostKeyChecking=yes` → falla |
| Clave de usuario ajena | `Permission denied (publickey)` |
| **Recepción seguida de corte** | un envoltorio de prueba ejecuta la orden REAL en el Sensor1 y retrasa la respuesta 3 s; el cliente agota el tiempo (1,2 s): el Sensor1 **sí recibió y consumió** la solicitud (un registro, un `consumido`); resultado incierto → puerta **bloqueada** |
| **Reconexión y bloqueo** | con SSH ya funcionando, 3 invocaciones nuevas: **bloqueadas con 0 conexiones nuevas** (contador de «Accepted publickey» sin cambio); tras la **reanudación manual registrada** se consulta **el mismo id** y se continúa: **una sola limpieza** |
**Tiempos observados (banco, loopback; `evidencia-ssh-real\tiempos-ssh.json`):** orden de solo lectura 0,15–0,24 s; `solicitar` 0,17–0,26 s; corte tras recibir hasta el bloqueo 3,8 s (con tiempo de espera de 1,2 s por orden y 2 consultas fallidas); reconexión y consulta del mismo id hasta continuar 3,1 s; una puerta completa con el lanzador 3,1 s (con `espera_agente` de banco 2 s). **No son tiempos del laboratorio** (sin latencia de red ni carga).
**Límites:** el envoltorio que retrasa la respuesta es de prueba (el comando forzado real no lleva retraso); no se ejercieron las claves ni el `sshd` del Sensor1 real; versiones de OpenSSH de los hosts desconocidas. No se hicieron mutaciones de las pruebas de SSH (se añadió el control negativo en su lugar).

## 2c. Copia de banco del lanzador del bastión (`lanzador_puerta_banco.py`)
Equivale al modo `puerta` de `compuerta_b.py` (que **no se modifica**: se importa de `herramientas\`) pero llama a la puerta integrada (`puerta_fn_banco`) con `LimpiezaRemota` + `SshReal`; cada turno del bucle construye objetos nuevos y solo comparte ficheros. Subcomandos `ejecutar`, `reanudar` y `descartar-pendiente` (decisiones manuales registradas, con quién y por qué). `--espera-fin` por omisión 15 s (valor actual); 75 s sigue como **propuesta** del Hallazgo 2. Para srv-dmz, en el laboratorio usa `orquestar_b.SshRunners.srv` (`--ssh-sensor-legado`/`--ssh-srv-legado`); en banco, srv-dmz sintético.
Pruebas (OpenSSH real, proceso nuevo como `gadmin` en cada ejecución): (1) una puerta con acuse → `liberada`, un `consumido`, sin bloqueo; (2) huésped mal fijado → `fallida` ×3 con **1 intento real y 2 omitidos**, bloqueo y pendiente en disco; ssh arreglado pero **sin** reanudación → sigue bloqueada con 0 conexiones nuevas; `reanudar` sin quién/por qué rechazado (rc 2); `reanudar` registrada → la ejecución **solo consulta el id pendiente** (desconocido en el Sensor1: incierto, bloqueado, **no se reenvía**); `descartar-pendiente` + `reanudar` registrados → **un** id nuevo y `liberada`.

## 2d. Prueba omitida: identificación e impacto
La suite sin privilegios (`--user 65534`, sistema de ficheros de solo lectura) informa **«66 pasan, 3 omitidas»**: `SKIPPED [3] test_transporte_d5.py:22 — requiere root en el contenedor`. Son **tres módulos**, no una prueba: `test_transporte_d5.py` (14 pruebas), `test_ssh_real_d5.py` (5) y `test_lanzador_puerta_banco.py` (2); los dos últimos importan del primero y heredan su salto. **Por qué se omiten:** necesitan crear usuarios (uid 1001/1002), cambiar de usuario para los procesos del Sensor1 y del bastión y arrancar `sshd`. **Impacto:** ninguno en la corrección (se ejecutan **aparte como root**: 14/14 y 7/7, con evidencia); sí es un riesgo de proceso: **una ejecución sin root de la suite no ejercita el límite distribuido ni SSH**, y «66 pasan» no los incluye. Mitigación propuesta: ejecutar siempre los tres módulos en el contenedor como root (`pruebas-transporte-simulado.txt` y `pruebas-ssh-real-y-lanzador.txt`) y citar los dos totales.

## 3. Auditoría: ruta, propietario, permisos y retención propuestos (a revisión; no instalado)
| Elemento | Propuesta |
|---|---|
| Publicador (escribe) | `m4rk` (verificado en solo lectura el 10-nov: `User=m4rk`, `UMask=0022`; `Restart=always`; ExecStart con `/home/m4rk/cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py`) |
| Control | `/home/m4rk/feed-v2/d5/control/` `0700 m4rk:m4rk` (`control.json`, `solicitudes/`, `lock`) |
| Auditoría | `/home/m4rk/feed-v2/d5/auditoria/` `0750 m4rk:m4rk`; ficheros `0640 m4rk:m4rk`. **Nueva**, separada de `~/feed-v2/d5-auditoria/` (copias de estado de la D5 antigua, que se conserva) |
| Lectura | el subcomando forzado (`m4rk`); análisis posterior por `m4rk` o `root` (archivadora: copiar, no mover). Sin grupo de lectura propio (en banco `d5aud` era una simulación) |
| Rotación | `d5-auditoria.logrotate.propuesta`: `su m4rk m4rk`, `daily`, `rotate 30`, `compress` + `delaycompress`, `nocopytruncate`, `create 0640 m4rk m4rk`; sin `dateext` |
| Retención | 30 generaciones diarias ≥ campaña + análisis; fuera de retención el id queda «publicación sin confirmar»; copia con hash al cierre de la campaña |
| Verificado en banco | `logrotate` real **forzado** con `su m4rk m4rk` sobre ficheros del usuario del publicador: el fichero nuevo sale `0640` del mismo usuario, el publicador sigue escribiendo y el id viejo se reconstruye desde `.1`/`.gz` **a través del subcomando del Sensor1** |
| Sin verificar | la ejecución **diaria** del temporizador; `logrotate` real en el Sensor1 (versión desconocida); el estado de `logrotate.timer` en el Sensor1 durante la corrida (se aplaza según el protocolo) |

## 4. Cómo se invoca D5 de verdad (recordatorio)
`compuerta_b.py puerta` llama a `puerta_fn()` en cada turno y construye una `Puerta` nueva; cada orden remota es un proceso SSH. El bloqueo vive en `puerta-bloqueo.json` del bastión (atómico, `flock`, ilegible = bloqueado; la reanudación lo archiva). La puerta integrada hace un **solo intento** (sin reintento automático).

## 5. Criterio «SPAN o salida» (para revisión antes de otra corrida)
Texto, referencias y evidencia exigida por cada vía: `CRITERIO-E3-SPAN-O-SALIDA.md`. Resumen: los objetivos dicen «SPAN **o** salida»; el borrador del protocolo v3 dice «y»; `analizar_b.py` solo implementa SPAN; se propone «o» y se **registran ambas vías** siempre que haya datos (`e3_v2` no modifica `analizar_b` y sin serie de salida devuelve exactamente lo mismo → B2 sigue indeterminado).

## 6. Hallazgo 2: espera de 75 s (probada a escala 1/60)
Puerta a fin + 15 s con decisión a fin + 50,6 s → falla y bloquea; a fin + 75 s → pasa con **una** solicitud y la señal tardía se ve y se limpia; decisión a fin + 85 s → falla (el límite). Detalle y límites en `PROPUESTA-HALLAZGO-2.md`. **Decisión explícita de Mark.**

## 7. Versiones y hashes (SHA-256 completos, 11-nov)
| Artefacto | SHA-256 |
|---|---|
| propuestas\d5-sin-reinicio\adaptador_banco.py | 41eaca8aa54ed0db693864f86c6f0324fc6c45f940a9a8f1dd1821c6cd843132 |
| propuestas\d5-sin-reinicio\adaptador_banco_rot.py | 4cedd2ce77371a4a93aee0862d01d23faada5fc1773c4eef46d7a019c88948a1 |
| propuestas\d5-sin-reinicio\auditoria_d5.py | d1095bc5e95392255f99a2ef04d1412e75cb9e76b08a651dfedcc3d08a301519 |
| propuestas\d5-sin-reinicio\d5-auditoria.logrotate.propuesta | c13d0d36bf308bc1e3ad203e5ad6cfe177612b11248e57c6dc1c2a83f59c3133 |
| propuestas\d5-sin-reinicio\d5_control.py | ec22b721ff117d1ee5cbe30925dd318e8abf7788026f283bf43fda24f7fa2606 |
| propuestas\d5-sin-reinicio\emulador_compuerta_d5.py | ae56514fca8abf8fa84332d410867b322c9e19efe65628e5ac9cb8960115d0da |
| propuestas\d5-sin-reinicio\hacer_d5_episodio_banco.py | 65511cc1a313cd552d46413044402f62e21a62f3211713089ed2047408455b19 |
| propuestas\d5-sin-reinicio\hacer_publicador_d5.py | 3edf26a4fea1bec94a46d00cf1c2d61ec84823648ac0247bbbca0ddf4a049d69 |
| propuestas\d5-sin-reinicio\lanzador_puerta_banco.py | c2ec10b42751985cfe4749a19d6fa58289979be2ba242368c240d72742e2c438 |
| propuestas\d5-sin-reinicio\lector_solo_lectura.py | b66cfb4469a7e28f1b882cfbc1c5c8c9537a3710fe63e507c4faa7915b0e532e |
| propuestas\d5-sin-reinicio\mutar_auditoria_rot.py | 42362639261f2a64014a5107e0c092ce8309cc6ad9658101c11f6d571d46f1a5 |
| propuestas\d5-sin-reinicio\mutar_d5_sin_reinicio.py | fa9c57af2de118c94a4458822b038d892093487809bb3b5ef534d68bb0f158da |
| propuestas\d5-sin-reinicio\mutar_integracion_d5.py | e84c511fdf771b6ef71f1134a87acd80807dd6b2b5db223bb4847f5e9d4d3032 |
| propuestas\d5-sin-reinicio\mutar_invocaciones_d5.py | 55c36bdfeb4308e55a5adf0d9788121572c39f9da9f3affc8acd9968cd231320 |
| propuestas\d5-sin-reinicio\mutar_puerta_simulada.py | 166ae4ef0c4cd83a941be7d1c758e053dfe70841290a924a191803b87121e2eb |
| propuestas\d5-sin-reinicio\mutar_transporte_d5.py | 2cb348a34108df5ee235e7ccfe213c24d77e8766ce44bfa912ddf59615cdc0f2 |
| propuestas\d5-sin-reinicio\probar_integracion_systemd.py | 3e6c7eb99710402ead4ddaa46fe4bba67dbab530b2c976a8da351b262bab5bcd |
| propuestas\d5-sin-reinicio\probar_logrotate.py | 5d3bfd0b3af45148e9b53fa867cb18a2322561e00d8d6ec6537282ac1673da20 |
| propuestas\d5-sin-reinicio\probar_systemd.py | fb3b8917fcf836e4f7983d3a0ec48142c68c78e5d9bbd2e76ce788fd0d6ff57c |
| propuestas\d5-sin-reinicio\puerta_simulada_banco.py | 52e4fdbaa9e10de46afab7e7a0d0c7128101770bce6ce3dee29735198b83e381 |
| propuestas\d5-sin-reinicio\sensor_control_d5.py | 6f36032e6f74c124c0ba9158a8cacccb34876d88938bddcbf333d56073c2efc0 |
| propuestas\d5-sin-reinicio\test_adaptador_extremo_a_extremo.py | 6f306db7a9afdd76961e858226bbd6f851c8bbd26685714f60327e5b705ada8a |
| propuestas\d5-sin-reinicio\test_auditoria_rotacion.py | 8943dc1be3aa50ccac7edb3fab3d32437854ecb91078e6685de384c0518a251b |
| propuestas\d5-sin-reinicio\test_d5_sin_reinicio.py | 5ceeab64f4915736b12ab939261fa8b62d8413c3e09936e0234f8760c12bb0a1 |
| propuestas\d5-sin-reinicio\test_espera_puerta.py | ebc783a88213f6db5e0e936e3cb8f37e4fc061d5d181fee77e14b4ff38b8a571 |
| propuestas\d5-sin-reinicio\test_flujo_completo.py | df069b03e62d4284fa239f16dcf1c407cec701b64de995a3c7861bb465df0b16 |
| propuestas\d5-sin-reinicio\test_integracion_d5.py | eb2d9e75a1ad1b09f40290e76134a78389e89e548d74935797efb53f071d1b88 |
| propuestas\d5-sin-reinicio\test_invocaciones_d5.py | dfd7c722da35354621afbad0b8eaf9a64cf22a30c0308bfd92d85c6df5c712aa |
| propuestas\d5-sin-reinicio\test_lanzador_puerta_banco.py | 3c7597a997aeac1f7e38f30e8cfd6e4ef2d45f316726902b3722cff944a6e395 |
| propuestas\d5-sin-reinicio\test_puerta_simulada.py | c1955900c05b23c5e707ff80764cecf61aecc123bb5e7f91ac6ae38512c8ccea |
| propuestas\d5-sin-reinicio\test_ssh_real_d5.py | 26b8a44aa584cb463645ace3b4d97a4478a3a8aaee3edee45c545f7ff8c08dd5 |
| propuestas\d5-sin-reinicio\test_transporte_d5.py | b02b3a7acde4146d18af3d06618aff9802c29be2da8edac9217ed37e03a4301d |
| propuestas\d5-sin-reinicio\transporte_bastion.py | 2dc8d7eb306880dd0e563c83ffa0c2bbb55b88aafc21fc63d7bfdc92d3ebb2b3 |
| instrumentacion\analizar_b_instrumentado.py | 618ac31c7938127060215e70844c60bf900f07d1129b2f0845d13ae66477a99e |
| instrumentacion\analizar_intentos.py | 687a1e1e8823d8241cf982cdc63f40640bcbb9dc2d5b1990a2a52c7899f8c2d7 |
| instrumentacion\clientes_factor1_tx.py | d86c7edc9f10e353fca11aee506bd13bf1b6c3a587e8baf55d7d9d73d8d6c307 |
| instrumentacion\inundacion_instrumentada.sh | 7ac5335848469ed6a4facdf55a79dab82e2d7050404dc881a95d89c6793fc18e |
| instrumentacion\muestreador_set.py | 410759c2cb6a9750025e409f63e725312211c54e6bbde687ca1ca030cd7f0bdb |
| instrumentacion\test_instrumentacion.py | e7c650742d5c6d8887e44960d0b9cc9f32dcc7cb6538336451d16b32f06d12a5 |
| paquete-despliegue\SHA256SUMS | 560fd6549fa6d357c99054fa3a5c02ffa5a127aa72016495fd3b32d05297fcb1 |
| paquete-despliegue\adaptador_banco.py | 41eaca8aa54ed0db693864f86c6f0324fc6c45f940a9a8f1dd1821c6cd843132 |
| paquete-despliegue\adaptador_banco_rot.py | 4cedd2ce77371a4a93aee0862d01d23faada5fc1773c4eef46d7a019c88948a1 |
| paquete-despliegue\auditoria_d5.py | d1095bc5e95392255f99a2ef04d1412e75cb9e76b08a651dfedcc3d08a301519 |
| paquete-despliegue\cf_d5_bastion.sh | d7c94188a8cb5b99293ccbbb9397d8a7a41f7c8b03454faebc2980e2e56c5dad |
| paquete-despliegue\cf_d5_instrumentacion.sh | 504fd104487abd68a2a6b3c63e5f8fe420307f1bf1ca7881acf8950b869d98f4 |
| paquete-despliegue\cf_d5_sensor1.sh | c074fdd48987b06766cca0cbc594dda1da95bf151bc473bebac65ffe6aae6fbf |
| paquete-despliegue\clientes_factor1_tx.py | d86c7edc9f10e353fca11aee506bd13bf1b6c3a587e8baf55d7d9d73d8d6c307 |
| paquete-despliegue\d5-auditoria.logrotate.propuesta | c13d0d36bf308bc1e3ad203e5ad6cfe177612b11248e57c6dc1c2a83f59c3133 |
| paquete-despliegue\d5_control.py | ec22b721ff117d1ee5cbe30925dd318e8abf7788026f283bf43fda24f7fa2606 |
| paquete-despliegue\hacer_d5_episodio_banco.py | 65511cc1a313cd552d46413044402f62e21a62f3211713089ed2047408455b19 |
| paquete-despliegue\inundacion_instrumentada.sh | 7ac5335848469ed6a4facdf55a79dab82e2d7050404dc881a95d89c6793fc18e |
| paquete-despliegue\lanzador_puerta_banco.py | c2ec10b42751985cfe4749a19d6fa58289979be2ba242368c240d72742e2c438 |
| paquete-despliegue\muestreador_set.py | 410759c2cb6a9750025e409f63e725312211c54e6bbde687ca1ca030cd7f0bdb |
| paquete-despliegue\publicar_feed_v2_d5.py | 58e2a0b2b06908922f017199987f6e9b28bc8a808b174962d270832909b25451 |
| paquete-despliegue\sensor_control_d5.py | 6f36032e6f74c124c0ba9158a8cacccb34876d88938bddcbf333d56073c2efc0 |
| paquete-despliegue\test_guiones_paquete.py | 73faeb8ecc03a39cbc505956176132edf8e3032388b9c8bf73dabf27ea5a97bc |
| paquete-despliegue\transporte_bastion.py | 2dc8d7eb306880dd0e563c83ffa0c2bbb55b88aafc21fc63d7bfdc92d3ebb2b3 |
| CRITERIO-E3-SPAN-O-SALIDA.md | 5b155fff6e385f2acd8ec6daea419d079962628c2f9cb6830375fa479fb653c4 |
| CRITERIO-E3-FINAL-PARA-APROBAR.md | 40aa0702ad3fab9d0f75ac8c18bc55fbf17894a957d489283142205ca5d5508d |
| PROPUESTA-HALLAZGO-2.md | aad215778e5d98bf90926190d8202d85f2895faade0d80c547045ffcfef27502 |
| PROPUESTA-INSTRUMENTACION-VALIDACION-B.md | a38df9a5fbf77478da820133745fe0305d5aea7781c099f2b0f47c74417fe615 |
| herramientas\d5_episodio.py | 85c71124098cb7cb34d1f64f8184168c863c16843f286d82c3c519f8df7db34a |
| herramientas\compuerta_b.py | 32e1f3ef160a1d6e67bfa96096f4cda7ff2c50e26de35700d6938c233545b4f1 |
| herramientas\analizar_b.py | 611d4b166214fed9aa255ec089bf1456eb54ccbe2e1b1571bdda3690575c0dcf |
| herramientas\orquestar_b.py | babc528bcf4734b059ba03d5d0583c1810aea7023334e8a546ed1655094fe8b7 |
| paquete-despliegue-evidencia\ensayo_seco_espejo.sh | 3e2f1d5ed4a451cede920479210816a12716c282525849a54d7edec09bc1d5d6 |
| paquete-despliegue-evidencia\salida-modo-seco.txt | b97a6c0490c695cf0d09b3e277116accbcdf903202c0eb54a01104c77f0d11f5 |
| publicador original (producto-etapa3; = el del Sensor1, verificado en lectura) publicar_feed_v2.py | 5733f17d39bfa5fe667ee13aecd133ea4859834899c5f4f6ea21360ebe4002a2 |
| publicador derivado publicar_feed_v2_d5.py (= paquete-despliegue\publicar_feed_v2_d5.py) | 58e2a0b2b06908922f017199987f6e9b28bc8a808b174962d270832909b25451 |
| d5_episodio_banco.py (derivado reproducible de `herramientas\d5_episodio.py` 85c71124…) | 27b63c4167df1ec69180dc05319adb78e3af462e75a181c347eda8092e12ac34 |
Entorno de banco: imágenes `cyberflow-etapa3-banco:1` y `cyberflow-etapa3-banco-logrotate:1` (Debian 13, OpenSSH_10.0p2 Debian-7+deb13u4, systemd 257.13, logrotate 3.22.0-1, Python 3.13.5). **No se midieron** las versiones de systemd, logrotate, Python ni OpenSSH de los hosts reales.

## 8. Guiones concretos por host (carpeta `paquete-despliegue\`; seco por omisión; ensayados sobre árboles falsos y, con rutas reales, sobre un espejo local: 11 pruebas)
Cada guion: `sha256sum -c SHA256SUMS` antes de tocar nada (si algo no coincide, **no instala**), **seco por omisión** (`--aplicar` para actuar), copias de seguridad con hash, y **la evidencia se archiva, no se borra**. Ninguno hace nada con `sudo` salvo con `--con-sudo` (el `sudo` es de Mark); sin él deja el contenido en `pendiente-sudo\`.
| Host / cuenta | Guion | Qué hace (instalar) | Aceptación | Reversión |
|---|---|---|---|---|
| **Sensor1** `m4rk` | `cf_d5_sensor1.sh {instalar\|aceptar\|revertir}` | copia `sensor_control_d5.py`, `adaptador_banco*.py`, `auditoria_d5.py`, `d5_control.py` a `~/cf-b/herramientas/` (0644, el subcomando 0755); `publicar_feed_v2_d5.py` en **`~/cf-b/d5/`** (fuera de `ec78ca5`, que es de solo lectura y tiene `SHA256SUMS`; el original debe ser `5733f17d…` o no instala) y el drop-in añade `Environment=PYTHONPATH=<engine de ec78ca5>`; crea `~/feed-v2/d5/control` (0700) y `auditoria` (0750); añade **una** línea `authorized_keys` con `command="…sensor_control_d5.py … --ssh-original",restrict` y la clave dedicada (no duplica; respalda el fichero con sha); genera el drop-in de systemd **a partir del `ExecStart` original leído (multilínea, unido entero)** con el derivado, `PYTHONPATH` y las 3 opciones, y el logrotate (`su m4rk m4rk`); en seco **imprime** el contenido exacto del drop-in y del logrotate | comprobaciones: hashes = paquete, original intacto, `SHA256SUMS` de ec78ca5 sigue verificando, el derivado arranca con el **python del venv real**, modos, **una** línea con comando forzado y `restrict`, drop-in y logrotate presentes (sudo de Mark), el comando permitido responde y uno fuera de la lista se rechaza; en el Sensor1 real además unidad activa y publicador sin `--aplicar` y se anota `NRestarts` | `authorized_keys` vuelve **exactamente** al original; quita derivado, drop-in y logrotate (sudo); archiva `~/feed-v2/d5` como `d5-archivado-<ts>` con `.sha256` y el derivado como `…retirado-<ts>`; reinicio del publicador solo con `--reiniciar` |
| **Bastión** `gadmin` | `cf_d5_bastion.sh {clave\|instalar\|aceptar\|revertir}` | `clave`: par **dedicado** `~/.ssh/cyberflow-d5-sensor` (no sobrescribe) e imprime la pública; `instalar`: copia `transporte_bastion.py`, `lanzador_puerta_banco.py`, `hacer_d5_episodio_banco.py` (0755), deriva `d5_episodio_banco.py` del `d5_episodio.py` existente (que **no** se toca) y **fija** el huésped en `known_hosts_d5` desde `CF_HOSTKEY` obtenida **fuera de banda** (nunca `ssh-keyscan` a ciegas; imprime la huella para compararla) | hashes, derivado reproducible, clave 0600, `known_hosts_d5` con una clave ed25519, el lanzador arranca | archiva clave, `known_hosts_d5`, artefactos y derivado en `respaldo-d5` (retirar antes la línea del Sensor1); los originales no se tocan |
| **srv-dmz** `adminsrvdmz` | `cf_d5_instrumentacion.sh srvdmz …` | copia `muestreador_set.py`; `iniciar`/`parar` con `--aplicar` | hashes, 0755, el muestreador arranca (`--help`) | archiva la carpeta de instrumentación; los `set-lecturas.jsonl` no se borran |
| **Kali** `adminatacante` | `cf_d5_instrumentacion.sh kali …` | copia `inundacion_instrumentada.sh`; muestra la línea que Mark pondrá en la config firmada (misma duración, URL y lazos) | hashes, 0755, `bash -n` | archiva; los `intentos-*.tsv` no se borran |
| **Clientes** `adminclientes` | `cf_d5_instrumentacion.sh clientes …` | copia `clientes_factor1_tx.py`; el arranque con `--registro` lo ordena Mark | hashes, 0755, sintaxis | archiva; `clientes_lab.py` no se toca |
Artefactos exactos y hashes: `paquete-despliegue\SHA256SUMS` (copia de lo de §7). Orden de uso: Sensor1 `instalar` → bastión `clave` → Sensor1 `instalar` con `CF_PUBKEY` → bastión `instalar` → `aceptar` en ambos → (sudo de Mark: drop-in y logrotate) → comprobaciones de §9.

## 9. Comprobaciones de aceptación (cada una con criterio de pasa/falla; en este orden)
**Solo lectura:** (1) preflight (srv-dmz agente sin `--aplicar`, 0 tablas cyberflow, `ppi-brute-lab` inactivo; Sensor1 `--politica if_senal` sin `--aplicar`; clientes `target` activo; Kali sin generadores; relojes |desfase| ≤ 1 s medidos al inicio); (2) hashes instalados = §7.
**Tras instalar, sin tráfico:** (3) publicador derivado publica con **0 reinicios** (`NRestarts`, `MainPID` estables 10 min); (4) **SSH real con comando forzado**: los 9 comandos rechazables de la prueba se rechazan y los 4 permitidos funcionan, y el bastión **no** puede abrir un shell ni leer el árbol del Sensor1; (5) una solicitud real sobre estado vacío: acuse con secuencia, el mismo id en pendiente/registro/ack/auditoría; (6) corte de SSH tras recibir (matar la conexión a mitad): bloqueo, 3 invocaciones sin llamadas, reanudación manual, consulta del mismo id, **una** limpieza; (7) rotación forzada de la auditoría entre `consumido` y `publicado` → el id se reconstruye con el subcomando; (8) puerta a fin + 75 s con una decisión sintética tardía a fin + 50 s sobre estado de prueba; (9) instrumentación: una acción de cada perfil produce línea con hora; el muestreador escribe cada 2 s.
**Durante la corrida:** `NRestarts` del publicador no aumenta; ninguna puerta lanzó más de una solicitud; ninguna reanudación sin registro; toda restricción es sobre 10.10.20.30 (P1).
**Después:** `analizar_b` + `e3_v2` + `control_desde_transacciones`; copias con hash de todo lo temporal; segunda medición de relojes.

## 10. Reversión por host (sin borrar evidencia)
- **Sensor1:** retirar el drop-in y la línea de `authorized_keys`; `daemon-reload` y un reinicio del publicador al original (`publicar_feed_v2.py` `5733f17d…`, que nunca se tocó); retirar `/etc/logrotate.d/cf-d5-auditoria`; `desarmar` (logrotate.timer); **conservar** `~/feed-v2/d5/` (control, solicitudes y auditoría), archivado con sha256.
- **Bastión:** detener la puerta; archivar `puerta-bloqueo.json*`, `puertas-D5.jsonl`, `puerta-banco.jsonl`, `limpiezas\`; borrar la clave `cyberflow-d5-sensor` **solo después** de retirar su línea en el Sensor1.
- **srv-dmz:** `b_revertir_srvdmz.sh` (R0–R7, ejecutado en B2 el 10-nov); detener el muestreador.
- **Kali:** parar generadores; mover `corrida\` e `intentos-*.tsv` a un directorio con sufijo y hash; restaurar `escenarios-4c.json`.
- **Clientes:** `clientes_parar_factor1.sh` / `clientes_restaurar.sh` y volver a `clientes_factor1.py`.
- **Disparadores:** P1–P5 o X1–X3 del protocolo, o fallo de una comprobación de aceptación → reversión inmediata y aviso (como en B2, sin esperar `sudo`).

## 11. Bloqueos que realmente quedan
1. **Decisiones de Mark:** aprobar «SPAN o salida» (o «y»); Hallazgo 2 (A/B/bloqueo manual; la espera de 75 s sigue como propuesta, probada a escala 1/60 con sus límites); ruta, propietario y retención de la auditoría (§3) y la clave dedicada; despliegue y `sudo`; orden de corrida con `--aplicar` (solo Kali 10.10.20.30).
2. **Hacia el laboratorio real (no verificable en banco):** `sshd`, claves, versión de OpenSSH, `python` del venv y la ruta real de `ExecStart` del Sensor1; los guiones se ensayaron sobre árboles falsos y su primera ejecución real será la de instalación (por eso van en seco por omisión y con comprobaciones de aceptación).
3. **Huésped del Sensor1:** su clave pública debe obtenerse **fuera de banda** y comparar su huella antes de fijarla (el guion no hace `ssh-keyscan` a ciegas).
4. **Sin verificar:** ejecución diaria de logrotate; duración real de la puerta con SSH real (margen frente a los 210 s); versiones de los hosts.
5. **Riesgo residual del Hallazgo 2:** una decisión posterior a fin + 75 s bloquea la puerta (seguro; exige reanudación manual).
6. **Proceso de pruebas:** los 3 módulos que exigen root no corren en una suite sin privilegios (§2d).
7. **Evidencia faltante para E3 inundación y E4** no existe en B2: solo se obtiene con la instrumentación en una corrida nueva.
**Ya no son bloqueos:** el lanzador del bastión (§2c) y el transporte con OpenSSH real (§2b).

## 13. Revisión del paquete en los hosts reales (11-nov, 00:20–00:30Z): lecturas y modo seco (sin instalar nada)
**Alcance respetado:** solo lecturas con las mismas cuentas y vías de siempre (`gadmin` en el bastión; `m4rk`, `adminsrvdmz`, `adminatacante` y `adminclientes` por el bastión), **sin `sudo`, sin crear ni modificar ficheros en ningún host, sin tráfico, sin servicios tocados**. Salidas íntegras en `paquete-despliegue-evidencia\lecturas-hosts-reales\`.
**Incidente propio (declarado):** en la primera lectura del bastión incluí `ssh-keygen -h` creyendo que era «ayuda»; en `ssh-keygen` `-h` no es ayuda y **empezó a generar un par de claves** leyendo del mismo flujo que el guion. La salida se cortó (`head -1`) y el proceso murió. **Comprobé después, en solo lectura, que no se creó nada**: no hay ficheros nuevos en `~/.ssh` ni en `~` (el `find` por fecha solo devolvió `relay-v2/traza.jsonl`, un servicio existente) y `id_ed25519` conserva su fecha del 27-jul. Repetí la lectura sin esa orden y pasando el guion por `base64` para que ningún comando pueda consumir su entrada.

### 13.1 ¿El modo seco solo inspecciona y muestra lo previsto? Sí, con una corrección
- Todas las acciones que escriben o cambian estado van envueltas en `run`, que en seco **solo imprime `[seco] …`**; lo demás son lecturas (`sha256sum`, `stat`, `systemctl cat`, `grep`). Verificado de tres maneras: (a) revisión línea a línea; (b) 11 pruebas (`paquete-despliegue-evidencia\pruebas-guiones.txt`), una de ellas ejecuta **todos** los guiones en seco y en `aceptar` y compara una huella del árbol completo antes y después; (c) ensayo sobre un **espejo local con las rutas reales** (`/home/m4rk`, `/home/gadmin`, `/home/adminatacante`, …): huella antes = huella después (`salida-modo-seco.txt`).
- **Una excepción encontrada y corregida:** `cf_d5_bastion.sh aceptar` escribía un fichero temporal en `/tmp`; ahora compara por tubería sin escribir (`hacer_d5_episodio_banco.py … -`).
- **Por qué no se ejecutó en el host:** los guiones verifican `SHA256SUMS` contra los artefactos, así que necesitan el paquete en el host: eso **crearía `~/cf-b/paquete-despliegue/` (17 ficheros, 111,4 KB) en cada host**. Es una escritura remota y queda para la decisión de instalación. Con el paquete copiado, el modo seco en el host sigue sin escribir nada (salvo que se ejecute `aceptar`, que solo lee).

### 13.2 Resumen por host
| Host | Compatibilidad leída | Cambios exactos previstos (al instalar) | Respaldo | Reversión |
|---|---|---|---|---|
| **Sensor1** `m4rk` (10.10.60.11) | Ubuntu 24.04.2, kernel 6.8.0-53; OpenSSH 9.6p1 (banco 10.0p2); Python del **venv 3.14.4** (banco 3.13.5) y `/usr/bin/python3` 3.12.3 (lo usa el comando forzado); logrotate 3.21.0 (banco 3.22.0), **temporizador diario `logrotate.timer` habilitado y activo (último 11-nov 00:00Z, próximo 12-nov 00:00Z)**; unidad `ppi-publicar-feed-v2`: `User=m4rk`, `Group=m4rk`, `UMask=0022`, `Restart=always`, `RestartSec=2`, `ProtectSystem=no`, **sin drop-ins**, `NRestarts=18`, MainPID 1971245, ExecStart **multilínea** con `/home/m4rk/cyberflow/.venv/bin/python …/ec78ca5/scripts/engine/publicar_feed_v2.py`; publicador original `5733f17d…` ✓; **`ec78ca5` es de solo lectura y su `SHA256SUMS` (87 ficheros) verifica hoy (rc 0)**; `~/.ssh` 0700, `authorized_keys` 0600 con **2 claves** (una ya es comando forzado + `restrict`: `cf-feed-ssh.sh`); el bastión se conecta desde **10.10.10.30**; `/home/m4rk` 0750 | `~/cf-b/respaldo-d5/<ts>/`, `~/cf-b/herramientas/` (+5 ficheros), `~/cf-b/d5/publicar_feed_v2_d5.py`, `~/feed-v2/d5/control` (0700) y `auditoria` (0750); **una línea** nueva en `authorized_keys`: `from="10.10.10.30",command="/usr/bin/python3 -I /home/m4rk/cf-b/herramientas/sensor_control_d5.py --base … --ssh-original",restrict ssh-ed25519 <clave dedicada> cf-bastion-d5`; con sudo: drop-in `/etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf` (`Environment=PYTHONPATH=…/engine`, `ExecStart=` vacío y el nuevo con el derivado + 3 opciones) y `/etc/logrotate.d/cf-d5-auditoria`; **un** reinicio del publicador | `authorized_keys` copiado con sha en `~/cf-b/respaldo-d5/<ts>/` | `authorized_keys` vuelve exactamente al original; quitar drop-in y logrotate (sudo); archivar `~/feed-v2/d5` con hash; reinicio con el `ExecStart` original (un solo reinicio anotado) |
| **Bastión** `gadmin` (10.10.10.30) | Debian 13, OpenSSH 10.0p2 y Python 3.13.5 **idénticos al banco**; herramientas existentes con los mismos hashes que las copias locales (`d5_episodio.py` 85c71124…, `compuerta_b.py` 32e1f3ef…, `orquestar_b.py` babc528b…); `~/.ssh` 0700; `known_hosts` con `HashKnownHosts yes`; no existen `cyberflow-d5-sensor` ni `known_hosts_d5`; `config` con alias `sensor1`, `srvdmz`, etc. y sockets `cf-relay-*` (relé v2 existente); 8,5 GB libres | `~/cf-b/herramientas/` (+3 artefactos y `d5_episodio_banco.py` derivado); `~/.ssh/cyberflow-d5-sensor` (+`.pub`, generados allí, no se copian); `~/.ssh/known_hosts_d5` (una línea) | `~/cf-b/respaldo-d5/<ts>/` | mover clave, `known_hosts_d5`, artefactos y derivado a `respaldo-d5` (antes, quitar la línea del Sensor1) |
| **srv-dmz** `adminsrvdmz` | Ubuntu 24.04.5, Python 3.12.3; `~/cf-b/herramientas` existe; `/usr/local/sbin/cf-nft-helper` (root, 0755) existe; el muestreador usa `sudo -n` sobre ese ayudante (el `NOPASSWD` de la cuenta **no se probó**: requeriría `sudo`) | `~/cf-b/instrumentacion/muestreador_set.py` (0755); arranque/parada solo con `iniciar`/`parar --aplicar` | `~/cf-b/respaldo-d5/` | mover la carpeta; los `set-lecturas.jsonl` no se borran |
| **Kali** `adminatacante` | Kali rolling, bash 5.3.3, curl 8.17.0, Python 3.13.9; `~/cf-campana-A/escenarios/escenarios-4c.json` y `~/cf-e4-4c` existen; **`~/cf-b` no existe** (se crearía) | `~/cf-b/instrumentacion/inundacion_instrumentada.sh` (0755); el cambio de `escenarios-4c.json` lo hace Mark con la config firmada | `respaldo-d5` | mover la carpeta; restaurar `escenarios-4c.json` |
| **Clientes** `adminclientes` | Ubuntu 24.04.2, Python 3.12.3; `~/cf-e4/4c/clientes_factor1.py` `69d79937…` y `clientes_lab.py` `ae5134a7…` = los de B2; **`~/cf-b` no existe** | `~/cf-b/instrumentacion/clientes_factor1_tx.py` (0755) | `respaldo-d5` | mover; `clientes_lab.py` no se toca |

### 13.3 Discrepancias frente al banco
| # | Discrepancia | Estado |
|---|---|---|
| 1 | **El árbol `ec78ca5` es de solo lectura y tiene `SHA256SUMS`**: copiar el derivado «al lado» habría fallado y roto la verificación | **Corregido**: el derivado va a `~/cf-b/d5/`, el drop-in añade `PYTHONPATH` al `engine` (probado: sin `PYTHONPATH` falla con `No module named 'escalada'`; con él arranca) y la aceptación comprueba que `SHA256SUMS` sigue verificando |
| 2 | **El `ExecStart` real es multilínea**; el guion leía solo la primera línea | **Corregido** (se une entero; se aborta si no contiene la ruta esperada; el drop-in se imprime en seco) |
| 3 | Python del venv **3.14.4** frente a 3.13.5 del banco; `/usr/bin/python3` 3.12.3 frente a 3.13.5 | **Abierta**: no probable en banco; mitigada con la aceptación «el derivado arranca con el python del venv» (`--help`) y la primera limpieza real sobre estado vacío |
| 4 | OpenSSH 9.6p1 en el Sensor1 frente a 10.0p2; logrotate 3.21.0 frente a 3.22.0 | Sin impacto previsto (`restrict`, `from=` y `command=` existen desde 7.x; `su` en logrotate desde 3.x); se comprueba en la aceptación |
| 5 | El origen que ve el Sensor1 es **10.10.10.30** (auth.log) | **Mejora aplicada**: `from="10.10.10.30"` en la clave (el banco no lo tenía) |
| 6 | `aceptar` del bastión escribía en `/tmp` | **Corregido** |
| 7 | `sshd` del Sensor1: `X11Forwarding yes` y, por el tamaño de `50-cloud-init.conf` (27 bytes, ilegible sin root), probablemente `PasswordAuthentication yes` | **Observación** ajena al paquete: `restrict` neutraliza X11/reenvíos para la clave nueva; la configuración efectiva solo se ve con `sudo sshd -T` (§13.6) |
| 8 | Ya existe `/etc/logrotate.d/cyberflow-etapa4` (`su m4rk m4rk`, `copytruncate`) para `/home/m4rk/feed-v2/*.jsonl` | **Sin conflicto**: el patrón no entra en subdirectorios; el nuestro es otro fichero y sin `copytruncate` |
| 9 | El drop-in sube `NRestarts` de 18 a 19 al reiniciar | Esperado; se anota como línea base y no cuenta como reinicio de campaña |

### 13.4 Valores que usaría el lanzador y parámetros definitivos propuestos
- **`--espera-fin`:** el lanzador usa **15 s por omisión** (valor actual de `compuerta_b`); **propuesta: 75 s** (cierre de la ventana de 60 s + 15 s) **sigue pendiente de tu decisión**; probada a escala 1/60, límites en `PROPUESTA-HALLAZGO-2.md`. Resto de parámetros por omisión: `espera_agente` 25 s (> refresco de 20 s del publicador), `espera_feed` 60 s, sondeo 2 s, espera de la limpieza 20 s, 3 fallos de consulta, tiempo de ssh 15 s.
- **Auditoría:** `/home/m4rk/feed-v2/d5/auditoria/d5-auditoria.jsonl` (directorio 0750, ficheros 0640 tras la 1.ª rotación (el primero, creado por el publicador con `UMask=0022`, es 0644 dentro de un directorio 0750), `m4rk:m4rk`); control `/home/m4rk/feed-v2/d5/control/` (0700); `logrotate` diario (`daily`), `rotate 30`, `su m4rk m4rk`, `compress` + `delaycompress`, `nocopytruncate`, `create 0640 m4rk m4rk`, sin `dateext`; temporizador de systemd existente (próxima ejecución real 12-nov 00:00Z).
- **Clave dedicada:** ed25519, sin frase de paso, `~/.ssh/cyberflow-d5-sensor` (0600) en el bastión; en el Sensor1 una sola línea con `from="10.10.10.30",command="… --ssh-original",restrict`, comentario `cf-bastion-d5`; huésped fijado en `~/.ssh/known_hosts_d5` con `10.10.60.11 ssh-ed25519 …`.

### 13.5 Huella del huésped del Sensor1
- Clave ed25519 del huésped (pública), leída del propio Sensor1: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG+jdLmGHlDG93QX6AFMOl5KD+j5t/ETcx5cjNTbeybF root@cyberflow-sensor` → huella **`SHA256:xHCL2/TSa7S8QE+ZRIhjmjcqQcm+7n7lrw/5i2BnfSQ`** (calculada también localmente con `ssh-keygen -lf`).
- **Canal ya confiable e independiente de esta revisión:** el `known_hosts` del bastión (fijado antes de esta revisión, última modificación 6-nov) tiene para 10.10.60.11 la **misma huella ed25519** (`ssh-keygen -F 10.10.60.11 | ssh-keygen -lf -`). Coinciden.
- **Comprobada por Mark desde la consola del Sensor1: coincide (§14).** Para repetirla desde la consola del Sensor1 (canal físico/hipervisor): `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` debe mostrar exactamente la huella anterior. Si coincide, `CF_HOSTKEY` es `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG+jdLmGHlDG93QX6AFMOl5KD+j5t/ETcx5cjNTbeybF`.

### 13.6 Comandos exactos que necesitan tu `sudo` (ninguno ejecutado)
**En el Sensor1 como `m4rk`, después de copiar el paquete y ejecutar `cf_d5_sensor1.sh instalar --aplicar` (sin `--con-sudo`, que deja los ficheros en `~/cf-b/paquete-despliegue/pendiente-sudo/`):**
```
sudo install -d -m 0755 /etc/systemd/system/ppi-publicar-feed-v2.service.d
sudo install -m 0644 -o root -g root ~/cf-b/paquete-despliegue/pendiente-sudo/zz-d5-sin-reinicio.conf /etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf
sudo install -m 0644 -o root -g root ~/cf-b/paquete-despliegue/pendiente-sudo/cf-d5-auditoria /etc/logrotate.d/cf-d5-auditoria
sudo logrotate -d /etc/logrotate.d/cf-d5-auditoria        # simulación (depuración): no rota nada
sudo systemctl daemon-reload
systemctl cat ppi-publicar-feed-v2.service                # ver el ExecStart EFECTIVO antes de reiniciar
sudo systemctl restart ppi-publicar-feed-v2.service       # UN reinicio, fuera de campaña, anotado (NRestarts 18 -> 19)
```
**Solo lectura que requiere root (opcional, antes de instalar):** `sudo sshd -T | grep -E '^(authorizedkeysfile|pubkeyauthentication|passwordauthentication|allowtcpforwarding|permituserenvironment|allowusers|x11forwarding)'` y `sudo sshd -t`.
**Reversión (Sensor1):** `sudo rm -f /etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf /etc/logrotate.d/cf-d5-auditoria && sudo systemctl daemon-reload && sudo systemctl restart ppi-publicar-feed-v2.service`.
**srv-dmz, durante la corrida:** el muestreador ejecuta `sudo -n /usr/local/sbin/cf-nft-helper` (no se probó el `NOPASSWD`; si pidiera contraseña, el guion falla y se registra: es solo lectura de los sets).
Ni el bastión, ni la Kali, ni los clientes necesitan `sudo`.

### 13.7 Bloqueos encontrados
1. **Decisiones de Mark:** criterio E3 (`CRITERIO-E3-FINAL-PARA-APROBAR.md`), espera 15/75 s, ruta/retención/clave (§13.4), instalación y `sudo`, orden de corrida.
2. **Copiar el paquete a cada host** (escritura remota: `~/cf-b/paquete-despliegue/`, 17 ficheros, 111,4 KB) es el primer paso de la instalación y exige tu autorización expresa.
3. **Python 3.14.4 del venv** sin probar con el derivado (§13.3 nº 3).
4. **`NOPASSWD` de `adminsrvdmz`** para el muestreador sin comprobar.
5. **Configuración efectiva de `sshd` del Sensor1** solo visible con `sudo` (§13.6).

## 14. Preparación en los hosts (11-nov, 01:05–01:10Z): huella confirmada, huésped fijado, copia del paquete y comprobaciones — SIN instalar
**Huella confirmada por Mark desde la consola del Sensor1:** `SHA256:xHCL2/TSa7S8QE+ZRIhjmjcqQcm+7n7lrw/5i2BnfSQ`, igual a la leída por SSH y a la que el `known_hosts` del bastión ya tenía fijada de antemano. **Registrada como verificada por un canal independiente (consola).** Con ella se **fijó la identidad del Sensor1** en el bastión: `~/.ssh/known_hosts_d5` (0600, una línea `10.10.60.11 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG+jdLmGHlDG93QX6AFMOl5KD+j5t/ETcx5cjNTbeybF`); comprobado con `ssh-keygen -lf` y con una conexión de solo lectura con `StrictHostKeyChecking=yes`, `UserKnownHostsFile` apuntando a ese fichero y la clave existente: rc 0, el huésped mostró la misma huella.
**Efectos reales en los hosts (todo lo escrito; nada más):**
| Host | Creado | Cómo deshacerlo |
|---|---|---|
| Bastión `gadmin` | `~/.ssh/known_hosts_d5` (0600) y `~/cf-b/paquete-despliegue/` (17 ficheros, 111,4 KB; directorio 0750, ficheros 0644 y `*.sh` 0755) | `rm -r ~/cf-b/paquete-despliegue; rm ~/.ssh/known_hosts_d5` |
| Sensor1 `m4rk`, srv-dmz `adminsrvdmz` | `~/cf-b/paquete-despliegue/` (mismos 17 ficheros) | `rm -r ~/cf-b/paquete-despliegue` |
| Kali `adminatacante`, clientes `adminclientes` | `~/cf-b/` y `~/cf-b/paquete-despliegue/` (mismos 17 ficheros) | `rm -r ~/cf-b` (solo contiene el paquete) |
Copia por `tar` sobre SSH (extracción sin propietario ni permisos del origen, y luego `chmod`), con la comprobación `sha256sum -c SHA256SUMS`: **TODOS COINCIDEN en los 5 hosts**. No se tocó nada más: `authorized_keys`, unidades, `/etc`, `ec78ca5` y `~/feed-v2` sin cambios (comprobado antes/después).
**Comprobaciones de preparación (salidas íntegras en `paquete-despliegue-evidencia\preparacion-en-hosts\`):**
| Host | Resultado |
|---|---|
| Sensor1 | **Seco de `instalar`** imprime lo previsto (incluido el drop-in real derivado del `ExecStart` multilínea y el logrotate) y no cambia nada; **`aceptar` sin instalar**: 6 OK y 14 FALLAN esperados (lo no instalado); **siguen OK:** `ec78ca5` sin el derivado, **`SHA256SUMS` de `ec78ca5` verifica**, publicador original `5733f17d…` intacto, unidad activa y **sin `--aplicar`**; `NRestarts` 18 sin cambio, sin drop-ins, `authorized_keys` con las mismas 2 huellas, `~/feed-v2/d5` no existe. **Python:** los artefactos compilan e importan con `/usr/bin/python3` **3.12.3** y con el **venv 3.14.4**; el derivado **arranca con el python real del venv** (`--help`, con `PYTHONPATH` al engine) → **cierra la discrepancia nº 3** de §13.3 en lo que se puede probar sin ejecutarlo; el comando forzado con `/usr/bin/python3 -I` responde `desconocida` a un id inexistente y **rechaza** `cat /etc/passwd` y un origen ajeno, sin escribir nada (rutas inexistentes) |
| Bastión | seco de `clave`, `instalar` y `revertir` correctos; **el derivado de su `d5_episodio.py` real = el validado en banco** (`27b63c41…`); lanzador y `transporte_bastion` importan con Python 3.13.5; conexión de solo lectura con el huésped fijado rc 0; **no existen** `cyberflow-d5-sensor` ni los artefactos instalados |
| srv-dmz | seco correcto; el muestreador arranca (`--help`, Python 3.12.3); **el `NOPASSWD` del muestreador sigue sin probarse** (requiere `sudo`) |
| Kali | seco correcto; `bash -n` OK (bash 5.3.3); `curl`, `date +%s.%N`, `seq`, `awk`, `sort` y `mktemp` presentes; `curl -w '%{http_code} %{time_connect}'` contra un puerto local cerrado da `000` y rc 7 (**sin tráfico al laboratorio**) |
| Clientes | seco correcto; sintaxis OK (Python 3.12.3); el `clientes_lab.py` real (`ae5134a7…`, **idéntico al usado en banco**) importa y tiene `Cliente._http`, `HTTPConnection.getresponse` y los 6 perfiles |
**Antes de instalar queda por decidir/hacer (en este orden):** (1) tu decisión sobre el criterio E3, la espera (15/75 s) y la ruta/retención; (2) bastión `cf_d5_bastion.sh clave --aplicar` (genera el par dedicado) → pasar la pública al Sensor1; (3) Sensor1 `cf_d5_sensor1.sh instalar --aplicar` con `CF_PUBKEY` y `CF_FROM=10.10.10.30` (sin `--con-sudo`); (4) tus comandos de `sudo` de §13.6; (5) `aceptar` en ambos y las comprobaciones de §9. **Nada de esto se ha ejecutado.**
## 15. Pasos 2 y 3 ejecutados (11-nov, 01:12–01:20Z): clave dedicada y preparación de instalación del Sensor1 (sin `--con-sudo`, sin reinicio)
**Paso 2 — clave dedicada (bastión, `cf_d5_bastion.sh clave --aplicar`, rc 0):** `~/.ssh/cyberflow-d5-sensor` (0600) y `.pub` (0644), ed25519 sin frase, huella **`SHA256:gw4T8ep3ZrJ42EhwICNy0qbd0OcEoh82yJMqdsRwVaA`**, comentario `cf-bastion-d5`; la privada corresponde a la pública. Ninguna otra clave del bastión cambió (fechas intactas). Pública: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP63AOo0DkRKobfK1HZPJXjSNKxCDILVOow+06ULBMIF cf-bastion-d5`.
**Paso 3 — Sensor1 (`cf_d5_sensor1.sh instalar --aplicar`, con `CF_PUBKEY` y `CF_FROM=10.10.10.30`; rc 0), conexión con el huésped fijado por la huella confirmada en consola:**
| Elemento | Estado |
|---|---|
| `authorized_keys` **antes** | sha256 `108095ec3efdec5a191ca738ee7fb1a977a21ed37b8acfa7ab24d46af6503d5c`, 2 líneas (huellas `SHA256:SL4EjhSK…` y `SHA256:D3LRY5PxV…`); línea 1 `4d68d23e398faa7c…`, línea 2 `79f22a9e2db4167a…` |
| Respaldo conservado | `/home/m4rk/cf-b/respaldo-d5/20261111T011542Z/authorized_keys` (0600, 284 bytes, 2 líneas) + `authorized_keys.sha256` → **`OK`** |
| `authorized_keys` **después** | sha256 `28a8b1245122096e44d146f1b481605e440789310a90eb9ab7ca54808c35a198`, 3 líneas, 0600 `m4rk`; **las dos claves existentes están presentes y byte a byte idénticas** (hash de las 2 primeras líneas = hash del fichero anterior; hashes por línea iguales; las dos huellas iguales); la 3.ª es la nueva (`SHA256:gw4T8ep3…` = la clave dedicada) con `from="10.10.10.30",command="/usr/bin/python3 -I /home/m4rk/cf-b/herramientas/sensor_control_d5.py … --ssh-original",restrict` |
| Creado en `~/cf-b/herramientas/` | `sensor_control_d5.py` (0755), `adaptador_banco.py`, `adaptador_banco_rot.py`, `auditoria_d5.py`, `d5_control.py` (0644), hashes = paquete |
| Creado | `~/cf-b/d5/publicar_feed_v2_d5.py` (0644; dir 0750), `~/feed-v2/d5/control` (0700, vacío), `~/feed-v2/d5/auditoria` (0750, vacío), `~/feed-v2/d5` (0750) |
| `pendiente-sudo/` | `/home/m4rk/cf-b/paquete-despliegue/pendiente-sudo/zz-d5-sin-reinicio.conf` sha256 `16c2ca0d9ca8565f45a54549a2eaa2c93843a020bbeadf0a66f4943908806673` (789 bytes) y `cf-d5-auditoria` sha256 `445efe82897bc7d7ffa78a8d0560c1cf75db91bc59062a155f688c79f0997b4b` (201 bytes) |
| **No cambió** | unidad (sin drop-ins, `NRestarts` 18, MainPID 1971245), proceso sin `--control-d5`, `ec78ca5` (`SHA256SUMS` verifica), publicador original `5733f17d…`, `/etc` |
Ajuste menor aplicado: `mkdir -p` dejó `~/feed-v2/d5` y `~/cf-b/d5` en 0775; los puse en **0750** (son directorios que yo creé). Anotado para el guion (la próxima versión hará `chmod 750`).
**Prueba funcional de la clave nueva con `sshd` real (bastión → Sensor1, huésped fijado, solo lectura):** `resultado` de un id inexistente → `desconocida`; `feed --desde 0` → feed vigente y limpio; `cat /etc/passwd` y `solicitar … --origen 10.10.20.99` → **rechazadas** (rc 2); la sesión sin orden → rechazada; el reenvío remoto con `restrict` → **falla** (rc 255). No se creó ningún control ni registro.
**Aceptación tras la preparación: 18 OK y 2 FALLAN** (`paso3-sensor1-verificacion.txt`). Correspondencia con los **14 fallos anteriores** (todos eran componentes **ausentes**: «No such file or directory» o directorios inexistentes): los **12** que dependían de lo copiado por esta preparación ahora pasan (5 herramientas, derivado, `control` 0700, `auditoría` 0750, `authorized_keys`, comando permitido, comando rechazado, derivado con el python del venv); los **2** restantes son exactamente los que exigen tu `sudo`: **drop-in de systemd** y **logrotate**. No hay ningún fallo por otra causa.
**Logrotate: ¿puede la unidad real acceder a la ruta de auditoría? Sí, sin incompatibilidad.** `logrotate.service` (Ubuntu 24.04): `ProtectHome=no` (el propio fichero lo dice: «no ProtectHome for userdir logs»), `ProtectSystem=full` (solo `/usr`, `/boot` y `/etc` de solo lectura; `/home` escribible), `CapabilityBoundingSet` con `cap_dac_override`, `cap_setuid`, `cap_setgid`, `cap_chown`, sin `NoNewPrivileges` ni `RestrictSUIDSGID`; **sin perfil de AppArmor**; la ruta `/home/m4rk/feed-v2/d5/auditoria` es atravesable (`/home` 755, `m4rk` 750, `feed-v2` 750, `d5` 750); **la misma unidad rotó hoy a las 00:00Z los ficheros de `/home/m4rk/feed-v2/`** (`senales-if.jsonl.1`, `.2.gz`…); el análisis de la configuración (`logrotate -d`, como `m4rk`, sin rotar) la lee sin errores. Una precisión: el publicador (`UMask=0022`) creará el primer `d5-auditoria.jsonl` con **0644**, no 0640; no expone nada porque el directorio es 0750; `create 0640` rige para los ficheros nuevos tras cada rotación. Pendiente de la simulación con root (`logrotate -d` con sudo, en el bloque de abajo).

### Bloque para el Sensor1 (como `m4rk`; una orden por línea; rutas completas; NO incluye el reinicio)
**Fase 0 — verificar lo preparado (sin sudo):**
```
sha256sum /home/m4rk/cf-b/paquete-despliegue/pendiente-sudo/zz-d5-sin-reinicio.conf /home/m4rk/cf-b/paquete-despliegue/pendiente-sudo/cf-d5-auditoria
```
Esperado: `16c2ca0d9ca8565f45a54549a2eaa2c93843a020bbeadf0a66f4943908806673` y `445efe82897bc7d7ffa78a8d0560c1cf75db91bc59062a155f688c79f0997b4b`.
**Fase 1 — drop-in de systemd:**
```
sudo install -d -m 0755 -o root -g root /etc/systemd/system/ppi-publicar-feed-v2.service.d
sudo install -m 0644 -o root -g root /home/m4rk/cf-b/paquete-despliegue/pendiente-sudo/zz-d5-sin-reinicio.conf /etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf
sha256sum /etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf
ls -l /etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf
```
Esperado: sha256 `16c2ca0d…6673` y `-rw-r--r-- 1 root root 789`.
**Fase 2 — logrotate:**
```
sudo install -m 0644 -o root -g root /home/m4rk/cf-b/paquete-despliegue/pendiente-sudo/cf-d5-auditoria /etc/logrotate.d/cf-d5-auditoria
sha256sum /etc/logrotate.d/cf-d5-auditoria
sudo logrotate -d /etc/logrotate.d/cf-d5-auditoria
```
Esperado: sha256 `445efe82…7b4b`; en la simulación: `considering log /home/m4rk/feed-v2/d5/auditoria/d5-auditoria.jsonl`, `does not exist -- skipping`, **sin ninguna línea `error:`** (si aparece «insecure permissions» o «unknown user», detenerse y avisarme).
**Fase 3 — recargar systemd (sin reiniciar el servicio):**
```
sudo systemctl daemon-reload
systemctl show ppi-publicar-feed-v2.service -p DropInPaths -p NeedDaemonReload -p NRestarts -p MainPID
ps -o args= -p 1971245
bash /home/m4rk/cf-b/paquete-despliegue/cf_d5_sensor1.sh aceptar
```
Esperado: `DropInPaths=/etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf`, `NeedDaemonReload=no`, `NRestarts=18`, `MainPID=1971245` (**sin cambios: el proceso en marcha sigue siendo el original**); `ps` muestra el `ExecStart` original **sin** `--control-d5`; aceptación: **`resumen: 20 OK, 0 FALLAN`** y rc 0.
**Fase 4 — lecturas con root, opcionales (no cambian nada):**
```
sudo sshd -t
sudo sshd -T
```
Esperado: `sshd -t` sin salida (rc 0). De `sshd -T` me interesan: `authorizedkeysfile`, `pubkeyauthentication`, `passwordauthentication`, `allowtcpforwarding`, `permituserenvironment`, `allowusers`, `x11forwarding`.
**Deliberadamente NO incluido (siguiente autorización):** reiniciar `ppi-publicar-feed-v2.service` (sube `NRestarts` a 19 y activa el canal de control) y cualquier corrida.
**Revertir lo hecho hasta aquí:** Sensor1 (sin sudo): `bash /home/m4rk/cf-b/paquete-despliegue/cf_d5_sensor1.sh revertir --aplicar` (quita la línea `cf-bastion-d5` dejando `authorized_keys` idéntico al respaldo `/home/m4rk/cf-b/respaldo-d5/20261111T011542Z/authorized_keys`, sha `108095ec…`; archiva `~/feed-v2/d5` con hash y retira el derivado). Si ya se hicieron las fases 1–3, además con sudo: borrar `/etc/systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf` y `/etc/logrotate.d/cf-d5-auditoria` y ejecutar `daemon-reload`. Bastión: `bash /home/gadmin/cf-b/paquete-despliegue/cf_d5_bastion.sh revertir --aplicar` (mueve la clave dedicada y `known_hosts_d5` a `respaldo-d5`).

## 12. Estimación del trabajo restante desde este punto (solo lo que falta)
| Tramo | Horas | Depende de |
|---|---|---|
| Primera instalación real y comprobaciones de aceptación (Sensor1 + bastión + srv-dmz/Kali/clientes), con la clave dedicada y el huésped fijado | 1–1,5 | `sudo` y orden de Mark |
| Ajustes que salgan de esa primera ejecución real (rutas, `ExecStart`, versiones) | 0,5–1 | lo anterior |
| Corrida de 25 episodios (5,0 min por episodio; ≈ 7 min tras un DNS con reintento; sin reintentos ≈ 5 min) | 2,1–2,3 | orden de Mark |
| Reversión y verificación | 0,5 | — |
| Análisis E1–E5 con `e3_v2`, PCAP, transacciones y sets | 1–1,5 | — |
| **Total** | **≈ 5,1–6,8 h (central ≈ 6 h)**, de las cuales ≈ 3,6–4,3 h con el laboratorio activo | |
Las decisiones de Mark no cuentan como horas de trabajo. Baja respecto de la v2 (7,1–9,3 h) porque el lanzador del bastión, los guiones por host y la prueba con OpenSSH real **ya están hechos**; lo que queda es la ejecución real y su análisis. Si una decisión cambia el diseño (p. ej. otra ruta de auditoría, opción B del Hallazgo 2), se suma ≈ 1–3 h de rehacer y volver a probar.
