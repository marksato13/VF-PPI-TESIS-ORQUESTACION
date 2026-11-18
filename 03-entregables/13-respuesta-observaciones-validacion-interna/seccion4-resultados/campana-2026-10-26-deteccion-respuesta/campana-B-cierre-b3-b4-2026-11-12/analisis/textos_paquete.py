README = """# Paquete de cierre de la Campana B (B3 + B4), 12-nov-2026

Cierra la Campana B como **dos tramos de los 25 episodios previstos**: **B3** (episodios 1-6) y **B4** (episodios 7-25). Branch local `campana-b-cierre-b3-b4`, commit base `@BASE@`. Ruta del paquete: `@REL@/`. **No publicado** (push pendiente de revision).

## Que contiene
| Ruta | Contenido |
|---|---|
| `CONSOLIDADO-25-EPISODIOS.md` | Tabla de los 25 episodios (tramo, estados, E1-E5), denominadores, los ocho `incompleto_timeout`, motivos de indeterminacion de E3 y de no aplicabilidad, cobertura por familia y limitaciones abiertas |
| `HISTORIAL-CAMPANA-B.md` | Corridas, ensayos y correcciones con sus nombres e IDs reales (incluida B1 y B2): que se probo, por que se detuvo, donde esta la evidencia |
| `balances/` | `BALANCE-B3-PARCIAL.md` y `BALANCE-B4.md` **originales** (B4 hasta su cierre tecnico y analisis del 12-nov; la parte anadida despues esta en `reanalisis/`) |
| `reanalisis/` | Reanalisis de E1 por destino bajo el criterio vigente, con pruebas, regresion y trazabilidad por episodio; evidencia complementaria de E3 (no formal) |
| `resultados/` | `resultados-por-episodio.csv/.json` (los 25, con E1-E5, evidencia o motivo, criterio, version del analizador y hashes), salidas crudas de los analizadores y del reanalisis |
| `criterios/` | Criterio E3 fijado el 11-nov y sus antecedentes; limitacion del generador de inundacion. El criterio E1-E5 de origen es `OBJETIVOS-Y-CRITERIOS.md` (ya versionado; ver `INDICE-EVIDENCIA.md`, seccion C) |
| `analisis/` | Scripts y pruebas de los analizadores y del reanalisis, y el constructor de este paquete |
| `pruebas/` | Ejecucion de las pruebas al construir el paquete, y lo que no se pudo re-ejecutar |
| `manifiestos/` | Hashes de los PCAP crudos (@N3@ de B3, @N4@ de B4) y de clientes/intentos/salidas; los PCAP **no** estan en el paquete |
| `INDICE-EVIDENCIA.md`, `SHA256SUMS` | Indice con hashes y referencias a los originales; suma de verificacion de este paquete |

## Reglas aplicadas
- **Balances originales conservados**; E1 por destino es un **reanalisis** bajo el criterio vigente, con su codigo y pruebas.
- **Veredictos formales de E3 sin cambios** (5 cumple, 15 indeterminado, 5 no aplica) y **ocho `incompleto_timeout` conservados**.
- **Limitacion abierta:** discrepancia entre el SPAN y los contadores de srv-dmz. El ensayo del contador y la repeticion de los escaneos quedan **fuera del alcance** de este cierre.
- Excluidos: PCAP crudos, credenciales, registros sensibles (ver `INDICE-EVIDENCIA.md`, seccion F).

## Verificar
Desde esta carpeta: `sha256sum -c SHA256SUMS`. Los scripts de `analisis/` usan rutas absolutas del equipo de trabajo (`C:\\Users\\markp\\cf-b3`, `cf-b4`) para leer las copias locales de la evidencia; no se ejecutan sin ellas.
"""

INDICE_CAB = """# Indice de evidencia de la Campana B (B3 + B4)

Commit base del repositorio: `@BASE@`. Este indice liga cada resultado del paquete con su criterio escrito, la version del analizador y la evidencia original. Las copias de trabajo (`cf-b3`, `cf-b4`) estan **fuera del repositorio** (rutas cortas por el limite de Windows) y no se publican."""

