# Mapa verificable de fases y especificación de conectores — N-03

**Corte:** 31-oct-2026. **Estado:** insumo técnico preparado; no son figuras corregidas ni metodología ya incorporada al manuscrito. Se revisaron fuentes locales, código, configuración, rótulos XML y diagramas Mermaid; no se renderizaron ni se comprobó su legibilidad visual. No se contactaron hosts.

## 1. Identidad de las fuentes y criterio de vigencia

- Repositorio documental: HEAD verificado `1e378d2c1917adb1c530b83f82c1d693c310b4ac`. Antes de esta tarea tenía la auditoría GUI/TAM sin seguimiento; se consultó como material ajeno de solo lectura.
- Producto: rama `main`, HEAD verificado `7b275b8bab1c8343e55f40a103ee980dc497620b`. Hay una modificación local preexistente en `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\dashboard.py`; no se usa para certificar una versión desplegada.
- Código local ≠ versión activa remota. La campaña del 29-oct documenta hashes y proceso con motor `7b275b8`; esa evidencia permite describir aquel corte, no el estado remoto del 31-oct.
- La configuración local referencia un manifiesto y un joblib limpios que **no están presentes en la ruta local referenciada**. Su ausencia no prueba que falten en Sensor1: la identidad desplegada se sustenta en la evidencia archivada de campaña.

### Fuentes de audio (rutas completas)

| Clave | Fuente y localización | Instrucción verificable |
|---|---|---|
| A0 | `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\ANALISIS-NEEMIAS-MEDIUM.md`, líneas 58–70, 93, 103–106 | N-03: fases separadas y continuidad; N-06: explicar CyberFlow. |
| A1 | `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\WhatsApp Ptt 2026-10-28 at 3.59.06 PM.txt`, líneas 185–290, 325–382 | N2 05:10–11:48: fases, evitar documentos repetidos, círculos 1/2 y explicación de salidas como entradas. |
| A2 | `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\verificacion\neemias-medium-1140-1240.txt`, líneas 4–13 | N2-C 00:00–00:17 + **700 s** = N2 11:40–11:57; parámetros en texto; 10/30/60 **segundos**, no centisegundos. |
| A3 | `C:\Users\markp\Downloads\audios\investigacion\neemias\resultado-whisper-medium\WhatsApp Ptt 2026-10-28 at 3.59.06 PM.txt`, líneas 535–559 | N2 19:45–20:40: nombre de producto/propuesta; explicar en metodología en qué consiste. |

**Límite:** el audio no muestra la lámina ni identifica con certeza los documentos «1» y «2». La expresión ASR «pick-up» no demuestra que el documento 1 sea PCAP. Los dos identificadores orales quedan como **AUDIO-1 = no identificado** y **AUDIO-2 = no identificado**. No se les asigna equivalencia técnica sin cotejar la lámina mostrada.

### Catálogo técnico (las claves T se resuelven siempre a estas rutas y líneas)

