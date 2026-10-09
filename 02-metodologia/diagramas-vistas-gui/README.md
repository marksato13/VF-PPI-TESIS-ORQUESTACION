# Vistas de la GUI de CyberFlow — en Mermaid

Réplica **1:1** de las tres vistas de topología del panel (`dashboard.py`,
`TOPO_VISTAS`), en Mermaid editable. Fuente de verdad: los datasets `completa`,
`metodologica` y `entrenamiento` del panel a fecha 2026-10-09.

- `01-operacional.mmd` — **Operacional**: cómo funciona en vivo (el camino del paquete).
- `02-metodologica.mmd` — **Metodológica**: cómo se construyó (las 7 fases del método).
- `03-entrenamiento.mmd` — **Entrenamiento**: el ciclo datos → comparar → entrenar → reentrenar.

Cada `.mmd` tiene su `.png` ya renderizado al lado. Convención de color (igual que la GUI):
hosts en azul, **artefactos** (ficheros) como cilindros con borde punteado, **sumidero**
en rojo, y acento teal para modelo/decisión/respuesta.

---

## 1 · Operacional (cómo funciona en vivo)

```mermaid
---
title: CyberFlow — Vista Operacional (cómo funciona en vivo · el camino del paquete)
---
flowchart LR
  subgraph G0["Hosts · VLAN 20/30"]
    direction TB
    atacante(["Atacante (Kali)<br/>10.10.20.30 · lanza los ataques"])
    clientes(["Clientes<br/>10.10.20.21-.26 · 6 perfiles legítimos"])
    servidor(["Servidor<br/>10.10.30.10 · objetivo HTTP/HTTPS"])
    gateway(["pfSense / gateway<br/>10.10.20.1 · enruta entre VLAN"])
  end
  subgraph G1["1 · Adquisición"]
    direction TB
    red["Red de la entidad<br/>VLAN 10-100"]
    span["Espejo SPAN<br/>CORE-STACK"]
    nic["Interfaz en escucha<br/>ens37 · SIN IP"]
    captura["tcpdump<br/>SERVICIO"]
    pcap[("anillo live-*.pcap<br/>ARTEFACTO")]
    suricata["Suricata<br/>SERVICIO"]
    eve[("eve.json<br/>ARTEFACTO")]
  end
  subgraph G2["2 · Análisis"]
    direction TB
    motor["Atribución de flujo<br/>SERVICIO"]
    variables["Variables / 10 s<br/>L2·L3·L4·L7"]
    descartes["Fuera del cálculo<br/>SUMIDERO"]
    reentrenamiento["Reentrenamiento<br/>MENSUAL / POR DERIVA"]
    modelo["Modelo recalibrado<br/>IF · CALIBRADO"]
    heuristicos["Heurísticos<br/>DETERMINISTAS"]
  end
  subgraph G3["3 · Decisión y respuesta"]
    direction TB
    control["Decisión<br/>PERMIT / LIMIT / BLOCK"]
    feed[("Feed firmado<br/>ed25519")]
    agente["Agente en host<br/>nftables LIMIT/BLOCK"]
  end
  subgraph G4["4 · Observabilidad"]
    direction TB
    registro[("motor_decision.log<br/>ARTEFACTO")]
    panel["Este panel<br/>SOLO LECTURA"]
    wazuh["Wazuh (SIEM)<br/>CONCENTRADOR"]
  end

  atacante -->|ataca| red
  clientes -->|tráfico| red
  servidor -->|objetivo| red
  gateway -->|enruta| red
  red -->|al troncal| span
  span -->|copia| nic
  nic -->|paquetes| captura
  nic -->|paquetes| suricata
  captura --> pcap
  suricata --> eve
  pcap -->|"L3·L4"| motor
  eve -->|"HTTP·DNS·TLS"| motor
  motor -->|atribuye por IP| variables
  motor -. descarta .-> descartes
  variables -->|"28 al modelo (31 extraídas)"| modelo
  variables -->|mismas variables| heuristicos
  reentrenamiento -->|entrena y congela| modelo
  modelo -->|"score &lt; umbral"| control
  heuristicos -->|confirmado| control
  control -->|veredicto firmado| feed
  feed -->|pull + verifica| agente
  control -->|cada decisión| registro
  registro -->|lee| panel
  registro -->|syslog| wazuh

  classDef host fill:#1b2b3a,stroke:#3a5169,color:#dce8f5;
  classDef arte fill:#15202c,stroke:#2b3a4a,color:#9fd0ff,stroke-dasharray:4 3;
  classDef sink fill:#2a1a1a,stroke:#6a3030,color:#f0c0c0;
  classDef accent fill:#13343b,stroke:#2a7f8a,color:#8fe0ea;
  class atacante,clientes,servidor,gateway host;
  class pcap,eve,registro,feed arte;
  class descartes sink;
  class modelo,control accent;
```

---

## 2 · Metodológica (cómo se construyó · 7 fases)

```mermaid
---
title: CyberFlow — Vista Metodológica (cómo se construyó · las 7 fases del método)
---
flowchart LR
  subgraph F1["1 · Datos y línea base"]
    m_datos["Línea base real<br/>SPAN · PCAP · eve"]
  end
  subgraph F2["2 · Preproceso y features"]
    m_feat["28 features L3/L4/L7<br/>extractor congelado"]
  end
  subgraph F3["3 · Modelado híbrido"]
    m_modelo["IF + heurísticos<br/>híbrido"]
  end
  subgraph F4["4 · Experimento y eval."]
    m_eval["Replay vs Suricata<br/>9/9 vs 0/9"]
  end
  subgraph F5["5 · Respuesta"]
    m_resp["PERMIT/LIMIT/BLOCK<br/>feed firmado"]
  end
  subgraph F6["6 · Despliegue"]
    m_desp["Desplegado en sensor<br/>systemd · replicable"]
  end
  subgraph F7["7 · Validación"]
    m_valid["Interna + externa<br/>demo · TAM"]
  end

  m_datos --> m_feat --> m_modelo --> m_eval --> m_resp --> m_desp --> m_valid

  classDef accent fill:#13343b,stroke:#2a7f8a,color:#8fe0ea;
  class m_modelo,m_resp accent;
```

---

## 3 · Entrenamiento (el ciclo · reentrenamiento)

```mermaid
---
title: CyberFlow — Vista Entrenamiento (el ciclo · datos → comparar → entrenar → reentrenar)
---
flowchart LR
  e_datos["Datos acumulados<br/>multilayer-v3.csv"]
  e_part["Partición 60/20/20<br/>sin fuga temporal"]
  e_comp["Comparar 7 modelos<br/>elegir el mejor"]
  e_train["Entrenar + congelar<br/>umbral α=0,05"]
  e_eval["Evaluar FPR / TPR<br/>test ciego + Kali"]
  e_antes["Antes vs después<br/>¿mejora?"]
  e_dec["Desplegar o conservar<br/>criterio"]

  e_datos --> e_part --> e_comp --> e_train --> e_eval --> e_antes --> e_dec
  e_dec -. "reentrenar: mensual / por deriva" .-> e_datos

  classDef accent fill:#13343b,stroke:#2a7f8a,color:#8fe0ea;
  class e_comp,e_train,e_dec accent;
```
