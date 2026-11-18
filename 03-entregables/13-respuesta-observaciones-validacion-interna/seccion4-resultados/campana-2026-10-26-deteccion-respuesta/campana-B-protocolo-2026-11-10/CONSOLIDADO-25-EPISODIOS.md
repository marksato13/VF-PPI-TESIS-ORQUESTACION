# Tabla de cobertura de los 25 episodios (B3 + B4)

Dos corridas separadas: **B3** = episodios 1-6 (corrida parcial cancelada por decision de Mark tras el episodio 6, ID `4c-20261111T051928Z-2eb2f728a738`; los seis en clase de salud C0) y **B4** = episodios 7-25 (ID `4c-B4-20261111T135745Z-b0ec7e96836a`, los 19 en C0). El orden es el de `orden_completo` del generador. Fuentes: `resultado-b3.json`, `resultado-b4.json`, `resultado-b4-e1-por-destino.json`. E3 y los estados del generador son los formales; no se reclasifican.

| Nº | Tramo | Episodio | Generador | Clase | E1 | E2 | E3 | E4 | E5 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | B3 | `inundacion_http-r4` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 2 | B3 | `fuerza_bruta_http-r4` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 3 | B3 | `dns_inusual-r1` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 4 | B3 | `fuerza_bruta_http-r3` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 5 | B3 | `dns_inusual-r3` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 6 | B3 | `inundacion_http-r3` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 7 | B4 | `fuerza_bruta_http-r1` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 8 | B4 | `escaneo_breve-r4` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 9 | B4 | `escaneo_sostenido-r5` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 10 | B4 | `fuerza_bruta_http-r5` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 11 | B4 | `escaneo_breve-r2` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 12 | B4 | `fuerza_bruta_http-r2` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 13 | B4 | `escaneo_sostenido-r2` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 14 | B4 | `dns_inusual-r4` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 15 | B4 | `escaneo_breve-r5` | completo | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 16 | B4 | `inundacion_http-r2` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 17 | B4 | `inundacion_http-r1` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 18 | B4 | `escaneo_sostenido-r3` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 19 | B4 | `escaneo_sostenido-r1` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 20 | B4 | `dns_inusual-r2` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 21 | B4 | `inundacion_http-r5` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 22 | B4 | `dns_inusual-r5` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 23 | B4 | `escaneo_breve-r3` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 24 | B4 | `escaneo_breve-r1` | completo | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |
| 25 | B4 | `escaneo_sostenido-r4` | incompleto_timeout | C0 | indeterminado → **verificado** (por destino) | cumple | indeterminado | cumple | cumple |

## Totales sobre los 25

| Indicador | cumple/verificado | indeterminado | no aplica | fallido |
|---|---|---|---|---|
| E1 original | 15 | 10 | 0 | 0 |
| E1 lectura por destino | 25 | 0 | 0 | 0 |
| E2 | 20 | 0 | 5 | 0 |
| E3 | 5 | 15 | 5 | 0 |
| E4 | 25 | 0 | 0 | 0 |
| E5 | 20 | 0 | 5 | 0 |

## Cobertura por familia (5 planificados por familia)

| Familia | B3 (episodios) | B4 (episodios) | Total |
|---|---|---|---|
| inundacion_http | 2 (r4, r3) | 3 (r2, r1, r5) | 5 |
| fuerza_bruta_http | 2 (r4, r3) | 3 (r1, r5, r2) | 5 |
| dns_inusual | 2 (r1, r3) | 3 (r4, r2, r5) | 5 |
| escaneo_breve | 0 (-) | 5 (r4, r2, r5, r3, r1) | 5 |
| escaneo_sostenido | 0 (-) | 5 (r5, r2, r3, r1, r4) | 5 |

Estados del generador sobre los 25: completo 17, incompleto_timeout 8. Los 8 `incompleto_timeout` son escaneos de B4 (conservados).

Nota B3 (episodio 6): su E5 es "cumple, retirada explicita" (resultado-b3.json); la puerta D5 de esa corrida devolvio lista=false por el contador descartes_limite (falso bloqueo ya diagnosticado y corregido en B4). No cambia ninguna celda.
Nota E1: la columna muestra el resultado historico y, en los 10 escaneos, la lectura por destino (ver BALANCE-B4.md, «Trazabilidad E1»). El resto de celdas es el resultado formal original.
