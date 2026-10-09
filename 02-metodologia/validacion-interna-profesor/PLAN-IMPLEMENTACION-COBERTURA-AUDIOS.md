# Plan por bloques — validación interna y cobertura de los audios

**Fecha de corte:** 2026-10-09. **Estado:** planificación; no se modificó el producto ni el sensor al redactar este plan.

## Fuentes y alcance

- `CYBERFLOW/PROMPTS-CODEX-OPENCODE.md`: reglas de trabajo y tres encargos para el producto.
- `CYBERFLOW/producto-as-deployed/docs/VALIDACION-INTERNA-COBERTURA-AUDIOS.md` (`8118d7d`): siete requisitos del profesor, evidencia y responsables.
- `producto-as-deployed/docs/VALIDACION-INTERNA-TECNICA.md` y `docs/GUION-DEMO.md`: requisitos técnicos, límites y guion.
- `orquestacion-limpio/02-metodologia/metodologia-7-fases/` y `comparacion-cyberflow-suricata/`: método y resultados. Las notas 26, 28, 31 y 32 sostienen 9/9 vs 0/9, Nikto y ablación, **con sus límites**.

La **validación interna** es una demostración técnica grabada y observaciones del profesor/expertos. **TAM y juicio de expertos externos** constituyen una validación posterior; la lista de tablas/figuras y el artículo son entregables editoriales. No mezclar esos cierres con una modificación del panel.

## Línea de base antes de implementar

| Aspecto | Estado constatado | Consecuencia |
|---|---|---|
| Repo de trabajo | `producto-as-deployed`, rama local `master`, **4 commits adelante** de `origin/as-deployed-sensor-20261006`, árbol limpio. Los cuatro son `edb4036`, `6e2a25d`, `5c9d0ac`, `8118d7d`. | No hacer pull/reset ni push automático; preservar los cuatro commits de Mark/Claude. El mapa de audios dice «3 commits» y debe actualizarse a cuatro. |
| GUI local vs sensor | SHA-256 de `scripts/engine/dashboard.py` local `e3648ab0...58fea0`; en Sensor1 `53499d6c...70a2ec32f`. `ppi-dashboard` está activo, pero **no sirve aún el mismo archivo local**. | Una casilla «listo en código» no prueba «visible en vivo». Desplegar únicamente tras QA y respaldo del archivo del sensor. |
| Modelo vivo | Sensor1 usa `if_recalibrado_2026_09`, Pipeline IsolationForest, umbral `score_samples=-0,568892`, `calibrado_en_esta_red=true`. | No cambiar joblib, manifiesto, umbral ni servicio del motor en estos bloques. Conservar la entrada histórica OCSVM en logs, pero no mostrarla como detector actual. |
| GUI local | Ya existen tres vistas de topología, visor `/api/archivo`, «Pruebas previas» y columna Acción. Aún figuran `card('Detector', 'OCSVM')` y un paso del tour que dice «One-Class SVM». | Corregir textos y probar roles/JS; **no volver a implementar** vistas, visor ni columna. |
| Reentrenamiento | Runbook y comparador existen, pero el runbook apunta a un `--antes` JSON inexistente en el repo; usa `--anomalias`/`--informe` en `puntuar_deteccion.py`, que solo acepta `--modelo`, `--csv`, `--etiqueta` y espera un paquete dict, no el Pipeline desplegado. | **Bloqueo real del requisito 3.** Corregir contrato y fuente de métricas antes de ejecutar un ensayo; no inventar informe «antes». |

## Orden y dependencias

```text
B0 congelar estado y fuentes
 ├─ B1 GUI: detector y guía ──────────────┐
 ├─ B2 reconciliar modelo/config/docs ───┤
 └─ B3 reentrenamiento demostrable ──────┼─ B4 evidencia y límites ── B5 publicar GUI ── B6 sesión interna
                                           └────────────────────────────── B7 artículo/listas y validación externa
```

### B0 — Preflight y protección del trabajo existente (P0)

