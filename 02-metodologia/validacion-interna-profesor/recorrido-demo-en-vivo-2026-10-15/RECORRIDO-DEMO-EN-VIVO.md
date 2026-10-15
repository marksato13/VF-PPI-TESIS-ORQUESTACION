# Recorrido de demostración en vivo: ataque → detección → respuesta → reversión

**Uso:** guion para la sustentación. Sigue un ataque real de principio a fin, con
**qué teclear**, **qué explicar** y **qué mirar en la GUI y en el host**, y por qué
cada cosa ocurre cuando ocurre.

**Topología de la demo**
- **Atacante:** Kali `10.10.20.30` (VLAN 20)
- **Objetivo:** srv-dmz `10.10.30.10` (VLAN 30 · DMZ) — el host protegido
- **Detecta y decide:** Sensor `10.10.60.11` (VLAN 60), pasivo por el espejo SPAN
- **Transporta el feed:** VM-GESTION `10.10.10.30` (relay)
- **Aplica la respuesta:** el **agente** en srv-dmz, sobre su propio nftables

> **Idea central que hay que transmitir:** el sensor **observa y decide**, pero
> **no ejecuta**. Publica una **orden firmada** (feed ed25519); cada host la trae,
> verifica la firma y la aplica en su propio cortafuegos. La respuesta **sigue al
> feed en tiempo real**: bloquea mientras hay amenaza y se revierte al cesar.

---

## 0. Punto de partida (antes de atacar)

1. **Panel abierto** (por Tailscale): `https://10.10.60.11:8788/`, sesión admin.
2. **Generadores de tráfico normal parados** → el panel está en PERMIT (limpio),
   para que el ataque se vea sin ruido. *(Por qué: con el tráfico legítimo activo
   se ven los falsos positivos acotados del modelo —LIMIT, nunca BLOCK—; para la
   demo se silencian; ver §8.)*
3. **Dos terminales** abiertas: una en la **Kali** (el ataque) y una en **srv-dmz**
   (verificar el nftables).

**Guion (GUI → Salud / Actividad):**
> *"El sistema en reposo: todo en marcha, sin alertas, todo en PERMIT. Ahora lanzo
> un ataque real desde la Kali."*

---

## 1. El ataque (desde la Kali) — **sostenido**

```bash
# escaneo de puertos SOSTENIDO: repite hasta que lo pares con Ctrl+C
while true; do nmap -sT -T4 --max-retries 1 -p 1-3000 --open 10.10.30.10 >/dev/null 2>&1; echo "escaneo $(date +%T)"; done
```

**Por qué sostenido (justificación):** la respuesta **sigue al feed**, y el feed
lista a una IP **mientras el sensor la ve atacar**. Un disparo único de 20 s
produce un bloqueo que se levanta solo en ~2 min; para **mostrarlo con calma** se
mantiene el ataque en bucle. (En la vida real, un atacante persistente mantiene el
bloqueo; uno que se rinde, lo libera.)

**Guion:**
> *"Un escaneo de puertos sostenido contra el servidor: miles de intentos de flujo
> a muchos puertos, casi ninguno completado. Es un patrón que el tráfico humano
> nunca produce."*

---

## 2. Qué hace el motor (detección) — **inmediata**

El sensor ventanea por IP cada 10 s y decide sobre las variables de la ventana.
Línea real (`logs/motor_decision.log`):

```json
{"decision": "ALERT", "detector_name": "if_recalibrado_2026_09",
 "entity_ip": "10.10.20.30",
 "heuristico": {"accion": "BLOCK", "heuristico": "port_scan",
                "motivo": "34298 intentos/30s a muchos puertos, 0% completados"},
 "score": -0.62, "threshold": -0.568892}
```

**Dos señales a la vez:**
- **Regla `port_scan` → BLOCK:** muchos puertos, ~0 % completados. Patrón inequívoco.
- **Anomalía del modelo (IsolationForest):** `score < umbral` → el modelo, por su
  cuenta, también marca la ventana.

La acción final por IP es la **más severa**: **BLOCK**.

