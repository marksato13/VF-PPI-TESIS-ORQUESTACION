# Revisión de legibilidad de ROC y precisión–recall

Revisión de diseño de [la figura original](https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/tree/9ac4fbe04b51b012f363f42752589ed7b6dc2042/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25/figura-roc-pr); no es otro experimento.

- Datos fijados a `028de214fb2ddc809f6eb4876574ada647b3dafb`; primera publicación y auditoría reutilizable fijadas a `9ac4fbe04b51b012f363f42752589ed7b6dc2042`. HEAD y origin/main al iniciar: 9ac4fbe, sin commits posteriores.
- `principal.png`, `.svg`, `.pdf`: 18 × 10 cm, PNG 600 dpi; cinco curvas completas 0–1, sin marcadores ni leyenda alfa. Referencias en las leyendas bajo cada panel.
- `ampliacion.png`, `.svg`, `.pdf`: 18 × 11,2 cm; mismos datos, colores, estilos y métricas. Conserva diez configuraciones (veinte marcadores en total): círculo abierto α=0,05, rombo abierto α=0,03. No se desplazan coordenadas.
- `previa.png` y `zoom-previa.png`: renderizados PDF a 180 dpi para revisión al tamaño de inserción.
- `gris.png` y `zoom-gris.png`: las mismas previsualizaciones en escala de grises para comprobar los patrones de línea.
- `generar.py`: código reproducible. La auditoría de la primera publicación se carga de Git tras verificar su hash; no se ejecuta su generador ni se escribe en las carpetas anteriores.
- `puntos.csv`: copia exacta del CSV anterior, umbrales y diez matrices preservados.
- `control.md` y `control.json`: verificaciones numéricas y de exportación.
- `MANIFIESTO.json`: commits, versiones y hashes de todas las entradas y salidas. Los CSV completos de curvas permanecen en [la versión original](https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/tree/9ac4fbe04b51b012f363f42752589ed7b6dc2042/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/4.1-modelos/comparacion-metodos-2026-10-25/figura-roc-pr), identificados por commit y hash.

## Reproducción

Se necesitan los dos commits en el historial local, numpy, scikit-learn, Matplotlib, Pillow y PyMuPDF. No se necesita acceso al sensor. Las rutas largas de Windows se manejan internamente sin cambiar la configuración del sistema. Los datos, las métricas y las coordenadas son reproducibles; el renderizado puede cambiar en otras versiones de bibliotecas o fuentes.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde la carpeta de esta revisión:
`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\figura-roc-pr\revision-legibilidad`.

```powershell
python generar.py --solo-auditar
python generar.py
```

La opción de auditoría no escribe archivos.

## Lectura y alcance

Paleta Okabe–Ito y cinco patrones de línea diferentes, idénticos en ambos paneles; grosor 1,05 pt para todos los métodos. No se destaca IF. No hay explicaciones dentro de los paneles.

Límites de ampliación: ROC FPR 0–0,065, TPR 0,45–1; PR recall 0,50–0,98, precisión 0–0,045. La nota bajo las leyendas aclara que ROC-AUC y AP pertenecen a las curvas completas. Las curvas o puntos que se superponen conservan sus posiciones; los dos alfas usan tamaños y formas distintos. No son umbrales óptimos.

PR mantiene cada escalón, sin interpolación suave, envolvente ni área trapezoidal: `steps-post` sobre recall decreciente; AP = −ΣΔrecall·precision[:-1]. ROC y PR se calculan con todas las puntuaciones de evaluación, nunca con predicciones binarias. Validación se usa solo para los diez cuantiles.

Se mantienen las 74 normales Kali y las ventanas sin paquetes recientes. No se reentrena, repuntúa, reetiqueta ni filtra. No se edita el Word ni se modifica el sistema. La evaluación sigue siendo reutilizada y por ventana: el cambio de diseño no cambia conclusiones.
