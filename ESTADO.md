# Estado

**Actualizado:** 29 de septiembre de 2026

---

## En una frase

El sistema está **desplegado y funcionando sobre tráfico real**, en modo
observación. El bloqueo del 17-sep —«la red no tiene tráfico de usuarios»— **está
superado**: la campaña `piloto-con-dns` inyecta tráfico representativo (~44–48 %
de las ventanas con L7, hosts repartidos por VLAN). Una **recalibración
en seco** (29-sep, sensor1) baja el FPR de **92,4 % a 4,45 %** en tráfico normal
retenido, y la **corrida de la Kali** (30-sep) mide la detección: **TPR 69 % global,
100 % en ataques HTTP** (fuerza bruta/flood/web-scan), 63 % escaneo, 0 % DNS-entropy
—limitación declarada— al mismo umbral (notas `L` y `M`). Falta **congelar** el
modelo (`calibrado=true`) para cerrar `v1.0.0`.

---

## Qué está en marcha

| Componente | Estado | Evidencia |
|---|---|---|
| Espejo SPAN del núcleo hacia el sensor | ✅ validado | `04-evidencias/cyberflow/D-validacion-espejo-2026-09-17.md` |
| Suricata sobre `ens37`, `eve.json` con tráfico real | ✅ activo | `G-suricata-2026-09-17.md` |
| Búfer en anillo de PCAP, 240 s | ✅ activo | `I-motor-desplegado-2026-09-17.md` |
| Motor de decisión (OCSVM), **modo observación** | ✅ activo | ídem |
| Bloqueo con `nftables` | ⬜ desactivado a propósito | ver decisión pendiente 1 |

**Las etiquetas 802.1Q sobreviven al espejo** y llegan hasta `eve.json`. Eso
confirma que la variable de distribución por VLAN es viable, que estaba en duda.

---

## Lo que bloquea

### 🟢 1 · Tráfico de usuarios — RESUELTO por el piloto (29-sep)

**Contexto (17-sep).** Medido entonces, ventana de 95 s y 1647 paquetes:

| Tipo | Paquetes | % |
|---|---|---|
| STP / PVST+ | 470 | 29 % |
| VRRP / CARP | 441 | 27 % |
| pfsync | ~511 | 31 % |
| **Tráfico IP real** | **211** | **13 %** |

Entonces el 87 % era plano de control y las VLAN de usuarios no tenían estaciones.

**Actualización (29-sep), medido sobre la línea base acumulada (336 964 filas,
45 entidades, campaña `piloto-con-dns`):**

| Señal | Sensor1 |
|---|---|
| Ventanas con L7 (HTTP/DNS/TLS) | **44,2 %** (HTTP 109k · DNS 100k · TLS 48k) |
| Ventanas con datos TCP | 18,6 % |
| Ventanas con SYN | 21,2 % |
| «Solo control» | 55,7 % |

Las entidades top son **hosts de usuario** repartidos por VLAN 10/20/30/40/100
(~7 % de filas cada uno), **no** los switches/pfSense emitiendo CARP. El piloto
inyectó tráfico representativo: la línea base ya sirve para recalibrar.

### 🔴 2 · El modelo no es trasladable, y ya está medido

Primeros minutos sobre tráfico real, **sin ningún ataque en curso**:

```
decisiones : 92 en 7 ventanas
  ALERT     85    92,4 %
  PERMIT     7     7,6 %
```

Las entidades señaladas eran las interfaces de VLAN de pfSense emitiendo CARP.
**92,4 % de falsos positivos.** Predicho por la metodología, ahora medido — y
sirve como línea base contra la que medir la mejora de la recalibración.

**Medida de la mejora (29-sep, recalibración EN SECO en sensor1).** Con la línea
base enriquecida por el piloto (337 980 filas elegibles, **sin fuga temporal**,
69,6 h; train 204 148 / validation 65 633 / test 65 421), umbral congelado desde
validación (`alpha=0,05`):

