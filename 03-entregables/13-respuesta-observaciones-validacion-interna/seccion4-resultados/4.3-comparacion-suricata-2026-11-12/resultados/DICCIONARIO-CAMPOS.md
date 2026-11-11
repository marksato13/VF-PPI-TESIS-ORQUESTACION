# Diccionario de campos — `resultados-por-episodio.csv` (21 filas, una por episodio elegible)

Segundos «desde el inicio» = marca − `inicio_utc` (marca del generador, `marcas.jsonl`). `cf_*` provienen de `analisis-3b.json` (`s50` v2) y `suri_*` de las alertas de Suricata (`extractos/<config>/<episodio>/alertas.jsonl`, no publicado; las alertas que cuentan están en `alertas-validas-episodios.csv`).

| Campo | Significado | Respaldo |
|---|---|---|
| `episodio`, `familia`, `repeticion`, `destino`, `servicio`, `inicio_utc`, `fin_utc`, `duracion_s` | Identificación y marcas del generador | `marcas.jsonl` (`evento` inicio/fin, `reloj.pared_utc`); `protocolo/episodios-campana-A-4c.csv` |
| `elegible` | Cumple integridad 12/12 y fuente C0 | `integridad.json`; `analisis-3b.json` → `en_poblacion_principal` |
| `cf_HIB01_detecta_tiempo_datos` | Primera ventana atribuible con señal de `HIB_0.01` cierra ≤ `fin_utc` | `analisis-3b.json` → `episodios.<id>.ventanas[]` (`senales`, `atribucion`, `window_end_utc`) |
| `cf_HIB01_cierre_ventana_utc` / `_s` | Cierre de la primera ventana con señal (marca de datos, rejilla de 10 s) | idem, `window_end_utc` |
| `cf_HIB01_escritura_senal_utc` / `cf_HIB01_disponibilidad_s` | Escritura de la señal (`registro_escrito_en` del ciclo) y segundos desde el inicio | idem, `disponible_utc`; `ciclos.jsonl` → `registro_escrito_en` |
| `cf_HIB01_retraso_s` | Escritura − cierre de ventana (redondeado por el analizador) | idem, `retraso_s` |
| `cf_HIB01_categoria_s50` | `oportuna` / `solo_posterior` / `ausencia_con_observacion_suficiente` | `analisis-3b.json` → `episodios.<id>.HIB_0.01.categoria` |
| `cf_IF01_*`, `cf_HEUR_*`, `cf_HIB03_*` | Mismas lecturas para IF α = 0,01, heurísticos y `HIB_0.03` (sensibilidad) | `analisis-3b.json` → `episodios.<id>.<config>.categoria` y ventanas |
| `cf_heuristico_en_ventana` | Regla heurística registrada en esa ventana | `ventanas[].heuristico` |
| `suri_P_*` / `suri_S1_*` | Suricata con `HOME_NET` principal / original. `validas_durante`, `validas_posterior`: alertas válidas con tiempo de paquete ≤ `fin` o en (`fin`, `fin`+60 s]; `firmas_ET_durante`: las válidas sin prefijo `SURICATA` | `protocolo/PROTOCOLO-REPLAY-4.3.md` §2 |
| `suri_P_primera_utc` / `_s` / `_sid` / `_firma` | Primera alerta válida durante el episodio | `alertas.jsonl` (`timestamp`, `sid`, `firma`) |
| `suri_P_primera_ET_*` | Primera alerta válida con firma ET (sin prefijo `SURICATA`) | idem |
| `suri_P_2221010_durante` / `_posterior` | Alertas SID 2221010 **filtradas** por intervalo, par y puerto | idem |
| `suri_P_excluidas_*_total_rebanada` | `SURICATA STREAM` y `ET INFO` de toda la rebanada (informativo; no filtrado por intervalo) | `resumen-eve.json`/`alertas.jsonl` |
| `coincidencia_*` | ambos / solo_CyberFlow / solo_Suricata / ninguno; `datos` o `disponibilidad` (criterio de CyberFlow) y `regla_fijada` o `solo_ET` (criterio de Suricata) | derivado de las columnas anteriores |
| `respaldo` | Dónde comprobar la fila | — |

`control-unidades-entidad-ventana.csv` (2.218 filas): `entidad`, `window_end_utc`, `score_if`, `heuristico`, `cf_IF01`/`cf_HEUR`/`cf_HIB01`/`cf_IF03`/`cf_HIB03` (1 = marcada), `suricata_principal_marcado`/`suricata_s1_marcado` y su número de alertas válidas y SID. Origen: `manifiestos/control-extracto-sensor1.txt` (filas `R`: `entidad, window_end, score, decision_if, heuristico, detector, decision`) y `extractos/<config>/control_30min/alertas.jsonl`.
