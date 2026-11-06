# Preparación de la ejecución de E-carga v2 (Etapa 4A), 06-nov

**Estado: preparado. NO ejecutado y NO programado.**
- No se ha arrancado ningún generador.
- No se ha abierto ninguna ventana de observación.
- No hay ningún cron, `at`, temporizador de systemd ni espera en segundo plano para la franja propuesta.
- Este documento no autoriza nada. La ejecución necesita una orden posterior y explícita de Mark (§9).

Las pruebas «en seco» y «de humo» de este documento se hicieron sin carga y sobre periodos de segundos. **No son E-carga
ni ninguna ventana**, y sus números no tienen valor de medida. Ningún dato histórico (06-nov, 04-nov) se usa como
resultado del ensayo futuro. Esos datos solo sirvieron para probar las herramientas.

**Referencias de partida**
- Protocolo: [`../PROTOCOLO-CARGA-v2.md`](../PROTOCOLO-CARGA-v2.md), r2 (docs `a56e674`).
- Producto: `ae2900e`, rama `recuperacion/etapa4a-pendientes-20261106`.
- Evaluador: `evaluar_ecarga.py` 2026-11-06.4, sha256 `53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f`.

**Nada de esto cambia el protocolo.** No cambia ningún criterio ni umbral de K1–K5 ni de S1–S15. Tampoco cambia:
- la franja ni la ventana;
- el calentamiento;
- las condiciones de parada;
- el modo sombra.

No se ha tocado nada de esto: detector, modelo, escalador, características, α, reglas, política `if_senal`, captura,
Suricata ni el Word.

## 1. Versiones y rutas en los hosts (nada instalado en servicios, nada reiniciado)

### 1.1 Paquete del producto

**`~/cf-e4/paquete-ae2900e`** en el bastión, en Sensor1 y en srv-dmz.
- Se construyó desde `origin` (`git archive ae2900e`).
- El script se negaba a copiar si la carpeta ya existía, así que no se sobrescribió nada.
- Contenido: 461 ficheros.
- `SHA256SUMS` interno: `41f917874de3687c3961467a2625861ec48e8c824223933b21669116d0ffba9c`.
- tgz: `09ab20c800b3329c461c810290850ead706c57856f5de635051a8407421e4975`.
- En los tres hosts, `sha256sum -c --strict` da rc 0.
- En los tres hosts, `evaluar_ecarga.py` coincide con el sha256 publicado y `VERSION` = 2026-11-06.4.
- Transcripción: `../evidencia/11-preparacion-ecarga/paquete-ae2900e.txt`.

**`~/cf-e4/paquete-f6dc685` lleva el evaluador 2026-11-06.3, con el defecto de la r2 (§0.1 del protocolo). NO se usa para
el veredicto.**
- Se ha dejado intacto, sin modificar ni borrar.
- Junto a él hay un aviso en los tres hosts: `~/cf-e4/paquete-f6dc685.NO-USAR-PARA-VEREDICTO.txt`.
- Los paquetes anteriores también siguen intactos.

### 1.2 Guiones de ejecución

**`~/cf-e4/ecarga-v2-guiones-c7f24510`** en el bastión, en Sensor1 y en clientes.
- La etiqueta es el sha256 de su `SHA256SUMS`.
- Copia publicada: [`guiones-c7f24510/`](guiones-c7f24510/).

| Guion | Host | Qué hace |
|---|---|---|
| `muestreo_bastion.sh DIR FIN PARADA real\|seco` | bastión | Hace las mismas lecturas B/S/D que `obs_muestreo.sh` del 06-nov, cada 30 s, más la línea C con el estado de los generadores. Ejecuta la guardia tras cada muestra. En modo `real` **para** los generadores una sola vez: si la guardia lo pide o al llegar a PARADA. **Nunca los arranca.** No sobrescribe |
| `guardia.py` | bastión | Condiciones de §3.7 del protocolo, sin añadir ninguna (§5) |
| `sensor1_muestreadores.sh comprobar\|arrancar\|parar\|estado` | Sensor1 | Comprobaciones previas y `obs_pcap --en-seco`. Lanza `salud_captura muestrear` (10 s), `muestreo_fino` (1 s) y `obs_pcap`, que terminan solos en FIN. La parada solo afecta a sus PID. Sin sudo |
| `generadores.sh estado\|permisos\|arrancar\|parar` | clientes | `systemctl start/stop cyberflow-lab.target` con `sudo -n`; es el único permiso NOPASSWD que existe. `arrancar` comprueba antes el hash `ae5134a7…` del generador. `parar` comprueba que el target queda inactivo y con 0 procesos |
| `test_guardia.py` | — | 14 pruebas |

