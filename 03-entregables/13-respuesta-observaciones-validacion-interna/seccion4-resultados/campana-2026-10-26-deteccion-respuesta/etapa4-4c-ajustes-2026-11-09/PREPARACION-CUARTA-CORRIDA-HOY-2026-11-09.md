# Cuarta corrida de la Campaña A: preparación para hoy 09-nov-2026 (NO iniciada)

Preparado a las 19:20Z (14:20 Perú). Todo el arranque, el borrado y el aplazamiento de logrotate esperan la autorización expresa de Mark.

## 1. Estado medido (solo lectura)
- Servicios del Sensor1 activos, `NRestarts=0`. `logrotate.timer` normal: próxima 00:00Z (19:00 Perú); no hay aplazamiento vigente.
- Disco del Sensor1: **3 305 848 832 B libres (92 %)**. Corridas archivadas: 1 664 539 255 + 1 539 943 267 + 1 533 068 754 B. Las tres tienen copia verificada en el bastión (9,0 GB libres).
- Espejo: tras la medición D (35 min, 0 cortes), 120 s de muestreo a las 19:15Z: mínimo 24 pkt/s, media 209, 0 s < 20 pkt/s. **Medición E** (nueva, no unida a las anteriores) iniciada 19:19:25Z; cumple 30 min a las **19:49:25Z (14:49:25 Perú)** sin cortes.
- Sin el borrado, 3,3 GB libres no alcanzan: una corrida de unas 4 h ocupa 2,6–2,9 GB y la rotación de `eve.json` (775 MB, `maxsize 500M`, `copytruncate`) añade un pico de ~0,8 GB.

## 2. ¿Alcanzan los 3,07 GB de las dos corridas más recientes?
Sí: libre pasaría de 3,31 a ≈ 6,38 GB. Restando la corrida (≈ 2,9 GB) y el pico de rotación (≈ 0,8–1,0 GB) quedan ≈ 2,4–2,7 GB (disco ≈ 83 % al final). La corrida 1 permanece en el Sensor1 (original intacto).

## 3. Qué sigue en uso hasta `s40` y qué usa `s50`
- **En uso hasta que `s40` termine (no deben rotarse):** `/var/log/suricata/eve.json` (el vigía lee con cursor; `s30` copia el segmento desde el byte de `eve/inicio.json`; `copytruncate` invalidaría el desplazamiento), `/var/log/suricata/stats.log`, `~/cyberflow/logs/motor_decision.log`, `~/cyberflow/logs/_state/ciclos.jsonl`, `~/feed-v2/*.jsonl` (`via-rapida-resumen`, `traza`, `senales-if`, `senales-rapidas`), el archivador de PCAP y los muestreadores de recursos y salud (escriben en `~/cf-e4/4c`).
- **`s50` solo usa copias:** `~/cf-e4/4c/{copias,archivo-pcap,salud,replay,eve/inicio.json,estado-inicial}` y las herramientas de `~/cf-e4/herramientas` y `~/cyberflow-e4/herramientas-20261106`. No lee los logs vivos, así que la rotación no la afecta **si `s40` ya terminó con `COPIAS COMPLETAS`**.

## 4. Cronograma si `s10` arranca a las 14:50 Perú (19:50Z)
| Hito | Perú |
|---|---|
| Fin de la medición E (30 min seguidos) | 14:49 |
| **`s10`** (c03 v2, c05, s10) | **14:50** |
| I1–I8 con 30 min de muestras, `k01` | 15:20–15:23 |
| `b01`: control de 30 min | 15:28–15:58 |
| I1–I8 e I5 renovados, `g01` v4 (`8f5a5529…`) | ≈ 16:00 |
| Fin de la batería (25 episodios, ≈ 125–130 min) | ≈ 18:05–18:10 |
| `b20`, `s20` (fin + 330 s) | ≈ 18:15 |
| Replay `s30` (≈ 25 min con la captura completa) | ≈ 18:16–18:41 |
| **`s40` terminado** (+ restauración de clientes) | **≈ 18:45** |
| **`s50` terminado** | **≈ 19:10** (19:05–19:20) |

Con la rotación normal de las 19:00, `s40` terminaría solo ≈ 15 min antes. Una pausa como la P3 de hoy (7 min) más cualquier retraso puede dejar la rotación encima de `s30` o `s40`, lo que corrompería la copia de EVE. **Recomiendo aplazarla.**