| Clave | Ruta absoluta y líneas | Uso |
|---|---|---|
| T1 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\configs\cyberflow.local.toml`, 16–37, 39–83, 95–102, 118–128 | Perfil local: captura, alcance, IF limpio, rutas, mantenimiento supervisado. |
| T2 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\configs\features\multilayer-v2.json`, 2–35 | Unidad IP iniciadora/fin causal, paso 10 s y 28 variables con ventanas 10/30/60 s. |
| T3 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\motor_decision.py`, 503–579, 614–688, 705–732 | Alcance/dedup, extracción, guarda de PCAP completos, score, señales, registro y no evaluadas. |
| T4 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\heuristicos.py`, 2–21, 28–78, 92–165 | Cuatro reglas, umbrales razonados, acción y prioridad. |
| T5 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\engine\publicar_feed.py`, 42–105, 125–174 | Señales → política de respuesta por IP; exclusiones; escalada, serialización y firma. |
| T6 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\scripts\enforce\agente_enforce.py`, 49–51, 81–129, 172–221 | Verifica firma, plan nftables y aplicación opcional; dry-run no es aplicación. |
| T7 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\docs\APRENDIZAJE.md`, 3–5, 80–106, 123–132 | Candidatos, evaluación y promoción humana; límites del aprendizaje. |
| T8 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-main\docs\FICHA-TECNICA-DESPLIEGUE-VIGENTE.md`, 32–41, 90–100, 146–159, 186–204 | Arquitectura SPAN distribuida; contrato y límites históricos. El detector y timers de esta ficha antigua no fijan el corte actual. |
| T9 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.1-modelos\comparacion-metodos-2026-10-25\NOTA-COMPARACION.md`, 3–23, 29–47, 61–95 | Cinco detectores offline, particiones reales, umbral desplegado distinto y límites de comparación. |
| T10 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\INFORME-CAMPANA-A-2026-10-29.md`, 3–9, 29–35, 69–87, 124–135, 222–249 | Campaña A realizada, 0/25 evaluables, IF limpio y agente remoto desactivado; no prueba de enforcement en esa campaña. |
| T11 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\ejecucion-2026-10-29\investigacion-ciclos-motor\INVESTIGACION-CICLOS-MOTOR.md`, 162–241 | Variante por entidad/pendientes: equivalencia 773/773, estimaciones offline y no desplegadas; inundación aún problemática. |
| T12 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\NOTA-APORTE-COMPONENTES.md`, 7–9, 27–37, 62–100 | Resultado antiguo pertenece a modelo anterior; recálculo no equivale a ensayo nuevo. |
| T13 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\PENDIENTES.md`, 3–20, 24–41, 45–65 | Corte atrasado; interna realizada, BLOCK con antecedente, campañas finales y validación externa abiertas. |
| T14 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\14-auditoria-gui-tam\01-hallazgos-agentes\HALLAZGOS-A-UTILIDAD.md`, 3, 17–35, 54–58 | Auditoría estática ajena: distinguir decisión/publicación/aplicación; no certifica GUI remota ni percepción TAM. |

## 2. Inventario y conciliación de numeraciones existentes

Hay **tres clasificaciones documentales**. No deben mezclarse ni renumerarse silenciosamente:

1. **Siete fases de tesis F1–F7**, elegidas aquí como índice de láminas por ser la estructura metodológica ya escrita.
2. **F00–F09 de ejecución del proyecto**, donde F07 es dashboard y no validación.
3. **Estándar de 8 fases más extensiones** del análisis de artículos semilla: referencia de literatura, no un segundo pipeline del producto.

La advertencia explícita de correspondencias del proyecto está en `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\fases\PROCEDIMIENTO.md`, líneas 14–31. El estándar y sus extensiones están en `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\FASES-METODOLOGIA-TESIS.md`, líneas 27–71. Ambos contienen estados/cifras históricos que deben contrastarse con T9–T13.

### Fases de tesis encontradas: entradas, salidas y evidencia

Los identificadores **CF-Axx** y **CF-Cxx** de las secciones siguientes son propuestas editoriales nuevas. No son nombres presentes en el audio ni archivos nuevos del producto.

| Fase real documentada | Entrada verificable / función | Salida y consumo propuestos | Estado y evidencia de contraste |
|---|---|---|---|
| F1 Datos y línea base | Tráfico copiado por SPAN, perfil de captura y alcance; adquisición de PCAP y EVE | CF-A01 PCAP, CF-A02 EVE → F2; CF-A03 inventario/hashes → F4/F6 | Adquisición documentada, no captura inline. La fila CSV pertenece lógicamente a F2 aunque el F1 antiguo también la dibuja. T1, T8, T10. |
| F2 Preprocesamiento y features | CF-A01 + CF-A02 y contrato v2; filtrado, dedup, atribución por IP, agrupación temporal | CF-A04 filas de variables → F3/F4; contrato CF-A05 como referencia externa | Implementado; separación entre dedup de paquetes y duplicados de vectores. No imputar ni balancear en la figura sin evidencia. T2–T3, T9:19–22. |
| F3 Modelado híbrido | CF-A04 para construcción/evaluación offline; en operación, vector + modelo/manifiesto congelado y reglas | CF-A06 paquete de modelo/calibración → F6/F4 y puntuador; CF-A07 registro de detección → F5/F4/F6 | Diferenciar entrenamiento del IF, inferencia, reglas aditivas y política de respuesta. El IF limpio sustituye a la identidad antigua; T1, T3–T5, T9. |
| F4 Experimento y evaluación | CF-A01/02/03/04, CF-A06/07, protocolo, episodios y configuración baseline | CF-A08 informe/métricas/elegibilidad → F7 y lectura operativa F6 | Existe replay y campaña A realizada, pero A tiene 0/25 episodios evaluables. No dibujar éxito comparativo. T9–T12. |
| F5 Respuesta/enforcement | CF-A07, lista protegida, estado de escalada, clave de firma | CF-A09 feed+firma → relay/agente; CF-A10 evidencia de aplicación/reversión → F4/F6/F7, solo cuando exista | Implementación distribuida existente. En A el agente estaba parado; feed o acción inferida no son CF-A10 confirmado. T5–T6, T10:222–239. |
| F6 Despliegue/operación | CF-A06, perfil y unidades; observación de CF-A03/07/09/10 | CF-A11 evidencia de despliegue/estado, panel y registros → F7/F4; habilita F1/F3/F5 | Habilitador transversal, no transformación de un informe F4 en paquetes de red. Config local real y evidencia archivada; no estado remoto actualizado. T1, T8, T10. |
| F7 Validación | CF-A08 + CF-A11 y CF-A10 cuando corresponda; guion/instrumento y participantes | CF-A12 acta/respuestas/observaciones → revisión humana documentada | Interna registrada el 15-oct; externa aún requiere respuestas reales y demostración coherente. No representar TAM calculado por tener una plantilla. T13:11,36; T14. |