### 1.3 Herramientas de evaluación

**`~/cf-e4/ecarga-v2-evaluacion-e83f4be6`** en Sensor1 y en el bastión.
- Copia publicada: [`evaluacion-e83f4be6/`](evaluacion-e83f4be6/).

| Herramienta | Qué produce |
|---|---|
| `sensor1_post.sh DIR DESDE HASTA` | Escribe `DIR/post`, solo con lecturas: `clasificar_periodo --suricata-eve`, `comparar_suricata`, `evaluar_ecarga perfiles`, `derivar_pcap`, el listado de `/var/log/suricata`, el ruleset de después y `SHA256SUMS`. Añade `eve.json.1` y `eve.json.1.gz` si rotaron dentro de la ventana |
| `derivar_bastion.py MUESTRAS DESDE HASTA` | S1, S6, S8, S9 y S10 |
| `derivar_pcap.py PCAP.jsonl DESDE HASTA` | S2 y S3 |
| `construir_entrada.py` | La entrada de `veredicto` y su trazabilidad (§4) |
| `test_evaluacion.py` | 17 pruebas |

### 1.4 Herramientas vigentes que se usan sin cambios

- En Sensor1, `~/cyberflow-e4/herramientas-20261106`: `salud_captura.py` y `clasificar_periodo.py`, VERSION
  2026-11-06.1.
  - `comprobar` verifica su `SHA256SUMS`.
  - También verifica que `salud_captura.py` es idéntico al del paquete.
- `comparar_suricata.py`, `muestreo_fino.py`, `obs_pcap.py` 2026-11-06.2 y `evaluar_ecarga.py` 2026-11-06.4, del
  paquete `ae2900e`.
- Verificadores `verificar_{bastion,sensor1,srvdmz}.sh`, también del paquete `ae2900e`.
- Del 06-nov, en `evidencia/06-observacion/`:
  - `precheck.sh` (sha256 `b3127edd…`), sin cambios;
  - `obs_p4_post.sh` (sha256 `25d8d369…`), cambiando **solo** su carpeta fija (§4.3).

## 2. Comprobaciones previas y en seco ya hechas (06-nov, sin carga)

**Todas se repiten en P0 antes de arrancar nada (§3, paso 1).** Que hoy hayan salido bien no vale para el día del
ensayo.

| Comprobación | Resultado | Evidencia (`../evidencia/11-preparacion-ecarga/`) |
|---|---|---|
| Relojes | NTP sincronizado en los cuatro hosts. `Etc/UTC` en Sensor1 y en clientes | `comprobar-seco.txt` |
| Verificadores del paquete `ae2900e` | Bastión 8 OK, rc 0. Sensor1 24 OK, rc 0. srv-dmz 4 OK, rc 0 (con `CON_SUDO=1` y el respaldo `srvdmz-p4-fase-c-20261106T043944Z`) | `comprobar-seco.txt` |
| Sensor1 `comprobar` | Todo OK, sin ningún FALLO:<br>- paquete y evaluador verifican;<br>- herramientas verifican;<br>- venv presente;<br>- lectura de `eve.json`, del anillo y de softnet;<br>- lecturas SIGUSR1 en el journal;<br>- `/home` 12 294 MiB (≥ 2 GiB);<br>- `MemAvailable` 6 357 MiB (≥ 1 GiB);<br>- DIR libre;<br>- 0 procesos `--aplicar`;<br>- ningún muestreador vivo | `comprobar-seco.txt` |
| `obs_pcap --en-seco` | rc 0, `fin_utc` 2026-11-09T04:16:00Z, sin crear ninguna salida | `comprobar-seco.txt` |
| Mecanismo de los muestreadores | Arrancan los tres y sus ficheros crecen. `parar` manda TERM y quedan 0 vivos. Volver a arrancar en el mismo DIR aborta con rc 2 | `comprobar-seco.txt` |
| Permisos de los generadores | NOPASSWD **solo** para `start` y `stop` de `cyberflow-lab.target`. Hash `ae5134a7…`. Target inactivo y deshabilitado, 0 procesos | `comprobar-seco.txt` |
| Muestreo del bastión con la guardia, en modo **seco** | 3 muestras y `parar` false. Escribe «SECO: se pararían» y no para nada. El mismo DIR aborta con rc 2 | `comprobar-seco.txt` |
| Vía de parada, en modo **real** con el target ya parado | `generadores.sh parar` rc 0: «target inactivo y 0 procesos». No se arrancó ningún generador | `prueba-parada.txt` |
| Cadena de evaluación en Sensor1 (prueba de humo de ~18 s, sin generadores, rotulada PRUEBA) | `sensor1_post` y `construir_entrada` rc 0. `veredicto` rc 1, «carga insuficiente», sin error de contrato | `humo-sensor1.txt` |
| Lectura de S7 (`obs_p4_post.sh` derivado, sobre las 3 muestras en seco) | rc 0. Entregas en orden, 0 entregadas sin aceptar, publicador sin retroceso | `prueba-s7.txt` |
| Lectura de S11 (`precheck.sh`, sin cambios) | rc 0. Hashes iguales a los congelados de O11: modelo `df547da0…`, manifiesto `b3ad6805…`, esquema `e032a1a2…`, `ec78ca5` OK, `suricata.yaml` `0962ce68…`. Rulesets `24c320e3…` y `e3b0c442…` | `prueba-s11.txt` |
| Pruebas de los guiones y de la evaluación, en el banco Docker (sin red, usuario 65534, montajes de solo lectura) | `test_guardia` 14/14. `test_evaluacion` 17/17. Los dos `SHA256SUMS` verifican | `pruebas-banco.txt` |
| Plantilla sin resultados frente al evaluador publicado | rc 2 («campo no reconocido»). Sin la marca, también rc 2 (clase `None`) | `plantilla-rc.txt` |
| Espacio para la evidencia | Bastión: 14 GB libres. Sensor1: 12 GiB libres en `/home` | `comprobar-seco.txt` y §2 |

