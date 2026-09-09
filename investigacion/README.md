# Investigación

El registro de **cómo se hizo** el producto: diseño experimental, campañas,
modelado, validación y los requisitos del jurado.

Está aquí y no en el repositorio del producto porque son cosas distintas. El
producto responde a *qué es y cómo se usa*; esto responde a *cómo se llegó a
él y por qué se decidió así*.

| Carpeta | Qué hay |
|---|---|
| `fase00-infraestructura/` | Las 5 VM, las 3 redes, el modelo de acceso |
| `fase01-diseno-experimental/` | Campañas, gates G0–G7, techos de carga |
| `fase02-features-multicapa/` | Diccionario de variables, versiones G5 y v2 |
| `fase03-dataset/` | **182 documentos**, uno por campaña |
| `fase04-modelado/` | Los 7 candidatos, ablación, significancia, estabilidad |
| `fase05-motor-tiempo-real/` | Diseño del motor y sus fallos de producción |
| `fase06-dashboard/` | Panel operativo |
| `fase07-validacion-final/` | F6: 58 corridas, 2 pases |
| `07-mejoras-futuras/` | Debilidades con su costo y riesgo |
| `requisitos-jurado/` | Las observaciones del jurado |
| `CLAUDE-producto.md` | Instrucciones de trabajo del producto |

## Lo que hay que saber al usarlo

**Las cifras se verifican en su fuente primaria**, que está aquí, pero los
artefactos que las producen viven en el repositorio del producto. Antes de
citar un número, compruébelo con `stack/bin/ppi-trace cifra <valor>`.

**El diccionario de variables se duplicó a propósito.** La versión v2 vive
también en el producto como `docs/dataset/DICCIONARIO_VARIABLES.md`, porque
define las columnas del dataset que se publica y sin ella nadie puede
interpretarlo. Si cambia una, cambie la otra.
