# Tabla 9 — Cobertura y tiempos de detección frente a Suricata (4.3)

Comparación **descriptiva** entre CyberFlow híbrido con α = 0,01 (`HIB_0.01`: Isolation Forest con umbral −0,6223889502095352 o heurísticos) y Suricata 7.0.3 con ET Open, sobre las mismas capturas de la cuarta corrida de la Campaña A (modo sombra). Población: **21 de 25 episodios elegibles** (5 DNS, 5 inundación HTTP, 5 fuerza bruta HTTP, 5 escaneo sostenido, 1 escaneo breve). Es una sola corrida con cinco repeticiones por familia y no tiene significancia estadística; los intervalos del total son de Clopper–Pearson al 95 %. La Campaña A también aportó a la elección de α = 0,01, por lo que `HIB_0.01` no es independiente de estos datos.

## Cómo se lee cada columna
- **CyberFlow, tiempo de datos.** Un episodio cuenta como detectado si la primera ventana de 10 s con señal de la configuración, atribuible al episodio, **cierra** a más tardar en `t_fin`. «Atribuible» (definición de `analizar_3b.py`): hay paquetes del origen hacia el destino del episodio dentro de la ventana y de [`t_inicio`, `t_fin`]. La marca es el cierre de la ventana (rejilla de 10 s, con historia retrospectiva de hasta 60 s), no el primer paquete.
- **CyberFlow, disponibilidad (`s50`).** Categoría oficial «oportuna»: el registro de la señal se **escribió** (`registro_escrito_en` del ciclo del motor) antes de `t_fin`. Incluye el retraso de procesamiento.
- **Suricata, regla fijada.** Una alerta cuenta si es `event_type = alert`, no empieza por `SURICATA STREAM ` ni `ET INFO `, su tiempo de paquete está en [`t_inicio`, `t_fin` + 60 s], el par es Kali – destino del episodio (cualquier sentido) y el puerto es el del servicio generado (cualquier TCP en escaneos). El episodio se detecta con ≥ 1 alerta **durante** el episodio (≤ `t_fin`).
- **Suricata, solo firmas ET Open.** Lectura complementaria que además descarta las alertas con prefijo `SURICATA` (eventos de motor/decodificación). **Estaba descrita antes del replay** como sensibilidad («excluyéndolas», `protocolo/PROTOCOLO-REPLAY-4.3.md`, línea 21; fijado a las 20:31:18Z según `protocolo/FIJADO.txt`). El resultado de la **regla fijada se conserva como principal**; el de firmas ET Open es complementario. Lo que resta en los episodios son firmas ET.

## Panel A — Cobertura por familia

| Familia | Elegibles | CyberFlow `HIB_0.01`, tiempo de datos | CyberFlow `HIB_0.01`, disponibilidad (`s50`) | Suricata, regla fijada | Suricata, solo firmas ET Open |
|---|---|---|---|---|---|
| dns_inusual | 5 | 5/5 | 5/5 | 0/5 | 0/5 |
| inundacion_http | 5 | 5/5 | 5/5 | 5/5 | 0/5 |
| fuerza_bruta_http | 5 | 5/5 | 5/5 | 5/5 | 0/5 |
| escaneo_sostenido | 5 | 5/5 | 5/5 | 5/5 | 5/5 |
| escaneo_breve | 1 | 1/1 | 0/1 | 0/1 | 0/1 |
| **Total** | 21 | 21/21 (IC95 84–100 %) | 20/21 (IC95 76–100 %) | 15/21 (IC95 48–89 %) | 5/21 (IC95 8–47 %) |

## Panel B — Tiempos desde el inicio del episodio (mediana [mín–máx], segundos)

