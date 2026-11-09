# Verificación previa de la Campaña A (4C), solo lectura (09-nov-2026 04:09–04:14Z = 23:09–23:14 del 8-nov, Perú)

**Estado: verificación previa; no se lanzó nada ni se escribió en ningún host. La Campaña A no está autorizada (Mark la autoriza por separado).**

| Comprobación | Resultado |
|---|---|
| Bastión (`verificar_bastion.sh`, sin sudo) | `VERIFICACIÓN BASTIÓN OK` |
| Relojes (`p10b`) | sensor +7,9 ms, Kali +5,2 ms, srv-dmz +6,3 ms, clientes +5,3 ms; los cuatro `|desfase| ≤ 1 s: SI` (criterio de inicio: ≤ 0,1 s, cumplido) |
| Sensor1: servicios | `ppi-motor` (NR 0), captura, vía rápida, publicador v2, Suricata y `cf-tcpdump-estadisticas.timer` `active`; motor **sin** `--enforce` |
| **I5** (0 `kernel_drops` en 30 min, por EVE) | **cumple**: `cero_explicito`, 0 descartes, 226 muestras (`salud_captura.py i5`, rc 0) |
| Kali | sin procesos de `nmap`/`hydra`/generadores (conteo 0), NTP sincronizado, 0 permisos `continuar` |
| Clientes | `cyberflow-lab.target` y las seis unidades `active` (los pone a factor 1,0 `k01` al empezar) |
| `ppi-brute-lab` en srv-dmz | `inactive/disabled` (el protocolo §5.3 lo arranca) |
| Rotación (C12) | `logrotate.timer` activo, próxima a las **2026-11-10T00:00Z (19:00 Perú del 9-nov)**; última ejecución 09-nov 03:22Z (al reanudar tras la 4B). Una 4C de 2 h 45 min–3 h cabe si empieza antes de ≈ 20:00 Perú del 9-nov |
| Disco (I7) | 7,9 GB libres (78 %); el archivo de la 4B ocupa 2,4 GB. Cumple ≥ 2 GB |
| Archivo de la 4C | `~/cf-e4/4c` no existe (`s10 4c` crea la carpeta y abortaría si existiera) |

## Hallazgos y puntos abiertos
1. **Quedó viva la vigilancia de `b01` de la 4B** (bash del bastión, escribe cada minuto en `~/cf-e4/4b/vigilancia.log`). No es un riesgo, pero `b01 4c` lanzaría otra: conviene pararla antes (solo ese proceso; no lo hice).
2. **I1–I8 completos no se pueden dar por cumplidos aún:** I1 e I3–I6 se miden sobre los 30 min posteriores al `s10 4c` y exigen el archivo abierto; I8 exige `CON_SUDO=1 verificar_srvdmz.sh` (sudo de Mark).
3. **Pendientes de Mark antes de empezar** (README §5): C4 y C5 (respaldos frescos del día en sensor, srv-dmz y bastión, con sha256; srv-dmz con `CON_SUDO=1`), y su orden de la 4C.
4. **Escrituras que la campaña hará y que NO se hicieron aquí:** copiar `escenarios-4c.json`, `generar_campana.py` y `esquema_campana.py` a la Kali (§5.2), `c03`, arranque de `ppi-brute-lab` y `c05` (§5.3).
5. **4B abierta:** el análisis `s50` ya está hecho; sus copias y resultados no se han publicado.
6. La causa de las ventanas ausentes en `.23` y `.25` queda sin determinar (ver `DB-3-RESULTADO-4B.md`).
