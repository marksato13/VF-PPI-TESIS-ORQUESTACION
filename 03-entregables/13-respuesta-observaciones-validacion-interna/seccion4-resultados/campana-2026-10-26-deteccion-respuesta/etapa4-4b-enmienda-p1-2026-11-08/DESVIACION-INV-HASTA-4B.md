# Desviación respecto a la regla literal del protocolo 4B: `INV_HASTA` (09-nov-2026)

**Decisión de Mark (chat, 09-nov-2026): opción A.** Se documenta aquí por separado para no confundir dos instantes distintos.

## Los dos instantes

| Qué | Valor | De dónde sale |
|---|---|---|
| **Cierre físico del archivo** | **2026-11-09T03:00:41Z** | Último PCAP `OK` del archivador (`live-20261109030036.pcap`, inicio 03:00:36Z) + 5 s. El archivador se detuvo en `s40` (TERM a las 03:00:22Z, `FIN OK` 03:01:13Z, 7173 de 7173). |
| **Corte efectivo del replay (inventario)** | **2026-11-09T02:05:00Z** | Argumento `--hasta` de `s30`, que el protocolo fija como `HASTA + 300 s` = 02:00:00Z + 300 s. La última ventana del inventario es `2026-11-09T02:04:50Z`. |

## Regla literal y por qué se desvía
El protocolo (§7.2 paso 8) define `<INV_HASTA>` = `cierre_archivo` = «inicio del último PCAP `OK` + 5 s». Esa regla supone que `s40` se ejecuta enseguida después de `s30`/`s20`, de modo que el cierre físico del archivo y el corte del replay coinciden.
En esta corrida no coincidieron: `s20` cumplió a las 02:05:56Z, el replay `s30` tardó 50 min 37 s (02:06:31Z → 02:57:08Z) y `s40` se ejecutó a las 03:00:22Z; el archivador siguió escribiendo 55 min más allá del corte del replay.

Aplicar la regla literal (`INV_HASTA` = 03:00:41Z) habría pedido a `s50` ventanas requeridas entre 02:05:00Z y 03:00:41Z para las que el inventario **no se calculó**, y las habría tratado como ventanas sin inventario. `INV_HASTA` define el rango del inventario (`--inventario-rango "INV_DESDE,INV_HASTA"`), por eso se fija en el rango que el replay realmente enumeró.

## Efecto sobre el análisis
- El control comparable es `[2026-11-08T18:00:00Z, 2026-11-09T02:00:00Z]` (8 h). Termina 5 min **antes** del corte del replay, así que el inventario cubre las 8 h completas con margen de 300 s.
- Los PCAP archivados entre 02:05:00Z y 03:00:41Z existen y están archivados (`copias/archivar.log`), pero no entran en el inventario ni en el análisis del control.
- No cambia ningún umbral, modelo, α, heurístico, clase ni criterio.

## Comando
`r4.sh s50_analisis_e4.sh sensor 4b 2026-11-08T17:15:48Z 2026-11-09T02:05:00Z 2026-11-08T18:00:00Z 2026-11-09T02:00:00Z`
(`INV_DESDE` = primer PCAP `OK` archivado 17:15:48Z; `INV_HASTA` = 02:05:00Z; control = 18:00:00Z → 02:00:00Z.)
