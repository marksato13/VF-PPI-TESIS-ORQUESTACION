# Procedimiento de las fases implementadas

**5 de septiembre de 2026** · Consolidado desde el repositorio del producto.

Este documento responde a una sola pregunta por fase: **¿qué se hizo, con qué
comando, y qué artefacto verificable produjo?** No repite el contenido del
producto; lo referencia con su ruta y su hash.

Toda cifra se verifica en la fuente primaria que aquí se indica. Ninguna se
escribe de memoria.

---

## Advertencia: la numeración de las dos carpetas no coincide

Es la trampa más fácil de este repositorio. `F05` aquí **no** es
`fase05-` en el producto:

| Aquí | En el producto | Contenido |
|---|---|---|
| `F01-infraestructura` | `docs/fase00-infraestructura/` | VM, red, acceso |
| `F02-diseno-experimental` | `docs/fase01-diseno-experimental/` | Campañas, preflight, ledger |
| `F03-features` | `docs/fase02-features-multicapa/` | Diccionario y extractor |
| `F04-dataset` | `docs/fase03-dataset/` | 182 documentos de campaña |
| `F05-modelado` | `docs/fase04-modelado/` | Los 7 candidatos y el congelado |
| `F06-motor-tiempo-real` | `docs/fase05-motor-tiempo-real/` | Motor y enforcement |
| `F07-dashboard` | `docs/fase06-dashboard/` | Panel operativo |
| `F08-validacion-operacional` | `docs/fase07-validacion-final/` | F6, 58 corridas |
| `F09-tesis-y-publicacion` | `docs/entregables/` | Los cuatro entregables |

`F00-gobernanza` no tiene carpeta equivalente: vive en este repositorio.

---

## F03 · Contrato de variables

**Producto:** `docs/fase02-features-multicapa/`

1. `01-diccionario-multicapa-G5.md` define 14 variables causales por IP
   iniciadora, con ventanas de 10, 30 y 60 s y tres señales L7 pasivas.
2. `02-validacion-extractor-G5.md` registra las pruebas sintéticas, la
   regresión HTTP y una campaña DNS con calentamiento de 60 s.
3. `03-diccionario-multicapa-v2.md` extiende a **28 variables** y se **genera
   desde el extractor congelado**, no se redacta a mano:
   `scripts/entregables/generar_diccionario_features.py`.

**Límite declarado y no resuelto:** `tls_handshake_failure_ratio_60s` es no
observable en esta configuración y permanece constante en todo el dataset. De
las 28, **27 tienen variación observable**.

| Artefacto | SHA-256 |
|---|---|
| `configs/features/multilayer-v2.json` | `1445ccd4f33f…` |
| `scripts/features/extract_multilayer_v2.py` | `c85f67a37d37…` |

---

## F04 · Dataset

**Producto:** `docs/fase03-dataset/` — 182 documentos, uno por campaña.

Cada campaña pasa por el orquestador `scripts/campaign/`, que produce
manifiesto, inventario, contadores, serie temporal del Sensor, segmento EVE y
hashes. **Los artefactos brutos no entran en Git**; el dataset derivado sí.

Composición: **220 episodios normales · 1.373 ventanas** repartidas en
entrenamiento 824, validación 273 y prueba 276, más **179 ventanas de
anomalías** para evaluación — 161 originadas genuinamente en Kali y 18
heredadas de una generación anterior, que **se reportan por separado**.

Partición **disjunta por episodio**: ningún episodio se reparte entre
particiones, y los gates lo comprueban.

| Artefacto | SHA-256 |
|---|---|
| `artifacts/dataset/multilayer-v2-normal.csv` | `3846d44c0fe3…` |
| `artifacts/dataset/multilayer-v2-anomalies.csv` | `d115ef987cbd…` |

---

## F05 · Modelado

**Producto:** `docs/fase04-modelado/` — 11 documentos.

El orden real, que no es el de los números de archivo:

1. `03-diagnostico-pipeline-multilayer-v2.md` — diagnóstico del pipeline.
2. `04-protocolo-…-y-hoja-de-ruta.md` — protocolo `PM-multilayer-v2-v1`.
3. `05-resultado-calibracion-….md` — calibración, vía
   `scripts/modeling/calibrate_multilayer_v2_v1.py`.
4. `06-modelo-final-congelado-ocsvm.md` — **el modelo congelado**.
5. `07-metricas-…-7-modelos.md` y `07-ablacion-multicapa.md` — comparación y
   ablación, vía `scripts/modeling/experiments/ablacion_multicapa.py`.
6. `08-significancia-entre-modelos.md` — McNemar con corrección de Holm sobre
   21 pares.
7. `09-validacion-cruzada-y-estabilidad.md` — estabilidad del umbral.
8. `10-protocolo-determinismo-y-semillas.md` — determinismo.

**Calibración del modelo congelado**, leída del manifiesto:

```
ocsvm_scaled     alpha 0,05 · k 13 · umbral 1,8126087939765134
                 comparación: score < threshold
                 n_windows 273 · train_rows 824
                 strict_alert_count 13 en 10 episodios
```

| Artefacto | SHA-256 |
|---|---|
| `artifacts/model/ocsvm_scaled.joblib` | `af9b50c29f83…` |
| `artifacts/model/manifest.json` | `0a1e8c52dc32…` |

**Dos cosas que el jurado va a mirar, y conviene tener escritas:**

El manifiesto registra `role = sensitivity_or_comparator` para `ocsvm_scaled`,
mientras que la política declara `if_primary_weighted` como principal. **El
artefacto congelado contradice su política registrada.** La elección se hizo
por desempeño empírico medido, no por la regla por defecto, y así consta.

`if_uniform` e `if_exact_collapsed` comparten umbral exacto
(`-0.5543415531007138`) **y contenido idéntico por hash**. Dos candidatos que
debían diferir, no difieren.

---

## F06 · Motor en tiempo real

**Producto:** `docs/fase05-motor-tiempo-real/`

`scripts/engine/motor_decision.py` reusa directamente el extractor congelado,
sin duplicar fórmulas. En `ALERT` real —no en el heurístico de ventana sin
tráfico— bloquea la IP LAN ofensora por nftables **en el propio Sensor**, que
ya es el router LAN↔DMZ, con expiración nativa de 120 s. Sin SSH entre VMs.

```
ppi-motor-capture.service     captura al anillo de PCAP
ppi-motor.service             puntúa y decide
ppi-enforce                   helper raíz que aplica el bloqueo
```

**Dos fallos reales de producción, encontrados y corregidos** — no en pruebas
sintéticas: un `set -e` que silenciaba el script para el caso normal, y un
bucle de re-bloqueo infinito por podar memoria según el reloj en vez de según
el tamaño. `02-fp-ventana-sin-paquetes.md` documenta el tercero.

**Limitaciones declaradas:** no hay nivel `LIMIT` intermedio, porque exigiría
un segundo umbral sin calibrar; y el anillo guarda unos 120 s, menos que una
campaña offline completa.

| Artefacto | SHA-256 |
|---|---|
| `scripts/engine/motor_decision.py` | `b46333b04b75…` |

---

## F07 · Dashboard

**Producto:** `docs/fase06-dashboard/`

`ppi-dashboard.service` en VM02, puerto `8788` **solo en loopback**, acceso
remoto exclusivamente por túnel SSH. Solo lectura: no ejecuta ninguna acción.

Umbral y métricas se **leen del `manifest.json` congelado, no están escritos en
el código**. Validado end-to-end: una IP bloqueada automáticamente por el motor
apareció en el panel con su expiración exacta.

Hay manual de usuario aparte: `02-manual-dashboard-analista.md`.

---

## F08 · Validación operacional

**Producto:** `docs/fase07-validacion-final/`

`scripts/f6/run_f6.py` ejecuta las corridas y `scripts/f6/analyze_f6.py` las
analiza. **Dos pases de 29 corridas** con el motor activo, más 2 pruebas de
aislamiento.

Confirmado: detección y bloqueo inline con lead time mediano de **8,0 s**
(rango 6,1–13,7, n = 8), el heurístico de fuerza bruta disparando en
producción, y **cero caídas en 58 corridas** — 55 con verificación explícita de
servicios.

**Las dos limitaciones que más pesan, medidas y declaradas:**

1. **El FPR benigno de 4,71 % en laboratorio no se sostiene en operación.** En
   campaña se midió **25,81 %** (pase 1) y **22,97 %** (pase 2). Y en
   aislamiento, un `iperf-tcp 200M` legítimo produjo un falso positivo genuino
   que **bloqueó al cliente legítimo**: los scores del tráfico pesado se apiñan
   en el margen del umbral. Es la debilidad más importante ante el jurado.
2. **El motor se atrasa bajo carga sostenida**, hasta 161 s, por reparsear el
   anillo de PCAP completo en cada ciclo.

Ninguna se ha corregido: hacerlo exigiría recalibrar, y recalibrar sin una
evaluación nueva invalidaría el congelamiento. Las mejoras candidatas están en
`docs/07-mejoras-futuras/01-debilidades-y-mejoras.md`, filas #11 y #12.

| Artefacto | SHA-256 |
|---|---|
| `results/f6/f6_resultados.jsonl` | `83a8d416cff0…` |

Existe también `f6_resultados.pass1-contaminado.jsonl`, conservado a
propósito: un pase descartado que **no se borró**.

---

## Cómo verificar todo esto sin fiarse de este documento

```bash
stack/bin/ppi-trace cifra 88,8        # ¿de dónde sale un número?
stack/bin/ppi-trace req  REQ-013      # cadena completa de un requisito
stack/bin/ppi-trace check             # ¿sigue siendo cierto lo declarado?
stack/bin/ppi-inventario              # 639 archivos clasificados
```

Los hashes publicados se comprueban contra `docs/dataset/SHA256SUMS` del
producto.
