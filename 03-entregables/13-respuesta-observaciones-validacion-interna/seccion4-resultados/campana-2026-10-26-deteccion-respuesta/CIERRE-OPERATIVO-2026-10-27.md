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
| 02 | Archivado (mecanismo) | captura SENSOR 10.10.60.11 · 07:52:47–07:53:17 | `cf-capturar /tmp/arch-…pcap 25` + tráfico Kali+bastión | mecanismo OK **226 pkts / 0 drops** (antes 24 B); pero **solo-Kali** (`host 10.10.20.30`) → NO es el archivo de la campaña (ver 07) |
| 03 | Telemetría endpoint/DNS/extractor | SENSOR · 07:56 (eventos 07:52–07:53) | `grep eve.json` + `systemctl start cyberflow-acumular` | http 401/401/200 en :18081; dns `*.lab-ppi` NOERROR; acumulador 07:53:00 → `http_req60=12 authfail=0,50`, `dns_q60=6 uniq=0,50` |
| 04 | Multi-entidad (no solo-Kali) | SENSOR · 07:58 | conteo `entity_ip` en acumulador + `grep -c src_ip` en eve | **30 entidades** distintas; decenas de miles de eventos no-Kali; Kali = 1 de 30 |
| 05 | Modo sombra (estado + procedimiento) | SENSOR + srv-dmz · 08:00 ; arnés en LAPTOP | solo-lectura `systemctl`/`nft` + `tests/test_sombra.sh` | motor **sin `--enforce`**; agente active+enabled; sets **vacíos**; arnés **11/11** |
| 06 | Config Suricata efectiva | SENSOR · 08:05 | `sha256sum suricata.yaml` + `grep 18081` | `8e084b7d…efa04`; `detection-ports dp "80, 18081"`; Suricata 7.0.3 activo |
| 07 | **Archivado full-span (toda la población)** | SENSOR · 16:48–16:53 | `archivar_captura.sh` barrido/inventario/estado-motor + `tcpdump -nr` + tests | **75 ficheros, 0 dup/solape/hueco** (inventario por marca de paquete, 1126 s); ambos tráficos (Kali 74, bastión 7688); 75/75 copias sha-verificadas; descartes del proceso **no medidos** (NRestarts=0); tests 5/5; sin root |

## 2. Archivado con tráfico benigno real

**Corrección respecto al cierre anterior.** `cf-capturar` aplica `host 10.10.20.30`: su PCAP **solo**
contiene tráfico de la Kali y **no** conserva el control normal de otras entidades. EVE y el acumulador
**no** sustituyen esos paquetes (son telemetría derivada). Por tanto `cf-capturar` **no** es el archivo de
la campaña; solo sirvió para validar el mecanismo de captura (226 pkts / 0 drops).

**Procedimiento habilitado y ENDURECIDO (ejecutable con mis permisos reales, SIN cambios administrativos).**
`ppi-motor-capture` ya captura **todo el espejo** (`tcpdump -i ens37`, **sin filtro de host**, ficheros de 15 s,
grupo `m4rk`). `scripts/archivar_captura.sh` los copia a un directorio propio antes de la poda
(`cyberflow-limpieza`, `-mmin +15`). El archivador: **no oculta fallos** (registra fichero/hora/motivo en
`archivar.log`, marca `ESTADO.txt` OK/PENDIENTE/FALLO y sale con código ≠ 0); copia **solo ficheros cerrados**
y **verifica integridad** (sha256 copia==origen, temporal + `mv` atómico); **reintenta** las copias fallidas
(nunca las marca archivadas ni las salta); **detecta pérdida** (fichero visto que desaparece sin archivarse →
FALLO); hace **prechequeos** (herramientas, lectura origen, escritura destino, espacio mínimo) y un **barrido
final** persistido. Verificado con `tests/test_archivador.sh` (5/5: copia correcta, permiso denegado, error de
copia, copia incompleta, pérdida; los fallos son visibles y no terminan en éxito).

