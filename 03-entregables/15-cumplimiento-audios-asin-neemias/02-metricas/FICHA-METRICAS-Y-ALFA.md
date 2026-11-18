# Ficha de consulta y defensa: métricas, población y α

**Corte documental:** 31-oct-2026. Repositorio documental examinado en HEAD `1e378d2c1917adb1c530b83f82c1d693c310b4ac`. N-01 y N-02 tienen contraste técnico preparado; la consulta y la aceptación del método siguen pendientes. Las preguntas del audio no constituyen aprobación de balanceo, reentrenamiento ni cambio de α.

## 1. Explicación oral breve

> Evaluamos ventanas de 10 segundos por entidad, no 84 ataques independientes. En la evaluación de referencia hay 65 421 ventanas etiquetadas como normales y 84 como ataque. Precisión pregunta cuántas de las alertas fueron verdaderas; recall pregunta cuántas de las 84 ventanas de ataque detectamos; FPR pregunta qué fracción de las ventanas normales generó una falsa alarma. Por eso 54 de 84 es recall de 64,29 %, no precisión. En la recalibración analítica α=0,03, esas 54 detecciones conviven con 1 723 falsas alarmas: la precisión es 54 de 1 777, es decir 3,04 %. La baja prevalencia hace que falsas alarmas relativamente poco frecuentes dominen el conjunto de alertas. Debemos mostrar ambas medidas y su población, sin cambiar los datos para elevar porcentajes.
>
> Aquí α selecciona un cuantil de los scores de validación. No es el nivel de significancia de una prueba de hipótesis. El sistema documentado conserva α=0,05 sobre 65 633 ventanas; la comparación offline usa 65 553, excluyendo 80 ventanas de normalidad no confirmada. α=0,03 se seleccionó después de observar la evaluación: es sensibilidad exploratoria, no un óptimo demostrado. Consultar cómo presentar estos resultados es distinto de autorizar cambiar el modelo.

## 2. Definiciones y denominadores

Clase positiva = ventana etiquetada como ataque. TP = positiva alertada; FN = positiva no alertada; FP = normal alertada; TN = normal no alertada. Se habla de señales de detección, no necesariamente de bloqueos aplicados.

| Medida | Fórmula | Qué contiene el denominador | Pregunta que responde |
|---|---|---|---|
| Precisión (valor predictivo positivo) | TP/(TP+FP) | Todas las ventanas predichas positivas | De las alertas, ¿qué proporción corresponde a ataque? |
| Recall (sensibilidad) | TP/(TP+FN) | Todas las ventanas etiquetadas como ataque, aquí 84 | De lo que había que detectar, ¿cuánto detectamos? |
| FPR | FP/(FP+TN) | Todas las ventanas etiquetadas como normales, aquí 65 421 | Del tráfico normal evaluado, ¿qué proporción alertamos por error? |
| F1 | 2TP/(2TP+FP+FN) | Combinación de detecciones, falsas alarmas y omisiones | Media armónica de precisión y recall |

**Unidades:** en las tablas de esta ficha, precisión, recall, FPR y prevalencia se expresan todos en **%**. Un 0,0810 en escala 0–1 equivale a 8,10 %, no a 0,0810 %. F1, ROC-AUC y AP se citan expresamente en escala **0–1**. Los conteos son ventanas; los tiempos son segundos. No comparar porcentajes con razones sin convertir.

La expresión oral «en función de los 84» es resoluble manteniendo el nombre correcto: **TP/84 es recall**. No autoriza sustituir la precisión por recall, rebalancear el test, quitar normales ni reetiquetar ventanas. El denominador de precisión tampoco es el total de normales ni el total de evaluación. Si un denominador fuese cero, la métrica sería no definida, no automáticamente cero; esto importa para los episodios no evaluables de la campaña A.

### Desbalance: explicación técnica

