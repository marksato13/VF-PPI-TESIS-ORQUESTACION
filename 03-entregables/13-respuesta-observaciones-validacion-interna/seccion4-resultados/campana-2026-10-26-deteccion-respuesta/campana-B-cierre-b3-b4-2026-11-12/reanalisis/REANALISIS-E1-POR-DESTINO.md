# Reanalisis de E1 por destino (12-nov-2026) bajo el criterio vigente

**Los balances originales (`../balances/`) no se modifican.** Este documento anade un reanalisis offline de E1 sobre las copias definitivas de la evidencia. No cambia E2-E5, no reclasifica E3 y conserva los ocho `incompleto_timeout`.

## Criterio tal como esta escrito
`OBJETIVOS-Y-CRITERIOS.md fila E1 (linea 93) @ blob 888f66482572`: «senal atribuible (paquetes **del origen al destino del episodio** dentro de la ventana y de [inicio, fin]) de la regla prevista, con t_det + eps < t_fin_eval». Habla de destino, no de puerto.

## Que cambia respecto del lector original
El lector original (`analizar_b3.py`/`analizar_b4.py`) ademas filtraba por puerto (80, 18081, 53). Para los escaneos no habia puerto y devolvia `indeterminado: sin lector de paquetes para este servicio` (indeterminado de herramienta, no de datos). `e1_por_destino.py` cuenta todos los paquetes origen->destino (Kali -> 10.10.30.10; Kali -> 10.10.10.20 en DNS). Diferencia deliberada: sin paquetes en la ventana devuelve `indeterminado`; el lector historico devolvia el resultado de la senal.

## Implementacion y pruebas
- `analisis/e1_por_destino.py` (sha256 28ec88c088a41c58...), `analisis/test_e1_por_destino.py` (9 pruebas: 8 de comportamiento y una que exige eliminar 5 mutantes; todas pasan), `analisis/aplicar_e1_destino_25.py` -> `resultados/resultado-e1-por-destino-25.json`.
- Extraccion del SPAN: `analisis/span_extract2.py` (PCAP B3: 514 ficheros; B4: 2.343; manifiestos con hash en `manifiestos/`).
- Ejecucion registrada en `pruebas/PRUEBAS-EJECUTADAS.md`.

## Regresion sobre los 15 episodios con puerto
El veredicto original coincide con el de por destino en los 15. Los conteos del lector historico difieren algo de los nuevos: la ventana de evidencia se guardo redondeada a 0,1 s (diferencias de hasta ~0,9 %, consistente con ese redondeo) y, en DNS, el lector historico contaba ambos sentidos Kali<->DC1 (aproximadamente el doble). No se modifica ningun resultado formal.

| Episodio | Tramo | Conteo del lector historico | Conteo por puerto (nuevo lector) | Conteo por destino | Veredicto original = por destino |
|---|---|---|---|---|---|
| `inundacion_http-r4` | B3 | 24378 | 24490 | 24490 | si |
| `fuerza_bruta_http-r4` | B3 | 4536 | 4536 | 4536 | si |
| `dns_inusual-r1` | B3 | 196 | 98 | 98 | si |
| `fuerza_bruta_http-r3` | B3 | 1438 | 1428 | 1428 | si |
| `dns_inusual-r3` | B3 | 200 | 100 | 100 | si |
| `inundacion_http-r3` | B3 | 25942 | 25848 | 25848 | si |
| `fuerza_bruta_http-r1` | B4 | 3280 | 3256 | 3256 | si |
| `fuerza_bruta_http-r5` | B4 | 3248 | 3248 | 3248 | si |
| `fuerza_bruta_http-r2` | B4 | 2014 | 2010 | 2010 | si |
| `dns_inusual-r4` | B4 | 140 | 70 | 70 | si |
| `inundacion_http-r2` | B4 | 13720 | 13642 | 13642 | si |
| `inundacion_http-r1` | B4 | 12660 | 12604 | 12604 | si |
| `dns_inusual-r2` | B4 | 148 | 74 | 74 | si |
| `inundacion_http-r5` | B4 | 12856 | 12852 | 12852 | si |
| `dns_inusual-r5` | B4 | 140 | 68 | 68 | si |

