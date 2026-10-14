# Recorrido: tráfico normal (0 falsos positivos) + escaneo detectado, a la vez

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

**Resultado en el motor** (registro real, mismas ventanas):

```
PERMIT  10.10.20.24  modelo recalibrado (IsolationForest)  normal -0.554
PERMIT  10.10.20.25  modelo recalibrado (IsolationForest)  normal -0.434
PERMIT  10.10.20.26  modelo recalibrado (IsolationForest)  normal -0.460
```

**Todos los clientes PERMIT. Ningún falso positivo.** Sus scores quedan por
encima del umbral (−0,568892): son tráfico normal, que es con lo que se calibró.

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
etiqueta `REGLA: PORT_SCAN` (una además con `ANOMALÍA DEL MODELO`). Ningún
cliente aparece. **(captura `img/CAMP-02-alertas.png`)**

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

- **Falsos positivos:** con tráfico legítimo real de seis perfiles, el sistema
  marcó **0** clientes. Es la comprobación en vivo de la tasa de falsos
  positivos (el modelo congelado tiene 4,45 % de FPR sobre la partición de
  prueba; con los heurísticos y la lista de nunca-bloquear, sobre el benigno del
  ensayo el sistema completo da 0).
- **Detección simultánea:** en la misma ventana, el único que se marcó fue el
  atacante, por el modelo **y** por el heurístico `port_scan`, con BLOCK.
- **Separación limpia:** no hace falta parar el tráfico legítimo para ver el
  ataque; el sistema distingue uno de otro por IP y ventana.

Cobertura completa por familia en
[COBERTURA-ATAQUES-COMPROBADOS.md](../COBERTURA-ATAQUES-COMPROBADOS.md).
