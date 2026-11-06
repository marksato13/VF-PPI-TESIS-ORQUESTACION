# Criterios fijados antes de medir: pendientes de la 4A (P1, P4) y observación de integración en sombra

Fijado el **2026-11-06 ~03:55 UTC** y publicado en `main` **antes** de instalar nada y antes de la observación. No se ajusta con los resultados. Si un resultado no los cumple, se conserva tal cual y se dice qué no se puede concluir. **No se repiten ventanas** hasta obtener una limpia.

Código: producto, rama `recuperacion/etapa4a-pendientes-20261106` @ `313f8f8` (base `ce353ef`).

## 1. Criterios de medida nuevos (P1): Suricata por eventos `stats` de EVE

Herramienta `scripts/etapa4/salud_captura.py` VERSION `2026-11-06.1`, `CRITERIOS_EVE`:

| Parámetro | Valor | Razón |
|---|---|---|
| `eve_intervalo_s` | 8 | `stats.interval` del `suricata.yaml` desplegado (`0962ce68…`) |
| `eve_max_hueco_s` | 20 | 2 intervalos + 4 s. Dos muestras más separadas = tramo sin medida |
| `eve_borde_s` | 10 | La muestra que acota cada extremo debe estar a ≤ 10 s fuera del periodo |
| `eve_tolerancia_arranque_s` | 3 | Identidad de proceso: `t − uptime` estable (uptime entero + jitter) |

Estados de la medida de un periodo. Una ausencia **nunca** se convierte en cero:

| Estado | Cuándo | Clase (§3 de SALUD-CAPTURA, sin cambios) | I5 |
|---|---|---|---|
| `cero_explicito` | Cobertura completa, un solo proceso, `kernel_drops` presente en todas las muestras, Δ = 0 | no empeora la clase | **cumple** |
| `descartes` | Igual, con Δ `kernel_drops` > 0 | C1 | no cumple |
| `ausente` | Falta `kernel_drops`/`kernel_packets`/`uptime` en alguna muestra del tramo, o no hay eventos stats | C3 | no demostrable |
| `desactualizada` | La fuente dejó de escribir (última muestra > 20 s antes de «ahora» sin llegar al fin del periodo) o el uptime no avanza | C3 | no demostrable |
| `error_lectura` | Fichero no legible; línea stats corrupta en mitad del fichero; misma hora con valores distintos; contador que decrece sin cambio de proceso | C3 | no demostrable |
| `cobertura_insuficiente` | Sin muestra en `[desde − 10, desde]` o `[hasta, hasta + 10]`; hueco > 20 s; reinicio de Suricata dentro del tramo | C3 | no demostrable (o no cumple si se vieron descartes parciales) |

- **I5 sin cambios.** Solo para iniciar la 4C, se exigen 0 `kernel_drops` en los 30 min previos. Lo nuevo es la fuente: EVE stats en vez de `stats.log`. El periodo termina en la última muestra, que debe tener ≤ 20 s. Solo `cumple` permite iniciar la 4C.
- **C0 sigue siendo la población principal.**
- **El ensayo histórico del 04-nov (06:26:55–07:26:55) sigue siendo C3.** La medida retrospectiva con la herramienta nueva se publica aparte, rotulada como tal, y no lo reclasifica.

## 2. Criterio P4 (entrega feed + firma)

En la cadena publicador → relé → agente, en modo paquete:

- 0 rechazos `firma_invalida` y 0 `paquete_invalido` en la observación;
- todas las secuencias **entregadas** por el relé aparecen **aceptadas** por el agente, en orden;
- la firma ed25519 se sigue verificando en el agente (mismo `feed.verificar`).

## 3. Aceptación de la instalación en sombra

Antes de instalar:

- respaldo sellado y verificable en cada host;
- `ec78ca5` con `SHA256SUMS` OK;
- hashes de modelo, escalador, features y manifiesto anotados;
- `suricata.yaml` `0962ce68…`;
- v1 inactivos (`ppi-publicar-feed.timer`, `ppi-relay-feed.timer`, `ppi-enforce-agent.timer`);
- ningún proceso con `--aplicar` ni `--enforce`;
- ruleset de srv-dmz vacío (sha256 `e3b0c442…`) y ruleset de Sensor1 anotado.

Después de instalar:

- lo mismo;
- relé con `--entrega paquete`, agente con `--paquete`, sin `--aplicar`;
- hashes instalados iguales a los del paquete;
- `verificar_*.sh` sin FALLO.

Cualquier fallo lleva a **reversión** con los guiones de `deploy/etapa4/pendientes/`.

## 4. Observación técnica de integración (≥ 60 min, ventana fija)

- **Ventana.** Empieza **≥ 10 min después** del último reinicio causado por la instalación; el arranque queda fuera. Dura **60 min**, fija: no se recorta ni se desplaza.
- **Tráfico.** Ninguna acción sobre el laboratorio durante la ventana: sin ataques, sin generadores, sin cambios. Solo lecturas cada ≤ 60 s.

| # | Comprobación | Criterio |
|---|---|---|
| O1 | Estabilidad | Ni `ppi-motor`, `ppi-motor-capture`, `ppi-via-rapida@ens37`, `suricata`, `ppi-publicar-feed-v2`, `ppi-relay-eventos` ni `ppi-enforce-agent-v2-dmz` cambian de PID ni de `NRestarts` |
| O2 | Legibilidad de PCAP | Todos los ficheros del anillo que empiezan dentro de la ventana se leen sin error de formato (cabecera y registros completos), incluido el primero de la ventana |
| O3 | Rotaciones | Salto del anillo ≤ 7 s. Si `eve.json` rota en la ventana, se informa |
| O4 | Continuidad EVE | Muestras stats sin hueco > 20 s y un solo proceso de Suricata |
| O5 | Calidad de captura | `clasificar_periodo.py --suricata-eve` sobre la ventana. Se publica la clase **tal como salga**; la herramienta debe dar un estado de Suricata medido (`cero_explicito` o `descartes`) |
| O6 | Recursos | `/home` libre ≥ 2 GB; carga y memoria informadas |
| O7 | Secuencias | Ver §2. Además: secuencias del publicador sin retroceso |
| O8 | Firmas | 0 `firma_invalida` y 0 `paquete_invalido` |
| O9 | Panel | HTTPS responde (401 sin sesión) desde el bastión. El estado del agente se verifica **directamente** en srv-dmz (el panel puede decir «agente desconocido») |
| O10 | Sin aplicaciones | 0 eventos `aplicacion`; ruleset de srv-dmz y de Sensor1 iguales antes y después; sin `--aplicar` ni `--enforce`; v1 inactivos |
| O11 | Congelado | Hashes de detector, modelo, escalador, features y manifiesto iguales antes y después |
| O12 | Carga | **Comparable** si Suricata cuenta ≥ 596 789 paquetes en la ventana (50 % de la hora del ensayo del 04-nov, 1 193 578). Por debajo: «carga insuficiente», y no se concluye nada sobre descartes bajo carga |

Lo que esta observación **no** es: no es la 4B, ni la 4C, ni la campaña B, ni una prueba de eficacia contra ataques.