Fuentes originales de estas siete fases (también son los **siete diagramas Mermaid reutilizables**, uno por archivo):

| Fase | Ruta absoluta | Líneas del diagrama / interfaz |
|---|---|---|
| F1 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F1-datos-y-linea-base.md` | 11–45 / 91–95 |
| F2 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F2-preprocesamiento-y-features.md` | 11–34 / 89–93 |
| F3 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F3-modelado-hibrido.md` | 12–31 / 128–132 |
| F4 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F4-experimento-y-evaluacion.md` | 11–25 / 68–73 |
| F5 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F5-respuesta-enforcement.md` | 12–42 / 81–86 |
| F6 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F6-despliegue-y-operacion.md` | 10–34 / 72–76 |
| F7 | `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\metodologia-7-fases\F7-validacion.md` | 11–31 / 69–74 |

## 3. Registro de artefactos propuesto y contrato salida → entrada

**No se crean los artefactos CF-Axx en esta tarea.** Son identidades editoriales para reconocer la misma salida en varias láminas. Una entidad lógica puede materializarse en CSV offline o en filas en memoria; no se dibujará un CSV persistido en el camino en vivo si no existe.

| ID propuesto | Artefacto y tipo | Productor → consumidor / conector propuesto | Contrato mínimo / evidencia |
|---|---|---|---|
| CF-A01 | Captura cruda PCAP | F1 → F2 **CF-C01**; F1 → F4 **CF-C01** por referencia | Periodo UTC, captura/host, archivos y hashes; en A PCAP voluminosos permanecen remotos, con manifiesto local. T1:16–37; T10:181–195,251–270. |
| CF-A02 | Eventos de aplicación EVE JSON | F1/Suricata → F2 **CF-C02**; copia de evaluación → F4 **CF-C02** | Eventos HTTP/DNS/TLS con tiempo; distinguir EVE de producción del EVE baseline del replay. T2:19–35; T3:536–539. |
| CF-A03 | Inventario/manifiesto y alcance | F1/registro experimental → F4/F6 **CF-C03** | Fuentes, hashes, exclusiones, cobertura, relojes; no es detector. T10:29–35,181–195,251–263. |
| CF-A04 | Filas/vectores por IP y fin de ventana | F2 → F3 y F4 **CF-C04** | Clave entidad/tiempo, 28 columnas en orden, conteos auxiliares, elegibilidad e historia; modo offline conserva campaña/partición. T2–T3, T9:18–23. |
| CF-A05 | Esquema/diccionario de variables | Referencia versionada → F2/F3/F4 **CF-C05** | Contrato compartido, no documento regenerado por cada ventana; v2 tiene 28 variables. T2. |
| CF-A06 | Modelo + manifiesto/calibración | Construcción F3 → despliegue F6, puntuador F3 y evaluación F4 **CF-C06** | ID, hash, escalador/orden, función de score, umbral y población de calibración. Ruta configurada no sustituye artefacto inspeccionado. T1:69–102; T9:19–47; T10:29–35. |
| CF-A07 | Registro JSONL de detecciones/decisiones | Inferencia F3 → F5/F4/panel F6 **CF-C07** | `entity_ip`, `window_end_utc`, `logged_at`, score/threshold, `decision`, `detector_name`, `heuristico`, marcas de fuentes. `ventana_no_evaluada` se conserva aparte, no como PERMIT. T3:660–732. |
| CF-A08 | Métricas e informe con elegibilidad | F4 → F7 y diagnóstico F6 **CF-C08** | Unidad/población, descartes, cobertura, versión; admite n/a, no inventar tasas sin evaluables. T10:69–87. |
| CF-A09 | Feed serializado + firma | F5 publicador → bastión → agente **CF-C09** | IP/acción/hasta/nivel/motivo, versión de reglas y firma; no cambiar identidad al pasar por relay. T5:92–105,165–174; T8:37–41. |
| CF-A10 | Evidencia de aplicación y retirada | Agente/host + comprobación → F4/F6/F7 **CF-C10** | Host, hora, resultado sin errores y estado nftables correlacionado a entrada de feed. No es un acuse integrado que se presuma disponible en GUI. T6; T14:30–35,54–58. |
| CF-A11 | Estado/versiones del despliegue y evidencia de operación | F6 → F4/F7 **CF-C11**; habilita F1/F3/F5 | Config/unidades/hash/proceso/fecha y modo sombra o activo; servicios activos no prueban continuidad. T10:29–35,222–239. |
| CF-A12 | Acta/respuestas/observaciones de validación | F7 → revisión humana **CF-C12** | Instrumento y versión demostrada, respuesta real, evidencia; no flecha automática de vuelta al entrenamiento. T13:11,35–36; T7:80–106. |

