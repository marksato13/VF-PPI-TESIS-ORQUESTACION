# Recorrido de demostración en vivo: ataque → detección → respuesta → reversión

**Uso:** guion para la sustentación. Sigue un ataque real de principio a fin, con
**qué teclear**, **qué explicar** y **qué mirar en la GUI y en el host**, y por qué
cada cosa ocurre cuando ocurre.

> **⚠️ Actualización post-demo (2026-10-16).** Este guion describe la demo tal como se
> ejecutó el **15-oct-2026**. Justo después se endureció el enforcement y **cambiaron dos
> cosas**: (1) la cadena de respuesta se **escalonó a 10 s** (publicar :00 · relay :03 ·
> agente :06), de modo que la respuesta en el host llega en **~15 s**, no en ~2 min
> (evidencia: `producto-main/docs/evidencias/tiempos-2026-10-15-cadena-10s.md`); y (2) el
> agente pasó a **modo cuarentena**: una vez bloqueada, la IP **permanece bloqueada hasta
> que vence su `timeout`** (escalera 300/1800/3600 s), **aunque el atacante deje de
> atacar** — ya **no** se libera sola al cesar. La mejora que proponía el §9 **ya está
> implementada**. Donde el texto diga "~2 min" o "se revierte al cesar", vale esta nota;
> los §6, §7, §8 y §9 están corregidos abajo.

**Topología de la demo**
- **Atacante:** Kali `10.10.20.30` (VLAN 20)
- **Objetivo:** srv-dmz `10.10.30.10` (VLAN 30 · DMZ) — el host protegido
- **Detecta y decide:** Sensor `10.10.60.11` (VLAN 60), pasivo por el espejo SPAN
- **Transporta el feed:** VM-GESTION `10.10.10.30` (relay)
- **Aplica la respuesta:** el **agente** en srv-dmz, sobre su propio nftables

> **Idea central que hay que transmitir:** el sensor **observa y decide**, pero
> **no ejecuta**. Publica una **orden firmada** (feed ed25519); cada host la trae,
> verifica la firma y la aplica en su propio cortafuegos. La respuesta se propaga por el
> feed: bloquea ante la amenaza y **caduca sola** (vigente: en **cuarentena**, por la
> escalera de reincidencia, no al cesar el ataque; ver §6).

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

**Por qué sostenido (justificación):** mantener el ataque en bucle deja ver **con calma**
toda la cadena —detección por ventana, decisión y respuesta en el host— sin tener que
cronometrar un disparo único. *(Vigente: con la cuarentena, incluso un ataque corto queda
bloqueado y **permanece** hasta su `timeout`; el bucle es por comodidad de la demo, ya no
porque el bloqueo se levante al parar. Ver §6.)*

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

## 3. La cadena de respuesta (sensor → host) — **~15 s (vigente)**

```
decisión (motor, cada 10 s)
   → publicador: feed FIRMADO ed25519   (ppi-publicar-feed, :00/10 s)
   → relay en el bastión                 (ppi-relay-feed, :03/10 s)
   → agente en srv-dmz: trae y VERIFICA la firma, y SINCRONIZA nftables
                                          (ppi-enforce-agent, :06/10 s)
   → nftables en srv-dmz
```

**Por qué ~15 s (justificación):** los tres relojes se **escalonaron a 10 s** (publicar
:00 · relay :03 · agente :06), así que un paso ya no espera al siguiente ciclo. Medido:
decisión→nft **15,3 s**, escaneo→bloqueo **41,4 s**
(`producto-main/docs/evidencias/tiempos-2026-10-15-cadena-10s.md`). Sigue siendo una
cadena **distribuida y firmada** donde el sensor nunca está en línea y cada host aplica
por su cuenta. *(En la demo del 15-oct los relojes eran de 60 s en serie → ~2 min.)*

**Guion:**
> *"La detección es inmediata; la respuesta se propaga por un feed firmado y el host la
> aplica en unos 15 segundos. El sensor decide; el host obedece una orden autenticada."*

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

### 4.4 Bloqueos — *la respuesta efectiva* (a los ~15 s)
`10.10.20.30 · BLOCK · port_scan` **en vigor**, con caducidad y nivel de
reincidencia.
> *"La respuesta aplicada, reconstruida del registro y del feed firmado."*

---

## 5. Verificación **en el servidor objetivo** (srv-dmz)

No es solo el panel: se comprueba en el **propio host**. **Como root/sudo:**

```bash
sudo nft list set inet cyberflow cyberflow_bloqueados
```
Salida (a los ~15-40 s de iniciar el ataque sostenido):
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

## 6. Reversibilidad: contención por **cuarentena** (comportamiento vigente)

**Para el ataque** (en la Kali): `Ctrl + C`.

**Vigente (desde 2026-10-16):** parar el ataque **no** levanta el bloqueo. El agente
opera en **modo cuarentena**: aunque el sensor deje de ver a la Kali y la saque del feed,
el agente **mantiene** la IP en el nftables hasta que **vence su `timeout`** (el de la
escalera: 300 → 1800 → 3600 s según reincidencia). El bloqueo **dura lo que dice la
escalera, no lo que dura el ataque**. Para liberar antes hay que borrar el elemento a
mano (§7).

