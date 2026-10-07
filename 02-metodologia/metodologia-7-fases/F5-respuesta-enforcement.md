# F5 · Respuesta / enforcement ◆ (aporte)

**Objetivo.** Convertir la **decisión** del motor en **acción real**: PERMIT /
LIMIT / BLOCK, distribuida como **feed firmado (ed25519)** que los **agentes en
los hosts** aplican por **nftables** con caducidad escalada. Como el sensor
observa por **espejo SPAN**, no está en el camino del tráfico: **la acción la
aplica el host**, no el sensor. La alerta va **hacia adentro** (Wazuh); el sensor
nunca sale a Internet.

## Diagrama (flujo de decisión real)

```mermaid
flowchart TD
  A["Suricata → eve.json + anillo PCAP (240 s)"] --> B["extractor<br/>28 features por entidad y ventana"]
  B --> C{"IP en exclusión?<br/>gateways · DNS · sensor · bastión"}
  C -- sí --> P["PERMIT (sin puntuar)"]
  C -- no --> D{"packet_count_10s > 0 ?"}
  D -- no --> P2["PERMIT<br/>(heurístico de ventana vacía)"]
  D -- sí --> E["score = score_samples(x)<br/>IsolationForest recalibrado"]
  E --> F{"score &lt; umbral (-0,568892)?"}
  F -- no --> G["PERMIT"]
  F -- sí --> L["LIMIT"]

  B --> H["heuristicos.py (umbrales versionados)"]
  H --> H1{"brute-force / port-scan"}
  H1 -- sí --> BK["BLOCK"]
  H --> H2{"http-abuse / dns-entropy"}
  H2 -- sí --> L

  L --> ESC["escalada.py<br/>300 / 1800 / 3600 s · nunca ∞"]
  BK --> ESC
  ESC --> FEED["publicar_feed.py<br/>feed FIRMADO ed25519"]
  FEED -. "pull + verifica firma" .-> AG["agente_enforce.py (en hosts DMZ)<br/>nftables: LIMIT=rate · BLOCK=set+timeout"]
  ESC --> AL["Alerta: Wazuh + log + panel<br/>(el sensor NUNCA sale a Internet)"]

  classDef permit fill:#e6f4ea,stroke:#34a853;
  classDef limit fill:#fef7e0,stroke:#f9ab00;
  classDef block fill:#fce8e6,stroke:#ea4335;
  class P,P2,G permit;
  class L limit;
  class BK block;
```

## Flujo

`motor_decision.py` combina modelo + heurísticos y resuelve la acción: las IP en
**exclusión** o las ventanas **vacías** son PERMIT; el **score bajo umbral** da
**LIMIT**; los heurísticos de **fuerza bruta / escaneo** dan **BLOCK**, y los de
**abuso HTTP / entropía DNS** dan LIMIT. `escalada.py` fija la **caducidad**
(300 / 1800 / 3600 s, **nunca ∞ automático**) y `publicar_feed.py` emite un
**feed firmado con ed25519**: la red confía en la orden porque está **firmada**,
no por su origen.

Los **agentes en los hosts** (`agente_enforce.py`) hacen *pull* del feed,
**verifican la firma** y aplican **nftables** en su propio kernel (LIMIT = *limit
rate*, BLOCK = *set + timeout*). En paralelo se emite **alerta a Wazuh + log +
panel**. Diseño en `DISENO-ENFORCEMENT.md` / `flujo-decision.md`.

## Cómo se ejecuta

```bash
# En el sensor: publicar el feed firmado (lo genera el motor)
python3 scripts/engine/publicar_feed.py
# En cada host DMZ: agente que verifica firma y aplica nftables
python3 scripts/enforce/agente_enforce.py
# Activar bloqueo real desde la config (vs solo observación):
#   [motor] modo = "bloqueo"   (añade --enforce)   ·   bloqueo_segundos = 120
```

## Cifras / evidencia clave

- **Respuesta confirmada en vivo:** corte real 200→000; `port_scan`→BLOCK (3/3
  tras la mejora `VERSION_UMBRALES 2026-10-06.2`, `flow≥200 & syn≤0,1`) y
  `brute_force`→BLOCK (401, "240 req HTTP/60s, 100 % fallo de auth").
- **Tiempos (honestos):** detección ~2–40 s; respuesta total hasta BLOCK
  ~1–2,5 min (dominada por la cadencia del feed firmado, configurable).
- **Falsos positivos de heurísticos:** ~0,01–0,08 % (712 450 ventanas).
- **Evidencia:** `04-evidencias/cyberflow/{N-e2e-enforcement,
  O-enforcement-vivo-campana-ataque}.md`.

## Entradas y salidas

- **Entradas:** decisión del motor (LIMIT/BLOCK), clave privada ed25519, config
  `[motor]`.
- **Salidas:** feed firmado (`.json` + firma), reglas nftables en los hosts (IP
  con caducidad), alerta Wazuh, `logs/motor_decision.log`.

## Archivos que se tocan / se usan

| Archivo | Tipo | Rol |
|---|---|---|
| `scripts/engine/motor_decision.py` | `.py` | Produce la decisión (PERMIT/LIMIT/BLOCK) |
| `scripts/engine/escalada.py` | `.py` | Caducidad escalada (300/1800/3600 s) |
| `scripts/engine/publicar_feed.py`, `feed.py` | `.py` | Feed firmado ed25519 (publicado por el sensor) |
| `scripts/enforce/agente_enforce.py` | `.py` | En hosts: verifica firma y aplica nftables |
| `ppi-enforce` (helper raíz versionado) | helper | Única vía con privilegio para el bloqueo |
| `01-arquitectura/DISENO-ENFORCEMENT.md`, `flujo-decision.md` | `.md` | Diseño de la respuesta |
| `04-evidencias/cyberflow/{N-e2e-enforcement,O-enforcement-vivo-campana-ataque}.md` | `.md` | Evidencia de enforcement real |
| `configs/cyberflow.toml` → `[motor]` `modo`, `bloqueo_segundos` | `.toml` | Observación vs bloqueo, caducidad |
| `logs/motor_decision.log` | `.log` | Registro de cada decisión |

➡ Anterior: [F4](F4-experimento-y-evaluacion.md) · Siguiente: [F6 · Despliegue / operación ◆](F6-despliegue-y-operacion.md)
