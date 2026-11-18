# Propuesta de instrumentación para una futura validación de la Campaña B (NO instalada, NO desplegada, 10-nov-2026)

Objetivo: que E3 (inundación) y E4 puedan **evaluarse con los criterios vigentes** en una corrida futura, y que E5 tenga serie continua. Todo es **temporal** (existe solo durante la corrida), de solo escritura local en cada host, sin cambiar el tráfico ni los criterios. Cada pieza se prueba primero en banco; instalarla es una decisión posterior (despliegue y orden de corrida de Mark).

## Por qué hoy no se pueden evaluar (evidencia de la revisión de B2, §45.2decies–45.2undecies)
- **E3 inundación:** la salida del generador es un único total sin hora (`intentos=4181`); el servidor de :80 no registra peticiones; solo el SPAN da SYN/s, y queda por debajo del umbral (38/s frente a 156/s).
- **E4:** los perfiles de clientes solo cuentan `acciones N, fallidas M` cada 200 acciones; el servidor de :80 no registra peticiones; solo hay una reconstrucción indirecta desde el SPAN.

## 1. Intentos del generador con hora (E3)
- **Qué:** un registro por iteración del bucle de la inundación, en la Kali: `t_inicio` (epoch con ns), `t_fin`, `codigo_http` (`000` = sin respuesta/timeout), `t_conexion`. Fichero temporal `/home/adminatacante/cf-e4-4c/intentos-<episodio>.tsv`.
- **Cómo, sin tocar el generador firmado:** el comando de la inundación ya se lanza con `bash -c`; la variante instrumentada es otro comando del escenario (config) que envuelve cada `curl` con `curl -s -o /dev/null -w '%{time_connect} %{http_code}' --max-time 2 …` y añade `date +%s.%N` antes y después. Se declara en `escenarios-4c.json` y se firma como parte de la config de la corrida.
- **Tamaño:** ≈ 40–50 iteraciones/s × 90 s ≈ 4.000–4.500 líneas por episodio (≈ 150 KB); 5 episodios de inundación ≈ 0,8 MB.
- **Cómo permite evaluar E3 con el criterio vigente:** el texto de `OBJETIVOS-Y-CRITERIOS` E3 exige que «consta que el generador siguió intentándolo después de `t_apl` (**SPAN o salida**)». Con este registro, la vía «salida» pasa a tener serie temporal: iteraciones por segundo antes y después de `t_apl`, y su continuidad durante ≥ 5 bloques. **Decisión de criterio (declarar antes de ejecutar, no se cambia aquí):** `analizar_b.py` implementa la vía SPAN con `INTENTO_MIN = 0,5·B0` de SYN; el protocolo lo escribe como «SYN ≥ 50 % de B0 **y** salida». Hay que decidir cuál rige. Con el generador actual (bucle síncrono con `curl --max-time 2`) el propio límite reduce los SYN/s, de modo que la vía SPAN seguiría sin alcanzar el umbral aunque el generador siga iterando; el registro con hora permite demostrar la continuidad por la vía «salida».

