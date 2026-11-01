# Referencias: commits, ramas y hashes (Etapa 2)

## Repositorio del producto (código)

- Repositorio: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos>
- Rama candidata: **`candidato/etapa2-20261101`**
  <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/candidato/etapa2-20261101>

| Commit | Contenido |
|---|---|
| `24f8a80` | Base: el motor incremental instalado en sombra en el paso 2. **Es lo desplegado; no cambia.** |
| `420f921` | Etapa 2 (1/2): disparo por eventos en el motor, `decision_id` y `heuristicos` (todas las reglas), arnés de replay con reloj de coste, troceador PCAP, `evaluar_todas`, contrato feed v2 (`feed.py`) |
| **`2be53351fb47d03628d96c179078bf00c8105813`** | Etapa 2 (2/2): publicador v2, agente v2, helper nft restringido, relé por eventos, limpieza D5, unidades y sudoers candidatos, comparador de replays, tasa DNS, banco :2 con git, pruebas y ensayos |

Diferencia total frente a la base: `git diff --stat 24f8a80 2be5335` → 23 ficheros, +3179/−5.

Comparación en GitHub: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/compare/24f8a80...2be53351fb47d03628d96c179078bf00c8105813>

### sha256 de los ficheros clave en `2be5335`

Calculados con `git show 2be5335:<fichero> | sha256sum`.

```
b187a3d1c83a3f93f8a4e0b1552dfda8463fdd9f70e6a93a288b7aae3fe23a20  scripts/engine/motor_decision.py
079d8275430830eb4e8fd188c4ca94065d63de8b83b167b5c376405ac158c870  scripts/engine/heuristicos.py
9aca9ddfd31965455340130a951c7e1fc01673be3a22a0ebd3a617dfceb592ce  scripts/engine/feed.py
1429b958964def18e3ee8c73490921e1ee9049b62a7cf36af31db274ec32b861  scripts/engine/publicar_feed_v2.py
d686c187e0fdd8fad78691ed4b1d72222ea1d836ded9ccc28c7b29d3010b396e  scripts/engine/replay_motor.py
441999447db8f0d377f7983c125ab42db6c553ffa225b2f92bff4c98b0e1b4b0  scripts/engine/trocear_pcap.py
b09332da4c3fd67cd5450243482351af4849acc5f0553ce97516f995803bf389  scripts/engine/comparar_replays.py
bb218fdcc6e16aebf5eadcd04ea8d371f92765aaa21e68838d791dad48f6803b  scripts/engine/tasa_dns_por_origen.py
a54cc2f9159ecf17c402c79d40db523c8ade125ce2323959d65459570f9cc793  scripts/enforce/agente_enforce_v2.py
37b314e311b11e2fc03b12e09cd1261e76988c6990bf1599e84f62da5aa1119a  scripts/enforce/cf_nft_helper.py
d1f4eb15f5844b8b192fe74935c2f9e743829f05ca430378db0ef9da86ea472e  scripts/enforce/limpiar_origen.py
bea2e487aab5d2c8ee20597ff0769a063066a1384e149779662ef3263ebda84c  deploy/enforcement/relay_eventos.py
f8d26d7a459598033b13fc9641f00bb8d0f7279b5847bb1c0ed0611ea2a9f9df  deploy/enforcement/candidato-etapa2/cf-feed-ssh.sh
314950258cc350aabc721d03d6e4d7e33fd41ba2381a0b56570e0f24054c01dd  deploy/enforcement/candidato-etapa2/cf-nft-helper.sudoers
903fdd243048ed45abfab0e9684a541e6b977991f39c6855f9011946dad349c7  deploy/pruebas-aisladas/Dockerfile
c173925fec376cdf607ecc4c1875ba0bbd8d07dc74436efee8e3e11b575c150e  tests/test_etapa2_cadena.py
0afb99a962db84357b980f21f780deccdd25c552a490a339b3733c5ef2574324  tests/test_etapa2_disparo.py
```

## Datos de entrada de los replays

Archivados del 3B. **No se suben** por tamaño; están referenciados en el manifiesto del 3B.

| Dato | Identificación |
|---|---|
| PCAP del 3B | 844 ficheros `live-*.pcap` de 15 s. Concatenación de registros: 2 229 358 paquetes en el tramo troceado, sha256 de registros `85f2bf178c2305230e49466a22263ed4464957746e818ee578c634e69d3416c9` (`resultados/trocear-e5.json` y `trocear-e15.json`, idénticos en 5 y 15 s) |
| `eve-segmento.json` | 1 087 178 líneas (copia del 3B, `voluminosos-sha256.txt` del 3B) |
| `marcas.jsonl` | Marcas de la Kali del 3B |
| Modelo | `if_limpio_2026_10_desplegable.joblib`, sha256 `df547da0…`; manifiesto `b3ad6805…` (los del paso 2 y el 3B) |

## Banco aislado

- Imagen `cyberflow-etapa2-banco:2`, construida desde `deploy/pruebas-aisladas/Dockerfile` (sha256 arriba).
- ID local: `sha256:2ece1c602cbd8b97ace2aae97e38ac88ed86377c8cf73bc7a0f7b8cc37044b8c`.
- No se publica en ningún registro de imágenes.

## Repositorio de documentación

- <https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION>, rama `main`.
- Commit de esta entrega: el que añade esta carpeta. Su hash está en el mensaje del commit y en `git log -- <esta carpeta>`; no se escribe aquí porque un fichero no puede contener el hash del commit que lo incluye.
- Integridad de la carpeta: `MANIFIESTO.sha256` (verificable con `sha256sum -c MANIFIESTO.sha256` desde esta carpeta).
