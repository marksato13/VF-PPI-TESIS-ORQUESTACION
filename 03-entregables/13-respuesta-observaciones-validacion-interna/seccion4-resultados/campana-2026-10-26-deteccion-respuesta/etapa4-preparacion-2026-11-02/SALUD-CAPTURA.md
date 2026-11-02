# Salud de la captura: medida por fuente y criterios fijados antes de la Etapa 4

Fijado el **2026-11-02**, antes de instalar la 4A y antes de cualquier control (4B) o campaña (4C). Lo que aquí se fija **no se ajusta a la vista de los resultados**. Si algo obliga a apartarse, se para, se documenta la desviación y se decide antes de seguir.

Herramienta: `scripts/etapa4/salud_captura.py` (VERSION `2026-11-02.2`) de la rama `candidato/etapa3-20261102` @ `f9cf801` (la `.1` de `acc6588` daba C0 con cobertura SIGUSR1 incompleta: corregido, ver [etapa4-correcciones-2026-11-02](../etapa4-correcciones-2026-11-02/README.md)). En el Sensor1 queda, tras la fase 1 de la 4A, en `/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py`. Solo lee. Un campo que no se puede leer queda `null` con su `motivo`: **nunca se escribe 0 en su lugar**.

## 1. Correcciones a lo publicado en el cierre de la Etapa 3

| Afirmación anterior | Corrección |
|---|---|
| `MATRIZ.md` §3, punto 5: «`kernel_drops` = 0 en su resumen [de la vía rápida]» | **El resumen de la vía rápida no tiene ese campo.** `via-rapida-resumen.jsonl` lleva solo `bloque_hasta`, `paquetes_tcp` (acumulado del proceso), `bytes_pendientes` y `cpu_s` (`detector_rapido.py`, `modo_flujo`). Los descartes del socket de la vía rápida los da su **tcpdump** con SIGUSR1 (§2.3). `bytes_pendientes` son los bytes de un registro PCAP a medio llegar por la tubería: **no es pérdida ni cola**. |
| `calidad_fuentes.py` §(2) y protocolo 3B §7: «tcpdump solo informa sus descartes al terminar; no medible por intervalo» | Era cierto **con la forma de leerlo del 3B**. tcpdump imprime sus contadores acumulados con **SIGUSR1 sin parar la captura**. Probado en el banco con `-G` + `-Z` y en modo tubería (§2.1). En la Etapa 4 se mide por intervalo. |
| `calidad_fuentes.py`: ficheros de 15 s fijos | La 4A rota el anillo a **5 s**. Con 15 s fijos, perder un fichero de 5 s (salto de 10 s) no se detectaba. Se añadió `--duracion-pcap` (por defecto 15, para reproducir el 3B). La Etapa 4 lo usa con `--duracion-pcap 5`. Prueba: `tests/test_calidad_fuentes_rotacion.py`, 4 casos. |
| Número de PCAP archivados como prueba de continuidad | **No lo es.** La continuidad se juzga por los saltos entre inicios consecutivos (`archivar.log`) **y** por las marcas de paquete (`archivar_captura.sh inventario`). Además, que el anillo no tenga huecos no dice nada de los paquetes que el kernel descartó dentro de un fichero: eso lo da §2.1. |

## 2. Qué se mide en cada fuente

### 2.1 Anillo PCAP (`ppi-motor-capture`, tcpdump `-G 5`)

