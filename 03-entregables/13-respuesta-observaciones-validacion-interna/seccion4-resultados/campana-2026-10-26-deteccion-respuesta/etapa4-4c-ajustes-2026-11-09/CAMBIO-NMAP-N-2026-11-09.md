# Cambio de la 4C: los dos `nmap` llevan `-n` (09-nov-2026)

**Estado:** probado en banco y en el laboratorio, desplegado en la Kali, commit local, **no publicado**. Autorizado por Mark el 09-nov («opción 2»: `-n` en `escaneo_breve`, documentar, actualizar el hash fijado y el manifiesto, probar en banco y revisar los demás episodios de escaneo).

## Por qué (cancelación X3, 09-nov 12:50:26Z)
La segunda batería (g01 v4, lanzada 12:11:39Z) completó 8 de 25 episodios, todos C0, y el vigía la canceló por **X3**: «tráfico de la Kali a 10.10.10.21:53 (dns) durante un episodio». El episodio 8 fue `escaneo_breve-r4` (`nmap -sT -T4 --max-retries 1 -p 1-1000 10.10.30.10`, 12:49:36–12:49:54Z). Sin `-n`, nmap hace una consulta DNS inversa (PTR) del destino a **todos** los servidores de `/etc/resolv.conf` de la Kali (`10.10.10.20` y `10.10.10.21`). La lista blanca del vigía es `10.10.10.20,10.10.30.10`. EVE del Sensor1 entre 12:44 y 12:51Z: 8 flujos UDP/53 a `10.10.10.20` (primero 12:49:42Z) y 8 a `10.10.10.21` (primero 12:49:36Z). El generador se detuvo solo (`generador.rc` 3, «CANCELADA por la vigilancia»). La cancelación es definitiva (SALUD-CAPTURA §4.2): esa corrida se conserva aparte.

La corrida cancelada anterior (X1, 10:06Z) no había llegado a ningún escaneo, por eso no salió antes.

## Qué cambia
- Nuevo `scripts-4c-n/esquema_campana.py` (sha256 `45f743d2ef35f7691ecaa8aeda47eb22445d5a288d2ed559aa30709d14943cee`): solo cambian las dos líneas de `comando_de` de `escaneo_breve` y `escaneo_sostenido` (se inserta `"-n"` tras `"-sT"`) más un comentario. Frente al `esquema_campana.py` de `scripts-4c/` (`e762e604…`).
- Comandos resultantes: `nmap -sT -n -T4 --max-retries 1 -p 1-1000 10.10.30.10` y `nmap -sT -n -T4 --max-retries 0 --max-rate 1500 -p 1-65535 10.10.30.10`.
- `guiones/c03_kali_e4.sh` v2 (sha256 `a6f805e147821fb3cc7a7e459c3d93b12100fe6f0fbea30497a0a36a6f8566fa`): única diferencia de código, el hash fijado de `scripts-4c/esquema_campana.py`. Los demás hashes no cambian: `generar_campana.py` `99e6bdae…`, `escenarios-4c.json` `73c0b204…` (el JSON **no** se toca), y los históricos de `scripts/` (`c586d813…`, `e762e604…`).
- Los archivos históricos del repositorio (`scripts/`, `scripts-4c/`) **no se modifican**: los referencian la 3B, las simulaciones y documentos publicados.

## Alcance (se ha revisado cada escenario de `escenarios-4c.json`)
| Escenario | Herramienta | ¿Consulta el DNS del sistema? |
|---|---|---|
| `dns_inusual` | `dig +time=1 +tries=1 @10.10.10.20 …` | No: servidor explícito, solo `10.10.10.20` |
| `inundacion_http` | `curl http://10.10.30.10/` | No: IP literal |
| `escaneo_breve` | `nmap` | **Sí** (PTR a los dos servidores) → `-n` |
| `escaneo_sostenido` | `nmap` | **Sí**, misma construcción → `-n` (**no estaba en la autorización textual; se aplica por la misma causa y la revisión pedida; Mark puede revertirlo**) |
| `fuerza_bruta_http` | `curl http://10.10.30.10:18081/auth` | No: IP literal |

Efecto sobre el diseño: los episodios de escaneo dejan de generar consultas DNS inversas (antes añadían dos o más eventos `dns` del propio nmap al EVE del episodio). Hay que tenerlo presente al leer el análisis de la 4C; el resto de la campaña (orden, semilla 20261102, tiempos, destinos) no cambia. **X3 y la lista blanca (`10.10.10.20,10.10.30.10`) se mantienen.**

## Pruebas
- Banco (`tests/test_nmap_sin_dns.py`, 8 OK): el esquema histórico sigue intacto; los dos `nmap` llevan `-n` y, quitándolo, son el comando anterior; dig/curl idénticos byte a byte; comandos exactos; diff de código = exactamente 2 líneas; el **generador original** con el esquema nuevo simula (sin tráfico) el plan de 25 episodios con el mismo orden y `-n` solo en escaneos; X3/lista blanca sin cambios; `c03` v2 solo cambia el hash del esquema. **3 mutaciones** (quitar `-n` del sostenido, quitar el `@destino` del dig, `-n` duplicado) hacen fallar las pruebas; fichero restaurado y verificado (`45f743d2…`).
- Laboratorio (`evidencia/x3-y-nmap-n/prueba_dns_nmap.out`, 13:53–13:54Z): `nmap -sL 10.10.30.10` (solo resolución, sin sondas al destino) **sin** `-n` → 8 flujos DNS a `10.10.10.21` y 8 a `10.10.10.20`; **con** `-n` → ningún flujo DNS de la Kali. Reproduce exactamente la causa de X3.

## Despliegue
Kali: `~/cf-campana-A/scripts-4c-previo-e762e604/` (copia `cp -a` del directorio anterior) y `~/cf-campana-A/scripts-4c/esquema_campana.py` = `45f743d2…` (hash verificado antes y después de mover); `generar_campana.py` `99e6bdae…`. `c03` v2 ejecutado a las 13:54:40Z con las seis sumas «La suma coincide».

## Corridas cerradas y conservadas
- `4c-cancelada-20261109T1058Z` (X1, 6 episodios) y `4c-x3-cancelada-20261109T1350Z` (X3, **8 episodios**), en Sensor1, bastión y clientes; Kali `cf-e4-4c-cancelada-20261109T1058Z` y `cf-e4-4c-x3-cancelada-20261109T1350Z`. Cada una cerrada con `b20` v2, `s20` CUMPLE, `s30` (rc 0) y `s40` v3 y archivada **renombrando** (nada borrado). Se analizan aparte de la corrida válida, sin mezclar.
