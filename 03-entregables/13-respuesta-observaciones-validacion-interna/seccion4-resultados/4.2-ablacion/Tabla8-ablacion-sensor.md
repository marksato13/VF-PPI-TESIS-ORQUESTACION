# Tabla 8 (sensor) - Ablacion de componentes, modelo limpio + heuristicos vigentes

Datos del SENSOR (misma distribucion que el modelo). Modelo `if_limpio_2026_10`, umbral `decision_function < -0.069397` (= `score_samples < -0,569397`); heuristicos `2026-10-06.2`.

## Deteccion sobre el trafico Kali del sensor (181 ventanas excluidas del entrenamiento)

| Unidad | Total | IF limpio solo | Heuristicos solos | Hibrido (OR) |
|---|---:|---:|---:|---:|
| ventanas | 181 | 50/181 | 41/181 | 54/181 |
| episodios (contiguidad) | 1 | 1/1 | 1/1 | 1/1 |

Reglas heuristicas disparadas (por ventana): http_abuse=32, port_scan=9

## Falsos positivos por componente - benigno del sensor (65 421 ventanas de test retenidas)

> Accion calculada OFFLINE; NO es una restriccion aplicada en el host.

| Componente | Ventanas con alerta | FPR | de las cuales LIMIT | BLOCK |
|---|---:|---:|---:|---:|
| IF limpio | 2961 | 4.53% | - | - |
| Heuristicos | 472 | 0.72% | 472 | 0 |
| Hibrido (OR) | 3423 | 5.23% | - | - |

El FPR del IF sobre el benigno del sensor valida el valor del model card (~4,5 %).