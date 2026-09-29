# L · Tráfico representativo y recalibración en seco (sensor1)

**Fecha:** 29 de septiembre de 2026
**Máquina:** `cyberflow-sensor1` (10.10.60.11), red real de producción
**Objetivo:** comprobar, con datos, (a) si la línea base ya tiene tráfico
representativo —lo que bloqueaba la tesis el 17-sep— y (b) cuánto baja el FPR una
recalibración, **sin tocar el modelo desplegado ni el piloto en curso**.

## 1. Composición de la línea base (medida)

Sobre `artifacts/linea-base/multilayer-v3.csv` (336 964 filas, 45 entidades,
campaña `piloto-con-dns`):

| Señal | Valor |
|---|---|
| Ventanas con L7 (HTTP/DNS/TLS) | **44,2 %** — HTTP 109 576 · DNS 100 387 · TLS 48 592 |
| Ventanas con datos TCP (segmentos>0) | 18,6 % |
| Ventanas con SYN>0 | 21,2 % |
| «Solo control» (ni L7 ni datos ni SYN) | 55,7 % |

Las 15 entidades con más filas son **hosts de usuario** repartidos por
VLAN 10/20/30/40/100 (10.10.10.20, 10.10.30.10, 10.10.20.2x, 10.10.40.10, …),
~7 % de filas cada una — **no** las interfaces de pfSense emitiendo CARP. El
piloto `piloto-con-dns` inyectó tráfico representativo. Esto **supera el bloqueo
del 17-sep** (entonces el 87 % era plano de control y las VLAN de usuarios no
tenían estaciones).

## 2. Recalibración en seco (no invasiva)

Se ejecutó el pipeline hasta evaluar, escribiendo en `/tmp/recal`, **sin
`congelar`**: el modelo desplegado (`ocsvm_scaled`), la configuración
(`calibrado_en_esta_red=false`) y el piloto quedaron intactos.

**Particionado** (`particionar_linea_base.py --solo-elegibles`):

```
filas elegibles : 337 980       horas cubiertas : 69,6
train 204 148 · validation 65 633 · test 65 421
descartadas por guarda : 2 778
fuga_temporal : ninguna          conjuntos_vacios : ninguno
```

**Entrenamiento y umbral** (`entrenar_preliminar.py`, IsolationForest 500 árboles,
umbral = percentil `alpha=0,05` de validación, congelado antes de ver `test`):

```
FPR validacion : 0,0500
FPR TEST       : 0,0445   (4,45 %)
umbral (decision_function) : -0,068892
```

## 3. Resultado

| | Sin recalibrar (17-sep) | Recalibrado en seco (29-sep) |
|---|---|---|
| FPR sobre tráfico normal | **92,4 %** | **4,45 %** |

La recalibración sobre la base enriquecida por el piloto baja los falsos positivos
**~20×** y clava el objetivo (`alpha` 5 %), **sin fuga temporal** (partición por
bloques horarios con banda de guarda de 60 s).

**Matiz honesto.** Esto mide FPR sobre tráfico **normal** (no hay ataques en la
base): demuestra que el modelo deja de gritar «lobo», no su capacidad de
**detección**. Esa otra mitad se validará con la corrida de la Kali del piloto.

## 2.bis Detección preliminar (cross-dataset, indicativa)

Se puntuó el conjunto de **anomalías congelado** (`artifacts/dataset/multilayer-v2-anomalies.csv`,
179 ventanas) con este mismo modelo preliminar y su umbral:

```
detectadas (score < umbral): 81 / 179  ->  TPR = 45,3 %
score anomalias: min -0,1744 · mediana -0,0645 · max 0,069   (umbral -0,068892)
```

**No es la cifra de tesis, y es un piso pesimista.** Esas 179 anomalías vienen de
**otra red** (el dataset v2 original), puntuadas por un modelo entrenado sobre el
**normal de sensor1**: las escalas de features no coinciden y la mediana de score
queda pegada al umbral. Como referencia, el OCSVM desplegado —entrenado sobre el
*mismo* normal que esas anomalías— sacaba 158/179 (88 %). La cifra publicable de
detección exige la **Kali sobre la red de sensor1** (misma distribución que el
normal de entrenamiento). Harness: `scripts/modeling/puntuar_deteccion.py`.

Modelo preliminar persistido (no es el desplegado):
`artifacts/preliminar/ensayo-if-v2.joblib` + `ensayo-if-v2.json`.

## 4. Pendiente para cerrar

- Corrida de la Kali → medir detección (TPR) con este mismo umbral.
- **Congelar** el modelo preliminar → `calibrado_en_esta_red=true` (toca el modelo
  desplegado; coordinar con el fin del piloto).
- Con ambas cosas, desbloquear `v1.0.0` (P2).