| Familia | Episodios con alerta de ambos | CyberFlow: cierre de ventana (s) | CyberFlow: escritura de la señal (s) | Suricata: 1.ª alerta contada (s, tiempo del paquete) | Qué alerta contó |
|---|---|---|---|---|---|
| dns_inusual | 0 | 19,66 [13,95–20,93] | 23,72 [16,94–25,76] | — | ninguna |
| inundacion_http | 5 | 3,95 [0,85–5,95] | 9,76 [7,35–15,16] | 0,14 [0,08–0,82] | SID 2221010 (evento de decodificación) |
| fuerza_bruta_http | 5 | 3,95 [1,99–6,34] | 9,51 [8,25–12,27] | 1,15 [0,07–8,67] | SID 2221010 (evento de decodificación) |
| escaneo_sostenido | 5 | 3,31 [0,81–9,25] | 5,97 [5,11–13,14] | 0,24 [0,13–0,24] | SID 2010937 `ET SCAN … mySQL port 3306` (firma ET) |
| escaneo_breve | 0 | 3,94 [3,94–3,94] | 7,75 [7,75–7,75] | — | ninguna |
| **Comparables (ambos alertan)** | 15 | 3,95 [0,81–9,25] | 9,15 [5,11–15,16] | 0,24 [0,07–8,67] | — |

- Marcas: *Suricata* = `timestamp` del paquete que dispara la alerta (offline); *CyberFlow, cierre de ventana* = `window_end_utc` de la primera ventana atribuible con señal (marca de datos, cuantizada a 10 s); *CyberFlow, escritura* = `disponible_utc` (escritura del registro). Todas se miden contra el `t_inicio` del generador.
- Entran en el resumen «comparables» solo los **15** episodios con alerta de ambos sistemas (10 con el evento de decodificación SID 2221010; **5 con firmas ET Open**, los escaneos sostenidos). DNS (5) y escaneo breve (1) quedan **no comparables**: Suricata no emitió alerta válida.
- Resolución: la marca de CyberFlow cae en una rejilla de 10 s; las diferencias Suricata − CyberFlow (cierre de ventana) van de -9,02 a +4,72 s, todas menores de 10 s. **No permiten ordenar a los dos sistemas.** La columna de escritura no es comparable con el tiempo del paquete de Suricata.

### Detalle por episodio