> **Tiempo:** esto aparece en la GUI en **~20-30 s** (casi inmediato). Es la
> **detección**. La **respuesta en el host** tarda más (§3).

---

## 3. La cadena de respuesta (sensor → host) — **~2 minutos**

```
decisión (motor, cada 10 s)
   → publicador: feed FIRMADO ed25519   (ppi-publicar-feed, cada 60 s)
   → relay en el bastión                 (ppi-relay-feed, cada 60 s)
   → agente en srv-dmz: trae y VERIFICA la firma, y SINCRONIZA nftables
                                          (ppi-enforce-agent, pull cada 60 s)
   → nftables en srv-dmz
```

**Por qué tarda ~2 min (justificación):** son dos relojes de 60 s en serie
(publicar + traer). No es lentitud: es el precio de una cadena **distribuida y
firmada** donde el sensor nunca está en línea y cada host aplica por su cuenta.

**Guion:**
> *"La detección es inmediata; la respuesta se propaga por un feed firmado y el host
> la aplica en ~2 minutos. El sensor decide; el host obedece una orden autenticada."*

---

## 4. La visualización en el panel (en orden)

### 4.1 Decisiones — *el registro por ventana* (a los ~20-30 s)
Filtra por `10.10.20.30`: cada ventana con su acción **BLOCK**, el motivo
`port_scan` y el **score frente al umbral** (mini-barra). Exportable a CSV.
> *"Aquí está el registro por ventana: BLOCK, con el motivo y el score. Es la
> evidencia cruda, trazable y descargable."*

### 4.2 Alertas — *lo que el sistema detectó*
Tarjetas **BLOCK · REGLA: PORT_SCAN** y, en las ventanas más densas, **ANOMALÍA DEL
MODELO**.
> *"Dos señales que coinciden: la regla determinista y el modelo."*

### 4.3 Scores — *la mirada del modelo*
La ventana del ataque es la **barra roja** a la izquierda del umbral.
> *"Fuera del rango que el modelo aprendió como normal."*

### 4.4 Bloqueos — *la respuesta efectiva* (a los ~2 min)
`10.10.20.30 · BLOCK · port_scan` **en vigor**, con caducidad y nivel de
reincidencia.
> *"La respuesta aplicada, reconstruida del registro y del feed firmado."*

---

## 5. Verificación **en el servidor objetivo** (srv-dmz)

No es solo el panel: se comprueba en el **propio host**. **Como root/sudo:**

```bash
sudo nft list set inet cyberflow cyberflow_bloqueados
```
Salida (a los ~2 min de iniciar el ataque sostenido):
```
set cyberflow_bloqueados {
    type ipv4_addr
    flags timeout
    elements = { 10.10.20.30 timeout 58m1s expires 57m52s }
}
```

**Guion:**
> *"Aquí, en el cortafuegos del propio servidor, la IP de la Kali está en la regla
> de **drop**. La respuesta es real, aplicada por el host, no una alerta en una
> pantalla."*

**Vista del atacante** (2ª terminal en la Kali):
```bash
nmap -Pn -p80,443 10.10.30.10      # pasa de 'open' a 'filtered'
```

---

## 6. Reversibilidad: el bloqueo **sigue al feed**

**Para el ataque** (en la Kali): `Ctrl + C`.

A los **~2 min**, el sensor deja de ver a la Kali → la **saca del feed** → el agente,
al sincronizar, la **quita del nftables**. El bloqueo **se levanta solo**.

**Dos mecanismos la liberan** (lo que ocurra primero):
1. **Sincronización del agente con el feed** (el principal, ~2 min tras parar): el
   agente hace que nftables coincida con el feed; si la IP ya no está, la borra.
2. **`timeout` del elemento** (red de seguridad): nftables borra el elemento al
   vencer su TTL aunque nadie lo toque. Es el **fail-safe** si el feed dejara de
   publicarse.

**Guion:**
> *"Cuando el ataque cesa, la respuesta se revierte sola: es proporcional, no una
> lista negra permanente. El timeout de nftables es solo una red de seguridad."*