**El `timeout` es ahora el mecanismo de liberación** (ya no la sincronización con el
feed): nftables borra el elemento al vencer su TTL. El bloqueo sigue siendo **reversible
y proporcional** —caduca solo, no es lista negra permanente— pero su duración la fija la
**política de reincidencia**, no el cese del ataque.

**Guion:**
> *"Una vez contenida, la IP queda en cuarentena: el bloqueo dura lo que marca la escalera
> de reincidencia, aunque el atacante se detenga. Caduca solo —es reversible—, pero no
> premia al que ataca y suelta."*

> **En la demo del 15-oct** el sistema operaba en modo *seguir-feed*: el bloqueo se
> levantaba solo ~2 min después de cesar el ataque. Ese comportamiento se sustituyó por la
> cuarentena descrita arriba.

> **Nota sobre el `timeout 58m`:** crece con la **reincidencia** (escalera
> 300 → 1800 → 3600 s en 24 h, `escalada.py`). En una sesión de muchas pruebas sube;
> para una demo limpia conviene resetear el contador y que arranque en 300 s.

---

## 7. Liberar la IP para repetir una prueba

**En orden** (el orden importa):
1. **Kali:** `Ctrl + C` — **para el ataque primero**. *(Si no, el agente la vuelve a
   bloquear al siguiente ciclo, porque el feed sigue viéndola.)*
2. **Vigente:** parar **no** la libera; en cuarentena la IP sigue bloqueada hasta que
   vence su `timeout` de la escalera (300 s en el primer bloqueo). Para repetir una prueba
   de inmediato, **bórrala a mano** (paso 3).
3. **Forzarlo ya** (srv-dmz, como root):
   ```bash
   nft delete element inet cyberflow cyberflow_bloqueados { 10.10.20.30 } 2>/dev/null
   nft delete element inet cyberflow cyberflow_limitados  { 10.10.20.30 } 2>/dev/null
   nft list set inet cyberflow cyberflow_bloqueados     # debe salir SIN elements
   ```
   *(En cuarentena, el borrado manual es la vía normal para reiniciar una prueba: el
   agente no lo re-añade mientras la IP no vuelva a aparecer en el feed.)*

---

## 8. Preguntas frecuentes (ten lista la respuesta)

**«¿Por qué hay alertas si no he atacado?»**
> *"Son los falsos positivos **acotados** del modelo (~4,45 %) sobre el tráfico
> **legítimo** de los clientes, más un artefacto del heurístico DNS sobre el
> resolutor. **Nunca bloquean: solo degradan 5 min (LIMIT)**. El BLOCK se reserva a
> señales inequívocas. Para esta demo paré el generador de tráfico normal para que
> el ataque se vea limpio."*

**«¿Y si el atacante para para evadir el bloqueo?»**
> *"No le sirve: en modo **cuarentena** el bloqueo **persiste** aunque deje de atacar,
> hasta que vence su plazo; y cada reincidencia **escala** la caducidad
> (300 → 1800 → 3600 s). Además, el escaneo queda registrado y trazable."*

---

## 9. Cuarentena: de propuesta a **implementado**

**Estado (2026-10-16): ya implementado.** En la demo del 15-oct la respuesta *seguía al
feed* (un ataque corto → bloqueo corto, se revertía al parar), lo que dejaba una puerta:
un atacante que **pulsa y suelta** se liberaba rápido. Para cerrarla se adoptó el **modo
cuarentena**: el agente mantiene la IP bloqueada hasta que **vence su `timeout` de la
escalera** (300/1800/3600 s), aunque el atacante deje de atacar; el bloqueo **dura lo que
dice la escalera**, no lo que dura el ataque.

> Honestidad metodológica: lo que aquí se proponía como mejora **ya está en operación**
> (ver §6). El `timeout` de nftables sigue siendo el tope y la vía de liberación, así que
> la contención continúa siendo **reversible y acotada**, no una lista negra permanente.

---

## 10. Resumen del recorrido (quién hace qué, en orden)

| # | Dónde | Comando / acción | Qué demuestra |
|---|---|---|---|
| 0 | GUI · Salud/Actividad | — | estado limpio, en PERMIT |
| 1 | **Kali** | `while true; do nmap -sT -T4 -p 1-3000 --open 10.10.30.10; done` | el ataque |
| 2 | GUI · Decisiones/Alertas/Scores | filtrar `10.10.20.30` | **detección** (~20-30 s): regla + modelo |
| 3 | GUI · Bloqueos | — | la respuesta **decidida** (en vigor) |
| 4 | **srv-dmz** | `sudo nft list set inet cyberflow cyberflow_bloqueados` | la respuesta **aplicada en el host** (~15 s) |
| 5 | **Kali** (2ª term.) | `nmap -Pn -p80,443 10.10.30.10` | el **corte** (open→filtered) |
| 6 | **Kali** | `Ctrl+C` | el ataque cesa → la IP queda en **cuarentena** (sigue bloqueada hasta su `timeout`) |

**La frase que ata todo:**
> *"CyberFlow observa por el espejo, decide, **firma** la orden, y el **propio host**
> la aplica en segundos — con una respuesta **reversible y acotada**: contiene en
> cuarentena y caduca sola según la escalera de reincidencia."*
