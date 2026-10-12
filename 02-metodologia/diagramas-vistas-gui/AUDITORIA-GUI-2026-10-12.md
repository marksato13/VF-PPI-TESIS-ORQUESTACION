# Auditoría del panel — 12-oct-2026

**Cómo se hizo.** Capturas de cada sección con el panel en modo demo (rama del sensor,
`473e758`) y lectura del código de refresco. No se revisó el panel en vivo con sesión
iniciada: lo marcado «verificar en vivo» depende de datos que la demo no trae.

**Pregunta de la auditoría.** ¿Puede un analista ver, en cada sección, qué está entrando
ahora, qué se está acumulando y qué se decidió, con gráficos que se lean solos?

## Cadencia de refresco hoy

| Qué | Cada cuánto |
|---|---|
| Salud, actividad, scores, bloqueos, decisiones, mapa | 5 s |
| Datos en vivo (tramas y eventos) | 1 s; confirmación del motor cada 10 s |
| Variables | 60 s |
| Aprendizaje | 5 min |
| Comparación con Suricata | una vez al cargar |

Ninguna sección dice cuándo se actualizó por última vez ni avisa si el dato está viejo.

## Hallazgos por sección

| Sección | Qué muestra | Qué le falta |
|---|---|---|
| Salud | Tarjetas de servicios (vacía en demo) | Ingesta en cifras: tramas/s, eventos/s, edad de la última decisión, filas acumuladas y su ritmo, edad del feed |
| Actividad | 5 contadores; barras por minuto en dos colores; IPs con más acciones | Eje y escala; barras apiladas por acción; valor al pasar el ratón; variación frente a la hora anterior |
| Scores | Histograma de ~12 barras con el umbral | Eje con valores; conteo por barra; comparación con la distribución del conjunto de oro; selector de tramo |
| Bloqueos | Tabla con cuenta atrás | Historial de lo que ya caducó; edad del feed del que sale |
| Decisiones | Tabla de las últimas 100 con mini-recta de score | Gráfico de score en el tiempo con el umbral; filtros por acción y detector; detalle por fila con las variables que dispararon; más de 100 filas |
| Variables | Catálogo de las 28 + 3, estático | Valor actual y tendencia por variable; marca cuando sale del rango del oro; contador del dataset que se acumula |
| Datos en vivo | Tramas y eventos al segundo, con trazabilidad | Ritmo en gráfico; reparto por protocolo (verificar en vivo) |
| Modelo | Tarjetas y texto fijo | Verificar en vivo que el aviso de «punto débil» y las cifras correspondan al Isolation Forest vigente (64,3 % de detección, nota S) |
| Suricata | Protocolo y tabla desde el fichero de datos | Nada urgente |
| Alcance | 3 contadores | Desglose (duplicados del espejo, PCAP ilegibles, por protocolo) y tendencia |
| Aprendizaje | Tarjetas y tres tablas | Gráfico de PSI y FPR por día con sus umbrales; cuenta atrás a la próxima corrida |
| Mapa del sistema | Siete vistas | Hecho el 12-oct |

## Plan por bloques

| Bloque | Qué | Por qué primero |
|---|---|---|
| G1 | Franja «Pulso»: tramas/s, eventos/s, edad de la última decisión, filas acumuladas, edad del feed; y «actualizado hace N s» por sección | Responde a «ver lo que entra y lo que se acumula» en una mirada |
| G2 | Actividad: barras apiladas por acción, con eje, escala y detalle al pasar el ratón | Es lo primero que mira un analista |
| G3 | Decisiones: score en el tiempo con el umbral, filtros y detalle por fila | Explica cada decisión |
| G4 | Variables con valor actual, tendencia y rango del oro | Convierte el catálogo en un monitor |
| G5 | Scores: histograma con eje, conteos y referencia del oro | |
| G6 | Aprendizaje: PSI y FPR por día | |
| G7 | Modelo y Alcance: textos y desgloses, tras verificar en vivo | |