**Dónde:** `producto-as-deployed` y Sensor1 en lectura. **Responsable:** implementación local; Mark aprueba cualquier despliegue.

1. Registrar HEAD, estado limpio, los cuatro commits no publicados y hashes del panel local/vivo; revisar diff antes de editar.
2. Identificar el comando de demo, fixtures y tests relevantes. Confirmar que las rutas del visor `/api/archivo` tienen lista de permitidos y control de rol; no exponer secretos ni rutas arbitrarias.
3. Fijar la tabla «afirmación → artefacto → versión → ámbito» para no mezclar FPR test 4,45 %, F6 histórico 22,97–25,81 %, 9/9 del **híbrido** y 6/9 del modelo solo.

**Cierre:** baseline reproducible, sin modificaciones en Sensor1; inventario de rutas y hashes guardado en evidencia sin copiar claves ni credenciales.

### B1 — Coherencia de GUI y recorrido guiado (P0; requisitos 1, 2, 4 y 5)

**Dónde:** `producto-as-deployed/scripts/engine/dashboard.py` (Prompt 1). **Dependencia:** B0.

1. Sustituir `card('Detector', 'OCSVM')` por el nombre real de `/api/status`, usando `DETECTOR_LABEL` con fallback; mantener `ocsvm_scaled` como etiqueta histórica.
2. Corregir el paso «One-Class SVM» del tour y cubrir tres vistas, *Pruebas previas* y el flujo real del visor («Ver archivos» → ficha → «◎ Ver contenido»). Comprobar que pasos ocultos por rol se omitan correctamente.
3. Verificar la sección Modelo: 7 candidatos y ablación **modelo 6/9, heurísticos 7/9, combinado 9/9**. La columna Acción ya existe: solo comprobarla, no duplicarla.
4. Validación: tests enfocados de panel, arranque local `--demo`, extraer el **JS servido** y ejecutar `node --check`; probar respuesta 403 fuera de whitelist de `/api/archivo` y lectura permitida con rol desarrollador. Revisar visualmente las tres vistas y el tour.

**Cierre:** ninguna etiqueta del detector vivo dice OCSVM; demo y JS servido pasan, visor no da acceso fuera de la lista, evidencia de vistas/roles. **No desplegar todavía.**

### B2 — Reconciliación del modelo desplegado (P0; requisitos 1, 2 y 6)

**Dónde:** Prompt 2, `configs/cyberflow.toml`, manifiestos y model cards de `producto-as-deployed`. **Dependencia:** B0; puede prepararse al mismo tiempo que B1.

1. Elaborar `docs/RECONCILIACION-MANIFIESTO-MOTOR.md`: origen de cada ruta/umbral, valor en el artefacto, valor efectivo del servicio, acción segura.
2. Explicar la secuencia histórica: `if_primary_weighted` declarado principal en el experimento, OCSVM comparador/promovido antes y **IsolationForest recalibrado** efectivo hoy. Distinguir `decision_function=-0,068892` de `score_samples=-0,568892`.
3. Actualizar textos y ficha del detector operativo; conservar documentación histórica de OCSVM y evidencia. El `.toml` genérico todavía apunta a OCSVM: **no modificarlo ni regenerar systemd** sin comprobar qué instalación consume ese archivo y acordar la migración con Mark.
4. Cruzar con `VALIDACION-INTERNA-TECNICA.md`: separar el FPR histórico F6 del test normal recalibrado; no afirmar que una medición borra la otra.

**Cierre:** informe de diferencias, ficha y texto coherentes con runtime; cero cambios en modelo/umbral/servicio.

### B3 — Reentrenamiento en seco con comparación ANTES/DESPUÉS (P0; requisito 3)

**Dónde:** `docs/RUNBOOK-REENTRENAMIENTO-DEMO.md`, `scripts/modeling/comparar_reentrenamiento.py` y scorer. **Dependencias:** B0 y fuente «antes» validada en B2.