| Aspecto | Valor |
|---|---|
| Contador | Línea `C packets captured, R packets received by filter, D packets dropped by kernel` del propio tcpdump |
| Obtención | `cf-tcpdump-estadisticas.timer` (cada 30 s, `OnCalendar=*:*:00/30`) ejecuta `systemctl kill --kill-whom=main --signal=SIGUSR1 ppi-motor-capture.service`. Hace falta root porque tcpdump corre como `tcpdump` tras `-Z`. La línea va al journal de la unidad. Se exporta con `sudo -n journalctl -u ppi-motor-capture -o short-iso-precise` (m4rk tiene NOPASSWD para `journalctl`) |
| Unidades | Paquetes. Acumulados desde el arranque de **ese** proceso (PID) |
| Muestreo | Cada 30 s (`AccuracySec=1s`). **Cobertura exigida** (versión `.2`): una lectura en [inicio − 32 s, inicio], otra en [fin, fin + 32 s], ningún hueco entre lecturas consecutivas > **30 + 2 s** (periodo del timer más su tolerancia), un único PID en todo el tramo y contadores válidos (enteros ≥ 0, capturados ≤ recibidos) y no decrecientes dentro del PID. Las lecturas sin hora o sin PID no cuentan. Si falta cualquiera de esas condiciones la clase es **C3** (cobertura insuficiente), nunca C0. Ejemplo reproducido: periodo [10, 110] con lecturas solo en 0 y 120 → C3 (hueco de 120 s) |
| Incremento | `D(fin) − D(inicio)` del **mismo PID** = paquetes que el kernel descartó en el socket de tcpdump en el periodo |
| Reinicio | Cambio de PID (el contador empieza en 0). Un periodo que contiene un cambio de PID es **C3** |
| Lectura correcta | Con D = 0, `R > C` son paquetes en el búfer (en vuelo), **no pérdida**. Banco E3: `R = C + D` al terminar |
| Banco | `deploy/etapa4/banco/ensayo_tcpdump_estadisticas.sh`, E1 (anillo `-G 2 -Z`), E2 (tubería), E3 (`R = C + D`). Salida en `evidencia/banco/ensayo-tcpdump-estadisticas.txt`. **La captura nunca se interrumpió**: el número de ficheros y los paquetes por fichero siguieron igual tras cada señal |

### 2.2 Archivador (`archivar_captura.sh`, 2181af5f…, intervalo 20 s)

| Aspecto | Valor |
|---|---|
| Contador | Líneas `OK live-….pcap`, `FALLO`, `PERDIDO` de `archivar.log` y estado de `ESTADO.txt` (`vistos`, `archivados`) |
| Unidades | **Ficheros**, no paquetes |
| Continuidad | Salto entre inicios consecutivos ≤ 5 + 2 s (`calidad_fuentes.py --duracion-pcap 5`; `salud_captura.py --rotacion 5`), y el inventario por marca de paquete sin `HUECO/REINICIO` |
| Margen | `cyberflow-limpieza.timer` borra los PCAP del anillo con más de 15 min. El archivador barre cada 20 s, de modo que la rotación de 5 s no cambia el margen |
| No prueba | Que no se perdieran paquetes dentro de un fichero (eso es §2.1) ni que el SPAN entregara todo (§2.7) |

### 2.3 Vía rápida (`ppi-via-rapida@ens37`)

| Aspecto | Valor |
|---|---|
| Contador de pérdida | Línea SIGUSR1 de **su** tcpdump (corre como m4rk). El timer señala solo al tcpdump hijo del `bash` principal: SIGUSR1 al `bash` o al `python` los **mataría** |
| Contador de proceso | `via-rapida-resumen.jsonl`: `paquetes_tcp` (acumulado del detector), `bytes_pendientes`, `cpu_s`, `bloque_hasta`. **No hay `kernel_drops`** (§1) |
| Muestreo | Resumen cada `--tic` (0,05 s); SIGUSR1 cada 30 s |
| Cola en la tubería | `capturados(SIGUSR1) − paquetes_tcp` con la tubería drenada debe ser 0. Banco E5: 0. **No es pérdida**: es lo que aún no se leyó. En el Sensor1 también puede aproximarse con `Δwchar(tcpdump) − Δrchar(detector)` de `/proc/<pid>/io`, que existe en el Sensor1 pero no en WSL2: por eso E4 no se ejecutó en el banco |
| Reinicio | Cambio de PID de su tcpdump o `NRestarts` de la unidad |
| Salud | Antigüedad de `bloque_hasta` ≤ 2 s |
| Alcance | Solo clasifica la evaluación de la vía rápida. **No** clasifica la del IF ni la de los heurísticos |

