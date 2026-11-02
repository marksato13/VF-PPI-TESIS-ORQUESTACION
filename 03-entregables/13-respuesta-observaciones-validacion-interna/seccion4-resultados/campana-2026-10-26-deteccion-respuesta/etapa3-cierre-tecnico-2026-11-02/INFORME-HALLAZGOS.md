# Cierre técnico de la Etapa 3: los tres hallazgos

Cada hallazgo sigue el mismo orden: problema, causa, cambio, evidencia y resultado. Al final de cada uno se separa lo **medido en archivos**, lo **ensayado en el banco** y lo **pendiente en Sensor1**.

---

## 1. Lectura continua de `detector_rapido.py --flujo`

**Problema.** Una ráfaga que produce una señal y llega por la tubería en una sola escritura no se emitía mientras la tubería seguía abierta. Salía al llegar otro paquete o al cerrarse la entrada.

**Causa.** El bucle hacía `select` sobre el descriptor y leía con `sys.stdin.buffer`.

- La primera lectura copiaba al búfer interno de Python todos los bytes disponibles.
- Los paquetes que quedaban en ese búfer **no hacen «legible» el descriptor**, así que `select` esperaba al siguiente byte del kernel.
- En la unidad real el siguiente byte llega casi siempre (el espejo nunca calla), pero en tráfico escaso la señal podía retrasarse sin límite.
- En Windows la rama de `select` no se usaba; por eso las pruebas del portátil no lo veían.

**Cambio** (`scripts/engine/detector_rapido.py`):

- Un hilo lector hace `os.read` sobre el descriptor; esa llamada vuelve en cuanto hay bytes, aunque sean parciales. La marca de llegada se toma al salir de la lectura.
- El bucle principal pasa cada trozo a `AnalizadorPcapIncremental`, que devuelve **todos** los registros completos del búfer propio. Una cabecera o un paquete partido espera al resto sin bloquear.
- **Causalidad intacta:** el reloj del detector sigue avanzando solo con marcas de paquetes. En el tic se llama a `avanzar(det.t)`, nunca con el reloj de pared, y no se adelanta el reloj de evidencia.
- **Tiempos separados:**
  - `t_evidencia`: marca del paquete;
  - `disponible_en`: llegada del trozo de bytes que la completó;
  - `emitido_en`: tras escribir la línea.
- El resumen añade `bytes_pendientes`.

**Evidencia.** `tests/test_detector_rapido_flujo.py` lanza el detector como proceso, con la tubería **abierta**, igual que la unidad.

| Prueba | `585da7b` (Linux) | Corregido |
|---|---|---|
| Ráfaga completa en una sola escritura, tubería abierta | **falla** (0 señales; aparece al cerrar) | pasa |
| Cabeceras y paquetes partidos en trozos de 7 bytes | pasa | pasa |
| Tráfico escaso, cierre de la entrada, CPU < 0,5 s en ~2,5 s | pasa | pasa |
| Sin paquete posterior no hay señal (no se adelanta el reloj); el paquete que resuelve g basta | pasa | pasa |
| Analizador incremental ≡ lector de fichero con cualquier troceo (1, 3, 16, 17, 24, 25, 1000 bytes) | falla (no existe) | pasa |

Tres de las regresiones pasan también en `585da7b`, y se dice así. Con trozos sucesivos o con el paquete que resuelve en otra escritura, cada escritura despierta a `select`, y la versión antigua acababa leyendo. Esas pruebas protegen la corrección (troceo, cierre y no adelantar el reloj). La que reproduce el defecto es la de la escritura única.

**Resultado.**

- **Archivos y pruebas:** resuelto.
- **Banco:** repetida la alternativa C con tráfico escaso y con carga (§1 de `COMPARACION-REFERENCIA.md`).
- **Pendiente en Sensor1:** que la unidad arranque y emita en vivo (procedimiento, paso 1).

---

## 2. Bloqueo por HTTP tardío (`auth_failure_heuristic`)

**Problema.** `auth_failure_heuristic`, el heurístico interno del motor, convertía PERMIT en ALERT con las **columnas del IF** `http_request_count_60s` y `http_auth_failure_ratio_60s`. Esas columnas cuentan también las transacciones que Suricata registra tarde, sin ninguna trama de su flujo en el cable. El publicador convertía después **cualquier** ALERT `*_heuristic` en BLOCK. Así una entidad con 0 peticiones válidas en la vista HTTP podía acabar bloqueada, o ver renovado su bloqueo.

**Causa.** La Etapa 3 movió `brute_force` y `http_abuse` a la vista HTTP (`httph_*`), pero el heurístico interno, que es anterior, siguió leyendo la fila del IF.