1. Reparar el runbook contra los `--help` reales: `particionar_linea_base.py` y `entrenar_preliminar.py` sí existen; `puntuar_deteccion.py` **no** acepta `--anomalias`/`--informe` y no carga el Pipeline del modelo vivo. Elegir `20-puntuar-por-ventana.py` u otro adaptador comprobado para TPR del congelado; no fingir compatibilidad.
2. Obtener el informe ANTES **desde un artefacto real verificable** (manifiesto/informe del IF desplegado), normalizar la escala y esquema antes de compararlo con el DESPUÉS. Si no existe un campo, declararlo «no disponible» y bloquear la conclusión; no fabricar `artifacts/model/if_recalibrado_desplegable.json`.
3. Ejecución aislada: copiar datos necesarios a un entorno de prueba (preferible Sensor2 o carpeta aislada con Python/dependencias compatibles), particionar con guarda, entrenar candidato en ruta separada y conservar hashes. La línea base del sensor ya supera 300 MB: estimar tiempo, memoria y disco antes de correr; **no usar ni reiniciar el modelo vivo**.
4. Hacer que `comparar_reentrenamiento.py` muestre FPR validación/test y TPR/cobertura en unidades comparables. La política de promoción exige **cobertura ≥ actual y FPR ≤ actual**: si falta cobertura, salida «evaluación incompleta», nunca «candidato aprobado» solo por FPR.
5. Guardar tabla `comparacion-*.md`, informe de partición y comandos exactos; un resultado desfavorable también cierra el ensayo, **sin desplegar**.

**Cierre:** runbook ejecutable de punta a punta en seco, tabla ANTES/DESPUÉS basada en fuentes reales, decisión justificada y pruebas de parsing/escala/fail-closed. Mark solo muestra el resultado en la validación.

### B4 — Evidencia, delimitaciones y guion (P1; requisitos 1, 4 y 6)

**Dónde:** `docs/VALIDACION-INTERNA-COBERTURA-AUDIOS.md`, `VALIDACION-INTERNA-TECNICA.md`, `GUION-DEMO.md`, orquestación notas 19–32. **Dependencias:** B1–B3 para el material final.

1. Mapa por cada una de las siete exigencias: acción de pantalla, comando/artefacto, cifra, limitación, quién lo demuestra. Separar «listo local» de «verificado vivo».
2. Declarar límites **con denominador y contexto**: N=3 por familia en batería, Nikto N=1, ET Open 0/9 solo bajo ese ruleset/configuración, 4,45 % test normal vs 22,97–25,81 % F6 histórico, DNS modelo 0 % (lo cubre heurístico), L2 no entra en scoring v2, 27/28 observables, enforcement en el host y no sensor inline.
3. Resolver contradicciones del material de demo: `VALIDACION-INTERNA-TECNICA.md` §2 dice tres tiempos medidos, §4 aún dice que faltan decisión+bloqueo; cotejar `evidencias/tiempos-2026-10-06.md`. El guion cita versión de umbrales `2026-10-06.1`, mientras la nota 32 describe un fix `2026-10-06.2`; verificar qué versión **ejecuta** el publicador antes de ponerla en pantalla.
4. Para «cuarentena/aislar», no inventar un cuarto estado: el sistema actual ofrece PERMIT/LIMIT/BLOCK. Acordar si BLOCK de una IP satisface el discurso de aislamiento o declarar cuarentena granular como trabajo futuro.

**Cierre:** guion de demo con cada afirmación respaldada y límites; no quedan «listo» donde solo hay plan o código local.

### B5 — Publicación controlada del panel en Sensor1 (P1; requisitos 2, 4 y 5)

**Responsable:** Mark publica/autoriza el despliegue y teclea sudo. **Dependencias:** QA de B1–B4.

1. Mark decide si publicar los commits locales en `origin/as-deployed-sensor-20261006`. Ningún agente hace push por su cuenta.
2. Respaldar `dashboard.py` vivo (su hash **no coincide** con el archivo local); comparar antes de reemplazar y transferir **solo** el artefacto revisado, sin tocar joblib, manifiesto, capturas ni servicios del motor.
3. Verificar sintaxis Python, JS servido, tests y permisos; Mark ejecuta el reinicio controlado de `ppi-dashboard` con sudo. Comprobar estado HTTPS/login y roles, tres vistas, visor de código, *Pruebas previas*, tarjeta Detector y tour. Capturas fechadas de la GUI ya autenticada las aporta Mark; no compartir contraseña.
4. Conservar copia anterior y comando de rollback; si la GUI falla, restaurar solo `dashboard.py` y reiniciar únicamente el panel.

