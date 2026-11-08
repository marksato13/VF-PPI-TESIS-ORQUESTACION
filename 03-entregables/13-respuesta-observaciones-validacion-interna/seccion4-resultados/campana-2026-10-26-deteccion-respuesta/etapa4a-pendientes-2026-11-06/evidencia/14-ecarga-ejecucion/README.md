# E-carga v2-1, variante r5: ejecución del sábado 7 de noviembre (22:00 Perú, 03:00Z del 8)

Identificador: **`E-carga-v2-1`, variante r5**. Procedimiento: `ecarga-v2-preparacion/PROCEDIMIENTO-ECARGA-v2-VARIANTE-r5.md`
(protocolo `PROTOCOLO-CARGA-v2-r5.md`, `70b945b`). Producto: rama `recuperacion/etapa4a-pendientes-20261106` @ `f3de3fc`
(código `0a794f4`); paquete del bastión `ecarga-bastion-0a794f4` (SHA256SUMS `fa9b4c7b…`).

## Veredicto (tal como sale, rc 1)

`veredicto.json` (evaluador 2026-11-06.4): **estabilidad técnica = «carga insuficiente»**, `habilita_condicion_3 = false`.

| Criterio | Valor | Regla |
|---|---|---|
| K1 paquetes | true (1 080 397) | ≥ 596 789 |
| K2 ráfagas ≥ 5 000 paq/8 s | true (16) | ≥ 9 |
| **K3 flujos grandes** | **false (37)** | ≥ 50 flujos de ≥ 1 000 paquetes |
| K4a perfiles | true | — |
| K5 | true | — |
| S (todas) | sin incumplimientos ni «sin medida». S2, S3, S14 true (Sensor1); S7 true (179/179 entregas aceptadas en orden, 125 lecturas sin retroceso); S11 true; S15 true | §4.4 |
| Clase de captura | C0; Suricata «cero explícito», 1 084 173 paquetes y 0 descartes (0,0/M) | — |

Según el §5 del procedimiento, un veredicto rc 1 se publica tal cual y **no se repite** sin orden nueva y versión nueva del
protocolo. La condición (3) sigue pendiente. La E-carga no produce episodios.

## Cronología

| Hora (Z, 08-nov) | Paso | Resultado |
|---|---|---|
| 07-nov 19:02–19:12 | T1–T3, F0–F3 | traslado VERIFICADO; opción `--forzar-laborable` aplicada por Mark (F2) y comprobada (F3) |
| 00:05–00:35 | Fase A de la **r6** (franja 20:00 Perú) | A0b–A8 conformes; puerta G conforme a las 00:35Z |
| 00:50 | — | **sin orden de arranque a tiempo**: la r6 no pasó de la fase A. Evidencia apartada en `intento-r6-20h/` (SHA256SUMS de 81 ficheros, `MOTIVO.txt`) por `rearmar_r5.sh`, ejecutado por Mark a las 01:13:58Z |
| 02:05–02:31 | Fase A de la r5 | A1–A8 conformes; A8: bastión y Sensor1 ssh rc 0, LIBRE |
| 02:3x | — | orden de arranque de Mark |
| 02:49:30–02:50:46 | B1–B5 | muestreadores ARRANQUE_CONFIRMADO; **P12 CUMPLE** (02:50:06Z); muestreo y guardia del bastión vivos |
| 03:00:00,13 | C1 | `cyberflow-lab.target` arrancado; 6 perfiles running; C1b `FORZAR.vivo` CUMPLE |
| 03:15–04:15 | Ventana fija | la guardia no pidió parada (0 lecturas `parar: true`) |
| 04:17:03–04:17:04 | C4 | parada por fin previsto, confirmada al primer intento |
| 04:18:20 | C5 | `PARADO_CONFIRMADO` rc 0. C5 leyó 12 s antes de que existiera `RESULTADO-PARADA`; relectura en `C5b-relectura-resultado-parada.txt` (confirmada, `comprobacion_final_rc` 0) |
| 04:21–04:22 | Fase R | Mark retiró la opción (`R-revertir-terminal-mark.txt`); `R-forzar-sin` CUMPLE |
| 04:30–04:33 | D1–D6 | post de Sensor1 sellado; D2 (P0 anticipado) rc 0; veredicto rc 1; sellado de `$X` (63 ficheros) |
| 04:33–04:35 | E1–E2 | copia `bastion-X/` verificada; paquete idéntico en los 3 hosts antes y después del ensayo |

## Incidencias

- La franja r6 se perdió por falta de la orden de arranque antes de las 00:50Z, no por un fallo técnico.
- Una protección de la herramienta del asistente bloqueó `rearmar_r5.sh`; lo ejecutó Mark.
- Un aviso de espera del asistente fue detenido por memoria baja del portátil; no afectó a ningún paso.
- C5 se lanzó a 04:18:20Z y `RESULTADO-PARADA` se escribió a 04:18:32Z (al final de la comprobación final); relectura conservada.

## Contenido

`A*` (fase A r5), `B*`, `C*`, `D*`, `E2-*`, `R-*`, `F*`, `T*`, `manual/` (S11 y S15), `bastion-X/` (carpeta completa del
bastión con `SHA256SUMS`, incluidos `veredicto.json`, `entrada-veredicto.json`, `trazabilidad.json` y `post-sensor1/`),
instantáneas `antes-p0-inmediato/`, `despues-p0-inmediato/`, `despues-ensayo/`, e `intento-r6-20h/`. `SHA256SUMS` cubre esta carpeta.
