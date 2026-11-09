# Preparación de la cuarta corrida (09-nov-2026, 16:30–16:50Z): espacio y espejo

**Estado:** preparada, **NO iniciada**. Espera la orden de Mark. Nada se ha borrado. Sin publicar.

## 1. Copia de las dos corridas archivadas más pequeñas al bastión
| Corrida (Sensor1 `~/cf-e4/…`) | Copia en el bastión | Bytes en ficheros | Ocupa en disco | Ficheros / dirs / enlaces |
|---|---|---|---|---|
| `4c-x3-cancelada-20261109T1350Z` | `/home/gadmin/cf-e4/archivo-sensor1/4c-x3-cancelada-20261109T1350Z` | 1 533 068 754 | 1 538 035 712 B (Sensor1) | 2312 / 12 / 0 |
| `4c-x3b-cancelada-20261109T1625Z` | `/home/gadmin/cf-e4/archivo-sensor1/4c-x3b-cancelada-20261109T1625Z` | 1 539 943 267 | 1 544 364 032 B (Sensor1) | 2012 / 12 / 0 |

Verificación: **inventario completo idéntico** (tipo, modo, tamaño de ficheros, mtime en s, ruta; 2324 y 2024 entradas) y **SHA-256 idéntico de todos los ficheros** (2312 y 2012). Huellas del listado: `84c6163c8d125d3e…` y `29239c6f6b176ee3…` (sensor = bastión). Listados completos en el bastión: `…/archivo-sensor1/<corrida>.{inventario2,sha256}-{sensor1,bastion}.*`. Primera comparación con diferencias solo de artefacto (tamaño de entrada de directorio y subsegundo del raíz), corregida en `inventario2`.

**Espacio recuperable en el Sensor1 si se borran del Sensor1 esas dos carpetas: 3 082 399 744 B (≈ 3,08 GB / 2,87 GiB).** Libre ahora 3 402 702 848 B (91 % usado) → ≈ 6 485 102 592 B tras el borrado. Consumo previsto de una corrida nueva: ≈ 2,6–2,9 GB (las tres anteriores ocuparon 1,53–1,66 GB cada una en 2–3 h; ésta duraría ≈ 4 h). **Sin liberar espacio el margen sería ≈ 0,5 GB: no es seguro.** El borrado NO está autorizado.

## 2. Espejo: sigue inestable
- Muestreo de `ens37` cada 1 s en el Sensor1 (16:32:47Z → 16:47:50Z, `~/espejo-1s-20261109.log`): mediana 195 pkt/s, **9 tramos de 20–27 s con 0 pkt/s** (16:35:30, 16:36:07, 16:37:41, 16:38:23, 16:41:41, 16:42:08, 16:45:07, 16:45:56). Antes de las 15:26Z no hubo ni uno en 6 h.
- La NIC del Sensor1 **no pierde enlace** (`carrier_changes=1`, `down=0`, sin eventos en el journal) y el tráfico previo a cada corte es bajo (100–3000 pkt/s): no es saturación del destino de 100 Mb/s. Los clientes no registran fallos (1 acción fallida en miles): la red de laboratorio funciona; falla la entrega del espejo.
- Cortes anteriores (tasa de `ens37` en las muestras de salud): 15:26:58–15:27:18, 15:27:58–15:28:08, 15:28:39–15:29:49, 15:31:20–15:31:40, 16:02:19–16:02:59, 16:05:00–16:05:20.
- Documentado: sesión SPAN 1 en **CORE-STACK** (SSH 10.10.99.10): fuentes `Gi1/0/23` (pfSense-A, troncal) y `Gi2/0/23` (pfSense-B) desde el 22-sep (`BANCO-DE-PRUEBAS.md`), destino **`Gi2/0/19`** (`CYBERFLOW-SPAN-DST`, 100 Mb/s, VLAN 999). Sensor1: NIC `ens37`, vmxnet3, MAC `00:0c:29:3d:f9:4e`, promiscua. No hay en los documentos el host ESXi ni el nombre de la VM; se localiza por esa MAC.

## 3. Vigilancia sin conexiones de sondeo
`evidencia/preparacion-cuarta-corrida/estado_bateria_b.sh`: solo lectura local en el bastión (`vigia/vigia.jsonl`, `corrida/marcas.jsonl`, `pgrep`); no abre ninguna conexión a Kali, Sensor1 ni srv-dmz. Probado sobre la corrida archivada. X3 y la lista blanca no se tocan.

## 4. Condiciones de arranque
1. Mark decide el borrado (o libera espacio de otra forma). 2. Espejo sin cortes durante ≥ 30 min seguidos en el muestreo de 1 s. 3. Orden de Mark. Cronograma desde `s10` (T): +33 min k01; +70 min g01; +≈ 3 h 18 fin de batería; +≈ 3 h 52 `s40`; +≈ 4 h 12 `s50`. Rotación: 00:00Z (19:00 Perú). Recomendado T ≤ 17:30Z (12:30 Perú); no arrancar después de 18:45Z (13:45 Perú).
