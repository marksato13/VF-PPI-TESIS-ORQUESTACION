# P — Equivalencia del umbral del modelo desplegado (Sensor1, 2026-10-10)

**Qué se comprueba.** Que el umbral con el que decide el motor (`score_samples`) es el
mismo punto de corte que el calibrado en el informe de entrenamiento
(`decision_function`), sobre el **artefacto vivo**, sin modificarlo. Cierra la duda de si
la promoción del modelo recalibrado al motor transformó bien el umbral de escala.

**Veredicto: `EQUIVALENTE`.** Salida completa en
[`P-equivalencia-umbral-sensor1-2026-10-10.json`](P-equivalencia-umbral-sensor1-2026-10-10.json).

## Cómo se ejecutó

- Dónde: Sensor1 (`cyberflow-sensor`), usuario `m4rk`, entorno del motor
  (`~/cyberflow/.venv`: CPython 3.14.4, scikit-learn 1.9.0). Fecha: 2026-10-10T04:06:26Z.
- Script: `scripts/modeling/verificar_equivalencia_umbral.py` del commit
  [`56cce52`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/56cce52c9a094b0d58e9532d8aeacc5fdff26b99/scripts/modeling/verificar_equivalencia_umbral.py)
  (rama del sensor; idéntico en `main@98d7c62`), SHA-256 del fichero en el sensor
  `fe9d0309899154b16eab10ef456ac2a97a3eaaa45db08e5887b30bd7fe4c277d`.
- Orden:

```bash
.venv/bin/python scripts/modeling/verificar_equivalencia_umbral.py \
  --modelo artifacts/preliminar/if_recalibrado_desplegable.joblib \
  --manifiesto artifacts/preliminar/manifest-if-recalibrado.json \
  --detector if_recalibrado_2026_09 \
  --umbral-decision -0.06889178778834089
```

El `--umbral-decision` es el `umbral_decision_function` del informe de calibración
`artifacts/preliminar/ensayo-if-v2.json` (SHA-256
`ec3ed06304fdbe6367ab1b69e40498980e6eed6df890f67ae5c4001f98c86421`).

## Resultados

| Comprobación | Resultado |
|---|---|
| Artefacto | `Pipeline` con `IsolationForest` final; SHA-256 `d27f68711fcb0f6657611bd7feb17759bc4fae36b9e61fbd5ca8d1190128125a` (coincide con la reconciliación del 9-oct) |
| Manifiesto | SHA-256 `564b3a080e22f20731d3a9ec8bde251cc166ce37be8e78e5247e4e3ed1e8fb5e` |
| `offset_` del Isolation Forest | **−0,5** (`contamination = "auto"`) |
| `score_samples − decision_function − offset_` en 256 filas | desvío máximo **0,0** |
| Umbral que usa el motor | **−0,568892**, leído de `detectors.if_recalibrado_2026_09.calibration.threshold` con la regla `score < threshold` — la misma lectura que `motor_decision.load_threshold` |
| Umbral del informe (escala `decision_function`) | −0,06889178778834089 |
| Diferencia entre ambos, ya en la misma escala | **2,1·10⁻⁷** |

## Lectura

- La promoción **no cambió la decisión**: −0,06889179 − 0,5 = −0,56889179 frente a los
  −0,568892 del manifiesto.
- **La diferencia de 2,1·10⁻⁷ es redondeo**: el manifiesto guarda el umbral con seis
  decimales. El umbral efectivo en producción es, por tanto, el redondeado. Solo cambiaría
  la decisión de una ventana cuyo score cayera dentro de ese intervalo de 2·10⁻⁷; se
  declara, no se corrige.
- Las filas son sintéticas a propósito: la relación entre las dos funciones es
  algebraica (`decision_function = score_samples − offset_`) y no depende de los datos.
  Lo que se verifica es el artefacto y el umbral, no el desempeño.