### Reglas para implementar los círculos sin duplicar documentos

1. Dibujar cada documento completo **una vez**, al producirlo; la entrada siguiente es un círculo con ID y leyenda que remite al mismo artefacto. El consumidor no vuelve a dibujar el documento con otro nombre.
2. En la primera pareja F1/F2 pueden usarse círculos **1 = CF-C01 / CF-A01** y **2 = CF-C02 / CF-A02**, **solo como propuesta nueva**. No se afirma que sean los 1/2 del audio. Resto: círculos 3–12 con tabla de correspondencias. Mantener ID global a través de todas las fases, no reiniciar 1 en cada página.
3. Cuando se use un paquete conjunto, rotular «1+2» y declarar que contiene dos fuentes diferentes; no convertirlas en un solo documento indistinguible.
4. La lectura de varias salidas por una fase se expresa con varios conectores entrantes. Una copia EVE distinta de un replay debe tener sufijo de ejecución y hash, aunque sea del mismo tipo CF-A02.
5. Toda salida debe tener consumidor identificado en la tabla; si es salida final de investigación (CF-A12), rotularla como archivo/observaciones finales. No forzar una flecha F4 → F5 para simular continuidad: **el publicador consume CF-A07, no un informe de métricas**.
6. Diferenciar con leyenda: flujo de datos; habilitación de despliegue; evaluación offline; mantenimiento supervisado. Las flechas de mantenimiento no representan un bucle autónomo de actualización.

Texto de enlace propuesto entre F1/F2: «La adquisición genera la captura cruda CF-A01 y los eventos estructurados CF-A02. Ambas fuentes, identificadas respectivamente por los conectores propuestos 1 y 2, se utilizan en el preprocesamiento para construir variables por IP iniciadora y fin de ventana. El contrato CF-A05 determina qué variables se extraen; los documentos de origen no se generan de nuevo en F2».

## 4. Especificación implementable por lámina

Usar una lámina por fase, con título, entradas por ID, operaciones centrales y salidas por ID. El índice de siete fases puede conservarse como orientación, no como sustituto de las láminas legibles. Colocar explicación inmediatamente antes/después de cada figura en su subsección metodológica; número editorial definitivo pendiente de la estructura del manuscrito.