**Cambio.**

- `scripts/engine/motor_decision.py`:
  - la condición antigua (fila del IF) se registra como **señal histórica**, `auth_failure.historico`;
  - la **misma** condición (≥ 5 peticiones y ≥ 80 % de 401/403, umbrales sin cambio) sobre la vista HTTP es `auth_failure.vista`;
  - solo `auth_failure.autoriza` (decisión del IF = PERMIT y vista = sí) convierte en ALERT;
  - se añade `decision_if`, la clasificación pura del IF (None si no se puntúa), para separarla de la decisión final.
- `scripts/engine/publicar_feed_v2.py`, defensa en profundidad:
  - un ALERT `*_heuristic` solo produce BLOCK si el registro trae `auth_failure.autoriza`. Si es un registro anterior sin ese campo, se exige que la vista HTTP tenga peticiones válidas suficientes;
  - si no, se traza como evento `rechazada`, sin entrada nueva ni renovación.
- **Sin cambios:** el modelo, el escalador, las 28 características, los 3 α y los umbrales.

**Cambio de decisión final, separado del IF.** Al corregir la heurística interna cambia la decisión final (`decision`) de las ventanas en que solo la señal histórica disparaba: pasan de ALERT a PERMIT. La clasificación pura del IF no cambia, porque scores y vectores son idénticos. El recuento en el 3B está en `COMPARACION-REFERENCIA.md` §3.

**Cambio de contrato declarado.** Dos pruebas anteriores fijaban el comportamiento retirado y se actualizaron a propósito:

- `test_motor_incremental.py::ExtremoAExtremo`: la entidad «solo L7», 401 sin tramas, ya no acaba en `auth_failure_heuristic`; queda con `auth_failure = {historico: true, vista: false, autoriza: false}`;
- `test_etapa2_cadena.py::test_legacy_auth_failure_heuristic_es_block_srv_dmz`: ahora necesita vista; se añade el caso «sin vista → rechazada».

**Evidencia.** `tests/test_auth_failure_vista.py`:

| Prueba | `585da7b` | Corregido |
|---|---|---|
| Solo HTTP tardío → ni restricción nueva ni renovación (también con un BLOCK vigente por evidencia válida) | **falla** (BLOCK) | pasa (`rechazada`) |
| Fuerza bruta vigente con evidencia válida → se conserva la respuesta | pasa | pasa |
| HTTP legítimo con anomalía solo del IF → `if_senal` no restringe; la señal del IF se conserva | pasa | pasa |
| Válida y tardía mezcladas: 3 válidas + 200 tardías → nada; 6 válidas → BLOCK; válidas con ratio bajo → nada | **falla** | pasa |
| Recorrido completo: motor real (`replay_motor`) → registro → publicador → feed **firmado** | **falla** | pasa |

En el recorrido completo hay 4 entidades sintéticas:

- 401 con tramas → BLOCK;
- solo tardíos → nada;
- 3 válidas por minuto más tardíos → nada;
- 7-8 válidas por minuto más tardíos → BLOCK.

El feed verificado contiene exactamente las dos IP con evidencia válida. En ellas `decision = ALERT` y `decision_if = PERMIT`: el cambio es de la heurística, no del IF.

**Resultado.**

- **Archivos y pruebas:** resuelto.
- **Replay del 3B:** `COMPARACION-REFERENCIA.md` §3.
- **Pendiente en Sensor1:** que el registro en vivo traiga `decision_if` y `auth_failure` (procedimiento, paso 1).

---

## 3. Captura de la vía rápida con las VLAN del espejo

**Problema.** La unidad captura con el filtro `tcp`, y el espejo entrega tramas 802.1Q. La batería de la Etapa 3 reinyectaba **sin** etiqueta (`--enet-vlan=del`), así que no comprobaba el comando de captura con VLAN.

**Ensayo** (`deploy/pruebas-aisladas/ensayo_vlan_captura.py`; `resultados/vlan/`). Montaje:

- los 5 escaneos grabados del 3B, en su forma original (13 913 de 13 917 tramas con etiqueta en r1) y sin etiqueta;
- sin doble etiqueta en ninguna muestra;
- tres filtros: `tcp` (unidad `585da7b`), `tcp or (vlan and tcp)` (candidato) y sin filtro;
- fuera de línea con `tcpdump -r`, y en vivo con la **tubería completa** de la unidad (`tcpdump -i vB -n -U --immediate-mode -s 128 -w - <filtro> | detector_rapido.py --flujo`) sobre la veth del contenedor;
- banco: tcpdump 4.99.5, libpcap 1.10.5 (TPACKET_V3), kernel 6.18 (WSL2).

