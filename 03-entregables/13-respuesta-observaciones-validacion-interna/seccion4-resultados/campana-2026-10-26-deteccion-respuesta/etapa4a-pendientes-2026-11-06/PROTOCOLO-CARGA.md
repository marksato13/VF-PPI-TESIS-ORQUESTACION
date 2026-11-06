# Protocolo E-carga: estabilidad de la integración en sombra con carga suficiente (propuesto 2026-11-06)

**Estado: propuesto y publicado. NO ejecutado.** No se ha arrancado ningún generador ni se ha abierto ninguna
observación. La ejecución necesita una orden posterior y explícita de Mark. Este documento fija **antes** todo lo que
decide el resultado. Si algo cambia después de publicarlo, se publica una versión nueva con su propio identificador.
La versión anterior se conserva.

Identificador: **E-carga v1 (2026-11-06)**. Se refiere a la medida O12 de la observación fija del 06-nov
([`README.md`](README.md) §8). **No la sustituye ni la reevalúa**: O12 sigue siendo «carga insuficiente».

## 1. Por qué hace falta: lo que se sabe de la carga del 06-nov

| Medida (mismo método: `comparar_suricata.py`, ráfaga ≥ 5 000 paquetes/8 s, flujo grande ≥ 1 000 paquetes) | Base 4A, 04-nov 02:19:45–03:19:51 | Ensayo del anillo, 04-nov 06:26:55–07:26:55 | **Observación 06-nov 04:50–05:50** |
|---|---|---|---|
| Paquetes (Suricata, eventos `stats` de EVE) | 936 761 | 1 193 578 | **584 616** (587 592 con las muestras que acotan la ventana desde fuera, `salud_captura`) |
| Paquetes por 8 s: p50 / p95 / máx | 1 856 / 4 306 / 7 168 | 1 477 / 7 437 / 19 406 | **1 304 / 1 792 / 3 130** |
| pps máximos en un intervalo | 896 | 2 426 | **391** |
| Ráfagas ≥ 5 000 por 8 s | 11 | 68 | **0** |
| Flujos ≥ 1 000 paquetes | 63 | 79 | **0** |
| Flujos de los seis perfiles legítimos (10.10.20.21–26) | — | presentes (.22: 512, .23: 95 y .26: 112 flujos hacia srv-dmz) | **0** |

Fuentes:
- `evidencia/08-carga/intensidad_obs.txt`;
- `evidencia/08-carga/eve_clientes.txt`;
- `../etapa4a-cierre-complementario-2026-11-04/README.md` §6.3.

**Hallazgo.** En la ventana del 06-nov **no funcionaba ningún generador legítimo**:
- Las seis unidades `cyberflow-lab-*` y `cyberflow-lab.target` están `disabled`.
- No se activaron desde que el host de clientes arrancó, el 05-nov a las 23:58:08Z: `ActiveEnterTimestamp` está vacío.
- EVE no tiene ni un flujo con origen 10.10.20.21–26 en la ventana. Solo hay 2 flujos de 10.10.20.20, con 4 paquetes en total.
- Fuentes: `evidencia/08-carga/clientes_ro3.txt`, `clientes_ro4.txt` y `eve_clientes.txt`.

El tráfico que hubo fue el de fondo de la red: AAA, Wazuh, pfSense, el bastión, etc.

Esta comparación muestra la distinción que pide el criterio:
- El **volumen total** del 06-nov fue el 49 % del ensayo.
- Las **ráfagas** y los **flujos grandes** fueron **cero**.
- La **intensidad máxima** fue un 16 % de la del ensayo.

Un volumen parecido no indica la misma demanda. Cumplir solo el umbral de paquetes tampoco habría bastado.

## 2. Decisión: ensayo técnico adicional dentro de la 4A, no integrado en la 4B

**Elección:** E-carga es un **ensayo técnico adicional de la 4A**. Es el último que le falta, y se ejecuta y publica
**antes** de iniciar el control formal de la 4B.

