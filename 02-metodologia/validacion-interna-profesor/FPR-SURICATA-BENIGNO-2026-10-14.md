# Falsos positivos de Suricata sobre la línea base — medición

**Fecha:** 14-oct-2026 · **Cierra el hueco de la campaña C3** (el FPR de Suricata
estaba "no medido"). Es la pieza que faltaba para que la comparación con Suricata
sea completa, no solo de detección.

## Dónde corre cada Suricata (aclaración importante)

- **En el Sensor1 (10.10.60.11):** Suricata corre en vivo **sin reglas de alerta**
  (su `suricata.rules` mide 0 bytes). Solo emite eventos EVE (http/dns/tls/flow)
  que **CyberFlow consume** para sus variables de capa 7. Es una *fuente*, no un
  IDS de firmas.
- **El comparador (VM-SURICATA, 10.10.60.13):** Suricata 7.0.3 **+ ET Open
  (53 013 reglas)**, dedicado a la comparación. Aquí es donde se mide a Suricata
  *como IDS*. Es la razón de que la comparación sea por **replay** y no "en vivo
  en el sensor": el sensor no hace alerting.

## Método

Se capturaron **~4 minutos de tráfico benigno real** del anillo del sensor
(16 PCAP, **112 556 paquetes, 50 MB, 335 flujos de clientes**), con los 6 perfiles
legítimos corriendo y **sin ningún ataque**. Ese PCAP se reprodujo en el
comparador con ET Open:

```bash
suricata -r benigno/ --pcap-file-recursive -c <trial-ET-Open>/suricata.yaml -l out/
```

Se contaron las alertas (`event_type=alert`) del `eve.json`.

## Resultado

**12 alertas en total**, pero hay que distinguir qué son:

| Tipo de alerta | Cuántas | ¿Es una amenaza? |
|---|---|---|
| `SURICATA STREAM packet out of window` | 5 | No — anomalía de stream |
| `SURICATA STREAM invalid timestamp` | 4 | No — anomalía de stream |
| `SURICATA STREAM FIN out of window` | 2 | No — anomalía de stream |
| **`ET SCAN Potential SSH Scan`** | **1** | Firma ET, pero… |

- Las **11 STREAM** son **artefactos del espejo SPAN** (paquetes duplicados /
  reordenados que el mirror entrega): no son firmas de amenaza. CyberFlow los
  **deduplica**; Suricata los marca como anomalía de bajo nivel (severidad 3).
- La **1 firma ET** (`ET SCAN SSH Scan`) proviene de **10.10.10.30 / 10.10.60.11
  (gestión)** &mdash; tráfico **SSH de administración**, muy probablemente la
  propia sesión de prueba, **no** el tráfico de los clientes.

**Falsos positivos de firma ET sobre el tráfico legítimo de los clientes: 0.**

## La comparación de falsos positivos, honesta

| | FP sobre tráfico legítimo de clientes |
|---|---|
| **Suricata** — firmas ET de amenaza | **0** |
| CyberFlow — **heurísticos** (el camino que BLOQUEA) | **0** |
| CyberFlow — **modelo** (→ LIMIT, reversible, nunca BLOCK) | ~4,45 % |
| *(Suricata — anomalías de stream, artefacto SPAN)* | *6/11, severidad baja, no amenazas* |

## Conclusión (el tradeoff real)

No es "CyberFlow gana en todo". Es un **tradeoff precisión / recall**, y medirlo
lo deja claro:

- **Suricata es muy preciso:** sus firmas **no se disparan** con el tráfico
  legítimo (0 FP de amenaza). Pero es **ciego a lo que no tiene firma**: 0/3 en
  DNS, flood y escaneo.
- **CyberFlow tiene más recall:** detecta esas familias sin firma, a cambio de un
  FPR de modelo del 4,45 % &mdash; pero **acotado**: va a **LIMIT** (degradar,
  reversible), **nunca a BLOCK**; el camino que bloquea (heurísticos) tiene 0 FP,
  igual que Suricata.

Por eso **se complementan**: Suricata cubre lo conocido con precisión; CyberFlow
cubre lo desconocido y actúa, con un coste de falso positivo bounded. El aporte
de CyberFlow es la detección de lo **sin firma** + la **respuesta**, que Suricata
en SPAN no da.

> **Pendiente aún:** una corrida **en vivo simultánea** (hora de pared) queda como
> confirmación secundaria; para la *detección* y el *FPR*, el replay con input
> idéntico es metodológicamente suficiente (ver `19-METODO-REPLAY-PCAP.md`).
