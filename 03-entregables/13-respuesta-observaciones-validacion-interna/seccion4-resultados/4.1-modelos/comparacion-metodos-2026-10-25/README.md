# Comparación de cinco detectores de novedad (25-oct-2026)

Compara el IF congelado `if_limpio_2026_10`, sin reentrenarlo, con One-Class SVM, LOF (`novelty=True`), Elliptic Envelope
y PCA por error de reconstrucción. Usa las mismas filas, las mismas 28 características y el mismo escalador congelado.
El umbral sigue un criterio común (cuantil 1−α de la validación) con α = 0,03 y 0,05.
Todo se calculó **offline** en el laptop. No se tocó el modelo desplegado, sus servicios ni su configuración.

## Archivos

| Archivo | Contenido |
|---|---|
| `config-comparacion.json` | Configuración registrada **antes** de entrenar, más la desviación D1 (Elliptic Envelope) |
| `comparar_metodos.py` | Código único: auditoría, entrenamiento por método, consolidación y manifiesto |
| `AUDITORIA-DATOS.json` | Conteos, exclusiones, solapes por clave y calidad de las 28 variables |
| `salidas/puntuaciones-<método>.csv.gz` | Puntuación de anomalía por ventana, con clave y etiqueta (validación 65 553, prueba normal 65 421, ataques 84) |
| `salidas/meta-<método>.json` | Parámetros usados, tiempos, diagnósticos y avisos de cada método |
| `TABLA7-comparacion-completa.csv` | Tabla completa con precisión total |
| `TABLA7-comparacion.md` | Tabla legible (paneles α = 0,03 y 0,05; umbrales y tiempos) |
| `resultados-comparacion.json` | Todo lo anterior más la verificación del IF, los diagnósticos y el solapamiento de detecciones |
| `MANIFIESTO-COMPARACION.json` | Versiones, semilla y SHA-256 de entradas, código y salidas |
| `REFERENCIAS-VERIFICADAS.md` | Fuentes primarias verificadas y pendientes bibliográficos |
| `NOTA-COMPARACION.md` | Hallazgos técnicos, alcance y pendientes |

## Reproducir

Hace falta una copia de solo lectura de los artefactos del sensor (`~/cyberflow/artifacts`). El script verifica sus SHA-256
contra `../calibracion-alfa-2026-10-24/datos-sensor/sensor-procedencia.json` y se detiene si alguno no coincide.

```
DIR/preliminar/limpio-2026-10/{particionado-limpio.csv, if_limpio_2026_10_desplegable.joblib,
                               manifest-if-limpio-2026-10.json, if_limpio_2026_10.json}
DIR/aprendizaje/oro/oro.csv
DIR/aprendizaje/ataques/ataques-nota-M.csv
DIR/escalador-congelado.json        (opcional: parámetros del escalador exportados en el sensor)
```

```
python comparar_metodos.py --datos DIR --auditar
python comparar_metodos.py --datos DIR --metodo IF          # y OCSVM, LOF, EllipticEnvelope, PCA
python comparar_metodos.py --datos DIR --consolidar
```

Los datos crudos (`particionado-limpio.csv`, 150 MB) **no** se publican en este repositorio. Están en el sensor y se identifican por su hash.
