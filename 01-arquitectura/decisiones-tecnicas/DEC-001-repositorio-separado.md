# DEC-001 · Repositorio de orquestación separado

| | |
|---|---|
| **Fecha** | 4 de septiembre de 2026 |
| **Estado** | Aceptada |
| **Fase** | `PHASE-00` |

## Contexto

El repositorio del producto acumula código, dataset, modelos, PCAP, 181
documentos de campaña y 162 revisiones. Durante esta sesión aparecieron seis
fallos de trazabilidad —no de código— que ese repositorio no podía prevenir por
sí solo: documentos envejecidos, formatos desincronizados y la misma cifra
escrita de cuatro maneras.

## Opciones consideradas

| Opción | A favor | En contra |
|---|---|---|
| **Carpeta dentro del producto** | Un solo `git clone` | Mezcla gobernanza con artefactos; el repo ya es grande |
| **Repositorio separado** | Frontera clara; se puede hacer privado | Dos repos que sincronizar |
| **Solo un `TASK.md`** | Coste cero | No escala a matriz de requisitos ni auditorías |

## Decisión

**Repositorio separado**, con la regla de que aquí solo van **referencias con
hash**, nunca copias de artefactos.

## Consecuencias

- **Acepta:** dos repositorios que mantener, y el riesgo de que este quede
  desactualizado respecto al producto.
- **Descarta:** duplicar dataset, modelos o documentación técnica.
- **Revisar si:** este repositorio deja de actualizarse durante más de dos
  semanas mientras el producto sí avanza. Sería señal de que la capa no aporta y
  conviene replegarla a un `TASK.md`.

## Evidencia

Los seis riesgos materializados están listados con su manifestación concreta en
[`PLANIFICACION.md`](../../PLANIFICACION.md), sección 1.
