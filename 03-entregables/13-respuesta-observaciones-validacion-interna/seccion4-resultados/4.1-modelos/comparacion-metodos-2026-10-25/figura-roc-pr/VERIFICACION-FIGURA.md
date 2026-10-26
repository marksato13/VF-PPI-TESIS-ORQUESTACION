# Verificación de curvas y puntos operativos

Fuente única: `028de214fb2ddc809f6eb4876574ada647b3dafb`. No existen revisiones posteriores al comenzar la tarea.

## Auditoría previa

- SHA-256 de las cinco puntuaciones, metadatos, tabla, JSON, configuración y código: coincidentes con el manifiesto y los blobs del commit.
- Cada archivo: 131 058 filas, sin claves duplicadas, claves vacías ni puntuaciones no finitas.
- Claves, particiones y etiquetas idénticas entre los cinco archivos.
- Curvas: 65 505 observaciones = 65 421 normales (0) + 84 ataques (1). Cero filas de validación en las curvas.
- Validación: 65 553 filas, usadas solo para cuantiles lineales 1−α. Regla estricta: puntuación > umbral.
- Se conservan las 74 normales de 10.10.20.30. No se filtran ventanas por actividad; las 45 558 normales sin paquetes recientes constan en el JSON fuente.
- Mayor puntuación representa mayor anomalía en los cinco métodos, según configuración y código de generación verificados.
- Sin carga de modelos, reentrenamiento, repuntuación, acceso al sensor ni cambios de despliegue.

## Métricas recalculadas

| Método | ROC-AUC | AP | ΔAUC vs JSON | ΔAP vs JSON |
|---|---:|---:|---:|---:|
| IF | 0.9247265513258 | 0.1858068839763 | 0 | 0 |
| OCSVM | 0.8690714573229 | 0.6356616971916 | 0 | 0 |
| LOF | 0.9762796422585 | 0.0290660721884 | 0 | 0 |
| Elliptic Envelope | 0.9179326428604 | 0.3811037448703 | 0 | 0 |
| PCA | 0.9486616355168 | 0.5944055724226 | 0 | 0 |

Referencias redondeadas del encargo: diferencias absolutas ≤ 5,1·10⁻¹¹; detalle completo en JSON. AUC contrastada por pares normal/ataque; AP por conteos independientes agrupados y por el área de escalones, no por trapecios PR.

## Puntos operativos (orden 0,05; 0,03)

| Método | α | Umbral anomalía | TP | FP | TN | FN | FPR prueba | Recall | Precisión |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IF | 0.05 | 0.5694578968203693 | 54 | 2955 | 62466 | 30 | 0.045168982437 | 0.642857142857 | 0.017946161515 |
| IF | 0.03 | 0.5898535710336615 | 54 | 1723 | 63698 | 30 | 0.026337108879 | 0.642857142857 | 0.030388294879 |
| OCSVM | 0.05 | -297.17116473859403 | 71 | 3319 | 62102 | 13 | 0.050732945079 | 0.845238095238 | 0.020943952802 |
| OCSVM | 0.03 | -263.3060306010344 | 59 | 1958 | 63463 | 25 | 0.029929227618 | 0.702380952381 | 0.029251363411 |
| LOF | 0.05 | 1.5094663238037738 | 79 | 3766 | 61655 | 5 | 0.057565613488 | 0.940476190476 | 0.020546163849 |
| LOF | 0.03 | 2.189323719487029 | 77 | 2314 | 63107 | 7 | 0.035370905367 | 0.916666666667 | 0.032204098703 |
| Elliptic Envelope | 0.05 | 247480102.42436323 | 48 | 3039 | 62382 | 36 | 0.046452973816 | 0.571428571429 | 0.015549076774 |
| Elliptic Envelope | 0.03 | 989355962.2513443 | 44 | 1785 | 63636 | 40 | 0.027284816802 | 0.523809523810 | 0.024056861673 |
| PCA | 0.05 | 4.233583332682266 | 71 | 3539 | 61882 | 13 | 0.054095779643 | 0.845238095238 | 0.019667590028 |
| PCA | 0.03 | 5.745082955563664 | 71 | 2116 | 63305 | 13 | 0.032344354259 | 0.845238095238 | 0.032464563329 |

Diez matrices idénticas a la Tabla 7 y al JSON; umbrales y tasas dentro de tolerancias de coma flotante (JSON). Conteos contrastados mediante búsqueda binaria independiente. No hay empates con los cuantiles. Los puntos se calcularon directamente, sin buscar un vecino ni desplazar coordenadas.

## Representación y límites de lectura