## 3. Secuencia del día del ensayo (SOLO TRAS ORDEN EXPLÍCITA DE MARK)

**Franja propuesta.** Es la de §3.2 del protocolo, **sin programar**:

| Paso | Epoch | Hora UTC |
|---|---|---|
| P0 | 1794191400 | 02:30Z |
| T_g | 1794193200 | 03:00Z |
| Ventana | 1794194100–1794197700 | 03:15–04:15Z (22:15–23:15 en Perú, dom 08-nov) |
| Fin de `obs_pcap` | 1794197760 | 04:16Z |
| Parada | 1794197820 | 04:17Z |
| Análisis, no antes de | 1794198600 | 04:30Z |

**Carpeta del ensayo.** `~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/` en el bastión (`bastion/`, `manual/`, `post-sensor1/`) y
en Sensor1 (`sensor1/`). Ningún guion sobrescribe. Si la carpeta existe, se aborta.

**Quién ejecuta qué.** Lo ejecuto yo desde el portátil, por ssh al bastión y desde ahí a cada host, con las llaves ya
autorizadas. Ningún paso necesita la contraseña de sudo de Mark.

Abreviaturas usadas en los bloques:
- G = `~/cf-e4/ecarga-v2-guiones-c7f24510`
- V = `~/cf-e4/ecarga-v2-evaluacion-e83f4be6`
- P = `~/cf-e4/paquete-ae2900e`
- X = `~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z`

### Paso 0: comprobar que la franja sigue siendo viable

Antes de P0 se comprueba:
- que `date +%s` < 1794191400;
- que la franja publicada en §3.2 no ha cambiado;
- que nadie usa el laboratorio en esa franja.

**Si no es viable, no se desplaza en silencio.** Antes de arrancar se fija una franja nueva con los mismos desfases, en
otra madrugada laborable UTC. Se publica en `evidencia/` con su commit y con la comprobación de `weekday()`.

### Paso 1: P0, 02:30Z (solo lecturas; si algo falla, no se arranca nada)

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
G=~/cf-e4/ecarga-v2-guiones-c7f24510; X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z
mkdir "$X" "$X/manual" || exit 2                      # si existe, aborta
(cd $G && sha256sum -c --strict --quiet SHA256SUMS) && (cd ~/cf-e4/paquete-ae2900e && sha256sum -c --strict --quiet SHA256SUMS)
# relojes de los 4 hosts, los 3 verificadores con rc 0, generadores.sh permisos y estado: las mismas órdenes de
# evidencia/11-preparacion-ecarga/comprobar_seco.sh (sin su prueba de mecanismo)
bash "$X/manual/precheck.sh" antes > "$X/manual/s11-precheck-antes.txt" 2>&1   # S11 «antes»
```

`$X/manual/precheck.sh` y `$X/manual/obs_p4_post.sh` se copian antes, por scp, desde el repositorio publicado
(`evidencia/06-observacion/`). Se comprueba que sus sha256 son `b3127edd…` y `25d8d369…`.
- `precheck.sh` se usa sin cambios.
- `obs_p4_post.sh` se usa con la única modificación de §4.3.

```bash
# [SENSOR1 m4rk] → lo ejecuto yo (desde el bastión)
bash ~/cf-e4/ecarga-v2-guiones-c7f24510/sensor1_muestreadores.sh comprobar \
  ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1-comprobar 1794197760 2026-11-09T04:16:00Z   # todo OK y obs_pcap --en-seco rc 0
