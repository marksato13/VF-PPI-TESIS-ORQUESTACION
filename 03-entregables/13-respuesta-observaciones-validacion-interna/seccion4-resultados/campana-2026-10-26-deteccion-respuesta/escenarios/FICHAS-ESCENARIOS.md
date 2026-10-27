# Fichas de escenarios

Cinco escenarios. Origen siempre Kali 10.10.20.30. Parámetros en `escenarios.json`. **No ejecutados.**
Las comprobaciones técnicas previas (las de `../COMPROBACIONES-PREVIAS.md`) se marcan con su `episodio_id` propio y se
**excluyen de la evaluación**. ≥ 5 repeticiones por escenario, orden aleatorizado con semilla 20261026.

Cada ficha: objetivo · origen/destino/servicio · comando y versión · tasa/concurrencia/alcance/duración · acción
prevista · evidencia de actividad · cliente legítimo y control · interrupción y limpieza.

---

## 1. DNS inusual

- **Objetivo:** consultas DNS con nombres variables a ritmo controlado; detección por `dns_entropy`.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.10.20, UDP/53.
- **Comando (dig, BIND utils):** bucle de 90 s, `dig +time=1 +tries=1 @10.10.10.20 "$(openssl rand -hex 8).${ZONA_LAB}" +short`, `sleep 0.4` (~2,3 consultas/s).
- **Tasa/alcance/duración:** ~2,3/s, 90 s, nombres aleatorios dentro de una **zona de laboratorio reservada**.
- **Acción prevista:** LIMIT. 10.10.10.20 está en `NUNCA_BLOQUEAR` y sin agente → **solo detección**, no contención en ese destino.
- **Evidencia de actividad:** conteo de consultas en `marcas.jsonl`; eventos `dns` en `eve.json`.
- **Control:** un cliente legítimo resolviendo nombres normales del laboratorio en paralelo.
- **Interrupción/limpieza:** el bucle termina solo a los 90 s; no deja estado. **Bloqueo previo:** la zona debe resolver local y no consultar a terceros (hoy el resolutor reenvía a Internet).

## 2. Inundación HTTP

- **Objetivo:** peticiones repetidas a un recurso de prueba; detección por `http_abuse` o anomalía del modelo.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP/80.
- **Comando (curl):** bucle de 90 s de `curl -s -o /dev/null --max-time 2 http://10.10.30.10/`, con **concurrencia fija 8** (8 bucles en paralelo; `timeout_s` 150).
- **Tasa/concurrencia/duración:** concurrencia 8, `max_time` 2 s, 90 s. Valor fijado de antemano, no ajustado al detector.
- **Acción prevista:** LIMIT (rate 100/s, reversible).
- **Evidencia de actividad:** conteo de peticiones en `marcas.jsonl`; eventos `http` en `eve.json`. El `/` devolvió 200 el 26-oct.
- **Control:** cliente legítimo navegando el recurso a ritmo normal.
- **Interrupción/limpieza:** termina a los 90 s; sin estado.

## 3. Escaneo breve

- **Objetivo:** barrido TCP de rango fijo, con su **duración natural** (no se prolonga para asegurar detección).
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP 1–1000.
- **Comando (nmap):** `nmap -sT -T4 --max-retries 1 -p 1-1000 10.10.30.10`.
- **Alcance/duración:** 1000 puertos; la duración la fija nmap. Se registran la **duración del comando** y los **SYN efectivos** que cruzan el espejo.
- **Acción prevista:** BLOCK (`port_scan`) si la actividad llega al sensor.
- **Evidencia de actividad:** salida de nmap (puertos) + SYN en el PCAP.
- **Control:** cliente legítimo abriendo conexiones normales al servicio.
- **Interrupción/limpieza:** nmap termina solo. **Nota:** muchos puertos pueden ir filtrados por el cortafuegos y no cruzar el espejo (hallazgo del 1-oct); se registra qué llegó.

## 4. Escaneo sostenido

- **Objetivo:** barrido TCP de alcance amplio y ritmo definido, para mantener actividad más tiempo.
- **Origen → destino / servicio:** 10.10.20.30 → 10.10.30.10, TCP 1–65535.
- **Comando (nmap):** `nmap -sT -T4 --max-retries 0 --max-rate <R> -p- 10.10.30.10`, con `<R>` fijado antes.
- **Alcance/ritmo/duración:** 65 535 puertos a `<R>` paq/s; la duración resulta del alcance y el ritmo.
- **Acción prevista:** BLOCK (`port_scan`, rama de ráfaga ≥ 200 intentos/30 s).
- **Evidencia de actividad:** salida de nmap + SYN en el PCAP; duración del comando y SYN efectivos.
- **Control:** igual que el 3.
- **Interrupción/limpieza:** nmap termina solo. `<R>` no se ajusta según el detector.

## 5. Fuerza bruta HTTP

- **Objetivo:** intentos de autenticación fallidos con credenciales ficticias; detección por `brute_force`.
- **Origen → destino / servicio:** 10.10.20.30 → **endpoint de autenticación de prueba en srv-dmz** (pendiente de preparar).
- **Comando (curl):** bucle de 90 s de `curl -u fake:fake$RANDOM http://10.10.30.10:<PUERTO>/<ruta-auth>`, registrando el código.
- **Respuesta esperada:** **401 verificable**. No confundir 404 ni errores de conexión con fallo de autenticación.
- **Acción prevista:** BLOCK (`brute_force`: ≥ 5 req/60 s con ≥ 80 % de 401/403).
- **Evidencia de actividad:** conteo de 401 en `marcas.jsonl` y en el log del endpoint.
- **Control:** un login legítimo correcto (200) en paralelo.
- **Interrupción/limpieza:** el bucle termina a los 90 s; el endpoint de prueba es un servicio aislado que se detiene al final.
- **Bloqueo previo:** **no existe el endpoint** (`/login` → 404, 8081 cerrado). Hay que prepararlo (servicio aislado que
  devuelva 401). Su preparación reproducible se entrega en `../scripts/endpoint_brute_prueba.md`.
