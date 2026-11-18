# Respaldo local de los registros no publicados (resumen)

Los PCAP originales, los `eve.json.gz` completos y los registros internos **no se publican**. Se copiaron el 11-nov-2026 a una carpeta local del equipo de trabajo del autor (fuera del repositorio) y se verificaron contra los hashes publicados. Los originales siguen además en el Sensor1 (PCAP y registros del motor) y en el comparador (salidas de Suricata), lo que da una segunda copia independiente; no se subieron a ningún servicio externo.

| Contenido | Archivo local | Bytes | sha256 | Verificación |
|---|---|---|---|---|
| 1.583 PCAP de 5 s (21 episodios + control), tal como los archivó el Sensor1 | `pcap.tar` | 1,120,552,960 | `ec44a812e3b9d0fb8f28c224af8449a2e2a470dce035a0966f0b231b1fa4e94e` | 1583/1583 ficheros con sha256 igual al de `protocolo/pcap-lista-fija.csv` |
| Salidas de Suricata de las 22 rebanadas × 2 configuraciones (`eve.json.gz`, `alertas.jsonl`, `suricata.log`, `hashes.txt`, `rc.txt`, `resumen-eve.json`) y los `.estado`/`.log` por rebanada | `eve-comparador.tar` | 243,384,320 | `1e7d3223a8613116ad32494ae0dde811c1c95cbbfacf912f5e087e47025ea391` | 44/44 `eve.json.gz` con sha256 igual a `manifiestos/trazabilidad-rebanadas.csv` (`*_eve_gz_sha256`); `eve.json` sin comprimir coincide con `*_eve_sha256` en las comprobadas |
| Registros internos de la corrida: `motor_decision.log`, `marcas.jsonl`, `ciclos.jsonl`, `SHA256SUMS` | `registros-sensor1.tar` | 170,096,640 | `a3e24bb8c6cb81e5e1a95061dc54e577bd17fbb718cd168de48181cba9835554` | `motor_decision.log` y `marcas.jsonl` con los sha256 de `manifiestos/REFERENCIAS-ORIGINALES.md` |
| Espacio de trabajo del análisis (scripts, listas, extractos, inventario, constructores del paquete) | `trabajo/` | — | — | copia de los archivos usados |

Los hashes de los `.tar` son del contenedor local y se calcularon al terminar la copia; los hashes que respaldan las cifras son los de cada fichero original (tablas anteriores).
