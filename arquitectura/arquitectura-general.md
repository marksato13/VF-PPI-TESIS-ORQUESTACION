# Arquitectura general

## Dos repositorios, una frontera clara

```
VF-PPI-TESIS-ORQUESTACION          VF-Sistema-Open-Source-…
(este)                              (el producto)
├── requisitos y trazabilidad       ├── código y tests
├── estado de las afirmaciones      ├── dataset y modelos congelados
├── handoffs y auditorías           ├── documentación por fases
├── planificación y riesgos         ├── PCAP y EVE
└── punteros con hash  ─────────────►  los artefactos
```

**Aquí solo van referencias con hash.** Una copia se desincroniza; un hash no.

## El laboratorio del producto

```
        PPI-LAN 10.20.0.0/24              PPI-DMZ 10.30.0.0/24
   ┌──────────────────────┐         ┌──────────────────────┐
   │ VM05 cliente  .20    │         │ VM03 servidor  .10   │
   │ VM04 Kali     .100   │         │ nginx · SSH · DNS    │
   └──────────┬───────────┘         └──────────▲───────────┘
              │                                │
              └────►  VM02  SENSOR + ROUTER  ──┘
                      10.20.0.1 / 10.30.0.1
                      Suricata · motor · nftables · dashboard
```

**Todo el tráfico LAN↔DMZ pasa por VM02.** Por eso el bloqueo no necesita SSH a
otra máquina: escribe la regla en su propio cortafuegos y surte efecto
inmediato.

## Servicios de orquestación

| Capa | Componente | Límite explícito |
|---|---|---|
| Nativo | Hermes, Herdr, OpenCode, uv, Tailscale, restic | Usuario dedicado, systemd, permisos mínimos |
| Docker | PostgreSQL, pgvector, Gitea, JupyterLab | **No sustituyen a Git ni a los artefactos** |
| Documentación | Quarto, Pandoc, LaTeX, Mermaid | La fuente es el `.md`, nunca el PDF |

> **Un servicio sin usuario es deuda.** No se levanta ninguno hasta que un paso
> concreto de `TASK-ACTUAL.md` lo necesite.
