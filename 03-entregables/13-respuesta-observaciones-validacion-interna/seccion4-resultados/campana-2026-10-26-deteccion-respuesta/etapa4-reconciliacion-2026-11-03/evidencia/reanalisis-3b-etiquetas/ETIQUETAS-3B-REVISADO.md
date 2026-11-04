| Episodio | Principal | Oportunas (cualquiera) | Señal IF | Regla prevista | Otra regla | Reglas oportunas |
|---|---|---|---|---|---|---|
| dns_inusual-r1 | sí | 7 | 7 | 7 | 0 | dns_entropy |
| dns_inusual-r2 | sí | 7 | 0 | 7 | 0 | dns_entropy |
| dns_inusual-r3 | no | 8 | 0 | 8 | 0 | dns_entropy |
| dns_inusual-r4 | sí | 6 | 0 | 6 | 0 | dns_entropy |
| dns_inusual-r5 | no | 8 | 7 | 6 | 2 | dns_entropy, http_abuse |
| escaneo_breve-r1 | sí | 1 | 1 | 0 | 1 | brute_force |
| escaneo_breve-r2 | sí | 0 | 0 | 0 | 0 | — |
| escaneo_breve-r3 | sí | 0 | 0 | 0 | 0 | — |
| escaneo_breve-r4 | no | 0 | 0 | 0 | 0 | — |
| escaneo_breve-r5 | sí | 0 | 0 | 0 | 0 | — |
| escaneo_sostenido-r1 | no | 3 | 3 | 3 | 0 | port_scan |
| escaneo_sostenido-r2 | sí | 4 | 4 | 4 | 0 | port_scan |
| escaneo_sostenido-r3 | sí | 5 | 5 | 0 | 4 | brute_force |
| escaneo_sostenido-r4 | sí | 4 | 4 | 4 | 0 | port_scan |
| escaneo_sostenido-r5 | sí | 3 | 3 | 3 | 0 | port_scan |
| fuerza_bruta_http-r1 | sí | 8 | 8 | 8 | 0 | brute_force |
| fuerza_bruta_http-r2 | no | 8 | 8 | 8 | 0 | brute_force |
| fuerza_bruta_http-r3 | no | 8 | 8 | 8 | 0 | brute_force |
| fuerza_bruta_http-r4 | sí | 8 | 8 | 8 | 0 | brute_force |
| fuerza_bruta_http-r5 | sí | 8 | 8 | 8 | 0 | brute_force |
| inundacion_http-r1 | no | 8 | 8 | 8 | 0 | http_abuse |
| inundacion_http-r2 | no | 8 | 8 | 8 | 0 | http_abuse |
| inundacion_http-r3 | no | 8 | 8 | 8 | 0 | http_abuse |
| inundacion_http-r4 | no | 8 | 8 | 8 | 0 | http_abuse |
| inundacion_http-r5 | sí | 6 | 6 | 6 | 0 | http_abuse |

| Familia (población principal) | Episodios | Con alguna emisión oportuna | Con señal IF oportuna | Con regla prevista oportuna | Solo otra regla |
|---|---|---|---|---|---|
| dns_inusual | 3 | 3 | 1 | 3 | 0 |
| escaneo_breve | 4 | 1 | 1 | 0 | 0 |
| escaneo_sostenido | 4 | 4 | 4 | 3 | 0 |
| fuerza_bruta_http | 3 | 3 | 3 | 3 | 0 |
| inundacion_http | 1 | 1 | 1 | 1 | 0 |
| **Total** | 15 | 12 | 10 | 10 | 0 |
