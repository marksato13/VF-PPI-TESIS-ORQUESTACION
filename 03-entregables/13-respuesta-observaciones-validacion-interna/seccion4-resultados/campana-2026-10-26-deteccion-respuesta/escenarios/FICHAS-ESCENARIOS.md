# Fichas de escenarios

Cinco escenarios. Origen siempre Kali 10.10.20.30. Parámetros en `escenarios.json` (fuente única; esta ficha la
describe y no la sustituye). Las comprobaciones técnicas previas (las de `../COMPROBACIONES-PREVIAS.md`) se marcan con
su `episodio_id` propio y se **excluyen de la evaluación**. 5 repeticiones por escenario (25 episodios), orden
aleatorizado con semilla 20261026, 60 s de calentamiento inicial, 120 s de contexto previo y 90 s de observación
posterior por episodio.

Cada ficha: objetivo · origen/destino/servicio · comando · tasa/concurrencia/alcance/duración/timeout · acción
prevista · evidencia de actividad · cliente legítimo y control · interrupción y limpieza.

> **Actualizada el 2026-10-28** para que coincida con la configuración vigente (`escenarios.json` sha256
> `67798012cbd306e9…`, igual en la Kali). Solo cambia el texto: no cambia ningún parámetro, escenario ni la lógica
> del detector. Sustituye los marcadores `${ZONA_LAB}`, `<R>`, `<PUERTO>` y `<ruta-auth>` de la versión del 26-oct
> por los valores que se fijaron después, y retira los dos bloqueos previos ya resueltos (zona DNS y endpoint).

## Estado: qué está hecho y qué está pendiente

| | Preparación ya realizada (no es resultado de detección) | Pendiente: se mide en la campaña A |
|---|---|---|
| DNS inusual | Zona local `lab-ppi` en el DC1 con comodín `*` → 10.10.30.10; resuelve local, sin salida a Internet (27-oct, `../infra-2026-10-27/`). El sensor recibe eventos `dns` y el acumulador calcula `dns_query_count_60s` y `unique_dns_name_ratio` (`../evidencia-entorno-2026-10-27/03-telemetria.txt`). Nombre único resuelto el 28-oct a las 23:19 UTC. | Si alguna configuración lo detecta, cuándo y con qué atribución |
| Inundación HTTP | `http://10.10.30.10/` responde 200 (26-oct y 28-oct a las 23:19 UTC) | Ídem |
| Escaneo breve | Kali → srv-dmz alcanzable; el motor puntúa el tráfico de la Kali | Ídem, y cuántos SYN cruzan el espejo |
| Escaneo sostenido | Ídem; `max_rate` fijado en 1500 antes de la campaña, sin ajustarlo al detector | Ídem |
| Fuerza bruta HTTP | Endpoint `10.10.30.10:18081/auth` (servicio aislado `ppi-brute-lab`). Sin credencial devuelve 401 (28-oct, 23:19 UTC). Cadena pfSense → Suricata (`detection-ports` 80,18081) → extractor confirmada el 27-oct, con `http_auth_failure_ratio_60s > 0` | Ídem, y la proporción real de 401 en la campaña |
| Todos | Generador simulado sin `--autorizado` el 28-oct a las 23:44 UTC: 25 episodios, 5 por escenario, comandos y orden iguales al repositorio (`../simulacion-2026-10-28/`) | Ejecución real (prompt 2), en un directorio distinto del de la simulación |

Nada de la columna izquierda anticipa una detección: solo muestra que el tráfico llega y que la telemetría lo ve.

---

## 1. DNS inusual

- **Objetivo:** consultas DNS con nombres variables a ritmo controlado; detección por `dns_entropy`.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.10.20, UDP/53.
- **Comando (dig, BIND utils):** bucle de 90 s, `dig +time=1 +tries=1 @10.10.10.20 "$(openssl rand -hex 8).lab-ppi" +short`, `sleep 0.4` (~2,3 consultas/s). Imprime `intentos=<N>` al final.
- **Tasa/alcance/duración/timeout:** ~2,3/s, 90 s, nombres aleatorios dentro de la zona de laboratorio `lab-ppi`; `timeout_s` 150.
- **Acción prevista:** LIMIT. 10.10.10.20 está en `NUNCA_BLOQUEAR` → **solo detección**. En la campaña A (modo sombra) ninguna acción se aplica: solo se registra la propuesta.
- **Evidencia de actividad:** conteo de consultas en `marcas.jsonl`; eventos `dns` en `eve.json`. Con el comodín `nxdomain_ratio` = 0; la señal va por unicidad de nombres.
- **Control:** un cliente legítimo resolviendo nombres normales del laboratorio en paralelo.
- **Interrupción/limpieza:** el bucle termina solo a los 90 s; no deja estado.

## 2. Inundación HTTP