```
FPR validacion : 0,0500
FPR TEST       : 0,0445   (4,45 %)   vs   0,924 (92,4 %) sin recalibrar
```

El FPR sobre tráfico normal retenido baja de **92,4 % a 4,45 %** (~20× menos) y
clava el objetivo. Es una recalibración **en seco**: escribió en `/tmp/recal`, no
tocó el modelo desplegado ni el piloto. **Matiz:** mide falsos positivos sobre
tráfico normal (no hay ataques en la base); la **detección de ataques** se validará
con la corrida de la Kali. Falta **congelar** para dejar `calibrado_en_esta_red=true`.

### 🟡 3 · El entorno congelado exige Python 3.14.4, y no es negociable

El sensor tenía 3.12.3 y tres de las seis dependencias fijadas no existen para
esa versión. Se intentó recongelar el entorno sobre 3.12 ejecutando el
protocolo completo, y **hubo que revertirlo**:

| Detector | 3.14 / sklearn 1.9.0 | 3.12 / sklearn 1.7.2 |
|---|---|---|
| `ocsvm_scaled` (desplegado) | 158/179 | 158/179 ✅ |
| **`if_primary_weighted`** | **97/179** | **103/179** ❌ |

Causa medida: en scikit-learn 1.7.2, `IsolationForest.fit` **acepta
`sample_weight`, no avisa, no falla y lo ignora**. Delta máximo entre ajustar
con y sin pesos: `0.0000000000`.

El protocolo pondera por `1/filas_por_episodio` para corregir un desbalance
medido —5 de 132 episodios concentran el 31,7 % de las filas—, y bajo 1.7.2 esa
corrección no ocurre sin que nada lo indique.

**Resuelto compilando CPython 3.14.4 desde el código fuente en el sensor**
(deadsnakes solo ofrece 3.14.6, y el guardarraíl exige la versión exacta).
Evidencia completa en `04-evidencias/cyberflow/J-recongelado-entorno-2026-09-17.md`.

### 🟡 4 · El modelo principal declarado no es el que se ejecuta

El manifiesto declara `if_primary_weighted` como conclusión principal, pero el
motor despliega `ocsvm_scaled`. Hay que explicarlo en la tesis o alinearlo. No
es consecuencia de nada reciente: ya estaba así.

---

## Decisiones pendientes

| # | Decisión | Por qué importa |
|---|---|---|
| 1 | **¿El bloqueo es demostrativo o corta tráfico real?** | Con un espejo el sensor observa pero no está en el camino. Cambia el alcance de la tesis |
| 2 | **¿La réplica es para disponibilidad o para rendimiento?** | No se diseña igual |
| 3 | **¿Cómo se genera el tráfico?** | Es lo que desbloquea todo lo demás |
| 4 | **¿Montar Python 3.14 o recongelar sobre 3.12?** | Afecta al artefacto ya publicado |
| 5 | **`tls_handshake_failure_ratio_60s`** | Hacerla observable, retirarla, o documentarla como no observable. Dejarla ambigua, no |

---

## Correcciones al material anterior

Medido el 17 de septiembre, contradice lo documentado antes:

- **La máscara de la VLAN 60 es `/24`**, confirmado contra pfSense
  (`VLAN60_GESTION -> v4: 10.10.60.2/24`). Estaba documentada como `/24` y `/28`
  en sitios distintos.
- **pfSense-B sí emite.** Figuraba como «no responde a nada»; en la VLAN 100
  transmite 200 paquetes y recibe 281. Puede seguir sin responder a sondeos IP
  desde la VLAN 10, que es como se midió entonces.
- **El disco del sensor no estaba ampliado.** El disco virtual sí (40 GB), pero
  el volumen lógico seguía en 18,5 GB. Corregido a 36,9 GB.
- **La interfaz de captura pedía DHCP** y había una interfaz `ens38`
  configurada que no existe. Corregido.
- **El espejo ya es permanente.** Estaba solo en `running-config` y un reinicio
  del switch lo borraba; ahora figura en `startup-config`.