| Episodio | Inicio (generador, UTC) | CyberFlow: cierre de ventana (s) | CyberFlow: escritura de la señal (s) | Suricata: 1.ª alerta (s) | SID / firma |
|---|---|---|---|---|---|
| `dns_inusual-r1` | 22:07:36.049274 | 13,95 | 16,94 | — | ninguna alerta válida |
| `dns_inusual-r2` | 23:25:49.412954 | 20,59 | 25,76 | — | ninguna alerta válida |
| `dns_inusual-r3` | 22:17:36.045972 | 13,95 | 19,69 | — | ninguna alerta válida |
| `dns_inusual-r4` | 22:58:30.335226 | 19,66 | 25,64 | — | ninguna alerta válida |
| `dns_inusual-r5` | 23:35:49.067385 | 20,93 | 23,72 | — | ninguna alerta válida |
| `inundacion_http-r1` | 23:12:04.052526 | 5,95 | 15,16 | 0,138 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `inundacion_http-r2` | 23:07:04.889782 | 5,11 | 12,78 | 0,367 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `inundacion_http-r3` | 22:22:36.129366 | 3,87 | 7,35 | 0,076 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `inundacion_http-r4` | 21:57:36.046386 | 3,95 | 9,76 | 0,823 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `inundacion_http-r5` | 23:30:49.154996 | 0,85 | 8,29 | 0,089 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `fuerza_bruta_http-r1` | 22:27:36.050084 | 3,95 | 8,25 | 8,674 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `fuerza_bruta_http-r2` | 22:49:08.014867 | 1,99 | 8,47 | 0,072 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `fuerza_bruta_http-r3` | 22:12:36.382544 | 3,62 | 9,51 | 1,459 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `fuerza_bruta_http-r4` | 22:02:36.048134 | 3,95 | 11,35 | 1,145 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `fuerza_bruta_http-r5` | 22:40:33.662280 | 6,34 | 12,27 | 0,247 | 2221010 `SURICATA HTTP unable to match response to requ` |
| `escaneo_sostenido-r1` | 23:21:26.689998 | 3,31 | 5,97 | 0,244 | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` |
| `escaneo_sostenido-r2` | 22:54:08.021028 | 1,98 | 5,11 | 0,129 | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` |
| `escaneo_sostenido-r3` | 23:17:04.031659 | 5,97 | 9,15 | 0,238 | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` |
| `escaneo_sostenido-r4` | 23:47:59.185153 | 0,81 | 5,13 | 0,241 | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` |
| `escaneo_sostenido-r5` | 22:36:10.746070 | 9,25 | 13,14 | 0,228 | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` |
| `escaneo_breve-r4` | 22:32:36.059352 | 3,94 | 7,75 | — | ninguna alerta válida |

### Escaneos sostenidos: primer SID válido y marcas observadas

| Episodio | Inicio (UTC) | Suricata, 1.ª alerta válida (tiempo del paquete) | SID / firma | Cierre de la 1.ª ventana de `HIB_0.01` | Escritura de la señal | Señales en esa 1.ª ventana |
|---|---|---|---|---|---|---|
| `escaneo_sostenido-r1` | 23:21:26.689998 | 23:21:26.933896 (+0,244 s) | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` | 23:21:30 (+3,31 s) | 23:21:32.662755 (+5,97 s) | heurístico `port_scan`, híbrido `HIB_0.01` |
| `escaneo_sostenido-r2` | 22:54:08.021028 | 22:54:08.150118 (+0,129 s) | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` | 22:54:10 (+1,98 s) | 22:54:13.133416 (+5,11 s) | heurístico `port_scan`, híbrido `HIB_0.01` |
| `escaneo_sostenido-r3` | 23:17:04.031659 | 23:17:04.269609 (+0,238 s) | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` | 23:17:10 (+5,97 s) | 23:17:13.180068 (+9,15 s) | IF α=0,01, heurístico `port_scan`, híbrido `HIB_0.01` |
| `escaneo_sostenido-r4` | 23:47:59.185153 | 23:47:59.426346 (+0,241 s) | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` | 23:48:00 (+0,81 s) | 23:48:04.318542 (+5,13 s) | heurístico `port_scan`, híbrido `HIB_0.01` |
| `escaneo_sostenido-r5` | 22:36:10.746070 | 22:36:10.973816 (+0,228 s) | 2010937 `ET SCAN Suspicious inbound to mySQL port 3306` | 22:36:20 (+9,25 s) | 22:36:23.887919 (+13,14 s) | IF α=0,01, heurístico `port_scan`, híbrido `HIB_0.01` |

En los cinco, la primera alerta válida es el SID 2010937 (puerto 3306), entre 0,13 y 0,24 s después de la marca de inicio del generador, con el mismo resultado con el HOME_NET original. Son tres marcas distintas: el **paquete** que dispara una firma por puerto (depende de cuándo `nmap` probó el 3306, no del reconocimiento del barrido), el **cierre de una ventana** de 10 s de CyberFlow y la **escritura** de su señal. Solo las dos primeras son tiempos de datos. Respaldo: `resultados/resultados-por-episodio.csv` (columnas `suri_P_primera_*`, `cf_HIB01_cierre_ventana_*`, `cf_HIB01_escritura_senal_*`).

## Notas
1. **`escaneo_breve-r4` (7,75 s).** Inicio 22:32:36,059; fin 22:32:40,743 (4,68 s). La primera ventana con señal de `HIB_0.01` cierra a las 22:32:40,000 (+3,94 s; 0,74 s antes del fin) por el heurístico `port_scan`; el IF con α = 0,01 no alertó (puntuación −0,6019). La señal se escribió a las 22:32:43,805 (**+7,75 s** del inicio y +3,06 s del fin; retraso 3,8 s), por lo que la categoría oficial es «solo_posterior». El 7,7 de `s50` es ese valor con una decimal. Campos: `analisis-3b.json` → `episodios.escaneo_breve-r4.ventanas[0].{window_end_utc, disponible_utc, retraso_s}` y `…HIB_0.01.primera.disponible_desde_inicio_s` (7,7); marcas de inicio/fin en `marcas.jsonl` (`evento: inicio|fin`).
2. **21/21 frente a 20/21 en CyberFlow.** Difieren solo en `escaneo_breve-r4`: detectado por tiempo de datos, tardío por disponibilidad. `HIB_0.03` (sensibilidad) da los mismos 21/21 y 20/21 y los mismos tiempos.
3. **DNS.** El heurístico `dns_entropy` señaló los 5 episodios; el IF con α = 0,01 solo 1 (`dns_inusual-r4`). Suricata: ninguna alerta sobre el par Kali–DC1 con ninguno de los dos `HOME_NET`; sí leyó las consultas DNS (840 y 836 eventos `dns` Kali→DC1 en `dns_inusual-r1` y `-r4`, mismos conteos con ambas configuraciones; comprobado solo en esas dos rebanadas).
4. **SID 2221010** (`SURICATA HTTP unable to match response to request`, categoría `Generic Protocol Command Decode`) es un **evento de decodificación**, no una firma de amenaza. Con la regla fijada (intervalo [`t_inicio`, `t_fin` + 60 s], par Kali–10.10.30.10, TCP/80 en inundación y TCP/18081 en fuerza bruta): **inundación 4.149** (3.171 durante el episodio y 978 posteriores) y **fuerza bruta 877** (655 y 222); con el `HOME_NET` original, 4.181 y 875. Aparece también en el control legítimo (13 eventos, 11 contados en unidades marcadas). Hipótesis, no verificada: que su aparición esté relacionada con la duplicación del espejo (en `inundacion_http-r1` las alertas se reparten entre las VLAN 20 y 30). No debe citarse ningún conteo sin ese filtro de intervalo.
5. **Sensibilidades.** `HIB_0.03`: misma cobertura y tiempos; en el control marca 200 unidades (9,02 %) y 140 ventanas. `HOME_NET` original de Suricata: mismos 15/21 y 5/21 y mismos 79 pares en el control; cambia solo el número de alertas `ET INFO` (excluidas) y el conteo de SID 2221010 (menos de 1 %).
6. **Control legítimo.** Se usa «proporción de unidades marcadas», no tasa de falsos positivos: no hay etiquetas por unidad. Tabla en `README.md` y `resultados/resultados-control.json`.
7. **Nikto** es un antecedente separado (6-oct-2026, N = 1) y **no entra en esta tabla ni en sus totales**; ver `README.md`.

## Control legítimo de 30 minutos (21:23–21:53 Z)

| Detector | Unidades entidad–ventana marcadas (de 2.218) | Ventanas de 10 s con al menos una unidad marcada (de 181) |
|---|---|---|
| CyberFlow `HIB_0.01` (principal) | 54 (2,43 %) | 54 (29,8 %) |
| CyberFlow `IF_0.01` | 54 (2,43 %) | 54 (29,8 %) |
| CyberFlow `HEUR` | 0 (0,00 %) | 0 (0,0 %) |
| CyberFlow `HIB_0.03` (sensibilidad) | 200 (9,02 %) | 140 (77,3 %) |
| Suricata, HOME_NET principal | 79 (3,56 %) | 67 (37,0 %) |
| Suricata, HOME_NET original (sensibilidad) | 79 (3,56 %) | 67 (37,0 %) |

Los 79 pares marcados por Suricata pertenecen **todos** al conjunto de 2.218 pares entidad–ventana de CyberFlow (0 fuera), con ambos `HOME_NET`. Cada alerta se asignó al iniciador de su flujo y a la ventana de 10 s que la contiene, y se deduplicó por par (184 alertas válidas → 79 pares). Quedaron fuera de conteo 129 alertas atribuidas al bastión 10.10.10.30 (no está en la población de CyberFlow) y 12 con ventana fuera del intervalo; además se excluyeron 1.177 `ET INFO` y 310 `SURICATA STREAM`. Predominaron `GPL ICMP PING *NIX` (172 de 184), seguido de SID 2221010 (11) y `SURICATA Applayer Wrong direction first Data` (1). Solapamiento entre sistemas: 5 pares comunes.
