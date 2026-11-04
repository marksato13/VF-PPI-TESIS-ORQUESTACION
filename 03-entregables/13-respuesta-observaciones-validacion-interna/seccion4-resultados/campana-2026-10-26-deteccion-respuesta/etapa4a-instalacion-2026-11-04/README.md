# Etapa 4A: instalación de la candidata en sombra y validación técnica (2026-11-04)

> **Veredicto.** La **4A técnica queda validada en sombra**. La candidata (código **ec78ca5**, herramientas
> **f1a12d7**) está instalada en Sensor1, en el bastión y en srv-dmz. Se observó 60 min (02:19:45 → 03:19:51 UTC) sin
> reinicios, sin aplicaciones, con el ruleset de srv-dmz idéntico a la línea base y con correspondencia 1:1
> publicador ↔ agente (secuencias 27 → 206).
>
> **El panel corresponde a la cadena v2.** Está desplegado aparte, versión **a27889d**, y no forma parte de los hashes
> congelados del detector.
>
> **Antes de la 4B falta una decisión, no un arreglo:** los descartes de Suricata. Hubo 7 en la ventana. La propuesta
> de corrección está preparada y **no aplicada**. Ver §8 y [PROPUESTA-SURICATA-ANILLO.md](PROPUESTA-SURICATA-ANILLO.md).
>
> **No se avanzó a la 4B.** No hubo ataques, no se activaron restricciones, no se eligió α, no se reentrenó y no se
> tocó el Word ni la evidencia histórica.

Petición: la de Mark del 04-nov (fases 1 a 5), tras la P0 del mismo día (01:38 UTC). Base:
[`../etapa4-reconciliacion-2026-11-03/`](../etapa4-reconciliacion-2026-11-03/README.md).

## 1. Referencias confirmadas

| Qué | Referencia | Dónde |
|---|---|---|
| Producto (base de recuperación) | `recuperacion/etapa4a-20261103` @ **b2f29944a58ec73b2954097b52804eede757ac0d** | repo del producto |
| Candidata de investigación | **3a9f26b** (`candidato/etapa3-20261102`) | idem |
| Código del detector instalado | **ec78ca5** (motor, publicador v2, vía rápida, agente v2, `salud_captura.py`) | Sensor1 `~/cyberflow-e4/ec78ca5` (SHA256SUMS verificado) |
| Documentación previa | **bd5c475** (P0) | este repo, `main` |
| **Herramientas de instalación (nuevo)** | rama **`recuperacion/etapa4a-instalacion-20261104`** @ **f1a12d7** (sobre b2f2994) | GitHub, **no** fusionada en main |
| **Panel (nuevo, aparte)** | rama **`panel/cadena-v2-20261104`** @ **a27889d** (sobre ca66db5) | GitHub, **no** fusionada en main |

Repo del producto: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos>
— ramas [`recuperacion/etapa4a-instalacion-20261104`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/recuperacion/etapa4a-instalacion-20261104)
y [`panel/cadena-v2-20261104`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/panel/cadena-v2-20261104).

El modelo (`if_limpio_2026_10`), el scaler, las 28 variables y el umbral **−0,5693969936322356** no cambiaron. El
`motor_startup` del 04-nov 02:11:07 UTC lo registra con `disparo=eventos` y el manifiesto `limpio-2026-10`. Se
mantiene `if_senal`. No hay reglas de demo, ni ICMP, ni DC1, ni límite DNS, ni `--aplicar`, ni `--enforce`.

## 2. Qué se hizo, en orden (UTC, 04-nov)

