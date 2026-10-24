# Nueva calibración α del IF congelado — nota (24-oct-2026)

Calibración **offline**. El modelo, el escalador y el umbral desplegados no cambian: el sensor
sigue con `if_limpio_2026_10`, umbral −0,5693969936322356 (α = 0,05, validación original).

## Procedencia

| Elemento | Valor |
|---|---|
| Modelo | `if_limpio_2026_10_desplegable.joblib`, SHA-256 `df547da0…fd60` = el declarado en el manifiesto desplegable |
| Pipeline | `StandardScaler` → `IsolationForest(n_estimators=500, random_state=20260813)`, 28 características, orden verificado contra el informe de entrenamiento |
| Datos | `particionado-limpio.csv` (SHA `5ef83b32…`, entrada declarada del entrenamiento), `oro.csv`, `ataques-nota-M.csv` |
| Puntuaciones | calculadas en el sensor en solo lectura (`datos-sensor/sensor_calib.py`, Python 3.14.4, scikit-learn 1.9.0, NumPy 2.5.1) |
| Documentación | `VF-PPI-TESIS-ORQUESTACION`, rama `main`, commit base `1b45e05` |
| Implementación | `VF-Sistema-Open-Source…`, `main` en origin = `b204f59`. No se ejecutó código del repo: el sensor no tiene `.git`; se usó el artefacto desplegado y su manifiesto |

Hashes completos de entradas, modelo y salidas: `MANIFIESTO-CALIBRACION-ALFA.json`.

## Qué está verificado

1. **Conteos:** entrenamiento 203 967 (204 148 de la partición − 181 con `eligible_training=False`), validación 65 633, prueba normal 65 421, ataques 84. Ver `TRAZABILIDAD-DATOS.md`.
2. **Las 181 exclusiones del entrenamiento** son la única diferencia entre `particionado-limpio.csv` y `particionado-nota-L.csv`. Son ventanas de 10.10.20.30 de la ráfaga del 27-sep (21:35–22:05 UTC).
3. **Independencia:** los 84 ataques no comparten ninguna clave (campaña, IP, ventana) con entrenamiento, validación ni prueba. Validación, prueba y entrenamiento son disjuntos. `oro.csv` es exactamente la partición de prueba.
4. **Umbral desplegado reproducido:** el cuantil 0,05 lineal de la validación completa da −0,5693969936322356, con diferencia 0,0.
5. **80 ventanas de 10.10.20.30 en validación**, separadas en `validacion-kali-80-excluidas.csv`. Se excluyen **solo** de la nueva calibración y no se etiquetan como ataque. Validación sin Kali: 65 553 ventanas.
6. **Alineación con 4.1:** las puntuaciones de prueba y ataque recalculadas son idénticas al export canónico (`scores-todos-candidatos-full.csv.gz`, SHA `6e98219f…`), con diferencia máxima 0,0 y las mismas claves. ROC-AUC 0,92473 y AP 0,18581 se recalculan iguales: no dependen del umbral.
7. **Comprobación previa reproducida exactamente**, sin ajustes (validación sin Kali):
   - α = 0,03 → umbral −0,5898535710336618; TP 54, FN 30, FP 1 723, TN 63 698.
   - α = 0,05 → umbral −0,5694578968203694; TP 54, FN 30, FP 2 955, TN 62 466.
8. **Identidades 0,03 frente a 0,05:** las 54 ventanas de ataque detectadas son **las mismas** (no solo el mismo número). Los 1 723 FP de 0,03 son un subconjunto de los 2 955 de 0,05: se eliminan 1 232. Ningún ataque cae entre los dos umbrales. Lo mismo ocurre con la validación original.

## Lo que hay que leer con cuidado

- **Excluir las 80 ventanas Kali apenas mueve el umbral:** la diferencia máxima es 9,1·10⁻⁵ para cualquier α. Las dos curvas de la figura se superponen.
- **La elección α = 0,03 es una selección posterior.** Se justifica viendo TP y FP en la evaluación, así que la prueba normal y los ataques dejan de ser una prueba independiente para esa elección. Mirando solo la validación, 0,03 no tiene ninguna ventaja sobre 0,05.
- **0,03 queda en el borde del tramo plano.** El ataque detectado con la puntuación más alta (−0,59086) está a solo 0,001 del umbral 0,03 (−0,58985). Con α = 0,025 ya se pierde un TP (53/84). Todo el tramo α ≈ 0,03–0,05 detecta los mismos 54 ataques, y con solo 84 ventanas de ataque esa meseta no es una estimación robusta.
- **La prueba normal incluye 74 ventanas de 10.10.20.30** (sin cambios, como se pidió). Su normalidad tiene la misma incertidumbre que la de las 80 de validación; conviene declararlo en 4.1.