Prevalencia observada = 84/65 505 = **0,128234 %**. Para una población y umbral fijos, precisión = recall·p / [recall·p + FPR·(1−p)]. Por eso una FPR de unos pocos puntos porcentuales sobre 65 421 normales puede producir miles de FP frente a decenas de TP. El desbalance ayuda a explicar el resultado, pero no prueba que el modelo sea adecuado ni que todo el problema se reduzca al desbalance.

El IF es un detector de anomalías ajustado sobre ventanas nominalmente normales; no procede inferir de una precisión baja que se entrenó un clasificador supervisado con esos mismos 84 ataques o que «solo aprendió no ataques». Esas 84 ventanas se usan para evaluación. Una revisión de etiquetas, trazabilidad o población no equivale a decidir reentrenamiento. Un eventual experimento de balanceo tendría que justificarse para el objetivo y conjunto pertinentes, acordarse por separado y mantener una evaluación representativa, trazable y no usada para seleccionar el método. **No se ha aprobado ni ejecutado aquí.**

## 3. Poblaciones y versiones: no reconciliar mezclándolas

| Uso | Población / versión | Lectura correcta |
|---|---|---|
| Partición train declarada | 204 148 ventanas | No es el tamaño efectivo del ajuste limpio |
| Ajuste efectivo del IF limpio y comparación | 203 967 = 204 148 − 181 no elegibles | Exclusión por bandera `eligible_training`; no por eliminar toda una IP |
| Calibración operativa original | 65 633 ventanas | Incluye 80 de Kali, 17 con actividad observable, sin confirmación independiente de normalidad/ataque |
| Calibración analítica sin Kali | 65 553 = 65 633 − 80 | Solo cambia la población de calibración; no convierte las excluidas en ataques |
| Evaluación de 4.1 y matrices por ventana de 4.2 | 65 421 normales + 84 ataques = 65 505 | Conserva 74 normales de Kali de normalidad no confirmada y 45 558 normales sin paquetes en 10 s |
| Replay de 4.2 | 9 episodios del 5-oct, tres familias | Otra campaña y otra unidad; no se suma a las 84 ventanas |
| Campaña A del 29-oct | 25 episodios ejecutados; 0 evaluables | No proporciona un recall de ataque válido ni valida el α candidato |

Fuentes S03–S08, S10. La disjunción de claves entre entrenamiento, validación y evaluación está documentada; **no equivale a una prueba ciega**, porque se reutilizó la evaluación durante el desarrollo. La ausencia de solape no elimina la selección posterior ni la dependencia temporal entre ventanas.

### Matrices del mismo IF limpio: calibración original frente a derivadas

| Estado y población de calibración | α | Umbral `score_samples` (alerta si score < umbral) | TP | FP | TN | FN | Precisión % | Recall % | FPR % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Operativo documentado, 65 633 | 0,05 | −0,5693969936322356 | 54 | 2 961 | 62 460 | 30 | 1,791045 | 64,285714 | 4,526070 |
| Analítico sin Kali, 65 553 | 0,05 | −0,5694578968203694 | 54 | 2 955 | 62 466 | 30 | 1,794616 | 64,285714 | 4,516898 |
| Analítico sin Kali, selección posterior | 0,03 | −0,5898535710336618 | 54 | 1 723 | 63 698 | 30 | 3,038829 | 64,285714 | 2,633711 |
| Analítico sin Kali, complemento exploratorio | 0,01 | −0,6223889502095352 | 50 | 567 | 64 854 | 34 | 8,103728 | 59,523810 | 0,866694 |

S03–S07. Los umbrales de referencia anteriores proceden de calibración. La reproducción de Tabla 7 registra −0,5694578968203693 y −0,5898535710336615; Tabla 7c registra −0,6223889502095351. Las diferencias del orden de 10⁻¹⁶ proceden de la orientación/aritmética del cuantil y no cambian las matrices publicadas. **No** confundir esa diferencia numérica con la diferencia real de población 65 633 frente a 65 553.

