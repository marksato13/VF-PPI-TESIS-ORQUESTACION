# Referencias consultadas (Etapa 1, 1-nov-2026; versión 3)

## HEAD consultado al empezar la consolidación (versión 3)

| Repositorio | Rama | HEAD |
|---|---|---|
| Documentación (`VF-PPI-TESIS-ORQUESTACION`) | `main` | `c1de49d474dc86a36ce20e852ad04cced9897ad9`, la entrega que se consolida |
| Código (`VF-Sistema-Open-Source-…`) | `main` | `7b275b8bab1c8343e55f40a103ee980dc497620b` (sin cambios) |
| Código | `candidato/motor-rendimiento-20261031` | `24f8a80e376d89b78454fd16854d2239a1b7d278` (sin cambios; es el motor desplegado) |

**Ficheros de la versión 3** (todos de `24f8a80`, salvo los que se indican):

- `configs/features/multilayer-v2.json` (28) y `multilayer-v3.json` (31);
- `scripts/features/extract_multilayer_v2.py` (`FEATURE_NAMES`, `METADATA_COLUMNS`);
- `scripts/engine/motor_decision.py` (líneas 374–379, comprobación esquema = extractor);
- `deploy/enforcement/relay-feed.sh`, `ppi-enforce-agent.service` y `scripts/engine/feed.py` (firma ed25519 con openssl).

**Lecturas en vivo de solo lectura, 1-nov-2026, sin cambios:**

- **sensor** (`m4rk`): `cyberflow.local.toml`, manifiesto del modelo, sha256 y `n_features_in_` del joblib. Detalle en `contrato/sensor-lectura-modelo.txt`.
- **DC1** (`dcadmin`, cuenta de lectura documentada en `infra-2026-10-27/README-EVIDENCIA-INFRA.md`): sistema, Samba, DNS, nftables y dependencias. Detalle en `d1-dc1/`.
- **Desde el bastión:** LDAP rootDSE anónimo de DC1 y DC2, y banner SSH.
- `/etc/resolv.conf` de la Kali.

La corrección de la versión 2 se hizo sobre `2482a40` con los mismos HEAD de código.

## Repositorios y commits

**Documentación:** https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION

| Commit | Contenido | Uso en esta etapa |
|---|---|---|
| `c1de49d` | Etapa 1, versión 2 | entrega consolidada por esta versión (se conserva en Git) |
| `2482a40` | Etapa 1, versión 1 | entrega corregida por la versión 2 (se conserva en Git) |
| `f16b673` (origin/main al empezar la versión 1) | Revisión 3B: integridad v2, recálculo v2 y diagnósticos | población v2 (15/25), demora A–D, análisis revisado |
| `191b043` | Criterios v2, escritos antes del reanálisis | cadena de calidad de evidencia (sin cambios) |
| `67fc1f5`, `b714492` | Paso 3B: ejecución y evidencia byte a byte | marcas, `motor_decision.log.gz`, `ciclos.jsonl`, `control-declarado.json`, feed y estado finales, relojes |
| `1b35bf6`, `a07d64b` | Paso 3A cerrado | antecedentes del protocolo (inventario, no evaluadas) |
| `99fe3e8`, `b86ee8c` | Pasos 2 y 1 del motor incremental | procedimiento de instalación y reversión |

**Código:** https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos

| Ref. | Commit | Uso |
|---|---|---|
| `candidato/motor-rendimiento-20261031` | `24f8a80e376d89b78454fd16854d2239a1b7d278` | Motor desplegado en el sensor: `motor_decision` 6c274d9e, `heuristicos` 10deb05d (VERSION 2026-10-06.2), `motor_incremental` a403307a. Timers de `deploy/enforcement/`. |
| `main` | `7b275b8bab1c8343e55f40a103ee980dc497620b` | Versiones de repo del publicador (ea82777c), la escalada (0be76d51) y el agente (3ffd53cd) |
| `as-deployed-sensor-20261006` | `f57ca00771030296f0d83d60d8a39b4aad1f5a94` (snapshot as-deployed, 29-oct) y `6d92ff3` (16-oct) | Origen de las versiones **desplegadas** del publicador, la escalada y el agente |

## Versiones desplegadas frente a las del repositorio

Ficheros descargados en modo solo lectura del sensor y de srv-dmz, y copiados en `codigo-desplegado/`:

| Fichero | Desplegado (sha256, 8) | Dónde | `main` / candidato | Diferencia |
|---|---|---|---|---|
| `publicar_feed.py` | f7bc4c7d | sensor | ea82777c | **Solo docstrings, comentarios y formato.** El AST sin docstrings ni anotaciones es idéntico. |
| `escalada.py` | 7d80ab4a | sensor | 0be76d51 | Ídem: AST idéntico |
| `agente_enforce.py` | 2985c123 = `6d92ff3` | srv-dmz | 3ffd53cd (`22eb2a8`) | Docstrings y comentarios. La única diferencia del AST es construir `actuales` con un literal de diccionario en lugar de una comprensión: comportamiento equivalente. |
| `configs/cyberflow.local.toml` | 5b157749 | sensor | — | referencia de la configuración del motor |

**Conclusión:** el comportamiento de la cadena desplegada es el del código del repositorio. Las diferencias de texto se deben a que `main` reescribió comentarios y formato después del despliegue (`22eb2a8`).

## Cadencias medidas (Etapa 1, solo lectura)

| Medida | Valor | Cómo |
|---|---|---|
| Publicador: arranque y duración | :x0,29; p50 0,598 s, máx 0,773 s (972 ejecuciones del 3B) | journal del sensor (`ppi-publicar-feed.service`) |
| Relé: duración | 1,065–1,612 s | `systemctl show ppi-relay-feed.service` en el bastión |
| Agente: duración | p50 0,173 s, máx 0,564 s (76 201 ejecuciones, octubre) | journal de srv-dmz |
| Agente: estado actual | timer **inactivo y deshabilitado** (sombra) | `systemctl is-enabled/is-active` |
| Relojes | \|desfase\| ≤ 0,0036 s ± 0,0006 en los 4 hosts | `relojes-3b.log` |

## Evidencias anteriores sobre el enforcement

- `04-evidencias/cyberflow/N-e2e-enforcement-2026-09-30.md`: e2e con crones de 1 min.
- `04-evidencias/cyberflow/O-enforcement-vivo-campana-ataque-2026-10-01.md`: advierte que una ráfaga de 23 s caduca de la ventana del feed. El riesgo sigue presente con la ventana de 120 s para las decisiones tardías.
- `01-arquitectura/DISENO-ENFORCEMENT.md`: diseño un feed / N agentes, la escalera y NUNCA_BLOQUEAR.

## Hashes de las entradas de la herramienta

Están en `resultados/presupuesto-e2e.json` → `entradas_sha256`, calculados sobre los ficheros tal como se leen (el `.gz` comprimido).

El registro del motor descomprimido es `bf51f308dfa0bd66…`, el mismo que figura en `ejecucion-3b-2026-11-01/evidencia/sensor/copias/SHA256SUMS` y en `revision-3b-2026-11-01/resultados/sensor/sha256-entradas.txt`. Se comprobó con `gzip -dc | sha256sum`.