Justificación:
1. **Es una pregunta de la 4A.** La 4A acepta la integración en sombra. La cadena v2 en modo paquete (relé
   `--entrega paquete`, agente `--paquete`), instalada el 06-nov, **nunca ha funcionado con los perfiles legítimos
   activos**. La 4B usará esa misma cadena como instrumento. Si se mide su estabilidad dentro de la 4B, el primer uso
   con carga sería a la vez la prueba del instrumento y la medida del experimento.
2. **Atribución.** Dentro de la 4B, un fallo con carga no se podría atribuir: podría venir de la integración o de
   lo que la 4B añada. Y un resultado favorable de la 4B no debe leerse como aceptación retroactiva de la 4A.
3. **Cabe en el alcance de la 4A.** Solo hacen falta los generadores legítimos que ya existen, sin modificarlos. No
   hacen falta ataques, `--enforce`, `--aplicar` ni cambios de captura o de Suricata. Todo queda en sombra.
4. **Coste bajo.** Son 75 min de laboratorio con las herramientas de la observación del 06-nov, ya probadas.

**Consecuencia para el criterio de avance.** Mientras E-carga no tenga resultado «estable con carga suficiente», la 4B
**puede prepararse, pero no iniciarse**. Así queda en el criterio único del [`README.md`](README.md) §0.

## 3. Diseño, fijado antes de ejecutar

### 3.1 Perfiles legítimos y configuración (sin cambios)

- **Generador:** `~/laboratorio/clientes_lab.py` en el host de clientes (10.10.20.20), sha256 `ae5134a7…` (leído el
  06-nov). Antes de empezar se comprueba ese mismo hash. Si es distinto, no se ejecuta.
- **Perfiles:** los seis, uno por IP:
  - ofimática (.21), navegación (.22), descargas (.23), aplicación (.24), ligero (.25), errático (.26);
  - todos contra srv-dmz 10.10.30.10, con DNS 10.10.10.20;
  - tal como los arranca `cyberflow-lab.target`: `--intensidad` por defecto y curva horaria `factor_horario` **sin
    fijar** (no se usa el envoltorio `clientes_factor1.py`). Son las condiciones del ensayo del anillo.
- **Franja horaria:** la ventana debe caer entera en la franja de madrugada del generador, 23:00–08:00 UTC, de lunes a
  viernes. Es la misma `base` 0,12 que regía en el ensayo del anillo (miércoles 06:26–07:26 UTC). Así la demanda de
  los perfiles es la del ensayo de referencia, no una mayor elegida para superar el umbral.
- **Ninguna acción más** sobre el laboratorio: sin ataques, sin Kali, sin restricciones, sin cambios de captura ni de
  Suricata, y sin reinicios de servicios del sistema.

### 3.2 Tiempos

| Fase | Duración | Qué ocurre |
|---|---|---|
| Comprobación previa (P0) | — | Ver §3.5. Si algo falla, no se arrancan los generadores |
| Arranque de generadores (T_g) | — | `sudo -n systemctl start cyberflow-lab.target` y comprobación de los seis activos |
| Calentamiento | **15 min** (T_g → T_g + 900 s) | Más que el horizonte de historia del motor (230 s) con margen, y tiempo para que los perfiles con ritmo largo (ligero 12 s, descargas 8 s ajustados por la curva) produzcan flujos. Se informa aparte y no cuenta |
| **Ventana** | **60 min fijos** (T_g + 900 s → T_g + 4 500 s) | Se fija en epoch y se publica en `evidencia/` **antes** de T_g. No se corta, no se mueve y no se prolonga |
| Parada de generadores | T_g + 4 620 s | `sudo -n systemctl stop cyberflow-lab.target`. Vuelven al estado de antes (inactivos), salvo que Mark ordene otra cosa por escrito |
| Lecturas posteriores | ≤ 30 min | Verificadores, hashes y análisis (solo lectura) |

### 3.3 Instrumentación (la de la observación del 06-nov, solo lectura)

- **Bastión:** `obs_muestreo.sh` cada 30 s, con Sensor1 y srv-dmz por ssh: PID, `NRestarts`, entregas, aceptaciones,
  rulesets, panel 401 y procesos con `--aplicar`/`--enforce`.