```

### Paso 2: ~02:55Z, muestreadores (solo lectura; no arrancan ningún generador)

```bash
# [SENSOR1 m4rk] → lo ejecuto yo
bash ~/cf-e4/ecarga-v2-guiones-c7f24510/sensor1_muestreadores.sh arrancar \
  ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 1794197760 2026-11-09T04:16:00Z
```

```bash
# [BASTIÓN gadmin] → lo ejecuto yo. Línea base de la guardia = primera muestra, tomada ANTES de T_g
X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z
setsid nohup bash ~/cf-e4/ecarga-v2-guiones-c7f24510/muestreo_bastion.sh "$X/bastion" 1794197880 1794197820 real \
  > "$X/bastion.out" 2>&1 < /dev/null &
```

Hay dos fines distintos:
- **FIN 1794197880 (04:18Z)** cubre la muestra «≤ 60 s después de HASTA» que exige la cobertura de S1/S6/S8–S10.
- **PARADA 1794197820 (04:17Z)** es la parada de los generadores de §3.2.

### Paso 3: T_g = 1794193200 (03:00:00Z), arranque de los generadores

```bash
# [BASTIÓN gadmin] → lo ejecuto yo, en primer plano y solo tras la orden; no es una tarea programada
while [ "$(date +%s)" -lt 1794193200 ]; do sleep 0.2; done
ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 \
  'bash ~/cf-e4/ecarga-v2-guiones-c7f24510/generadores.sh arrancar; bash ~/cf-e4/ecarga-v2-guiones-c7f24510/generadores.sh estado'
```

**Vigilancia durante la ventana.** Solo se lee:
- `tail` de `$X/bastion/guardia.jsonl` y de `eventos.log`;
- `sensor1_muestreadores.sh estado`.

### Paso 4: fin y parada (§5)

- **04:16Z.** Los muestreadores de Sensor1 terminan solos. `obs_pcap` hace su pasada final.
- **04:17Z.** `muestreo_bastion.sh` (modo real) ejecuta `generadores.sh parar` y anota en `eventos.log` el rc y el estado
  «target inactivo y 0 procesos».
- **Comprobación independiente**, tras la parada:

```bash
# [CLIENTES adminclientes] → lo ejecuto yo (desde el bastión)
bash ~/cf-e4/ecarga-v2-guiones-c7f24510/generadores.sh estado   # target inactive, procesos=0
```

- **Respaldo manual.** Si `eventos.log` no muestra la parada antes de las 04:18Z:
  - se ejecuta `generadores.sh parar` a mano;
  - el retraso se anota como incidencia en la evidencia.

### Paso 5: análisis, no antes de 04:30Z (solo lecturas)

```bash
# [SENSOR1 m4rk] → lo ejecuto yo
bash ~/cf-e4/ecarga-v2-evaluacion-e83f4be6/sensor1_post.sh ~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 1794194100 1794197700
```

```bash
# [BASTIÓN gadmin] → lo ejecuto yo
X=~/cf-e4/ecarga-v2-ejecucion-20261109T0300Z; V=~/cf-e4/ecarga-v2-evaluacion-e83f4be6; P=~/cf-e4/paquete-ae2900e
scp -r -q -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11:cf-e4/ecarga-v2-ejecucion-20261109T0300Z/sensor1 "$X/post-sensor1"
(cd "$X/post-sensor1/post" && sha256sum -c --strict --quiet SHA256SUMS)          # lo copiado es lo sellado en Sensor1
python3 -I $V/derivar_bastion.py "$X/bastion/muestras.txt" 1794194100 1794197700 > "$X/bastion_s.json"
# S7, S11 y S15: §4.3. S14: §4.4
python3 -I $V/construir_entrada.py --desde 1794194100 --hasta 1794197700 \
  --clasificacion "$X/post-sensor1/post/clasificacion/clasificacion.json" --comparar "$X/post-sensor1/post/comparar.json" \
  --perfiles "$X/post-sensor1/post/perfiles.json" --perfiles-rc "$(cat "$X/post-sensor1/post/perfiles.rc")" \
  --bastion "$X/bastion_s.json" --pcap "$X/post-sensor1/post/pcap_s.json" \
  --manual S7=<v>:"$X/manual/s7-obs_p4_post.txt" --manual S11=<v>:"$X/manual/s11-comparacion.txt" \
  --manual S15=<v>:"$X/manual/s15-verificadores-despues.txt"  [--manual S14=… solo si hay definición publicada, §4.4] \
  --salida-entrada "$X/entrada-veredicto.json" --salida-traza "$X/trazabilidad.json"
