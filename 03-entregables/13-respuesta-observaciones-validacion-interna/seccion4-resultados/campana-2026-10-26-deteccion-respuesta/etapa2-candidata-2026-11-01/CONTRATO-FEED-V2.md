# Contrato del feed v2 y pruebas de aislamiento (Etapa 2, puntos 5 y 6)

Código en la rama `candidato/etapa2-20261101` (hashes en [REFERENCIAS.md](REFERENCIAS.md)):

- `scripts/engine/feed.py` (`construir_v2`, `validar_v2`, `id_entrada`);
- `scripts/engine/publicar_feed_v2.py`;
- `scripts/enforce/agente_enforce_v2.py`;
- `scripts/enforce/cf_nft_helper.py`;
- `deploy/enforcement/relay_eventos.py`.

El v1 desplegado (`publicar_feed.py`, `agente_enforce.py`, `relay-feed.sh`) **no se modifica**.

## 1. Formato (todo firmado)

Se firma el JSON canónico completo (`sort_keys`, sin espacios) con ed25519 (`openssl pkeyutl -rawin`), igual que en v1.

```json
{"version": 2, "emisor": "sensor1", "secuencia": 1842, "generado": 1793522870.1,
 "expira": 1793522930.1, "umbrales": "2026-10-06.2",
 "entradas": [
  {"id": "9f0c…", "ip": "10.10.20.30", "destino": "dc1", "alcance": "dns", "accion": "LIMIT",
   "hasta": 1793523170, "evento_id": "10.10.20.30|2026-11-01T09:01:20+00:00|dns_entropy",
   "motivo": "dns_entropy: …", "detector": "dns_entropy", "nivel": 0, "revisar_humano": false},
  {"id": "41ab…", "ip": "10.10.20.30", "destino": "srv-dmz", "alcance": "todo", "accion": "BLOCK", …}]}
```

| Campo | Regla |
|---|---|
| `version` | Debe ser 2. El agente v2 rechaza el feed v1 entero (`version_no_soportada`). |
| `secuencia` | Crece en cada publicación. Si es menor que la ya aplicada → `secuencia_anterior` (repetición o fuera de orden). Si es igual → `repetido` (no se toca nada). |
| `expira` | Si `expira ≤ ahora` → `feed_caducado`: no se aplica nada nuevo. Lo ya aplicado caduca solo por el timeout nativo de nft. |
| `generado` | Si `generado > ahora + 30 s` → `feed_del_futuro` (reloj o manipulación). |
| `destino` | `srv-dmz` o `dc1`. Cada agente aplica solo su destino; el resto se cuenta como `ajenas`. Un destino desconocido se rechaza. |
| `alcance` | `srv-dmz` admite solo `todo`; `dc1` admite solo `dns`. Cualquier otro par se rechaza (`alcance_no_permitido`). Si falta o no es texto, `alcance_desconocido`. **Una entrada v1 con `alcance: "all"` nunca se reinterpreta como `todo`.** |
| `id` | `sha256(ip|destino|alcance|accion|evento_id)[:16]`. Si no coincide → `id_incoherente`; si se repite → `id_duplicado`. |
| `evento_id` | `entidad|fin_de_ventana|regla`: la decisión del motor que originó la entrada. |
| `hasta` | Debe ser mayor que `ahora` y no superar `ahora + 3720 s` (tope de la escalera más margen). |

## 2. Reglas de publicación (candidato)

- **D3 `if_senal`:** una ALERT del IF no restringe. Se escribe en `senales-if.jsonl` con los α que supera (0,05 / 0,03 / 0,01). Con `--politica actual` se reproduce el v1, solo para comparar.
- **Destino por regla:** `dns_entropy` → (dc1, dns, LIMIT). `brute_force`, `port_scan`, `http_abuse` y `auth_failure_heuristic` → (srv-dmz, todo, su acción). El motor candidato registra **todas** las reglas que disparan (`heuristicos`), no solo la más severa. Así una misma ventana puede producir una entrada para cada destino, y las dos coexisten.
- **Sin renovación por reprocesado:** `hasta = logged_at de la decisión + escalera`, calculado una sola vez por `evento_id` y guardado en el estado. Releer la misma decisión no amplía nada. Solo una decisión nueva (otra ventana) puede ampliar o escalar.
- **Escalera por (ip, destino):** BLOCK en srv-dmz y LIMIT en DC1 no comparten contador.
- **NUNCA_BLOQUEAR += 10.10.10.21 (DC2):** la lista existe en el publicador, en el agente y en el helper. DC2 sigue evaluándose, porque el motor no lo excluye: su señal del IF y sus heurísticos se registran.

## 3. Agente y helper

- El agente verifica la firma, ejecuta `validar_v2` y planifica:
  - nunca acorta una caducidad aplicada;
  - un LIMIT no degrada un BLOCK vivo;
  - un BLOCK saca al origen de `limitados`.
- No ejecuta nft: llama a `sudo -n /usr/local/sbin/cf-nft-helper` sin argumentos y le pasa un JSON por stdin.
- El helper valida todo (perfil, operación, set, IPv4 canónica, IPs especiales, NUNCA_BLOQUEAR y timeout entre 1 y 3720) antes de tocar nada. Él mismo construye el texto nft de **su** tabla y lo aplica en una sola transacción.
- Perfil `dmz`: tabla `inet cyberflow_dmz`, separada de la `inet cyberflow` del v1. Perfil `dns`: tabla `inet cyberflow_dns`. Sus reglas solo casan `meta l4proto {udp,tcp} th dport 53` en el hook input. El tráfico saliente de DC1 hacia su reenviador no pasa por ellas.
- LIMIT por origen: set dinámico `tasa_origen` con `update … limit rate over N/second`. Cada origen tiene su propio cubo; el v1 compartía uno.
- Contadores: `counter` en cada elemento de `bloqueados` y `limitados` (paquetes y bytes por origen y acción) y en cada regla (descartes totales por acción).

