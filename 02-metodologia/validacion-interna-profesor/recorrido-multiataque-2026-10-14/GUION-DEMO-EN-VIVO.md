# Guion de demo en vivo — CyberFlow (validación interna)

Objetivo: ejecutar ataques desde la Kali y **verlos al instante en el panel**,
explicando el recorrido detección → decisión → respuesta.

> **Tiempos que debes narrar:** el motor **detecta en segundos** (lo ves en
> *Decisiones* y *Alertas* casi al momento). La **respuesta (BLOCK/LIMIT) llega al
> host en ~2 minutos**, porque viaja en un feed firmado que se publica cada 60 s y
> el agente del host lo trae cada 60 s. No es lentitud: es la cadena distribuida.

---

## Paso 0 — Abrir el panel (elige UNA opción)

**Opción A · Panel real (con login):**
```
pwsh C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\ver-panel.ps1
```
Abre `https://127.0.0.1:8788/` → acepta el aviso de certificado autofirmado →
inicia sesión como **admin**. (Necesitas la contraseña de admin.)

**Opción B · Copia sin login (a prueba de balas):**
```
pwsh C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\ver-panel-demo.ps1
```
Abre `http://127.0.0.1:8788/` sin login. Pulsa **"Modo desarrollo"** (arriba a la
derecha) para ver todas las secciones.

> Si no estás seguro de la contraseña, usa la **Opción B**. Muestra el mismo panel
> con los mismos datos en vivo.

## Paso 0.bis — Abrir una consola en la Kali
En otra ventana:
```
ssh -t gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
```
Comprobación previa (que el camino está abierto):
```
nmap -Pn -p80,443 10.10.30.10          # deben salir 80 y 443 "open"
```

---

## Recorrido recomendado (2 ataques en vivo, limpio y sin choques)

El orden importa: el DGA va al **resolutor** (no corta nada); el escaneo **bloquea**
el acceso a la DMZ. Por eso DGA primero, escaneo después.

### 1) DGA / DNS de alta entropía  →  `dns_entropy`  →  **LIMIT**
En la Kali:
```
for i in $(seq 1 80); do r=$(head -c6 /dev/urandom | od -An -tx1 | tr -d " \n"); \
  dig +short ${r}.francos-sac.com @10.10.10.20 >/dev/null 2>&1; sleep 0.5; done
```
En el panel (≈30–60 s después), ve a **Decisiones** y escribe `10.10.20.30` en el
filtro de IP. Qué señalar:
- Filas `LIMIT · dns_entropy` con *"… consultas DNS/60s, … nombres únicos"*.
- La columna **MODELO dice "normal"**: *"el modelo no ve el DGA; el heurístico sí.
  Esta es la razón de tener heurísticos además del modelo."*
- (En **Alertas** también aparece, y marca tanto al atacante como al resolutor.)

### 2) Escaneo de puertos  →  `port_scan`  →  **BLOCK + corte real**
En la Kali:
```
nmap -sT -T4 --max-retries 1 -p 1-3000 --open 10.10.30.10
```
En el panel, en este orden:
- **Decisiones** (filtro `10.10.20.30`): filas `BLOCK · port_scan` *"… intentos/30s,
  0% completados"*, y muchas con **ANOMALÍA DEL MODELO** → *"aquí coinciden la regla
  y el modelo"*.
- **Alertas**: las tarjetas BLOCK con el motivo y la mini-barra de score.
- **Scores**: la barra roja a la izquierda del umbral = la ventana anómala.
- **Bloqueos** (espera ~2 min): `10.10.20.30 · BLOCK · port_scan` **en vigor**, con
  caducidad y nivel de reincidencia. *"El sensor decide; el agente del host aplica
  nftables; esta vista reconstruye del registro y del feed."*

**Prueba del corte** (en la Kali, ~2 min tras lanzar el escaneo):
```
nmap -Pn -p80,443 10.10.30.10          # ahora salen "filtered": la Kali quedó cortada
```
*"Antes del ataque estaban `open`; tras el BLOCK, `filtered`. La respuesta es real."*

> El bloqueo de primera ofensa **dura 5 min y caduca solo**. No hay que tocar nada.

---

## Las otras dos familias (muéstralas con la evidencia grabada)

Flood HTTP (`http_abuse`→LIMIT) y fuerza bruta HTTP (`brute_force`→BLOCK) **cortan el
acceso a la DMZ** igual que el escaneo, así que en vivo competirían por el alcance.
Lo más limpio es enseñarlas con las capturas del documento
[`RECORRIDO-MULTIATAQUE-RESPUESTA.md`](RECORRIDO-MULTIATAQUE-RESPUESTA.md) (imágenes
`30/31/32-http-*`). Ahí se ve la fuerza bruta *"22 req HTTP/60s con 100% de fallo de
auth"* → BLOCK, con el detalle de que el propio ataque se autocortó.

### Si las quieres EN VIVO (opcional, requiere un paso extra)
La fuerza bruta necesita el endpoint de laboratorio en srv-dmz:8081 (ya está
dejado en `/home/adminsrvdmz/endpoint_401.py`). Arráncalo antes:
```
ssh gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \
  'setsid python3 /home/adminsrvdmz/endpoint_401.py --port 8081 >/tmp/ep.log 2>&1 </dev/null &'"
```
Comprueba que escucha:  `nmap -Pn -p8081 10.10.30.10`  (debe salir "open").
- Flood:  `seq 1 250 | xargs -P10 -I{} curl -s -o /dev/null http://10.10.30.10/`
- Fuerza bruta:  `for i in $(seq 1 50); do curl -s -o /dev/null -u admin:mal$i http://10.10.30.10:8081/; sleep 0.4; done`
Ojo: tras el escaneo, la Kali está bloqueada 5 min → o esperas a que caduque, o
haces estas ANTES del escaneo.

---

## Si algo sale raro
- **El panel no abre:** prueba la otra opción (A↔B). Si B dice "address already in
  use", edita `ver-panel-demo.ps1` y cambia `$Inter = 28801` por otro número.
- **El 80 sale `filtered` desde el principio** (antes de atacar): la segmentación
  cambió; avísame.
- **No aparece el BLOCK en Bloqueos:** dale ~2 min (3 ciclos de feed) y refresca.
- **Reincidencia alta:** si repites el escaneo varias veces, el nivel sube; no afecta
  a la demo (solo alarga la caducidad).
</content>
