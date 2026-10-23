# 4.2 (1) - Auditoria de etiquetas de las 181 ventanas excluidas

`eligible_training=False` = EXCLUIDA del entrenamiento, **no** = maliciosa. Por eso NO se
presenta 50/181 ni 54/181 como *recall*. Se etiqueta cada ventana y se separan las inciertas.

## Composicion

- Total excluidas: **181**
- Entidades: 10.10.20.30=181
- Rango temporal (una sola rafaga continua, NO se parte en episodios): 2026-09-27T21:35:00Z -> 2026-09-27T22:05:00Z
- En la **rafaga activa documentada** (27-sep 21:35-22:05 UTC): **181**
- Disparan un **heuristico** determinista: **41**

## Resultado de la auditoria

**Las 181 caen TODAS dentro del periodo de ataque documentado** (27-sep 21:35-22:05 UTC),
una sola rafaga continua. Pero eso es una etiqueta de **PERIODO**, no una verdad por-ventana de
trafico malicioso activo: dentro de una rafaga hay ventanas de 10 s de baja intensidad o huecos.
Por eso NO se declara recall por-ventana sobre estas 181.

| Etiqueta | Ventanas |
|---|---:|
| en periodo de ataque documentado | 181 |
| de ellas, con senal fuerte (dispara heuristico) | 41 |
| incierto (fuera de rafaga / sin regla) | 0 |

## Fraccion de ventanas del periodo marcadas por cada componente (NO es recall)

| Componente | Ventanas marcadas / total del periodo |
|---|---:|
| IF limpio | 50/181 |
| Heuristicos | 41/181 |
| Hibrido (OR) | 54/181 |

> Esto NO es un recall de laboratorio: las 181 son contaminacion ambiental de una sola
> rafaga, no una bateria curada con ground truth por familia. El recall formal por familia
> sale de la bateria instrumentada nueva (4.2 paso 2), no de aqui.

Detalle por ventana: `auditoria-181-ventanas.csv`.