# Campaña nueva — detección (4.2) y respuesta (4.4)

**Fase: preparación endurecida. No se ha ejecutado ningún ataque ni la campaña.** La campaña A se autoriza en la
instrucción siguiente. Correcciones sobre `b59c6c8` descritas en `MATRIZ-OBSERVACIONES.md`.

Carpeta independiente: no modifica `../4.2-ablacion/aporte-componentes-r2-2026-10-26/` ni ninguna evaluación anterior.

## Contenido

| Archivo | Contenido |
|---|---|
| `PLAN-CAMPANA.md` | Plan A/B, historia/registros, marcas, criterios, **secuencia prep→ejecución→restauración**, estados de madurez |
| `config-campana.json` | Configuración congelada (versión `2026-10-28.1`): modelo+hashes, umbrales α 0,05/0,03/0,01 con su fuente verificable y el desplegado aparte, 7 configuraciones de análisis, 28 características, lógica de combinación, `logged_at` vs `window_end`, relojes/DNS medidos |
| `CAMBIOS-2026-10-28-alfa001.md` | Registro de cambios de la ampliación a α 0,01 (qué cambia, qué no, comprobaciones) |
| `CAMBIOS-2026-10-28-procedencia.md` | Corrección de procedencia temporal: clasificaciones derivadas vs emisiones observadas (config `2026-10-28.2`) |
| `CAMBIOS-2026-10-28-umbral-ausente.md` | Registro de decisión sin la clave `threshold`: se conserva como evidencia incompleta (umbral y configuración desconocidos), con incidencia |
| `escenarios/escenarios.json` · `FICHAS-ESCENARIOS.md` | Escenarios v2 (tipos separados, tasas fijas, pendientes explícitos) |
| `scripts/esquema_campana.py` | Esquema + validación + construcción de comandos |
| `scripts/generar_campana.py` | Generador (Kali): valida, simula por defecto, inicio/fin separados, mata el grupo en timeout |
| `scripts/analizar.py` | Analizador: clasifica por `logged_at` **7 configuraciones comparativas derivadas** (IF 0,05/0,03/0,01, heurísticos, híbrido 0,05/0,03/0,01), **Tabla 8 solo con atribución confirmada e integridad apta**, control FPR, calidad de datos, procedencia y orden de umbrales; lista **aparte** las emisiones observadas (alertas reales con emisor/umbral registrados; desconocido si faltan) |
| `scripts/verificar_integridad.py` | Informe de integridad por episodio: estados **verificado / declarado_sin_verificar / ausente / desconocido** (un booleano no es verificación; exige respaldo accesible o informe externo correspondiente); `analizar.py --integridad` lo exige para declarar evaluable |
| `scripts/generar_manifiesto.py` | Manifiesto con sha256 de los **bytes publicados por git** (LF), reproducible y verificable contra el commit |
| `scripts/capturar.sh` · `estimar_espacio.sh` | Captura continua (ens37) y estimación de espacio |
| `scripts/comprobar_relojes.sh` | Desfase por host, antes y después |
| `scripts/modo_sombra.sh` · `restaurar_enforcement.sh` | Sombra para A (`--ejecutar --motor-verificado`) y restauración (`--ejecutar --escalada-revisada`); los flags confirman comprobaciones previas; no aplicados aún |
| `EJEMPLO-descriptor-integridad.json` · `EJEMPLO-integridad-salida.json` · `EJEMPLO-fixtures/` · `EJEMPLO-evidencia-destino.csv` | Ejemplos de integridad (declarado / no apto / apto) con **fixtures de herramienta** (no capturas de campaña) y formato de evidencia de destino |
| `ESTADO-ENTORNO-2026-10-27.md` | Preparación del entorno real antes de A: accesos, relojes, DNS, endpoint, archivado, enforcement; cambios/reversión; **veredicto NO LISTO** con 3 pendientes críticos del usuario |
| `scripts/endpoint_brute/` | Endpoint 401 correcto (`app.py`, unidad systemd, README con nginx y Suricata) |
| `tests/test_herramientas.py` · `tests/fixtures.py` | Verificación sin ataques (188 comprobaciones; datos sintéticos/fixtures = comprobaciones del código) |
| `tests/regresion_alfa.py` · `tests/golden-5config-fixtures.json` · `tests/golden-7config-fixtures.json` | No-regresión de detección y cobertura frente a los analizadores de `0d40bdb` (5 configs) y `a6dc5ab` (7 configs); solo se excluyen, y se listan aparte, las claves de procedencia/etiquetado temporal |
| `tests/test_matar_grupo.py` | Terminación del grupo de procesos (4 casos) contra la función publicada |
| `tests/test_sombra.sh` | Fallo seguro de sombra/restauración con comandos simulados (11/11) |
| `RELOJES-DNS.md` | Relojes y DNS medidos + pasos administrativos |
| `MATRIZ-OBSERVACIONES.md` | Observación → corrección → archivo → comprobación → estado |
| `RESULTADOS-VERIFICACION.md` | Resultados de las verificaciones sin ataques |
| `COMPROBACIONES-PREVIAS.md` | Comprobaciones benignas y bloqueos |
| `evidencia-precheck/` · `MANIFIESTO-CAMPANA.json` | Evidencia cruda y hashes |