### 2.4 Suricata (EVE, base de L7 y de los heurísticos)

| Aspecto | Valor |
|---|---|
| Contador | `capture.kernel_packets` y `capture.kernel_drops` de `stats.log` (`Total`, todos los hilos) |
| Unidades | Paquetes, acumulados desde el arranque de Suricata |
| Muestreo | Un bloque cada 8 s. Delta entre la última muestra ≤ inicio y la primera ≥ fin (cota conservadora) |
| Reinicio | Baja el `uptime` de la línea `Date:` o decrece un contador. El periodo es C3 |
| Observado el 2-nov | +3 316 descartes de +2 042 102 paquetes en una hora (0,16 %), **a ráfagas**. 0 en los 32 s medidos a las 19:25 |
| Riesgo | Con los criterios v3 (`OBJETIVOS-Y-CRITERIOS` §6.1), cualquier descarte en el periodo de un episodio lo hace **C1** y lo saca de la población principal. El 3B perdió así 9 de 25. Ver la condición S1 (§4) |

### 2.5 Interfaz ens37

`/sys/class/net/ens37/statistics`: `rx_packets`, `rx_dropped`, `rx_missed_errors`, `rx_fifo_errors`, `rx_over_errors`. Son tramas, acumuladas desde el arranque del sistema.

`rx_dropped` crece de forma regular, +140 cada 10 s, también sin carga. Las otras tres están a 0. Su significado en este laboratorio **no está determinado**: puede incluir tramas que la pila no entrega a ningún protocolo, como VLAN sin subinterfaz. Se informa **sin clasificar**.

### 2.6 Detector (motor)

| Aspecto | Valor |
|---|---|
| Contador | `_state-e4/ciclos.jsonl`: `duracion_s`, `retraso_pcap_s` (`inicio_ciclo − marca_pcap`), `ventanas_pendientes`. Registro: decisiones y eventos `ventana_no_evaluada` |
| Pérdida | El motor no descarta paquetes: lee PCAP cerrados. Una ventana **sin decisión** solo se establece contra el inventario (`replay_motor.py` sobre el archivo): estado `ausente`. Un hueco > 20 s entre escrituras se informa, **no prueba pérdida** (protocolo 3B §5) |
| Salud | `retraso_pcap_s` ≤ 25 s (Etapa 2, R2). Es informativo durante el periodo y condición de inicio (§4) |

### 2.7 Espejo (SPAN) frente a sensor

Todos los contadores de §2.1–§2.5 están **en el sensor**: miden lo que el sensor perdió **después** de recibir la trama.

La pérdida **antes** del sensor (switch o puerto espejo, vSwitch o hipervisor) **no es visible**: no hay acceso a los contadores del SPAN. Se declara como límite. Una ausencia de paquetes del ataque en el PCAP (`trafico_observado.py`: `paquetes = 0` o `captura_cubre_ventana = false`) con el sensor en C0 se informa como «**no observado en el sensor; causa no determinable**». No se atribuye al detector.

## 3. Clases del periodo (OBJETIVOS-Y-CRITERIOS v3 §6.1, sin cambios)

| Clase | Condición (la peor que se cumpla) | Uso |
|---|---|---|
| **C3** | Tramo sin muestra > 30 s; reinicio o parada de un componente (PID, `NRestarts`, uptime de Suricata); Suricata sin medida; anillo sin medida o salto > 7 s; archivador sin medida o con `FALLO`/`PERDIDO`; tcpdump del anillo sin lecturas SIGUSR1 que acoten el periodo | Fuera. No evaluable |
| **C2** | tcpdump del anillo con `D` > 0 en el periodo | Fuera de la población principal; cuenta para la regla del 20 % |
| **C1** | Suricata con `kernel_drops` > 0 en el periodo | Fuera de la población principal (L7 incompleta); se publica aparte con sus detecciones |
| **C0** | Ninguna de las anteriores | Población principal |