| Hora | Host | Paso | Resultado | Evidencia |
|---|---|---|---|---|
| 01:38 | srv-dmz | P0 (Mark): v1 parado, tabla `inet cyberflow` volcada y retirada | hecha | `../etapa4-reconciliacion-2026-11-03/evidencia/laboratorio/p0-srvdmz-2026-11-04.md` |
| 01:4x | los 3 | Lecturas previas: versiones, hashes, servicios, v1 apagado | OK | `evidencia/00-lecturas-previas/` |
| 01:56 | bastión | Respaldo `bastion-20261104T015600Z` | verifica | `evidencia/01-respaldos/` |
| 01:57 | srv-dmz | Respaldo base `srvdmz-20261104T015754Z` (ruleset vacío con `rc=0 bytes=0`) | verifica | idem |
| 02:03 | Sensor1 | Respaldo `sensor1-20261104T020318Z`: el manifiesto no verificaba (defecto D2) y la instalación **paró antes de tocar nada** | conservado como evidencia | idem |
| 02:10 | Sensor1 | Respaldo `sensor1-20261104T021028Z` + instalación fases 0–5 (Mark, sudo) | OK | `evidencia/02-instalacion/` |
| 02:11:07 | Sensor1 | Motor ec78ca5 `--disparo eventos` arrancado, sin `--enforce`; captura `-G 5` | OK | `evidencia/03-verificacion/out_verif_inicio.txt` |
| 02:15 y 02:18 | srv-dmz | Dos paradas falsas del instalador (D3, D4). Cada vez se revirtió la fase 1 parcial con `revertir_srvdmz.sh` y la traza se copió aparte | REVERSIÓN OK ×2 | `evidencia/02-instalacion/out_instalar*.txt` |
| 02:18:44 | srv-dmz | Instalación del agente v2 en sombra (fases 0–2) | OK | `out_instalar3.txt` |
| 02:18 | Sensor1 | Llave del relé v2 con comando forzado `servir` | OK | idem |
| 02:18:51 | bastión | Relé `ppi-relay-eventos`; primera entrega (secuencia 24) en 0,381 s; relé v1 intacto | OK | idem |
| 02:19 | los 3 | Verificación inicial: Sensor1 OK, bastión OK, srv-dmz sombra demostrada (1 FALLO falso, D5) | OK | `out_verif_inicio.txt` |
| 02:19:45–03:19:51 | Sensor1 | **Observación de 60 min** (muestreador cada 10 s) | C1 (solo Suricata) | `evidencia/04-observacion-60min/` |
| 03:12–03:25 | Sensor1 | Diagnóstico de los descartes de Suricata | §8 | `evidencia/05-suricata/` |
| 03:22 | bastión, srv-dmz | Verificación final | OK | `evidencia/03-verificacion/out_verif_final.txt` |
| 03:31:57 | Sensor1 | Panel e0dc71d (respaldo `panel-20261104T033157Z`) | activo | `evidencia/06-panel/` |
| 03:41:31 | Sensor1 | Panel **a27889d** (respaldo `panel-20261104T034131Z`) | activo, verificado | idem |

## 3. Respaldos (todos verificados con su SHA256SUMS antes de modificar)

| Host | Respaldo | Estado |
|---|---|---|
| bastión | `/home/gadmin/respaldos-etapa4/bastion-20261104T015600Z` | 0 fallos (hecho con el script anterior a 785377b, pero verifica) |
| srv-dmz | `/home/adminsrvdmz/respaldos-etapa4/srvdmz-20261104T015754Z` | 0 fallos, **línea base de la reversión**, `ruleset.lectura: rc=0 bytes=0` |
| srv-dmz | `…/srvdmz-20261104T015601Z` | primer intento (ruleset vacío sin constancia de lectura); conservado |
| srv-dmz | `…/srvdmz-evidencia-20261104T021521Z`, `…T021844Z` | trazas del agente de las dos fases 1 revertidas |
| Sensor1 | `/home/m4rk/respaldos-etapa4/sensor1-20261104T021028Z` | 0 fallos, **línea base de la reversión** |
| Sensor1 | `…/sensor1-20261104T020318Z` | 2 fallos esperados (D2): el manifiesto se escribía antes de la línea final; conservado |
| Sensor1 | `…/panel-20261104T033157Z` | panel ca66db5 (`a5186d2e…`) + unidad; 0 fallos |
| Sensor1 | `…/panel-20261104T034131Z` | panel e0dc71d + `cadena_v2.py`; 0 fallos |
| Sensor1 | `/home/m4rk/respaldo-cyberflow-v1-20261104T0138Z.nft` | volcado de la tabla de la demo (P0), sha `4bbb5783…`; **no se recarga en ninguna reversión** |

