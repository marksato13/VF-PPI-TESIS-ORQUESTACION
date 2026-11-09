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

## Verificación ampliada (09-nov 04:47–04:50Z = 23:47–23:50 del 8-nov, Perú; solo lectura)

### 1. Bloqueo: el vigía de la 4C se pausaría solo desde el primer permiso
`g01` lanza `vigia_4c.py sensor …` **sin** `--journalctl`, o sea con el valor por defecto `sudo -n journalctl -u ppi-motor-capture …`. El sudoers de `m4rk` solo permite `/usr/bin/journalctl --no-pager *` (con `--no-pager` primero).
Probado en el Sensor1 con la herramienta real (`vigia_4c.py` `62260830…`, carpetas de la 4B, sin escribir):

| Forma | Resultado |
|---|---|
| Como lo lanza `g01` (sin `--journalctl`) | `tcpdump: {"ok": false, "motivo": "journalctl rc=1: sudo: a password is required"}` → sin lectura SIGUSR1 = P4 = pausa; `clasificar_episodios` daría C3 |
| `--journalctl "sudo -n journalctl --no-pager"` | `tcpdump: {"ok": true, "lecturas": [...pid 1355, descartados_kernel 0...]}` |

Es el mismo defecto que dejó vacías las dos extracciones de `s40` (formas `journalctl -u … --no-pager`). **Corrección propuesta (no aplicada): `g01` v2**, con `--journalctl "sudo -n journalctl --no-pager"` en la línea 60, probada en banco y publicada para revisión. Sin ella, no se debe lanzar la batería. Una alternativa (añadir una regla de sudoers) es un cambio de configuración del Sensor1 que no se propone.

### 2. `sudo -n` por host (sonda `sudo -n true` y `sudo -n -l`)
| Host | Resultado |
|---|---|
| srv-dmz `adminsrvdmz` | `sudo -n true` rc 0; `NOPASSWD: ALL` → `respaldo_srvdmz.sh` y `CON_SUDO=1 verificar_srvdmz.sh` pueden ejecutarse sin contraseña (el vigía y `estado_sombra.py --alcance completo` también). Corrijo lo que dije el 8-nov: no exigía contraseña |
| Sensor1 `m4rk` | pide contraseña; solo `journalctl --no-pager *` y `systemctl is-active/show/...` sin contraseña → el respaldo del sensor con `CON_SUDO=1` necesita a Mark |
| Bastión `gadmin` | pide contraseña; solo `NOPASSWD: /usr/local/sbin/respaldo-stream` |
| Clientes | `systemctl daemon-reload` y `start cyberflow-lab.target` sin contraseña |

### 3. `b01`
- Sigue viva la vigilancia de `b01` de la **4B**: `~/cf-e4/4b/vigilar.sh`, PID 980094, 10,9 h de ejecución, una línea por minuto. `b01 4c` no lo bloquea (sus guardas son por carpeta `~/cf-e4/4c`), pero conviene pararla antes (`kill 980094`, solo ese proceso); `b20` de la 4C no la toca.
- Sus campos `tcpdump:` y `drops_sur=` salen vacíos por el mismo `sudo -n journalctl` y por `stats.log` de Suricata 7. No afecta al vigía de la 4C (aparte).
- `b01 4c` exige `DESDE` en el futuro, ≥ `inicio_archivo` + 230 s y duración ≥ 1 800 s; el protocolo pide el archivo abierto ≥ 10 min antes de `desde` y 30 min de muestras para I1–I8.

### 4. Franja (hora de Perú, sin cruzar la rotación)
Próxima rotación: **9-nov 19:00 Perú** (10-nov 00:00Z). Con `S` = apertura del archivo (`s10 4c`), `X` = orden de Mark: `S = X + 30 min`.

| Paso | Hora |
|---|---|
| `s10 4c` (apertura del archivo) | `S` |
| I1–I8 con 30 min de muestras e **I5** | `S + 30` |
| `k01` (factor 1,0) | `S + 31` |
| `b01 4c` (declaración) | `S + 36` |
| `desde` / `hasta` del control | `S + 40` / `S + 70` |
| **I5 inmediatamente antes de `g01`** (ventana 1800 s = el control) y `g01` | `S + 70` / `S + 71` |
| Fin de la batería (≈ 1 h 57 min) | `S + 188` |
| `s20` (fin_ultimo + 330 s) y `s30` | `S + 194` |
| Fin del replay (estimado 20–30 min) y `s40` | `S + 225` |
| Restauración de clientes; laboratorio libre | `S + 230` |

Archivo abierto ≈ 3 h 50 min. **Último inicio que no cruza la rotación:** `S` ≤ 14:55 del 9-nov (`s40` terminado antes de las 18:45), es decir, orden `X` ≤ 14:25.
Ejemplo con `X` = 00:30 del 9-nov: `S` 01:00; I1–I8 01:30; `desde` 01:40; `hasta` 02:10; `g01` 02:11; fin de batería ≈ 04:08; `s20` 04:14; `s40` ≈ 04:50; laboratorio libre ≈ 04:55.
