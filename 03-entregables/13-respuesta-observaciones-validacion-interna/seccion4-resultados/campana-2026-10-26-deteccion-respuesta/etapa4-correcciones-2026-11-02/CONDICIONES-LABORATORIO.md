# Condiciones del laboratorio antes de la 4A (lectura, 2026-11-02 ≈ 22:00 UTC)

> **Solo lectura.** Nada se instaló, reinició, habilitó, deshabilitó ni editó. Sin sudo. Guiones y salidas literales
> en [`lectura-laboratorio/`](lectura-laboratorio/):
>
> - `[SENSOR1 m4rk]` `l1_sensor_actividad.sh` → `.txt` (21:59:38Z) y `l3_sensor_detalle.sh` → `.txt` (22:00:17Z);
> - `[CLIENTES adminclientes]` `l2_clientes_actividad.sh` → `.txt` (21:59:44Z).
>
> Los tres los lancé yo desde el bastión (`gadmin`), con las llaves de siempre.

## 1. `piloto-con-dns`: es una etiqueta histórica, no una campaña en marcha

| Lectura | Resultado |
|---|---|
| Dataset `artifacts/linea-base/multilayer-v3.csv` | Última fila con `piloto-con-dns`: **2026-09-30T03:20:50Z**. Las últimas 5 000 filas son `linea-base` |
| Quién escribe el dataset | `cyberflow-acumular.service` (timer cada 10 min), con `--campaign-id linea-base` |
| Clientes | 6 perfiles (`cyberflow-lab-*.service`, desde el 1-nov 10:36:59) sin etiqueta de campaña; sin crontab |
| Únicas menciones vivas | `configs/cyberflow.toml:109 campana = "piloto-con-dns"`. Ningún proceso en marcha lo lee para etiquetar: la unidad del acumulador pasa su propio `--campaign-id` |

**Conclusión.** No hay campaña `piloto-con-dns` activa que interfiera con la 4A–4C. La condición del README §5 de la
preparación («`piloto-con-dns` cerrado o declarado compatible por Mark») queda satisfecha por lectura: no hace
falta preguntar. La línea del `toml` se deja como está (no se toca el laboratorio); se anota como residuo.

## 2. Procesos y temporizadores que coinciden con las fases 4A–4C

| Elemento | Frecuencia / estado | Interferencia posible | Tratamiento |
|---|---|---|---|
| `cyberflow-acumular.timer` | cada 10 min (:00, :10, …), lee el anillo PCAP y `eve.json` | CPU y E/S en el Sensor1 durante la extracción | Se registra en `salud`; correlación en el diagnóstico (§4) |
| `cyberflow-limpieza.timer` | cada 5 min; borra `live-*.pcap` con > 15 min | Ninguna sobre el archivador (barre cada 20 s) | Sin cambios |
| `cyberflow-aprendizaje.timer` | 00:30 UTC, Nice 19; último resultado `rechazado` (no despliega) | Carga nocturna | Fuera del intervalo de 4B/4C |
| `logrotate.timer` | 00:00 UTC; `copytruncate` de `eve.json`, HUP a Suricata, `maxsize 500M` | Corta la lectura de EVE; `s30` se para si la detecta | PROTOCOLO-4C §2: el intervalo no contiene la rotación |
| `ppi-publicar-feed.timer` (v1) | cada 10 s | Publica el feed v1 del motor viejo | Lo sustituye la 4A (v2 en sombra) |
| `ppi-dashboard` | continuo | Lectura de logs | Sin cambios |
| Motor viejo `24f8a80` | en marcha desde 1-nov 03:14 | Es el motor que la 4A reemplaza | 4A |
| Suricata | en marcha desde 30-oct 19:55, `NRestarts=0`, af-packet `ens37`, `cluster_flow` | Descartes a ráfagas (§3) | Diagnóstico (§4) |
| Captura `ppi-motor-capture` | tcpdump `-G 15` (la 4A pasa a `-G 5`) | — | 4A |
| cron de sistema | `e2scrub_all`, `sysstat` | `sysstat` puede dar `sar` para correlacionar (no comprobado si recoge) | §4 |

## 3. Descartes de Suricata observados (2-nov, 00:00–22:00 UTC)

De `stats.log` (el rotado `stats.log.1` no es legible sin sudo):

