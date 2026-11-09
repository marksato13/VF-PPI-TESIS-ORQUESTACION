# Ventana viable del martes 10-nov-2026 para la cuarta corrida (no iniciada)

Todas las horas en Perú (UTC-5); entre paréntesis, UTC. Rotación de logrotate: 19:00 Perú (00:00Z). Desfase de duraciones tomado de las tres corridas de hoy.

## Cronograma propuesto
| Hora Perú | Hito |
|---|---|
| 06:45 | Revisión de logrotate tras la rotación de hoy (ver abajo) y estado de disco, servicios y espejo |
| 07:00 (12:00Z) | **Inicio de la prueba del espejo: 30 min seguidos sin cortes** (muestreo de 1 s en `ens37`, umbral < 20 pkt/s). Se evalúa a las 07:30 |
| 07:35 (12:35Z) | **`s10` 4C** (si el espejo pasó y hay espacio): c03 v2, c05, s10 |
| 08:10 | I1–I8 con 30 min de muestras (verificadores de `paquete-a1cea5e`; srv-dmz con sudo, ya autorizado) y `k01` |
| 08:15 | `b01`: control nuevo de 30 min (08:20–08:50) |
| 08:55 | I1–I8 e I5 renovados y `g01` v4 (`8f5a5529…`) |
| ≈ 11:10 | fin previsto de la batería (25 episodios) |
| ≈ 11:25 | `b20`, `s20` |
| ≈ 11:30–11:50 | replay `s30` (≈ 16 min por 2 h de datos; más con la batería completa), `s40`, restauración de clientes |
| **≈ 12:15** | **cierre de `s50`** (estimación +4 h 40 min desde `s10`, con holgura sobre el +4 h 12 min medido) |

Margen hasta la rotación de las 19:00: **≈ 6 h 45 min**. Si hubiera una pausa P3 de unos 10 min, como hoy, o incluso dos, sigue cabiendo con holgura. Hora límite para arrancar `s10` con la holgura mínima de 2 h antes de las 19:00: **≈ 12:00 Perú**; recomiendo no pasar de las 09:00.

## Prueba del espejo antes del arranque
Se hace el martes 07:00–07:30 Perú, no hoy: así el resultado refleja el estado real de la mañana. Si hay un solo segundo por debajo de 20 pkt/s durante los 30 min, la prueba se reinicia (sin unir tramos). Hasta el arranque no se inicia ningún generador.

## Logrotate después de la rotación de hoy (00:00Z = 19:00 Perú)
Datos de hoy (solo lectura): `logrotate.timer` activo, próxima ejecución 00:00Z, la última fue hoy 03:22Z; `eve.json` pesa 775 MB y su regla (`maxsize 500M`, `copytruncate`) lo rotará, copiando 775 MB antes de comprimir (el disco aguanta con 3,1 GB libres, pero en ese instante bajará). Reviso, en este orden, a las 06:45 Perú del martes (o antes si estás en sesión a las 19:05 de hoy):
1. `systemctl status logrotate.service` y su journal de 00:00Z: éxito, sin errores.
2. `/var/lib/logrotate/status`: fechas nuevas para `eve.json`, `motor_decision.log`, `ciclos.jsonl` y `feed-v2/*.jsonl`.
3. Que Suricata sigue escribiendo EVE y con eventos `stats` posteriores a 00:00Z; que `ppi-motor`, `ppi-motor-capture`, `ppi-via-rapida@ens37`, `ppi-publicar-feed-v2` y `suricata` mantienen PID y `NRestarts`.
4. Disco libre tras la rotación y que el cursor de EVE del vigía arranca desde cero con `s10` nuevo.
5. Que el aplazamiento anterior ya no aplica y el timer quedó en su horario normal.

## Disco
Estado hoy: 3,1 GB libres (92 %). Una corrida consume 2,6–2,9 GB y la rotación de EVE añade un pico de ≈ 0,8 GB.

Mayores consumidores del Sensor1 (solo lectura): `~/cf-e4` 7,9 GB (corridas archivadas 4,74 GB), `~/cyberflow` 3,8 GB, `/var/log/journal` 3,3 GB, `/var/log/suricata` 3,0 GB (de los que ≈ 1,6 GB son `eve.json.1-*.backup` antiguos, propiedad de root).

| Opción | Qué toca | Ganancia | ¿Conserva los originales? |
|---|---|---|---|
| A. Borrar de `~/cf-e4` del Sensor1 las dos carpetas ya copiadas y verificadas | `/home/m4rk/cf-e4/4c-x3-cancelada-20261109T1350Z` y `/home/m4rk/cf-e4/4c-x3b-cancelada-20261109T1625Z` | ≈ 3,07 GB | El original sobrevive solo como copia verificada en el bastión |
| B. Copiar también la corrida 1 al bastión (14 GB libres, verificación sha256) y luego A + borrar esa | las 3 carpetas | ≈ 4,74 GB | Igual, con 3 copias verificadas |
| C. Reducir `/var/log/journal` (vacuum) o mover `eve.json.1-*.backup` al bastión | requiere root y cambia el sistema | hasta ≈ 3,3 GB / ≈ 1,6 GB | No toca la evidencia, pero modifica el sistema; lo ejecutaría Mark con sudo |

No existe una forma de ganar espacio sin mover o borrar algo: **comprimir las carpetas en el sitio** sí liberaría espacio (los PCAP comprimen), pero cambia los ficheros originales, así que no lo propongo. La opción menos invasiva para los originales es **B** (copias verificadas antes de cualquier borrado). **Todo borrado queda pendiente de tu autorización**; sin ella, solo haría la copia de la corrida 1 al bastión (que no borra nada) y esa copia no libera espacio por sí sola.
