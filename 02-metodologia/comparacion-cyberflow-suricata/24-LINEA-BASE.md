# 24 · Línea base normal (justificación de umbrales)

**Fecha:** 2026-10-05 · **Ventana:** `19:45:31Z`–`19:50:17Z` (20 PCAP del anillo,
~5 min, **sin ataque**). Mismo pipeline que el detector desplegado (extractor v2).
**Objetivo:** sustentar los escenarios y umbrales con el comportamiento normal
medido ("anómalo = lo que supera lo normal"), indicación directa del asesor.

> **Nota del espejo:** el SPAN muestra cada trama **≈2 veces** (sesión `Both`). Las
> cifras de red van **×2** respecto al enlace real; se reportan así (consistente con
> el detector, que ve lo mismo) y se indica la mitad aproximada.

## Red (nivel enlace, desde los PCAP)
| Métrica | SPAN (medido) | Enlace real (≈ mitad) |
|---|---|---|
| Paquetes/s | 58,3 | ~29 |
| Throughput | ~68 kbps | ~34 kbps |
| Tamaño medio de paquete | 147 B | 147 B |

(17 190 tramas en 295 s. `mean_ip_len_10s`: mediana 56 B, p95 190 B, máx 821 B.)

## Rangos normales por entidad (527 ventanas, 19 entidades, **excluida la Kali**)
| Feature | mediana | p95 | máx |
|---|---|---|---|
| `dns_query_count_60s` | 0 | **8** | **8** |
| `unique_dns_name_ratio_60s` | 0 | 0,125 | 0,5 |
| `dns_query_rate_60s` | 0 | 0,13 | 0,13 |
| `http_request_count_60s` | 0 | 0 | 10 |
| `flow_attempt_count_30s` | 0 | 7 | 71 |
| `unique_dst_port_ratio_30s` | 0 | 0,5 | 1,0 |
| `syn_completion_ratio_10s` | 0 | 0 | 1,0 |

## Justificación de los umbrales de ataque (anómalo = supera lo normal)
| Familia | Feature | Normal (p95 / máx) | Umbral detector | Ataque observado |
|---|---|---|---|---|
| **DNS** (E3) | `dns_query_count_60s` | 8 / 8 | ≥ 20 | **280** |
| **DNS** (E3) | `unique_dns_name_ratio_60s` | 0,125 / 0,5 | ≥ 0,45 (corregido) | 0,5 |
| **Scan** (E1) | `flow_attempt_count_30s` | 7 / 71 | ≥ 20 | por medir |
| **Scan** (E1) | `unique_dst_port_ratio_30s` | 0,5 / 1,0 | ≥ 0,5 | por medir |
| **Brute** (E2) | `http_request_count_60s` | 0 / 10 | ≥ 5 (+≥80% fallo) | por medir |
| **Flood** (E4) | `http_request_count_60s` | 0 / 10 | ≥ 100 | por medir |

- **DNS:** el conteo normal **nunca pasa de 8/60s**; el ataque llegó a **280** → el
  umbral de 20 queda **holgadamente por encima de lo normal**. Justificado.
- **Umbral DNS corregido (0,45) validado:** **0 de 527** ventanas normales
  dispararían `dns_entropy(0.45)` → **FPR = 0 %** en esta base, mientras detecta el
  ataque en ~1 s. El `≥20` por sí solo ya separa (normal máx 8 < 20).
- **Scan/Brute/Flood:** el umbral exige **varias condiciones a la vez** (p.ej.
  scan = ≥20 intentos **y** ≥50 % puertos únicos **y** ≤30 % handshakes). El normal
  alcanza alguna aislada (flow 71, port-ratio 1,0) pero **no las tres juntas**; se
  confirmará al correr E1/E2/E4.

## Limitaciones (honestas)
- Ventana **corta (~5 min)** y en horario de **poca actividad de los clientes**
  `.21-.26` (no aparecen con tráfico de aplicación en esta ventana; dominan IP de
  infraestructura `.x.2`). Para blindar la tesis conviene una **base más larga en
  horario activo** (p.ej. 1 h con los 6 perfiles generando) → repetir y promediar.
- Cifras de red **dobladas por el espejo**; se reporta la mitad como aproximación
  al enlace real.

## Efecto en el plan
- Cierra en gran parte **P0-06** (umbrales ya **justificados por la base**, no
  arbitrarios) para DNS; faltan los números de ataque de E1/E2/E4.
- Habilita **desplegar el fix del DNS** (umbral 0,45) con FPR 0 % comprobado en esta
  base — pendiente del OK de Mark (cambia el enforcement en vivo) y de una base más
  larga para confirmar.