- **Sensor1:**
  - `salud_captura muestrear` cada 10 s;
  - `obs_pcap.py` sobre cada PCAP del anillo en cuanto se cierra;
  - **corrección obligatoria antes de usarlo:** la hora de fin se pasa como **epoch explícito** y se comprueba en seco
    antes de T_g (el 06-nov estaba mal calculada; `sensor1/incidencias.txt`).
- **Recursos:** `muestreo_fino.py` a 1 s: CPU por hilo de Suricata, softirq, iowait, E/S de disco, softnet,
  `MemAvailable`, `/home`.
- **Intensidad:** `comparar_suricata.py` con `--stats-eve` y `--eve` (mismo método y parámetros que en §1).
- **Cobertura de perfiles:** flujos EVE por IP de origen (.21–.26) en cada tramo de 10 min de la ventana.
- **Antes y después:** `verificar_bastion.sh`, `verificar_sensor1.sh` y `verificar_srvdmz.sh` del paquete `a1cea5e`, y
  los hashes congelados de O11.

### 3.4 Carga requerida («carga suficiente»)

La ventana cuenta como **carga suficiente** solo si se cumplen **todas** estas condiciones. Ninguna compensa a otra:

| # | Dimensión | Umbral | Origen del umbral (ya publicado; no se cambia) |
|---|---|---|---|
| K1 | Volumen | ≥ **596 789** paquetes de Suricata en la ventana (eventos `stats` de EVE) | O12 (50 % de 1 193 578), `CRITERIOS-FIJADOS.md` |
| K2 | Ráfagas | ≥ **9** intervalos de 8 s con ≥ 5 000 paquetes | Ensayo del anillo (80 % de la base 4A), `CRITERIOS-ENSAYO-ANILLO.md` |
| K3 | Flujos grandes | ≥ **50** flujos de ≥ 1 000 paquetes | Ídem |
| K4 | Cobertura de perfiles | Los seis orígenes .21–.26 con flujos en **cada** uno de los 6 tramos de 10 min. Errático (.26) con al menos un tramo de ráfaga visible: un intervalo de 8 s en el que su tasa de flujos supere 3 veces su mediana de la ventana | Nuevo, de cobertura. Comprueba que la carga **es** la de los perfiles, no ruido de fondo |
| K5 | Cobertura de la medida | Eventos `stats` sin hueco > 20 s y con bordes a ≤ 10 s; un solo proceso de Suricata | `CRITERIOS-FIJADOS.md` §1 |

Se informan sin umbral, para comparar con §1:
- paquetes por 8 s (p50/p95/máx);
- pps máximos;
- paquetes en flujos grandes;
- volumen por cliente hacia srv-dmz.

**La intensidad se registra, no se elige.** Los generadores no se ajustan durante la ventana.

### 3.5 Comprobación previa P0 (todo solo lectura; si algo falla, no se arranca nada)

1. Los tres verificadores (`a1cea5e`) con **rc 0**.
2. Hashes congelados iguales a los de O11: modelo, manifiesto, esquema, `ec78ca5` y `suricata.yaml`.
3. Sin `--aplicar`/`--enforce`; rulesets de Sensor1 (`24c320e3…`) y srv-dmz (`e3b0c442…`) iguales a los del 06-nov.
4. Generador con hash `ae5134a7…`, los seis servicios inactivos y sin procesos de perfiles vivos (punto de partida
   conocido).
5. Ventana dentro de la franja 23:00–08:00 UTC de un día laborable. `/home` de Sensor1 ≥ 2 GB y `MemAvailable` ≥ 1 GiB.
6. Ventana fijada en epoch y publicada, con su commit, antes de T_g.

### 3.6 Criterios de aceptación

| # | Criterio | Igual que |
|---|---|---|
| S1–S11 | Los mismos O1–O11 de `CRITERIOS-FIJADOS.md`, aplicados a la ventana nueva y sin cambiar ningún valor: continuidad de los 7 servicios, PCAP legibles, salto ≤ 7 s, EVE sin hueco > 20 s, clasificación tal cual, recursos, entregadas = aceptadas en orden, 0 `firma_invalida`/`paquete_invalido`, panel 401, 0 aplicaciones y rulesets iguales, hashes iguales | Observación del 06-nov |
| S12 | Descartes de Suricata medidos (`cero_explicito` o `descartes` con su valor). Una ausencia **no** cuenta como cero | P1 |
| S13 | Descartes por millón **< 14,95** (2 × la base 4A) | Criterio de reversión del ensayo del anillo |
| S14 | Sin saturación nueva de CPU, softirq, disco ni memoria; softnet `dropped` = 0 | Ensayo del anillo |
| S15 | Verificadores con rc 0 después de la ventana | §3 de los criterios |

