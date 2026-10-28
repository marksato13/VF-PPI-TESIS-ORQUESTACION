# Preparación tras el preflight bloqueado (2026-10-28)

Resuelve los pendientes del preflight `e6a676a` («Preflight bloqueado»). Es **verificación de preparación**, no
resultados de la campaña A: no se ha ejecutado ningún ataque, ni el generador en modo autorizado, ni pruebas de
respuesta activa. El preflight anterior (`preflight-2026-10-28/`) se conserva sin cambios.

Horas en UTC (Perú = UTC−5). Sondas en `sondas/`, salidas crudas en `salidas/out_<sonda>.txt`, ficheros traídos del
sensor en `sensor/`, herramientas de diagnóstico en `herramientas/`. Sumas en `SHA256SUMS.txt`.

## 1. Modo sombra (antes de cualquier tráfico de prueba)

| Hora | Paso | Evidencia |
|---|---|---|
| 07:27:31 | Estado previo del sensor: unidades, argv, sha256 de la implementación, `feed.json` (c0ca50a4), `estado.json` (73310d14), nft | `sensor/estado-previo-072731/`, `out_p20` |
| 07:29:20 | Copias a srv-dmz y Kali con hash verificado; feed/firma/escalada **copiados del sensor** a `~/cf-campana/feed-sensor-20261028-072920/` (no se consulta una ruta del sensor desde srv-dmz) | `out_p21`, `salidas/copias-HASHES.txt` |
| — | El motor **no** aplica restricciones: argv sin `--enforce` (antes y después del reinicio) | `out_p20`, `out_p46` |
| 07:29:23 | **1.er intento: falla de forma segura.** `systemctl mask` rechaza la unidad (`/etc/systemd/system/ppi-enforce-agent.service` ya existe); además, con `pipefail`, un `is-active` inactivo (rc 3) abortaría el paso 1 | `out_p22` |
| — | Corrección de `scripts/modo_sombra.sh` (sha bc2742f8…; anterior a7d35295…): lectura del estado tolerante al código de salida (vacío = error), **timer deshabilitado** además de parado, enmascarar solo si se puede, `mecanismo` registrado, verificación ampliada | `tests/test_sombra.sh` 18/18 (`out_harness_script_corregido.txt`); con el script anterior 15/18 (`out_harness_con_script_anterior.txt`) |
| 07:33:39 | Timer devuelto a su estado original (active/enabled) para respaldar el estado real | `out_p23` |
| 07:33:40 | **Sombra activada** con el script corregido (rc 0). Respaldo `/opt/cf-sombra-estado/20261028-073340` (= `ultimo`): timer active/enabled, servicio static, `mecanismo=timer-deshabilitado`, escalada 73310d14, nft-antes c104c485 | `out_p23` |
| 07:33:41 · 08:06:10 · 09:06:48 | Verificación independiente: timer inactive/disabled, servicio inactive/static, `cyberflow_bloqueados` y `cyberflow_limitados` con **consulta rc 0 y sin elementos**, 0 ejecuciones del agente desde 07:33:42 | `out_p23`, `out_p39`, `out_p47` |

**Propuestas frente a restricciones aplicadas.** El publicador sigue escribiendo el feed: 559 ejecuciones desde la
sombra hasta 09:06:55, con hasta 6 entradas LIMIT y ningún BLOCK. A las 09:06:50 propone LIMIT para 10.10.20.21,
.22, .24 y .26, todos perfiles legítimos, por alertas del modelo (`out_p49`). Son **propuestas no aplicadas**: el
agente está parado y los sets están vacíos.

## 2. Diagnóstico de las 241/2 791 ventanas

**Sobre el archivo del preflight** (ventanas 06:46–07:04, `diag_ventanas.py` y `emular_ciclos.py`; `out_p27`–`out_p29`):

- **Entidad, límites y definición, sin diferencias.** 752 claves vivas y 0 duplicadas. El recálculo completo
  con el código del motor y el lote (`acumular_v3`) coinciden en `packet_count_10s` en 739/739.
- **VLAN, sin efecto.** El 95,7 % de las tramas son 802.1Q, y el motor las decodifica igual que el lote
  (`parse_con_contexto`, 0x8100/0x88A8).