- Todas las puntuaciones y umbrales distintos se utilizan; `drop_intermediate=False` en ROC y PR; `path.simplify=False`.
- PR: `steps-post` sobre recall decreciente devuelto por scikit-learn. Su área es −ΣΔrecall·precision[:-1], igual a Average Precision. No se usa integración trapezoidal PR.
- Prevalencia: 84/65 505 = 0.001282344859171 (0.128234486 %), dibujada en su altura real.
- El desequilibrio hace que los puntos PR se concentren junto al eje inferior; la ampliación se entrega como complemento, no como sustitución de los paneles 0–1.
- Los solapamientos se mantienen en coordenadas reales. Círculo abierto = α 0,05; rombo abierto = α 0,03, con tamaños distintos.
- Métricas por ventana sobre evaluación reutilizada; no es un test independiente. Las curvas no demuestran superioridad universal ni equivalen al rendimiento operativo del sistema híbrido.
- Esta comparación usa 65 553 filas de validación, no las 65 633 del umbral operativo desplegado. Los puntos son configuraciones de referencia, no umbrales óptimos.

## Validación de exportaciones

[
  {
    "name": "roc-pr-cinco",
    "size_cm": [
      18,
      11
    ],
    "font_points": [
      8,
      9
    ],
    "texts_outside_canvas": [],
    "line_width_equal_all_methods": true,
    "path_simplification": false,
    "roc_bounds": [
      [
        0.0,
        1.0
      ],
      [
        0.0,
        1.0
      ]
    ],
    "pr_bounds": [
      [
        0.0,
        1.0
      ],
      [
        0.0,
        1.0
      ]
    ],
    "png_pixels": [
      4251,
      2598
    ],
    "png_dpi": [
      599.9988,
      599.9988
    ],
    "svg_has_raster_images": false,
    "pdf_has_raster_images": false,
    "pdf_text_extracted": "0\n0,2\n0,4\n0,6\n0,8\n1\nTasa de falsos positivos\n0\n0,2\n0,4\n0,6\n0,8\n1\nTasa de verdaderos positivos\nReferencia aleatoria\n(a) Curvas ROC\n0\n0,2\n0,4\n0,6\n0,8\n1\nRecall\n0\n0,2\n0,4\n0,6\n0,8\n1\nPrecisión\nPrevalencia:\n0,1282 %\n(junto al eje)\n(b) Curvas precisión–recall\nConfiguraciones de validación:\nIF  (ROC-AUC = 0.9247)\nOCSVM  (ROC-AUC = 0.8691)\nLOF  (ROC-AUC = 0.9763)\nElliptic Envelope  (ROC-AUC = 0.9179)\nPCA  (ROC-AUC = 0.9487)\nIF  (AP = 0.1858)\nOCSVM  (AP = 0.6357)\nLOF  (AP = 0.0291)\nElliptic Envelope  (AP = 0.3811)\nPCA  (AP = 0.5944)\nα = 0,05\nα = 0,03",
    "pdf_text_blocks_outside_page": []
  },
  {
    "name": "ampliacion",
    "size_cm": [
      18,
      11
    ],
    "font_points": [
      8,
      9
    ],
    "texts_outside_canvas": [],
    "line_width_equal_all_methods": true,
    "path_simplification": false,
    "roc_bounds": [
      [
        0.0,
        0.065
      ],
      [
        0.45,
        1.0
      ]
    ],
    "pr_bounds": [
      [
        0.5,
        0.98
      ],
      [
        0.0,
        0.045
      ]
    ],
    "png_pixels": [
      4251,
      2598
    ],
    "png_dpi": [
      599.9988,
      599.9988
    ],
    "svg_has_raster_images": false,
    "pdf_has_raster_images": false,
    "pdf_text_extracted": "0\n0,02\n0,04\n0,06\nTasa de falsos positivos\n0,5\n0,6\n0,7\n0,8\n0,9\n1\nTasa de verdaderos positivos\n(a) ROC: ampliación operativa\n0,5\n0,6\n0,7\n0,8\n0,9\nRecall\n0\n0,01\n0,02\n0,03\n0,04\nPrecisión\nPrevalencia = 0,1282 %\n(b) PR: ampliación operativa\nConfiguraciones de validación:\nIF  (ROC-AUC = 0.9247)\nOCSVM  (ROC-AUC = 0.8691)\nLOF  (ROC-AUC = 0.9763)\nElliptic Envelope  (ROC-AUC = 0.9179)\nPCA  (ROC-AUC = 0.9487)\nIF  (AP = 0.1858)\nOCSVM  (AP = 0.6357)\nLOF  (AP = 0.0291)\nElliptic Envelope  (AP = 0.3811)\nPCA  (AP = 0.5944)\nα = 0,05\nα = 0,03",
    "pdf_text_blocks_outside_page": []
  }
]