INDICE_HOSTS = """## B. Originales en los hosts del laboratorio (rutas; no incluidos)

| Tramo | Host | Ruta | Referencia |
|---|---|---|---|
| B3 | Sensor1 | `~/cf-e4/4c-B3-parcial-6ep-20261111T0620Z` | PCAP, EVE, motor, salud, copias definitivas |
| B3 | bastion, clientes | `~/cf-e4/4c-B3-parcial-6ep-20261111T0620Z` | vigia, compuerta D5, marcas / transacciones por perfil |
| B3 | Kali | `~/cf-e4-4c-B3-parcial-6ep-20261111T0620Z/` | `corrida/marcas.jsonl` sha256 `1d129f0b1139dd13e2157f73e3957547895b265c045cad109ff1daa25971ddc1`, intentos con hora |
| B3 | srv-dmz | `/var/lib/cyberflow/agente/traza-B-20261111T060906Z.jsonl`; `/var/lib/cyberflow/reversion-B/PRE-B-20261111T051804Z`; `.../EVIDENCIA-ANTES-REVERSION-20261111T060850Z` | traza del agente, respaldo previo, estado antes de revertir |
| B4 | Sensor1 (3,9 GB), bastion, clientes | `~/cf-e4/4c-B4-completa-19ep-20261111T1740Z` | s40 `COPIAS-COMPLETAS.ok` (7.325 PCAP, 0 FALLO/PERDIDO) |
| B4 | Kali | `~/cf-e4-4c/` (`corrida/`, `intentos/`) | `corrida/marcas.jsonl` sha256 `9e9c95efa9a2b5847b70bca556bbb8fb81b83918864cfb31ff46124d044e747f` |
| B4 | srv-dmz | `/var/lib/cyberflow/agente/traza-B-20261111T171449Z.jsonl` (+`.sha256`); `~/cf-b/set-lecturas-B4-20261111T1740Z.jsonl` sha256 `e03a1b734ad5ae7a4a0a39a702d7376e6a19bd0663b25c7d4a779d7231c8b187`; `/var/lib/cyberflow/reversion-B/PRE-B-20261111T135620Z` | traza de la corrida (375 aplicaciones), muestreo del set, respaldo previo |
| B1 | Sensor1 / Kali / bastion / srv-dmz | `~/cf-e4/4c-B-cancelada-X3-completo-20261110T1615Z` / `~/cf-e4-4c-B-cancelada-X3-20261110T1626Z` / `~/cf-e4/4c-B-cancelada-X3-20261110T1626Z` / `traza-B-20261110T161315Z.jsonl` | corrida cancelada por X3; **no** aporta episodios al consolidado |
| B2 | Sensor1 / Kali / bastion / srv-dmz | `~/cf-e4/4c-B2-cancelada-X1-completo-20261110T1833Z` y `...-20261110-175000-183200` / `~/cf-e4-4c-B2-cancelada-X1-20261110T1832Z` / `~/cf-e4/4c-B2-cancelada-X1-20261110T1832Z` / `traza-B-20261110T183104Z.jsonl` (+`.sha256`) | corrida cancelada por X1; **no** aporta episodios al consolidado |
| Campana A | bastion | `~/cf-e4/4c-A-completa-20261110T1033Z` y las canceladas `4c-cancelada-20261109T1058Z`, `4c-x3-cancelada-20261109T1350Z`, `4c-x3b-cancelada-20261109T1625Z` | antecedente en sombra"""

