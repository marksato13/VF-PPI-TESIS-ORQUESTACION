# Plan de campaña — detección (4.2) y respuesta (4.4)

**Fecha:** 26-oct-2026. **Fase:** preparación. **No se ejecuta ningún ataque en esta etapa.**
La campaña A se autorizará en la siguiente instrucción, tras revisar esta preparación.

Configuración congelada y versionada: `config-campana.json`. Comprobaciones previas: `COMPROBACIONES-PREVIAS.md`.

## 0. Por qué una campaña nueva

La batería del 5-oct no permite una Tabla 8 evaluable (ver `../4.2-ablacion/aporte-componentes-r2-2026-10-26/NOTA-R2.md`):
el PCAP empieza 7–21 s antes de cada ataque, no hay registro del motor de ese día y los heurísticos se ajustaron con
esos mismos episodios. Esta campaña genera episodios nuevos con historia continua, relojes comparables y
configuración congelada, y **separa detección de respuesta**.

## 1. Dos campañas separadas

| | **A — Detección (4.2)** | **B — Respuesta (4.4)** |
|---|---|---|
| Objetivo | Comparar IF 0,05 · IF 0,03 · IF 0,01 · heurísticos · híbrido 0,05 · híbrido 0,03 · híbrido 0,01 sobre las mismas ventanas (una sola campaña) | Cadena ataque → señal → feed firmado → agente → nftables → efecto → retirada/caducidad |
| Enforcement | **Sombra** (no altera el tráfico) | **Aplicar** |
| Tráfico | Intacto en todos los episodios | La respuesta modifica el tráfico posterior |
| Orden | Primero | Después, en ensayos separados |

**No se mezclan los resultados.** En A, todos los episodios ven la red igual. En B, cada bloque es una familia y se
reinicia o se registra el estado de la escalera entre bloques.

### Modo sombra de A — procedimiento (requiere intervención, §9)

Estado en vivo al 26-oct: el agente de srv-dmz corre `--aplicar` y el publicador cada 10 s (enforcement activo).
Procedimiento real (el mismo en `scripts/modo_sombra.sh`, README y matriz), con **fallo seguro**:

1. `modo_sombra.sh --ejecutar --motor-verificado` en srv-dmz: guarda el estado real, **detiene** el agente
   (`ppi-enforce-agent.timer` y `.service`), lo **enmascara** (que ningún timer lo reactive), **vacía** los sets
   `cyberflow_bloqueados` y `cyberflow_limitados`, y **verifica** (agente inactivo+enmascarado, nft consultable y sin
   elements). Aborta con código ≠0 si algo falla; una consulta nft fallida **no** se interpreta como set vacío.
2. `--motor-verificado` exige confirmar antes en el **sensor** que `ppi-motor` no corre con `--enforce` (vía directa).
   Se detiene el **agente** (lo que aplica), no el publicador: parar el publicador no invalida un feed ya publicado.
3. Al terminar A: `restaurar_enforcement.sh --ejecutar --escalada-revisada` restaura el agente al estado guardado
   (sin defaults que arranquen servicios), tras **vaciar** los sets. **No** anuncia «restauración exacta» (los sets
   vaciados son limpieza experimental no recuperable) y aborta si el respaldo o la verificación fallan.

> **Los flags confirman comprobaciones ya hechas, no las sustituyen.** `--motor-verificado` declara que **ya**
> comprobaste en el sensor que `ppi-motor` no corre con `--enforce`; `--escalada-revisada` declara que **ya** revisaste
> el feed y el contador de escalada. Sin ellos, los scripts abortan.

El motor y el panel siguen corriendo: A necesita que el motor **decida y registre**, solo que la acción no se aplique.

## 2. Configuración congelada (`config-campana.json`)

