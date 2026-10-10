# Q — Promoción reproducible del modelo desplegado (Sensor1, 2026-10-10)

**Qué se comprueba.** Que el paso publicado `scripts/modeling/promover_preliminar.py`
convierte el paquete de `entrenar_preliminar.py` en el artefacto que carga el motor, y
que, aplicado al **paquete original** del modelo vivo, reproduce ese modelo. Responde a la
revisión: «documentar o publicar el paso que convierte el paquete preliminar en el
Pipeline desplegable y genera su manifiesto, y verificar conjuntamente orden de
variables, hash y equivalencia».

Además se publican aquí, por primera vez, el **manifiesto operativo** y el **informe de
calibración** del modelo vivo.

## Ficheros

| Fichero | Qué es | SHA-256 |
|---|---|---|
| [`manifest-if-recalibrado.json`](manifest-if-recalibrado.json) | Manifiesto **operativo** que usan motor y panel en Sensor1 | `564b3a080e22f20731d3a9ec8bde251cc166ce37be8e78e5247e4e3ed1e8fb5e` |
| [`ensayo-if-v2.json`](ensayo-if-v2.json) | Informe de calibración del 29-sep (`entrenar_preliminar.py`) | `ec3ed06304fdbe6367ab1b69e40498980e6eed6df890f67ae5c4001f98c86421` |
| [`promocion.json`](promocion.json) | Salida de `promover_preliminar.py` sobre el paquete original | — |
| [`manifest-if-recalibrado-reproducido.json`](manifest-if-recalibrado-reproducido.json) | Manifiesto que genera la promoción | `a79fb4af5e3061b63b6b1be4d5f6be90d35e445edc762bf126fb3529055870e6` |
| [`comparacion-con-vivo.json`](comparacion-con-vivo.json) | Comparación del artefacto reproducido con el vivo | — |

El paquete original (`artifacts/preliminar/ensayo-if-v2.joblib`, SHA-256
`9a4e02645df9484037ba9386c488cc431cba4b8564c3b4892de3c5ed210c579d`) coincide con el
`salida_sha256` de su informe: la cadena paquete → informe es coherente. Los `.joblib` no
se publican (modelo recalibrado con tráfico no publicable); quedan sus hashes.

## Cómo se ejecutó

- Sensor1, usuario `m4rk`, entorno del motor: CPython 3.14.4, scikit-learn 1.9.0,
  joblib 1.5.3. 2026-10-10T04:24Z. Salida a `~/cf-deploy/reproduccion-20261010042428/`;
  **no se tocó nada desplegado**.
- Script: `promover_preliminar.py` del commit
  [`8ef1e70`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/8ef1e70a35b06aa8dad5dff267fd8cfec62f0134/scripts/modeling/promover_preliminar.py)
  de `main` (SHA del fichero `23c043ac287860d089e32ec45a3cfe3d66199fa8d126701c2daa9e00f6a1f3f6`;
  el commit siguiente solo corrige un comentario).

```bash
.venv/bin/python scripts/modeling/promover_preliminar.py \
  --paquete artifacts/preliminar/ensayo-if-v2.joblib \
  --informe artifacts/preliminar/ensayo-if-v2.json \
  --detector if_recalibrado_2026_09 \
  --salida-modelo "$REP/if_recalibrado_2026_09_desplegable.joblib" \
  --salida-manifiesto "$REP/manifest-if-recalibrado-reproducido.json" \
  --deteccion-global 0.6923076923076923 --deteccion-kali 0.6923076923076923 \
  --deteccion-fuente "nota M: 54/78 ventanas Kali"
```

> **Primer intento fallido (registrado).** La primera ejecución abortó al cargar el
> extractor: el script lo importaba sin registrarlo en `sys.modules`, cosa que el
> `@dataclass` del extractor necesita. En las pruebas no aparecía porque el motor ya había
> importado ese módulo. Se corrigió (commit `8ef1e70`) y se añadió una prueba que ejecuta
> el script en un proceso nuevo; falla con la versión anterior y pasa con la corregida.

## Resultados

| Comprobación | Resultado |
|---|---|
| Orden de variables del paquete = contrato v2 = extractor del motor | ✅ 28 variables, mismo orden |
| `score_samples − decision_function − offset_` (512 filas de control) | desvío **0,0**; `offset_ = −0,5` |
| Equivalencia del par escrito (`verificar_equivalencia_umbral`) | ✅ `EQUIVALENTE` |
| Pasos del `Pipeline` reproducido / vivo | `scaler`, `model` / `scaler`, `model` |
| Scores del reproducido frente al **vivo**, 5000 filas | diferencia máxima **0,0** |
| Umbral reproducido (exacto) frente al del manifiesto vivo | −0,5688917877883409 frente a −0,568892: **2,1·10⁻⁷** (redondeo a 6 decimales del vivo) |
| Decisiones distintas usando cada uno su umbral, 5000 filas | **0** |
| ¿Mismo fichero byte a byte? | **No**: SHA reproducido `e901ce9e…`, vivo `d27f68…` |

## Lectura

- La cadena publicada **entrenar (v2) → promover → verificar** produce un artefacto que
  el motor acepta y que, desde el mismo paquete, **se comporta igual que el desplegado**:
  mismos scores, mismo orden de variables y el mismo umbral salvo el redondeo.
- **No** es una reproducción byte a byte: los bytes del pickle difieren aunque los objetos
  sean los mismos. Por eso la auditoría se hace por comportamiento y umbral, y el hash
  sirve para identificar cada artefacto concreto, no para probar la promoción.
- El artefacto reproducido **no se desplegó**; el vivo sigue siendo `d27f68…`.
