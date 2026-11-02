# Preparación de la Etapa 4 de CyberFlow (2 de noviembre de 2026)

> **Prepara y verifica; no inicia la Etapa 4 ni autoriza la campaña B.** Solo hubo lecturas del laboratorio (sin
> reinicios, instalaciones, enforcement, reglas, tráfico de prueba ni campañas) y pruebas offline en el portátil y en
> el banco aislado. No cambian el modelo, el escalador, las 28 características, los umbrales ni las reglas de
> detección. No se reabrieron los tres arreglos de la Etapa 3. No se editó el Word. La imagen Docker y la evidencia
> temporal se conservan.

## 1. Versiones

| Qué | Versión | Comprobado |
|---|---|---|
| Código que se instalaría | `ec78ca5` (`ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742`), rama `candidato/etapa3-20261102`, sin cambios | sin commits posteriores en el código del producto |
| Herramientas de la Etapa 4 (producto) | `acc6588` (`acc6588d7ab34f91f01c46e734d55d64c0bf5ccf`) en la misma rama: solo `scripts/etapa4/`, `deploy/etapa4/` y pruebas | `git ls-remote` = `acc6588…` |
| Documentación de partida | `4adfdf2` (cierre técnico de la Etapa 3) en `main` | |
| Entrega de partida | `../etapa3-cierre-tecnico-2026-11-02/` | corregida en este cierre (§4) |
| Lo desplegado hoy en Sensor1 | motor **24f8a80** + cadena v1 as-deployed **f57ca00**; `~/cyberflow` **no** es un checkout | [ESTADO-OBSERVADO](ESTADO-OBSERVADO-LABORATORIO.md) |
| `main` del producto | `7b275b8` (no es lo desplegado) | |

## 2. Contenido

| Documento | Qué es |
|---|---|
| [ESTADO-OBSERVADO-LABORATORIO.md](ESTADO-OBSERVADO-LABORATORIO.md) | Lecturas del 2-nov: unidades, procesos, disco frente a cargado, hashes de modelo/esquema/config/umbral, captura, cadena v1, relé, agentes, piloto-con-dns |
| [SALUD-CAPTURA.md](SALUD-CAPTURA.md) | Pérdida por fuente (anillo, archivador, vía rápida, Suricata, ens37, detector, SPAN), clases C0–C3 y criterios I/P/X fijados antes de medir |
| [PROCEDIMIENTO-ETAPA4.md](PROCEDIMIENTO-ETAPA4.md) | 4A: paquete, traslado, respaldos, instalación en sombra, verificación y reversión sin git |
| [PROTOCOLO-4B-CONTROL.md](PROTOCOLO-4B-CONTROL.md) | Control normal nuevo: 6 perfiles a factor 1,0, métricas M1 separadas |
| [PROTOCOLO-4C-CAMPANA-A.md](PROTOCOLO-4C-CAMPANA-A.md) | Campaña A nueva: 25 episodios, 7 configuraciones + vía rápida aparte, marcas de tiempo, escaneo breve contra la ráfaga real |
| [ORDEN-4C.md](ORDEN-4C.md) | Semilla 20261102, orden y horario estimado publicados antes |
| [OBSERVACION-DNS-ETAPA4.md](OBSERVACION-DNS-ETAPA4.md) | Observación DNS de 7 días, aparte y pasiva |
| [MATRIZ.md](MATRIZ.md) | pendiente → corrección → evidencia → estado |
| [CAMBIOS.md](CAMBIOS.md) | Nota de cambios de este cierre |
| `config-campana-4c.json`, `escenarios-4c.json`, `herramientas-e4.sha256` | Configuración de análisis, de la batería y hashes de las herramientas que se copian al sensor |
| `guiones/` | Guiones de 4B/4C/DNS (`r4.sh` + `b01 b20 c03 c05 d01 g01 k01 p10b s10 s20 s30 s40 s50`), todos LF, `bash -n` y shellcheck `-S warning` limpios |
| `evidencia/` | Lecturas del laboratorio, banco, paquete, salud en vivo (4 muestras de solo lectura), regresión de `control_4b.py` |