> **Nota sobre el `timeout 58m`:** crece con la **reincidencia** (escalera
> 300 → 1800 → 3600 s en 24 h, `escalada.py`). En una sesión de muchas pruebas sube;
> para una demo limpia conviene resetear el contador y que arranque en 300 s.

---

## 7. Liberar la IP para repetir una prueba

**En orden** (el orden importa):
1. **Kali:** `Ctrl + C` — **para el ataque primero**. *(Si no, el agente la vuelve a
   bloquear al siguiente ciclo, porque el feed sigue viéndola.)*
2. **Espera ~2 min** → se libera sola.
3. **Forzarlo ya** (srv-dmz, como root), si no quieres esperar:
   ```bash
   nft delete element inet cyberflow cyberflow_bloqueados { 10.10.20.30 } 2>/dev/null
   nft delete element inet cyberflow cyberflow_limitados  { 10.10.20.30 } 2>/dev/null
   nft list set inet cyberflow cyberflow_bloqueados     # debe salir SIN elements
   ```

---

## 8. Preguntas frecuentes (ten lista la respuesta)

**«¿Por qué hay alertas si no he atacado?»**
> *"Son los falsos positivos **acotados** del modelo (~4,45 %) sobre el tráfico
> **legítimo** de los clientes, más un artefacto del heurístico DNS sobre el
> resolutor. **Nunca bloquean: solo degradan 5 min (LIMIT)**. El BLOCK se reserva a
> señales inequívocas. Para esta demo paré el generador de tráfico normal para que
> el ataque se vea limpio."*

**«¿Y si el atacante para para evadir el bloqueo?»**
> *"El bloqueo se levanta al cesar, sí, pero mientras ataca está contenido; y cada
> reincidencia **escala** la caducidad (300 → 1800 → 3600 s). Además, el escaneo
> queda registrado y trazable."*

---

## 9. Mejora propuesta: modo **cuarentena**

Hoy la respuesta **sigue al feed**: un ataque corto → bloqueo corto (se revierte al
parar). Es coherente con "respuesta proporcional y reversible", pero deja una
puerta: un atacante que **pulsa y suelta** se libera rápido.

**Mejora (trabajo futuro):** un **modo cuarentena** en el publicador, que mantenga
la IP en el feed hasta que **venza su `timeout` de la escalera** (300/1800/3600 s),
aunque el atacante deje de atacar. Así el bloqueo **dura lo que dice la escalera**,
no lo que dura el ataque. Es un cambio acotado y configurable (una política
`[enforcement] modo = "seguir-feed" | "cuarentena"`), sin tocar el agente ni la
firma.

> Honestidad metodológica: se declara el comportamiento **actual** (seguir el feed,
> con `timeout` como tope) y se propone la cuarentena como mejora medible, no se
> presenta como si ya estuviera.

---

## 10. Resumen del recorrido (quién hace qué, en orden)

| # | Dónde | Comando / acción | Qué demuestra |
|---|---|---|---|
| 0 | GUI · Salud/Actividad | — | estado limpio, en PERMIT |
| 1 | **Kali** | `while true; do nmap -sT -T4 -p 1-3000 --open 10.10.30.10; done` | el ataque |
| 2 | GUI · Decisiones/Alertas/Scores | filtrar `10.10.20.30` | **detección** (~20-30 s): regla + modelo |
| 3 | GUI · Bloqueos | — | la respuesta **decidida** (en vigor) |
| 4 | **srv-dmz** | `sudo nft list set inet cyberflow cyberflow_bloqueados` | la respuesta **aplicada en el host** (~2 min) |
| 5 | **Kali** (2ª term.) | `nmap -Pn -p80,443 10.10.30.10` | el **corte** (open→filtered) |
| 6 | **Kali** | `Ctrl+C` | el ataque cesa → la respuesta **se revierte** (~2 min) |

**La frase que ata todo:**
> *"CyberFlow observa por el espejo, decide, **firma** la orden, y el **propio host**
> la aplica — con una respuesta **reversible** que sigue a la amenaza en tiempo
> real, y un timeout como red de seguridad."*
