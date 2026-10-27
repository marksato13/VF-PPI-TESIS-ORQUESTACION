# Campaña nueva — detección (4.2) y respuesta (4.4)

**Fase: preparación endurecida. No se ha ejecutado ningún ataque ni la campaña.** La campaña A se autoriza en la
instrucción siguiente. Correcciones sobre `b59c6c8` descritas en `MATRIZ-OBSERVACIONES.md`.

Carpeta independiente: no modifica `../4.2-ablacion/aporte-componentes-r2-2026-10-26/` ni ninguna evaluación anterior.

## Contenido

| Archivo | Contenido |
|---|---|
| `PLAN-CAMPANA.md` | Plan A/B, historia/registros, marcas, criterios, **secuencia prep→ejecución→restauración**, estados de madurez |
| `config-campana.json` | Configuración congelada: modelo+hashes, umbrales, 28 características, lógica de combinación, `logged_at` vs `window_end`, relojes/DNS medidos |
| `escenarios/escenarios.json` · `FICHAS-ESCENARIOS.md` | Escenarios v2 (tipos separados, tasas fijas, pendientes explícitos) |
| `scripts/esquema_campana.py` | Esquema + validación + construcción de comandos |
| `scripts/generar_campana.py` | Generador (Kali): valida, simula por defecto, inicio/fin separados, mata el grupo en timeout |
| `scripts/analizar.py` | Analizador: clasifica por `logged_at`, separa emitido/derivado, Tabla 8, control FPR, calidad de datos |
| `scripts/capturar.sh` · `estimar_espacio.sh` | Captura continua (ens37) y estimación de espacio |
| `scripts/comprobar_relojes.sh` | Desfase por host, antes y después |
| `scripts/modo_sombra.sh` · `restaurar_enforcement.sh` | Sombra para A y restauración exacta (ejecutables con `--ejecutar`; no aplicados aún) |
| `scripts/endpoint_brute/` | Endpoint 401 correcto (`app.py`, unidad systemd, README con nginx y Suricata) |
| `tests/test_herramientas.py` · `tests/fixtures.py` | Verificación sin ataques (33 comprobaciones) |
| `RELOJES-DNS.md` | Relojes y DNS medidos + pasos administrativos |
| `MATRIZ-OBSERVACIONES.md` | Observación → corrección → archivo → comprobación → estado |
| `RESULTADOS-VERIFICACION.md` | Resultados de las verificaciones sin ataques |
| `COMPROBACIONES-PREVIAS.md` | Comprobaciones benignas y bloqueos |
| `evidencia-precheck/` · `MANIFIESTO-CAMPANA.json` | Evidencia cruda y hashes |

## Estado por pieza (documentado / implementado / probado aislado / verificado en entorno)

- Generador, esquema, analizador, endpoint: **implementados y probados de forma aislada** (33 comprobaciones + CLI + loopback).
- Muerte del grupo de procesos: **probada** en Windows y **verificada en el entorno** (sonda `killpg` en el sensor).
- `logged_at` como hora de emisión, desfase del sensor (−47,55 s), egress del DNS, interfaz de captura (ens37): **verificados en el entorno**.
- Scripts de sombra/restauración y captura: **implementados**; **no aplicados** al entorno (por indicación).
- Endpoint en srv-dmz, zona DNS local, sincronización del sensor: **documentados**, pendientes de ejecución.

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