| Lámina | Nodos y conectores mínimos que debe mostrar | Ajuste mínimo sobre el material existente |
|---|---|---|
| F1 | Tráfico real → copia SPAN → interfaz pasiva; bifurcación tcpdump/Suricata → CF-A01/02; inventario CF-A03 | Quitar dataset/calibración de la salida directa de captura; remitirlos a F2/F3. No copiar toda la topología en cada fase. |
| F2 | CF-C01/02 + CF-C05 → alcance/dedup → atribución → «Agrupación por IP y tiempo» → CF-A04 | Sustituir documentos duplicados por círculos. Quitar valores detallados del nodo; distinguir datos en memoria y dataset offline. |
| F3 | Dos bloques: construcción/calibración offline → CF-A06; operación CF-A04 + CF-A06 → puntuación IF y heurísticos → CF-A07 | No confundir salida de score ALERT/PERMIT con LIMIT/BLOCK final. Incluir guarda sin paquetes L3/L4 y posibilidad de señal L7; no «vacía = nunca hay regla». |
| F4 | Fuentes congeladas y protocolo → comprobación de integridad/cobertura → puntuar/comparar → CF-A08 | Mismo PCAP cuando el protocolo lo exige; separar episodio/ventana y los umbrales derivados offline. Quitar 9/9 vs 0/9 como rótulo de método vigente. |
| F5 | CF-C07 → selección de señal/acción → exclusiones/agregación/escalada → CF-A09 → relay → verificación → agente/nftables; evidencia externa CF-A10 | Reutilizar la cadena ya dibujada. El modo de observación del sensor SPAN no impide enforcement distribuido; activar `--enforce` local no es la instrucción correcta para esa arquitectura. En campaña A marcar agente desactivado. |
| F6 | Configuración local + CF-C06 → unidades/captura/motor/panel; estado/registro → CF-A11 | Dibujar soporte transversal. Panel como observabilidad, no autoridad que cambia modelo o confirma host remoto. No usar el perfil genérico histórico como perfil de Sensor1. |
| F7 | CF-C08/11 y CF-C10 si disponible → demostración y validación interna/externa → CF-A12 | Separar «sesión interna realizada» y «externa por ejecutar/confirmar». Quitar 8 s inline y 58 corridas como resultados del IF limpio actual. |

### Parámetros que se explican en texto, no dentro de las cajas

- **Unidad y tiempo:** IP iniciadora y fin causal de ventana; ventanas 10/30/60 s, paso de emisión 10 s (T2). No es escoger una sola ventana global ni latencia garantizada. A2 respalda los segundos y la separación texto/figura.
- **Captura:** interfaz `ens37` sin IP de captura; 16 archivos × 15 s = 240 s; historia motor 230 s y retención 15 min (T1). Son tres magnitudes distintas de las ventanas de variables.
- **Alcance:** red de entidades `10.10.0.0/16`, exclusión de protocolos 112/240 y lista de IP de gestión/infraestructura (T1:39–67). Exclusión de scoring ≠ lista nunca-bloquear del publicador. El DNS/AD puede clasificarse y estar protegido frente a aplicación (T10:131–135).
- **Dedup:** describir la regla de copia SPAN y cuantificar por separado paquetes suprimidos y vectores repetidos. El 62 % de vectores duplicados de entrenamiento (T9:21) no es proporción de paquetes duplicados SPAN.
- **Features:** 28 columnas v2; extracción ampliada/L2 no acredita uso de L2 por el modelo. En el entrenamiento auditado hay dos constantes, no confundirlo con «27 observables» del contrato operativo (T9:19–23; T8:90–100).
- **Modelo:** ID `if_limpio_2026_10`; score `score_samples`, condición estricta `<`; umbral desplegado archivado **−0,5693969936322356** sobre validación de 65 633. Umbrales derivados sobre 65 553 para α 0,05/0,03/0,01: **−0,5694578968203694 / −0,5898535710336618 / −0,6223889502095352** (T9:43–47; T10:29–35). No copiar `umbral = 1.8126…` residual del TOML ni −0,568892 antiguo como corte limpio.
- **Heurísticos:** versión `2026-10-06.2`; fuerza bruta ≥5 solicitudes/60 s y fallo ≥0,8 → BLOCK; escaneo rama normal ≥20 intentos/30 s, unicidad ≥0,45, completitud ≤0,3, o ráfaga ≥200 y completitud ≤0,1 → BLOCK; HTTP ≥100 solicitudes/60 s con fallo <0,8 → LIMIT; DNS ≥20 consultas/60 s y NXDOMAIN ≥0,5 o unicidad ≥0,45 → LIMIT. Son valores del código inspeccionado, no parámetros aprobados en audio ni prueba de todas las ramas en vivo (T4:40–136).
- **Respuesta:** fuente reciente de decisiones por defecto 120 s; LIMIT 300 s y BLOCK escalonado 300/1800/3600 s según política histórica documentada; timers 10 s escalonados según láminas/pending actualizados, no una garantía de tiempo total (T5; T8:126–137; T13:84–91). Verificar las unidades archivadas del corte que se use al redactar.
- **Elegibilidad:** distinguir PCAP incompleto, pendiente/no regenerada y decisión PERMIT; continuidad del motor y marcas de fuentes deben formar parte de la evaluación (T3:705–732; T10). No convertir ausencia de evaluación en TN/FN.
- **Reentrenamiento:** describir solo como procedimiento de candidatos con promoción humana, separado de inferencia; tener `activo=true` en configuración no prueba ejecución nocturna actual, ni promoción efectiva (T1:118–128; T7).

