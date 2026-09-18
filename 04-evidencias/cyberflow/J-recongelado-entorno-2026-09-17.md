# Intento de recongelar el entorno sobre Python 3.12, y por qué se revirtió

**2026-09-17.** Ejecutado sobre `cyberflow-sensor`.

---

## 1. Por qué se intentó

El sensor tiene Python 3.12.3. `requirements-model.txt` fija el entorno para
CPython 3.14.4, y **tres de sus seis dependencias no existen** para 3.12:

| Fijado | Máximo disponible para cp312 |
|---|---|
| `numpy==2.5.1` | 2.2.6 |
| `scikit-learn==1.9.0` | 1.7.2 |
| `scipy==1.18.0` | 1.16.3 |

El modelo cargaba con las versiones disponibles, pero scikit-learn avisaba:

```
Trying to unpickle estimator OneClassSVM from version 1.9.0 when using
version 1.7.2. This might lead to breaking code or invalid results.
```

La hipótesis era que, al ir a recalibrarse con datos reales de todos modos,
salía más barato recongelar el entorno sobre 3.12 que montar 3.14.

## 2. Qué se hizo

Se ejecutó **el protocolo de calibración publicado**, sin modificarlo: mismo
dataset, mismos hiperparámetros, mismas semillas de estabilidad, mismas
particiones. Lo único que cambió fue el intérprete y las versiones de las
bibliotecas.

```
preflight  -> train 132 episodios / 824 filas
              validation 44 / 273
              anomalies 132 / 179        (todas las comprobaciones pasan)
execute-once -> codigo de salida 0
```

## 3. El resultado

| Detector | Detecciones 3.14 → 3.12 | Umbral | Hash del modelo |
|---|---|---|---|
| `ocsvm_scaled` **(desplegado)** | 158 → 158 | igual | distinto |
| `lof_scaled` | 77 → 77 | igual | distinto |
| `elliptic_envelope_scaled` | 49 → 49 | **distinto** | distinto |
| `if_exact_collapsed` | 103 → 103 | **distinto** | distinto |
| `if_uniform` | 103 → 103 | **distinto** | distinto |
| **`if_primary_weighted`** | **97 → 103** | **distinto** | distinto |
| `if_scaled_weighted` | 97 → 103 | **distinto** | distinto |

> **Corrección del 2026-09-18.** La primera versión de esta tabla comparaba solo
> el número de detecciones y daba por exactos a `elliptic_envelope_scaled`,
> `if_exact_collapsed` e `if_uniform`. Al automatizar la comprobación con
> `scripts/analysis/verificar_reproduccion.py` apareció que sus **umbrales
> también cambian**, aunque el recuento coincida. Solo el OCSVM y el LOF
> conservan el umbral, y **ningún modelo conserva el hash**. Comparar
> recuentos no basta.

Los umbrales lo explican:

```
if_primary_weighted   antes  -0.50606563
if_primary_weighted   ahora  -0.55456155
if_exact_collapsed (sin ponderar), semilla 20260817, ahora  -0.55456155
```

El modelo **ponderado** pasó a dar exactamente el mismo umbral que el **no
ponderado**.

## 4. La causa, medida

```python
sklearn 1.7.2
IsolationForest.fit(self, X, y=None, sample_weight=None)

# 300 filas de 28 columnas, peso 20x en las primeras 50
delta maximo con y sin sample_weight: 0.0000000000
```

**`IsolationForest.fit` acepta `sample_weight`, no emite aviso, no falla, y lo
ignora por completo.**

El protocolo `PM-multilayer-v2-v1` pondera cada fila por
`1/filas_por_episodio` para corregir un desbalance medido: **5 de 132 episodios
concentran 261 de 824 filas de entrenamiento, el 31,7 %**. Bajo scikit-learn
1.7.2 esa corrección no se aplica, y nada lo indica.

## 5. Por qué importa para la tesis

`if_primary_weighted` es, según el propio manifiesto, **la conclusión
principal** del modelado:

> *if_primary_weighted es la conclusion principal; LOF/OCSVM y las demas ramas
> IF son comparadores/sensibilidad.*

Y el campo `deviation_from_pm_f1_v1` justifica esa elección diciendo que se
verificó que `sample_weight` **sí** cambia los scores en este dataset. Bajo
3.12 esa afirmación deja de ser cierta, pero **el manifiesto se seguiría
generando con el mismo texto**.

Es el peor tipo de fallo de reproducibilidad: el resultado sale, es plausible,
y nada avisa de que la corrección metodológica se perdió por el camino.

## 6. Decisión

**Revertido.** El entorno vuelve a fijar CPython 3.14.4, y el guardarraíl
`EXPECTED_PYTHON` del script de calibración se mantiene — ahora con la
justificación escrita en el código.

| Para qué | Entorno |
|---|---|
| Desplegar y ver el sistema funcionando | 3.12 sirve: el OCSVM conserva resultado y umbral |
| Calibrar, reentrenar o publicar una cifra | **3.14.4, sin excepción** |

## 7. Una tensión que esto sacó a la luz

El manifiesto declara `if_primary_weighted` como modelo principal, pero
**el motor despliega `ocsvm_scaled`**. Si el modelo principal de la tesis no es
el que se ejecuta en producción, hay que explicarlo o alinearlo. No es
consecuencia de este experimento: ya estaba así.

## 8. Efecto colateral detectado

Al verificar la integridad de los datos se descubrió que **dos de los trece
hashes publicados no cuadraban**:

```
sha256sum -c docs/dataset/SHA256SUMS
  ...
  sha256sum: WARNING: 2 computed checksums did NOT match
```

Causa: los CSV publicados son **CRLF** —el módulo `csv` de Python escribe
`
` por defecto— y su hash se calculó sobre esos bytes. Al commitear desde
Windows, `core.autocrlf` los **normalizó a LF**, y esos bytes se publicaron.
Los datos no estaban alterados, pero **la comprobación de integridad fallaba**,
que es exactamente lo que ese fichero existe para impedir.

> **Corrección del 2026-09-18.** La primera versión de este apartado decía que
> la conversión había sido de LF a CRLF. Es al revés: se comprobó contando los
> bytes del fichero original, que tiene 1374 retornos de carro, uno por línea.

Corregido restaurando los bytes originales y añadiendo `.gitattributes` para
que los artefactos publicados no se conviertan en ninguna plataforma.
Verificado: 13 de 13 correctos, y los blobs de Git coinciden con el manifiesto.
