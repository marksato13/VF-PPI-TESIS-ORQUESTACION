# Matriz de la preparación de la Etapa 4

Estados (los tres del encargo; nada más):

- **Preparado y probado offline:** escrito y ejercitado en el portátil o en el banco aislado, sin tocar el laboratorio.
- **Verificado mediante lectura:** comprobado en el laboratorio solo leyendo (sin reinicios ni cambios).
- **Pendiente:** no se puede cerrar sin ejecutar en vivo o sin sudo de Mark; queda como condición.

| # | Pendiente | Corrección o trabajo | Evidencia | Estado |
|---|---|---|---|---|
| 0 | Versiones de partida | `ec78ca5` (código), `acc6588` (herramientas, en GitHub), `4adfdf2` (docs) y la entrega de la Etapa 3 coinciden; sin cambios posteriores en el código | `git log`, `git ls-remote` (README §1) | Verificado mediante lectura |
| 1.1 | «Sensor1 ejecuta `7b275b8`» | Falso: motor 24f8a80 + cadena v1 as-deployed f57ca00; `~/cyberflow` no es checkout. Avisos en 4 ficheros de la Etapa 3 | ESTADO §1; `procedencia.json` (77 ficheros contra 4 commits) | Verificado mediante lectura |
| 1.2 | Unidades, overrides, comando, intérprete, cwd, rutas | Unidad sin drop-ins, `cmdline`, `exe`, `cwd`, arranque exacto (btime + starttime), sin `--enforce` | `s1_inventario.txt`, `s1_detalle*.txt` | Verificado mediante lectura |
| 1.3 | Disco frente a cargado | mtime/ctime ≤ arranque, `motor_startup`, formato de las decisiones de 24f8a80. Límite: sin prueba criptográfica; `comprobar_importaciones.sh` (`python -v`) para la 4A | ESTADO §1.2; `evidencia/banco/ensayo-unidades-importaciones.txt` | Verificado mediante lectura (lo cargado: evidencia fuerte, no criptográfica) |
| 1.4 | Modelo, escalador, esquema, config, umbral | sha256 del joblib = manifiesto; escalador dentro del pipeline; esquema (solo CRLF); umbral −0,5693969936322356; `cyberflow.local.toml` con umbral y MAC obsoletos que el motor no usa | ESTADO §1.3 | Verificado mediante lectura |
| 1.5 | Publicador, relé, agentes | v1 activo y funcionando (feed de srv-dmz actualizado 19:11:56); agente v1 disabled/inactive; v2 inexistente | ESTADO §3 | Verificado mediante lectura |
| 1.6 | nft de srv-dmz y DC1, `Defaults` de sudoers | Guiones de respaldo con `CON_SUDO=1` | PROCEDIMIENTO §3 | **Pendiente** (sudo de Mark) |
| 1.7 | Respaldo y reversión sin git | Respaldo de unidades, drop-ins, estado y hashes; reversión al contenido copiado y al `is-enabled`/`is-active` del respaldo; orden relé → srv-dmz → sensor | PROCEDIMIENTO §3 y §7; `bash -n` + shellcheck; fases sin sudo probadas | Preparado y probado offline (fases con sudo: pendientes) |
| 2.1 | Pérdida del anillo PCAP | tcpdump SIGUSR1 cada 30 s (`cf-tcpdump-estadisticas.timer`): C/R/D acumulados por PID, cambio de PID = reinicio | `evidencia/banco/ensayo-tcpdump-estadisticas.txt` (`-G`+`-Z`, tubería, R = C + D) | Preparado y probado offline; **línea base en vivo pendiente** |
| 2.2 | Archivador y continuidad | Saltos entre inicios > 7 s y marcas de paquete; el número de PCAP no prueba nada; `calidad_fuentes.py --duracion-pcap 5` | `tests/test_calidad_fuentes_rotacion.py` (4) | Preparado y probado offline |
| 2.3 | Vía rápida (`kernel_drops`) | Corregido: el resumen no tiene ese campo; descartes por su tcpdump SIGUSR1; `bytes_pendientes` ≠ pérdida | SALUD §1, §2.3; aviso en MATRIZ de la Etapa 3 | Preparado y probado offline |
| 2.4 | Suricata con denominadores | `kernel_drops` / `kernel_packets` de `stats.log` por intervalo; 0,16 % en una hora el 2-nov, a ráfagas | ESTADO §2; SALUD §2.4 | Verificado mediante lectura; **diagnóstico S1 pendiente** |
| 2.5 | Sensor frente a SPAN | El SPAN no es visible: solo la cota `retraso_primer_paquete_s` | SALUD §2.7 | **Pendiente** (declarado) |
| 2.6 | Cola y `bytes_pendientes` no son pérdida | Separados en SALUD; el campo ausente queda `null`, no 0 | `salud_captura.py`; `evidencia/salud-en-vivo/` (C3 sin SIGUSR1, como debe) | Preparado y probado offline |
| 2.7 | Criterios fijados antes | C0–C3, I1–I8, P1–P5, X1–X3, evaluabilidad | SALUD §3–4 | Preparado y probado offline |
| 3.1 | 4A | Paquete (82 ficheros, código = ec78ca5), unidades con `systemd-analyze` en contenedor, verificación sin sudo | `evidencia/paquete/`, `evidencia/banco/` | Preparado y probado offline |
| 3.2 | 4B control nuevo | 6 perfiles a factor 1,0; ≥ 2 h (8 h para P2); M1a–M1g separadas; `control_4b.py` | `evidencia/control-4b/` (regresión exacta: 2 644 ventanas; IF 395/254/83; HEUR 92; HIB 466/336/171) | Preparado y probado offline |
| 3.3 | 4C: 25 episodios, 7 configuraciones + vía rápida aparte, α sin elegir | ORDEN-4C (semilla 20261102, orden publicado); `config-campana-4c.json` | `orden_4c.py`, `estimar_duracion_4c.txt` (1 h 56 min; 3B real 6 986,7 s) | Preparado y probado offline |
| 3.4 | 4C: marcas de tiempo distinguidas | generador, tráfico observado, evidencia, disponibilidad, emisión, publicación, entrega, propuesta | PROTOCOLO-4C §3; `referencia_trafico_4c.py` | Preparado y probado offline |
| 3.5 | 4C: escaneo breve contra la ráfaga real | `t_fin_eval` = mín(último SYN, fin del generador), ε 0,01 s; sin tráfico, `no_determinable` | `tests/test_referencia_trafico_4c.py` (5) | Preparado y probado offline |
| 3.6 | 4C: sombra = detección oportuna | Sin `t_apl` ni `t_efecto`; la propuesta no cuenta como respuesta | PROTOCOLO-4C §7 | Preparado y probado offline |
| 3.7 | 4C: planificados / ejecutados / admitidos / excluidos | Definiciones y publicación | PROTOCOLO-4C §8 | Preparado y probado offline |
| 3.8 | Fin de la batería (en el 3B, a mano) | `b20_fin_bateria_e4.sh`: marcas con tres sha256, `fin_ultimo`, relojes y traza del relé | `fin_ultimo` contra el 3B = 1793527325.818114, idéntico al informe | Preparado y probado offline |
| 4.1 | DNS: 734/1 044 frente a 0/428 | Separadas; ninguna aprueba el límite | OBSERVACION-DNS §1 | Preparado y probado offline |
| 4.2 | DNS: TCP/53 y continuidad | TCP/53 limitación declarada; la ausencia de DNS no prueba continuidad (todos los eventos + `stats.log`) | `d01_dns_dia_e4.sh` + `probar_d01_dns.py` | Preparado y probado offline; **observación pendiente** |
| 4.3 | piloto-con-dns | No demostrable por lectura (última fila 30-sep, sin acta) | ESTADO §4 | **Pendiente** (Mark) |
| 5 | Comandos completos con host, usuario, privilegios, esperado y parada | Todos los bloques etiquetados; ningún «…» en comandos | PROCEDIMIENTO, PROTOCOLO-4B/4C, OBSERVACION-DNS | Preparado y probado offline |
| 6 | Publicación y manifiesto | `MANIFIESTO.sha256` de esta carpeta y el regenerado de la Etapa 3, verificados contra los bytes de GitHub | CAMBIOS.md | Preparado (verificación tras el push) |