Aunque ambos α=0,05 redondeen a precisión 1,79 %, sus FP difieren en seis y su FPR redondeada es 4,53 % frente a 4,52 %. No tomar TP de una fila y FP o umbral de otra. Pasar de 0,05 a 0,03 en la calibración sin Kali elimina 1 232 FP y conserva las mismas 54 detecciones en esta evaluación; pasar de 0,03 a 0,01 elimina 1 156 FP y pierde cuatro TP. Esto es un compromiso observado, no garantía futura.

## 4. Qué es α y qué elección se puede defender

Sea s = `score_samples`, donde valores menores son más anómalos. Se calcula τ = cuantil lineal α de s en validación y se alerta si s < τ. En la escala común a = −s, mayor = más anómalo, el umbral es cuantil lineal 1−α de a y se alerta si a > umbral. Para PCA, a es el error de reconstrucción. Cada método tiene **su propio umbral**, con el mismo procedimiento de calibración.

α regula aproximadamente la cola alertada de la validación nominalmente normal. Por tamaño finito/interpolación y empates, la fracción puede no ser exactamente α; en Tabla 7 no hay empates y las FPR de validación son 3,000625 % y 5,000534 %. **No garantiza esa FPR en prueba ni en operación**, ni es la probabilidad de que una alerta sea falsa. Una prueba de significancia requeriría hipótesis nula, estadístico y distribución/p-valor; este procedimiento no los usa. Tampoco α=0,05 implica un intervalo de confianza del 95 % para estas métricas.

**Elección original documentada:** α=0,05 con validación completa reproduce exactamente el umbral desplegado. La reproducción verifica el procedimiento y su valor, no demuestra una optimización ni una razón de coste operativa previa. No se inventa esa justificación.

**Después de observar resultados:** la nota del 24-oct identifica expresamente α=0,03 como selección posterior, al examinar TP/FP. La nota propone 0,05 sin Kali como calibración analítica principal y 0,03 como sensibilidad; es una **recomendación documental, no aprobación del asesor ni despliegue**. La comparación del 25-oct registra configuraciones antes de su ajuste, pero eso no borra el origen posterior de la selección de 0,03. El complemento 0,01 tampoco es una elección prospectiva demostrada ni una aprobación del audio.

El borde del tramo 0,03–0,05 es frágil: con 0,025 hay 53 TP, según sensibilidad publicada; no se puede llamar a 0,03 «más estable». La campaña A posterior no proporciona población de ataque evaluable para confirmar el compromiso. Sigue humana la elección de qué configuración presentar como principal, qué coste de FP/FN aceptar y qué protocolo futuro autorizar.

## 5. Comparación canónica de métodos: alcance y límites

Tabla 7, α=0,03, validación 65 553 y evaluación común 65 505 (S03–S05):

| Método | TP | FP | Precisión % | Recall % | FPR % |
|---|---:|---:|---:|---:|---:|
| IF | 54 | 1 723 | 3,04 | 64,29 | 2,63 |
| OCSVM | 59 | 1 958 | 2,93 | 70,24 | 2,99 |
| LOF | 77 | 2 314 | 3,22 | 91,67 | 3,54 |
| Elliptic Envelope | 44 | 1 785 | 2,41 | 52,38 | 2,73 |
| PCA | 71 | 2 116 | 3,25 | 84,52 | 3,23 |

El IF presenta menor FPR en esta tabla, pero otros métodos detectan más ventanas y PCA tiene mejor precisión y F1 en este corte. No hay ganador universal ni evidencia aquí de que IF sea mejor o más estable. IF: ROC-AUC=0,924727 y AP=0,185807 (0–1); son métricas de scores continuos y no cambian por variar α sobre los mismos scores/etiquetas. ROC-AUC y AP ordenan aspectos distintos; AP no es la precisión de una fila. No atribuir sus valores al híbrido binario.