HISTORIAL = """# Historial de la Campana B: corridas, ensayos y correcciones

Campana B = respuesta real con el agente `--aplicar` **solo sobre la Kali 10.10.20.30** (acciones BLOCK/LIMIT en srv-dmz 10.10.30.10), 25 episodios previstos (5 por familia). Horas en UTC (Peru = UTC-5). Los nombres de carpeta y los IDs son los reales de los registros.

## 0. Antecedente: Campana A (sombra, sin `--aplicar`)
| Corrida | ID (nonce) | Resultado | Por que se detuvo |
|---|---|---|---|
| `4c-cancelada-20261109T1058Z` | `4c-20261109T093448Z-96a2520f2a6d` | cancelada con 6 episodios | X1: 6 episodios en C2/C3 > 20 % de 25 |
| `4c-x3-cancelada-20261109T1350Z` | `4c-20261109T121126Z-05ed6aa511c8` | cancelada con 8 episodios | X3: trafico de la Kali a 10.10.10.21:53 (dns) durante un episodio |
| `4c-x3b-cancelada-20261109T1625Z` | `4c-20261109T150419Z-a95a5acb0f39` | cancelada con 10 episodios | X3: trafico de la Kali a 10.10.10.30:41410 (flow) durante un episodio |
| `4c-A-completa-20261110T1033Z` | `4c-20261109T215425Z-3bf15267cb93` | **completa, 25/25** (09-nov 21:57-23:50Z) | -- (en esta corrida los escaneos duraron 4,6-5,0 s y 52-53 s: referencia sin restriccion) |

## 1. Corridas de la Campana B
| Corrida | ID (nonce) | Fechas (UTC) | Episodios | Resultado | Por que se detuvo | Evidencia |
|---|---|---|---|---|---|---|
| **B1** (primera ejecucion) | `4c-20261110T154043Z-efa28e2dd8f0` | 10-nov 15:41:08Z (2.o intento de `g01b`, hash `51fe3472505ad8fa`) - 16:09:43Z; primer episodio `inundacion_http-r4` 15:45:00,80Z | 5 de 25 completos | cancelada | X3 original: el vigia cancelo por un flujo de la Kali a 200.25.3.17:123 (sincronizacion horaria `systemd-timesyncd`, 1 paquete y 94 B por sentido, unico flujo fuera de la lista blanca). El 1.er `g01b` (15:39:47Z) paro antes de lanzar: `ppi-brute-lab` inactivo | `~/cf-e4/4c-B-cancelada-X3-20261110T1626Z`; PRE-B `PRE-B-20261110T153859Z`; `traza-B-20261110T161315Z.jsonl`. **Separada; no aporta episodios al consolidado** |
| **B2** (repeticion) | `4c-20261110T175110Z-0dd27945608f` | 10-nov 17:51-18:28Z (ronda de X1 18:28:10Z; cancelacion del generador 18:28:40Z, rc 3; el episodio 7 no se lanzo); reversion 18:31Z | 6 | cancelada | X1: 6 episodios en C2/C3 (los seis en **C3** por el reinicio del publicador que provocaba la limpieza de D5, Hallazgo 1) | `~/cf-e4/4c-B2-cancelada-X1-20261110T1832Z`; PRE-B `PRE-B-20261110T175033Z`; `traza-B-20261110T183104Z.jsonl`. Resultados historicos: E1 6/6, E2 4/4 (DNS sin punto de aplicacion), E3 fuerza bruta 2/2 cumple y **inundacion 2/2 indeterminado**, E4 no evaluable (sin registro por transaccion), E5 4/4. **No aporta episodios al consolidado** |
| **B3** | `4c-20261111T051928Z-2eb2f728a738` | 11-nov; control [04:45, 05:15Z]; PRE-B `PRE-B-20261111T051804Z`; `--aplicar` 05:18:35Z; `g01c` 05:19:41Z; episodio 1 05:23:38Z; alarma 05:58Z; cierre 06:09-06:20Z | **6** (episodios 1-6), todos completos, clase C0 | cancelada por decision de Mark tras el episodio 6 | La puerta D5 se bloqueo tras `inundacion_http-r3` (fin 05:55:37Z): `descartes_limite` (contador de instrumentacion, no una restriccion) se contaba como «presente». Falso positivo de diseno; no habia restriccion real. Se reviso y se revirtio | `~/cf-e4/4c-B3-parcial-6ep-20261111T0620Z` (5 hosts); marcas sha256 `1d129f0b...`. **Tramo B3 del consolidado** |
| **B4** | `4c-B4-20261111T135745Z-b0ec7e96836a` | 11-nov; control [08:15, 08:45Z] declarado 08:11:36Z; PRE-B `PRE-B-20261111T135620Z`; `--aplicar` 13:57:16Z; `g01d` 13:57:58Z; episodio 7 (`fuerza_bruta_http-r1`) 14:01:55,47Z; ultimo fin 17:09:07,7Z; reversion 17:14:55Z; `s40` 17:39Z | **19** (episodios 7-25), 11 completos y 8 `incompleto_timeout`, clase C0 | completa (`campana_fin: completa`, X1 0/19) | -- | `~/cf-e4/4c-B4-completa-19ep-20261111T1740Z` (Sensor1, bastion, clientes); marcas sha256 `9e9c95ef...`. **Tramo B4 del consolidado** |

B4 se lanzo como **corrida nueva** (no reanudacion de B3): `generar_campana_b.py` `0705751a...` con `--desde-episodio fuerza_bruta_http-r1`, `CF_PLANIFICADOS=19`, `g01d` (sha `81dd7003...`). Entre el control de B4 (terminado 08:45Z) y el lanzamiento (13:57Z) los servicios de medicion siguieron en marcha sin reinicios ni huecos; la interrupcion fue de las herramientas de trabajo, no del laboratorio.

## 2. Ensayos y correcciones (orden cronologico)
| Fecha | Que se probo | Resultado y por que se detuvo | Evidencia |
|---|---|---|---|
| 10-nov | Excepcion de X3 para el NTP de la Kali (aprobada 16:30:05Z): vigia `generador/vigia_4c_b.py` `a4b64381fc54313f...`, `--ntp-permitido 200.25.3.17` | 21 + 2 pruebas, 12/12 mutaciones; usada en B2-B4 | `REGISTRO-EXCEPCION-X3-NTP.md` (carpeta de trabajo) |
| 10-nov | Revision de la evidencia de B2 (PCAP 503/503, clientes, Kali, srv-dmz, relojes, E5) | Cerrada; E1 por paquetes verificado 6/6 | `revision-evidencia-b2\\` (carpeta de trabajo) |
| 10-11-nov | D5 sin reinicio del publicador (propuesta de banco): systemd 257 en contenedor, auditoria rotable con logrotate real, simulador, integracion; 134 pruebas, mutaciones | Pasan en banco; ejecucion diaria de logrotate **aun sin observar** (proxima 12-nov 00:00Z) | `propuestas\\d5-sin-reinicio\\` (carpeta de trabajo) |
| 11-nov | Criterio E3 fijado antes de lanzar (SPAN o salida; K=5 LIMIT, K=3 BLOCK; theta 0,5; B0 10 bloques previos; BLOCK = SPAN unica fuente por decision de Mark) | Vigente; no se cambia durante ni despues de la corrida | `criterios/CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md` |
| 11-nov 03:49Z | Ensayo de la puerta D5 (`ensayo-puerta-20261111T034919Z`) | Duracion 104,7 s desde el fin simulado (espera 75,0 s + puerta 29,7 s); hueco minimo entre episodios 210 s -> margen 105,3 s | carpeta de trabajo |
| 11-nov (B3) | Falso bloqueo de la puerta tras el episodio 6 | Causa: el D5 original contaba `descartes_limite` como restriccion. Se conservo B3 como parcial y se preparo la correccion en banco (`d5_episodio_corregido.py` `00c1bb29...`; derivado de banco `58f715e2...`; falla cerrado) | `balances/BALANCE-B3-PARCIAL.md`; `propuestas\\d5-descartes-limite\\` |
| 11-nov 06:55Z | Ensayo de laboratorio 1 del D5 corregido (rafaga 60 s) | **Inconcluso**: el LIMIT llego a +55 s y las renovaciones del agente destruyen la entrada de `descartes_limite`; la puerta no se ejecuto | pasos 17-20 de `corrida-2026-11-11\\` |
| 11-nov 07:16Z | Ensayo de laboratorio 2 (rafaga 120 s) | **Inconcluso** por lo mismo; revertido 07:16:45Z | pasos 22-24 de `corrida-2026-11-11\\` |
| 11-nov 07:27Z | Ensayo por inyeccion 1 (un LIMIT por `cf-nft-helper`, agente en sombra, rafaga 3 s) | Estado reproducido (Kali en `limitados` y `descartes_limite`) pero **puerta no validada**: `lista=false`. Causa: en el camino real `SshRunners.srv` ejecutaba en srv-dmz el `d5_episodio.py` **original**; el corregido solo estaba en el bastion. Revertido 07:27:55Z | `corrida-2026-11-11\\prueba-lab-d5-inyeccion\\` |
| 11-nov | Correccion del camino SSH | `d5_episodio_corregido.py` desplegado en srv-dmz como archivo separado (original `85c71124...` intacto); `lanzador_puerta_banco.py` `4600b8b8...` con `--remoto-srv`; `g01d` `81dd7003...`; preflight v5 (37 OK / 0 FALLAN / 1 PENDIENTE: logrotate diario); `test_srv_remoto_ssh.py` (4 pruebas) | `paquete-despliegue-r2\\` (carpeta de trabajo) |
| 11-nov 07:38Z | Ensayo por inyeccion 2 (mismo procedimiento, una sola vez) | **Valido**: retirada de la restriccion, `descartes_limite` conservado, `lista=True`, publicador con el mismo PID 2115304 y NRestarts 0; revertido 07:39:12Z, sombra verificada | `corrida-2026-11-11\\prueba-lab-d5-inyeccion-2\\` |
| 12-nov | Consolidado de 25 episodios y E1 por destino | E1 25/25 verificado bajo el criterio literal; E3 sin cambios | `reanalisis/`, `CONSOLIDADO-25-EPISODIOS.md` |

## 3. Limitaciones abiertas (declaradas, sin ensayo en este cierre)
1. **SPAN frente a contadores de srv-dmz:** el contador del elemento cuenta mucho menos que el SPAN (5-20 % en escaneos, ~50 % en fuerza bruta, con cota superior por reinicios). Sin explicar.
2. **E3 de los 10 escaneos:** indeterminado por el criterio fijado; la evidencia complementaria no es formal.
3. **Los 8 escaneos `incompleto_timeout`:** la causa interna en `nmap` no se observo; el contraste con la Campana A indica que el BLOCK alarga el escaneo 1-2 ordenes de magnitud.
4. **Logrotate diario** de la auditoria: sin observar.
"""