## Estado por pieza (documentado / implementado / probado aislado / verificado en entorno)

- Generador, esquema, analizador, verificador de integridad, endpoint: **implementados y probados de forma aislada** (188 comprobaciones + CLI + loopback).
- Umbral registrado ausente (28-oct, sobre `a69224c`): un registro sin la clave `threshold` se conserva con incidencia y umbral/configuración desconocidos (no da latencia confirmada): **probado de forma aislada**.
- Procedencia temporal (28-oct, `2026-10-28.2`): clasificaciones derivadas separadas de las emisiones observadas; detección y cobertura sin cambios: **probado de forma aislada**.
- α 0,01 (28-oct): umbral completo con procedencia verificada, comparación estricta, escala de anomalía, 7 configuraciones, no-regresión de 0,05/0,03 y anidamiento: **probado de forma aislada** (fixtures/sintéticos, no resultados experimentales).
- Analizador (cobertura, score null, atribución confirmada→Tabla 8, ventana previa, emitido/derivado, integridad): **probado de forma aislada** con fixtures de resultado conocido, incluido el recorrido hasta el fichero de la Tabla 8.
- Sombra/restauración con fallo seguro (detener+enmascarar el agente, no dry-run; `--escalada-revisada`): **implementadas y probadas de forma aislada** (`test_sombra.sh` 11/11); **no aplicadas** al entorno.
- Terminación del grupo de procesos (incl. hijo que ignora SIGTERM y padre que termina antes): **probada contra la función publicada**, en Windows (casos 1–2) y **verificada en el entorno** (sensor Linux, 4/4).
- Contadores del generador = **intentos** del bucle (no peticiones enviadas ni respuestas; eso se mide con PCAP/EVE/servidor).
- `logged_at` como hora de emisión, desfase del sensor (−47,55 s), egress del DNS, interfaz de captura (ens37): **verificados en el entorno**.
- Captura continua y endpoint en srv-dmz, zona DNS local, sincronización del sensor, parseo HTTP de Suricata en el puerto: **documentados**, pendientes de ejecución/verificación en el entorno.

## Pendientes reales (máquina · acción · permisos · quién)

| # | Máquina | Acción | Permisos | Quién puede resolverlo |
|---|---|---|---|---|
| 1 | Sensor 10.10.60.11 | Forzar sincronización de `timesyncd` (ya apunta al bastión) y medir desfase | sudo con contraseña (m4rk tiene ALL) | Mark en el sensor; luego yo verifico |
| 2 | DNS/AD 10.10.10.20 | Crear zona local reservada + comprobar no-egress | acceso al DNS/AD (sin mis llaves) | Mark / administrador del DNS |
| 3 | srv-dmz 10.10.30.10 | Desplegar `endpoint_brute/` y confirmar que Suricata parsea el puerto | sudo (adminsrvdmz NOPASSWD ALL) | yo, cuando se autorice; o Mark |
| 4 | pfSense | Permitir Kali→srv-dmz:18081 (endpoint) | admin pfSense | Mark / administrador del cortafuegos |
| 5 | Sensor | Ruta de archivado con espacio para captura continua | sudo NOPASSWD `cf-capturar` / tcpdump | yo |
| 6 | srv-dmz / sensor | Poner en sombra (A) y restaurar (B) | sudo (NOPASSWD ALL en srv-dmz) | yo, al autorizar A; revertir tras A |
| 7 | Kali 10.10.20.30 | Encender y lanzar `generar_campana.py --autorizado` | acceso Kali | Mark enciende; ejecución al autorizar A |

**La campaña A no está lista** mientras sigan abiertos 1–4. Los puntos 5–7 son del momento de ejecución.
