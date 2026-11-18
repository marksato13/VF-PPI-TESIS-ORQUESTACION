# Referencias a los originales y hashes

Rutas en los hosts del laboratorio (relativas a la cuenta de servicio; sin credenciales). Hashes sha256 completos.

| Elemento | Ubicación | sha256 |
|---|---|---|
| PCAP de la corrida (2.846 ficheros de 5 s) | Sensor1 `~/cf-e4/4c-A-completa-20261110T0951Z/archivo-pcap/` | por fichero en `protocolo/pcap-lista-fija.csv` (los 1.583 usados) |
| Marcas del generador | Sensor1 `…/copias/marcas.jsonl` (idéntico en el bastión `~/cf-e4/4c-A-completa-20261110T1033Z/corrida/`) | `5fd72ab9da47eb7fddc498debec1f4affcdb127e3636c339663d362d3e3fe1c1` |
| Decisiones del motor | Sensor1 `…/copias/motor_decision.log` (91.094.575 bytes) | `733d7a0cab66ef1a6358c80cc2285a6d0da8693722c11a018c5dfb49bb9267cd` |
| Análisis `s50` v2 | `main`: `…/etapa4-4c-s50-v2-2026-11-10/evidencia/analisis-v2/analisis-4c/analisis-3b.json` | `3aa77fc0f5b70694cafb260f5d6edabe54bbfa10c870fed8f8a6e7c7fb0215f1` |
| Control de CyberFlow (`s50`) | `…/analisis-v2/control-4b.json` | `2b6db072b067ffbd99b03561e77f31edf97122d354629f5ce09b870517058122` |
| Modelo IF | Sensor1 `~/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib` | `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60` |
| Manifiesto del modelo | idem `manifest-if-limpio-2026-10.json` | `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7` |
| Heurísticos / motor | Sensor1 `~/cyberflow-e4/ec78ca5/scripts/engine/` | `heuristicos.py` `5d30ffe6a8156c07954f39752e175becb7bfa0fd21a6119e1e6537b2a1217f68`; `motor_decision.py` `b652582dd9ac8ee5754bde9fb1b9cb90bc713575320685232353033014dfc565` |
| Reglas ET Open | comparador `/var/lib/suricata/rules/suricata.rules` | `7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9` |
| Tarball de reglas | comparador `~/et-open-20261002.tar.gz` | `3facf0eaed30caf56d2eba43d96ccd2b79dcc851c8d6be4c822e67b4120a7355` |
| YAML original / principal | comparador `/etc/suricata/suricata.yaml` / `~/cf-4.3/suricata-homenet-principal.yaml` | `d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650` / `8dc620e3bbd73a904a5a5444e07224c53a4f1d64d479db1a7c1ae67b3fc78346` |
| Salidas de Suricata | comparador `~/cf-4.3/out/{principal,s1}/<rebanada>/eve.json.gz` (+ `suricata.log`, `alertas.jsonl`) | por rebanada en `manifiestos/trazabilidad-rebanadas.csv` (`*_eve_sha256`, `*_eve_gz_sha256`) |
| Registros de comparación | `main`: `02-metodologia/comparacion-cyberflow-suricata/27-…`, `28-…` (Nikto) | notas 27 `7ca840508aefc051…`, 28 `37e5cab13da3f5b3…` (16 primeros caracteres) |

Decisión de α = 0,01 (Mark, 10-nov-2026): consta en el documento de trabajo de la Campaña B `PREPARACION-B-RESULTADOS-2026-11-10.md` §1 y §16 (**no publicado**; sha256 `f360032760814441e7a4035c125dafb0ede113d177ea92e5f9ca5d4e36b97a87`) y en el registro `~/cf-b/alfa-b.json` del Sensor1 (sha256 `c61c4e015e68eb36d313f148df78cf2b70a9f1d738b3749f58bdb63a052ac9e6`). La calibración de los umbrales (cuantil 0,01 de 65.553 puntuaciones de validación) está en `main`: `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json`.
