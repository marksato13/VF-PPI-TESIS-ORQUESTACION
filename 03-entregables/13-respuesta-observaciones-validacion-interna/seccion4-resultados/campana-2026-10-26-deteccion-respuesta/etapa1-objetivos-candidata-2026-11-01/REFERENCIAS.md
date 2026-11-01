# Referencias consultadas (Etapa 1, 1-nov-2026; versión 2)

## HEAD consultado al empezar la corrección (versión 2)

| Repositorio | Rama | HEAD |
|---|---|---|
| Documentación (`VF-PPI-TESIS-ORQUESTACION`) | `main` | `2482a4024c730564574c6cc819b0afd02a2a66f7`, la entrega que se corrige |
| Código (`VF-Sistema-Open-Source-…`) | `main` | `7b275b8bab1c8343e55f40a103ee980dc497620b` (sin cambios desde la versión 1) |
| Código | `candidato/motor-rendimiento-20261031` | `24f8a80e376d89b78454fd16854d2239a1b7d278` (sin cambios; es el motor desplegado) |

En la versión 2 se consultó además `configs/features/multilayer-v2.json` (en `24f8a80`): 28 características, **12 de ellas L7 del EVE**, y `configs/cyberflow.local.toml` (`esquema = "configs/features/multilayer-v2.json"`).

## Repositorios y commits

**Documentación:** https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION

| Commit | Contenido | Uso en esta etapa |
|---|---|---|
| `2482a40` | Etapa 1, versión 1 | entrega corregida por esta versión (se conserva en Git) |
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