Herramientas nuevas o cambiadas en `../scripts/` (documentación): `calidad_fuentes.py` (`--duracion-pcap`),
`control_4b.py`, `referencia_trafico_4c.py`, con sus pruebas en `../tests/`.

## 3. Estado en una línea por fase

| Fase | Estado |
|---|---|
| 4A instalación en sombra | **Preparado y probado offline**; las fases con sudo, pendientes de ejecución por Mark |
| 4B control normal | **Preparado y probado offline** (regresión exacta contra el control del 3B) |
| 4C campaña A | **Preparado y probado offline** (orden, análisis, referencia de tráfico y `fin_ultimo` contra datos del 3B o sintéticos) |
| Observación DNS 7 días | **Preparado y probado offline** (`d01`); no iniciada |

## 4. Correcciones publicadas

- «Sensor1 ejecuta `7b275b8`» y «`git switch` en `~/cyberflow`»: falsas. Corregidas en ESTADO-OBSERVADO y con avisos
  en `../etapa3-cierre-tecnico-2026-11-02/` (README, MATRIZ, DEPENDENCIAS-Y-COMANDOS y PROCEDIMIENTO-ETAPA4, este
  último marcado como sustituido).
- «`kernel_drops` = 0 en el resumen de la vía rápida»: ese campo no existe. Corregido en SALUD-CAPTURA §1 y con aviso
  en la MATRIZ de la Etapa 3.
- «tcpdump solo informa al terminar», «ficheros de 15 s fijos», «número de PCAP = continuidad»: SALUD-CAPTURA §1.

## 5. Condiciones antes de instalar

Ninguna se da por cumplida con lo visto el 2-nov; se comprueban el día de la instalación.

| # | Condición | Quién / cómo |
|---|---|---|
| C1 | Mark pide la Etapa 4 por escrito (y, aparte, cada una de 4B, 4C y la observación DNS) | Mark |
| C2 | **piloto-con-dns** cerrado o declarado compatible. Su estado **no pudo demostrarse** (última fila 30-sep, sin acta de cierre): queda como requisito pendiente, sin asumir que terminó | Mark |
| C3 | Mark acepta los dos cambios de captura: anillo `-G 5` y `--disparo eventos` | Mark |
| C4 | Reglas nft efectivas de srv-dmz y de DC1 respaldadas, y `Defaults` de sudoers de srv-dmz leídos | Mark (sudo), PROCEDIMIENTO §3 |
| C5 | Respaldos **frescos** del día en sensor, srv-dmz y bastión, con sha256 | PROCEDIMIENTO §3 |
| C6 | Línea base SIGUSR1 del anillo real (≥ 30 min tras la 4A) | lo mido yo tras la 4A |
| C7 | Diagnóstico de las ráfagas de descartes de Suricata (S1: +3 316 en una hora el 2-nov) o riesgo declarado | lectura tras la 4A |
| C8 | `rx_dropped` de ens37 (crece +140/10 s): se informa sin clasificar | lectura |
| C9 | `mac_esperada` obsoleta en `cyberflow.local.toml` (`00:0c:29:15:7c:02` ≠ `00:0c:29:3d:f9:4e`): no la usa el motor, pero se declara y **no se toca** en la Etapa 4 | declarado |
| C10 | El SPAN no es visible desde el sensor: la pérdida del espejo no se mide; solo la cota `retraso_primer_paquete_s` | declarado |
| C11 | Observación DNS de 7 días antes de cualquier LIMIT DNS; TCP/53 fuera del LIMIT como limitación declarada | OBSERVACION-DNS |
| C12 | Intervalos de 4B y 4C fuera de la rotación diaria de `eve.json` (`logrotate.timer`) | lectura del día |
| C13 | Kali sin procesos de ataque y relojes sincronizados (desfase ≤ 0,1 s al empezar) | lectura del día |

## 6. ¿Se puede pedir la ejecución de la Etapa 4?

Está **lista para solicitarse la 4A**, no para ejecutarse sin más: el procedimiento, la reversión y los protocolos
están cerrados y probados offline, pero la instalación exige antes C1–C5 (dos de ellas solo las puede resolver Mark:
piloto-con-dns y los respaldos con sudo). La 4B y la 4C dependen además de la 4A cerrada y de C6–C7. Nada de esto
autoriza la campaña B.
