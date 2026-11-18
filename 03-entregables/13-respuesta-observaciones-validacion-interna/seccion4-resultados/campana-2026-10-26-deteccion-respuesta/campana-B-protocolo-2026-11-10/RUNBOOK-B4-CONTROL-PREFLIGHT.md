# B4 (episodios 7–25): control y preflight — preparativos (11-nov-2026). B4 NO lanzado.

Aprobado por Mark: B4 = corrida nueva (enmienda), `--desde-episodio fuerza_bruta_http-r1` (generador `0705751a…`), `CF_PLANIFICADOS=19`, reporte de B3 y B4 por separado. Reglas duras y hosts: `RUNBOOK-CORRIDA-B-NUEVA-2026-11-11.md` (sin SSH a Kali ni srv-dmz durante el control; vigilancia solo desde el bastión; reversión R0–R7 preparada; `cf-b-fin` a las 8 h). Los scripts operativos usados hoy están copiados en `corrida-2026-11-11\scripts-operativos\` (ejecutor `run_react.ps1 -Hop {local|sensor|kali|srvdmz|clientes} -Script X.sh`).

## Estado de los preparativos (preflight v4: 33 OK, 0 FALLAN, 2 PENDIENTES)
| Elemento | Estado |
|---|---|
| D5 corregido en el bastión (`d5_episodio_banco.py` 58f715e2…) | ✅ desplegado, respaldo `~/cf-b/respaldo-d5/20261111T065343Z-d5-corregido` |
| Generador del tramo en la Kali (`scripts-4c-ii`) + `sha256-esperado-ii.txt` (13 sumas; las listas original e `-i` de B3 siguen verificando) | ✅ |
| `g01d_lanzar_tramo_7_25.sh` (2653d89b…) en `~/cf-b/guiones/` del bastión, `bash -n` OK, exige `CF_PLANIFICADOS=19\|25` | ✅ (no ejecutado) |
| Simulacro en seco en la Kali (sin `--autorizado`) | ✅ el tramo = exactamente B3[6:] (19: 7 `fuerza_bruta_http-r1` … 25 `escaneo_sostenido-r4`), mismo orden y mismos comandos/destino/servicio/timeout que el plan completo, ninguno de los 6 de B3, nonce de prueba ≠ B3; 0 eventos `fin` |
| Evidencia de B3 apartada en los 5 hosts | ✅ (verificado por el preflight) |
| **Ensayo de laboratorio concluyente del D5 corregido** (marca `~/cf-b/prueba-lab-d5-corregido.ok`) | ⏳ **PENDIENTE**: dos ensayos inconclusos (§ resultado en `PLAN-TRAMO-7-25.md` §10); decisión tuya |
| Logrotate diario sobre la auditoría | ⏳ pendiente de observación (próxima 2026-11-12 00:00Z) |

## Secuencia del control y del lanzamiento (≈ 1 h 20 min hasta lanzar; la batería ≈ 2,5–3 h)
Todos como en B3 (comandos exactos en `scripts-operativos\`); `~/cf-e4/4c` no existe en ningún host (B3 apartada).
1. **Preflight v4 en `FASE=pre`** (solo lectura): `prueba-d5-e2e\preflight_tramo_7_25_v4.sh` → sin FALLA.
2. **srv-dmz (lo ejecuto yo, `adminsrvdmz` NOPASSWD):** `ppi-brute-lab` start; **apartar `~/cf-b/set-lecturas.jsonl` de B3 antes de iniciar el muestreador** (`prep_srv.sh` ya lo hace); `cf_d5_instrumentacion.sh srvdmz iniciar --aplicar`; `c05_brute_prep_e4.sh completa` (401/401/200/404).
3. **Sensor1:** espejo de 1 s en `ens37` durante 1.800 s (`esp_start.sh`) + `s10_sensor_archivo_e4.sh 4c`.
4. **Clientes:** `k01_clientes_factor1_tx_e4.sh 4c` (6 perfiles a factor 1,0 con registro por transacción; sin duplicados).
5. **Espejo estricto:** al terminar, 0 s < 20 pkt/s (`esp_an.sh`) y revisar los timestamps (muestras ≈ 1.786 de 1.800: el bucle salta 1 s de reloj cada ~2 min; no hay pérdida si el intervalo máximo es 2 s).
6. **Control de 30 min:** `b01_bastion_control_e4.sh 4c <DESDE> <HASTA> <INICIO_ARCHIVO>` con DESDE ≥ INICIO_ARCHIVO + 230 s, ≥ factor 1,0 + 230 s y en el futuro, HASTA = DESDE + 30 min; `k20_canal_control_simulado.sh 4c <HASTA>`. Sin SSH a Kali/srv-dmz.
7. **Revisión del control y I1–I8** (`i18b.sh`, `i18c.sh`): 0 propuestas / 0 señales rápidas / 0 heurísticos, `clasificar_periodo` C0, relojes ≤ 1 s, verificadores de Sensor1 (umbral α = 0,01), bastión y srv-dmz, NTP de la Kali = 200.25.3.17, 401 del endpoint.
8. **PRE-B** de srv-dmz (`preb.sh`) y `verificar_srvdmz` contra él.
9. **Activación:** `act_real.sh` (`CF_HORAS=8`) y **`CF_PLANIFICADOS=19 bash ~/cf-b/guiones/g01d_lanzar_tramo_7_25.sh <HASTA_CONTROL_ISO> srvdmz-p4-fase-c-20261106T043944Z`**. El ID de B4 será `4c-B4-<UTC>-<12 hex>`.
10. **Monitor:** `monitor-bastion.py` persistente en el bastión (`scripts-operativos\`) + `monloop.ps1` en el portátil (tramos de 10 min). Reversión ante alarma: `b_revertir_srvdmz.sh` (sudo en srv-dmz), `b_r6`, `b_r7`, `clientes_restaurar.sh`.
11. **Cierre:** `b20`, `s20`, `s30`, `s40`, reversión R0–R7 y `analizar_b3.py` adaptado (carpeta de B4).

## Observaciones para B4 que salen de los ensayos
- **El residual depende de las renovaciones:** el agente renueva el LIMIT cada ~20 s mientras el publicador emite la decisión y, por contrato del helper, cada `anadir` a `limitados` **destruye** la entrada de `descartes_limite` del origen. El residual solo sobrevive si hay descartes **después de la última renovación** (en B3 pasó en el episodio 6). Con D5 corregido eso es irrelevante para la puerta (el contador no cuenta), pero explica por qué no se reproduce a voluntad.
- **Antes del control** el feed y el estado del publicador pueden contener a la Kali por el ensayo (entradas `http_abuse` vigentes ≈ 300 s): la primera puerta D5 de B4 las limpia, pero el **control de 30 min debe empezar con el feed sin entradas de la Kali** (el preflight lo debería comprobar: añadir esa comprobación o esperar la caducidad).
