# Referencias

## Código

Repositorio: <https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos>, rama `candidato/etapa2-20261101`.

| Commit | Contenido |
|---|---|
| `953a4360dc9a7540048e2b956e3b500c4069a664` | punto de partida: el cierre técnico publicado |
| `862404ecb7c3e98375fcf598c00f96075219ecac` | Motor: resolver cada pendiente con el horizonte propio de su ventana |
| `4694e38eab22f2eeadf598ef5e9613eab3dda100` | Arnés de replay: CPU por ciclo, memoria privada y carga del equipo |
| `6b6ef82195075ef608d3735d52569d0521667fd5` | Motor: coste por ancla sin trabajo repetido (mismo resultado). **Versión propuesta** |

Diferencia `953a436..6b6ef82`: 4 ficheros.

- `scripts/engine/motor_decision.py`
- `scripts/engine/motor_incremental.py`
- `scripts/engine/replay_motor.py`
- `tests/test_motor_incremental.py`

## Documentación

- **Inicio del encargo:** `main` = `fb394a3` (cierre técnico), sin cambios posteriores.
- **Criterio de rendimiento:** commit `baa6e92`, publicado antes de medir.
- **Antecedente conservado sin cambios:** `../etapa2-cierre-tecnico-2026-11-01/`.

## Entradas congeladas (las del cierre técnico)

- PCAP archivado del 3B y anillo re-troceado de 5 s (2535 ficheros).
- Segmento de EVE: sha256 `b7bf61a2…318f`.
- Modelo `if_limpio_2026_10`: sha256 `df547da0…fd60`.
- Marcas del orquestador: `../ejecucion-3b-2026-11-01/evidencia/sensor/copias/marcas.jsonl`.
- Umbrales α: `../etapa2-cierre-tecnico-2026-11-01/guiones/umbrales-alfa.json`.

## Hashes de las salidas

Todos los ficheros de esta carpeta, salvo el propio `MANIFIESTO.sha256`, están en ese manifiesto. Se verificó contra los bytes descargados de GitHub.