**Resultados posibles, enunciados tal cual:**
- **estable con carga suficiente:** K1–K5 y S1–S15 se cumplen.
  - La clase de la ventana se informa aparte. Puede ser C0, o C3 si hubo descartes por debajo de S13: en ese caso es
    estable, pero la ventana **no** sirve como población C0.
- **no estable:** K1–K5 se cumplen y falla alguno de S1–S15.
- **carga insuficiente:** falla alguno de K1–K5. No se concluye nada sobre la estabilidad con carga, aunque S1–S15 se
  cumplan.
- **no demostrable:** falta una lectura, o una herramienta falló durante la ventana.

### 3.7 Parada anticipada (protege el laboratorio; la ventana no se repite)

Se paran los generadores, se conserva todo lo medido y el resultado es **no estable** o **no demostrable** si ocurre
cualquiera de estas cosas:
- `MemAvailable` < 1 GiB o `/home` < 2 GB en Sensor1;
- aparece `--aplicar` o `--enforce`, o cambia un ruleset;
- se reinicia un servicio de la cadena;
- `firma_invalida` o `paquete_invalido` sostenidos más de 60 s;
- Suricata deja de escribir EVE más de 60 s.

No se revierte nada automáticamente en los servicios de CyberFlow: el diagnóstico se hace primero y se publica.

### 3.8 Qué se hace ante cada resultado

- **Estable con carga suficiente:** se publica. Se cumple la condición 3 del criterio de avance (`README.md` §0) y la 4B
  queda técnicamente desbloqueada. I5 se sigue exigiendo antes de la 4C, con una lectura propia.
- **No estable:** se diagnostica la causa (solo lectura) y se publica. Cualquier corrección es un cambio nuevo con su
  propio banco y sus propios criterios. Después hace falta **otro** E-carga con identificador nuevo.
- **Carga insuficiente o no demostrable:** se publica tal cual y se explica por qué ocurrió (K1–K5).
  - Un nuevo intento necesita una **orden nueva** de Mark y una versión nueva del protocolo, publicada antes.
  - Esa versión no puede bajar ningún umbral de K1–K5 ni de S1–S15.
  - Ninguna ventana sustituye a otra. Todas se conservan y se citan con su identificador.
- **No se repiten ventanas hasta obtener una favorable.** Cada ejecución es una medida nueva. El informe final
  enumera todas, también las desfavorables.

### 3.9 Recursos y quién ejecuta

| Paso | Máquina | Quién |
|---|---|---|
| P0, instrumentación, análisis, publicación | Bastión, Sensor1, srv-dmz (solo lectura) | Claude |
| Arrancar y parar `cyberflow-lab.target` | Clientes `[CLIENTES adminclientes]`, `sudo -n` (se usó así el 01-nov, `clientes_restaurar.sh`) | Claude, **solo tras la orden de Mark**. Si `sudo -n` pidiera contraseña, lo ejecuta Mark |
| Nada | Sensor1/bastión/srv-dmz con sudo | No hace falta ningún sudo con contraseña |

Duración total: ≈ 15 min de P0 + 15 min de calentamiento + 60 min de ventana + 30 min de lecturas = **≈ 2 h**.

## 4. Lo que E-carga no demostrará

- **Detección oportuna, aplicación de restricciones y efecto real** sobre un ataque o sobre el tráfico legítimo: sin
  ataques y en sombra, el feed no tendrá medidas.
- **I5:** sigue exigiéndose en los 30 min previos al inicio real de la 4C, con una lectura propia en ese momento.
- **La causa de los descartes antiguos** del 03/04-nov.
- **Que la carga de producción esté cubierta:** la referencia es la del laboratorio (ensayo del anillo), no una
  carga real de la red de Francos.