- IF limpio y escalador congelados, con sha256.
- 28 características y su orden.
- Umbrales ya verificados (no se recalibra), escala `score_samples`, validación sin Kali (65 553 ventanas):
  α 0,05 = −0,5694578968; α 0,03 = −0,5898535710; **α 0,01 = −0,6223889502** (valor completo
  `-0.6223889502095352`, añadido el 28-oct, config `2026-10-28.1`). Procedencia: columna `validacion_sin_kali_65553`
  de `4.1-modelos/calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json`; `analizar.py` la contrasta por
  igualdad exacta y aborta si difiere. Señal IF si `score_samples < umbral` (estricto); en escala de anomalía,
  `−score > −umbral`.
- **Umbral desplegado ≠ recalibrado:** el motor en vivo usa −0,5693969936 (α 0,05 sobre las 65 633 ventanas
  originales) y no cambia; el «0,05» del análisis es el recalibrado sin Kali. Se informan por separado.
- Commits, blobs git y sha256 desplegado del extractor, motor, heurísticos, feed, escalada y agente.
- Lógica real de combinación, elegibilidad, exclusiones y política de respuesta.
- Escenarios, repeticiones (≥ 5), orden aleatorizado y semilla (20261026).

**Los tres α sobre puntuaciones comunes:** el modelo puntúa cada ventana una vez (`score_samples`); los tres umbrales
son tres cortes del mismo vector de scores, no tres modelos, ni tres pasadas, ni tres campañas. Los heurísticos no
dependen de α y se calculan una vez; híbrido α = IF α **o** heurísticos. Con los mismos scores, IF 0,01 ⊆ IF 0,03 ⊆
IF 0,05 (el analizador comprueba el orden de los umbrales y avisa si no se cumple).

**Emitidas vs derivadas (corregido 28-oct, config `2026-10-28.2`):**

- **Señal realmente emitida:** lo que el motor escribió en `motor_decision.log` como decisión `ALERT` (o como señal
  heurística registrada), con su emisor, umbral y hora **registrados**. `analizar.py` la lista aparte en
  `emisiones_observadas` (registro, componente emisor, decisión, `logged_at` y `window_end_utc`, modelo/score/umbral
  registrados, relación con el episodio, atribución y referencia a la línea del log). No es una columna de la Tabla 8.
  Si falta el emisor o el umbral, o el umbral registrado no es el desplegado, la configuración queda **desconocida**:
  no se rellena con el valor esperado ni se deduce una emisión de que el score cruce un umbral.
- **Clasificación comparativa derivada:** las **siete** configuraciones de la Tabla 8, **incluida IF 0,05**, se
  recomputan sobre los registros como **análisis de componentes y umbrales**. IF 0,05 usa el umbral recalibrado
  (−0,5694578968), no el desplegado (−0,5693969936): que un ALERT real coincida con su clasificación no demuestra que
  esa configuración emitiera. Una clasificación alternativa tampoco equivale a una acción aplicada.
- **Tiempos:** la **latencia real de emisión** solo se mide con una alerta del IF desplegado con configuración
  confirmada, durante el ataque y con atribución confirmada (`primera_alerta_IF_desplegado_confirmada_durante`:
  `logged_at − inicio`). En las configuraciones derivadas, `logged_at` es la **disponibilidad del registro** usado
  (`tiempo_significado`), no una latencia de emisión.

## 3. Escenarios

Fichas completas en `escenarios/FICHAS-ESCENARIOS.md`; parámetros legibles por máquina en `escenarios/escenarios.json`.
Cinco escenarios: DNS inusual, inundación HTTP, escaneo breve, escaneo sostenido, fuerza bruta HTTP. Para cada uno:
objetivo, origen/destino/servicio, comando exacto y versión, tasa/concurrencia/alcance/duración, acción prevista,
evidencia de que la actividad se generó, cliente legítimo de control y condiciones de interrupción y limpieza.

