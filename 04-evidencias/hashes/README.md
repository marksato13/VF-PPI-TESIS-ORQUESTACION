# Hashes de referencia

**Aquí no se copian artefactos: se copian sus huellas.**

Hay **dos mecanismos** de referencia al producto, según lo que se referencia:

| Qué se referencia | Cómo | Dónde |
|---|---|---|
| Artefactos **congelados** (dataset, modelo) | hash **SHA-256 de fichero** | este fichero de huellas |
| Código que **evoluciona** (panel, scripts, docs) | hash **de commit** | tablas de Evidencia de cada fase (`02-metodologia/fases/`) |

Ambos son inmutables: un commit fijo apunta a un estado exacto del árbol igual
que un SHA-256 apunta a un fichero exacto.

| Archivo | Qué es | Fecha |
|---|---|---|
| `SHA256SUMS-producto-2026-09-04.txt` | Los 13 artefactos congelados del producto | 4 sep 2026 |

Verificación, desde el repositorio del producto:

```bash
sha256sum -c docs/dataset/SHA256SUMS   # esperado: 13 archivos OK
```

Si un hash cambia sin autorización explícita, **es un incidente**: se detiene la
tarea y se reporta antes de continuar.

## Auditoría anti-duplicación

**29 sep 2026** — comparado el árbol completo de ambos repos: **0 copias
byte-idénticas de artefactos** (la única coincidencia es este propio fichero de
huellas, que es la referencia), **0 ficheros con el mismo nombre divergentes**,
los **13/13** artefactos congelados siguen casando con su huella, y todos los
commits y ficheros citados en las fases resuelven en el producto. La regla
"solo referencias, jamás copias" se cumple.
