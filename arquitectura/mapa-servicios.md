# Mapa de servicios

## En el producto (VM02)

| Servicio | Puerto | Estado | Evidencia |
|---|---|---|---|
| Suricata 8.0.3 | — | Activo | AF_PACKET sobre `ens35` |
| `ppi-motor-capture.service` | — | Activo | Anillo PCAP, `-W 16` (~240 s) |
| `ppi-motor.service` | — | Activo | `--history-seconds 230` |
| `ppi-dashboard.service` | **8788** | Activo | Solo loopback; acceso por túnel SSH |

## En la orquestación (propuesto)

| Servicio | Puerto | Estado | Se levanta cuando |
|---|---|---|---|
| PostgreSQL + pgvector | 5432 | **No desplegado** | Haya >100 documentos que indexar |
| Gitea | 3000 | **No desplegado** | Se necesite revisión por issues |
| JupyterLab | 8888 | **No desplegado** | Haya análisis exploratorio real |
| Hermes Agent | — | **No desplegado** | La coordinación manual no baste |
| Herdr | — | **No desplegado** | Haya procesos largos que sobrevivir |

**Ninguno se despliega por adelantado.** Cada uno necesita un paso concreto que
lo justifique, y su healthcheck antes de considerarse activo.