≥ 5 repeticiones por escenario, orden aleatorizado con semilla. 90 s para DNS e inundación HTTP. En los escaneos se
registra tanto la duración del comando como la actividad efectiva. **Las comprobaciones técnicas previas se marcan y se
excluyen de la evaluación.** No se ajustan los escenarios según el detector.

## 4. Historia y registros completos

- PCAP **continuo sin huecos** (no el anillo de 19 min, que recicla: archivar en paralelo o copiar el anillo entero sin
  cortes), EVE completo, features y scores por ventana, `motor_decision.log` íntegro, `marcas.jsonl` de la Kali.
- **≥ 120 s antes** de cada episodio y **≥ 90 s después** (60 s de horizonte + margen para el cierre de ficheros y la
  atribución de flujos). Se registra el arranque y calentamiento del motor.
- No se simula historia cambiando fechas ni se concatenan capturas con huecos.
- **Relojes:** el bastión está sincronizado; **el sensor no**. Corregir el sensor y guardar el desfase (antes y después)
  en sensor, bastión, Kali y srv-dmz. Toda corrección, antes de la campaña y documentada.

## 5. Marcas temporales por episodio

Identificador común (`episodio_id`) en todos los registros. Se conserva:

- inicio y fin del generador, con reloj de pared y monotónico (directo en Kali, no la sesión SSH);
- comando, código de salida y actividad enviada;
- primer y último paquete observado;
- `window_end`, puntuación y señales;
- **hora real de emisión** de la decisión (marca de escritura en `motor_decision.log`), **no** `window_end` ni la hora
  de lectura posterior del fichero.

Instrumentación adicional, si hace falta, como cambio mínimo, aislado y revisable, sin tocar la lógica de detección;
con su prueba de funcionamiento y su reversión documentadas.

## 6. Criterios de evaluación (fijados antes)

