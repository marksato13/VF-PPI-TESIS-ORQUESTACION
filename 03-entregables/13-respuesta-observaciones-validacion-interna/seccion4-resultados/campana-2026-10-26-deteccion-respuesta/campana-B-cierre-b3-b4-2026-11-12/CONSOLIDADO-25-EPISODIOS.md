# Consolidado de los 25 episodios de la Campana B (B3 + B4)

Campana B = respuesta real con el agente `--aplicar` limitado a la Kali 10.10.20.30. Los 25 episodios previstos (5 por familia) se ejecutaron en **dos tramos de corridas separadas**: **B3** (episodios 1-6, corrida parcial `4c-20261111T051928Z-2eb2f728a738`, cancelada por decision de Mark tras el episodio 6) y **B4** (episodios 7-25, corrida nueva `4c-B4-20261111T135745Z-b0ec7e96836a`, completa). Cada episodio proviene de una de ellas; ninguno procede de B1 ni de B2 (ver `HISTORIAL-CAMPANA-B.md`).

## Denominadores

| Concepto | Valor |
|---|---|
| Episodios previstos | 25 (5 por familia: inundacion_http, fuerza_bruta_http, dns_inusual, escaneo_breve, escaneo_sostenido) |
| Ejecutados | 25 = **B3: 6** (episodios 1-6) + **B4: 19** (episodios 7-25) |
| Estado del generador | completo 17, `incompleto_timeout` 8 (todos escaneos de B4); ninguno excluido del analisis |
| Clase de salud de la captura | C0 en los 25 (B3 6/6, B4 19/19) |
| E1, E4 | denominador 25 |
| E2, E3, E5 | denominador **20** (los 5 episodios `dns_inusual` son `no aplica`: DC1 no tiene punto de aplicacion) |

## Tabla de los 25 episodios

Resultado **formal** (analisis original, sin modificar) en E2-E5. En E1 se muestra el formal original y, cuando difiere, el **reanalisis por destino** (ver `reanalisis/`).

| N | Tramo | Episodio | Generador | Clase | E1 | E2 | E3 | E4 | E5 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | B3 | `inundacion_http-r4` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 2 | B3 | `fuerza_bruta_http-r4` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 3 | B3 | `dns_inusual-r1` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 4 | B3 | `fuerza_bruta_http-r3` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 5 | B3 | `dns_inusual-r3` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 6 | B3 | `inundacion_http-r3` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 7 | B4 | `fuerza_bruta_http-r1` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 8 | B4 | `escaneo_breve-r4` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 9 | B4 | `escaneo_sostenido-r5` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 10 | B4 | `fuerza_bruta_http-r5` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 11 | B4 | `escaneo_breve-r2` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 12 | B4 | `fuerza_bruta_http-r2` | completo | C0 | verificado | cumple | cumple | cumple | cumple |
| 13 | B4 | `escaneo_sostenido-r2` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 14 | B4 | `dns_inusual-r4` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 15 | B4 | `escaneo_breve-r5` | completo | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 16 | B4 | `inundacion_http-r2` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 17 | B4 | `inundacion_http-r1` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 18 | B4 | `escaneo_sostenido-r3` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 19 | B4 | `escaneo_sostenido-r1` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 20 | B4 | `dns_inusual-r2` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 21 | B4 | `inundacion_http-r5` | completo | C0 | verificado | cumple | indeterminado | cumple | cumple |
| 22 | B4 | `dns_inusual-r5` | completo | C0 | verificado | no aplica | no aplica | cumple | no aplica |
| 23 | B4 | `escaneo_breve-r3` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 24 | B4 | `escaneo_breve-r1` | completo | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |
| 25 | B4 | `escaneo_sostenido-r4` | incompleto_timeout | C0 | indeterminado -> **verificado** (reanalisis) | cumple | indeterminado | cumple | cumple |

## Totales

| Indicador | Denominador | cumple/verificado | indeterminado | no aplica | fallido |
|---|---|---|---|---|---|
| E1 formal original | 25 | 15 | 10 | 0 | 0 |
| E1 reanalisis por destino | 25 | 25 | 0 | 0 | 0 |
| E2 | 20 | 20 | 0 | 5 | 0 |
| E3 formal | 20 | 5 | 15 | 5 | 0 |
| E4 | 25 | 25 | 0 | 0 | 0 |
| E5 | 20 | 20 | 0 | 5 | 0 |

Por tramo (E1 formal original / E3 formal): **B3** E1 6/6 verificado; E3 2 cumple (fuerza bruta), 2 indeterminado (inundacion), 2 no aplica (DNS). **B4** E1 9/19 verificado y 10 indeterminado (escaneos, por herramienta); E3 3 cumple, 13 indeterminado (3 inundacion + 10 escaneos), 3 no aplica.

## Cobertura por familia y tramo

