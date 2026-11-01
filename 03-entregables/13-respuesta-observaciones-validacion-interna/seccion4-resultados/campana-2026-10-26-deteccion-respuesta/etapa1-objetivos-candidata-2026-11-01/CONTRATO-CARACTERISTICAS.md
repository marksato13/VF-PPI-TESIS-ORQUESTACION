# Contrato de características del IF (verificado el 1-nov-2026)

**Corrección documental:** el IF desplegado usa **28** características, de las que **11** son L7 del EVE, no 12 como decía la versión 2. El esquema ampliado tiene **31**: añade 3 de L2 que el IF actual **no** usa.

La corrección **no** cambia el vector de entrada, el escalador, el modelo ni sus umbrales, y **no** requiere reentrenar.

| Capa | Características del IF | Procedencia | Orden en el vector |
|---|---|---|---|
| L3 | **9** | PCAP | 1–6, 15–17 |
| L4 | **8** | PCAP | 7–11, 18–20 |
| L7 | **11** | EVE (Suricata) | 12–14, 21–28 |
| **Total del IF** | **28** | 17 PCAP + 11 EVE | — |
| L2 (solo en el esquema ampliado `multilayer-v3.json`) | 3: `arp_request_rate_10s`, `unique_src_mac_30s`, `mac_ip_binding_changes_60s` | PCAP | 29–31 |

La lista completa por nombre, orden, capa y fuente está en `resultados/contrato-caracteristicas.json`.

## Qué se comprobó y dónde

| Fuente | Versión | Resultado |
|---|---|---|
| `configs/features/multilayer-v2.json` | rama `candidato/motor-rendimiento-20261031` `24f8a80`, copiado en `contrato/` | 28 entradas, `order` 1–28 contiguo, nombres únicos |
| El mismo fichero **en el sensor** | `e032a1a2…` | idéntico al del repositorio salvo los finales de línea (CRLF) |
| `configs/cyberflow.local.toml` del sensor (`5b157749…`) | — | `esquema = multilayer-v2.json`; modelo y manifiesto `limpio-2026-10` |
| Manifiesto del modelo desplegado `manifest-if-limpio-2026-10.json` (`b3ad6805…`), copiado del sensor | `if_limpio_2026_10`, `model_sha256 df547da0…` | `schema: multilayer-v2.json`, `n_features: 28`, y la lista `features` **idéntica y en el mismo orden** que el esquema |
| Joblib desplegado, cargado con el Python del sensor (solo lectura) | `df547da0…` | `Pipeline`: `StandardScaler` y `IsolationForest`, ambos con **`n_features_in_ = 28`** |
| Extractor `scripts/features/extract_multilayer_v2.py` | `24f8a80` | `FEATURE_NAMES` (leído con `ast`, sin ejecutarlo) idéntico al esquema y en el mismo orden; las 11 L7 se calculan a partir de las observaciones de `eve.json` (`load_app_observations`) |
| `motor_decision.py`, líneas 374–379 | `24f8a80` | ordena el esquema por `order` y **aborta** si no coincide con `extractor.FEATURE_NAMES` |
| `configs/features/multilayer-v3.json` | `24f8a80` (igual en el sensor, `bf48a798…`) | 31 = las 28 en el mismo orden + 3 L2 de PCAP |

**Características frente a metadatos:** `METADATA_COLUMNS` del extractor (`packet_count_10s`, `syn_count_10s`, `dns_query_count_60s`, `http_request_count_60s`…) son **contadores auxiliares**, no entradas del modelo. Los heurísticos usan sus propios contadores, que tampoco son características del IF.

## Comprobación reproducible

Lo ejecuto yo: `[LAPTOP Git Bash]`, desde la carpeta de la Etapa 1.

```bash
export PYTHONDONTWRITEBYTECODE=1
python -I -B herramientas/contrato_caracteristicas.py --esquema contrato/multilayer-v2.json \
  --ampliado contrato/multilayer-v3.json --manifiesto contrato/manifest-if-limpio-2026-10.json \
  --extractor contrato/extract_multilayer_v2.py --salida resultados/contrato-caracteristicas.json
```

Salida: `por capa: {'L3': 9, 'L4': 8, 'L7': 11} | por fuente: {'eve': 11, 'pcap': 17}` y 13 comprobaciones OK. Las pruebas de `pruebas/test_presupuesto_e2e.py` (bloque 7) repiten el conteo y comprueban que una capa alterada se detecta.

La lectura del sensor (sha256, `n_features_in_`) está en `contrato/sensor-lectura-modelo.txt`. Se hizo sin sudo y sin cambios.