- **Durante:** señal atribuible entre inicio y fin del ataque.
- **Posterior:** primera señal tras el fin y hasta +60 s.
- **Sin detección:** observación completa sin señal atribuible.
- **No evaluable:** evidencia insuficiente. Incluye las ventanas del ataque que el motor registró como
  `ventana_no_evaluada` (añadido 28-oct, #59). Sin score, el IF no es evaluable en ellas; el heurístico es
  desconocido; el híbrido solo prueba detección con un positivo confirmado. La ausencia no se afirma, y una detección
  confirmada se mantiene visible fuera de la Tabla 8. En el control y las métricas, estas ventanas no son TN, FP ni
  FN: se informa la cobertura y las tasas son sobre ventanas evaluadas.

Atribución por escenario + origen + destino + contexto; no se cuenta cualquier anomalía de la Kali como detección.
Las configuraciones derivadas offline son análisis de umbrales sobre ventanas observadas, no alertas emitidas.

Además: control normal ≥ 30 min con los perfiles legítimos; denominadores comunes para comparar falsas alarmas;
criterio de etiquetado previo si se calculan métricas por ventana, **separadas** de las 65 505 ventanas de la Tabla 7.

## 7. Verificación de respuesta (campaña B)

- Dónde hay agentes y qué destinos admiten respuesta: **solo srv-dmz 10.10.30.10** tiene agente. 10.10.10.20 (DNS) está
  en `NUNCA_BLOQUEAR` y sin agente → el escenario DNS sirve para **detección**, no para afirmar contención en ese destino.
- Registros que distinguen acción **propuesta** (motor), **publicada** (feed) y **aplicada** (nft del host).
- Medir: tiempo hasta emitir la detección; tiempo adicional hasta aplicar la medida; efecto de LIMIT/BLOCK mientras el
  generador sigue intentando; impacto sobre un cliente legítimo; caducidad/retirada efectiva y recuperación.
- Registrar el estado inicial de restricciones y de la escalera. **No atribuir a una nueva detección un bloqueo que ya
  estaba instalado** (fue justo lo que contaminó el escaneo del 23-oct).

## 8. Scripts (en `scripts/`, parametrizados, aún no ejecutados)

| Script | Dónde corre | Qué hace |
|---|---|---|
| `generar_campana.py` | Kali | Valida la config, lanza los escenarios habilitados en orden aleatorizado por semilla, con calentamiento + contexto previo (≥120 s) y observación (≥90 s); escribe `marcas.jsonl` (inicio/fin separados, pared + monotónico, comando, código, salida completa en `salidas/`). **Simula sin `--autorizado`; aborta ante marcadores o destino fuera de la lista blanca; mata el grupo de procesos en timeout.** |
| `esquema_campana.py` | — | Esquema + validación (tipos, destinos, puertos, rutas, deps, placeholders) y construcción de comandos. |
| `tests/test_herramientas.py` + `tests/fixtures.py` + `tests/regresion_alfa.py` | Laptop/Linux | Verificación sin ataques (212 comprobaciones; 213 con el analizador previo), fixtures con resultado conocido y no-regresión de detección/cobertura frente a los analizadores anteriores (`tests/golden-5config-fixtures.json`, `tests/golden-7config-fixtures.json`). |
| `scripts/endpoint_brute/` | srv-dmz | Endpoint 401 correcto (Python o nginx), unidad systemd, README con Suricata/extractor. |
| `capturar.sh` | Sensor | Captura PCAP continua sin huecos a disco archivado, con rotación por tamaño; marca inicio/fin. |
| `modo_sombra.sh` / `restaurar_enforcement.sh` | srv-dmz | **Detiene y enmascara** el agente para A (impedir que aplique; NO es ejecutarlo en dry-run) y lo restaura para B según el estado guardado; fallo seguro. `restaurar` exige `--escalada-revisada`. |
| `verificar_integridad.py` | Laptop/sensor | Informe de integridad por episodio (PCAP/EVE/decisiones/historia/relojes); `analizar.py --integridad` lo exige para declarar evaluable. |
| `analizar.py` | Laptop/sensor | Lee `marcas.jsonl` + `motor_decision.log` (+ `--destinos`, `--integridad`); clasifica por `logged_at` D/P/N/NE en **7 configuraciones comparativas derivadas** (IF 0,05/0,03/0,01, heurísticos, híbrido 0,05/0,03/0,01) y lista aparte las **emisiones observadas** (alertas reales, con emisor y umbral registrados); la Tabla 8 cuenta **solo** detecciones durante con **atribución confirmada** y episodio **evaluable** (cobertura + evidencia de destino que cubre el intervalo + integridad apta). |
| `comprobar_relojes.sh` | cada host | Guarda el desfase NTP antes y después. |

Los scripts de generación son **generadores de carga de laboratorio** (nmap, bucles de `curl`/`dig`, intentos de auth
contra un endpoint de prueba), equivalentes a los ya versionados en `_campana/orquestar_campana.sh` y al `orq.sh` del
5-oct. No se ejecutan en esta fase.

## 8.bis Secuencia exacta: preparación → ejecución → restauración

**Preparación (requiere intervención, §9; una vez):**
1. Sensor: sincronizar `timesyncd` y medir desfase (`RELOJES-DNS.md`). `comprobar_relojes.sh` en los 4 hosts.
2. DNS/AD: crear la zona local reservada; comprobar no-egress. Fijar `params.zona_dns` y `habilitado:true` del DNS.
3. srv-dmz: desplegar `endpoint_brute/` (401); comprobar que Suricata lo parsea. Fijar `brute_puerto/brute_ruta` y `habilitado:true`.
4. Sensor: `estimar_espacio.sh` y preparar ruta de archivado con holgura.

**Ejecución de la campaña A (cuando se autorice):**
1. Sensor: `capturar.sh ens37 <dir>` (captura continua) — dejar corriendo.
2. Sensor: comprobar `ppi-motor` sin `--enforce`. srv-dmz: `modo_sombra.sh --ejecutar --motor-verificado` (detiene y enmascara el agente, vacía sets, verifica).
3. Control normal ≥ 30 min (tráfico legítimo) y arranque/calentamiento del motor registrados.
4. Kali: `generar_campana.py --config ../escenarios/escenarios.json --salida-dir ./corrida --autorizado`.
5. Al terminar: parar `capturar.sh`; recoger `marcas.jsonl`, `salidas/`, PCAP, EVE, `motor_decision.log`.

**Restauración (obligatoria tras A, antes de B):**
1. srv-dmz: `restaurar_enforcement.sh --ejecutar --escalada-revisada` (reactiva el agente al estado previo guardado; los sets vaciados no se recuperan).
2. Verificar enforcement activo (`journalctl -u ppi-enforce-agent`).

**Análisis (sin tráfico):** primero `verificar_integridad.py --descriptor … --salida integridad.json`; luego
`analizar.py --marcas … --motor … --destinos … --integridad integridad.json --control "desde,hasta"` (una sola
pasada produce las 7 configuraciones; comprobar en `analisis.json` que `umbrales.procedencia.estado = verificada` y
`umbrales.orden_respetado = true`; fuera del repositorio la procedencia queda `no_verificada` y se informa así). Un episodio
**solo es evaluable** con cobertura temporal continua, **evidencia de destino** (atribución confirmada) e **integridad
apta**; la Tabla 8 cuenta en el numerador **solo detecciones durante con atribución confirmada**. Las señales
observadas sin confirmar, previas, tardías o ambiguas van a registros complementarios, no al numerador. Sin
`--integridad` o sin `--destinos`, ningún episodio se declara evaluable. Revisar en `analisis.json` el bloque
`ventanas_no_evaluadas` (motivos, duplicados, conflictos, efecto por episodio) y la cobertura del control y de las
métricas antes de leer las tasas. Los contadores del generador son **intentos**
del bucle, no peticiones enviadas ni respuestas (eso se mide con PCAP/EVE/servidor).

**Campaña B (4.4), separada:** repetir con el agente en `--aplicar`, una familia por bloque, registrando cada eslabón.

## Estados de madurez (usados en `MATRIZ-OBSERVACIONES.md` y `README.md`)

- **Documentado (D):** descrito y con procedimiento, sin ejecutar.
- **Implementado (I):** código/escrito y revisado.
- **Probado de forma aislada (PA):** verificado con fixtures/loopback fuera del entorno real.
- **Verificado en el entorno (VE):** comprobado en sensor/bastión/srv-dmz.

**La campaña NO está lista** mientras sigan abiertos los requisitos críticos de §9 (NTP, zona DNS, endpoint,
captura/espacio) y la campaña A no esté autorizada.

## 9. Lo que requiere intervención humana antes de A

Detalle y comandos en `COMPROBACIONES-PREVIAS.md`. Resumen:

1. **NTP del sensor** sin disciplinar → sincronizar y medir el desfase.
2. **Modo sombra**: **detener y enmascarar** el agente de srv-dmz (impedir que aplique — esto **no** es ejecutar el
   agente en dry-run) y verificar sets vacíos. Revertir tras A con `restaurar_enforcement.sh --ejecutar --escalada-revisada`.
3. **Zona DNS de laboratorio**: el resolutor 10.10.10.20 reenvía a Internet; hace falta una zona/dominio reservado que
   resuelva localmente y no consulte a terceros.
4. **Endpoint de fuerza bruta**: no existe (`/login` → 404, 8081 cerrado); preparar un servicio aislado que devuelva 401.
5. **Captura continua y disco**: el anillo recicla cada ~19 min y quedan 21 GB; prever archivado sin huecos y espacio.
6. **Encender la Kali** para la campaña (ahora está encendida; confirmar en el momento).

Nada de esto se ejecuta aquí. La campaña A se lanza con la siguiente instrucción.