**Tiempo:** el CSV registra inferencia IF=3,1486032 s y PCA=0,0412727 s para 131 058 ventanas (validación + prueba + ataques), en laptop, con cargas/hilos del ensayo. IF **no es más rápido que PCA en esa medición**. No son latencias extremo a extremo ni tiempos del sensor; IF no se ajustó de nuevo en esa comparación. La nota recoge corridas y rangos, sin un benchmark estadístico controlado.

**Límites:** una configuración por método, evaluación reutilizada y 84 ventanas de ataque, sin intervalos ni prueba pareada calculados aquí. No asumir 84 episodios independientes ni atribuir significancia a diferencias de pocos TP. EE tiene desviación D1 (`support_fraction=0,75`) y covarianza mal condicionada; no presentar la configuración fallida por defecto como la que produjo la tabla. El OCSVM comparable es el entrenado con los mismos datos del sensor, no el candidato histórico de laboratorio. Tabla 7 supera la comparación histórica de siete candidatos.

## 6. Componentes, atribución y regla operativa reciente

S08–S09 separan tres resultados:

1. **Antecedente histórico:** IF contaminado 6/9, heurísticos antiguos 7/9, combinado 9/9. No es el IF limpio actual.
2. **Replay de nueve episodios con IF limpio:** IF 6/9, heurísticos 9/9, híbrido 9/9. Regla de atribución histórica: entidad fuente e intervalo [T0, último paquete + 60 s]. Heurísticos ajustados a la vista de esos mismos episodios. No demuestra ganancia del híbrido sobre heurísticos por cantidad de episodios.
3. **Matrices por ventana de la población de 4.1:** IF 0,03 = 54 TP/1 723 FP; heurísticos = 47/472; híbrido 0,03 = 54/2 192. Ambos aciertan 47, solo IF siete, solo heurísticos cero, ninguno treinta. El híbrido añade 469 FP sin nuevos TP. No sumar este reparto al de los episodios.

El control de figura comprueba la historia y explicita sensibilidades: si se exige señal dentro de T0–fin, los totales del replay pasan a IF 4/9, heurísticos 7/9 e híbrido 7/9. Con historia observada y elegibilidad real son IF 3/9 y heurísticos/híbrido 7/9; son sensibilidades distintas, no cifras intercambiables. El replay principal adelantó `capture_start` para elegibilidad: no recupera paquetes ausentes. El acumulador repuntuado es otra sensibilidad, no otro ensayo vivo.

**Regla reciente que impide extrapolar:** la campaña A exige señal DURANTE, atribución confirmada, cobertura/integridad suficiente y continuidad del motor; las tardías se informan aparte. El 9/9 de una ventana temporal que admitía +60 s no acredita 9/9 bajo esa regla. Además, el motor no puntúa IF si `packet_count_10s=0`, mientras Tabla 7 conserva esas ventanas puntuadas offline. Su FPR no es directamente la FPR operativa, y una señal sobre `NUNCA_BLOQUEAR` no equivale a bloqueo.

### Evidencia posterior que supera pendientes antiguos

S10 registra campaña A completada el 29-oct: **25 ejecutados, 0 evaluables**, por cobertura/continuidad (huecos hasta 43 s, tolerancia 20 s). `n/a` no significa cero detecciones ni 25 FN. El control cuenta 2 526 ventanas registradas con cobertura completa: IF 0,05 = 355/2 526 = 14,05 %; IF 0,03 = 231/2 526 = 9,14 %; IF 0,01 = 85/2 526 = 3,37 % (redondeo). No hay inventario independiente de ventanas esperadas; las que no escribió el motor no son TN. No combinar ese control con las 65 421 normales ni usarlo por sí solo para elegir α. No hubo evidencia comparativa válida de ataque ni respuesta activa en esa campaña en sombra.