## Recomendación

1. **Calibración principal: α = 0,05 sobre validación sin Kali** (umbral −0,5694578968; FPR 4,52 %, recall 64,29 %). Excluir las 80 ventanas se justifica *a priori*, porque su normalidad no está confirmada, sin mirar la evaluación. Es la única variación metodológicamente limpia.
2. **α = 0,03 como análisis de sensibilidad declarado como selección posterior**, no como configuración adoptada. Reduce los FP de 2 955 a 1 723 con los mismos 54 TP, pero está en el borde de la meseta y no se ha confirmado en tráfico independiente.
3. Si aun así se adopta 0,03 en el artículo, usar las variantes ya generadas (`TABLA6-variante-alfa0.03-sinKali.csv` y `TABLA7-fila-IF-variante-alfa0.03-sinKali.csv`), rotuladas como «selección posterior», conservando la fila desplegada.

## No confirmado

- Nada de esto se ha probado en tráfico independiente ni en vivo. El sistema desplegado sigue con −0,5693969936.
- Las métricas son del **IF solo**, por ventana. No aplican al híbrido (IF + heurísticos) ni a las campañas por episodio.
- Las demás configuraciones de la Tabla 7 no se recalibraron. Esta actualización no es una comparación entre algoritmos en condiciones idénticas.

## Datos necesarios para comprobar el nuevo umbral en operación

1. **Tráfico normal nuevo**, no usado en entrenamiento, validación ni prueba (por ejemplo, días posteriores al 24-oct con las exclusiones del perfil de egreso ya activas), puntuado con el mismo pipeline. Sirve para medir el FPR fuera de la muestra con −0,58985 frente a −0,56946.
2. **Una campaña de ataques nueva**, con episodios etiquetados (t0 por ataque) y familias con N ≥ 3. Sirve para medir el recall por ventana y por episodio sin selección posterior.
3. **Registros del motor en modo sombra con el umbral candidato** (puntuar sin actuar), para contar qué decisiones LIMIT/BLOCK habrían cambiado. Requiere una decisión de despliegue: no se hizo.
4. **Marcas t0–t5 por episodio** (detección, decisión, publicación, relay, aplicación), con el desfase entre relojes, para latencias y respuestas.
5. **Las ventanas sin paquetes recientes por separado.** En vivo no las puntúa el IF, así que el FPR offline no es el operativo.

## Correcciones concretas para el artículo (aplicar después; Word sin tocar)

- **§3.3.3:** declarar las tres exclusiones por separado: 2 778 por banda de guarda, 181 del entrenamiento (ráfaga Kali del 27-sep) y, si se adopta la recomendación 1, 80 de validación excluidas de la calibración. Añadir que la prueba normal conserva 74 ventanas de 10.10.20.30.
- **§3.3.5:** «el umbral se fija con α = 0,05 sobre las 65 553 ventanas de validación sin la entidad atacante» (si se adopta la recomendación 1). Dar el umbral −0,5694578968 y aclarar que el sistema desplegado usa −0,5693969936 (validación completa). La diferencia es 6,1·10⁻⁵ y no cambia ninguna detección (TP 54 en ambos); el FPR pasa de 2 961 a 2 955 FP.
- **§4.1, Tabla 6:**
  - Con la recomendación 1: FP 2 955, TN 62 466, FPR 4,52 %, precisión 1,79 % (54/3 009), F1 0,0349. TP y FN no cambian; ROC-AUC y AP tampoco.
  - Con 0,03 (selección posterior): FP 1 723, TN 63 698, FPR 2,63 %, precisión 3,04 % (54/1 777), F1 0,0580.
- **§4.1, Tabla 7:** cambiar solo la fila del IF limpio y conservar la fila desplegada identificada. Las otras ocho filas quedan como están, con la nota de que no se recalibraron.
- **§4.1, sensibilidad de α:** sustituir el párrafo por la tabla `SENSIBILIDAD-ALFA.md` (7 valores × 2 validaciones) y la figura `figura-sensibilidad-alfa`. Mencionar la meseta α ≈ 0,03–0,05 y el borde en 0,03.
- **Figura 4:** las curvas no cambian. Si se quieren mostrar los puntos operativos, usar `figura-roc-pr-puntos-operativos`.
- **Resumen y §5:** no citar el FPR de 0,03 como resultado del sistema. Si se cita, añadir «selección posterior, no desplegada».
