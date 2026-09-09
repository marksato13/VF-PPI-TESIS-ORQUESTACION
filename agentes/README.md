# Agentes y habilidades

Dos agentes con papeles opuestos a propósito. Ese contraste es lo único que
hace útil tener dos: si quien revisa también escribe, nadie mira desde fuera.

| | **la gorda nemi** | **gordiito asin** |
|---|---|---|
| Papel | Profesora de Investigación V y asesora | Ingeniero de sistemas |
| Herramientas | **Sin `Write` ni `Edit`** | Completas |
| Qué hace | Señala con ubicación exacta y prueba | Implementa y verifica |

**Ambos firman como agente.** No hablan por el Ing. Nemias Saboya Ríos ni por
el Ing. Fernando Manuel Asin Gómez, y su salida no debe presentarse como el
visto bueno de un asesor real. La regla está dentro de cada definición, no
solo aquí.

## Instalación

```bash
agentes/instalar.sh
```

Los copia a `~/.claude/`, **a nivel de usuario**, para que funcionen tanto en
este repositorio como en el del producto. Si vivieran solo en uno, dejarían de
cargarse al trabajar en el otro. Es idempotente: repetirlo solo actualiza.

## Habilidades

**De nemi** — revisión académica:
`revision-entregables-curso` · `revision-estructura-articulo` ·
`revision-redaccion-cientifica` · `preparacion-defensa`

**De gordiito asin** — técnicas del PPI:
`ppi-dataset-audit` · `ppi-feature-contract-review` · `ppi-model-evaluation` ·
`ppi-leakage-validity-audit` · `ppi-operational-validation` ·
`ppi-experiment-freezer` · `ppi-datasheet-builder` · `ppi-scientific-figures` ·
`ppi-release-readiness` · `ppi-scientific-claim-audit`

## Límite conocido

Un subagente **no hereda los servidores MCP** registrados a nivel de usuario.
En su primera revisión, nemi no tuvo acceso a `ppi-trace` y verificó todo a
mano contra las fuentes primarias. El trabajo salió bien, pero conviene
saberlo: si una tarea depende de una herramienta MCP, hay que comprobar
primero que el agente la tenga.
