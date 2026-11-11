# BALANCE DE B4 (tramo 7-25, 19 episodios) - 11-nov-2026

ID `4c-B4-20261111T135745Z-b0ec7e96836a`. Lanzado 13:57:58Z (`g01d`, `CF_PLANIFICADOS=19`, `--aplicar` solo Kali 10.10.20.30). Episodio 7 (`fuerza_bruta_http-r1`) inicio real 14:01:55,47Z. Ultimo fin 17:09:07,7Z; generador rc 0 (17:10:37Z); `campana_fin: completa`; vigia sin pausas ni cancelacion. X1: 0 de 19 episodios en C2/C3 (los 19 en C0). srv-dmz de vuelta en sombra 17:14:55Z (`verificar_srvdmz` OK). Corrida separada de B3 (6 episodios); el reporte no las mezcla.

Evidencia: `corrida-2026-11-11-B4\` (pasos 25-35), analisis `scripts-operativos\analizar_b4.py` -> `<carpeta de evidencia B4>\resultado-b4.json`. Criterios sin cambios (E3 = CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md).

## Cierre tecnico (17:14-17:39Z)
Reversion R0-R5 17:14:55Z (traza con 375 aplicaciones archivada, 0 tablas, agente sin --aplicar, verificar_srvdmz OK contra PRE-B-20261111T135620Z), clientes restaurados + R6 OK, R7 OK, b20 (marcas identicas en Kali/bastion/Sensor1 sha 9e9c95ef...), s20 condiciones 1-4 CUMPLE, replay offline rc=0, s40 COPIAS COMPLETAS (7.325 PCAP, 0 FALLO/PERDIDO; servicios mismos PID y NRestarts). Evidencia apartada como 4c-B4-completa-19ep-20261111T1740Z en Sensor1 (3,9 GB), bastion y clientes; Kali ~/cf-e4-4c-B4-completa-... no se creo con ese nombre: la evidencia sigue en ~/cf-e4-4c/ (corrida, intentos, marcas) y su copia en cf-b4\kali. Muestreo de srv-dmz: ~/cf-b/set-lecturas-B4-20261111T1740Z.jsonl. Logrotate diario: sigue sin observarse (12-nov 00:00Z).

## Estado del generador
Completos 11, `incompleto_timeout` 8 (conservados): `escaneo_breve-r4`, `-r2`, `-r3` (180 s) y `escaneo_sostenido-r5`, `-r2`, `-r3`, `-r1`, `-r4` (900 s). Los 2 `escaneo_breve` restantes (`-r5`, `-r1`) completaron en 138 s.

## Resultado por indicador (19 episodios)
| | verificado/cumple | indeterminado | no aplica |
|---|---|---|---|
| E1 senal | 9 | 10 | 0 |
| E2 aplicacion | 16 | 0 | 3 (DNS) |
| E3 efecto | 3 (fuerza bruta) | 13 | 3 (DNS) |
| E4 legitimos | 19 | 0 | 0 |
| E5 retirada | 16 | 0 | 3 (DNS) |

Por familia: fuerza_bruta_http x3 todo cumple. dns_inusual x3: E1 verificado, E2/E3/E5 no aplica (DC1 sin punto de aplicacion). inundacion_http x3: E1/E2/E4/E5 cumplen; E3 indeterminado en los 3 (el generador sincrono no sostiene intentos; limitacion conocida, sin cambios). escaneo_breve x5 y escaneo_sostenido x5: E2/E4/E5 cumplen; E1 y E3 indeterminado en los 10 (ver «Que se puede verificar con los criterios vigentes»). E5: 8 por caducidad natural (los incompleto_timeout) y 2 por retirada explicita (escaneo_breve completos).

## Los 8 incompleto_timeout (corregido 11-nov tras leer las salidas de nmap y el SPAN)
**Correccion de una inferencia previa.** Antes se dijo que a ~10 SYN/s «1.000 puertos no caben en 180 s». Los SYN no indican puertos distintos (cada puerto puede llevar 1 o 2 SYN y nmap reenvia a puertos ya conocidos). Se contaron los puertos de destino distintos en el SPAN (Kali -> srv-dmz, SYN sin ACK):

| Episodio | Duracion | SYN | Puertos distintos | Veces por puerto |
|---|---|---|---|---|
| escaneo_breve-r1 (completo) | 138 s | 2.216 | **1.000** | 995 x2, 4 x3, 1 outlier |
| escaneo_breve-r5 (completo) | 138 s | 2.216 | **1.000** | idem |
| escaneo_breve-r4 (timeout) | 182 s | 2.263 | 990 | 977 x2 |
| escaneo_breve-r3 (timeout) | 182 s | 2.262 | 990 | 977 x2 |
| escaneo_breve-r2 (timeout) | 182 s | 1.974 | 847 | 840 x2 |
| escaneo_sostenido-r5 | 902 s | 10.855 | 9.476 (14,5 %) | 1 por puerto |
| escaneo_sostenido-r4 | 902 s | 9.962 | 8.582 (13,1 %) | 1 por puerto |
| escaneo_sostenido-r3 | 902 s | 9.931 | 8.553 | 1 por puerto |
| escaneo_sostenido-r1 | 902 s | 9.932 | 8.556 | 1 por puerto |
| escaneo_sostenido-r2 | 902 s | 9.814 | 8.436 (12,9 %) | 1 por puerto |

- En cada escaneo hay un puerto con muchos SYN (80 o 443: 214-274 en el breve, 1.378-1.379 en el sostenido, ~1,5/s): son reintentos de nmap contra puertos abiertos, no puertos nuevos. Es una lectura, no probada.
- **Breve:** los 2 completos probaron los 1.000 puertos dos veces; r3 y r4 se cortaron con 990/1.000 y r2 con 847/1.000 (el tope de 180 s llego antes). El ritmo inicial difiere (puertos distintos a los 10 s: 410 en r1/r5, 208 en r3/r4, 65 en r2); no se ha explicado.
- **Sostenido:** en 902 s sondeo 8.436-9.476 de 65.535 puertos (~9,4-10,5 puertos/s, muy por debajo de `--max-rate 1500`). Extrapolacion (no medida): ~6.200-7.000 s para terminar a ese ritmo.
- **Salidas de nmap:** los 8 `.out` solo tienen la cabecera (nmap fue terminado por el generador, rc -15, sin informe). No aportan progreso. Los 2 breves completos informan «998 filtered tcp ports (no-response)», 80 y 443 abiertos, 138,26-138,27 s.
- BLOCK aplicado a +1,1-2,0 s del inicio, presente hasta el corte, renovado ~cada 20 s; 0 respuestas del servidor tras t_apl salvo 1 en sostenido-r5 y -r4 (fuera de los 3 primeros bloques).
- **Causa de que nmap vaya lento: sin confirmar.** Es compatible con que nmap se frene al no recibir respuestas, pero ninguna evidencia lo distingue de otras causas (p. ej. tiempos de espera propios de nmap). No se dedujo mas de lo que muestran los datos.

## SPAN frente a contadores de srv-dmz (mismas ventanas, con reinicios)
Cada `anadir` del agente reinicia el contador del elemento (destroy+add, mismo o distinto id). Se recorrieron las lecturas del muestreador (cada ~2 s): el contador observado = suma de incrementos y, tras cada reinicio (id nuevo o contador que baja), el valor leido (cota inferior); cota superior = cota inferior + paquetes del SPAN en el hueco entre la ultima lectura anterior al reinicio y la primera posterior. SPAN = todos los paquetes Kali -> srv-dmz en la misma ventana. (Una primera version sumaba ventanas solapadas del mismo id y daba razones erroneas; queda sustituida por `cmp2.py`.)

| Grupo | Contador observado / SPAN | Cota superior / SPAN |
|---|---|---|
| escaneos (10) | 0,05-0,07 | 0,12-0,20 |
| fuerza_bruta (3) | 0,47-0,50 | 0,55-0,60 |

Incluso con la cota superior, el contador de srv-dmz cuenta una fraccion del trafico que el SPAN ve llegar de la Kali (en escaneos ~un 12-20 % como maximo; en fuerza bruta ~la mitad). **No esta explicado.** Lo que el criterio vigente exige del contador es su existencia con id de regla e IP tras t_apl (existe), no su magnitud.

## Que se puede verificar con los criterios vigentes
- **E1 (senal)**
  - Verificado: fuerza_bruta (3), dns (3), inundacion (3) = 9.
  - Escaneos (10): la senal `port_scan` llega a +5,6-12,2 s del inicio, dentro del episodio (el calculo de tiempo la daria por verificada), y el SPAN tiene paquetes de la Kali en la ventana de evidencia del episodio (107-798). Pero el analizador oficial no tiene lector de paquetes para escaneos (no hay «puerto del servicio»), asi que el resultado oficial es **indeterminado (herramienta)**. Pasarlos a verificado exige ampliar el analizador a «cualquier puerto del destino»: decision de Mark; no se hizo.
- **E3 (efecto)**
  - Fuerza bruta (3): **cumple** (K = 3 bloques, 0 respuestas, SYN por bloque, atribucion con `primer_descarte`).
  - Inundacion (3): indeterminado (el generador sincrono no sostiene los intentos; limitacion conocida).
  - DNS (3): no aplica.
  - **Escaneos (10): sigue indeterminado.** El criterio fijado pide SYN «al destino y puerto del episodio»; en un escaneo no hay un unico puerto, y el analizador devuelve I2 sin calcular la atribucion. Los datos disponibles apuntan a que se cumpliria la parte absoluta de BLOCK (Kali envia >=1 SYN en 898-900 de ~899-900 bloques de 1 s tras t_apl, y 0 respuestas en los 3 primeros bloques; el contador del host existe con id e IP), pero eso aplicaria una lectura del criterio («cualquier puerto») que no esta fijada. El criterio no se cambia durante ni despues de la corrida (CRITERIO-E3-FIJADO...); no se reclasifica.
- Los 8 incompleto_timeout se conservan tal cual.
## Tabla de cobertura por familia (dos tramos)
B3 (episodios 1-6) y B4 (7-25) se reportan por separado; esta tabla los muestra como dos tramos de la misma secuencia de 25: B4 aporta fuerza_bruta 3, dns 3, inundacion 3, escaneo_breve 5, escaneo_sostenido 5.

## Repeticion
No se decide aqui. Propuesta: solo los 8 escaneos incompleto_timeout (y los demas escaneos si se extiende el analizador), en corrida separada, previa aprobacion; requiere una opcion de seleccion de episodios en el generador. Con los mismos parametros es probable que se repita el corte.