- **Fuente disponible en el instante de la decisión.** Se emuló el motor desplegado ciclo a ciclo: solo ficheros
  **cerrados**, búfer de 230 s y EVE hasta el inicio del ciclo. Reproduce lo registrado en vivo de forma exacta
  (pk10 y score a 1e-9) en 618/646 decisiones.
  - De los ceros con tráfico real, 37 se reproducen con la ventana **posterior** a la marca de agua de los PCAP
    cerrados.
  - Los 14 restantes caen en ciclos donde un fichero rotó dentro de la incertidumbre del inicio de ciclo (el
    motor viejo no lo registraba).
- **Mecanismo.** `build_rows` crea ventanas hasta la observación más nueva de la entidad, y EVE llega casi en
  tiempo real. Los paquetes, en cambio, solo se leen de ficheros cerrados (rotación de 15 s). La ventana se
  decidía con pk10=0 (`no_live_packets_heuristic`, PERMIT) o con un conteo a medias, y quedaba en
  `scored_windows`, así que nunca se reevaluaba.
- **Conclusión.** No era «cero tráfico»: eran datos todavía no disponibles. La evidencia anterior (emulación
  exacta y marca de agua) lo atribuye al instante de decisión respecto a la rotación del PCAP, no a la VLAN, a la
  entidad ni a la definición.
- **Diferencias de lote fuera de alcance.** `flow_duration_mean_30s` depende de la historia observada: 230 s en
  vivo frente a un anillo de 15 min en el lote. Es una propiedad de diseño de features y contexto, no se toca.

## 3. Corrección mínima (repositorio del producto)

- **Commit** `7b275b8bab1c8343e55f40a103ee980dc497620b` en `main` de
  `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`.
- **Ficheros:**
  - `scripts/engine/motor_decision.py`: blob `cebba977…`, sha256 de los bytes publicados
    `e2b2eb535091ea0fb7aa08054aa8cc4eff295a4e678269cba5d4a5ee5d95bc73`.
  - `tests/test_motor_completitud.py`: blob `8b2e27bd…`, 6 pruebas OK.
- **Código anterior:** el desplegado tenía sha256 `4c41ec44…`; equivale al commit `62a75a1` del producto y solo
  difiere de `53f919e` en el docstring.

Qué cambia y qué no:

- `ventana_completa(window_end, marca_pcap)`: la ventana se decide en el **primer ciclo** en que el paquete más
  nuevo leído de ficheros cerrados la cubre. No hay espera fija.
- Se conservan la clave y el `window_end` originales, y `logged_at` sigue siendo la hora real de emisión. Campos
  nuevos: `inicio_ciclo`, `marca_pcap`, `marca_eve` y `pendiente_desde`.
- Ninguna pendiente se pierde en silencio. Si no se completa en `history_seconds−60` (170 s), se escribe
  `ventana_no_evaluada` con su motivo:
  - `pcap_incompleto`: la captura no llegó;
  - `ventana_no_regenerada`: el PCAP la cubre, pero la poda del búfer eliminó las observaciones que la creaban.
- `claves_ya_registradas()`: al reiniciar, carga las claves ya escritas y no duplica decisiones.
- **Sin cambios** en el modelo, el escalador, las features, los umbrales, los heurísticos ni los escenarios. No
  hizo falta reentrenar.
- **Coste:** la decisión se retrasa hasta que cierra el fichero y corre el siguiente ciclo. En la comparación de
  30 min, la mediana de `logged_at − window_end` pasó de 11,8 s a 23,9 s; el p95 bajó de 49,4 s a 45,2 s. La espera
  de una pendiente fue de 11–44 s.
- **Suite completa del producto en Windows:** 449 pruebas, 3 fallos. Los mismos 3 fallan en `main` limpio
  (`53f919e`) por el entorno Windows (permisos 0o600, bash). Ninguno toca el motor.
- **Compatibilidad:** `publicar_feed.py` y el panel filtran `event == "decision"`, así que el evento nuevo no les
  afecta. `analizar.py` (campaña) también lo ignora; queda como pendiente #59 de la matriz.

## 4. Verificación benigna antes y después

**Instancia candidata en paralelo** (07:51:40–09:06:41). Mismos argumentos que producción, con su propio log y
estado; producción no se tocó. Se comparó por clave contra el **recálculo completo** y contra la **emulación exacta**
del candidato, reconstruida con su `inicio_ciclo`, `marca_pcap` y `marca_eve` (`comparar_motores.py`).

