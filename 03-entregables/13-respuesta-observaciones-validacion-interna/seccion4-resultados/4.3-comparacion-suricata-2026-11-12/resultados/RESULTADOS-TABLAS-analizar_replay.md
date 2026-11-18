## Tabla por episodio

| Episodio | Fam. | CF HIB_0.01 (oficial) | CF t datos (s) | CF IF_0.01 / HEUR | CF HIB_0.03 (sens.) | Suricata PRINCIPAL durante / posterior | 1.ª válida (s) | SIDs válidos | Suricata S1 durante | Coincidencia (principal) |
|---|---|---|---|---|---|---|---|---|---|---|
| `dns_inusual-r1` | dns | oportuna | 13.95 | no / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |
| `dns_inusual-r2` | dns | oportuna | 20.59 | no / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |
| `dns_inusual-r3` | dns | oportuna | 13.95 | no / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |
| `dns_inusual-r4` | dns | oportuna | 19.66 | sí / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |
| `dns_inusual-r5` | dns | oportuna | 20.93 | no / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |
| `inundacion_http-r1` | inundacion | oportuna | 5.95 | sí / sí | sí | 836 / 315 | 0.14 | 2221010 SURICATA HTTP unable to match resp | 838 | ambos |
| `inundacion_http-r2` | inundacion | oportuna | 5.11 | sí / sí | sí | 419 / 118 | 0.37 | 2221010 SURICATA HTTP unable to match resp | 421 | ambos |
| `inundacion_http-r3` | inundacion | oportuna | 3.87 | sí / sí | sí | 679 / 179 | 0.08 | 2221010 SURICATA HTTP unable to match resp | 686 | ambos |
| `inundacion_http-r4` | inundacion | oportuna | 3.95 | sí / sí | sí | 282 / 42 | 0.82 | 2221010 SURICATA HTTP unable to match resp | 282 | ambos |
| `inundacion_http-r5` | inundacion | oportuna | 0.85 | sí / sí | sí | 955 / 324 | 0.09 | 2221010 SURICATA HTTP unable to match resp | 956 | ambos |
| `fuerza_bruta_http-r1` | fuerza_bruta | oportuna | 3.95 | sí / sí | sí | 63 / 37 | 8.67 | 2221010 SURICATA HTTP unable to match resp | 63 | ambos |
| `fuerza_bruta_http-r2` | fuerza_bruta | oportuna | 1.99 | sí / sí | sí | 62 / 25 | 0.07 | 2221010 SURICATA HTTP unable to match resp | 60 | ambos |
| `fuerza_bruta_http-r3` | fuerza_bruta | oportuna | 3.62 | sí / sí | sí | 167 / 50 | 1.46 | 2221010 SURICATA HTTP unable to match resp | 167 | ambos |
| `fuerza_bruta_http-r4` | fuerza_bruta | oportuna | 3.95 | sí / sí | sí | 183 / 47 | 1.14 | 2221010 SURICATA HTTP unable to match resp | 183 | ambos |
| `fuerza_bruta_http-r5` | fuerza_bruta | oportuna | 6.34 | sí / sí | sí | 180 / 63 | 0.25 | 2221010 SURICATA HTTP unable to match resp | 180 | ambos |
| `escaneo_sostenido-r1` | escaneo_sostenido | oportuna | 3.31 | sí / sí | sí | 5 / 0 | 0.24 | 2002910 ET SCAN Potential VNC Scan 5800-58; 2010935 ET SCAN Suspicious inbound to MSSQ; 2010936 ET SCAN Suspicious inbound to Orac | 5 | ambos |
| `escaneo_sostenido-r2` | escaneo_sostenido | oportuna | 1.98 | sí / sí | sí | 5 / 0 | 0.13 | 2002910 ET SCAN Potential VNC Scan 5800-58; 2010935 ET SCAN Suspicious inbound to MSSQ; 2010936 ET SCAN Suspicious inbound to Orac | 5 | ambos |
| `escaneo_sostenido-r3` | escaneo_sostenido | oportuna | 5.97 | sí / sí | sí | 5 / 0 | 0.24 | 2002910 ET SCAN Potential VNC Scan 5800-58; 2010935 ET SCAN Suspicious inbound to MSSQ; 2010936 ET SCAN Suspicious inbound to Orac | 5 | ambos |
| `escaneo_sostenido-r4` | escaneo_sostenido | oportuna | 0.81 | sí / sí | sí | 5 / 0 | 0.24 | 2002910 ET SCAN Potential VNC Scan 5800-58; 2010935 ET SCAN Suspicious inbound to MSSQ; 2010936 ET SCAN Suspicious inbound to Orac | 5 | ambos |
| `escaneo_sostenido-r5` | escaneo_sostenido | oportuna | 9.25 | sí / sí | sí | 5 / 0 | 0.23 | 2002910 ET SCAN Potential VNC Scan 5800-58; 2010935 ET SCAN Suspicious inbound to MSSQ; 2010936 ET SCAN Suspicious inbound to Orac | 5 | ambos |
| `escaneo_breve-r4` | escaneo_breve | solo_posterior | 3.94 | no / sí | sí | 0 / 0 | — | — | 0 | solo_CyberFlow |