`salud_captura.py clasificar` aplica exactamente esta tabla.

**Cómo se ejecuta** para que el tcpdump que clasifica sea el del anillo:

- La clase del IF y de los heurísticos se calcula con `--tcpdump-log` **solo del journal de `ppi-motor-capture`**.
- La vía rápida se clasifica en una segunda ejecución con el journal de `ppi-via-rapida@ens37`.

El código acepta cualquier PID que acote el periodo, y por eso se separan los ficheros.

En cada episodio de la 4C el periodo es [`inicio − 60`, `fin + 60`]. En la 4B, cada ventana `w` se clasifica por [`w − 60`, `w`].

## 4. Criterios fijados

### 4.1 Inicio (4B y 4C)

Se evalúan sobre los **30 min anteriores**, con las muestras de `salud_captura.py`. Si alguno falla, **no se empieza**.

| # | Criterio |
|---|---|
| I1 | `ppi-motor`, `ppi-motor-capture`, `ppi-via-rapida@ens37`, `ppi-publicar-feed-v2`, `suricata` y `cf-tcpdump-estadisticas.timer` activos. `NRestarts` sin cambios en los 30 min. ≥ 600 s desde el último arranque del motor y de la captura |
| I2 | NTP sincronizado en Sensor1, bastión, srv-dmz, Kali y clientes. Desfase entre hosts ≤ 0,1 s (`p10b_relojes.sh`) |
| I3 | Anillo sin salto > 7 s. Archivador con `ESTADO.txt` `OK` y sin `FALLO` ni `PERDIDO` |
| I4 | Lecturas SIGUSR1 de los dos tcpdump presentes, separadas ≤ 30 s, con `D` sin incremento |
| I5 | Suricata medido (stats.log avanza). **Solo para la 4C:** 0 `kernel_drops` en los 30 min |
| I6 | Motor con `retraso_pcap_s` ≤ 25 s en todos los ciclos de los 30 min. Vía rápida con `bloque_hasta` de antigüedad ≤ 2 s |
| I7 | ≥ 2 GB libres en `/home` del Sensor1, y el `precheck` del archivador aprobado |
| I8 | Sombra demostrada: `verificar_sensor1.sh`, `verificar_bastion.sh` y `CON_SUDO=1 verificar_srvdmz.sh` sin `FALLO` |

### 4.2 Durante

**Continuar** mientras no se cumpla ninguna condición de pausa. Las clases se calculan después, con las mismas muestras, sin intervenir en vivo.

**Pausa.** No se lanza el episodio siguiente; el que está en curso termina y se conserva con su clase. En la 4B, el tramo se marca como degradado.

| # | Condición de pausa |
|---|---|
| P1 | Reinicio o parada de motor, captura, vía rápida o Suricata |
| P2 | Desfase de reloj > 1 s en cualquier host |
| P3 | Salto del anillo > 7 s, o `FALLO`/`PERDIDO` en el archivador |
| P4 | `D` > 0 en el tcpdump del anillo (C2), o sin lectura SIGUSR1 > 90 s (C3) |
| P5 | Tres episodios **consecutivos** en C1: se pausa para diagnosticar Suricata. No cambia su clasificación |