## 2. Transacciones de control con hora (E4)
- **Qué:** una línea por acción de cada uno de los seis perfiles: `t_epoch`, `perfil`, `origen` (10.10.20.21–26), `destino`, `metodo`, `ruta`, `codigo`, `latencia_ms`, `intencional` (si el fallo está en el diseño del perfil: 401/404/500 previstos). Ficheros temporales `~/cf-e4/4c/transacciones-<perfil>.tsv` en la VM de clientes.
- **Cómo, sin modificar `clientes_lab.py`:** un envoltorio como el que ya existe (`clientes_factor1.py` fija el factor horario envolviendo `clientes_lab`): `clientes_factor1_tx.py` envuelve el método que ejecuta una acción para escribir la línea. Es el mismo patrón ya usado y revertible parando los procesos.
- **Tamaño:** en B2 los seis perfiles hicieron 13.394 acciones en ≈ 6.700 s (≈ 2 por s en total); en ≈ 2,5 h serían ≈ 18.000 líneas (≈ 1,5 MB).
- **Cómo permite evaluar E4 con el criterio vigente:** E4 = «0 fallos de transacciones de control **atribuibles a una restricción** en [inicio − 60 s, fin_eval + 90 s]». Con el registro: (a) se cuentan transacciones y fallos por episodio y por ventana, con hora; (b) los fallos `intencional = true` se excluyen; (c) **«atribuible»** se define **antes de ejecutar**: un fallo es atribuible si el origen del cliente figura en un set restringido (`bloqueados`/`limitados`) en ese instante según la traza del agente y las lecturas del set (§3); toda restricción es solo sobre 10.10.20.30, así que el criterio es contrastable y no tautológico. Alimenta directamente el campo `control: [{t, ok, atribuible}]` que ya espera `analizar_b.py`. **Deja de ser indeterminado.**

## 3. Evidencia de aplicación y retirada, continua (E2, E5)
- **Lecturas del set cada 2 s en srv-dmz:** un muestreador de solo lectura (`cf-nft-helper listar`, el mismo contrato que usa `d5_episodio.srv_nft`) que escribe `set-lecturas.jsonl` (`t`, `bloqueados`, `limitados` con su `timeout`) en `/var/lib/cyberflow/agente/` o en un directorio de la cuenta de la campaña. Da la **serie continua** que hoy falta para E5 (hoy hay 2 lecturas por episodio) y permite ver la **caducidad natural**.
- **Un episodio con caducidad natural declarada:** repetir un episodio de fuerza bruta con la puerta D5 configurada para **no** retirar la regla, de modo que se observe la caducidad por tiempo (`hasta`) en la serie; los demás conservan la retirada explícita. Es una variante del plan de la corrida (decisión de Mark).
- **Se conserva lo que ya existe y funciona:** traza del agente (`aplicacion`, `confirmacion`, `retirada`, `primer_descarte`), pasos de la puerta (`puertas-D5.jsonl`), auditoría del publicador (`d5-auditoria.jsonl` con retención `rotate 30`, §45.2quinquies).

## 4. Relojes y copias
- **Medición de relojes al inicio y al final de la corrida** (hoy solo al inicio, 17:51:02Z; desfases −3,5 a −7,1 ms) para acotar la deriva en las ≈ 2,3 h; el mismo script del preflight (`relojes-4c.log`).
- **Copia con hash de todo lo temporal al cierre** (como `archivo-pcap-lista`): `intentos-*.tsv`, `transacciones-*.tsv`, `set-lecturas.jsonl`; el `journal` de `ppi-brute-lab` (hoy solo existe en el journal activo) exportado con su sha256.
- **Registro de accesos del servidor de :80 (opcional):** habilitar `log_message` en `servidor_lab.py` cambia un servicio del laboratorio; no se propone salvo decisión expresa. Alternativa sin tocarlo: eventos `http` de Suricata (EVE) si el registro HTTP está activo; **no se comprobó**.

## 5. Qué NO resuelve (pendientes separados)
- **Hallazgo de las ventanas anteriores (reintentos de la puerta, §43 Hallazgo 2):** pendiente aparte. Con la puerta integrada en banco (§45.6) un fallo por ese motivo **bloquea** la puerta y exige reanudación manual en vez de reintentar solo; decidir la espera de la puerta sigue pendiente.
- La clasificación C3 de la corrida y la decisión de desplegar o ejecutar.

## 6. Esfuerzo estimado (tras la decisión)
Envoltorios y muestreador en banco con datos sintéticos y pruebas: ≈ 2–3 h; verificación de que no alteran el tráfico (comparar el SPAN con y sin instrumentación en banco): ≈ 0,5 h; instalación y reversión el día de la corrida: ≈ 0,5 h.