## Resultado en los 10 escaneos
E1 = verificado en los 10: senal `port_scan` (prevista) dentro del episodio, paquetes de la Kali al destino en la ventana, 0 paquetes previos al inicio y ventana sin tocar el episodio anterior.

| Episodio | Senal (s tras inicio) | Paquetes Kali->destino en ventana y episodio | Previos al inicio | Toca episodio anterior | Resultado original | Por destino |
|---|---|---|---|---|---|---|
| `escaneo_breve-r4` | 11.96 (port_scan; tambien port_scan_temprano) | 433 | 0 | False | indeterminado | verificado |
| `escaneo_sostenido-r5` | 5.63 (port_scan; tambien port_scan_temprano) | 173 | 0 | False | indeterminado | verificado |
| `escaneo_breve-r2` | 12.2 (port_scan; tambien port_scan_temprano) | 107 | 0 | False | indeterminado | verificado |
| `escaneo_sostenido-r2` | 11.28 (port_scan; tambien port_scan_temprano) | 242 | 0 | False | indeterminado | verificado |
| `escaneo_breve-r5` | 7.44 (port_scan; tambien port_scan_temprano) | 798 | 0 | False | indeterminado | verificado |
| `escaneo_sostenido-r3` | 9.21 (port_scan; tambien port_scan_temprano) | 340 | 0 | False | indeterminado | verificado |
| `escaneo_sostenido-r1` | 5.85 (port_scan; tambien port_scan_temprano) | 322 | 0 | False | indeterminado | verificado |
| `escaneo_breve-r3` | 10.06 (port_scan; tambien port_scan_temprano) | 392 | 0 | False | indeterminado | verificado |
| `escaneo_breve-r1` | 7.56 (port_scan; tambien port_scan_temprano) | 675 | 0 | False | indeterminado | verificado |
| `escaneo_sostenido-r4` | 10.83 (port_scan; tambien port_scan_temprano) | 348 | 0 | False | indeterminado | verificado |

## Resultado global
E1 sobre los 25: formal original 15 verificado / 10 indeterminado; reanalisis por destino 25 verificado / 0 indeterminado.

---

# Anexo: texto anadido al BALANCE-B4 el 12-nov (sin cambios)

## Trazabilidad E1: lectura por destino (12-nov, offline sobre las copias definitivas)
**Este balance no se reescribe: las tablas de arriba son el resultado original.** Lo siguiente es adicional.

**Criterio tal como esta escrito** (`OBJETIVOS-Y-CRITERIOS.md`, fila E1): «senal atribuible (paquetes **del origen al destino del episodio** dentro de la ventana y de [inicio, fin]) de la regla prevista, con t_det + eps < t_fin_eval». Habla de destino, no de puerto. El lector historico (`analizar_b3.py`/`analizar_b4.py`) ademas filtraba por puerto (80, 18081, 53) y para escaneos no tenia puerto, por lo que devolvia «indeterminado: sin lector de paquetes» (indeterminado de herramienta, no de datos). Ampliar el lector a «todos los paquetes Kali -> 10.10.30.10» **aplica el criterio tal como esta escrito**, no lo reinterpreta.

**Implementacion** (no modifica analizar_b.py ni los analizadores originales): `e1_por_destino.py` + `test_e1_por_destino.py` (9 pruebas: 8 de comportamiento y una que exige eliminar 5 mutantes; todas pasan) + `aplicar_e1_destino.py` -> `resultado-b4-e1-por-destino.json`. Diferencia deliberada: sin paquetes dentro de la ventana devuelve indeterminado (el historico devolvia el resultado de la senal).
**Regresion:** en los 6 episodios con puerto (fuerza bruta e inundacion) el conteo por destino coincide con el conteo por puerto del mismo lector (3.256, 3.248, 2.010, 13.642, 12.604, 12.852): el veredicto no cambia.