En el repositorio solo se guardan los **manifiestos** (`evidencia/01-respaldos/*-respaldos-manifiestos.txt`), nunca el
contenido de los respaldos (unidades, sudoers y llaves). No se borró ningún respaldo ni ninguna evidencia.

**Permiso de lectura del journal (B3):** no hizo falta tocar sudoers. `m4rk` pertenece al grupo `adm` y lee el journal
sin sudo; la regla NOPASSWD existente exige `journalctl --no-pager …` como primer argumento. La lectura se comprobó
de verdad: los 244 registros SIGUSR1 de la ventana se leyeron. Una lectura fallida nunca cuenta como cero descartes,
porque `salud_captura.py` la marca como C3.

## 4. Versiones y hashes instalados

| Host | Componente | Versión | Comprobación |
|---|---|---|---|
| Sensor1 | motor, publicador v2, vía rápida | ec78ca5 en `~/cyberflow-e4/ec78ca5` | «código candidato sin cambios (SHA256SUMS)» OK al inicio y al final |
| Sensor1 | unidades | drop-ins `etapa4.conf` de motor y captura, `ppi-publicar-feed-v2`, `ppi-via-rapida@ens37`, `cf-tcpdump-estadisticas.timer` | `verificar_sensor1.sh` OK |
| Sensor1 | código base `~/cyberflow` (24f8a80, el de la reversión) | intacto **salvo** `scripts/engine/dashboard.py` (el panel, §7) y `cadena_v2.py` (nuevo) | `out_codigo_dif.txt`: única diferencia `dashboard.py` |
| Sensor1 | **panel** | a27889d: `dashboard.py` `16e7f430…db274`, `cadena_v2.py` `8dbaa377…24869` | versión registrada **aparte** de los hashes del detector |
| srv-dmz | agente v2 | `/opt/cyberflow/agente-v2/agente_enforce_v2.py --perfil dmz` (sin `--aplicar`) | `estado_sombra.py`: `con_aplicar=0` |
| bastión | relé v2 | `ppi-relay-eventos` (solo destino srv-dmz) | `verificar_bastion.sh` OK |

## 5. Validación en sombra

Verificación final (03:19–03:22): Sensor1 OK, salvo dos FALLOS falsos del verificador que se explican abajo; bastión
OK; srv-dmz OK con el verificador corregido.

- **Servicios y argumentos.** `ppi-motor`, `ppi-motor-capture`, `ppi-via-rapida@ens37`, `ppi-publicar-feed-v2`,
  `cf-tcpdump-estadisticas.timer` y `suricata` activos, con **NRestarts 0** en todos. El motor corre ec78ca5 con
  `--disparo eventos` y sin `--enforce`. La captura usa `-G 5`.
- **Nada aplica.**
  - No hay ningún proceso con `--enforce` o `--aplicar` en Sensor1.
  - En srv-dmz: `estado=sombra alcance=completo agentes=1 con_aplicar=0 tablas_cyberflow=0 eventos_aplicacion=0`.
  - v1 sigue `disabled`/`inactive` y `nft list tables` sale vacío.
  - El ruleset coincide con la línea base (sha `e3b0c442…`, vacío = vacío).
- **Decisiones y trazas.**
  - El motor registró 3 867 decisiones en la ventana (y 12 `pendiente_cancelada`).
  - 0 `decision_id` duplicados y 0 líneas no JSON.
  - Todas las decisiones llevan `decision_if` y `auth_failure`, y también `http_vista` y `dns_vista`.
  - 106 ALERT del IF, que coinciden 1:1 con las 106 señales de `senales-if.jsonl`.