## 5. Otras láminas existentes reutilizables y ajustes mínimos

| Ruta absoluta | Evidencia revisada y reutilización | Ajuste antes de incorporar |
|---|---|---|
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\02-metodologica.mmd` | Líneas 5–27: índice de las siete fases | Mantener índice; quitar «9/9 vs 0/9» de la metodología y no usar cadena lineal como dependencia técnica literal. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\01-operacional.mmd` | Líneas 12–71: PCAP/EVE, inferencia y observabilidad | Cambiar identidad/umbral antiguos; añadir relay y publicador explícitos; separar detección/decisión/aplicación. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\03-construccion-entrenamiento.mmd` | Líneas 5–45: construcción y promoción humana | Reconciliar particiones/modelo limpio y cinco comparadores recientes; módulo nocturno como capacidad documentada, no ejecución actual probada. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\drawio\VI-1_Arquitectura_operativa.drawio` | Página 0 «Arquitectura»; líneas 8–9,39–89,108: SPAN, análisis y respuesta distribuida | Reutilizar estructura física y separar las vistas por fase con IDs; agregar fecha/modo. Ya aclara que el host actúa. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\drawio\VI-3_Decision_hibrida.drawio` | Página 0 «Arquitectura»; líneas 28–46,48–76: dos niveles, score, reglas, publicador | Base preferible para F3/F5: conservar dos niveles, comprobar rótulo del umbral y añadir guardas/marcas PCAP. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\02-metodologia\diagramas-vistas-gui\drawio\VI-4_Respuesta_reversion.drawio` | Página 0 «Arquitectura»; líneas 37–79: copia SPAN, relay, firma y nftables | Reutilizar secuencia sin presentar 13/26,1/41,4 s (líneas 83–102) como medición actual. Quitar «no el cómputo» (línea 93): la campaña A muestra un cuello computacional. |
| `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\diagramas\topologia-laboratorio.drawio` | Archivo localizado; contenido no auditado en este frente | Solo candidato de contexto histórico; no sustituye una fase ni acredita arquitectura vigente. |

## 6. Contraste con pendientes y cambios recientes: decisiones para cerrar

1. **F4 ya no está solo planificada:** A se ejecutó el 29-oct con 25 episodios, pero **0/25 evaluables** por continuidad. Actualizar narrativa antes de usar cualquier tabla de éxito. No son 25 falsos negativos (T10:3–9,78–87).
2. **F2/F6 tienen diagnóstico posterior al informe inicial:** equivalencia de variantes por entidad/pendientes en **773/773 ciclos**, sin modificación del despliegue. La mejora estimada aún no resuelve inundación HTTP; falta medir en vivo una versión aprobada. Commits documentales `a99a615`, `9a5577a`, `1e378d2` y T11. No dibujar esa optimización como aplicada.
3. **Modelo limpio y comparación:** conservar F3 como modelado/integración; reemplazar la explicación de siete candidatos como selección actual demostrada por el contraste explícito con los cinco detectores de T9. IF no fue el mejor en detección y los comparadores no son plug-ins intercambiables certificados.
4. **Híbrido no implica mejora universal:** los antecedentes 6/9,7/9,9/9 corresponden a otra versión. El material actualizado no sostiene «ninguno basta por separado» como conclusión general del sistema limpio. Usar evaluación por componentes y declarar reutilización de episodios (T12; T13:16).
5. **Respuesta existe, pero A fue sombra:** el antecedente de BLOCK de octubre no equivale a agente activo el 29-oct. Confirmar qué corte se mostrará; no actualizar estado actual sin evidencia nueva (T13:12; T10:234–239).
6. **Antes de cerrar N-03:** identificar la lámina del audio y sus documentos 1/2; confirmar índice editorial F1–F7 con el autor; aplicar cambios en copias autorizadas; cotejar cada círculo con este registro y leer figuras al tamaño de publicación. Este frente entrega el mapa, no acredita esas tareas terminadas.
7. **Antes de cerrar N-06:** acordar la denominación «producto / marco metodológico implementado», revisar la propuesta de definición y aplicarla en metodología; mantener resultados y límites consistentes con los cortes. Responsable y fecha no están asignados nominalmente en el audio.
