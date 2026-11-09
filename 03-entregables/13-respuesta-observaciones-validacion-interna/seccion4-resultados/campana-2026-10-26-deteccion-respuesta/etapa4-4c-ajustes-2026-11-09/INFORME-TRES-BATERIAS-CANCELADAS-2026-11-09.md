# Informe de las tres baterías canceladas de la Campaña A (4C), 09-nov-2026

**Naturaleza de estos datos.** Son corridas **canceladas por el protocolo**, en modo sombra. **No constituyen resultados de la Campaña A completa** (25 episodios): ninguna llegó a la mitad, no tienen `s50` ni análisis de episodios, y no deben sumarse entre sí ni a una corrida completa. Este informe describe lo ocurrido y la evidencia archivada; no calcula métricas de detección. Las clases C0–C3 son las de **salud de captura** del periodo de cada episodio (SALUD-CAPTURA), no una evaluación del detector.

Resumen:

| | Corrida 1 | Corrida 2 | Corrida 3 |
|---|---|---|---|
| Carpeta (Sensor1/bastión/clientes) | `4c-cancelada-20261109T1058Z` | `4c-x3-cancelada-20261109T1350Z` | `4c-x3b-cancelada-20261109T1625Z` |
| Carpeta en Kali | `cf-e4-4c-cancelada-20261109T1058Z` | `cf-e4-4c-x3-cancelada-20261109T1350Z` | `cf-e4-4c-x3b-cancelada-20261109T1625Z` |
| Control declarado (UTC) | 08:15:00–08:45:00 | 11:39:00–12:09:00 | 14:32:30–15:02:30 |
| Vigía | 2026-11-02.1 (del paquete del 4-nov) | 2026-11-06.1 | 2026-11-06.1 |
| Lanzada / cancelada (UTC) | 09:34:50 / 10:06:48 (marca 10:07:50) | 12:11:39 / 12:50:26 (marca 12:51:24) | 15:04:32 / 15:59:19 (marca 16:00:31) |
| Episodios completados | **6 de 25** | **8 de 25** | **10 de 25** |
| Clasificados | 6 (todos C3) | 7 (todos C0) | 9 (8 C0, 1 C3) |
| Causa | X1 | X3 | X3 (tras pausa P3) |

## Corrida 1 — cancelada por X1
- **Episodios** (todos `completo`, 90 s cada uno): inundacion_http-r4 (09:37:50), fuerza_bruta_http-r4 (09:42:50), dns_inusual-r1 (09:47:50), fuerza_bruta_http-r3 (09:52:50), dns_inusual-r3 (09:57:50), inundacion_http-r3 (10:02:50). Siguiente no lanzado: fuerza_bruta_http-r1.
- **Clasificación:** los 6 salieron **C3** («Suricata sin medida completa en el periodo»). Esa clasificación **no es fiable**: el vigía 2026-11-02.1 medía Suricata por `stats.log`, y Suricata 7 no escribe `kernel_drops` cuando vale 0. Con el vigía 2026-11-06.1 (medida por EVE) los mismos 6 intervalos dan C0 (0 descartes; 405 986, 193 938, 39 591, 224 767, 64 042 y 405 212 paquetes), ver `evidencia/vigia-final-repeticion/`.
- **Cancelación:** X1 «6 episodios en C2/C3 > 20 % de 25» a las 10:06:48Z, antes de lanzar fuerza_bruta_http-r1. Sin pausas.
- **Evidencia:** `corrida/marcas.jsonl` (sha `bb5cfb28…`), `vigia/vigia.jsonl` (35 rondas), `vigilancia.log`, `control-declarado.json`; `s20` CUMPLE, replay `s30` rc 0 (10:59:33 de la segunda corrida no aplica; el de esta fue 07:36:43–10:09:20Z), `s40` v3 con 2586 pcaps archivados y 0 fallos; `evidencia/cancelacion-x1/` y `evidencia/c5/` en esta carpeta. Los 6 episodios se pueden reanalizar aparte con la `s50` de la 4C (paso 3 por EVE).

