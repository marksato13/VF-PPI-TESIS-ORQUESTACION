| Segmento | Version | Ciclos | Pared p50/p95/max (s) | CPU p95/max (s) | >10 s | >20 s | Retraso p95/max (s) | Pendientes max/fin | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| normal | 953a436 (ref) | 396 | 0.562/1.301/1.74 | 1.281/1.641 | 0 | 0 | 2.509/2.842 | 96/67 | si | si | - | si |
| normal | 862404e (cand) | 396 | 0.782/2.049/3.744 | 1.953/2.844 | 0 | 0 | 3.323/4.935 | 96/67 | si | si | - | si |
| normal | 6b6ef82 (opt) | 396 | 0.546/1.153/1.597 | 1.125/1.594 | 0 | 0 | 2.383/2.733 | 96/67 | si | si | - | si |
| inundacion_http-r1 | 953a436 (ref) | 18 | 2.65/6.545/6.545 | 6.047/6.047 | 0 | 0 | 7.584/7.584 | 77/66 | si | si | - | si |
| inundacion_http-r1 | 862404e (cand) | 18 | 3.607/8.191/8.191 | 7.906/7.906 | 0 | 0 | 10.355/10.355 | 77/70 | si | si | - | si |
| inundacion_http-r1 | 6b6ef82 (opt) | 18 | 2.798/5.412/5.412 | 5.344/5.344 | 0 | 0 | 6.612/6.612 | 77/68 | si | si | - | si |
| recuperacion-r1 | 953a436 (ref) | 24 | 2.364/6.28/6.639 | 4.781/4.859 | 0 | 0 | 7.851/7.851 | 71/62 | si | si | si | si |
| recuperacion-r1 | 862404e (cand) | 24 | 3.428/5.349/6.048 | 5.25/5.891 | 0 | 0 | 7.214/7.214 | 72/62 | si | si | si | si |
| recuperacion-r1 | 6b6ef82 (opt) | 24 | 1.738/3.37/3.855 | 3.297/3.438 | 0 | 0 | 4.998/4.998 | 71/62 | si | si | si | si |
| inundacion_http-r2 | 953a436 (ref) | 15 | 3.58/11.397/11.397 | 9.5/9.5 | 1 | 0 | 12.639/12.639 | 81/70 | **NO** | si | - | si |
| inundacion_http-r2 | 862404e (cand) | 18 | 4.408/6.989/6.989 | 6.719/6.719 | 0 | 0 | 8.211/8.211 | 77/69 | si | si | - | si |
| inundacion_http-r2 | 6b6ef82 (opt) | 18 | 2.942/5.545/5.545 | 5.359/5.359 | 0 | 0 | 6.552/6.552 | 76/69 | si | si | - | si |
| recuperacion-r2 | 953a436 (ref) | 23 | 3.085/7.239/7.394 | 6.234/6.438 | 0 | 0 | 8.756/8.756 | 74/64 | si | si | si | si |
| recuperacion-r2 | 862404e (cand) | 24 | 1.937/3.986/6.881 | 3.766/6.797 | 0 | 0 | 7.917/7.917 | 74/64 | si | si | si | si |
| recuperacion-r2 | 6b6ef82 (opt) | 24 | 1.734/2.916/3.973 | 2.828/3.891 | 0 | 0 | 5.064/5.064 | 74/64 | si | si | si | si |
| inundacion_http-r3 | 953a436 (ref) | 18 | 2.92/7.65/7.65 | 7.438/7.438 | 0 | 0 | 8.739/8.739 | 73/67 | si | si | - | si |
| inundacion_http-r3 | 862404e (cand) | 13 | 3.967/14.425/14.425 | 13.875/13.875 | 4 | 0 | 30.854/30.854 | 72/72 | **NO** | **NO** | - | si |
| inundacion_http-r3 | 6b6ef82 (opt) | 18 | 2.687/6.151/6.151 | 6.031/6.031 | 0 | 0 | 7.268/7.268 | 72/67 | si | si | - | si |
| recuperacion-r3 | 953a436 (ref) | 24 | 2.432/4.067/4.495 | 3.969/4.391 | 0 | 0 | 5.615/5.615 | 71/60 | si | si | si | si |
| recuperacion-r3 | 862404e (cand) | 18 | 4.329/17.79/17.79 | 17.5/17.5 | 2 | 0 | 25.04/25.04 | 71/60 | **NO** | **NO** | si | si |
| recuperacion-r3 | 6b6ef82 (opt) | 24 | 1.843/3.231/3.97 | 3.172/3.891 | 0 | 0 | 5.119/5.119 | 71/60 | si | si | si | si |
| inundacion_http-r4 | 953a436 (ref) | 18 | 2.377/5.573/5.573 | 5.406/5.406 | 0 | 0 | 6.805/6.805 | 71/65 | si | si | - | si |
| inundacion_http-r4 | 862404e (cand) | 18 | 2.826/8.185/8.185 | 8.125/8.125 | 0 | 0 | 9.246/9.246 | 71/64 | si | si | - | si |
| inundacion_http-r4 | 6b6ef82 (opt) | 18 | 2.32/5.595/5.595 | 5.5/5.5 | 0 | 0 | 6.835/6.835 | 71/65 | si | si | - | si |
| recuperacion-r4 | 953a436 (ref) | 24 | 2.648/4.595/4.681 | 4.438/4.547 | 0 | 0 | 5.781/5.781 | 76/58 | si | si | si | si |
| recuperacion-r4 | 862404e (cand) | 24 | 3.195/6.217/6.825 | 6.078/6.734 | 0 | 0 | 7.861/7.861 | 78/58 | si | si | si | si |
| recuperacion-r4 | 6b6ef82 (opt) | 24 | 1.573/2.946/3.723 | 2.828/3.672 | 0 | 0 | 4.881/4.881 | 76/58 | si | si | si | si |
| inundacion_http-r5 | 953a436 (ref) | 16 | 3.495/9.836/9.836 | 9.391/9.391 | 0 | 0 | 12.475/12.475 | 77/76 | si | si | - | si |
| inundacion_http-r5 | 862404e (cand) | 13 | 5.623/12.274/12.274 | 12.109/12.109 | 4 | 0 | 18.96/18.96 | 75/75 | **NO** | **NO** | - | si |
| inundacion_http-r5 | 6b6ef82 (opt) | 18 | 2.53/6.085/6.085 | 5.984/5.984 | 0 | 0 | 7.194/7.194 | 76/76 | si | si | - | si |
| recuperacion-r5 | 953a436 (ref) | 24 | 2.006/3.892/3.993 | 3.734/3.781 | 0 | 0 | 5.17/5.17 | 80/60 | si | si | si | si |
| recuperacion-r5 | 862404e (cand) | 22 | 4.196/7.167/10.797 | 6.969/10.391 | 1 | 0 | 16.376/16.376 | 82/60 | si | **NO** | si | si |
| recuperacion-r5 | 6b6ef82 (opt) | 24 | 1.617/2.795/3.217 | 2.75/3.141 | 0 | 0 | 4.326/4.326 | 80/60 | si | si | si | si |