python3 -I $P/deploy/etapa4/sensor1/evaluar_ecarga.py veredicto --entrada "$X/entrada-veredicto.json" > "$X/veredicto.json"; echo $? > "$X/veredicto.rc"
(cd "$X" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS)
```

`<v>` es `true`, `false` o `null` según la regla de §4.3, aplicada a lo que diga el fichero. No se escribe nunca antes
de leerlo.

**Último paso.** La carpeta `X` completa y la de Sensor1 se copian a `evidencia/12-ecarga-ejecucion/` y se publican con
su manifiesto, **sea cual sea el resultado** (§6).

## 4. Cómo se construye la entrada de `veredicto` desde salidas reales

`construir_entrada.py` sigue el contrato 2026-11-06.4 (§4.5 del protocolo):
- **No rellena nada por defecto.** Todo K o S que no se deriva de una fuente leída y del mismo periodo, ni se da con
  `--manual` y un fichero de evidencia, queda en `null` (sin medida).
- **No sobrescribe nada.**
- **Exige la medida EVE del mismo periodo.** Sin ella, rc 2: el bloque `suricata` no se inventa.

**Periodo.** Siempre es la ventana publicada: DESDE = 1794194100, HASTA = 1794197700, o la de la franja nueva si se
publicó una (§3, paso 0). Si una fuente tiene otro periodo (diferencia ≥ 0,5 s), la trazabilidad lo avisa y sus
criterios quedan en `null`.

### 4.1 Fuente de cada K y S

| Criterio | Herramienta → fichero | Campo | Regla (sin cambios de umbral) |
|---|---|---|---|
| K1 | `comparar_suricata.py --stats-eve --eve` → `post/comparar.json` | `paquetes` | ≥ 596 789. Exige el mismo periodo y `fuente_contadores` = «eve stats» |
| K2 | igual | `rafagas_ge_umbral` | ≥ 9, con `umbral_rafaga_paquetes_8s` = 5 000 |
| K3 | igual | `flujos_grandes` | ≥ 50, con `umbral_flujo_grande` = 1 000. `null` si `flujos_eve` = 0 (no se leyó ningún flujo) |
| K4a | `evaluar_ecarga.py perfiles` → `post/perfiles.json` y `perfiles.rc` | `K4a.cumple` | Se copia si rc 0 o 1, el periodo es el mismo y la versión es 2026-11-06.4. Si no, `null`. K4b va solo a la trazabilidad, como dato informativo |
| K5 | `clasificar_periodo.py --suricata-eve` → `post/clasificacion/clasificacion.json` | `suricata.medida.estado` | `cero_explicito` o `descartes` → true. `cobertura_insuficiente` → false. Cualquier otro estado → `null` |
| S1 | `derivar_bastion.py` → `bastion_s.json` | `S1.valor` | O1: PID y `NRestarts` constantes en los servicios de la cadena |
| S2 | `derivar_pcap.py` → `post/pcap_s.json` | `S2.valor` | O2: cero errores de formato, y el primer fichero empieza a ≤ rotación + 2 s de DESDE |
| S3 | igual | `S3.valor` | O3: salto máximo ≤ 7 s. La rotación de `eve.json` se informa en `suricata-ls.txt` |
| S4 | clasificación | `suricata.medida.estado` | Igual que K5 (O4) |
| S5 | clasificación | `clase_periodo` y estado | O5: clase calculada y estado de Suricata medido |
| S6 | `bastion_s.json` | `S6.valor` | O6: `/home` ≥ 2 GiB en todas las muestras |
| S7 | manual (§4.3) | — | O7 y criterio P4 |
| S8 | `bastion_s.json` | `S8.valor` | O8: Δ `firma_invalida` = Δ `paquete_invalido` = 0 en la ventana |
| S9 | `bastion_s.json` | `S9.valor` | O9: panel 401 y agente activo |
| S10 | `bastion_s.json` | `S10.valor` | O10: 0 `aplicacion`, rulesets constantes, 0 `--aplicar`/`--enforce`, v1 inactivos |
| S11 | manual (§4.3) | — | O11 |
| S12 | clasificación | `suricata.medida.estado` | Medido → true. Cualquier otro estado → false |
| S13 | clasificación | `suricata.medida.{descartes,paquetes}` | descartes × 10⁸ < 1 495 × paquetes. Es la regla < 14,95/M **exacta en enteros**: 14,95 no cumple. `null` sin medida |
| S14 | manual (§4.4) | — | **Pendiente de definición operacional** |
| S15 | manual (§4.3) | — | Verificadores con rc 0 después de la ventana |

**Cobertura de los S del bastión.**
- Se usan las muestras en [DESDE − 60, HASTA + 60].
- Tiene que haber una muestra a ≤ 60 s de cada borde y ningún hueco > 60 s.
- Si no se cumple, S1, S6, S8, S9 y S10 quedan **todos** en `null`.
- Un dato que falta en una muestra deja su S en `null`, nunca en true.

### 4.2 Bloque `suricata`, clase, motivos y descartes por millón

- **`suricata`** = `{estado, paquetes, descartes}`, copiados de `clasificacion.json` → `suricata.medida`. Es la medida EVE
  acotada al periodo, la que hace `clasificar_periodo --suricata-eve`.
  - Sin estado medido, `paquetes` y `descartes` son `null`. No se ponen a 0.
- **`clasificacion.clase_periodo`** se copia tal cual (C0, C1, C2, C3 o `no_evaluable`). No se recalcula ni se corrige.
- **`clasificacion.motivos`** son los motivos de `capturas.captura` y de `capturas.via-rapida`.
  - Cada uno va con su origen delante («captura: …», «via-rapida: …»).
  - Se añade el `motivo` general si lo hay.
- **`descartes_por_millon`** = descartes × 1 000 000 / paquetes, con los mismos dos enteros del bloque y **sin redondeo**.
  - Es `null` si no hay medida o si hay 0 paquetes.
  - La decisión de S13 no usa este flotante: usa la comparación exacta en enteros de §4.1.
- **K1 frente a la medida acotada.** K1 usa el método del comparador con el que se fijó el umbral (O12). El total de la
  medida acotada se guarda en la trazabilidad como dato informativo y no sustituye a K1.

### 4.3 Entradas manuales: S7, S11 y S15

Solo se admiten con `--manual Sx=true|false|null:FICHERO`. El fichero tiene que existir, y su sha256 queda en la
trazabilidad.

**S7: `manual/s7-obs_p4_post.txt`**
- Se ejecuta `obs_p4_post.sh` del 06-nov cambiando **solo** la línea `O=` por la carpeta del bastión del ensayo:
  `sed -E "s#^O=.*#O=$X/bastion#"`.
- Se anotan los sha256 del original (`25d8d369…`) y del derivado.
- Argumentos: DESDE y HASTA.
- **true** si:
  - «entregadas NO aceptadas: 0»;
  - «aceptadas en orden: True»;
  - «publicador … sin retroceso: True».
- **false** si cualquiera de las tres no se cumple.
- **null** si no hay ninguna entrega en la ventana o si el guion falla.
- El mismo fichero da el cruce de O1, O6 y O8–O10. Si discrepa de `derivar_bastion`, se publica la discrepancia y no
  se corrige ninguno de los dos.

**S11: `manual/s11-precheck-antes.txt` (P0), `manual/s11-precheck-despues.txt` y `manual/s11-comparacion.txt`**
- Se ejecuta `precheck.sh` sin cambios, antes y después.
- `s11-comparacion.txt` es el `diff` de las líneas de hash, `grep -E '^[0-9a-f]{64} '`, más las dos líneas
  «ec78ca5 SHA256SUMS OK».
- **true** si el `diff` está vacío y aparecen las dos líneas OK.
- **false** si algún hash difiere.
- **null** si falta alguno de los dos ficheros.

**S15: `manual/s15-verificadores-despues.txt`**
- Se ejecutan los tres verificadores del paquete `ae2900e` después de la ventana, como en P0.
- **true** si los tres dan rc 0.
- **false** si alguno da rc distinto de 0.
- **null** si no se ejecutó alguno.

### 4.4 S14: decisión pendiente (no se inventa un umbral)

S14 dice «Sin saturación nueva de CPU, softirq, disco ni memoria; softnet `dropped` = 0».
- **La parte de softnet `dropped` = 0 es medible.** La da `muestreo_fino` (1 s) y se lee directamente.
- **«Saturación nueva» no tiene un umbral numérico publicado**, ni en el protocolo ni en el ensayo del anillo de origen
  (cierre complementario del 04-nov, que la juzgó de forma cualitativa).

Sin una definición operacional publicada **antes** de T_g:
- S14 se registra como `null`;
- con un S en `null` el evaluador no puede dar «estable con carga suficiente»: el resultado sería, como mucho,
  «no demostrable».

**Necesita una decisión de Mark antes de pedir la ejecución.** No adopto ninguna regla. Hay dos opciones:
- **(a)** publicar antes de T_g la regla de «saturación nueva»: qué series de `muestreo_fino`, qué umbral y qué
  referencia (por ejemplo, la del ensayo del anillo del 04-nov);
- **(b)** aceptar de antemano que S14 quede en `null` y que el resultado máximo alcanzable sea «no demostrable».

Los datos se recogen igual con cualquiera de las dos: CPU, softirq, disco, memoria y softnet a 1 s.

### 4.5 Datos que faltan y contradicciones

- **Fuente que falta, ilegible o de otro periodo** → `null` en sus criterios y aviso en la trazabilidad. Nunca true.
- **Clasificación sin medida EVE, o de otro periodo** → `construir_entrada` da rc 2 y no se emite veredicto. Se publica
  la traza con el motivo.
- **Contradicciones.** Puede ocurrir que la clase no cuadre con los descartes, o que S12 o S13 no cuadren con las
  métricas.
  - No se corrige ningún valor.
  - El evaluador 2026-11-06.4 las lista en `incoherencias` y da «no demostrable», salvo si el resultado es «carga
    insuficiente».
- **Entrada inválida** (tipos, campos de más o de menos) → rc 2. No se habilita nada.

### 4.6 Trazabilidad

`trazabilidad.json` recoge, por cada campo de la entrada:
- `valor`, `fuente`, `campo` y `regla`;
- por cada fuente: fichero, sha256 y estado;
- los avisos, la lista `sin_medida` y el sha256 de la entrada escrita.

Así, cada valor del JSON lleva hasta su fichero de evidencia. Y cada fichero lleva hasta su `SHA256SUMS` sellado:
`post/SHA256SUMS` en Sensor1 y `SHA256SUMS` de la carpeta `X`.

### 4.7 Plantillas

Las dos están **rotuladas «plantilla sin resultados»**. Ningún valor está medido ni se da ningún criterio por cumplido.
- [`ENTRADA-VEREDICTO.PLANTILLA-SIN-RESULTADOS.json`](ENTRADA-VEREDICTO.PLANTILLA-SIN-RESULTADOS.json): todo `null`.
  El evaluador publicado la rechaza con rc 2, con la marca y también sin ella (`plantilla-rc.txt`).
- [`TRAZABILIDAD.PLANTILLA-SIN-RESULTADOS.json`](TRAZABILIDAD.PLANTILLA-SIN-RESULTADOS.json): la forma de la
  trazabilidad, con «<sin resultado>» en cada valor.

## 5. Parada: al final y por protección (§3.7 del protocolo, sin añadir condiciones)

**Al final.** `muestreo_bastion.sh` ejecuta `generadores.sh parar` en PARADA = 1794197820. Después se comprueba de
forma independiente, y si hace falta se recurre al respaldo manual (§3, paso 4).

**Por protección.** `guardia.py` se ejecuta tras cada muestra de 30 s, con la primera muestra como línea base. Para
**una vez** los generadores si ocurre cualquiera de estas cosas:
- `MemAvailable` < 1 GiB;
- `/home` < 2 GB, tomado como 2 GiB, que es la lectura prudente;
- `--aplicar` o `--enforce`, o un cambio de ruleset en Sensor1 o en srv-dmz;
- un evento `aplicacion` nuevo;
- el reinicio de un servicio de la cadena (cambio de PID o de `NRestarts`);
- `firma_invalida` o `paquete_invalido` sostenidos más de 60 s;
- EVE parado más de 60 s.

Sobre la guardia:
- **Un dato ilegible no para por sí solo.** Queda como aviso `SIN_LECTURA` y su S saldrá en `null`.
- **Una señal o una entrada del feed no es motivo de parada.**
- **Parada a mano.** Mark puede pedirla en cualquier momento. Se ejecuta con
  `[CLIENTES adminclientes] → lo ejecuto yo: bash ~/cf-e4/ecarga-v2-guiones-c7f24510/generadores.sh parar`.

**Tras una parada anticipada:**
- los muestreadores siguen hasta su FIN, para conservar la medida;
- la ventana no se corta, no se mueve ni se prolonga;
- el resultado es «no estable» o «no demostrable», según el evaluador.

## 6. Conservación

- Se conserva y publica todo: carpetas, salidas con rc distinto de 0, avisos, paradas e incidencias.
- Se publica también el resultado desfavorable: «carga insuficiente», «no estable» o «no demostrable».
- No se borra ni se repite en silencio ninguna corrida.
- Una repetición sería otra corrida, con su franja nueva publicada antes. No sustituye a la anterior.
- Las carpetas seco y PRUEBA del 06-nov se conservan en los hosts, rotuladas. No forman parte del ensayo.

## 7. Alcance

- E-carga forma parte de la Etapa 4A, en sombra.
- No se inicia la 4B, la 4C ni la campaña B. No se ejecutan ataques ni se activan restricciones.
- I5 sigue exigiendo cero descartes de Suricata en los 30 minutos previos al inicio de 4C.
- La población principal sigue siendo C0.

## 8. Estado de la preparación

| Tarea | Versión y ruta | Comprobación realizada | Evidencia | Pendiente |
|---|---|---|---|---|
| Paquete del producto | `ae2900e` → `~/cf-e4/paquete-ae2900e` (bastión, Sensor1, srv-dmz) | `SHA256SUMS` `41f91787…` rc 0. Evaluador `53e9f7bd…` = publicado. `VERSION` 2026-11-06.4 en los 3 hosts | `paquete-ae2900e.txt` | Volver a verificar en P0 |
| Excluir `f6dc685` | `~/cf-e4/paquete-f6dc685` intacto, más `paquete-f6dc685.NO-USAR-PARA-VEREDICTO.txt` | Aviso creado. Contenido sin tocar | `paquete-ae2900e.txt` | — |
| Guiones de ejecución | `c7f24510` → `~/cf-e4/ecarga-v2-guiones-c7f24510` (bastión, Sensor1, clientes) | `SHA256SUMS` verifica en los 3 hosts. 14/14 pruebas | `copiar-guiones.txt`, `pruebas-banco.txt` | — |
| Herramientas de evaluación | `e83f4be6` → `~/cf-e4/ecarga-v2-evaluacion-e83f4be6` (Sensor1, bastión) | `SHA256SUMS` verifica en los 2 hosts. 17/17 pruebas | `copiar-eval.txt`, `pruebas-banco.txt` | — |
| Herramientas, permisos y espacio | Sensor1 (`comprobar`), bastión, clientes | Todo OK. 12 GiB y 14 GB libres. `MemAvailable` 6,2 GiB | `comprobar-seco.txt` | Repetir en P0 |
| Relojes y verificadores | 4 hosts. Verificadores de `ae2900e` | NTP sí. `Etc/UTC`. Verificadores 8, 24 y 4 OK, todos con rc 0 | `comprobar-seco.txt` | Repetir en P0 |
| Versión del evaluador | `evaluar_ecarga.py` 2026-11-06.4 | sha256 y `VERSION` en los hosts. Rechaza la plantilla con rc 2 | `paquete-ae2900e.txt`, `plantilla-rc.txt` | — |
| `obs_pcap --en-seco` | Paquete `ae2900e`, fin 1794197760 / 2026-11-09T04:16:00Z | rc 0, `fin_utc` correcto, sin salida | `comprobar-seco.txt` | Repetir en P0 |
| Arranque y parada de los muestreadores | `sensor1_muestreadores.sh` y `muestreo_bastion.sh` (seco) | Arrancan, crecen, se paran con TERM. DIR existente → rc 2 | `comprobar-seco.txt` | — |
| Parada de los generadores (fin y protección) | `generadores.sh parar`, `muestreo_bastion.sh real`, `guardia.py` | Vía de parada real con rc 0 (target ya parado). Guardia probada con 14 casos | `prueba-parada.txt`, `pruebas-banco.txt` | — |
| Cadena de evaluación | `sensor1_post.sh`, `construir_entrada.py`, `veredicto` | Prueba de humo PRUEBA: rc 0, 0 y 1, sin error de contrato | `humo-sensor1.txt` | — |
| Lecturas de S7 y S11 | `obs_p4_post.sh` derivado (solo `O=`) y `precheck.sh` sin cambios | rc 0 en seco. Hashes = O11 | `prueba-s7.txt`, `prueba-s11.txt` | — |
| Entrada y trazabilidad | §4 y las plantillas sin resultados | Contrato y reglas documentados. Nada rellenado | este documento | — |
| **S14** | — | — | §4.4 | **Decisión de Mark: definición publicada antes de T_g, o aceptar `null` / «no demostrable»** |
| Franja | §3.2 del protocolo, **no programada** | Calendario: `weekday()` = 0 | protocolo §3.2 | Volver a comprobar su viabilidad al dar la orden; si no es viable, publicar una franja nueva antes |

## 9. Orden necesaria para ejecutar

Hace falta una orden explícita de Mark que diga:
1. **Autorizo ejecutar E-carga v2 en la franja publicada**: lun 09-nov, P0 02:30Z, T_g 1794193200 (03:00Z), ventana
   1794194100–1794197700, parada 04:17Z. O bien la franja nueva publicada que indique.
2. Que incluye arrancar `cyberflow-lab.target` con `generadores.sh arrancar` en T_g y pararlo en 04:17Z o por la
   guardia.
3. **La decisión sobre S14**: (a) la regla de «saturación nueva» que se publica antes de T_g, o (b) aceptar S14 en
   `null` y, con ello, como mucho «no demostrable».
4. Que la publicación de los resultados en `evidencia/12-ecarga-ejecucion/` se hace sea cual sea el resultado.

Sin esa orden no se ejecuta ni se programa nada.
