# Matriz: observación → corrección → archivo → comprobación

Correcciones sobre la preparación publicada en `b59c6c8`. Estado: **D** documentado · **I** implementado ·
**PA** probado de forma aislada · **VE** verificado en el entorno.

| # | Observación | Corrección | Archivo(s) | Comprobación | Estado |
|---|---|---|---|---|---|
| 1 | `duracion_s` de texto en escaneos → `TypeError` en `duracion_s + 120` | Separados: `duracion_objetivo_s` (número o null) y `timeout_s` (número); descripción en `duracion_descripcion` | `escenarios/escenarios.json`, `scripts/esquema_campana.py` | test rechaza `timeout_s` de texto | PA |
| 2 | Falta validar tipos/valores/destinos/puertos/rutas/deps | `esquema_campana.validar()` valida todo y exige herramientas si `--autorizado` | `scripts/esquema_campana.py` | 6 casos de validación en el test | PA |
| 3 | Marcadores `<PUERTO>/<R>/<ZONA_LAB>` podían colarse | La validación aborta ante cualquier `<...>` sin resolver o `null` en escenario habilitado | `esquema_campana.py`, `generar_campana.py` | test de marcador `<ZONA_LAB>` | PA |
| 4 | Config/fichas/comandos no coincidían; «por ejemplo 10 procesos» | Tasa/concurrencia/alcance fijos (concurrencia 8, max-rate 1500, rangos fijos); comandos derivados solo de la config | `escenarios.json`, `esquema_campana.comando_de`, `escenarios/FICHAS-ESCENARIOS.md` | comandos de los 5 sin marcadores (test) | PA |
| 5 | Variables de entorno cambiaban parámetros en silencio | Eliminado el uso de entorno para parámetros; se lee solo de la config y se escribe `config-efectiva.json` | `generar_campana.py` | revisión de código; `config-efectiva.json` al correr | I |
| 6 | Inicio/fin no separados; faltaban reloj monotónico e ids | Evento `inicio` escrito de inmediato y `fin` por separado, con `campana`/`episodio_id`, pared y monotónico | `generar_campana.py` | test: inicio y fin registrados por separado | PA |
| 7 | Solo se guardaban los últimos caracteres de salida | Salida completa a `salidas/<ep>.out`/`.err`; `fin` registra bytes y rutas | `generar_campana.py` | revisión; tamaños en el evento `fin` | I |
| 8 | Timeout/interrupción no mataban a los hijos | `start_new_session`/grupo; `killpg` (POSIX) o `taskkill /T` (Windows); episodio = `incompleto_*` | `generar_campana.py` | test de timeout mata al hijo (Windows) + sonda `killpg` en el sensor (Linux) | PA + VE |
| 9 | Faltaba calentamiento/observación entre episodios | Calentamiento inicial + contexto previo y observación posterior; no inicia el siguiente hasta cumplir la observación | `generar_campana.py`, `escenarios.json` (`tiempos_s`) | revisión; validación exige contexto≥120 y observación≥90 | I |
| 10 | Simulación debía ser el predeterminado | `--autorizado` explícito; sin él, simula | `generar_campana.py` | test: simulación no crea salidas de procesos | PA |
| 11 | `analizar.py` era un esqueleto | Implementado: lee/valida marcas y motor, correla por ids y clave de ventana, compara 5 configs, D/P/N/NE, compartidas/exclusivas, Tabla 8, control FPR, calidad de datos | `scripts/analizar.py` | test de analizador + corrida CLI sobre fixtures | PA |
| 12 | No clasificar por `window_end`; separar emitido/derivado | Clasificación por `logged_at` (emisión real); `emitido_en_vivo` = `decision==ALERT`; derivadas marcadas aparte | `scripts/analizar.py` | test: HEUR LIMIT en DNS sale derivado (no emitido); IF emitido | PA |
| 13 | No fabricar métricas por ventana sin etiquetas | Solo con `--etiquetas`; sin ellas se declara no calculado | `scripts/analizar.py` | test: sin etiquetas no calcula; con etiquetas TP=1/FP=0 | PA |
| 14 | Receta nginx: `auth_basic` + `return 200` evitaba la auth | Endpoint correcto en Python stdlib (401/200) y nginx corregido (200 tras la fase de auth) | `scripts/endpoint_brute/` | 401/401/200/404 en loopback | PA |
| 15 | Falta ver cómo Suricata/extractor observan el 401 | Sección con `HTTP_PORTS`, comprobación de `event_type:http status:401` y de `http_auth_failure_ratio_60s` | `scripts/endpoint_brute/README.md` | pendiente en srv-dmz | D |
| 16 | Scripts de sombra solo imprimían | Ejecutables con `--ejecutar`, guardan estado, detienen el AGENTE, vacían sets, verifican con fallo seguro | `scripts/modo_sombra.sh`, `restaurar_enforcement.sh` | revisión; no ejecutados en el entorno (por indicación) | D/I |
| 17 | «Detener el publicador no invalida un feed previo» | Se detiene el agente (lo que aplica), no el publicador; se vacían sets; se recuerda comprobar motor sin `--enforce` | `modo_sombra.sh` | revisión | D |
| 18 | Restaurar sin duplicar argumentos | No se edita la unidad: se enmascara/stop y luego unmask/start según estado guardado | `modo_sombra.sh`, `restaurar_enforcement.sh` | revisión | I |
| 19 | Captura: interfaz/rotación/nombres/descartes/espacio | `ens37` verificada; rotación `-C 200`; nombres con hora (sin sobrescribir); stats de tcpdump; estimador de espacio | `scripts/capturar.sh`, `estimar_espacio.sh` | throughput base medido (~113 MiB/h); interfaz confirmada | PA/VE |
| 20 | `logged_at`: ¿existe y qué instante es? | Confirmado en `motor_decision.py` (línea 601): `time.time()` del ciclo = emisión; el analizador lo usa | `scripts/analizar.py`, `config-campana.json` | lectura del código desplegado | VE |
| 21 | Relojes: no concluir por ausencia de chrony | Medido: sensor usa timesyncd (apunta al bastión) pero no sincroniza; desfase −47,55 s | `RELOJES-DNS.md` | 3 mediciones con RTT | VE |
| 22 | DNS: respuesta pública no prueba egress | Consulta única no cacheable → SOA externo: egress confirmado; preparada zona local + check de no-egress | `RELOJES-DNS.md` | `dig` de nombre aleatorio | VE |
| 23 | Referencias a `generar_campana.sh` (no existe) | Corregidas a `generar_campana.py` | `PLAN-CAMPANA.md`, `README.md`, `COMPROBACIONES-PREVIAS.md` | grep sin `generar_campana.sh` | I |