## Cobertura por familia

| Familia | n | CF HIB_0.01 (principal) | CF IF_0.01 | CF HEUR | CF HIB_0.03 (sens.) | Suricata principal | Suricata S1 (HOME_NET original) | Principal sin `SURICATA *` restantes |
|---|---|---|---|---|---|---|---|---|
| dns_inusual | 5 | 5/5 (100 %; IC95 48–100 %) | 1/5 (20 %; IC95 1–72 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 0/5 (0 %; IC95 0–52 %) | 0/5 (0 %; IC95 0–52 %) | 0/5 (0 %; IC95 0–52 %) |
| inundacion_http | 5 | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 0/5 (0 %; IC95 0–52 %) |
| fuerza_bruta_http | 5 | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 0/5 (0 %; IC95 0–52 %) |
| escaneo_sostenido | 5 | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) | 5/5 (100 %; IC95 48–100 %) |
| escaneo_breve | 1 | 1/1 (100 %; IC95 2–100 %) | 0/1 (0 %; IC95 0–98 %) | 1/1 (100 %; IC95 2–100 %) | 1/1 (100 %; IC95 2–100 %) | 0/1 (0 %; IC95 0–98 %) | 0/1 (0 %; IC95 0–98 %) | 0/1 (0 %; IC95 0–98 %) |
| TOTAL | 21 | 21/21 (100 %; IC95 84–100 %) | 16/21 (76 %; IC95 53–92 %) | 21/21 (100 %; IC95 84–100 %) | 21/21 (100 %; IC95 84–100 %) | 15/21 (71 %; IC95 48–89 %) | 15/21 (71 %; IC95 48–89 %) | 5/21 (24 %; IC95 8–47 %) |

## Coincidencias (CyberFlow HIB_0.01 vs Suricata principal)

| Familia | ambos | solo CyberFlow | solo Suricata | ninguno | indeterminado |
|---|---|---|---|---|---|
| dns_inusual | 0 | 5 | 0 | 0 | 0 |
| inundacion_http | 5 | 0 | 0 | 0 | 0 |
| fuerza_bruta_http | 5 | 0 | 0 | 0 | 0 |
| escaneo_sostenido | 5 | 0 | 0 | 0 | 0 |
| escaneo_breve | 0 | 1 | 0 | 0 | 0 |
| TOTAL | 15 | 6 | 0 | 0 | 0 |

## Sensibilidad: coincidencias con HIB_0.03