| Ventanas 07:53–08:23 (30 min, seis perfiles; `out_p37b`) | Producción (motor anterior) | Candidato (corregido) |
|---|---|---|
| Decisiones | 2 217 | 2 216 |
| pk10 igual al completo | 1 262 | **2 199** |
| Ceros con tráfico real | **669** | 1 |
| Conteo distinto | 274 | 4 |
| Sin referencia completa | 12 | 12 |
| Duplicados por clave | 0 | 0 |
| Pendientes recuperadas · no evaluadas | — | 1 278 · 1 |
| Reproducidas exactas por emulación (pk10 + score) | — | **2 216/2 216** |
| `logged_at − window_end` mediana / p95 / máx (s) | 11,8 / 49,4 / 244,9 | 23,9 / 45,2 / 244,0 |

- **Features que pueden mover el score** (candidato emulado frente al completo, en 2 216 claves):
  - `flow_duration_mean_30s` en 968 claves;
  - `unique_dst_ip/port_ratio_30s` en 93/92;
  - `flow_attempt_rate_10s` en 34;
  - otras en ≤12.

  Todas dependen de la historia y del contexto (búfer de 230 s). Por eso el score coincide con el del recálculo
  completo solo en 1 231 claves, aunque el pk10 coincida. Las ventanas que comparten pk10 entre ambos motores tienen
  el mismo score en 1 137/1 273. La equivalencia, por tanto, **no** se declara por la desaparición de los ceros. Se
  declara porque las 2 216 decisiones se reproducen exactamente con la entrada que tenía el candidato al decidir.
- **Las 5 discrepancias residuales del candidato** (`out_p44`): todos sus paquetes estaban en ficheros
  cerrados antes de decidir, y no hay paquetes fuera de orden entre ficheros (0). La causa es la **atribución del
  flujo**: `attribute_packets` asigna el flujo a quien envía el primer paquete visible, y en un flujo largo
  (p. ej. 10.10.40.10↔10.10.60.10, de unos 2 000 s) ese primer paquete del búfer de 230 s no es el SYN que ve el
  recálculo completo. Es la misma limitación de contexto, afecta igual a producción y queda fuera de alcance.
- **La «no evaluada»** (10.10.20.23 07:57:30, `out_p38`): era una ventana vacía real (completo pk10=0) que dejó de
  generarse al podarse las observaciones viejas de la entidad. Se registró de forma explícita. Su motivo motivó
  separar `ventana_no_regenerada` de `pcap_incompleto`.
- **Casos pedidos:**

  | Caso | Evidencia |
  |---|---|
  | Tráfico junto a la rotación | Los 37 ceros del preflight posteriores a la marca de agua, y los ejemplos con `pendiente_desde` |
  | Ventanas sin tráfico | 262 «vacía real» en el preflight; `empty_window_heuristic` |
  | VLAN | 97–98 % de tramas 802.1Q en los tramos comparados |
  | Fuente temporalmente incompleta | 1 278 pendientes que se recuperan con el pk10 completo |
  | Prevención de duplicados | 0 en paralelo y 0 tras el reinicio |

  No se fabricaron ataques ni fixtures.

**Despliegue** (`out_p41`). Fuera de campaña y en sombra:

- **08:44:50.744:** `sudo -n systemctl restart ppi-motor`. PID 2558538 → 2277062, NRestarts 0, 0 errores en el
  journal.
- **Arranque:** `claves_previas_cargadas=22180`.
- **Respaldo:** `~/cf-prep-20261028/respaldo-motor/motor_decision.py.4c41ec44`.

**Después del reinicio** (ventanas 08:40–08:53, verificadas a las 08:57, ya recuperado el contexto de 230 s;
`out_p37c`, `out_p45`):

| Motor | Decisiones | pk10 igual al completo | Ceros con tráfico | Conteo distinto |
|---|---|---|---|---|
| Corregido (desde 08:44:50) | 636 | **633** (3 sin referencia) | 0 | 0 |
| Anterior (antes de 08:44:50) | 384 | 209 | 126 | 49 |

En el corregido, `logged_at − window_end` tiene mediana 25,4 s, p95 36,3 s y máximo 247,2 s. No hubo duplicados en
el tramo del reinicio ni ventanas no evaluadas.

**Incidencias:**

- La instancia candidata y el archivador de diagnóstico se pararon a las 09:06:41–09:07.
- El archivo de diagnóstico es continuo de 07:19:55 a 09:06:24: 426 ficheros, 3 274 416 paquetes, 0 vacíos, 0
  solapes, hueco máximo entre ficheros 0,373 s y paso de nombres de 15–16 s (`out_p51`).
