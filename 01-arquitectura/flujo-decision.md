# Flujo de decisión (alineado a v1.0.0)

Este diagrama sustituye al boceto previo ("IF.decision_function, 14 features,
Telegram, DROP en el kernel del sensor"), que ya **no** refleja el sistema real.
Diferencias corregidas: **28 features**, IsolationForest **recalibrado**, el motor usa
**`score_samples`** con umbral **-0,568892**, LIMIT/BLOCK los decide la combinación
modelo + **heurísticos**, la acción se aplica **en el host** (no en el sensor, que
observa por espejo), y la alerta va a **Wazuh** (nunca egress externo).

```mermaid
flowchart TD
  A["Suricata → eve.json + anillo de PCAP (240 s)"] --> B["extractor v3<br/>28 features por entidad y ventana"]
  B --> C{"IP en exclusión?<br/>gateways · DNS · sensor · bastión"}
  C -- sí --> P["PERMIT (sin puntuar)"]
  C -- no --> D{"packet_count_10s > 0 ?"}
  D -- no --> P2["PERMIT<br/>(heurístico de ventana vacía)"]
  D -- sí --> E["score = score_samples(x)<br/>IsolationForest recalibrado"]
  E --> F{"score &lt; umbral (-0,568892)?"}
  F -- no --> G["PERMIT"]
  F -- sí --> L["LIMIT"]

  B --> H["Heurísticos deterministas<br/>(umbrales versionados)"]
  H --> H1{"brute-force / port-scan"}
  H1 -- sí --> BK["BLOCK"]
  H --> H2{"http-abuse / dns-entropy"}
  H2 -- sí --> L

  L --> ESC["Escalera de caducidad<br/>300 / 1800 / 3600 s · nunca ∞ automático"]
  BK --> ESC
  ESC --> FEED["Feed FIRMADO (ed25519)<br/>publicado por el sensor"]
  FEED -. "pull + verifica firma" .-> AG["Agentes en hosts (DMZ)<br/>nftables: LIMIT (limit rate) / BLOCK (set+timeout)<br/>en SU propio kernel"]
  ESC --> AL["Alerta: Wazuh + log + panel<br/>(adentro; el sensor NUNCA sale a Internet)"]

  classDef permit fill:#e6f4ea,stroke:#34a853;
  classDef limit fill:#fef7e0,stroke:#f9ab00;
  classDef block fill:#fce8e6,stroke:#ea4335;
  class P,P2,G permit;
  class L limit;
  class BK block;
```

## Notas de lectura
- **El sensor observa por espejo SPAN**: no está en el camino, así que la acción
  (LIMIT/BLOCK) la aplican los **agentes en los hosts**, no el sensor. Ver
  `DISENO-ENFORCEMENT.md`.
- **Modelo vs heurísticos**: el modelo (score) marca la anomalía → **LIMIT**; los
  heurísticos confirmados (fuerza bruta, escaneo) → **BLOCK**. Los heurísticos cubren
  los huecos del modelo (validado: 0,08 % de falsos positivos en tráfico normal).
- **Estado actual (v1.0.0)**: implementado hasta `PERMIT/ALERT` (observación,
  calibrado). El bloque LIMIT/BLOCK + feed + agentes es **v1.1** (rama
  `v1.1-enforcement`): el "cerebro" (heurísticos + feed + escalera) ya está y probado;
  falta integrarlo en el motor y los agentes de host (tras la validación).