- **La VLAN 40 se llama SERVICIOS** en pfSense, no FILESERVER. La 70 es
  TRANSIT_FORTIGATE.

---

## Pendientes del producto

| # | Tarea | Estado |
|---|---|---|
| P1 | **Instalar en una segunda VM limpia** (Ubuntu 24.04, dos NIC, captura en el puerto SPAN) | ✅ **HECHO (29-sep):** `cyberflow-sensor2` (10.10.60.12) desplegado **100 % offline** (sin Internet en el sensor, sin depender del sensor 1). Probado el **ciclo completo** desinstalar → reinstalar desde un clon **fresco** de `main` → `doctor.sh` sano. Evidencia: `04-evidencias/cyberflow/K-despliegue-turnkey-sensor2-2026-09-29.md`. Convierte «reinstalable» en **«replicable llave-en-mano»**. |
| P2 | **Etiquetar `v1.0.0`** | Desbloqueado por P1; pendiente tras recalibrar en la 2ª VM |

### Novedades desde el 17-sep (repo de producto)

- **Despliegue offline real** validado en una VM aislada: host de construcción
  (contenedor Docker con Internet) → *bundle* (Suricata `.deb` + CPython 3.14.4 +
  wheels `cp314`) → transferido por el bastión → instalado **sin Internet**.
  Documentado en `docs/INSTALACION.md` (Anexos A/B/C).
- **Herramientas nuevas del producto:** `scripts/setup/configurar.sh` (asistente
  que auto-detecta interfaz/red/MAC y escribe el `.toml`; ahora con **menú de
  escenarios 1/2/3** —observación por SPAN / en línea con bloqueo / personalizado—
  commit `73d292c`), `scripts/setup/preparar-bundle.sh` (arma el bundle offline en
  un host conectado), `scripts/setup/doctor.sh` (chequeo de salud del sistema en
  marcha).
- **Instalador adaptable a los dos escenarios de conectividad:** detecta si hay
  bundle de `.deb` e instala Suricata **offline con `dpkg -i`** (sin colgarse
  buscando Internet); si no, usa `apt-get` (commit `da43aa8`). Con esto quedan
  cubiertos los modos que se planificaron: auto-detección + operación
  (observación/bloqueo) + instalación (online/offline).
- **Fixes hallados probando el despliegue real:** el instalador ahora habilita
  `cyberflow-acumular.timer` y el desinstalador lo elimina; instalación offline de
  paquetes con `dpkg -i` (no `apt-get`); el instalador imprime la URL del panel;
  y, hallado en el ciclo desinstalar/reinstalar del 29-sep, el panel sin sus
  ficheros de auth se reporta como **AVISO, no FALLO** (commit `131ac27`); los
  **timers pasan a `OnCalendar`** porque con `OnUnitActiveSec` se quedaban sin
  próximo disparo tras reinstalar y la línea base dejaba de crecer (commit
  `56c01e8`); y `doctor.sh` ya **cuenta bien los avisos** (commit `f7d0fe8`).
- **Panel** mejorado: fila de KPIs, topología con recorrido y nodo «Cómo decide»,
  variables por capa con paleta, tabla con mini-barra de score, actividad con
  tooltip, asistente guiado y modo demo.
- **Entregables de tesis preparados:** informe consolidado de actualización,
  **instrumento TAM** e **instrumento de juicio de expertos** (validez del entorno).

Ya hecho y verificado antes: instalación/desinstalación desde cero, CI con tests,
recalibración del modelo en cada cambio, panel web funcionando.

## Lo siguiente, por orden

1. Decidir cómo se genera el tráfico *(decisión 3)*
2. Levantar los servicios que faltan: servidor web, ficheros, base de datos
3. Tomar una línea base que merezca ese nombre
4. Recalibrar, y comparar contra el 92,4 %
5. Diseñar los escenarios de ataque *(datos reales, escenarios controlados)*
6. Capa 2: las nueve variables, con los ocho pasos de validación