## 4. Pruebas (todas en el banco aislado, `--network none`)

Imagen `cyberflow-etapa2-banco:2` (`deploy/pruebas-aisladas/Dockerfile`): debian:trixie-slim con nft 1.1.3, la misma versión que DC1, y git 2.47.3. La versión :1 no traía git. Salidas literales en `resultados/`.

| Prueba | Qué demuestra | Resultado |
|---|---|---|
| `tests/test_etapa2_cadena.py` (pytest, 67 casos, nft real como root dentro del contenedor) | Rechazos de versión, caducidad, futuro, secuencias, duplicados, ids, destino y alcance (incluido `all` del v1), NUNCA (DC2); firma que cubre destino, alcance y secuencia; if_senal; destinos simultáneos; no renovación al releer; escalera por destino; reinicio del publicador y del agente; fallo del helper sin avanzar la secuencia; retirada observada; 16 rechazos del helper (incluida la inyección `"} ; flush ruleset"`); ciclo real del helper (crear, caducidad nativa, retirar, desinstalar); relé (solo cambios, reintento ante fallo de comunicación); limpieza D5; convivencia con la tabla del v1 | **67/67 OK** (`resultados/pytest-etapa2.txt`) |
| `tests/test_etapa2_disparo.py` (9 casos) | Fichero abierto que no dispara, disparo por cierre, plazo sin captura, periódico igual al desplegado, troceador con ficheros vacíos, truncados y rotación solo con paquete | **9/9 OK** (mismo fichero) |
| `deploy/pruebas-aisladas/ensayo_netns_dns.py` | Topología netns (servidor DNS en :53 y servicio TCP 389, origen señalado, cliente legítimo, reenviador) y 8 casos C0–C7 | **8/8 PASA** (`resultados/ensayo-netns-dns.json`) |
| `deploy/pruebas-aisladas/ensayo_cadena_eventos.py` | Procesos reales: publicador `--seguir`, relé por eventos (transporte local, sin ssh), agentes dmz y dns con helper y nft. 20 decisiones sintéticas (BLOCK dmz y LIMIT dns alternos); fallo de entrega a dc1 durante los 4 primeros eventos con reintento; reinicio del agente dmz en el evento 10; la misma decisión repetida en el evento 12 | **PASA** (`resultados/ensayo-cadena-eventos.json`): 20/20 confirmadas; decisión repetida → 0 entradas nuevas; 18 errores de entrega a dc1 mientras faltaba el directorio y luego entrega correcta; 0 rechazos. Desde `logged_at`: leído p50 0,13 s; publicado 0,15 s; entregado 1,08 s; aplicado 1,35 s; confirmado p50 1,43 s, máx. 12,7 s (el evento que esperó al reintento de dc1). |

Lectura del ensayo netns (valores de `resultados/ensayo-netns-dns.json`):

- **C1, LIMIT dns:** el origen señalado se queda en unas 6,5 respuestas/s, cerca de N = 5/s más la ráfaga. El legítimo y el 389 del origen señalado quedan intactos.
- **C2, BLOCK dns:** 0 respuestas DNS para el origen señalado, con el 389 intacto.
- **C3:** las consultas del servidor a su reenviador no se ven afectadas.
- **C4:** caducidad nativa sin intervención.
- **C5:** retirada y desinstalación sin restos.
- **C6:** BLOCK dmz corta el 389 del origen señalado y no el del legítimo. Con dos orígenes limitados, cada uno conserva su cupo (496 de 498), así que no comparten cubo.
- **C7:** el agente v2 completo aplica solo la entrada `dc1` (1 ajena) y deja la traza `recepcion → aplicacion → confirmacion`.

**Límites del ensayo:**

- es un servidor DNS de prueba, no Samba;
- el espacio de usuario es nft 1.1.3, el mismo que en DC1, pero el kernel es el del banco (6.18 WSL2), no el de los hosts;
- no hay tráfico real del laboratorio.

**Compatibilidad leída en solo lectura (1-nov, 21:52Z).** El helper usa `destroy`, que necesita nft ≥ 1.0.8 y kernel ≥ 6.3, y sets con `counter`:

| Host | Sistema | nft | Kernel | Python |
|---|---|---|---|---|
| srv-dmz | Ubuntu 24.04.5 | 1.0.9 | 6.8.0-139 | 3.12.3 |
| DC1 | Debian 13 | 1.1.3 | 6.12.96 | 3.13.5 |

Las dos versiones cumplen el requisito sobre el papel, pero no se ha ensayado en esos kernels.

**Batería base del repositorio** (mismo banco, imagen :2): **461 OK y 1 omitida, 0 fallos**.

Con la imagen :1 fallaban 18 pruebas, todas de `tests/test_f1_dataset_builder.py`, porque su fixture ejecuta `git init` y la imagen no traía `git` (`FileNotFoundError: 'git'`). Fallaban igual en 24f8a80 (lista idéntica): era un defecto del banco, no de la candidata. Se corrigió añadiendo git a la imagen y se repitió toda la batería (`resultados/pytest-etapa2.txt`, 2026-11-01T22:40Z). Esas 18 pruebas pasan ahora.
