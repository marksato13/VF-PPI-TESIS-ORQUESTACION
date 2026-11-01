# Diagnóstico de los descartes de Suricata por capas (Etapa 2, punto 3)

Solo lecturas en el sensor, sin sudo, el 1-nov-2026 a las 21:08Z y a las 21:48Z. No se cambió ninguna configuración ni se reinició ningún servicio.

- Evidencia literal: [evidencia/sensor-suricata-capas-2026-11-01T2108Z.txt](evidencia/sensor-suricata-capas-2026-11-01T2108Z.txt) y [evidencia/sensor-afpacket-efectivo-2026-11-01T2148Z.txt](evidencia/sensor-afpacket-efectivo-2026-11-01T2148Z.txt).
- Diagnóstico por intervalos del 3B (deltas cada 8 s): `../revision-3b-2026-11-01/diagnosticos/suricata-descartes.json`.

## 1. Acumulados frente a deltas

| Contador | Tipo | Desde | Valor | Uso correcto |
|---|---|---|---|---|
| `kernel_drops` de Suricata (eve stats) | acumulado del proceso | 30-oct 19:55:21 (PID 1372) | 8835 de 33 972 730 (0,026 %) | Solo dice que hubo pérdida en algún momento. Mezcla campañas, controles y el replay posterior al 3B. |
| Delta de `kernel_drops` cada 8 s (`stats.interval: 8`) | delta | 3B, 07:24–10:35 | 3232 de 9 436 692 (0,034 %) en **21 de 1431 intervalos** | Sitúa la pérdida en el tiempo y es lo que se cruza con episodios, CPU y motor. |
| `rx_dropped` de ens37 | acumulado desde el arranque del SO | hace 2 días | 2 485 235 | No es pérdida de captura (ver capa 2). |
| Descartes de tcpdump (SIGUSR1) | acumulado del proceso | 30-oct 19:55 → 1-nov 10:51 | 0 | Socket propio de tcpdump; no cubre el SPAN. |

**Regla para las campañas:** el criterio de «captura sin errores» usa siempre **deltas** en `[inicio − 120 s, fin + 90 s]`, nunca el acumulado. Es el criterio que ya aplicaba el analizador del 3B.

## 2. Capas