- **Publicador ↔ relé ↔ agente.**
  - El publicador hizo 180 publicaciones, secuencia monótona 27 → 206, política `if_senal`, **0 medidas nuevas**,
    0 rechazadas y 0 señales rápidas.
  - El relé hizo 192 entregas: traído → entregado p50 0,062 s, máximo 0,381 s, 0 errores y 0 parejas inconsistentes.
  - El agente registró **180 recepciones aceptadas con las mismas secuencias 27 → 206** y 0 eventos de aplicación.
- **FALLOS falsos del verificador encontrados al cerrar.** No cambian el veredicto. Se corrigieron en la rama de
  herramientas y se comprobaron en vivo:
  - D5 (srv-dmz): `stat` sin sudo sobre un directorio 2750 → c1bd845.
  - D7 (Sensor1): `motor_startup` buscado solo en las últimas 2000 líneas → f1a12d7. Ya da OK.
  - Tras el despliegue del panel, «código anterior ~/cyberflow intacto» marca `dashboard.py`. Es esperado: el panel
    es la única diferencia (§4).

**No se cumplió ningún criterio de parada**: ni aplicación, ni tabla, ni agente con `--aplicar`, ni reinicios, ni
fallo de captura. No hizo falta revertir.

## 6. Observación técnica de 60 minutos

Ventana **02:19:45 → 03:19:51 UTC** (3 606 s): 358 muestras cada 10 s, hueco máximo 10,12 s, 357 incrementos sin
reinicios. Datos crudos en `evidencia/04-observacion-60min/sensor1-cf-e4-4a/`.

| Medida | Resultado |
|---|---|
| Ciclos del motor | 719, todos `pcap_cerrado`; duración p50 0,39 s, p95 0,59 s, máx 0,90 s; separación máxima entre ciclos 6,27 s |
| Ventanas pendientes | p50 52, p95 60, máx 68 (estable; sin crecimiento) |
| Retraso pcap → decisión | p95 1,36 s, máx 1,62 s (criterio R2: ≤ 25 s) |
| Antigüedad del último ciclo | p95 4,4 s, máx 5,6 s |
| Vía rápida | 358/358 muestras OK, antigüedad máx 0,013 s; 0 señales |
| Anillo | 358/358 OK; salto entre ficheros dentro de 5 + 2 s |
| tcpdump del anillo | 122 lecturas SIGUSR1 de un mismo PID (1413865) que acotan la ventana; **0 descartados por el kernel** |
| tcpdump de la vía rápida | 122 lecturas (PID 1413924); **0 descartados** |
| Suricata | **7 descartes de 937 757 paquetes** (un solo intervalo, 03:05:47) |
| Memoria | motor 243 MB (RSS 275 MB), captura 56 MB, vía 26 MB, publicador 16 MB, Suricata 187 MB, panel 27 MB; host 1,1/7,9 GB |
| Carga | load 0,1–0,9 en 4 vCPU; /home 13 GB libres |
| **Clase del periodo** | **C1** para cada tcpdump: el único motivo son los descartes de Suricata |

**Intensidad de los perfiles** (tráfico real disponible; no se generó tráfico):
- ens37 recibió p50 212 pps, p95 483 y máximo 737.
- Peticiones HTTP a srv-dmz en la hora, por cliente: .24 338, .22 318, .21 210, .23 104, .26 102 y .25 36 (1 108
  en total).
- Volumen de descargas: .22 5,9 MB, .23 5,0 MB y .26 1,4 MB.
- DNS de los clientes hacia DC1, y DNS de 10.10.60.12 hacia 8.8.8.8/1.1.1.1.
- El SSH de administración desde el bastión (las propias lecturas de esta instalación) fue el mayor volumen en bytes.

**Señales del IF sobre tráfico legítimo.** En la ventana hubo 106, todas sin medida, porque `if_senal` no publica el
IF solo y α no está elegido:

