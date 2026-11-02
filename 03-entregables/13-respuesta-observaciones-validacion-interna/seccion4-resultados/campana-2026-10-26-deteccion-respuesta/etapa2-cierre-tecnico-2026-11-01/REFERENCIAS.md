# Referencias e insumos del cierre técnico

## Código

| Qué | Dónde | Identificador |
|---|---|---|
| Rama candidata | `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`, rama `candidato/etapa2-20261101` | `953a436` (sobre `3083f60`, sobre la base `2be5335`) |
| `scripts/engine/motor_decision.py` en `953a436` | — | sha256 `8afec81d6b786803d8bea978d4ab94a8717fb68326f26121c9dd8116cd77b47d` |
| `scripts/engine/motor_incremental.py` en `953a436` | — | sha256 `32f343b1036529cf9ff8ab263c40bbf23150a8a6de83f250da6fdd84e7919d02` |
| `scripts/engine/replay_motor.py` en `953a436` | — | sha256 `90db6cbbd49c16af7f29d12f197fa0238ff8d0727c9f8f94342b950919fad58a` |
| Analizador del 3B, sin modificar | `../scripts/analizar_3b.py` | sha256 `27e67fd1620762d7ec7cb172ea45465ad6edb7db77cf8d69c7c8102c8167050f` (el mismo que en la revisión 3B) |
| Módulos que usa el analizador | `../scripts/analizar.py`, `../scripts/poblacion.py` | sha256 `71674908…c763a` y `7b140ae4…3511b` |

Todos los replays de `resultados/replays/` se ejecutaron con estos tres ficheros del motor (`resultados/hash-codigo-replays.txt`). Los ensayos del banco sobre relé, agente y helper (`resultados/ensayos/`) se hicieron con el código de enforcement de `3083f60`. `953a436` solo cambia el motor, como muestra `git show --stat 953a436`.

## Datos (sin modificar)

| Insumo | Ruta | sha256 |
|---|---|---|
| Marcas del orquestador | `../ejecucion-3b-2026-11-01/evidencia/sensor/marcas.jsonl` (y `copias/marcas.jsonl`, idéntico) | `276314a81176a0eb914785f0a51738e0256aba48168ce05d9f1f016936d4243a` |
| Configuración de la campaña | `../ejecucion-3b-2026-11-01/evidencia/sensor/herramientas/config-campana-3b.json` | `cbf72fbb0f112e3db5cc3724640ee18fb3d42f1bc5e24680f5af25faf1939d60` |
| Evidencia de destino | `../ejecucion-3b-2026-11-01/evidencia/sensor/analisis/destinos-3b.csv` | `0f58e3f87b64f731500a9c578397b0166b8ec36b8fd25925fa61ec20bb6be063` |
| Calidad de fuentes (pérdidas de Suricata) | `../ejecucion-3b-2026-11-01/evidencia/sensor/analisis/calidad-fuentes.json` | `f6c7851ab6d9811824e31cf01126fdc6b39e8333c8dd38777699c95c10140347` |
| Integridad v2 | `../revision-3b-2026-11-01/resultados/sensor/integridad-v2.json` | `667d804e9548b6f2d4a6cb7e853e697d4eb31a9cb23443299beb5dd17f2d307c` |
| Análisis en vivo revisado (comparación) | `../revision-3b-2026-11-01/resultados/analisis-revisado/analisis-3b.json` | `87bfb2abf597d1036abf4f095a05e07a1f6b3a6b656d190aca3fc4b76527a784` |
| PCAP archivado del 3B | 844 ficheros `live-*.pcap` (07:04:56–10:35:53), fuera del repositorio (`.gitignore`: `*.pcap`) | Cada fichero coincide con `../ejecucion-3b-2026-11-01/evidencia/sensor/voluminosos-sha256.txt` (`sha256sum -c`: 844/844) |
| EVE del 3B (segmento) | fuera del repositorio (`eve.json*`) | `b7bf61a20a88d789c6fa6dedabd9cf1d6dbe08166da0b9cc24ab2d9a5ae9318f` |
| Modelo desplegable `if_limpio_2026_10` | fuera del repositorio (`*.joblib`) | `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60` (el `model_sha256` de su manifiesto) |
| Manifiesto del modelo | `manifest-if-limpio-2026-10.json` | `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7` |

### Anillos re-troceados

Generados con `trocear_pcap.py` a partir del PCAP archivado. Sus registros son idénticos a los del original (`registros_identicos: true`):

| Anillo | Ficheros | Paquetes | sha256 de los registros |
|---|---|---|---|
| Tramo 08:30–09:10, 15 s | 161 | 2 229 358 | `85f2bf17…16c9` |
| Tramo 08:30–09:10, 5 s | 481 | 2 229 358 | `85f2bf17…16c9` |
| Completo, 5 s | 2535 | 9 579 930 | `105bc3f0…b1e7` |

## Antecedente

La entrega `../etapa2-candidata-2026-11-01/` (documentación `c90c689`) se conserva sin cambios.

Sus replays del tramo (`tramo-r1` … `tramo-r7`) se compararon con el mismo comparador (`resultados/comparaciones/tramo-anterior.json`). Sus afirmaciones corregidas están en `CONCLUSIONES-CORREGIDAS.md`.
