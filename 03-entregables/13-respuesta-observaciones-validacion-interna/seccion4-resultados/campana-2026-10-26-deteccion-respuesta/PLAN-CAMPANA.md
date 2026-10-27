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
| Objetivo | Comparar IF 0,05 · IF 0,03 · heurísticos · híbrido 0,05 · híbrido 0,03 sobre las mismas ventanas | Cadena ataque → señal → feed firmado → agente → nftables → efecto → retirada/caducidad |
| Enforcement | **Sombra** (no altera el tráfico) | **Aplicar** |
| Tráfico | Intacto en todos los episodios | La respuesta modifica el tráfico posterior |
| Orden | Primero | Después, en ensayos separados |

**No se mezclan los resultados.** En A, todos los episodios ven la red igual. En B, cada bloque es una familia y se
reinicia o se registra el estado de la escalera entre bloques.

### Modo sombra de A — procedimiento (requiere intervención, §9)

Estado en vivo al 26-oct: el agente de srv-dmz corre `--aplicar` y el publicador cada 10 s (enforcement activo).
Para A, **antes** de generar tráfico:

1. Poner el agente en dry-run: quitar `--aplicar` del `ppi-enforce-agent.service` en srv-dmz (lo documenta su propia
   cabecera) **o** detener `ppi-publicar-feed.timer` en el sensor.
2. Verificar que `cyberflow_bloqueados` y `cyberflow_limitados` quedan **sin elements**.
3. Registrar el cambio y su hora. **Revertir al terminar A.**

El motor y el panel siguen corriendo: A necesita que el motor **decida y registre**, solo que la acción no se aplique.

## 2. Configuración congelada (`config-campana.json`)

- IF limpio y escalador congelados, con sha256.
- 28 características y su orden.
- Umbrales ya verificados (no se recalibra): α 0,05 = −0,5694578968; α 0,03 = −0,5898535710.
- Commits, blobs git y sha256 desplegado del extractor, motor, heurísticos, feed, escalada y agente.
- Lógica real de combinación, elegibilidad, exclusiones y política de respuesta.
- Escenarios, repeticiones (≥ 5), orden aleatorizado y semilla (20261026).

**Los dos α sobre puntuaciones comunes:** el modelo puntúa cada ventana una vez (`score_samples`); los dos umbrales
son dos cortes del mismo vector de scores, no dos modelos ni dos pasadas.

**Emitidas vs derivadas:** las decisiones del motor en `motor_decision.log` son las **emitidas en vivo** (el motor usa
α 0,05). IF 0,03, heurísticos solos e híbridos se recomputan **offline** sobre las ventanas observadas y se presentan
como **análisis de umbrales**, no como alertas emitidas.

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
- **No evaluable:** evidencia insuficiente.

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
| `tests/test_herramientas.py` + `tests/fixtures.py` | Laptop/Linux | Verificación sin ataques (33 comprobaciones) y fixtures con resultado conocido. |
| `scripts/endpoint_brute/` | srv-dmz | Endpoint 401 correcto (Python o nginx), unidad systemd, README con Suricata/extractor. |
| `capturar.sh` | Sensor | Captura PCAP continua sin huecos a disco archivado, con rotación por tamaño; marca inicio/fin. |
| `modo_sombra.sh` / `restaurar_enforcement.sh` | Bastión→srv-dmz | Pone el agente en dry-run para A y lo restaura para B; verifica sets vacíos. |
| `analizar.py` | Laptop/sensor | Lee `marcas.jsonl` + `motor_decision.log` + features/scores; produce categorías D/P/N/NE, emitidas vs derivadas y la Tabla 8. Reutiliza la lógica de `../4.2-ablacion/aporte-componentes-r2-2026-10-26/evaluar_r2.py`. |
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
2. srv-dmz: `modo_sombra.sh --ejecutar` (detiene el agente, vacía sets, verifica). Sensor: comprobar `ppi-motor` sin `--enforce`.
3. Control normal ≥ 30 min (tráfico legítimo) y arranque/calentamiento del motor registrados.
4. Kali: `generar_campana.py --config ../escenarios/escenarios.json --salida-dir ./corrida --autorizado`.
5. Al terminar: parar `capturar.sh`; recoger `marcas.jsonl`, `salidas/`, PCAP, EVE, `motor_decision.log`.

**Restauración (obligatoria tras A, antes de B):**
1. srv-dmz: `restaurar_enforcement.sh --ejecutar` (reactiva el agente al estado previo exacto).
2. Verificar enforcement activo (`journalctl -u ppi-enforce-agent`).

**Análisis (sin tráfico):** `analizar.py --marcas … --motor … --control "desde,hasta"` → Tabla 8, categorías,
emitido/derivado, control FPR y calidad de datos.

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
2. **Modo sombra**: poner el agente de srv-dmz en dry-run (o parar el publicador) y verificar sets vacíos. Revertir tras A.
3. **Zona DNS de laboratorio**: el resolutor 10.10.10.20 reenvía a Internet; hace falta una zona/dominio reservado que
   resuelva localmente y no consulte a terceros.
4. **Endpoint de fuerza bruta**: no existe (`/login` → 404, 8081 cerrado); preparar un servicio aislado que devuelva 401.
5. **Captura continua y disco**: el anillo recicla cada ~19 min y quedan 21 GB; prever archivado sin huecos y espacio.
6. **Encender la Kali** para la campaña (ahora está encendida; confirmar en el momento).

Nada de esto se ejecuta aquí. La campaña A se lanza con la siguiente instrucción.
