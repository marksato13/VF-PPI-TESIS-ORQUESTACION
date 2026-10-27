# Cierre operativo de la preparación — campaña A — 2026-10-27

Cierre sobre el commit `d58f5bac04c63f313e4935a2cde2ebb908a0577f`. **No se ejecutó ningún ataque ni
se inició la campaña.** No se tocó modelo, umbrales, escalador, heurísticos, política ni el Word.
Todo lo de abajo es **preparación/comprobación de entorno**, no episodios experimentales.

La evidencia cruda está en `evidencia-entorno-2026-10-27/` (ficheros 01–06) con `SHA256SUMS.txt`, y
los hashes de todos los entregables versionados en `MANIFIESTO-CAMPANA.json`.

## 1. Evidencia de comprobaciones (máquina · fecha · comando)

| # | Comprobación | Máquina / fecha (UTC) | Comando | Resultado |
|---|---|---|---|---|
| 01 | Relojes | BASTIÓN 10.10.10.30 · 2026-10-27 07:50 | `scripts/comprobar_relojes.sh` | chrony sync en bastión; sensor +0,18 s, srv-dmz +0,18 s, Kali +0,08…+0,24 s; inc < 0,27 s → **comparables** |
| 02 | Archivado real | captura SENSOR 10.10.60.11 · 07:52:47–07:53:17 | `cf-capturar /tmp/arch-…pcap 25` + tráfico Kali+bastión | **226 paquetes / 35.176 bytes** (antes: 24 bytes, 0 paquetes); 0 drops |
| 03 | Telemetría endpoint/DNS/extractor | SENSOR · 07:56 (eventos 07:52–07:53) | `grep eve.json` + `systemctl start cyberflow-acumular` | http 401/401/200 en :18081; dns `*.lab-ppi` NOERROR; acumulador 07:53:00 → `http_req60=12 authfail=0,50`, `dns_q60=6 uniq=0,50` |
| 04 | Multi-entidad (no solo-Kali) | SENSOR · 07:58 | conteo `entity_ip` en acumulador + `grep -c src_ip` en eve | **30 entidades** distintas; decenas de miles de eventos no-Kali; Kali = 1 de 30 |
| 05 | Modo sombra (estado + procedimiento) | SENSOR + srv-dmz · 08:00 ; arnés en LAPTOP | solo-lectura `systemctl`/`nft` + `tests/test_sombra.sh` | motor **sin `--enforce`**; agente active+enabled; sets **vacíos**; arnés **11/11** |
| 06 | Config Suricata efectiva | SENSOR · 08:05 | `sha256sum suricata.yaml` + `grep 18081` | `8e084b7d…efa04`; `detection-ports dp "80, 18081"`; Suricata 7.0.3 activo |

## 2. Archivado con tráfico benigno real

La prueba anterior (24 bytes) no contenía paquetes. Con el procedimiento que sí puedo ejecutar con mis
permisos (`cf-capturar` vía NOPASSWD en el sensor) y generando tráfico benigno real desde la Kali
(http 401/200 + dns `lab-ppi`) y desde el bastión (control-normal no-Kali), la captura recoge **226
paquetes legibles, 0 descartados**. La continuidad **no** se declara por que el fichero exista: se
comprueba con el conteo de paquetes, el tamaño y los eventos. La cobertura abarca control normal de
**toda la red** (30 entidades en el acumulador, eve con orígenes no-Kali) **más** el tráfico de
ensayo; **no** queda limitada a la Kali (el filtro solo-Kali afecta únicamente al pcap de `cf-capturar`,
no a eve ni al acumulador). EVE, decisiones del motor, features y scores quedan preservados (03/04).

## 3. Modo sombra sin ataques

Estado real (solo-lectura): el **motor** (`ppi-motor`, sensor) corre **sin `--enforce`** → no aplica
enforcement directo, solo emite al feed; el **agente** (`ppi-enforce-agent.timer`, srv-dmz) está
active+enabled (enforcement vivo) y los sets `cyberflow_bloqueados`/`cyberflow_limitados` están
**vacíos**. El **procedimiento revisado** (`modo_sombra.sh` → detener+enmascarar el agente, vaciar sets,
verificar vacíos, fallo-seguro; `restaurar_enforcement.sh` → restaurar exigiendo `--escalada-revisada`)
se verificó de extremo a extremo con el arnés de inyectables (**11/11**). **No se aplicó en producción**
durante la preparación: la sombra definitiva se activa al **inicio de A** y se deja el enforcement **vivo**
como estaba.

## 4. Unificación de config y documentos

- **`infra-2026-10-27/README-EVIDENCIA-INFRA.md`**: T3 pasa de "telemetría HTTP ⬜ pendiente" a **✅ resuelta**
  (causa: `detection-ports`, no `HTTP_PORTS`).
- **`config-campana.json`**: la precondición de A cambia la alternativa vieja *"detener solo el publicador"*
  por el **procedimiento de agente revisado** (`modo_sombra.sh --ejecutar --motor-verificado` + restauración).
- **`evidencia-entorno-2026-10-27/06-suricata-config.txt`**: registra el `suricata.yaml` efectivo con **hash,
  comprobación y reversión** tras añadir 18081.
- Se quitaron las afirmaciones anticipatorias (`escenarios.json`, `ESTADO-ENTORNO`): ya **no** se afirma que
  un escenario "disparará `brute_force`" ni "`dns_entropy`"; solo se afirma la **telemetría verificada**, y se
  dice explícitamente que **la detección se mide en la campaña**.
- Se mantiene la **salvedad del escaneo bajo pfSense** (solo :80/:443 abiertos a la Kali) sin tocar reglas
  para favorecer la detección.

## 5. Requisitos: ya comprobado vs. re-verificar al inicio de A

| Requisito | Estado en preparación | Al **inicio de A** |
|---|---|---|
| Relojes | comparables 27-oct (01) | **re-verificar** (medir offset Kali/sensor justo antes) |
| Captura activa | `cf-capturar` probado, 226 pkts (02) | **re-verificar** (arrancar captura continua por episodio) |
| Historia previa | N/A en preparación | **re-verificar** (≥120 s de contexto antes de cada episodio) |
| Modo sombra | estado real + procedimiento 11/11 (05) | **aplicar** `modo_sombra.sh --ejecutar --motor-verificado` y re-verificar sets vacíos |
| DNS `lab-ppi` / egress 0 | cerrado (T2) | ya hecho (monitorizar egress) |
| Endpoint 18081 + parseo HTTP | cerrado (T3 / 06) | ya hecho (comprobar hashes de código en sensor) |
| Hashes de código desplegado | registrados en `config-campana.json` | **re-verificar** contra el sensor justo antes |

## 6. ¿Preparado para el prompt 2?

**Sí, el entorno está preparado** para recibir el prompt 2 (ejecución de la campaña A). Lo que **falta**,
y es deliberado, son los pasos que **solo** se hacen al arrancar A: (a) aplicar el modo sombra en srv-dmz y
confirmar sets vacíos; (b) arrancar la captura continua y re-confirmar el reloj de la Kali; (c) re-verificar
los hashes del código desplegado en el sensor; (d) lanzar el generador con `--autorizado`. Ninguno de esos
pasos se ejecuta ahora. No queda **ningún bloqueante** de entorno.
