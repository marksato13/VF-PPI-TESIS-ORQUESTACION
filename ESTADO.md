# Estado

**Actualizado:** 17 de septiembre de 2026

---

## En una frase

El sistema está **desplegado y funcionando sobre tráfico real**, en modo
observación. Lo que bloquea la tesis ya no es técnico: **la red no tiene
tráfico de usuarios que analizar**.

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

### 🔴 1 · No hay tráfico de usuarios

Medido el 17 de septiembre, ventana de 95 s y 1647 paquetes:

| Tipo | Paquetes | % |
|---|---|---|
| STP / PVST+ | 470 | 29 % |
| VRRP / CARP | 441 | 27 % |
| pfsync | ~511 | 31 % |
| **Tráfico IP real** | **211** | **13 %** |

**El 87 % es plano de control de los switches y del cortafuegos.** Las VLAN de
usuarios tienen *exactamente* 96 paquetes cada una: un BPDU por VLAN, no
tráfico. Los tres switches de acceso no tienen ni una estación conectada.

Una línea base tomada así enseña al modelo que lo normal es el latido de STP y
CARP. **Sin resolver esto, la recalibración no produce nada utilizable.**

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

## Pendientes del producto (aparcados el 2026-09-18)

| # | Tarea | Qué la desbloquea |
|---|---|---|
| P1 | **Instalar en una segunda VM limpia** (Ubuntu 24.04, dos interfaces, captura en `PG-CYBERFLOW-SPAN`) | Que Mark cree la VM en el HIPERVISOR 4. Es lo que convierte «reinstalable» en «replicable» |
| P2 | **Etiquetar `v1.0.0`** | Después de P1, para que la 1.0 sea la instalada en dos máquinas |

Ya hecho y verificado: instalación desde cero en el sensor (`instalar.sh` /
`desinstalar.sh`), CI con 104 tests y recalibración del modelo en cada cambio,
panel web funcionando.

## Lo siguiente, por orden

1. Decidir cómo se genera el tráfico *(decisión 3)*
2. Levantar los servicios que faltan: servidor web, ficheros, base de datos
3. Tomar una línea base que merezca ese nombre
4. Recalibrar, y comparar contra el 92,4 %
5. Diseñar los escenarios de ataque *(datos reales, escenarios controlados)*
6. Capa 2: las nueve variables, con los ocho pasos de validación