| IP | Señales |
|---|---|
| 10.10.10.20 (DC1) | 53 |
| 10.10.20.24 | 33 |
| 10.10.50.51 | 6 |
| 10.10.20.22 | 5 |
| 10.10.50.52 | 4 |
| 10.10.20.21 | 2 |
| 10.10.10.21 | 2 |
| 10.10.40.10 | 1 |

Es un dato para la 4B/4C, no una acción.

**Cómo se clasificó, y por qué hubo que repetirlo.** No es un fallo de la captura; es el procedimiento correcto para
la 4C.
1. Si el inicio del periodo es la hora del fichero de inicio, el resultado es «insuficiente». Hay que usar la hora
   de la primera muestra, porque `t` está redondeado a ms.
2. El journal se exporta con al menos 32 s de margen a cada lado; si no, faltan las lecturas SIGUSR1 que acotan el
   periodo.
3. **Cada tcpdump se clasifica por separado.** Si se pasan los dos `--tcpdump-log` a la vez, `clasificar` ve dos PID y
   da C3.

Las salidas de los cuatro intentos se conservan: `out_cierre_obs*.txt` y `clasificacion*.json`.

**Observación menor.** `pcaps_ilegibles: 1` corresponde al primer fichero del anillo tras el arranque de las 02:11:07
(`live-20261104021107.pcap`, `PermissionError`; ya rotado). Se perdieron 5 s de pcap al arrancar la captura. Queda
como pendiente para la 4B.

## 7. Panel alineado con la cadena v2

**Qué cambia** (rama `panel/cadena-v2-20261104`, commits **e0dc71d** y **a27889d** sobre ca66db5):
- Se añade un módulo nuevo de solo lectura, `scripts/engine/cadena_v2.py`. Indexa por `decision_id` tres fuentes:
  `senales-if.jsonl`, `traza.jsonl` (campo `nuevos`) y `feed.json` del publicador v2.
- Con `~/feed-v2/traza.jsonl` presente, el panel ya **no deduce** la acción con la política v1. La acción es **solo la
  medida que publicó el publicador v2**.
- Cada decisión muestra los 7 pasos de la cadena, cada uno con su fuente:

| Paso | Valores posibles | Fuente |
|---|---|---|
| Señal IF | señal / sin señal / sin puntuar / desconocido | `senales-if.jsonl` |
| Regla heurística | la regla que conste | registro del motor |
| Decisión del motor | la que conste | registro del motor |
| Medida | nueva, renovada, escalada o mantenida (publicadas); rechazada; sin punto de aplicación; no publicada; desconocido | traza del publicador |
| Agente | desconocido (el sensor no tiene canal con la traza del agente v2) | — |
| Aplicación | no ejecutada (modo sombra) | modo declarado |
| Efecto | sin evidencia | — |

- En sombra, las medidas son **propuestas** y su aplicación es «no ejecutada». Si una fuente falta, o la traza leída
  no cubre la decisión, el estado es **desconocido**; el panel **nunca** vuelve a la política v1.
- Los acuses del agente v1 se muestran como **evidencia histórica de aplicación (v1)**, no como estado actual.
- Las medidas vigentes salen solo del feed v2.
- «Preparar demo» queda deshabilitado (botón oculto; el POST devuelve 409 sin escribir nada).
- Se conservan las mejoras visuales de la demo: G1–G3, alertas activas y escenario.
- No se tocaron reglas ni motor. `--sin-cadena-v2` conserva el panel de la demo para presentaciones históricas.

**Correspondencia panel ↔ trazas con datos reales** (03:41, última hora, 3 915 decisiones; `out_correspondencia2.txt`):

| | Panel anterior (ca66db5, política v1) | Panel desplegado (a27889d) | Trazas reales |
|---|---|---|---|
| Acciones | **54 LIMIT** (IF sobre legítimos) | **0** | 0 medidas en la traza, 0 entradas en el feed v2 |
| Señales IF | — | 108 decisiones «señal» | 108 en `senales-if.jsonl`, **mismo conjunto de ids** |
| Medida | — | 3 904 «no publicada», 11 «desconocido» (posteriores a la última publicación) | 272 publicaciones, 0 nuevos |
| Vigentes | reconstruidas con la escalera v1 | vacías, desde el feed v2 | feed v2 sin entradas |