- tcpdump no informa descartes mientras corre, así que **no se afirma pérdida cero**.

**Carga.** Con los perfiles a plena intensidad, cada motor consume unos 95 % de un núcleo, con ciclos medios de
11,9 s (producción) y 13,1 s (candidato, que compartía CPU con la comparación) para un paso de 10 s (`out_p43`). Bajo
la carga de un ataque **no se ha verificado**.

## 5. Perfiles legítimos

- `cyberflow-lab.target` se arrancó a las 07:36:11 (active/disabled, sin arranque automático; `out_p25`).
- Los seis servicios están active con NRestarts 0 y 0 errores en el journal a las 09:06:52 (`out_p48`).
- Argumentos originales: `--perfil X --origen 10.10.20.2N --servidor 10.10.30.10 --dns 10.10.10.20`.
- Alias .20–.26 presentes. No se usó tráfico del bastión ni se aumentó la intensidad.
- **Actividad real por IP** (`out_p35`, EVE de los últimos 10 min a las 08:02 y decisiones del motor):

  | IP | Eventos EVE | Decisiones | Suma pk10 |
  |---|---|---|---|
  | .21 | 324 | 63 | 388 |
  | .22 | 365 | 60 | 1 651 |
  | .23 | 70 | 60 | 5 138 |
  | .24 | 610 | 64 | 166 |
  | .25 | 49 | 45 | 10 |
  | .26 | 122 | 64 | 502 |

- **Horario.** `clientes_lab.py` ajusta la intensidad con la hora **UTC** del host: factor 0,12 antes de las
  08:00; 1,0 de 08:00 a 13:00; 0,55 de 13:00 a 15:00; 0,9 de 15:00 a 19:00; 0,35 de 19:00 a 23:00; ×0,3 en fin
  de semana. La prueba arrancó con factor 0,12 y pasó a 1,0 a las 08:00. La campaña A debe programarse entre las
  08:00 y las 13:00 UTC de un día laborable (03:00–08:00 en Perú), o declarar el factor vigente.

## 6. Copias y dependencias

- **Kali** `~/cf-campana-A/` (`out_p32`), hashes iguales a `e6a676a`:
  - `scripts/generar_campana.py` c586d813…;
  - `scripts/esquema_campana.py` e762e604…;
  - `escenarios/escenarios.json` 67798012….
- **Validación de la Kali:**
  - `validar(exigir_herramientas=True)` sin problemas; 5/5 escenarios habilitados, con herramientas presentes
    (bash, nmap).
  - Simulación sin `--autorizado` en `/tmp`: 25 episodios «simulado», rc 0, 0 salidas de proceso; borrada.
  - 0 procesos de herramientas vivos.
- Los 3 α y las 7 configuraciones siguen intactos en `config-campana.json`, que no se ha modificado.
- **srv-dmz** `~/cf-campana/`: `modo_sombra.sh` bc2742f8… (anterior conservado como `modo_sombra.sh.e6a676a`) y
  `restaurar_enforcement.sh` b27a0f3e….
- **Pruebas benignas desde la Kali** a las 08:01:41, en sombra (`out_p33`):

  | Prueba | Resultado |
  |---|---|
  | `preparacion-1793174501.lab-ppi` | NOERROR → 10.10.30.10 |
  | SOA `lab-ppi` | DC local |
  | GET :80 | 200 |
  | `/auth` sin credencial | 401 |
  | `/auth` con credencial ficticia | 401 |
  | `/auth` con la credencial de control | 200 |

- **Lectura de fuentes:** PCAP del anillo, EVE, log de decisiones, features (recálculo) y scores (pipeline
  desplegado) se leen en todos los diagnósticos.
- **Relojes** a las 08:01 frente al bastión (chrony, `out_p34`): sensor +7,5 ms, Kali −20,8 ms, srv-dmz +6,1 ms,
  clientes +4,5 ms, todos con NTP sincronizado.
- **Espacio:** 20 GB libres en el sensor (44 % usado). El archivo de diagnóstico ocupa 619 MB, unos 340 MB/h a
  plena intensidad.
- **Supervisión y parada:** PID del candidato en `motor.pid`; terminación del grupo del generador ya verificada
  (4/4); `TaskStop`/`kill` documentados.

