# PUNTO DE REANUDACIÓN — Campaña B (guardado el 10-nov-2026, noche; ≈ 23:00–23:30Z)

> Carpeta B = `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10\`
> Documento maestro: `PREPARACION-B-RESULTADOS-2026-11-10.md` (secciones 43–45.7; extracto `SECCIONES-43-45.md`).
> Memoria del proyecto: `C:\Users\markp\.claude\projects\C--Users-markp-Desktop-PY-MEGATRON\memory\cyberflow-campana-b-preparacion.md`.
> Idioma de trabajo: español. Cada comando lleva etiqueta de máquina/cuenta y quién lo ejecuta (CLAUDE.md global). Rutas siempre absolutas.

## 1. Objetivo
Cerrar la Campaña B (respuesta real con agente `--aplicar` solo sobre la Kali 10.10.20.30): dejar D5 sin reinicio verificado en banco, cerrar la revisión de fuentes de la repetición cancelada B2, y entregar un **paquete concreto para revisión** (versiones y hashes, cambios por host, comprobaciones de aceptación, reversión, estimación del trabajo restante) **sin desplegar ni correr**.

## 2. Paso exacto alcanzado
Estaba **preparando la instrumentación propuesta en copias locales** (petición vigente de Mark). Último acto: escribir `instrumentacion\test_instrumentacion.py` (**sin ejecutarlo**). No había ningún comando en curso. Antes de eso: persistencia del bloqueo de la puerta + emulador de invocaciones (terminado y probado).

## 3. Terminado (ejecutado y con resultado)
| Hito | Resultado | Evidencia |
|---|---|---|
| #1 D5 sin reinicio bajo systemd 257 (contenedor, 4 casos) | PASA (NRestarts 0, MainPID estable); registro formal §45.2ter | `propuestas\d5-sin-reinicio\evidencia-systemd\` |
| #3 auditoría rotable: rotador de banco + **logrotate 3.22.0-1 real** (forzado `-f`) | 33 comprobaciones OK; 44 pruebas; 46 mutaciones (27+19) detectadas; **ejecución diaria sin verificar** | `evidencia-auditoria\`, `evidencia-logrotate\` |
| Simulador (arnés / `compuerta_b.paso_puerta`) | 6 pruebas, 8/8 mutaciones; **hallazgo**: `compuerta_b.bucle` reintenta tras `fallida` | `evidencia-simulador\` |
| Revisión de fuentes de B2 | CERRADA: PCAP (503, sha OK), clientes, Kali, srv-dmz, relojes, E5 | `revision-evidencia-b2\`, §45.2novies–duodecies |
| Integración de D5 en copia de banco (decisión E solo-banco) | **Mark la dio por verificada**: 59 pruebas, 12/12 mutaciones, 3 casos systemd PASAN | `evidencia-integracion\` |
| Persistencia del bloqueo entre invocaciones (**nuevo, posterior a la verificación**) | `test_invocaciones_d5.py` 4 pasan; `test_invocaciones_d5 + test_integracion_d5` = 13 pasan; `mutar_invocaciones_d5.py` 8/8 | ejecutado en contenedor; **sin carpeta de evidencia guardada** |

**Hallazgo clave de invocación real:** `compuerta_b.puerta` llama a `puerta_fn()` en cada turno y crea `d5.Puerta(runners)` **NUEVA** cada vez (y cada orden remota es un proceso SSH nuevo). Un bloqueo en memoria se perdería → se añadió bloqueo en fichero (`puerta-bloqueo.json`, escritura atómica, cerrojo `flock`, fichero ilegible = bloqueado, reanudación archiva el caso).

## 4. Preparado pero NO verificado / NO terminado
- **Instrumentación** (`instrumentacion\`, creada, **ninguna prueba ejecutada**): `inundacion_instrumentada.sh` (7ac53358…), `analizar_intentos.py` (687a1e1e…), `clientes_factor1_tx.py` (d86c7edc…), `muestreador_set.py` (410759c2…), `analizar_b_instrumentado.py` (77140e8b…; `e3_v2` = «SPAN o salida», delega en `analizar_b.e3` si no hay salida), `test_instrumentacion.py` (718a1419…). `test_instrumentacion.py` tiene **dos líneas basura/tautológicas a limpiar** (en el test del envoltorio: la línea `acciones = ... if False else None` y el assert `all(...) or any(...)`) y su ejecución es lo primero que falta.
- **Cambió `hacer_d5_episodio_banco.py`** (ahora 7a3978a1…; antes baacb29f… y derivado e31e8b5e…): las **59 pruebas completas y los 3 casos systemd NO se repitieron** tras añadir la persistencia; solo se corrió el subconjunto de 13. Hay que re-ejecutar la suite completa y `probar_integracion_systemd.py` UNA vez (y regenerar hashes en `evidencia-integracion\sha256-completos.json`).
- **No creados todavía:** `CRITERIO-E3-SPAN-O-SALIDA.md` (regla escrita con referencias: `OBJETIVOS-Y-CRITERIOS` E3 dice «SPAN o salida»; protocolo v3 línea 37 dice «SYN ≥ 50 % de B0, y salida»; `analizar_b.py` `INTENTO_MIN=0,5`, `K_LIMIT=5`); prueba local de `inundacion_instrumentada.sh` con Git Bash + `curl.exe` + servidor sintético en loopback (el contenedor banco **no tiene curl**); **propuesta del Hallazgo 2**; **paquete final** (versiones/hashes, cambios por host, aceptación, reversión, estimación); actualización de la sección 45 con todo esto.
- **Corrección pendiente en §45.2decies:** dice que las «fallidas» de los perfiles de clientes incluyen fallos intencionales; es **inexacto**. En `clientes_lab.py` «fallida» = excepción (timeouts, conexión rechazada, ping fallido); los errores HTTP previstos (401/404/500) cuentan como acción hecha y `puerto_cerrado`/`abandono` no cuentan como fallo. Las 6 fallidas de la sesión B2 (navegación 4, aplicación 1, errático 1; **sin hora**) siguen sin poder situarse en episodios.

## 5. Procesos y contenedores activos
**Ninguno.** `docker ps` sin contenedores `cf-*` (los `cf-d5-systemd` y `cf-d5-integracion` se retiraron). Sin procesos Python del trabajo en la laptop. Imágenes locales que se conservan: `cyberflow-etapa3-banco:1` (banco) y `cyberflow-etapa3-banco-logrotate:1` (banco + logrotate, construida con autorización de Mark vía `apt` en la construcción). Tarea de fondo anterior detenida.

## 6. Decisiones ya autorizadas por Mark
1. Lectura y copia de registros existentes de B2 (clientes, salidas de la Kali) y del registro HTTP de srv-dmz; cuenta `adminsrvdmz` vía bastión `gadmin@10.10.10.30` con `~/.ssh/cyberflow-to-srv`, **sin sudo**.
2. Descarga del paquete Debian `logrotate` solo para construir la imagen de banco.
3. **Decisión E únicamente para banco**: integrar D5 sin reinicio en copia de `d5_episodio.py`, datos sintéticos, sin orquestador, rutas temporales, permisos ya probados (`nobody:d5aud`, dir 2750, ficheros 0640, UMask 027), retención de banco `rotate 30`.
4. Reglas fijas: solo un acuse válido continúa; tras fallo/incierto la puerta se bloquea, sin solicitudes nuevas; reanudación solo manual y registrada (quién y por qué); **C3 vigente**; sin despliegue ni corrida.
**NO autorizado:** despliegue, `sudo`, orden de corrida/`--aplicar`, cambios en servicios, cambio del criterio de E3, tocar `compuerta_b`/orquestador real.

## 7. Pendientes que requieren revisión/decisión de Mark
1. **Despliegue** (cambia publicador del Sensor1 y su `ExecStart`; requiere su `sudo`; actualizar SHA256SUMS de `ec78ca5`) y **orden de corrida**.
2. **Hallazgo 2** (reintentos de la puerta por ventanas del episodio anterior): sigue pendiente aparte; con el bloqueo, un fallo por este motivo exige reanudación manual. Falta la propuesta concreta (revisar las ventanas anteriores sin ignorar señales vigentes ni repetir solicitudes) como decisión explícita.
3. **Criterio de continuidad de E3**: elegir «SPAN o salida» (OBJETIVOS) vs «SPAN y salida» (protocolo v3) y fijarlo por escrito antes de otra corrida.
4. Ruta/propietario/retención definitivas de la auditoría; usuario y permisos reales del canal de control bastión→Sensor1; lectura entre hosts.
5. Instrumentación: aprobar y probar (ver §4) antes de instalar nada.
6. Estimación vigente (a rehacer desglosada en el paquete): ≈ 6,5–8 h tras decisiones; corrida de 25 episodios ≈ 2,3 h (2,1–2,9 h) — **cadencia real inicio→inicio 5,0 min, ≈ 7 min tras un DNS con reintento; los «37,5 min» = 17:51:10Z→18:28:40Z incluyen 4,0 min de calentamiento y 2,7 min de cierre**.

## 8. Rutas de evidencia (todas bajo la carpeta B salvo indicación)
- `revision-evidencia-b2\`: `evidencia-local\` (5 trazas B2 + `SHA256.txt`), `analizar_pcap_b2.py`, `lector_pcap.py`, `resultado-pcap.json`, `revisar_evidencia_b2.py`, `resultado-revision.json`, `e5_retirada_b2.py`, `e5-retirada-b2.json`, `analizar_srvdmz_b2.py`, `resultado-srvdmz.json`, `pcap-copia\` (manifiestos, `PROCEDENCIA.txt`, `relojes-4c.log`, `SHA256-clientes-kali.txt`).
- Copias fuera del repo (ruta corta por el límite de Windows): `C:\Users\markp\cf-b2-pcap\pcap\` (503 PCAP, sha 503/503 OK), `\clientes\`, `\kali\`, `\srvdmz\` (extracto journal sha `215b618d…`), `\bastion\relojes-4c.log`, tars y `SHA256-clientes-kali.txt`. **No versionado.**
- `propuestas\d5-sin-reinicio\`: código (`hacer_publicador_d5.py`, `adaptador_banco*.py`, `auditoria_d5.py`, `puerta_simulada_banco.py`, `hacer_d5_episodio_banco.py`, `emulador_compuerta_d5.py`), pruebas y mutadores, y evidencias `evidencia-{systemd,auditoria,logrotate,simulador,integracion}\`.
- Originales B2 (NO tocar): Sensor1 `~/cf-e4/4c-B2-cancelada-X1-completo-20261110T1833Z` y `…-20261110-175000-183200`; Kali `/home/adminatacante/cf-e4-4c-B2-cancelada-X1-20261110T1832Z`; bastión `/home/gadmin/cf-e4/4c-B2-cancelada-X1-20261110T1832Z`; srv-dmz `/var/lib/cyberflow/agente/traza-B-20261110T183104Z.jsonl` (+`.sha256`), journal activo de `ppi-brute-lab` (sin copia rotada).
- Primera corrida (cancelada por X3, `…-B-cancelada-X3-…`): **separada, no leída ni mezclada**.

## 9. Limitaciones de B2 (no cambiar los resultados históricos)
Los 6 episodios siguen **C3** (reinicio del publicador por D5, §43 Hallazgo 1). Matriz: E1 verificado 6/6; E2 verificado 4/4 (DNS sin punto de aplicación); E3 fuerza bruta verificado 2/2, **inundación indeterminado 2/2** (aceptadas −89,6 %/−89,8 %, pero SYN 38/s < 156/s; salida del generador = total sin hora); **E4 formal no evaluable** (no existe registro por transacción; el servidor :80 no registra peticiones) y reconstrucción indirecta indeterminada; E5 retirada explícita verificada 4/4 (en E6 sin episodio siguiente; sin caducidad natural; 2 lecturas del set por episodio). Reloj medido una sola vez al inicio (desfases ≤ 7,1 ms). Ningún criterio fallido.

## 10. Estado del laboratorio (última verificación, solo lectura, 10-nov ≈ 21:25–22:45Z)
Cerrado y restaurado por Mark; reversión R0–R7 ejecutada a las 18:31Z; `desarmar` 18:44:15Z (logrotate reanudado). srv-dmz: agente en sombra sin `--aplicar`, 0 tablas cyberflow, `ppi-brute-lab` **inactive**, web `:80/:443` activa y silenciosa. Sensor1: motor/publicador/vía rápida/Suricata activos, publicador con `--politica if_senal` sin `--aplicar`. Clientes: `cyberflow-lab.target` activo. Kali: sin generadores. **No se verificó de nuevo después de las ~22:45Z**: antes de cualquier acción real, repetir el preflight de solo lectura.

## 11. Siguiente paso concreto (en este orden, sin repetir lo aprobado)
1. **[LAPTOP PowerShell → lo ejecuto yo]** limpiar las 2 líneas basura de `instrumentacion\test_instrumentacion.py` y ejecutar SOLO ese fichero en contenedor `cyberflow-etapa3-banco:1` (`--network none --read-only`, montando la carpeta B en `/b` solo lectura y `producto-etapa3` en `/producto-etapa3`, `CF_LAB=/producto-etapa3/scripts/laboratorio`); corregir lo que falle.
2. Probar `inundacion_instrumentada.sh` en la laptop (Git Bash `C:\Program Files\Git\bin\bash.exe`, `curl.exe`, servidor sintético en loopback; **no tráfico al laboratorio**).
3. Re-ejecutar UNA vez la suite completa de `propuestas\d5-sin-reinicio` y `probar_integracion_systemd.py` (contenedor `cyberflow-etapa3-banco-logrotate:1` con systemd, ver `probar_integracion_systemd.py`) tras el cambio de persistencia; guardar `evidencia-integracion\` actualizada con hashes.
4. Escribir `CRITERIO-E3-SPAN-O-SALIDA.md` y la **propuesta del Hallazgo 2** (decisión explícita).
5. Construir el **paquete** (`PAQUETE-REVISION-B.md`): versiones/hashes de todo, cambios previstos por host (Sensor1, bastión, srv-dmz, Kali, clientes), comprobaciones de aceptación, reversión, estimación del trabajo restante desglosada; corregir §45.2decies; actualizar §45 y `SECCIONES-43-45.md`; actualizar la memoria.
6. Dejar despliegue y orden de corrida **para revisión de Mark**.

## 12. Mensaje breve para retomar en otra sesión
> Retoma la Campaña B desde `PUNTO-DE-REANUDACION-B.md` (carpeta B). Estado: D5 sin reinicio verificado en banco; el bloqueo de la puerta ahora persiste en fichero (4 pruebas + 8 mutaciones OK, **suite completa y systemd por repetir una vez**); instrumentación creada pero **sin ejecutar** (`instrumentacion\test_instrumentacion.py`). Haz el paso 1 del §11 sin repetir pruebas aprobadas, luego el paquete de revisión. Sin despliegue, sin sudo, sin corrida; C3 vigente; revisa el laboratorio en solo lectura antes de cualquier acción.

## 13. ACTUALIZACIÓN (11-nov, sesión retomada)
HECHO: pasos 1–5 del §11. Test de instrumentación 12/12 (líneas basura limpiadas); script de inundación probado en loopback; suite completa 63 pasan + mutaciones 12/12 y 8/8 + systemd 7/7 con el código de persistencia; escritos CRITERIO-E3-SPAN-O-SALIDA.md, PROPUESTA-HALLAZGO-2.md y PAQUETE-REVISION-B.md; §45.2decies corregida; §45.8 añadida. PENDIENTE: decisiones de Mark (criterio E3, Hallazgo 2, ruta/retención, despliegue y orden de corrida); construir el transporte SSH de la solicitud (no existe; ver PAQUETE §5). Sin contenedores activos; laboratorio verificado en sombra el 10-nov 23:24Z.

## 14. ACTUALIZACIÓN (11-nov, tarde)
HECHO: transporte distribuido en banco (sensor_control_d5.py, transporte_bastion.py; 14 pruebas, 12/12 mutaciones), espera de 75 s a escala (3 pruebas), e3_v2 registra ambas vías (13 pruebas), CRITERIO y PROPUESTA-HALLAZGO-2 ampliados, logrotate propuesto para m4rk, PAQUETE-REVISION-B.md v2, §45.9. Sin contenedores míos activos. PENDIENTE: decisiones de Mark; lanzador del bastión (puerta_fn_banco + SshReal) no construido; SSH real/clave forzada sin ejercer. Sin despliegue ni corrida.

## 15. ACTUALIZACIÓN (11-nov, noche)
HECHO: OpenSSH real en banco (5 pruebas), lanzador del bastión de banco (2 pruebas), guiones por host en paquete-despliegue\ (10 pruebas de ensayo), PAQUETE-REVISION-B.md v3 (estimación 5,1-6,8 h), §45.10. Suite sin root: 66 pasan, 3 omitidas (módulos que exigen root, se corren aparte: 14+5+2). PENDIENTE: decisiones de Mark; primera ejecución real de los guiones; huella del huésped fuera de banda. Sin contenedores míos activos; sin despliegue ni corrida.

## 16. ACTUALIZACIÓN (11-nov, 00:30Z)
HECHO: revisión del paquete v3 en hosts reales con lecturas (sin sudo, sin escribir en hosts) y modo seco en espejo local con rutas reales; correcciones (derivado a ~/cf-b/d5 + PYTHONPATH, ExecStart multilínea, from=10.10.10.30, aceptar sin /tmp); CRITERIO-E3-FINAL-PARA-APROBAR.md; PAQUETE v3.1 §13. INCIDENTE: ssh-keygen -h en lectura del bastión, verificado que no creó nada. PENDIENTE: decisiones de Mark; copiar el paquete a los hosts (escritura remota, 17 ficheros 111,4 KB) y sudo del Sensor1 (comandos en PAQUETE §13.6). Sin instalación ni corrida.

## 17. ACTUALIZACIÓN (11-nov, 01:10Z)
Huella del Sensor1 confirmada por Mark desde consola; identidad fijada en ~/.ssh/known_hosts_d5 del bastión. Paquete copiado a ~/cf-b/paquete-despliegue/ en los 5 hosts (sha OK) y comprobaciones de preparación hechas (PAQUETE §14, preparacion-en-hosts\). NO instalado. Siguiente: decisiones de Mark (E3, espera 15/75, ruta/retención), luego bastión 'clave --aplicar', Sensor1 'instalar --aplicar', sudo §13.6, aceptar.

## 18. ACTUALIZACIÓN (11-nov, 01:20Z)
Pasos 2 y 3 hechos: clave dedicada del bastión (huella gw4T8ep3…) e instalar --aplicar en Sensor1 sin sudo ni reinicio (authorized_keys respaldado en ~/cf-b/respaldo-d5/20261111T011542Z, 2 claves previas intactas; aceptación 18 OK / 2 FALLAN = drop-in y logrotate). pendiente-sudo hashes 16c2ca0d… y 445efe82…. Siguiente: Mark ejecuta el bloque sudo de PAQUETE §15 (sin reinicio); luego autorizar reinicio y corrida.

## 19. ACTUALIZACIÓN (11-nov, 01:45Z)
Fases sudo hechas por Mark (20 OK / 0 FALLAN). Preparando el reinicio controlado SOLO del publicador: Sensor1 y Kali conformes; clientes, srv-dmz (agente en sombra) y bastión SIN comprobar porque el enlace del lab cayó (ubuntu-router de Tailscale offline). Retomar: restablecer ruta a 10.10.0.0/16, repetir comprobaciones, luego entregar comando de reinicio + aceptación. Sin reinicio ni corrida.

## 20. ACTUALIZACIÓN (11-nov, 02:55Z)
Verificación previa completa y conforme (§45.15). Ruta a 10.10.0.0/16 = VM-GESTION (bastión); causa del corte de 01:44Z NO confirmada; ubuntu-router es del otro hipervisor. Referencia Sensor1: PID 1971245, NRestarts 18, secuencia 26060. Aceptación en reinicio-d5\ (dos guiones). Siguiente: Mark ejecuta el reinicio con sudo (solo ppi-publicar-feed-v2) y pega la salida; yo ejecuto la aceptación. Corrida con --aplicar: pendiente.

## 21. ACTUALIZACIÓN (11-nov, 03:10Z)
D5 ACTIVO en el publicador (PID 2115304 desde 03:05:25Z; NRestarts=0 por reinicio manual). Aceptación 33/33 en Sensor1 y 7/7 bastión–Sensor1; firma verificada con openssl; secuencia 26111 > 26095. Pendientes: prueba de limpieza D5 (primer solicitar, escribe control y auditoría) y corrida con --aplicar solo sobre Kali; decisiones E3 y espera 15/75 s.

## 22. ACTUALIZACIÓN (11-nov, 03:25Z)
Prueba D5 e2e PASA (id 8808ef6d…, acuse+auditoría+feed firmado seq 26130, PID 2115304 y NRestarts 0 continuos); Kali ya estaba limpia -> valida recorrido/acuse, no el efecto. E3 fijado en CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md. Preflight: 11 OK / 0 FALLAN / 9 PENDIENTES (instalar bastión e instrumentación, NOPASSWD muestreador, g01 con lanzador --espera-fin 75, aceptación §9 5-9, e3_v2 BLOCK, decisiones de Mark). Corrida --aplicar pendiente.

## 23. ACTUALIZACIÓN (11-nov, 03:50Z)
Instalado en bastión + instrumentación en Kali/clientes/srv-dmz; generador instrumentado en Kali (hashes verificados, simulacro: solo cambian los 5 episodios de inundación); g01c listo (no ejecutado); e3_v2 con rama BLOCK; preflight v2 = 24 OK / 0 FALLAN / 3 PENDIENTES (logrotate diario sin observar, decisión fuerza_bruta_http, medición de la puerta con ensayo_puerta_75.sh que exige UNA solicitud real). Orden de lanzar los 25 episodios con --aplicar: pendiente. NOTA: no hacer `cd` a rutas > 260 caracteres (rompe las shells).

## 24. ACTUALIZACIÓN (11-nov, 04:00Z)
BLOCK = SPAN única fuente (BLOCK_ADMITE_SALIDA=False; criterio sha 2d1a9e6b…). Ensayo de la puerta: acuse, control consumido, PID 2115304 y NRestarts 0 sin cambios; fin+75 s + puerta 28,7 s = 104,7 s -> margen 105,3 s frente a 210 s. Inundación instrumentada v2 (8e9b49b1…, -1,7 % de carga vs -18,5 % de la v1) instalada en la Kali. Preflight final v3: 26 OK / 0 FALLAN / 1 PENDIENTE (logrotate diario, observación 12-nov 00:00Z). Falta la orden de lanzar los 25 episodios con --aplicar (solo Kali) y sus pasos operativos (control 30 min, respaldo srv-dmz, b_activar_srvdmz, muestreador, g01c).