| Familia | B3 | B4 | Total |
|---|---|---|---|
| inundacion_http | 2 (r4, r3) | 3 (r2, r1, r5) | 5 |
| fuerza_bruta_http | 2 (r4, r3) | 3 (r1, r5, r2) | 5 |
| dns_inusual | 2 (r1, r3) | 3 (r4, r2, r5) | 5 |
| escaneo_breve | 0 (-) | 5 (r4, r2, r5, r3, r1) | 5 |
| escaneo_sostenido | 0 (-) | 5 (r5, r2, r3, r1, r4) | 5 |

## Los ocho `incompleto_timeout` (todos B4, conservados)

El generador termino el proceso (`nmap`, codigo -15) al agotar el tope del episodio. No se reclasifican, no se excluyen y no se repiten en este cierre.

| N | Episodio | Duracion (s) | Tope (s) | E2 | E3 | E5 |
|---|---|---|---|---|---|---|
| 8 | `escaneo_breve-r4` | 182.0 | 180 | cumple | indeterminado | cumple por caducidad_natural |
| 9 | `escaneo_sostenido-r5` | 902.0 | 900 | cumple | indeterminado | cumple por caducidad_natural |
| 11 | `escaneo_breve-r2` | 182.0 | 180 | cumple | indeterminado | cumple por caducidad_natural |
| 13 | `escaneo_sostenido-r2` | 902.0 | 900 | cumple | indeterminado | cumple por caducidad_natural |
| 18 | `escaneo_sostenido-r3` | 902.0 | 900 | cumple | indeterminado | cumple por caducidad_natural |
| 19 | `escaneo_sostenido-r1` | 902.0 | 900 | cumple | indeterminado | cumple por caducidad_natural |
| 23 | `escaneo_breve-r3` | 182.0 | 180 | cumple | indeterminado | cumple por caducidad_natural |
| 25 | `escaneo_sostenido-r4` | 902.0 | 900 | cumple | indeterminado | cumple por caducidad_natural |

Contraste (no formal): en la Campana A, sin restriccion, los mismos comandos terminaron en 4,6-5,0 s (breve) y 52,3-52,9 s (sostenido). Con BLOCK, breve tardo 138 s (2 completos) o mas de 182 s (3 cortados) y sostenido mas de 902 s (5 cortados). La causa interna en `nmap` no se observo.

## Motivos de indeterminacion de E3 (15 episodios)

| N | Episodio | Motivo |
|---|---|---|
| 1 | `inundacion_http-r4` | indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN 311.6/s, B0 intentos 155.9/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md |
| 6 | `inundacion_http-r3` | indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN 312.2/s, B0 intentos 156.0/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md |
| 8 | `escaneo_breve-r4` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 9 | `escaneo_sostenido-r5` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 11 | `escaneo_breve-r2` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 13 | `escaneo_sostenido-r2` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 15 | `escaneo_breve-r5` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 16 | `inundacion_http-r2` | indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN 312.2/s, B0 intentos 156.3/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md |
| 17 | `inundacion_http-r1` | indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN 307.2/s, B0 intentos 153.5/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md |
| 18 | `escaneo_sostenido-r3` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 19 | `escaneo_sostenido-r1` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 21 | `inundacion_http-r5` | indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN 313.8/s, B0 intentos 156.9/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md |
| 23 | `escaneo_breve-r3` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 24 | `escaneo_breve-r1` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |
| 25 | `escaneo_sostenido-r4` | indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria) |

## Motivos de `no aplica` (5, DNS)

`dns_inusual-r1`, `-r3` (B3) y `-r4`, `-r2`, `-r5` (B4): DC1 (10.10.10.20) no tiene punto de aplicacion; E2, E3 y E5 no aplican. E1 y E4 si se evaluan.

## Limitaciones abiertas

- **Discrepancia entre el SPAN y los contadores de srv-dmz (abierta).** El contador del elemento en `bloqueados` cuenta entre el 5 y el 20 % de los paquetes Kali->srv-dmz que el SPAN ve en los escaneos (cota superior, tras tener en cuenta los reinicios del contador por cada renovacion de la regla) y alrededor de la mitad en fuerza bruta. No esta explicada; el ensayo del contador queda **fuera del alcance** de este cierre. Detalle en `balances/BALANCE-B4.md` (seccion SPAN frente a contadores).
- La repeticion de los escaneos queda **fuera del alcance** de este cierre.
- E3 de los 10 escaneos sigue indeterminado por el criterio fijado; la evidencia complementaria esta en `reanalisis/`.
- E4 y E5 de B3 se calcularon con los datos de la corrida parcial; la puerta D5 de B3 devolvio `lista=false` tras el episodio 6 por un falso bloqueo ya diagnosticado y corregido antes de B4 (ver historial); no cambia ninguna celda.