## 7. Estado final (09:07) y pasos para el prompt 2

| Pieza | Estado |
|---|---|
| Enforcement | **En sombra.** Agente inactive, timer inactive/disabled, sets vacíos (rc 0). **No** se ha reactivado |
| Motor | `ppi-motor` activo con el corregido e2b2eb53…, PID 2277062, sin `--enforce` |
| Captura y servicios | `ppi-motor-capture`, Suricata, panel, publicador y acumulador activos, NRestarts 0 |
| Perfiles | Seis activos desde 07:36:11. Siguen en marcha para dar contexto; se pueden parar con `sudo systemctl stop cyberflow-lab.target` en clientes |
| Candidato y archivador | Parados. Ficheros conservados en `~/cf-prep-20261028/` (sensor) |

**Reversión del motor** (en el sensor, m4rk):

```
cp -p ~/cf-prep-20261028/respaldo-motor/motor_decision.py.4c41ec44 ~/cyberflow/scripts/engine/motor_decision.py
sudo -n systemctl restart ppi-motor
```

En el repositorio del producto, `git revert 7b275b8`.

**Reversión de la sombra** (en srv-dmz), solo **tras revisar** el feed y la escalada:

```
cd ~/cf-campana && bash ./restaurar_enforcement.sh --ejecutar --escalada-revisada
```

Usa `/opt/cf-sombra-estado/20261028-073340`. No se ejecuta automáticamente: el feed propone LIMIT para cuatro
perfiles legítimos.

**Para el prompt 2:**

1. Mantener la sombra durante la campaña A.
2. Programarla entre las 08:00 y las 13:00 UTC de un día laborable.
3. Antes de **analizar**, adaptar `analizar.py` para contar `ventana_no_evaluada` como cobertura no evaluable y
   actualizar la referencia `motor_decision.py:601` de `config-campana.json` (#59).
4. Interpretar las latencias con el retraso medido de la corrección.
5. Vigilar el retraso del ciclo del motor bajo carga.

## Tabla de estado

| Requisito | Estado |
|---|---|
| Sombra activa y verificada (agente, timer, sets con consulta OK) | OK |
| Propuestas del feed distinguidas de restricciones aplicadas | OK |
| Diagnóstico de la causa con evidencia (emulación exacta, marca de agua) | OK |
| Corrección versionada (producto `7b275b8`), pruebas, código anterior y reversión | OK |
| Paralelo ≥ 30 min con los seis perfiles: candidato coincide con el completo salvo 5 explicadas | OK |
| Despliegue en sombra, reinicio registrado, contexto recuperado, sin duplicados | OK |
| Equivalencia de features del score con el lote | NO VERIFICADO (diferencias de contexto/historia por diseño, fuera de alcance) |
| Seis perfiles activos, estables y con actividad real; horario documentado | OK |
| Copias de la Kali con hash, validación y simulación | OK |
| /auth, HTTP y DNS local (benignas) | OK |
| Relojes (≤ 21 ms) | OK |
| Archivado continuo, espacio y permisos | OK |
| Pérdida de paquetes de la captura | NO VERIFICADO (no se afirma pérdida cero) |
| Capacidad del motor bajo carga de ataque (ciclo de 12–13 s a plena intensidad benigna) | NO VERIFICADO |
| `analizar.py` cuenta `ventana_no_evaluada` | BLOQUEO para el **análisis** (no para generar el tráfico) — #59 |
| Reactivar el enforcement | No aplica a A; requiere revisar el feed (LIMIT de perfiles legítimos) |

## Conclusión

**Se puede preparar el arranque del prompt 2 en sombra.** El defecto que bloqueaba el preflight está diagnosticado,
corregido de forma mínima, versionado y verificado: en el motor desplegado, 633/633 decisiones coinciden con el
recálculo completo, sin ceros con tráfico ni duplicados.

Antes de *analizar* los resultados queda un requisito: que `analizar.py` trate `ventana_no_evaluada` (#59). Antes de
cualquier prueba de **respuesta activa** hay que revisar las propuestas LIMIT sobre perfiles legítimos. Quedan
documentadas como limitaciones abiertas, no resueltas:

- las diferencias de contexto en `flow_duration_mean_30s` y en la atribución de flujos largos;
- la capacidad del motor bajo la carga de un ataque;
- la ausencia de una medida de pérdida de paquetes.