- **Objetivo:** peticiones repetidas a un recurso de prueba; detección por `http_abuse` o anomalía del modelo.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP/80.
- **Comando (curl):** bucle de 90 s de `curl -s -o /dev/null --max-time 2 http://10.10.30.10/`, con **concurrencia fija 8** (8 bucles en paralelo). Imprime `intentos=<N>`.
- **Tasa/concurrencia/duración/timeout:** concurrencia 8, `max_time` 2 s, 90 s; `timeout_s` 150. Valores fijados de antemano, no ajustados al detector.
- **Acción prevista:** LIMIT (rate 100/s, reversible); en la campaña A solo se registra.
- **Evidencia de actividad:** conteo de peticiones en `marcas.jsonl`; eventos `http` en `eve.json`.
- **Control:** cliente legítimo navegando el recurso a ritmo normal.
- **Interrupción/limpieza:** termina a los 90 s; sin estado.

## 3. Escaneo breve

- **Objetivo:** barrido TCP de rango fijo, con su **duración natural** (no se prolonga para asegurar detección).
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP 1–1000.
- **Comando (nmap):** `nmap -sT -T4 --max-retries 1 -p 1-1000 10.10.30.10`.
- **Alcance/duración/timeout:** 1000 puertos; la duración la fija nmap; `timeout_s` 180. Se registran la **duración del comando** y los **SYN efectivos** que cruzan el espejo.
- **Acción prevista:** BLOCK (`port_scan`) si la actividad llega al sensor; en la campaña A solo se registra.
- **Evidencia de actividad:** salida de nmap (puertos) + SYN en el PCAP.
- **Control:** cliente legítimo abriendo conexiones normales al servicio.
- **Interrupción/limpieza:** nmap termina solo. **Nota:** muchos puertos pueden ir filtrados por el cortafuegos y no cruzar el espejo (hallazgo del 1-oct); se registra qué llegó.

## 4. Escaneo sostenido

- **Objetivo:** barrido TCP de alcance amplio y ritmo definido, para mantener actividad más tiempo.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP 1–65535.
- **Comando (nmap):** `nmap -sT -T4 --max-retries 0 --max-rate 1500 -p 1-65535 10.10.30.10`.
- **Alcance/ritmo/duración/timeout:** 65 535 puertos a un máximo de 1500 intentos/s (≥ ~44 s); la duración resulta del alcance y el ritmo; `timeout_s` 900. `max_rate` 1500 se fijó antes de la campaña y no se ajusta según el detector.
- **Acción prevista:** BLOCK (`port_scan`, rama de ráfaga ≥ 200 intentos/30 s); en la campaña A solo se registra.
- **Evidencia de actividad:** salida de nmap + SYN en el PCAP; duración del comando y SYN efectivos.
- **Control:** igual que el 3.
- **Interrupción/limpieza:** nmap termina solo; si supera el timeout, el generador termina su grupo de procesos y marca el episodio como incompleto.

## 5. Fuerza bruta HTTP

- **Objetivo:** intentos de autenticación fallidos con credenciales ficticias; detección por `brute_force`.
- **Origen → destino / servicio:** 10.10.20.30 → **endpoint de autenticación de prueba `10.10.30.10:18081/auth`** (srv-dmz, servicio aislado `ppi-brute-lab`).
- **Comando (curl):** bucle de 90 s de `curl -s -o /dev/null -w "%{http_code}\n" --max-time 2 -u fake:fake$RANDOM http://10.10.30.10:18081/auth`, registrando el código. Imprime `intentos=<N>`.
- **Duración/timeout:** 90 s, un intento tras otro (sin concurrencia), `max_time` 2 s; `timeout_s` 150.
- **Respuesta esperada:** **401 verificable**. No confundir 404 ni errores de conexión con fallo de autenticación.
- **Acción prevista:** BLOCK (`brute_force`: ≥ 5 req/60 s con ≥ 80 % de 401/403); en la campaña A solo se registra.
- **Evidencia de actividad:** conteo de 401 en `marcas.jsonl` y en el log del endpoint (`/opt/brute-lab/brute.log`).
- **Control:** un login legítimo correcto con la credencial de control (`control`, debe dar 200) en paralelo; se comprueba en el control normal.
- **Interrupción/limpieza:** el bucle termina a los 90 s. La preparación reproducible del endpoint está en `../scripts/endpoint_brute/README.md`.

---

## Una sola campaña para las siete configuraciones

Los comandos anteriores se ejecutan **una vez**. IF_0.05, IF_0.03, IF_0.01, HEUR, HIB_0.05, HIB_0.03 y HIB_0.01 se
calculan después sobre las mismas ventanas y puntuaciones de esa única campaña (`../config-campana.json`,
`configuraciones_analisis`). No hay un tráfico distinto por α ni por configuración. El motor en vivo conserva el umbral
desplegado (−0,5693969936322356).