## 5. Aplazamiento: ¿sirve el mecanismo de la 4B?
Sí. `/usr/local/sbin/cf-4b-rotacion` (v2026-11-08.2, sha `524562a2…`) está instalado y acepta `--fase 4c`. Prueba hecha hoy en solo lectura sobre una corrida 4C archivada: las comprobaciones de estructura pasan (replay rc 0, `cierre.t`, archivador OK, `SHA256SUMS` con 27 ficheros que verifican, imprescindibles, EVE copiado). Los `FALLO` de esa prueba vienen de la **línea base vieja del 8-nov** y de que las fuentes han crecido desde entonces; por eso `armar` **toma una línea base nueva** justo antes de `s10`. Funcionamiento:
1. `armar` guarda la línea base, arma el temporizador de tope y el vigía, **verifica** ambos y solo entonces para `logrotate.timer`; si algo falla, revierte.
2. **Reactivación normal:** el vigía arranca `logrotate.timer` cuando `cierre` y `comprobar` dan OK, es decir, en cuanto `s40` termina bien (≈ 18:45). Al arrancar, logrotate ejecuta la rotación pendiente (con `eve.json` ≈ 1 GB en ese momento: pico de disco a vigilar).
3. **Respaldo automático:** temporizador absoluto de tope. Propongo **01:30Z del 10-nov (20:30 Perú)**, época `1794274200`: si el cierre se retrasa o falla, a esa hora arranca `logrotate.timer` igualmente. Ese tope cubre un `s40` hasta las 20:30 (hasta 1 h 45 min de retraso sobre lo previsto).
4. Revertir a mano: `desarmar`.

## 6. Decisiones que necesito de Mark (en este orden)
1. **Borrado** en el Sensor1 de `/home/m4rk/cf-e4/4c-x3-cancelada-20261109T1350Z` y `/home/m4rk/cf-e4/4c-x3b-cancelada-20261109T1625Z` (3,07 GB), tras repetir justo antes la verificación de SHA-256 de sus copias del bastión. Lo ejecuto yo (los ficheros son de `m4rk`). No se toca la corrida 1.
2. **Aplazamiento con tope 01:30Z.** `[SENSOR1 m4rk]` → **lo ejecutas tú** (necesita sudo con contraseña): `sudo /usr/local/sbin/cf-4b-rotacion armar --tope 1794274200 --fase 4c`. Después yo verifico las unidades y `logrotate.timer` parado.
3. **Orden de arranque** de `s10` (y de la Campaña A en modo sombra con control nuevo, X3 y lista blanca iguales). Vigilancia solo desde el bastión (`estado_bateria_b.sh`), sin sondeos a Kali.

Hora de decisión: para `s10` a las 14:50 Perú, las órdenes 1 y 2 deben estar hechas antes de las ~14:45. Con retrasos, todo se desplaza minuto a minuto: con el aplazamiento, `s10` puede arrancar hasta ≈ 16:00 Perú y `s50` cerraría antes del tope de las 20:30.

## 7. Campaña B: para revisar al cerrar la A
Estado: **no tiene protocolo aprobado**. Solo existe `campana-B-borrador-local-2026-11-08/BORRADOR-B-V2-NO-APROBADO.md` (sin publicar; DB-1 a DB-15 abiertas, DB-3 sustituida por `etapa4-4b-enmienda-p1-2026-11-08/DB-3-PROPUESTA.md`; su cronograma está superado). Al cerrar la A, la revisión será:
- **Evidencia de la A que B necesita:** `t_det` por episodio (retardo espejo/búfer), CPU del Sensor1 con motor + Suricata + detector, y el comportamiento de la vía rápida de escaneo y del umbral `http_abuse` 600 en vivo (la A incluye `escaneo_breve`/`escaneo_sostenido` con `nmap -n`).
- **Puertas de B:** ninguna propuesta `http_abuse`/LIMIT sobre legítimos (DB-11); hash del código desplegado con vía rápida K = 8 y umbral 600; DB-12 (declarar `port_scan_temprano` como regla prevista en E1).
- **Solo mide B:** `t_apl` (transporte SSH real del relé al agente) y E3 (reacción de nmap real a los descartes).
- **Condición nueva por lo ocurrido hoy:** el espejo debe pasar una prueba de 30 min limpios antes de B, y B no se inicia sin esa prueba.
- Nada de B se ejecuta ni se publica sin tu aprobación; las DB abiertas se decidirán una a una.
