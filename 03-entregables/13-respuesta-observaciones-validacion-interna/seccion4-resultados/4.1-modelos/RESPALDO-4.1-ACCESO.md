# Acceso al respaldo canónico de 4.1

## Archivo

`../_campana/resultados-2026-10-23/eval41/v2/scores-todos-candidatos-full.csv.gz`

- Filas: 65 505.
- Configuraciones: 9 columnas de scores.
- Exportación: precisión completa, sin redondeo a seis decimales.
- SHA-256: `6e98219fb79a187b7256e664a4791a0619be70a68d9a23eee1e61c45de98ffc8`.
- Verificación: `cerrar_pendientes_41.py` comprueba hash, índices únicos, etiquetas, finitud y métricas.

## Acceso GitHub

Después de incorporar este archivo al repositorio, la URL verificable será:

`https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/blob/main/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/_campana/resultados-2026-10-23/eval41/v2/scores-todos-candidatos-full.csv.gz`

El archivo estaba excluido por la regla global `*.csv.gz`; la excepción específica de 4.1 ya fue añadida a `.gitignore`. Hasta que el cambio se confirme y se publique, la ruta local y este hash constituyen la verificación de integridad, pero no sustituyen el acceso GitHub.

## Archivo superado

`scores-todos-candidatos.csv.gz` contiene scores redondeados a seis decimales y no es el respaldo canónico para AP y ROC-AUC. Se conserva únicamente como artefacto histórico y no debe usarse para regenerar las tablas ni la figura.