S11 actualiza la investigación: `build_rows` por entidad se validó con igualdad exacta en **773/773 ciclos, 290 470 filas**. La variante de ventanas pendientes también logra **773/773 con filas idénticas y cobertura completa**. La regla correcta usa la **primera ancla no puntuada**, no «última decidida +10 s», que fue descartada por omitir ventanas nacidas por detrás. Esto es validación offline de equivalencia, no prueba de despliegue ni nueva campaña. Los tiempos estimados aún superan 9,5 s en 19/26 ciclos de inundación (máximo 20,3 s) y 13 pausas; se requiere medición en vivo para cualquier afirmación operativa. La causa analizada posteriormente actualiza el «no determinada» del informe inicial, sin cambiar su 0/25 evaluables.

No se usa `PENDIENTES.md` como prueba de inexistencia de campaña o de validación. Las decisiones de corrección, continuidad para un protocolo futuro y eventual nueva ejecución siguen pendientes; ninguna optimización recupera retroactivamente la evaluabilidad de la campaña A.

## 7. Audio: lo dicho, lo verificable y lo incierto

Se leyó íntegro S01 y el TXT S02 en 00:00–05:10 y 12:45–14:10. No se hizo nueva escucha ni corrección certificada de ASR.

| Referencia | Lectura del audio/análisis | Contraste y tratamiento |
|---|---|---|
| N1 00:00:00–00:00:07; N2 00:00:09–00:00:27 | Objeción a «1.79» y confusión con «8 %» | 1,79 % es compatible con dos matrices distintas; 8,10 % con IF 0,01. La grabación no identifica la fila mostrada: no adjudicarla por coincidencia numérica |
| N2 00:00:33–00:00:45 | Medium reconoce 55 421, versión anterior 65 421 | La prueba normal canónica tiene 65 421. La cifra ASR discrepante no crea otra población |
| N1 00:00:20 según S01 | Medium reconoce 65 553 y «ventanas de dinero» | 65 553 existe como validación sin Kali; no identifica con certeza el contexto oral ni sustituye el tamaño de test |
| N2 00:01:43–00:02:41 | Consulta y «en función» de los 84 | N-01: preparar denominadores/población; consulta al asesor pendiente, «Ferdinand» por confirmar |
| N2 00:03:54–00:04:34 | Posibilidades de balanceo y reentrenamiento | Preguntas/propuestas, sin método aprobado ni orden ejecutable |
| N2 00:12:51–00:13:20 | Se relaciona α con significancia/error y elegir el adecuado | N-02: explicar cuantil, confirmar criterio humano; no adoptar esa equivalencia estadística |
| N2 00:13:48–00:14:02 | Lectura de 54 con 0,03 y 50 con 0,01; también mención a 0,05 | Conteos compatibles con las tablas; su verificación viene de S03, S06, S07, no de tratar el audio como nueva medición |

## 8. Comprobación mínima efectuada

Se ejecutó el script local de solo lectura:

`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\15-cumplimiento-audios-asin-neemias\02-metricas\verificar_aritmetica.py`

Resultado: **10/10** matrices Tabla 7 con TP+FN=84, FP+TN=65 421, total=65 505; coincidencia CSV/JSON en conteos y cuatro métricas con tolerancia absoluta 10⁻¹². **5/5** matrices Tabla 7c con porcentajes concordantes a dos decimales y F1 a cuatro. Verificadas también las identidades aritméticas de las cuatro filas IF de esta ficha; la fila operativa usa los conteos documentados en S06, no una nueva inferencia.

Los hashes de Tabla 7, resultados JSON y configuración coinciden con el manifiesto **en sus bytes locales LF**:

- Tabla 7: `1232d87d7c5184ce60f20837fe176f89e02ac004da254da8660d46d539fe1b16`.
- JSON: `be5ff4c6fc58308f4496f45bbe93b67ba356ba5c96eb08d3ccefedc63a610a84`.
- Configuración: `d4291b951b0c26378e4bd58a6ff105211289c9d45104a0431bf5ab705ce2044f`.