Cumple todo: 953a436 (ref) = NO, 862404e (cand) = NO, 6b6ef82 (opt) = SI

### Etapas del motor (suma en s sobre todos los segmentos medidos)

| Etapa | 953a436 (ref) | 862404e (cand) | 6b6ef82 (opt) |
|---|---|---|---|
| decision_y_registro | 0.0 | 0.1 | 0.1 |
| eve_lectura | 15.8 | 19.1 | 23.2 |
| eve_poda | 0.1 | 0.1 | 0.1 |
| expiracion_y_escritura | 0.5 | 0.6 | 0.7 |
| filtro_plano_control | 16.3 | 21.1 | 30.9 |
| pcap_parseo | 66.9 | 85.0 | 100.1 |
| pcap_poda | 67.0 | 101.9 | 85.8 |
| pendientes | 50.2 | 70.5 | 44.4 |
| puntuacion | 14.6 | 18.8 | 22.0 |
| ventanas_por_ancla | 545.3 | 743.3 | 373.0 |

### Memoria y carga del equipo (maximos sobre los segmentos)

| Version | RSS max (MB) | Privada max (MB) | CPU sistema p50 (%) | CPU sistema max (%) | Memoria del equipo max (%) | Disponible min (MB) | Confirmada max / limite (MB) |
|---|---|---|---|---|---|---|---|
| 953a436 (ref) | 1168.3 | 1981.4 | 32.6 (normal) | 83.5 | 97 | 647 | 59850 / 68471 |
| 862404e (cand) | 1167.1 | 1981.0 | 31.5 (normal) | 79.3 | 89 | 3504 | 59227 / 68471 |
| 6b6ef82 (opt) | 1136.2 | 1951.1 | 36.2 (normal) | 66.9 | 84 | 5152 | 61048 / 68471 |
