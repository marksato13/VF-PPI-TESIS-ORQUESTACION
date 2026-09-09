# Diagrama de la metodología

**`DOC-016`** · Las seis subsecciones de «Proposed methodology» del artículo.

Se dibuja en Mermaid dentro de un `.md` a propósito: **GitHub lo renderiza
nativamente**, así que el diagrama se lee en el navegador sin exportar ninguna
imagen, y se corrige editando texto en vez de rehaciendo un PNG.

---

## El flujo

```mermaid
flowchart TD
    subgraph S1["3.1 · Testbed and traffic generation"]
        A1["5 VM · 3 redes aisladas<br/>PPI-MGMT · PPI-LAN · PPI-DMZ"]
        A2["Tráfico legítimo desde VM05<br/>Ataques desde VM04 (Kali)"]
        A3["Captura PCAP en el Sensor<br/>Suricata 8.0.3 · AF_PACKET"]
        A1 --> A2 --> A3
    end

    subgraph S2["3.2 · Multi-layer feature extraction"]
        B1["extract_multilayer_v2.py<br/><i>extractor congelado</i>"]
        B2["28 variables L3/L4/L7<br/>27 observables"]
        B1 --> B2
    end

    subgraph S3["3.3 · Dataset construction and labeling"]
        C1["220 episodios · 1.373 ventanas"]
        C2["train 824 · val 273 · test 276"]
        C3["Partición disjunta por episodio"]
        C1 --> C2 --> C3
    end

    subgraph S4["3.4 · Detection model and threshold calibration"]
        D1["7 candidatos evaluados"]
        D2["OCSVM · nu = 0,05"]
        D3["Umbral 1,8126<br/>alpha = 0,05 · k = 13"]
        D1 --> D2 --> D3
    end

    subgraph S5["3.5 · Real-time engine and inline enforcement"]
        E1["motor_decision.py<br/><i>reusa el extractor</i>"]
        E2["ALERT → nftables<br/>expiración 120 s"]
        E1 --> E2
    end

    subgraph S6["3.6 · Evaluation protocol"]
        F1["58 corridas · 2 pases"]
        F2["Lead time 8,0 s<br/>0 caídas"]
        F3["FPR operativo<br/>25,81 % y 22,97 %"]
        F1 --> F2 --> F3
    end

    A3 --> B1
    B2 --> C1
    C2 --> D1
    D3 --> E1
    E2 --> F1

    C3 -. "el umbral se fija SOLO con validación" .-> D3
    F3 -. "no reproduce el 4,71 % offline" .-> D3

    classDef propio fill:#0f5a6e,stroke:#0a3f4d,color:#fff
    classDef aviso fill:#8a1c1c,stroke:#5c1212,color:#fff
    class A1,A2,A3,E1,E2 propio
    class F3 aviso
```

**En azul**, lo que ningún artículo comparable de IJIES tiene: laboratorio
propio, generación de tráfico y motor con bloqueo real.
**En rojo**, la limitación medida que no se oculta.

Las dos flechas punteadas son las que un revisor va a mirar: el umbral se fija
**solo con validación**, nunca con prueba; y el FPR operativo **no reproduce**
el de laboratorio.

---

## De dónde sale cada bloque

```mermaid
flowchart LR
    F01["F01<br/>Infraestructura"] --> S31["3.1"]
    F02["F02<br/>Diseño experimental"] --> S31
    F03["F03<br/>Variables"] --> S32["3.2"]
    F04["F04<br/>Dataset"] --> S33["3.3"]
    F05["F05<br/>Modelado"] --> S34["3.4"]
    F06["F06<br/>Motor"] --> S35["3.5"]
    F07["F07<br/>Dashboard"] --> S35
    F08["F08<br/>Validación"] --> S36["3.6"]
    F00["F00 · Gobernanza"] -.- N1["sin subsección:<br/>organización interna"]
    F09["F09 · Tesis"] -.- N2["sin subsección:<br/><b>es</b> el artículo"]

    classDef fase fill:#1f3a4d,stroke:#0d1f2a,color:#fff
    classDef sec fill:#0f5a6e,stroke:#0a3f4d,color:#fff
    classDef nota fill:#2b2b2b,stroke:#555,color:#ddd
    class F00,F01,F02,F03,F04,F05,F06,F07,F08,F09 fase
    class S31,S32,S33,S34,S35,S36 sec
    class N1,N2 nota
```

**Diez fases de trabajo, seis subsecciones de artículo.** No se pierde nada:
`F00` es organización interna y `F09` **es** el artículo.

---

## Por qué 3.2 va antes que 3.3

En los cinco artículos de IJIES analizados el dataset va **antes** que las
variables, porque sus autores descargan NSL-KDD o UNSW-NB15 y luego seleccionan
características sobre él.

Aquí no. El extractor convierte los paquetes en vectores, y **esos vectores son
las filas del dataset** — 43 columnas: `episode_id`, `partition`, `label` y las
28 variables. No hay dataset antes de extraer.

Justificación completa y los cinco DOI:
`docs/articulo/02-estructura-metodologia.md` en el producto.