**Prueba real (2026-10-27 16:48–16:53, tráfico benigno identificable).** Kali 10.10.20.30 y bastión 10.10.10.30
(cliente legítimo) hacia srv-dmz. `barrido`: **vistos=75, archivados=75, 0 fallos (RC=0)**, cada copia con sha
verificado. `inventario` (por marca de **paquete**, no por nombre): **75 ficheros, 0 duplicados, 0 solapes, 0
huecos/reinicios**, 1126 s continuos. Leído del PCAP (no EVE): **ambos tráficos** (Kali 74 pkts, bastión 7688
pkts) + resto de la red (133 476 pkts, ≥30 entidades). Pérdidas: 0 huecos/solapes; integridad 75/75 sha-ok;
**descartes de kernel del proceso real `ppi-motor-capture` (PID 1393, NRestarts=0): NO MEDIDOS** (corre con `-G`
sin `--print-statistics`; las líneas "0 dropped" del journal son de PIDs antiguos, no del actual → no se usan
como sustituto ni se afirma 0 pérdidas). El "138 en 1024 s" del cierre anterior era un **artefacto de la copia
naíf repetida** (duplicados); con el barrido verificado el inventario real da 75 ficheros limpios. Detalle en
`evidencia-entorno-2026-10-27/07-archivado-full-span.txt` (incluye cómo comprobar el archivador antes y durante A).

**Cobertura por capa (no se confunden).**

| Capa | Qué es | Alcance | Rol |
|---|---|---|---|
| **PCAP full-span** (`archivar_captura.sh`) | paquetes crudos de `ens37` | **toda la población** (control normal + ensayo) | única que permite reprocesar paquetes; es el archivo de la campaña |
| PCAP `cf-capturar` | paquetes con filtro `host 10.10.20.30` | **solo Kali** | validación de mecanismo; NO archivo |
| EVE (Suricata) | eventos sobre `ens37` | red completa, **derivado** de paquetes | telemetría; no sustituye el PCAP |
| Decisiones (`motor_decision.log`) | alertas emitidas por entidad | entidades evaluadas | emisiones en vivo |
| Características (`multilayer-v3.csv`) | features por ventana/entidad | red completa, **derivado** de EVE+paquetes | entrada del motor |

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
| Captura full-span (archivo) | `archivar_captura.sh` probado: sin huecos, ambos tráficos, integridad (07) | **arrancar** `archivar_captura.sh` antes del control-normal y dejarlo durante toda A |
| Historia previa | N/A en preparación | **re-verificar** (≥120 s de contexto antes de cada episodio) |
| Modo sombra | estado real + procedimiento 11/11 (05) | **aplicar** `modo_sombra.sh --ejecutar --motor-verificado` y re-verificar sets vacíos |
| DNS `lab-ppi` / egress 0 | cerrado (T2) | ya hecho (monitorizar egress) |
| Endpoint 18081 + parseo HTTP | cerrado (T3 / 06) | ya hecho (comprobar hashes de código en sensor) |
| Hashes de código desplegado | registrados en `config-campana.json` | **re-verificar** contra el sensor justo antes |

## 6. ¿Preparado para el prompt 2?

**Sí, el entorno está preparado** para recibir el prompt 2 (ejecución de la campaña A). Lo que **falta**,
y es deliberado, son los pasos que **solo** se hacen al arrancar A: (a) aplicar el modo sombra en srv-dmz y
confirmar sets vacíos; (b) arrancar el archivado full-span y re-confirmar el reloj de la Kali; (c) re-verificar
los hashes del código desplegado en el sensor; (d) lanzar el generador con `--autorizado`. Ninguno de esos
pasos se ejecuta ahora. No queda **ningún bloqueante** de entorno.

**Comando de captura para el prompt 2** (lo ejecuto yo; sin root):

```
[SENSOR m4rk] → lo ejecuto yo
scripts/archivar_captura.sh ~/cf-campana-archivo/campana-A-$(date -u +%Y%m%d) 60
# Arrancar ANTES del control-normal; dejar correr durante historia previa, episodios y posterior;
# parar (Ctrl-C/SIGTERM) tras el último posterior (hace barrido final). Preserva full-span ens37
# (toda la población) sin huecos ni sobrescritura. Vigilar espacio con df (21 GiB libres).
```

**Cómo comprobar que el archivador funciona** — ANTES de A: `archivar_captura.sh barrido <DIR>` → RC=0 y
`ESTADO.txt` empieza por "OK"; `archivar_captura.sh estado-motor` → `is-active=active`, `NRestarts=0`. DURANTE
A (sin parar): `cat <DIR>/ESTADO.txt` debe seguir en "OK", `grep FALLO <DIR>/archivar.log` vacío, `df -h <DIR>`
con espacio; al terminar, Ctrl-C → barrido final y `archivar_captura.sh inventario <DIR>` → 0 solapes/huecos/duplicados.

Reversión del único estado creado (no hay cambio administrativo): `rm -rf ~/cf-campana-archivo ~/bin/archivar_captura.sh` en el sensor.