| | Etiquetada, `tcp` | Etiquetada, `tcp or (vlan and tcp)` | Sin etiqueta, ambos |
|---|---|---|---|
| **Fuera de línea** (`tcpdump -r`) | **0 tramas** | 100 % del TCP | 100 % del TCP |
| **En vivo** (comando de la unidad) | 100 % del TCP | 100 % del TCP | 100 % del TCP |

En vivo, en los 5 escaneos y con los dos filtros:

- llegan todos los SYN, SYN-ACK y RST de la muestra;
- libpcap reinserta la etiqueta en lo capturado, que el decodificador ya trata (0x8100 y 0x88A8);
- la deduplicación de copias del espejo y retransmisiones da **las mismas cifras que la referencia leída del fichero** (r1: 195 copias, 8 retransmisiones), con un disparo idéntico;
- tcpdump informa 0 paquetes perdidos por el kernel.

**Causa de que `tcp` funcione en vivo.** En Linux el kernel pasa la etiqueta a metadatos antes de entregar la trama a la captura (`skb_vlan_untag`), y el BPF ve la trama sin etiqueta. Con un fichero, la etiqueta sigue dentro de la trama y `tcp` no encuentra IPv4 en el desplazamiento 12.

**Cambio.** El filtro de la unidad y del banco pasa a `tcp or (vlan and tcp)`:

- en vivo da exactamente lo mismo;
- también acepta la etiqueta dentro de la trama (lectura de ficheros, o una pila que no la extraiga).

Una prueba nueva fija que la unidad y el banco usen el mismo filtro y que compile con la rama 0x8100 (`tcpdump -d`).

**Hallazgos del banco** (no del filtro), corregidos y declarados:

1. **Reenvío del contenedor.** Con `ip_forward=1` (valor por omisión), el banco reenviaba por `vB` unas 6 tramas por segmento sin etiqueta (SYN-ACK con TTL decrementado). La deduplicación las trataba como copias del espejo y no cambiaban los disparos, pero no son del cable. `red()` pone ahora `ip_forward=0`: con eso, la captura sin etiqueta coincide exactamente con la muestra.
2. **Lo que recibe srv-dmz.** En el espejo, los SYN del escaneo hacia srv-dmz están casi todos en la VLAN 20 (≈ 2 010 por escaneo, lado del atacante) y solo 4-5 en la VLAN 30 (lado de srv-dmz, tras el pfSense). La batería sin etiqueta entregaba los ≈ 2 010 a la pila de «srv-dmz», así que el «primer descarte» medido ocurría sobre SYN que el pfSense real ya filtra. La variante nueva **con VLAN** pone la pila de srv-dmz en `vB.30`, de modo que solo recibe la copia de la VLAN 30, mientras la captura escucha todo el espejo etiquetado en `vB`. Resultados en `COMPARACION-REFERENCIA.md` §1.

**Límites declarados:**

- solo se comprobó etiqueta simple: no hay QinQ en el laboratorio (0 tramas con doble etiqueta). Con QinQ, `vlan and tcp` solo cubre una etiqueta dentro de la trama;
- la versión de libpcap y el comportamiento del vNIC de Sensor1 no se han visto: se comprueban antes de instalar (`tcpdump --version` y `tcpdump -d` con el filtro; procedimiento, paso 0);
- no se tocó ningún switch, interfaz ni offload del laboratorio.

**Resultado.**

- **Archivos y banco:** resuelto.
- **Pendiente en Sensor1:** la versión de libpcap y que la captura en vivo vea los SYN (paso 1, en sombra y sin ataques: basta el tráfico normal).

---

## 4. DNS: dos cifras distintas y un protocolo

- **Atacante:** 734 de 1 044 consultas descartadas (≈ 70,3 %) en el banco.
- **Legítimos:** 0 de 428 descartadas en el banco, con unos 3,5 min por episodio. **Favorable, pero no aprueba el límite.**

El protocolo de varios días, con el criterio fijado antes de medir, está en [PROTOCOLO-OBSERVACION-DNS.md](PROTOCOLO-OBSERVACION-DNS.md), junto con TCP/53 y cómo evaluarlo sin bloquear DNS necesario. No se activó nada en DC1 ni se cambió el valor.

## 5. «392 restricciones»

Eran **ventanas de decisión** con disparos heurísticos sobre legítimos (382 de DC1, 4 de 10.10.20.22 y 6 de 10.10.20.26): ni equipos distintos (son 3) ni bloqueos aplicados. DC1 además está en `NUNCA_BLOQUEAR_V2`: el publicador nunca lo restringe. Se corrigió la redacción en `../etapa3-deteccion-temprana-2026-11-02/README.md` y `VALIDACION.md`.