Anotar las 3 915 decisiones cuesta 0,019 s.

**Interfaz de solo lectura, comprobada en vivo desde el bastión** (el acceso al panel está limitado a 10.10.10.30 por
la tabla `inet cyberflow_panel`, ya existente):
- `GET /api/status` sin sesión → 401;
- `POST /api/demo/preparar` → **409** «panel de solo lectura»;
- `~/feed/peticiones/preparar.json` sigue siendo el del 3-nov a las 17:02;
- `journalctl`: «cadena v2 desde /home/m4rk/feed-v2 (modo sombra); «Preparar demo» deshabilitado».

**Pruebas** (§9): 17 casos nuevos, entre ellos los exigidos:
- solo IF;
- regla con medida;
- sombra y modo activo;
- fuente ausente;
- fuera de cobertura;
- evidencia histórica de aplicación;
- servidor real con 409 y sin escritura;
- JS ejecutado con Node.

**Pendiente del panel.** No vi la interfaz autenticada, porque no uso credenciales. Lo que está verificado es la API
con datos reales y la lógica del navegador con Node. Mark debería abrirla una vez desde el bastión y confirmar la
franja «Cadena v2».

## 8. Descartes de Suricata: diagnóstico

**Hechos:**
- Acumulado desde el arranque de Suricata (30-oct 19:55): 82 038 descartes de 135 M paquetes (0,061 %).
- Por día (eve rotado):
  - 03-nov: 58 423 descartes en 155 intervalos, con picos de 07:33 a 09:13 (horas de campaña y demo);
  - 02-nov: 13 596 en 79 intervalos;
  - 01-nov: 9 650 en 47 intervalos;
  - 31-oct y 28-oct: **0**.
- Hoy:
  - 01:42:11: 164 de 3 405 paquetes en 8 s;
  - 02:08:27: 198 de 4 522;
  - 03:05:47: 7 de 5 766.

**Correlación del intervalo de la ventana (03:05:39–03:05:47):**
- **Carga:** ráfaga de recepción de 678 pps frente a una mediana de 210. Coincide con dos descargas HTTP grandes
  hacia srv-dmz (10.10.20.26: 2 469 paquetes; 10.10.20.23: 1 203).
- **Rotación:** no la hubo (eve rota a las 00:00).
- **CPU:** load 0,4 y los hilos de Suricata con 0,1–0,3 % de CPU.
- **Disco:** 63 % usado.
- **Reinicios:** ninguno.

**Lo que se descarta:**
- La NIC no pierde: `rx_missed 0`, y los dos tcpdump sobre la misma interfaz no descartaron nada.
- GRO y LRO están **apagados**.
- El `rx_dropped` de ens37 crece unas 14/s de forma constante (50 519 en la hora). No coincide con los descartes y no
  afecta a tcpdump ni a Suricata, así que no es pérdida de captura. Probablemente son tramas sin manejador de
  protocolo en el SPAN.

**Configuración real:**
- Suricata 7.0.3, af-packet en ens37 con `cluster_type: cluster_flow`.
- `threads` comentado (= auto, 4 workers).
- `ring-size`, `block-size`, `tpacket-v3` y `max-pending-packets` **sin fijar** (valores por defecto).
- vmxnet3 con el anillo RX en 1024 de un máximo de 4096.

**Hipótesis (no demostrada):** con `cluster_flow`, una descarga grande cae entera en un solo worker y una ráfaga corta
desborda el anillo por defecto de ese hilo, aunque la media de pps sea baja.

**Propuesta:** fijar `ring-size` del af-packet de ens37, con prueba, criterio y reversión, **preparada y no ejecutada**:
[PROPUESTA-SURICATA-ANILLO.md](PROPUESTA-SURICATA-ANILLO.md). Cambiar el YAML exige sudo (Mark) y reiniciar Suricata.

