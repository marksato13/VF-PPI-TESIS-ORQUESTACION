# Tercera batería de la 4C: cancelada por X3 tras fallos del espejo (09-nov-2026)

**Estado:** cerrada y archivada; **no publicada**. Lanzada 15:04:32Z con `g01` v4 (`8f5a5529…`), esquema con `nmap -n` (`45f743d2…`), control 14:32:30–15:02:30Z, I1–I8 e I5 conformes. Cancelada **15:59:19Z** con 10 de 25 episodios iniciados (9 clasificados).

## Línea de tiempo
| Hora (Z) | Hecho |
|---|---|
| 15:04:32 | batería lanzada; vigía 2026-11-06.1 y generador vivos, permiso «continuar» |
| 15:26:54–15:31:29 | **el espejo deja de entregar paquetes de forma intermitente**: huecos de 9–16 s en el anillo del Sensor1 (15:26:54, 15:27:03, 15:27:48, 15:27:59, 15:28:35, 15:28:44, 15:29:04, 15:29:15, 15:29:28, 15:29:39, 15:31:29). El vigía pasa a **pausa P3** (15:27:19); el episodio 5 (`dns_inusual-r3`, 15:27:29–15:28:59) cae dentro y queda **C3** |
| 15:37:40 | tras 300 s sin hueco el permiso vuelve a «continuar»; la batería sigue sola |
| 15:57:3x–15:59:0x | episodio 10 (`fuerza_bruta_http-r5`) |
| 15:59:06 | **un único paquete** `10.10.20.30:22 → 10.10.10.30:41410` en EVE (`flow`, `new`, `timeout`, 1 paquete al servidor, 0 al cliente). Es la respuesta de sshd de la Kali a una conexión SSH abierta por el bastión: el sondeo de seguimiento (`ssh kali` desde el bastión) de las 15:59:06Z |
| 15:59:19 | X3: «tráfico de la Kali a 10.10.10.30:41410 (flow) durante un episodio». El generador se detiene solo (rc 3) |
| 16:02:19–16:02:59, 16:05:00–16:05:20 | dos cortes más del espejo, **ya sin campaña** y sin actividad mía que los explique |

## Diagnóstico
- X3 cuenta cualquier evento EVE con `src_ip` = Kali hacia un destino fuera de la lista blanca (`vigia_4c.py`, `eve_fuera_lista`), sin mirar el sentido real de la conexión. Con el espejo sano, las conexiones bastión→Kali figuran con `src_ip` = bastión y no cuentan; si el espejo pierde el comienzo de un intercambio, Suricata registra un flujo con origen en la Kali y X3 se dispara.
- Tasa de `ens37` cada 10 s (muestras de salud): corrida X1 (07:36–10:56Z) 0 tramos con <20 % de la mediana; corrida X3 #2 (10:59–13:47Z) 0 tramos; esta corrida (13:54–16:05Z) **6 tramos a ~0 pkt/s**: 15:26:58–15:27:18, 15:27:58–15:28:08, 15:28:39–15:29:49, 15:31:20–15:31:40, 16:02:19–16:02:59, 16:05:00–16:05:20. Mediana ≈ 500 pkt/s. A las 16:23Z la tasa vuelve a ser normal (606 y 503 pkt/s).
- Las pausas y la cancelación son el comportamiento previsto del protocolo (P3, X3). No se tocaron ni el vigía, ni la lista blanca, ni los criterios.
- El cambio `nmap -n` funcionó en vivo: `escaneo_breve-r4` y `escaneo_sostenido-r5` se ejecutaron, quedaron C0 y no generaron consultas DNS fuera de la lista blanca.
- Mi parte: el sondeo que abrí hacia la Kali desde el bastión puso ese tráfico en el segmento espejado. En un nuevo intento se sondea solo el bastión (el vigía ya habla con la Kali por su canal).

## Clases (vigia_fin)
Primera (X1): 6 × C3. Segunda (X3 #2): 7 × C0. Tercera: `inundacion_http-r4` C0, `fuerza_bruta_http-r4` C0, `dns_inusual-r1` C0, `fuerza_bruta_http-r3` C0, `dns_inusual-r3` **C3**, `inundacion_http-r3` C0, `fuerza_bruta_http-r1` C0, `escaneo_breve-r4` C0, `escaneo_sostenido-r5` C0.

## Cierre
`b20` v2 (dos veces, la segunda tras fin+300 s), `s20` CUMPLE (tras esperar al archivador), `s30` rc 0 (16:05→16:21Z), `s40` v3 «COPIAS COMPLETAS» (1938 pcaps, 0 fallos, servicios sin reinicios), clientes restaurados, y la corrida archivada **renombrando**: `4c-x3b-cancelada-20261109T1625Z` (Sensor1, bastión, clientes) y `cf-e4-4c-x3b-cancelada-20261109T1625Z` (Kali). Se analiza aparte; nada se mezcla con otra corrida.

## Pendiente de decisión de Mark
Reparar el espejo (switch/ESXi) y decidir si hay cuarta corrida; el disco del Sensor1 está al 91 % (3,2 GB libres) y las tres corridas archivadas ocupan ≈ 4,6 GB. Ver el informe en el chat.