**Implementación (2026-11-02, corrección del defecto 3).** Estas condiciones las evalúa `scripts/etapa4/vigia_4c.py` (rama candidata @ `f9cf801`) cada 60 s, y el generador de la Kali (`scripts-4c/generar_campana.py`, `99e6bdae…`) no lanza un episodio sin un permiso `continuar` vigente del vigía (válido 150 s, con el nonce de la corrida). Sin lectura de una fuente, la condición correspondiente se da por cumplida (pausa): **una medida ausente nunca vale como limpia**. P2 usa el desfase que mide el propio vigía en cada ronda contra el bastión (sensor y srv-dmz con una lectura de reloj por SSH; la Kali en el mismo intercambio del permiso); un desfase cuya cota de medida supera 1 s cuenta como no medible y pausa. P4 «sin lectura > 90 s» es el umbral `sin_sigusr1`. Detalle y pruebas: [etapa4-correcciones-2026-11-02](../etapa4-correcciones-2026-11-02/TABLA-CORRECCIONES.md).

**Reanudar** solo tras ≥ 5 min seguidos sin ninguna condición de pausa. Si hubo reinicio del motor, además ≥ 230 s de historia. El episodio que se lanza después es el **siguiente del orden publicado**; no se repite ni se reordena.

**Cancelar.** La campaña o el control se cancela y no se reanuda:

| # | Condición de cancelación |
|---|---|
| X1 | Más del 20 % de los episodios ejecutados en C2 o C3 (DISEÑO v3) |
| X2 | Cualquier evento `aplicacion` en la traza del agente, o cualquier cambio del ruleset nft respecto al respaldo (salvo contadores) |
| X3 | Tráfico de ataque hacia un destino fuera de la lista blanca del escenario |

Lectura de X1 que aplica el vigía: se cancela en cuanto el número de episodios en C2 o C3 supera el 20 % de los **25 planificados** (más de 5), es decir, cuando la regla ya no puede cumplirse aunque los restantes salieran limpios. Contar sobre los «ejecutados» cancelaría por un solo episodio C2 al principio (1 de 1 = 100 %). Se fija aquí, antes de ejecutar. X2 lo detecta `estado_sombra.py` (srv-dmz, cada 300 s y en `g01`); X3, los eventos de EVE del origen Kali a destinos fuera de `10.10.10.20` y `10.10.30.10`.

### 4.3 Qué es evaluable

| Elemento | Población principal | Aparte |
|---|---|---|
| Episodio de la 4C | C0 y observación completa (protocolo 3B §6) | C1 y C2, con prefijo `fuera:`. C3 no evaluable. Las detecciones de todos se publican |
| Ventana de la 4B | C0 | C1 y C2 separadas; C3 excluida. Las cotas se calculan solo sobre C0 |
| Vía rápida | Periodo con su tcpdump acotado y `D` = 0, y resumen con antigüedad ≤ 2 s | El resto se informa |

## 5. Comandos de medida

Se ejecutan durante la 4B y la 4C y los deja preparados el procedimiento.

**Arranque del muestreador.** `[SENSOR1 m4rk]` → lo ejecuto yo (solo lectura, sin sudo). `<DIR>` es `/home/m4rk/cf-e4/4b` o `/home/m4rk/cf-e4/4c`, ya creado por el procedimiento.

```
setsid nohup /home/m4rk/cyberflow/.venv/bin/python -I \
  /home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py muestrear \
  --salida <DIR>/salud/muestras.jsonl \
  --suricata-stats /var/log/suricata/stats.log --interfaz ens37 \
  --unidad ppi-motor --unidad ppi-motor-capture --unidad ppi-via-rapida@ens37 \
  --unidad ppi-publicar-feed-v2 --unidad suricata \
  --anillo /var/lib/ppi-motor-capture --archivador <DIR>/archivo-pcap \
  --resumen-rapida /home/m4rk/feed-v2/via-rapida-resumen.jsonl \
  --ciclos /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl \
  --hijos-de-unidad ppi-via-rapida@ens37 --intervalo 10 \
  > <DIR>/salud/muestrear.out 2>&1 < /dev/null &
echo $! > <DIR>/salud/muestrear.pid
```

