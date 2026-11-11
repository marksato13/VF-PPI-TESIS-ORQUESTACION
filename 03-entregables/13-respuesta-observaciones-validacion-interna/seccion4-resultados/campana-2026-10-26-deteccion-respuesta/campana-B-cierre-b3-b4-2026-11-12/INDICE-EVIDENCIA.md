# Indice de evidencia de la Campana B (B3 + B4)

Commit base del repositorio: `f8cef33a470b983cdb93115b6c63543572fd1472`. Este indice liga cada resultado del paquete con su criterio escrito, la version del analizador y la evidencia original. Las copias de trabajo (`cf-b3`, `cf-b4`) estan **fuera del repositorio** (rutas cortas por el limite de Windows) y no se publican.

## A. Originales y su referencia (NO incluidos en el paquete)

| Tramo | Evidencia | Copia local de trabajo (no versionada) | sha256 |
|---|---|---|---|
| B3 | marcas_generador | `kali/corrida/marcas.jsonl (copia en bastion/corrida/marcas.jsonl)` | `1d129f0b1139dd13e2157f73e3957547895b265c045cad109ff1daa25971ddc1` |
| B3 | traza_agente_srvdmz | `cf-b3-agente.jsonl (srv-dmz traza-B-20261111T060906Z.jsonl)` | `82daf2e977071a6567017b6658031282e4bd259fec2c2aba89f16f9c7f163faf` |
| B3 | lecturas_set | `cf-b3-set-lecturas.jsonl` | `ecdc5459977c95e5ff07b4f1779d87281a741a10103624a6088fd09250f942a5` |
| B3 | traza_publicador | `evid/traza.jsonl` | `be9eebe6f870b8d4a463a5af7aecd1f1b37b603807affae334a33b9385ae789a` |
| B4 | marcas_generador | `kali/corrida/marcas.jsonl` | `9e9c95efa9a2b5847b70bca556bbb8fb81b83918864cfb31ff46124d044e747f` |
| B4 | traza_agente_srvdmz | `agente-B4.jsonl (srv-dmz traza-B-20261111T171449Z.jsonl)` | `29b23eb528335daa3ab3f2b446e3004feede07574adeae2b5bdd72d5a88957d4` |
| B4 | lecturas_set | `set-lecturas.jsonl` | `e03a1b734ad5ae7a4a0a39a702d7376e6a19bd0663b25c7d4a779d7231c8b187` |
| B4 | traza_publicador | `evid/traza.jsonl` | `0efb6a3869f3b195f565a623a4f18e22bbda98e9295fa63b99b04e97b6834411` |
| B3 | resultado-b3.json (analisis) | `resultados/resultado-b3.json` | `f2fed429d108c6b798c1c2ac47aba8f3c121f328f02d38c40087ca251b4722c0` |
| B4 | resultado-b4.json (analisis) | `resultados/resultado-b4.json` | `84acc013fa0e1f2c1b5d07363d05425b5d1a26dbfef5559cc8b1f553c2af5244` |
| B3 | PCAP crudos (514) | `<carpeta de trabajo B3>\pcap\` | manifiesto `manifiestos/pcap-B3.sha256` |
| B4 | PCAP crudos (2343) | `<carpeta de trabajo B4>\pcap\` (tar `pcap.tar` sha `2118d534fab12ea57b1e4ded412161682627564a39fddafcfc108861e944b239`) | manifiesto `manifiestos/pcap-B4.sha256` |
| B3+B4 | clientes, intentos y salidas (55 ficheros) | `cf-b3-clientes`, `cf-b4\clientes`, `kali\intentos`, `kali\corrida\salidas` | `manifiestos/evidencia-local-clientes-intentos-salidas.sha256` |

## B. Originales en los hosts del laboratorio (rutas; no incluidos)

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
| Campana A | bastion | `~/cf-e4/4c-A-completa-20261110T1033Z` y las canceladas `4c-cancelada-20261109T1058Z`, `4c-x3-cancelada-20261109T1350Z`, `4c-x3b-cancelada-20261109T1625Z` | antecedente en sombra

## C. Referencias al criterio escrito

| Indicador | Criterio | Version |
|---|---|---|
| E1 | OBJETIVOS-Y-CRITERIOS.md fila E1 (linea 93) @ blob 888f66482572 | `OBJETIVOS-Y-CRITERIOS.md` en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` (commit base `f8cef33`, blob `888f66482572`) |
| E2 | OBJETIVOS-Y-CRITERIOS.md fila E2 (linea 94) | `OBJETIVOS-Y-CRITERIOS.md` en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` (commit base `f8cef33`, blob `888f66482572`) |
| E3 | criterios/CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md + OBJETIVOS fila E3 (linea 95) | `OBJETIVOS-Y-CRITERIOS.md` en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` (commit base `f8cef33`, blob `888f66482572`) |
| E4 | OBJETIVOS-Y-CRITERIOS.md fila E4 (linea 96) | `OBJETIVOS-Y-CRITERIOS.md` en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` (commit base `f8cef33`, blob `888f66482572`) |
| E5 | OBJETIVOS-Y-CRITERIOS.md fila E5 (linea 97) | `OBJETIVOS-Y-CRITERIOS.md` en `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` (commit base `f8cef33`, blob `888f66482572`) |

**Donde consultar OBJETIVOS-Y-CRITERIOS.md:** ruta `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md` en el commit `f8cef33a470b983cdb93115b6c63543572fd1472` (ya en `origin/main`). La ultima modificacion del fichero es el commit `8ad1984` («Etapa 1 v3»); el contenido (blob `888f66482572b495dbc921a095251206898f7074`) es el mismo en `8ad1984` y en el commit base. Enlace: https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/blob/f8cef33a470b983cdb93115b6c63543572fd1472/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md

## D. Version de los analizadores (sha256 de los 16 primeros caracteres; completo en `SHA256SUMS`)

| Fichero | sha256 |
|---|---|
| `analisis/analizar_b.py` | `611d4b166214fed9` |
| `analisis/analizar_b_instrumentado.py` | `6d74bd9b7b4fd042` |
| `analisis/analizar_intentos.py` | `687a1e1e8823d824` |
| `analisis/lector_pcap.py` | `7df746cb23c80d11` |
| `analisis/analizar_b3.py` | `188c85bd06e84449` |
| `analisis/analizar_b4.py` | `700e0af48ff48a0c` |
| `analisis/e1_por_destino.py` | `28ec88c088a41c58` |
| `analisis/aplicar_e1_destino_25.py` | `371d05dd438c8083` |
| `analisis/test_e1_por_destino.py` | `2bab553080d574c0` |

## E. Trazabilidad por episodio

Cada fila de `resultados/resultados-por-episodio.csv` (y `.json`) lleva: tramo y `corrida_id`; criterio (`criterio_E1`, `criterio_E3`); analizador y version (`analizador`, `analizador_E1_reanalisis`); hashes de la evidencia de su tramo (`evidencia_marcas_sha256`, `evidencia_traza_agente_sha256`, `evidencia_set_lecturas_sha256`) y el manifiesto de PCAP; y, por indicador, el resultado con su evidencia o el motivo de indeterminacion o no aplicabilidad.

## F. Exclusiones

No se incluyen: PCAP crudos (3,x GB; solo manifiestos con hash), credenciales y claves SSH (los scripts solo citan nombres de ruta, ningun valor), registros de acceso a hosts (`accesos-kali.log`), journals, trazas del agente y salidas del generador en bruto (se referencian por hash). El historial cita rutas de los hosts del laboratorio, que son informacion de laboratorio aislado.