## Corrida 2 — cancelada por X3 (nmap sin `-n`)
- **Episodios completados (8):** inundacion_http-r4 (12:14:36), fuerza_bruta_http-r4 (12:19:36), dns_inusual-r1 (12:24:36), fuerza_bruta_http-r3 (12:29:36), dns_inusual-r3 (12:34:36), inundacion_http-r3 (12:39:36), fuerza_bruta_http-r1 (12:44:36), escaneo_breve-r4 (12:49:36–12:49:54).
- **Clasificación:** los 7 primeros **C0**; escaneo_breve-r4 quedó **sin clasificar** (la cancelación llegó antes de su clasificación).
- **Cancelación:** X3 a las 12:50:26Z: tráfico de la Kali a 10.10.10.21:53 (dns) durante un episodio. `nmap` sin `-n` consultó el DNS inverso a los dos servidores del `resolv.conf` de la Kali; 10.10.10.21 no está en la lista blanca (EVE: 8 flujos UDP/53 a cada servidor, primero 12:49:36Z y 12:49:42Z). Sin pausas. Siguiente no lanzado: escaneo_sostenido-r5.
- **Evidencia:** `marcas.jsonl` (sha `cb6e43b9…`), `vigia.jsonl` (41 rondas), `s20` CUMPLE, `s30` rc 0 (10:59:33–12:54:54Z), `s40` v3 con 2238 pcaps y 0 fallos; `CAMBIO-NMAP-N-2026-11-09.md` y `evidencia/x3-y-nmap-n/` (incluida la prueba en laboratorio con `nmap -sL`, con y sin `-n`).

## Corrida 3 — cancelada por X3 (paquete suelto de sshd) tras pausa P3 por el espejo
- **Episodios completados (10):** inundacion_http-r4 (15:07:29), fuerza_bruta_http-r4 (15:12:29), dns_inusual-r1 (15:17:29), fuerza_bruta_http-r3 (15:22:29), dns_inusual-r3 (15:27:29), inundacion_http-r3 (15:39:34), fuerza_bruta_http-r1 (15:44:34), escaneo_breve-r4 (15:49:34–15:49:39), escaneo_sostenido-r5 (15:53:09–15:54:01), fuerza_bruta_http-r5 (15:57:31–15:59:01).
- **Clasificación:** 8 C0, **dns_inusual-r3 C3** (cayó en un corte del espejo), y fuerza_bruta_http-r5 **sin clasificar**. escaneo_breve-r4 y escaneo_sostenido-r5, ya con `nmap -n`, salieron C0 y sin consultas DNS fuera de la lista blanca. Observación: escaneo_breve duró 5 s frente a 18 s en la corrida 2 (coherente con quitar la espera de la resolución inversa; no se ha verificado por separado).
- **Pausa:** P3 «salto del anillo 15–16 s > 7 s» desde 15:27:19Z hasta la reanudación a las 15:37:34Z (425 s), con 10 rondas en pausa; el episodio inundacion_http-r3 se aplazó de su hora prevista.
- **Cancelación:** X3 a las 15:59:19Z: un único paquete `10.10.20.30:22 → 10.10.10.30:41410` (flujo `new`, `timeout`, 1 paquete al servidor, 0 al cliente), respuesta de sshd de la Kali a una conexión abierta por un sondeo mío desde el bastión; con el espejo fallando, Suricata perdió el comienzo del intercambio y lo registró con origen en la Kali. Siguiente no lanzado: escaneo_breve-r2.
- **Espejo:** `ens37` cayó a ~0 pkt/s en 6 tramos (15:26:58–15:27:18, 15:27:58–15:28:08, 15:28:39–15:29:49, 15:31:20–15:31:40, 16:02:19–16:02:59, 16:05:00–16:05:20); la NIC no perdió enlace. Más tarde (16:35–17:48Z) hubo más cortes en las mediciones A–C, y la medición D (18:04:49–18:40:02Z) no tuvo ninguno.
- **Evidencia:** `marcas.jsonl` (sha `df530599…`), `vigia.jsonl` (57 rondas), `s20` CUMPLE (tras esperar al archivador), `s30` rc 0 (13:54:57–16:04:01Z), `s40` v3 con 1938 pcaps y 0 fallos; `INCIDENTE-TERCERA-BATERIA-X3-ESPEJO-2026-11-09.md`, `evidencia/tercera-bateria-x3-espejo/`, `evidencia/preparacion-cuarta-corrida/`; logs del espejo `espejo-1s-*.log` (A–D) en `/home/m4rk/` del Sensor1.

## Qué NO se ha hecho con estos datos
No se ejecutó `s50` ni se calcularon métricas de detección o respuesta. Cualquier análisis futuro debe tratar cada corrida por separado, con su propio control y su causa de cancelación, y no mezclarla con una Campaña A completa.

## Conservación
Originales en el Sensor1; copias verificadas (inventario y SHA-256 idénticos) de las corridas 2 y 3 en `/home/gadmin/cf-e4/archivo-sensor1/`. La corrida 1 **no tiene copia** en el bastión. Nada se ha borrado. Sin publicar.
