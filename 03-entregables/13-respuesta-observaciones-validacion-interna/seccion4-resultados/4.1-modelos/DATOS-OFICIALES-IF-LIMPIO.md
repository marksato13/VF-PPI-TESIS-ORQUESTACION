# Datos oficiales del modelo `if_limpio_2026_10` (referencia vigente)

**Data oficial: 337 719 ventanas** → tras la banda de guarda, **334 941** (entrenamiento 203 967 + validación 65 553 + prueba 65 421).
Es la data con la que se entrenó el modelo desplegado y se calibró el umbral que usa el motor en vivo
(α = 0,01 → `-0.6223889502095352`, manifiesto `limpio-alfa001-B`). Sustituye como referencia a «337 980» y a «337 799 / 335 021».

**Descarga** (repositorio del producto, Release `datos-if-limpio-2026-10`):
<https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/releases/tag/datos-if-limpio-2026-10>
— `if-limpio-2026-10-particionado-limpio.csv.gz` (7,5 MB, sha `84697fc3efc4c4c9eb07017582d52b4852d6b77712b3bbbdfe0fc29670ba827e`;
al descomprimir, `5ef83b32…1b573`), las dos listas de exclusión, el manifiesto y `SHA256SUMS`.

## Fichero físico

| Campo | Valor |
|---|---|
| Fichero | Sensor1 `/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/particionado-limpio.csv` |
| SHA-256 | `5ef83b32469238b74eb16c2c2ff422a7757711318c0c77646e67bb966e61b573` |
| Filas / bytes | 337 980 / 149 543 885 (supera el límite de GitHub para un repositorio: se publica comprimido como asset del Release del producto) |
| Origen | `artifacts/aprendizaje/base/particionado-nota-L.csv` (sha `bdf6f641…`), partición nota L sin fuga temporal |
| Modelo | `if_limpio_2026_10_desplegable.joblib`, sha `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60` |

No existe un CSV de 337 719 filas: la data oficial es ese fichero **con dos exclusiones explícitas por clave**
(`campaign_id`, `entity_ip`, `window_end_utc`), publicadas aquí.

## Cadena de recuentos (verificada contando el CSV en Sensor1, 13-nov-2026)

| Paso | Filas | Lista |
|---|---:|---|
| `particionado-limpio.csv` | 337 980 | — |
| − ventanas Kali 10.10.20.30 excluidas del entrenamiento (`eligible_training=False`, ráfaga 27-sep 21:35–22:05 UTC) | −181 | `calibracion-alfa-2026-10-24/datos-sensor/exclusiones-entrenamiento-181.csv` (sha `5403ed33…`) |
| − ventanas Kali 10.10.20.30 en validación (excluidas solo de la calibración α; normalidad no confirmada, no se etiquetan como ataque) | −80 | `calibracion-alfa-2026-10-24/validacion-kali-80-excluidas.csv` (sha `a8d1de2d…`) |
| **Data oficial** | **337 719** | |
| − banda de guarda de 60 s al inicio de cada bloque de 2 h (`particion=descartada_guarda`) | −2 778 | columna `particion` |
| **Tras partición y depuración** | **334 941** | |
| · entrenamiento | 203 967 | `particion=train`, `eligible_training=True` |
| · validación (calibración del umbral) | 65 553 | `particion=validation` sin las 80 |
| · prueba normal (= `oro.csv`, sha `08604ae3…`) | 65 421 | `particion=test`; incluye 74 ventanas de 10.10.20.30 sin cambios |

Umbral: `numpy.quantile(score_samples(validación 65 553), α, method="linear")`; α = 0,01 → `-0.6223889502095352`
(`calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json`, columna `validacion_sin_kali_65553`).
Con la validación completa (65 633) el mismo α daría `-0.6223738394125686`; el α = 0,05 inicial (`-0.5693969936322356`)
sí se calibró sobre 65 633 y es histórico.

## Qué documentos quedan como históricos

Los informes fechados que citan 337 980, 204 148 / 65 633 / 65 421 o el umbral α = 0,05 sobre 65 633 describen el
modelo recalibrado anterior o el estado de su fecha y **no se reescriben**. Para el modelo vigente manda este documento
y `DATOS-OFICIALES-IF-LIMPIO.json`.