**Relación con I5:** el último descarte fue a las 03:05:47, así que la condición I5 (0 descartes en los 30 min
previos) no se habría cumplido para empezar la 4C antes de las 03:35:47. Con los perfiles actuales de descarga, I5
puede fallar en cualquier momento. Por la corrección del 04-nov (PROCEDIMIENTO §5.2), si I5 falla la batería no
empieza: no se flexibiliza.

## 9. Pruebas

Ejecutadas en Linux (Debian trixie, Python 3.13, Node 20, OpenSSL 3.5). Salidas completas en `evidencia/07-pruebas/`.

| Conjunto | Ejecutadas | Pasan | Fallan | Saltadas (motivo) |
|---|---|---|---|---|
| Panel, rama a27889d: 13 ficheros del panel + `test_panel_cadena_v2.py` | 134 | **127** | 0 | 7: política de la demo A+C (`conftest.py`), mientras rija el motor de las campañas; previas |
| Panel, base ca66db5 (control) | 117 | 110 | 0 | 7 (las mismas) |
| Bancos de herramientas f1a12d7: comprobaciones 12/12, rechazo del helper 4/4, precondición v1 10/10, respaldos 6/6, estado de sombra S1–S10, unidades e importaciones U1–U3, estadísticas de tcpdump E1–E3 | 7 bancos | **7** | 0 | 0 |

**Notas:**
- **JS:** `test_served_script_parses_with_node` y `JsDelPanel` (sintaxis y comportamiento) se **ejecutaron** con Node.
  No se saltaron.
- **Windows:** en el portátil, las 12 pruebas que lanzan subprocesos (`test_panel_auth_e2e` y una de
  `gui_contract`) fallan con `WinError 6`, porque la consola de esta sesión no da un stdin válido a los procesos hijo.
  Pasa igual en ca66db5, así que no es un fallo del código. Por eso la batería vale en Linux.
- **Intermitente:** `test_served_demo_denies_outside_whitelist…` falló **una vez** en la base ca66db5 y pasó 3/3 en
  las repeticiones; en la rama no falló. Queda anotado como intermitente de la base.
- **Montaje del banco:** la primera ejecución del banco de unidades dio FALLO en U3 porque no monté el árbol 24f8a80
  en `/viejo`. Con el montaje que pide la cabecera, pasa todo (las dos salidas están en `bancos-herramientas.txt`).

## 10. Defectos de las herramientas encontrados en vivo

Todos están en la rama `recuperacion/etapa4a-instalacion-20261104`, con banco o comprobación en vivo, y ninguno tocó
el código del detector.

| # | Defecto | Efecto | Commit |
|---|---|---|---|
| D1 | El respaldo de srv-dmz no distinguía «ruleset vacío» de «lectura fallida» | el instalador habría parado con el ruleset vacío tras la P0 | 47502ca |
| D2 | Los respaldos escribían la línea final después del manifiesto | `RESPALDO.txt: FAILED`; la instalación del Sensor1 paró a las 02:03 | 785377b |
| D3 | La comprobación del rechazo del helper con `pipefail` (el helper sale con rc=1 al rechazar) | parada falsa en srv-dmz a las 02:15; fase 1 revertida | dedb048 |
| D4 | El `grep --aplicar` veía el comentario «SIN --aplicar» de la unidad, y había dos `pipefail` latentes (llave del relé y bastión) | parada falsa a las 02:18; fase 1 revertida | 26944fa |
| D5 | `verificar_srvdmz.sh`: `stat` sin sudo sobre `/var/lib/cyberflow/feed` (2750) | FALLO falso «feed v2 < 60 s» | c1bd845 |
| D6 | `verificar_srvdmz.sh` contaba como rechazo el `motivo` vacío de cada recepción aceptada | dato engañoso | dfa7065 |
| D7 | `verificar_sensor1.sh` buscaba `motor_startup` solo en las últimas 2000 líneas | FALLO falso tras unas 2000 decisiones | f1a12d7 |

