# Pruebas de los analizadores (ejecutadas al construir el paquete, 2026-11-11T18:36:23Z)

| Prueba | Resultado | Notas |
|---|---|---|
| `analisis/test_analizar_b.py` (analizador de B, E1-E5) | `36 passed in 0.17s` | pytest, Python 3.14.3, sobre las fuentes del paquete (copia identica a la de la carpeta de trabajo) |
| `analisis/test_e1_por_destino.py` (E1 por destino) | `9 passed in 0.03s` | 8 pruebas de comportamiento + 1 de mutantes (5 mutantes, todos eliminados) |

## No re-ejecutado en este cierre
`analisis/test_instrumentacion.py` (E3 `e3_v2`, instrumentacion de la inundacion, muestreador del set) requiere el banco Docker (`cyberflow-etapa3-banco:1`) con el producto de la etapa 3 montado; Docker Desktop estaba apagado al construir el paquete. Ademas importa muestreador_set.py y usa inundacion_instrumentada.sh y clientes_factor1_tx.py, que no estan en este paquete: no es ejecutable desde aqui. Su ultima ejecucion registrada esta en los documentos de la carpeta de trabajo y en `criterios/CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md` (9 pruebas de la rama BLOCK, 4 mutaciones eliminadas); no se ha repetido ni se ha modificado desde entonces.

## Salida literal
```
....................................                                     [100%]
36 passed in 0.17s
```
```
.........                                                                [100%]
9 passed in 0.03s
```
