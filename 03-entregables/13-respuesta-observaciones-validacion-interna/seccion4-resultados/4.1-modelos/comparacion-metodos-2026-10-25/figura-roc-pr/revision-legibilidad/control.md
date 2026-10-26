# Verificación de la revisión de legibilidad

Datos: `028de214fb2ddc809f6eb4876574ada647b3dafb`. Referencia gráfica: `9ac4fbe04b51b012f363f42752589ed7b6dc2042`. Sin actualizaciones posteriores al comenzar.

## Datos y resultados preservados

SHA-256, claves y etiquetas comprobados en los cinco archivos. Sin claves duplicadas, puntuaciones no finitas ni filtros adicionales. Curvas: 65 421 normales + 84 ataques = 65 505; cero filas de validación. Validación: 65 553 solo para cuantiles 1−α lineales; detección estricta score > umbral. Se conservan las 74 normales Kali y todas las ventanas sin paquetes recientes.

AUC/AP, diez matrices de confusión, umbrales y coordenadas coinciden exactamente con la Tabla 7 y la primera publicación. Los CSV de curvas de 9ac4fbe se contrastan sin pérdida de precisión; no se duplican en esta revisión. `puntos.csv` es idéntico por bytes al CSV operativo anterior.

| Método | ROC-AUC | AP | ΔAUC vs JSON | ΔAP vs JSON |
|---|---:|---:|---:|---:|
| IF | 0.9247265513258 | 0.1858068839763 | 0.0 | 0.0 |
| OCSVM | 0.8690714573229 | 0.6356616971916 | 0.0 | 0.0 |
| LOF | 0.9762796422585 | 0.0290660721884 | 0.0 | 0.0 |
| Elliptic Envelope | 0.9179326428604 | 0.3811037448703 | 0.0 | 0.0 |
| PCA | 0.9486616355168 | 0.5944055724226 | 0.0 | 0.0 |

| Método | α | Umbral | TP | FP | TN | FN |
|---|---:|---:|---:|---:|---:|---:|
| IF | 0.05 | 0.5694578968203693 | 54 | 2955 | 62466 | 30 |
| IF | 0.03 | 0.5898535710336615 | 54 | 1723 | 63698 | 30 |
| OCSVM | 0.05 | -297.17116473859403 | 71 | 3319 | 62102 | 13 |
| OCSVM | 0.03 | -263.3060306010344 | 59 | 1958 | 63463 | 25 |
| LOF | 0.05 | 1.5094663238037738 | 79 | 3766 | 61655 | 5 |
| LOF | 0.03 | 2.189323719487029 | 77 | 2314 | 63107 | 7 |
| Elliptic Envelope | 0.05 | 247480102.42436323 | 48 | 3039 | 62382 | 36 |
| Elliptic Envelope | 0.03 | 989355962.2513443 | 44 | 1785 | 63636 | 40 |
| PCA | 0.05 | 4.233583332682266 | 71 | 3539 | 61882 | 13 |
| PCA | 0.03 | 5.745082955563664 | 71 | 2116 | 63305 | 13 |

## Comprobación de las imágenes

Principal: ejes completos 0–1, sin círculos/rombos ni leyenda alfa; cinco curvas, referencias fuera de los paneles, grosor uniforme. Los vértices SVG de las diez curvas se contrastan contra todos los vértices calculados; no se omite ninguno. PR steps-post sobre recall decreciente, área escalonada igual a AP; sin trapecios PR ni suavizado.

Ampliación del mismo experimento: ROC FPR [0; 0,065], TPR [0,45; 1]; PR recall [0,50; 0,98], precisión [0; 0,045]. Círculo abierto α=0,05, rombo abierto α=0,03, en ese orden. Marcadores de 4,2 y 3,2 pt, sin desplazamiento. Sus veinte posiciones SVG se contrastan con las matrices. Algunos trazados coinciden; las coordenadas no se separan artificialmente.

Prevalencia 84/65 505 = 0,0012823448591710556 (0,1282 %): su posición real se comprueba también en el SVG. AUC y AP de la ampliación corresponden a las curvas completas, no a las áreas ampliadas.

PNG 600 dpi; SVG sin imágenes raster; PDF vectorial con fuentes incrustadas. Comprobación de cajas de texto sin recortes ni leyendas solapadas. Previsualizaciones desde PDF a 180 dpi, en color y gris. Los parámetros y comprobaciones detalladas figuran en `control.json`.

Se trata de una evaluación reutilizada por ventana, no un nuevo test independiente. No se cargan modelos ni se cambia el Word o el despliegue.