La verificación previa de S09 informa **15 textos** cuyo manifiesto fuente usa CRLF y cuya publicación Git usa LF; reconstruir CRLF reprodujo sus hashes. Aquí se cita esa comprobación, no se repite ni se presenta como corrupción de datos o cambio de resultados. Se distingue ese caso de los tres hashes LF comprobados ahora. No se reprodujeron PCAP, scores, cuantiles, intervalos ni campañas en este frente.

## 9. Fuentes absolutas y commits

Los commits son de procedencia; HEAD de consulta es el indicado al inicio. Los audios externos no tienen commit documental acreditado. Cada identificador S remite a la ruta completa siguiente.

- **S01, análisis completo:** `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\ANALISIS-NEEMIAS-MEDIUM.md`.
- **S02, TXT largo medium:** `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\WhatsApp Ptt 2026-10-28 at 3.59.06 PM.txt`.
- **S03, Tabla 7:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\TABLA7-comparacion-completa.csv`. Último commit de la tabla: `028de214fb2ddc809f6eb4876574ada647b3dafb`.
- **S04, resultados y configuración (mismo paquete de comparación):** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\resultados-comparacion.json`; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\config-comparacion.json`.
- **S05, protocolo y manifiesto 4.1:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\NOTA-COMPARACION.md`; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\MANIFIESTO-COMPARACION.json`.
- **S06, calibración y sensibilidad:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\calibracion-alfa-2026-10-24\NOTA-CALIBRACION-ALFA.md` (último commit `88692aee601a6e99655e14b608b5fa719f32790e`); `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\calibracion-alfa-2026-10-24\SENSIBILIDAD-ALFA.md`.
- **S07, complemento α=0,01:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\TABLA7c-alfa0.01.csv`; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\MANIFIESTO-TABLA7C.json`. Último commit de la tabla: `ca03812df66a421703b7ef09ffdb387e8db8e138`.
- **S08, historia y aporte de componentes:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\NOTA-APORTE-COMPONENTES.md`. Último commit `03055893722a941449624fef19036fd08929a51f`.
- **S09, atribución y hashes CRLF/LF:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\figura-opencode\control.md`; `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\figura-opencode\control.json`. Último commit del control Markdown `efc01a7956d347c09e2b030e1ef3a3e525025da4`, que verifica el commit fuente `03055893722a941449624fef19036fd08929a51f`.
- **S10, campaña A ejecutada:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\INFORME-CAMPANA-A-2026-10-29.md`. Último commit `e06805af03282b447cee620b84c240bd4c2fb493`.
- **S11, investigación y equivalencia:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\investigacion-ciclos-motor\INVESTIGACION-CICLOS-MOTOR.md`. Validación por entidad `a99a61528849ae22bd5343f3df0047bda4439c58`; solo pendientes `9a5577ad93217b85d48218552b6cbbe34852b594`; manifiesto actualizado en HEAD `1e378d2c1917adb1c530b83f82c1d693c310b4ac` mediante `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\MANIFIESTO-EJECUCION.sha256`.
- **S12, regla preregistrada de campaña:** `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\config-campana.json`. Último commit `719bf3ab3308496e903b4b419d99ad6a03707c99`; exige detección durante, atribución confirmada y cobertura.

## 10. Cierre propuesto, todavía no acordado

**N-01:** llevar denominadores, matrices, límites de población y propuesta de presentación al asesor; guardar su respuesta identificable y método aceptado. La revisión técnica está preparada; falta la consulta, no una manipulación de cifras.

**N-02:** confirmar qué calibración y α se presentarán como principales, con motivo y carácter original/posterior expresos; registrar respuesta y cualquier autorización de un experimento futuro por separado. Esta ficha no cambia el umbral operativo ni acredita una aprobación.
