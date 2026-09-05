# Hashes de referencia

**Aquí no se copian artefactos: se copian sus huellas.**

| Archivo | Qué es | Fecha |
|---|---|---|
| `SHA256SUMS-producto-2026-09-04.txt` | Los 13 artefactos congelados del producto | 4 sep 2026 |

Verificación, desde el repositorio del producto:

```bash
sha256sum -c docs/dataset/SHA256SUMS   # esperado: 13 archivos OK
```

Si un hash cambia sin autorización explícita, **es un incidente**: se detiene la
tarea y se reporta antes de continuar.
