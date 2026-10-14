# Recorrido: tráfico normal (ningún bloqueo; FP del modelo → LIMIT) + escaneo detectado

**Fecha:** 14-oct-2026 · **Escenario doble:** tráfico legítimo de los 6 perfiles
**y**, en la misma ventana, un escaneo de puertos desde la Kali.
**Objetivo:** justificar los **falsos positivos** (el tráfico normal no debe
alertar) y, a la vez, comprobar que el ataque **sí** se detecta.
**Clientes:** `10.10.20.21-.26` · **Atacante:** Kali `10.10.20.30` · **Objetivo:** srv-dmz `10.10.30.10` · **Decide:** Sensor `10.10.60.11`

Este recorrido es el complemento del de ataque del 13-oct: aquí lo importante es
lo que **NO** pasa (ningún cliente legítimo se marca) mientras el ataque que
corre en paralelo **sí** se marca. Es la prueba directa de la tasa de falsos
positivos.

---

## 0. Componentes

| Componente | Host | Estado |
|---|---|---|
| Sensor · motor / captura / Suricata / panel / publicador | 10.10.60.11 | activos |
| Tráfico legítimo (6 perfiles) | VM clientes 10.10.20.20 | `cyberflow-lab.target` activo |
| Atacante | Kali 10.10.20.30 | escaneo lanzado |
| Agente + cortafuegos | srv-dmz 10.10.30.10 | `ppi-enforce-agent.timer` activo (**modo sombra**) |

---

## 1. Tráfico normal (los 6 perfiles)

Arrancado en la VM de clientes:

```
sudo systemctl start cyberflow-lab.target
```

Cada perfil es una IP distinta golpeando al servidor con un patrón realista:
ofimática (.21), navegación (.22), descargas (.23), aplicación (.24), ligero
(.25), errático (.26). El motor puntúa **por IP**, así que son seis entidades.

**Resultado en el motor** (la mayoría de las ventanas, PERMIT):

```
PERMIT  10.10.20.24  modelo recalibrado (IsolationForest)  normal -0.554
PERMIT  10.10.20.25  modelo recalibrado (IsolationForest)  normal -0.434
PERMIT  10.10.20.26  modelo recalibrado (IsolationForest)  normal -0.460
```

**Ningún cliente es BLOQUEADO.** Los heurísticos de alta confianza (fuerza
bruta, escaneo…) **no disparan** con tráfico legítimo: 0 heurísticos, 0 BLOCK.

Pero hay que decirlo con precisión: el **modelo** tiene un FPR de ~4,45 %, así
que marca una **fracción** de las ventanas de los clientes como anomalía. Esas
no se bloquean: se traducen en **LIMIT** (degradar la tasa, reversible). Medido
en esta corrida (~1 h de tráfico real):

| | ventanas |
|---|---|
| ALERT del **modelo** sobre clientes (→ LIMIT) | 168 (.22: 76 · .24: 63 · .26: 14 · .21: 11) |
| Heurísticos disparados sobre clientes | **0** |
| Clientes **BLOQUEADOS** | **0** |
| En el feed: `.21`, `.22`, `.24` | **LIMIT** (nunca BLOCK) |

Es el **coste conocido de un falso positivo del modelo**, y es exactamente por
esto que una anomalía del modelo da **LIMIT y no BLOCK**: equivocarse solo
degrada, nunca corta. El camino que SÍ corta (los heurísticos) no se equivocó
ni una vez con los clientes.

---

## 2. El ataque, en la misma ventana (escaneo de puertos)

Comando en la Kali (10:40:23 → 10:40:49 UTC, 22,5 s):

```
nmap -sT -T4 --max-retries 1 -p 1-3000 --open 10.10.30.10
```

El cortafuegos solo deja 443 hacia la DMZ, así que nmap ve un único puerto
abierto; da igual para el patrón: el escaneo genera ~3600 intentos de flujo a
muchos puertos en segundos, que el sensor ve por el espejo.

---

## 3. Detección: modelo **y** heurístico

El sensor marca la Kali (10.10.20.30) por las **dos** señales:

```
ALERT  10.10.20.30  modelo if_recalibrado_2026_09  +  heuristico port_scan BLOCK
       motivo: "3601 intentos/30s a muchos puertos, 0% completados"
```

En el panel, sección **Alertas**: *2 alertas en la última hora · 2 por reglas ·
1 anomalía del modelo*, las dos para **10.10.20.30** con acción **BLOCK** y la
etiqueta `REGLA: PORT_SCAN` (una además con `ANOMALÍA DEL MODELO`).
**(captura `img/CAMP-02-alertas.png`, de los primeros minutos).**

> A lo largo de la hora, los clientes legítimos también aparecen en Alertas,
> pero como **anomalía del modelo** (score bajo el umbral) con acción **LIMIT**,
> nunca con `REGLA`/BLOCK: es el FPR del modelo del punto 1, no un ataque.

En **Decisiones**, los clientes se ven en PERMIT con score normal y, a la
derecha del scatter, los puntos del escaneo caen por debajo del umbral.
**(captura `img/CAMP-01-decisiones.png`)**

---

## 4. Respuesta: feed firmado → relay → host

El publicador tradujo la decisión en una entrada del feed firmado, y el relay la
llevó al host (comprobado en `~/enforce/feed.json` del srv-dmz):

```json
{"accion":"BLOCK","detector":"port_scan","ip":"10.10.20.30",
 "motivo":"port_scan: 3601 intentos/30s a muchos puertos, 0% completados",
 "nivel":10,"revisar_humano":true}
```

El agente del host, al leer el feed, **decide bloquear** la Kali (`~/enforce/shadow.log`):

```json
{"block": ["10.10.20.30"], "comandos": 10, "errores": 0, "estado": "aplicado"}
```

> **Modo sombra.** En este momento el agente corre en **modo sombra**
> (mide y registra lo que aplicaría, sin tocar nftables; INSTALACION.md §9.6).
> Por eso `nft` no muestra la IP: la decisión de bloqueo es correcta, solo no se
> aplica. El bloqueo **real** sobre el kernel del host (Kali 443 open → filtered)
> se validó de extremo a extremo el **13-oct** (recorrido de ataque). Quitar
> `--aplicar` del agente lo pone en sombra; añadirlo lo deja bloqueando de verdad.

---

## 5. Qué justifica este recorrido

- **Falsos positivos, con honestidad:** ningún cliente legítimo fue **bloqueado**
  (0 heurísticos, 0 BLOCK). El modelo, con su FPR ~4,45 %, sí marcó una fracción
  de ventanas de clientes como anomalía, pero esas van a **LIMIT** (degradar,
  reversible), no a BLOCK. El coste de un falso positivo del modelo está acotado
  por diseño: es la razón de ser de la respuesta graduada. El bloqueo se reserva
  para los heurísticos de alta confianza, que no se equivocaron.
- **Detección simultánea:** en la misma ventana, el **único BLOQUEADO** fue el
  atacante, por el modelo **y** por el heurístico `port_scan`.
- **Separación limpia:** no hace falta parar el tráfico legítimo para ver el
  ataque; el sistema distingue uno de otro por IP y ventana, y gradúa la
  respuesta (clientes → a lo sumo LIMIT; atacante → BLOCK).

Cobertura completa por familia en
[COBERTURA-ATAQUES-COMPROBADOS.md](../COBERTURA-ATAQUES-COMPROBADOS.md).
