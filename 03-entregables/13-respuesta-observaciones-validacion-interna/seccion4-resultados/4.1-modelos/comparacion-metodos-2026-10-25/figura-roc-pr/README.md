# Figura ROC y precisión–recall: cinco detectores

Fuente única: [028de214fb2ddc809f6eb4876574ada647b3dafb](https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/commit/028de214fb2ddc809f6eb4876574ada647b3dafb). Sin actualizaciones posteriores al iniciar la tarea. Entradas leídas de blobs Git fijados; se comprueba además que las copias locales coincidan. No se mezclan candidatos históricos.

## Entregables

- `roc-pr-cinco.png`: figura principal, 18 × 11 cm, 600 dpi; ambos paneles y ejes completos 0–1.
- La misma figura en `.svg` y `.pdf`, vectoriales, con texto conservado y fuentes TrueType incrustadas en PDF.
- `ampliacion.png`, `.svg`, `.pdf`: ampliación explícita de los puntos operativos; no sustituye la figura principal.
- `*-revision-180dpi.png`: renderizados desde los PDF para revisión a tamaño de inserción.
- `curvas-roc.csv` y `curvas-pr.csv`: todas las coordenadas de todos los umbrales; precisión de ida y vuelta de float64 mediante `repr`.
- `puntos-operativos.csv`: las diez configuraciones, primero α = 0,05 y luego α = 0,03 para cada método.
- `VERIFICACION-FIGURA.md` / `.json`: conteos, hashes, métricas, matrices, diferencias y comprobación de las exportaciones.
- `generar_figura.py`: auditoría y generación reproducibles, sin carga ni ajuste de modelos.
- `MANIFIESTO-FIGURA.json`: commit fuente, versiones, hashes de entradas y salidas.

## Reproducción

La raíz del repositorio se localiza automáticamente. El commit fuente debe estar disponible en Git. Versiones exactas de las bibliotecas en el manifiesto; no hace falta conexión al sensor. Las curvas y conteos son reproducibles; otras versiones de fuentes o renderizadores pueden cambiar los bytes de los gráficos.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde la raíz local del repositorio:
`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio`.

```powershell
python "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\figura-roc-pr\generar_figura.py" --solo-auditar
python "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\figura-roc-pr\generar_figura.py"
```

## Convenciones

Curvas exclusivamente con 65 421 normales y 84 ataques (65 505). Validación (65 553) solo para cuantiles. Todas las observaciones de cada conjunto se conservan, incluidas 74 normales Kali y las ventanas sin paquetes recientes. Mayor puntuación = más anómalo. Sin submuestreo, suavizado, búsqueda de hiperparámetros ni cambios al despliegue.

Los umbrales en CSV de curvas representan inclusión `score >= threshold`, convención de scikit-learn. ROC comienza con `inf`. En PR la última fila es el punto terminal (recall 0, precisión 1), sin umbral. En `puntos-operativos.csv` la regla es estricta `score > quantile(validacion, 1−α, method='linear')`; las coordenadas se calculan de sus matrices, no por proximidad a una curva.

PR se dibuja con `steps-post` sobre recall decreciente: AP = −ΣΔrecall·precision[:-1]. Se conserva cada umbral (`drop_intermediate=False`). No se calcula área trapezoidal PR ni envolvente de precisión. ROC se representa con todos los vértices empíricos. Cada método tiene el mismo grosor en ambos paneles, colores Okabe–Ito y estilo de línea diferenciado. Círculo abierto grande = α 0,05; rombo abierto pequeño = α 0,03. No hay desplazamientos de coordenadas.

Prevalencia = 84/65 505 = 0.001282344859171, marcada a su altura real; no se eleva para hacerla visible.

## Lectura y alcance

El panel PR completo comprime puntos operativos de precisión ≈ 0,016–0,033 cerca del eje. Algunas curvas y marcadores se superponen; la ampliación separada permite inspeccionarlos sin cambiar la figura principal ni los datos. Todas las métricas de leyenda pertenecen al conjunto completo, también en la ampliación.

ROC-AUC y AP resumen aspectos diferentes de la ordenación: se muestran los valores recalculados aunque su ranking difiera. La comparación es por ventana y reutiliza la evaluación; no es una nueva prueba independiente ni una selección de umbrales óptimos. La fuente usa 65 553 ventanas de validación; no confundirla con las 65 633 del umbral operativo desplegado. El Word y el sistema vivo no se modifican.
