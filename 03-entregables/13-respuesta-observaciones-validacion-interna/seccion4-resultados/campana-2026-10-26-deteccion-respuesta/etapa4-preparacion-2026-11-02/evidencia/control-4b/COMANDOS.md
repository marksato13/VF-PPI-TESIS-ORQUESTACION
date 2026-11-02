# Prueba offline de `scripts/control_4b.py` (2026-11-02)

## Regresión contra el control publicado del 3B

Intervalo: 2026-11-01 07:32:00Z – 08:05:00Z. `[LAPTOP PowerShell]` → lo ejecuté yo.

```
python -c "import gzip,shutil,sys;shutil.copyfileobj(gzip.open(sys.argv[1]),open(sys.argv[2],'wb'))" ejecucion-3b-2026-11-01/evidencia/sensor/copias/motor_decision.log.gz <scratchpad>/c4b/motor.log
python scripts/control_4b.py --motor <scratchpad>/c4b/motor.log --config preparacion-3a-2026-11-01/config-campana-3b.json --desde 2026-11-01T07:32:00Z --hasta 2026-11-01T08:05:00Z --salida <scratchpad>/c4b/control.json
```

**Resultado** (`regresion-control-3b.json`): 2 644 ventanas, todas en clase `sin_medida`, porque no se pasan datos de salud.

| Configuración | Falsas alarmas |
|---|---|
| IF_0.05 | 395 |
| IF_0.03 | 254 |
| IF_0.01 | 83 |
| HEUR | 92 |
| HIB_0.05 | 466 |
| HIB_0.03 | 336 |
| HIB_0.01 | 171 |

Es idéntico a `ejecucion-3b-2026-11-01/evidencia/sensor/analisis/analisis-3b/analisis-3b.json` → `control_normal`.

## Integración con `salud_captura.py` real

`salud_captura.py` del producto `acc6588`, VERSION `2026-11-02.1`. Se usaron las muestras en vivo de `../salud-en-vivo/` (30 s) y una ventana sintética. Resultado (`integracion-salud-captura.json`): clase `insuficiente`, con el motivo «ninguna muestra anterior o igual al inicio del periodo». Es lo correcto: las muestras no cubren [w − 60, w].

## Pruebas

`python -m pytest -q tests/test_control_4b.py tests/test_calidad_fuentes_rotacion.py tests/test_analizar_3b.py tests/test_herramientas.py` → **49 passed**.