| Familia (sensibilidad HIB_0.03) | ambos | solo CyberFlow | solo Suricata | ninguno | indeterminado |
|---|---|---|---|---|---|
| dns_inusual | 0 | 5 | 0 | 0 | 0 |
| inundacion_http | 5 | 0 | 0 | 0 | 0 |
| fuerza_bruta_http | 5 | 0 | 0 | 0 | 0 |
| escaneo_sostenido | 5 | 0 | 0 | 0 | 0 |
| escaneo_breve | 0 | 1 | 0 | 0 | 0 |
| TOTAL | 15 | 6 | 0 | 0 | 0 |

## Latencia comparativa

| Episodio | CyberFlow HIB_0.01 (s, datos) | Suricata (s, paquete) | Δ = Suricata − CF (s) | Lectura |
|---|---|---|---|---|
| `inundacion_http-r1` | 5.95 | 0.14 | -5.81 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `inundacion_http-r2` | 5.11 | 0.37 | -4.74 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `inundacion_http-r3` | 3.87 | 0.08 | -3.79 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `inundacion_http-r4` | 3.95 | 0.82 | -3.13 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `inundacion_http-r5` | 0.85 | 0.09 | -0.76 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `fuerza_bruta_http-r1` | 3.95 | 8.67 | +4.72 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `fuerza_bruta_http-r2` | 1.99 | 0.07 | -1.92 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `fuerza_bruta_http-r3` | 3.62 | 1.46 | -2.16 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `fuerza_bruta_http-r4` | 3.95 | 1.14 | -2.81 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `fuerza_bruta_http-r5` | 6.34 | 0.25 | -6.09 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `escaneo_sostenido-r1` | 3.31 | 0.24 | -3.07 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `escaneo_sostenido-r2` | 1.98 | 0.13 | -1.85 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `escaneo_sostenido-r3` | 5.97 | 0.24 | -5.73 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `escaneo_sostenido-r4` | 0.81 | 0.24 | -0.57 | no concluyente (< 10 s, rejilla de CyberFlow) |
| `escaneo_sostenido-r5` | 9.25 | 0.23 | -9.02 | no concluyente (< 10 s, rejilla de CyberFlow) |

## Control legítimo 30 min

| Detector / configuración | Unidad A: entidad-ventana con señal (de 2218) | Unidad B: ventana de 10 s con señal (de 181) | Alertas/eventos válidos |
|---|---|---|---|
| CyberFlow `HIB_0.01` | 54 (2.43 %) | 54 (29.8 %) | 54 señales entidad-ventana |
| CyberFlow `IF_0.01` | 54 (2.43 %) | 54 (29.8 %) | 54 señales entidad-ventana |
| CyberFlow `HEUR` | 0 (0.00 %) | 0 (0.0 %) | 0 señales entidad-ventana |
| CyberFlow `HIB_0.03` | 200 (9.02 %) | 140 (77.3 %) | 200 señales entidad-ventana |
| CyberFlow `IF_0.03` | 200 (9.02 %) | 140 (77.3 %) | 200 señales entidad-ventana |
| Suricata ET Open — HOME_NET principal | 79 (3.56 %) | 67 (37.0 %) | 184 alertas válidas (de 1812 totales) |
| Suricata ET Open — HOME_NET original (S1) | 79 (3.56 %) | 67 (37.0 %) | 184 alertas válidas (de 504 totales) |

**principal** — excluidas del conteo: {'ET INFO': 1177, 'STREAM': 310}; no contadas (fuera de población/intervalo): {'fuera_de_intervalo': 12, 'entidad_fuera_de_poblacion:10.10.10.30': 129}; firmas contadas: [(2100366, 'GPL ICMP PING *NIX', 172), (2221010, 'SURICATA HTTP unable to match response to request', 11), (2260001, 'SURICATA Applayer Wrong direction first Data', 1)]

**s1** — excluidas del conteo: {'STREAM': 310}; no contadas (fuera de población/intervalo): {'fuera_de_intervalo': 10}; firmas contadas: [(2100366, 'GPL ICMP PING *NIX', 172), (2221010, 'SURICATA HTTP unable to match response to request', 11), (2260001, 'SURICATA Applayer Wrong direction first Data', 1)]