| Capa | Medida | Resultado | Lectura |
|---|---|---|---|
| 0. Espejo (SPAN del conmutador) | No medible desde el sensor | — | **Abierta.** Ni tcpdump ni Suricata ven lo que el SPAN no entrega. Hacen falta los contadores del puerto espejo del conmutador (M-S5). |
| 1. NIC vmxnet3 (ens37) | `rx_missed_errors`, `rx_fifo_errors`, `rx_over_errors` | 0, 0, 0 | Sin pérdida en el anillo RX de la NIC (1024 de 4096 posibles). Las líneas «ring full» de ethtool son contadores de **TX**; no aportan nada sobre RX. |
| 1b. `rx_dropped` = 2 485 235 | Contador del kernel | — | Paquetes que la pila descarta **después** de entregarlos a los sockets AF_PACKET (por ejemplo, tráfico de otras MAC o VLAN sin manejador). Lo demuestra la fila siguiente: Suricata recibió prácticamente todo lo que entró por la NIC. |
| 2. Pila (softnet) | `/proc/net/softnet_stat`, columnas 2 y 3 | dropped 0 en las 4 CPU; time_squeeze 0x213–0x338 | Sin pérdida en el backlog. |
| 3. Entrega a sockets | `kernel_packets` de Suricata frente a `rx_packets` de la NIC | 33 972 730 frente a 33 974 053 | Coinciden al 99,996 %: los paquetes llegan a la capa de sockets. |
| 4. Socket AF_PACKET de **Suricata** (4 hilos W#01–04, `cluster_flow`) | `kernel_drops` | 8835 acumulados; 3232 en el 3B | **Aquí está la pérdida.** El kernel no pudo escribir en el anillo del socket porque los hilos no lo vaciaban a tiempo. |
| 4b. Socket AF_PACKET de **tcpdump** (`-B 65536` = 64 MiB) | Contador del proceso | 0 | El mismo tráfico, con un búfer explícito grande, no pierde. Por eso el PCAP (contenido del modelo, L3/L4) está completo. |
| 5. PCAP y EVE | — | PCAP completo; EVE incompleto en los 21 intervalos | Las características L7 (11 de 28, del EVE) pueden subestimarse en esos intervalos; las 17 de PCAP, no. |

**Conclusión por capas (demostrada):** la pérdida no ocurre en la NIC, ni en softnet, ni en la entrega a sockets. Ocurre en el vaciado del anillo AF_PACKET de Suricata. tcpdump no pierde nada en el mismo periodo.

**Causa (no demostrada):** no se sabe qué hace que el anillo de Suricata se llene en esos 21 intervalos.

## 3. Hipótesis abiertas y medición que las decide

| Id | Hipótesis | A favor | En contra | Medición que la decide |
|---|---|---|---|---|
| H1 | Anillo AF_PACKET por defecto demasiado pequeño para ráfagas | `ring-size`, `tpacket-v3`, `use-mmap` y `block-size` comentados: valen lo que diga el código de 7.0.3 («computed with respect to max-pending-packets [1024] and number of threads»); tcpdump, con 64 MiB, no pierde | Hay pérdidas con el sensor en reposo (07:28:57, CPU 0,09) | **M-S1** (sudo, solo lectura): tamaño efectivo del anillo, con `suricata --dump-config` más los valores por defecto del código, o con `ss -0 -e -m` / `/proc/1372/maps` como root |
| H2 | Un flujo intenso cae entero en un solo hilo (`cluster_flow`) y desborda su anillo mientras los otros están libres | El mayor episodio (08:34:02–08:34:42, 1146 descartes) cae dentro de `inundacion_http-r3`: un único origen y servicio | `inundacion_http-r5` no perdió | **M-S2:** `kernel_drops` **por hilo** (`stats: threads: yes`, cambio C1) durante un control |
| H3 | Competencia de CPU con el motor (ciclos pesados) | 08:34 coincide con el motor al 95 % de una CPU y un ciclo de 10,06 s; ningún servicio tiene afinidad, Nice ni cuota | El ciclo de 10,61 s de las 09:53 no tuvo pérdidas | **M-S3:** `pidstat -t -p <suricata>` y `-p <motor>` cada 1 s durante un control, cruzado con los deltas por hilo |
| H4 | Competencia con el replay offline después de la campaña (10:25–10:31) | Coincide en el tiempo | Solo explica ese tramo | Ya no aplica: los replays de la Etapa 2 se hicieron fuera del sensor |
| H5 | Pérdida aguas arriba (SPAN) | — | No explicaría `kernel_drops`; es otra pérdida, que no se ve | **M-S5:** contadores del puerto espejo del conmutador |

## 4. Cambios candidatos (NO aplicados)

Orden recomendado: primero medir y después cambiar una sola cosa cada vez.

| Id | Cambio en `/etc/suricata/suricata.yaml` | Para qué | Riesgo |
|---|---|---|---|
| C1 | `stats: threads: yes` | Medir H2 y H3 (diagnóstico, no corrige) | stats.log más grande; el EVE de stats no cambia |
| C2 | En `af-packet` de ens37: `use-mmap: yes`, `tpacket-v3: yes`, `ring-size: 8192`, `block-size: 1048576` | H1: un anillo más grande absorbe ráfagas | Memoria por hilo (unos 8192 × tamaño de trama); comprobar con `free` antes y después. **No usar tpacket-v3 en modo IPS** (aquí es IDS). |
| C3 | Unidad de Suricata: `CPUAffinity=1 2 3`; unidad del motor: `CPUAffinity=0` o `Nice=5` | H3: el motor no compite con los hilos de captura | El motor puede ir más lento; medir con `ciclos.jsonl` |
| C4 | `ethtool -G ens37 rx 4096` | NIC (hoy sin pérdida) | Prioridad baja: la capa 1 no pierde |

## 5. Procedimiento reversible (preparado; lo ejecuta Mark porque necesita sudo)

Bloque para `[SENSOR1 m4rk]` → **lo ejecutas tú**: necesita `sudo` con contraseña y reinicia Suricata. Hacerlo en una ventana sin campaña.

```bash
# 0. Medicion previa (solo lectura)
sudo suricata --dump-config | grep -E '^af-packet\.0\.' ; sudo ss -0 -e -m | head -40
# 1. Respaldo con huella
sudo cp -a /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.pre-etapa2
sha256sum /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.pre-etapa2
# 2. Un solo cambio (C1, y despues C2 en otra ventana), editando a mano
sudoedit /etc/suricata/suricata.yaml
# 3. Validar la configuracion ANTES de reiniciar
sudo suricata -T -c /etc/suricata/suricata.yaml -v
# 4. Aplicar y comprobar
sudo systemctl restart suricata && sleep 20 && systemctl is-active suricata
tail -n 60 /var/log/suricata/stats.log | grep -E 'capture.kernel_(packets|drops)'
# 5. Reversion (si algo falla o empeora)
sudo cp -a /etc/suricata/suricata.yaml.pre-etapa2 /etc/suricata/suricata.yaml
sudo suricata -T -c /etc/suricata/suricata.yaml && sudo systemctl restart suricata
```

**Criterio de éxito de C2:** en un control de 2 h con el mismo tráfico, deltas de `kernel_drops` = 0 en todos los intervalos de 8 s, y que la memoria disponible no baje de 3 GB.

**Estado:** diagnóstico por capas hecho. Causa no demostrada; queda pendiente de M-S1 a M-S3. No se ha aplicado ningún cambio.