- **77** incrementos de `capture.kernel_drops`, **13 324** descartes en total;
- paquetes 39 030 462 → 71 503 140: **0,041 %** del tramo;
- concentrados a las **09 h (3 492)** y **18 h (3 835)**;
- por minuto de la hora: `:00` 1 291, `:04` 878, `:42` 871, `:11` 822, `:35` 781, `:20` 771 (resto menores).

**No se atribuye causa.** Coincidir con `:00` (acumulador, limpieza, rotación de horas) es una hipótesis, no un
resultado: el resto de minutos con muchos descartes no coincide con ningún temporizador conocido.

Consecuencia para la 4C: con los criterios v3 cualquier descarte en el periodo de un episodio lo hace **C1** (fuera
de la población principal), y I5 exige 0 descartes en los 30 min previos. Con esta tasa, I5 puede no cumplirse.

## 4. Diagnóstico de los descartes, preparado para la 4A (no ejecutado)

Objetivo: saber **cuándo** se producen y **con qué coinciden**, sin cambiar nada de Suricata ni del laboratorio
durante la medida. Se hace dentro del periodo de observación de la 4A (PROCEDIMIENTO §5.3), solo con lecturas.

| # | Medida | Fuente | Cómo se correlaciona |
|---|---|---|---|
| D1 | Serie de `kernel_drops` y `kernel_packets` cada 8 s | `stats.log` (y `stats.log.1` con `sudo -n` si Mark lo permite) | Base de tiempos |
| D2 | Ejecuciones del acumulador, limpieza y aprendizaje | `journalctl -u cyberflow-acumular -u cyberflow-limpieza -u cyberflow-aprendizaje -o short-iso-precise` | Descartes dentro de [inicio, fin] de cada ejecución frente a fuera |
| D3 | Rotación de `eve.json` y HUP | `journalctl -u logrotate`, tamaño de `eve.json` | Ventana ± 60 s de cada rotación |
| D4 | Ráfagas de los perfiles de clientes | PCAP archivado: paquetes/s por origen `10.10.20.21–26` | Descartes frente a tasa de entrada |
| D5 | CPU por hilo de Suricata y del Sensor1 | `sar -u -P ALL` si `sysstat` recoge; si no, `pidstat`/`/proc/<pid>/task/*/stat` muestreado | Saturación de un hilo frente a total |
| D6 | Rotación del anillo de la 4A (`-G 5`) y del archivador | `archivar.log`, mtime de `live-*.pcap` | Descartes frente a escrituras de disco |
| D7 | Contadores de la NIC | `/sys/class/net/ens37/statistics/*` | `rx_missed_errors`/`rx_fifo_errors` (pérdida antes de Suricata) frente a `kernel_drops` |

Reglas del diagnóstico:

- se publica la tabla de coincidencias con su denominador (descartes dentro y fuera de cada tipo de evento) y **no**
  se declara causa sin una coincidencia que se repita y una alternativa descartada;
- ningún ajuste de Suricata (hilos, `ring-size`, `cluster_type`, reglas) durante la 4A–4C; si se propone uno, va en
  una nota aparte para decidir antes de la 4C, con su prueba;
- la observación DNS de 7 días (§5) no se usa para este diagnóstico ni al revés.

## 5. Observación DNS de 7 días y LIMIT: aparte y sin cambios

- La observación sigue **preparada y no iniciada**, tal como está en
  [OBSERVACION-DNS-ETAPA4](../etapa4-preparacion-2026-11-02/OBSERVACION-DNS-ETAPA4.md). Estas lecturas no la inician
  ni la sustituyen.
- El **LIMIT DNS no está aplicado** en ningún sitio (DC1 no se toca; ningún agente lleva `--aplicar`) y no se
  aprueba con nada de lo publicado aquí. Las cifras del banco (734/1 044 del atacante, 0/428 legítimas) siguen
  siendo del banco.

## 6. Lo que no se pudo leer

- `stats.log.1` (permisos de Suricata): el día anterior queda sin serie.
- Si `sysstat` tiene la recogida activa (requiere leer `/etc/default/sysstat` y `/var/log/sysstat/`; no se hizo).
- El estado de srv-dmz y del bastión no se volvió a leer en esta tanda: sigue el
  [ESTADO-OBSERVADO](../etapa4-preparacion-2026-11-02/ESTADO-OBSERVADO-LABORATORIO.md) del mismo día.