- **Resultado esperado:** una línea por cada 10 s en `muestras.jsonl`.
- **Parada:** si en 60 s no hay ≥ 5 líneas, o alguna fuente sale con `ok: false` salvo `proc_io` del tcpdump del anillo (que da `PermissionError`, esperado), no se empieza.

**Exportación de las lecturas SIGUSR1.** `[SENSOR1 m4rk]` → lo ejecuto yo (NOPASSWD para `journalctl`).

```
sudo -n journalctl -u ppi-motor-capture --since "<desde ISO>" -o short-iso-precise --no-pager \
  > <DIR>/salud/tcpdump-anillo.log
sudo -n journalctl -u ppi-via-rapida@ens37 --since "<desde ISO>" -o short-iso-precise --no-pager \
  > <DIR>/salud/tcpdump-via.log
grep -c 'packets captured' <DIR>/salud/tcpdump-anillo.log <DIR>/salud/tcpdump-via.log
```

- **Resultado esperado:** unas 2 líneas por minuto en cada fichero.
- **Parada:** 0 líneas en cualquiera de los dos. Indica que el timer no funciona: es C3 y se pausa.

**Incrementos y clasificación de un periodo.** `[SENSOR1 m4rk]` → lo ejecuto yo.

```
P=/home/m4rk/cyberflow/.venv/bin/python; S=/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py
$P -I $S intervalos <DIR>/salud/muestras.jsonl <DIR>/salud/incrementos.jsonl
$P -I $S clasificar --incrementos <DIR>/salud/incrementos.jsonl \
  --tcpdump-log <DIR>/salud/tcpdump-anillo.log --desde <ISO> --hasta <ISO> --rotacion 5
$P -I $S clasificar --incrementos <DIR>/salud/incrementos.jsonl \
  --tcpdump-log <DIR>/salud/tcpdump-via.log --desde <ISO> --hasta <ISO> --rotacion 5
```

- **Resultado esperado:** JSON con `clase` C0–C3, `motivos` e `info`. La primera ejecución vale para el IF y los heurísticos; la segunda, para la vía rápida.

**Calidad de fuentes por episodio** (análisis de la 4C). `[SENSOR1 m4rk]` → lo ejecuto yo.

```
python3 -I <CAMPAÑA>/scripts/calidad_fuentes.py --marcas <DIR>/corrida/marcas.jsonl \
  --stats <DIR>/eve/stats-inicio.log /var/log/suricata/stats.log \
  --archivador <DIR>/archivo-pcap/archivar.log --muestras <DIR>/recursos/muestras.jsonl \
  --duracion-pcap 5 --salida <DIR>/analisis/calidad-fuentes.json
```

`<CAMPAÑA>` es la copia del directorio `scripts/` de la campaña en el sensor, con su hash verificado.

## 6. Qué queda pendiente de medir en vivo

- **Línea base SIGUSR1 del anillo real.** Hoy es imposible sin root: tcpdump corre como `tcpdump`, y el timer llega con la 4A. Hasta tener ≥ 30 min de lecturas tras la 4A, el estado del socket de tcpdump es **desconocido**, no cero.
- **Diagnóstico de los descartes de Suricata (S1).** Antes de la 4C hay que saber si las ráfagas coinciden con algo identificable: rotación de `eve.json` con `copytruncate`, ráfagas de los perfiles `descargas`/`erratico`, o el `cluster_flow` con 4 hilos. Si no se identifica la causa y siguen apareciendo, la 4C se puede ejecutar, pero con el riesgo declarado de perder episodios por C1. **No** se cambia la clasificación.
- **Significado de `rx_dropped`** de ens37: se sigue informando sin clasificar.
- **Retardo del espejo** frente al reloj del Sensor1: `trafico_observado.py` da `retraso_primer_paquete_s` (primer paquete observado − inicio del generador). Es una cota que incluye la espera del propio generador; no es el retardo del SPAN aislado.
