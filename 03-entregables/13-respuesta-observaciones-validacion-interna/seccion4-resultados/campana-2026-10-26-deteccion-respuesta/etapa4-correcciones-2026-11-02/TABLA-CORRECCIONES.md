# Correcciones de las herramientas de la Etapa 4: hallazgo, corrección, prueba, resultado y pendiente

«Offline» = probado en el portátil (Windows) y en el banco Docker Linux (`cyberflow-etapa2-banco:2`), sin tocar el
laboratorio. «En vivo» = solo se puede comprobar en el laboratorio, a partir de la 4A.

Versiones: producto `candidato/etapa3-20261102` @ **`f9cf801`** (herramientas) y **`3a9f26b`** (solo pruebas
después); código del producto = `ec78ca5` sin cambios (`git diff ec78ca5 3a9f26b` fuera de `scripts/etapa4`,
`deploy/etapa4` y `tests` vacío). Documentación: guiones de `etapa4-preparacion-2026-11-02/guiones/` y
`scripts-4c/generar_campana.py` (`99e6bdae…`).

## 1. Los cuatro defectos

| # | Hallazgo | Corrección | Prueba | Resultado offline | Pendiente en vivo |
|---|---|---|---|---|---|
| **1** | `salud_captura.py` `.1` clasificaba **C0** un periodo sin cobertura SIGUSR1 (caso reproducido: [10, 110] con lecturas solo en 0 y 120) | `.2`: `cobertura_tcpdump` exige lecturas que acoten los dos extremos (≤ 30 + 2 s), sin huecos interiores > 32 s, **un único PID**, contadores válidos y no decrecientes; cualquier fallo = **C3** (nunca C0). Anillo y vía rápida se clasifican por separado, nunca mezclados. Tolerancia declarada: 2 s sobre el periodo de 30 s del timer (`AccuracySec=1s`) | `tests/test_etapa4_salud_cobertura.py` (17) + `test_etapa4_salud_captura.py` (11) | 28/28 pasan con `.2`; **9 fallan** con la versión anterior (`evidencia/pruebas/regresion-cobertura-sobre-version-anterior-acc6588.txt`: 9 failed, 6 passed, 2 skipped) | Lecturas reales del journal con `sudo -n journalctl` para m4rk (4A); el timer `cf-tcpdump-estadisticas` aún no está instalado |
| **2** | La comprobación de sombra en srv-dmz se contaba a sí misma (el patrón `--aplicar` aparecía en su propio `sh -c`/`ssh`) y una lectura fallida acababa en 0 = «sombra» | `deploy/etapa4/srvdmz/estado_sombra.py`: identifica los agentes por ejecutable y argumentos (`/proc/<pid>/cmdline`), excluye su propio árbol y envoltorios; estados `sombra` (0), `aplicando` (1), `desconocido` (2), `sombra_no_conforme` (3). Una lectura fallida (procesos, systemctl, sudo, nft, traza) da `desconocido`, **nunca cero**. Lo usan `verificar_srvdmz.sh` y `g01` | `tests/test_etapa4_estado_sombra.py` (16); banco Docker `deploy/etapa4/banco/ensayo_estado_sombra.sh` S1–S10 (procesos reales, `sh -c`, SSH simulado y SSH real a localhost) | 16/16; banco 10/10 OK, con la regresión del patrón antiguo reproducida (`evidencia/banco/ensayo-estado-sombra.txt`) | Ejecutarlo en srv-dmz con `--alcance completo --respaldo` (4A, verificación; requiere el sudo NOPASSWD de `adminsrvdmz`, leído el 2-nov) |
| **3** | P1–P5 y X1–X3 no estaban conectados a la ejecución: la batería seguía aunque se cumpliera una pausa o una cancelación | `scripts/etapa4/vigia_4c.py` (bucle en el bastión + `sensor` de solo lectura) evalúa cada 60 s y escribe un **permiso** en la Kali (nonce de la corrida, válido 150 s). `scripts-4c/generar_campana.py` (`99e6bdae…`) lo exige antes del contexto y antes de lanzar cada episodio: pausa = termina el actual y espera; reanudar = ≥ 300 s limpios (+ ≥ 230 s de historia del motor si se reinició) y **el siguiente en el orden**; cancelar = ningún episodio más, rc 3 y causa en `marcas.jsonl`. Fallo cerrado: permiso ilegible, caducado, de otro nonce o anterior al arranque = pausa; 1 800 s sin permiso = cancelación. 25 episodios, semilla, orden y parámetros iguales (`plan_orden` idéntico, comprobado por AST); sin `--permiso` el generador se comporta como antes | `tests/test_etapa4_vigia_decision.py` (14) y `test_etapa4_compuerta_banco.py` (6, extremo a extremo con el generador real y comandos inofensivos: pausa y orden, cancelación X2, pérdida del canal, nonce ajeno, permiso anterior al arranque, sin permiso) | Linux Docker **64/64**; Windows 63 + 1 omitida (necesita `/proc`); carga concurrente 2 × 3 ejecuciones del banco: **6/6** (`evidencia/pruebas/`) | `g01` probado por componentes y `bash -n`, no de punta a punta en el laboratorio; copiar `scripts-4c/` a la Kali (PROTOCOLO-4C §5.2); `sudo -n journalctl` para m4rk; coste del `sensor` cada 60 s en el Sensor1; el canal SSH persistente con la Kali (cambio de protocolo, abajo) |
| **4** | `s50_analisis_e4.sh` y `r4.sh` tragaban errores: un paso fallido acababa con rc 0 y un `SHA256SUMS` «completo»; `r4` devolvía el rc de `tee` | `s50`: cada paso en subshell con `set -e -o pipefail`, dependencias declaradas (los dependientes se omiten), `ESTADO-PASOS.tsv`, `.pasos/<id>.sha256`, salidas fallidas apartadas en `.fallidos/`; rc global ≠ 0; `SHA256SUMS.PARCIAL` + `PARCIAL.txt`; `REANUDAR=1` reutiliza solo pasos verificados y para si se alteraron. `r4`: `pipefail` y rc de `ssh` vía `PIPESTATUS`, línea final `## r4 rc=…` | `tests/ensayo_errores_s50_r4.sh` (herramientas y ssh falsos): S1–S8, R1–R4, V1–V2 | Todas OK; V1–V2 reproducen el defecto en las versiones de `d3464bf` (`evidencia/banco/errores-s50-r4/`) | Ninguno propio: se ejecuta en la 4B/4C |