**Resultado en los 10 escaneos:** senal `port_scan` verificada (+5,6 a +12,2 s; tambien `port_scan_temprano`, regla prevista segun el protocolo para el breve), paquetes Kali->destino en [ventana de evidencia ∩ episodio] entre 107 y 798, **0 paquetes de la Kali en la parte de la ventana anterior al inicio**, ventana sin tocar el episodio anterior. **E1 = verificado en los 10.** Tabla sobre los 25: E1 original 15 verificados / 10 indeterminados; con la lectura por destino, 25 / 0.

## Evidencia COMPLEMENTARIA de E3 en escaneos (no formal; E3 sigue indeterminado)
El criterio E3 fijado para BLOCK dice en su tabla de decision «>= 1 intento (SYN) por bloque» pero en su aclaracion de rama y en `e3_v2` «SYN del origen **al destino y puerto**», y un escaneo no tiene un unico puerto. Aplicar «cualquier puerto» seria reinterpretar un criterio fijado antes de la corrida («no se cambia durante ni despues»). Por eso **los 10 E3 de escaneo se mantienen indeterminados**. Evidencia que si existe: tras t_apl, la Kali envia >= 1 SYN en 898-900 de ~899-900 bloques de 1 s (breve: 178-179/179, 135/135), 0 respuestas del servidor en los 3 primeros bloques (1 SYN-ACK aislado mas tarde en sostenido-r5 y -r4), BLOCK en el set sin lecturas fallidas, y el contador de la regla existe con id e IP. Los datos son compatibles con el efecto, pero se presentan como complemento.

## Duracion de los escaneos: contraste con la Campana A (sin restriccion)
Mismos comandos y destino, Campana A (`4c-A-completa`, sin `--aplicar`): escaneo_breve 4,6-5,0 s, escaneo_sostenido 52,3-52,9 s, los 10 completos. Con BLOCK (B4): breve 138 s (2 completos) o > 182 s (3 cortados), sostenido > 902 s (5 cortados). La ralentizacion coincide con el BLOCK y es de 1-2 ordenes de magnitud. No se observo el mecanismo interno de nmap (reintentos/espera por falta de respuesta); es la explicacion mas probable, no una causa demostrada.

## Preguntas abiertas y repeticion (decision tuya)
1. **E3 formal de los 10 escaneos.** Pregunta de criterio, no de ensayo: ¿«puerto del episodio» incluye «cualquier puerto del destino» en un escaneo? Repetir los escaneos no la resuelve; solo una decision escrita (con la salvedad de que seria posterior a la corrida; por eso aqui va como complemento).
2. **¿Por que el contador del elemento en srv-dmz cuenta solo el 5-20 % de los paquetes que el SPAN ve (escaneos) y ~50 % (fuerza bruta), incluso con la cota superior por reinicios?** Es la unica discrepancia medida sin explicacion y afecta a la atribucion de E3 y a cualquier lectura del contador. **Ensayo propuesto (pequeño, separado, no repite ningun episodio):** agente en sombra, un BLOCK unico por helper (como el ensayo por inyeccion), sin renovaciones; la Kali envia un numero conocido de SYN (p. ej. `nmap -sT -n --max-retries 0 -p 1-200`); comparar SPAN, captura en srv-dmz y contador. Si SPAN = captura > contador, el contador no cuenta todo lo que la regla descarta (limite del instrumento); si SPAN > captura = contador, el espejo incluye trafico que no llega (limite del SPAN). Dura minutos.
3. **¿Repetir los 8 escaneos `incompleto_timeout`?** Con los mismos parametros es esperable el mismo resultado (la Campana A y B4 muestran que BLOCK alarga el escaneo mas alla del tope) y no responderia ninguna pregunta nueva: E1 ya queda verificado y E3 depende de la pregunta 1. Solo tendria sentido con otro parametro (tope mayor), que seria una corrida distinta con otra pregunta («¿cuanto tarda un escaneo bajo BLOCK en terminar?»). **Recomendacion: no repetir los 8; si se quiere cerrar algo, el ensayo de la pregunta 2.**