**Cierre:** hash del archivo vivo actualizado, servicio sano, recorrido autenticado y evidencia de las tres vistas. Las métricas de resultado van a Resultados; F6/F7 describe el componente y el método.

### B6 — Ensayo y sesión de validación interna (P1; requisitos 1–6)

**Responsable:** Mark + validadores; apoyo técnico prepara evidencia. **Dependencias:** B5 y B3.

1. Ensayo de guion con tiempos diferenciados: detección, decisión y respuesta. Medición con origen/destino y contexto; no prometer «bloqueo en segundos» si el feed minutely tarda 1–2,5 min.
2. Escenario controlado solo con autorización de Mark: captura por SPAN → decisión del modelo/heurístico → feed firmado → bastión → host → `nftables` → panel. Mantener listo un replay/evidencia histórica si no conviene generar tráfico en vivo.
3. Iniciar la grabación **con consentimiento de los participantes**; registrar preguntas, observaciones, responsable y mejora con enlace a evidencia. No sustituir la validación técnica por TAM.
4. Después de la sesión: acta de hallazgos, acciones priorizadas y correcciones localizadas; nunca reescribir un resultado desfavorable como éxito.

**Cierre:** video o acta de la sesión, lista de observaciones y trazabilidad requisito → demo → evidencia → corrección. La fecha «jueves» de guiones antiguos se sustituye por la fecha real de la sesión.

### B7 — Entregables académicos separados (P1/P2; requisito 7 y validación externa)

**Responsable:** Mark y compañero de artículo. **Dependencia:** evidencia consolidada de B4/B6.

1. Artículo/tesis: esquema metodológico de siete fases, lista de tablas y lista de figuras con numeración real; colocar la **descripción** de GUI/alertas en Metodología F5–F7 y las capturas/resultados en Resultados.
2. Validación externa: administrar TAM y juicio de expertos, calcular Alfa de Cronbach/V de Aiken con respuestas reales. No marcarla concluida por tener los instrumentos. Reconciliar previamente `03-entregables/08-validacion-usuarios/README.md`, que todavía prescribe SUS, con la decisión vigente TAM; conservar SUS como material histórico, sin intercambiar instrumentos ni resultados.
3. Reconciliar objetivos e hipótesis formales del PPI con F1–F7 y conclusiones; evitar «predicción total», «zero-day probado», «Suricata nunca detecta» o «bloqueo inline en el sensor».

**Cierre:** índices y sección académica revisados por el equipo de tesis, instrumentos aplicados con evidencia y conclusiones limitadas a lo medido.

## Secuencia mínima para la próxima validación interna

**B0 → B1 + B2 → B3 → B4 → B5 → B6.** B7 editorial puede avanzar en paralelo, pero TAM/juicio externo no sustituye B6. Si el tiempo es corto, no sacrificar **B3 (tabla antes/después real)** ni **B5 (GUI viva y verificable)** para añadir decoración o nuevas features.

## Reglas de ejecución

- Mantener separados `producto-as-deployed` (código de demo) y `orquestacion-limpio` (plan/evidencias). Este archivo es solo planificación.
- No sobrescribir los cuatro commits locales ni el `dashboard.py` vivo sin diff y respaldo. No tocar infraestructura, modelo congelado, umbrales, pfSense, CORE ni ejecutar Kali por este plan.
- No hacer push, reinicios ni despliegues sin intervención de Mark. No registrar contraseñas, claves privadas, PCAP completos ni datos sensibles en Git.
- En la fase de código seguir el formato del repo y comprobar **JavaScript servido**, no solo la cadena Python. Si la demo no tiene la evidencia, declararlo pendiente.