## 2. Otros cambios hechos al corregir

| Cambio | Motivo | Prueba |
|---|---|---|
| El generador con compuerta se publica en **`scripts-4c/`**; `scripts/generar_campana.py` sigue en `c586d813…` | No invalidar `MANIFIESTO-CAMPANA.json` ni la evidencia 3B, que citan `c586d813` | sha256 de ambos; `plan_orden` idéntico |
| **Canal de control persistente con la Kali** (ControlMaster, abierto por `g01`, cerrado por `b20`, cada uso en `accesos-kali.log`) | Sin canal no hay permiso; sustituye «ningún acceso a la Kali hasta `b20`» del 3B. Sus paquetes alimentan ventanas de la Kali en el motor (`--excluir` solo quita las ventanas de la entidad excluida): se publicará su volumen | Banco de la compuerta (con SSH simulado) |
| `b20` acepta rc 3 (cancelada), exige que el vigía haya terminado y cierra el canal | Coherencia con la compuerta | `bash -n` |
| `c03` comprueba 6 hashes y ausencia de permisos previos | No reutilizar permisos de otra corrida | `bash -n` |
| `s50` escribe `incrementos.jsonl` en su directorio de análisis | No mezclar con la salud de otra corrida | S1, S8 |
| Banco de la compuerta estable bajo carga (`3a9f26b`): validez 3 s en el banco, reintento de `os.replace` en el Kali simulado de Windows | En Windows `os.replace` sobre un fichero abierto da `PermissionError`; el generador lo trataba —bien— como pausa | 6/6 en carga concurrente |
| Paquete reconstruido: 85 ficheros, `426de9de…` | Herramientas nuevas | `evidencia/paquete/` |

## 3. Pruebas preexistentes que fallan en Windows (no relacionadas)

4 pruebas de la suite completa (`test_etapa2_correcciones` agente reintenta, `test_f1_preflight` bash_syntax,
`test_feed` genera_par_de_claves, `test_storage_audit`) fallan también sobre un extracto limpio de `acc6588`: son de
la plataforma, no de estas correcciones. En Linux (Docker, `--privileged`) la suite completa del producto en
`3a9f26b`: **708 passed, 2 skipped** (sin `node`; sin `tcpdump` en ese contenedor), en
`evidencia/pruebas/pytest-completo-linux-docker-3a9f26b.txt`.