## 11. Reversión

Procedimiento completo: [REVERSION-4A.md](REVERSION-4A.md).
- La reversión del agente de srv-dmz ya se ejecutó dos veces durante la instalación (fases 1 parciales) y funcionó.
- **Ninguna reversión reactiva la demo:** la línea base de srv-dmz se tomó después de la P0, así que el agente v1
  sigue apagado, y el volcado de la tabla de la demo no se recarga.
- El panel se revierte por separado, con su propio respaldo.

## 12. Estado para las fases siguientes

**Aptitud para la 4B: falta una decisión, no un arreglo.**
- La instalación en sombra es estable y la cadena v2 es trazable de punta a punta.
- Antes de empezar la 4B hay que resolver:
  1. **Suricata (B8/I5).** Decidir si se ensaya la propuesta del anillo (sudo, reinicio de Suricata, 60 min de
     medida). La otra opción es aceptar que, con los perfiles de descarga actuales, I5 puede impedir el arranque de la
     4C en cualquier momento. Sin corrección, las ventanas con descartes no son C0 y quedan fuera de la población
     principal.
  2. **Cadena v1 residual.**
     - `ppi-publicar-feed.timer` (v1) sigue activo en Sensor1 y publica cada 10 s un feed v1 con LIMIT para el cliente
       legítimo.
     - El relé v1 del bastión lo entrega a srv-dmz.
     - Hoy no aplica nada, porque el agente v1 está deshabilitado. Si alguien reactivara ese agente, aplicaría.
     - Decidir si se paran el publicador v1 y el relé v1 (sudo). Ni la P0 ni la 4A los tocaron, porque no estaban en
       su alcance.
  3. **Agente v2 sin canal hacia el sensor.** El panel muestra «agente: desconocido». Para la 4B, o se verifica en el
     host (como se hizo aquí), o se añade un canal de solo lectura de la traza del agente.
  4. **α** sigue sin elegirse. `if_senal` no publica el IF solo. Es una decisión metodológica de la 4B y no se tomó
     aquí.

**Pendientes técnicos (no bloquean la 4B):**
- el pcap ilegible al arrancar la captura (§6);
- el procedimiento de `clasificar` (por tcpdump y con margen de 32 s), que hay que escribir en el guion de la 4C o
  incorporar a la herramienta;
- el `rx_dropped` de ens37;
- que Mark vea el panel autenticado;
- `desplegar_panel.py` borra los `.bak` más antiguos que el quinto: no usarlo en la 4B sin quitar ese borrado.

**4C:** sin cambios en los criterios congelados.
- **Antes de empezar:** se exige I5 (0 descartes en los 30 min previos). Si I5 falla, no se empieza.
- **Durante la ejecución:** rigen los criterios congelados de pausa, cancelación y clasificación.
- **Población principal:** solo C0.

## 13. Contenido de esta carpeta

```
README.md                      este documento
PROPUESTA-SURICATA-ANILLO.md   corrección preparada para los descartes de Suricata (NO aplicada)
REVERSION-4A.md                reversión por host y del panel
evidencia/
  00-lecturas-previas/         versiones, hashes, servicios y estado de v1 antes de instalar
  01-respaldos/                manifiestos de los respaldos de los 3 hosts (sin su contenido) y b_recoger.sh
  02-instalacion/              salidas de distribución, respaldos, instalaciones y reversiones parciales
  03-verificacion/             verificaciones inicial y final, verificador corregido y diferencia de ~/cyberflow
  04-observacion-60min/        muestras, incrementos, journals, clasificaciones (sensor1-cf-e4-4a/) y sus scripts
  05-suricata/                 lecturas y correlaciones de los descartes, con sus scripts
  06-panel/                    despliegues, acceso desde el bastión, correspondencia con las trazas y scripts
  07-pruebas/                  salidas completas de los bancos de herramientas y de la batería del panel
MANIFIESTO.sha256              huellas de todo lo anterior
```
