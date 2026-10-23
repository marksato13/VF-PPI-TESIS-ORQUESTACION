# 4.1 (fleco 1) - Deteccion por familia del MODELO LIMPIO

Criterio OBSERVABLE (nota M, errata): DNS si dns_query_count_60s>0; si no HTTP si http_request_count_60s>0; resto escaneo.

| Familia | Ventanas | Detectadas (IF limpio) | TPR |
|---|---:|---:|---:|
| HTTP | 43 | 35 | 81.4% |
| escaneo | 33 | 19 | 57.6% |
| DNS | 8 | 0 | 0.0% |
| **Total** | **84** | **54** | **64.3%** |

Contraste nota M (modelo contaminado, mismo criterio): HTTP 35/43 - escaneo 19/33 - DNS 0/8.