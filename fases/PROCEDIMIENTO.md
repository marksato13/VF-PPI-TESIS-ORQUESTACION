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

## F01 · Infraestructura

**Producto:** `docs/fase00-infraestructura/`

Cinco máquinas virtuales sobre VMware ESXi, tres redes aisladas:

| VM | Función | PPI-MGMT | PPI-LAN | PPI-DMZ |
|---|---|---|---|---|
| VM01 | Administración y agentes | `10.10.10.10` | — | — |
| VM02 | Sensor, router, Suricata, motor | `10.10.10.20` | `10.20.0.1` | `10.30.0.1` |
| VM03 | Servidor protegido | `10.10.10.30` | — | `10.30.0.10` |
| VM04 | Kali, ataques controlados | `10.10.10.40` | `10.20.0.100` | — |
| VM05 | Cliente legítimo | `10.10.10.50` | `10.20.0.20` | — |

Todo el tráfico entre Cliente/Kali y el Servidor **cruza el Sensor**, que tiene
`ip_forward=1` y política de reenvío con nftables.

Se despliega con Ansible, en este orden:

```
ansible/playbooks/00-validar-controlador.yml
                  01-comprobar-conectividad.yml
                  02-auditar-recursos.yml
                  03-configurar-servicios-servidor.yml
                  04-configurar-cliente-f1.yml
                  05-ajustar-captura-suricata.yml
```

Acceso por la cuenta técnica `useransible` con claves Ed25519. **Sin sudo
general**: en VM02–VM05 solo puede ejecutar el reinicio exacto
`/usr/bin/systemctl reboot --no-wall`, y en el Sensor tres helpers versionados
—`ppi-suricata-metrics`, `ppi-pcap-control` y `ppi-enforce`—. La prueba
negativa con `/usr/bin/id` **falla en las cuatro VMs**, que es lo que se
quería.

VM01 tiene un segundo disco de 150 GiB montado por UUID en `/srv/ppi-evidence`,
con `nosuid,nodev,noexec`. Sobrevivió a un reinicio con el mismo UUID.
Auditable con `scripts/storage/audit_evidence_disk.py`.

**El riesgo que se encontró y se cerró:** las NIC externas de `172.17.25.0/24`
permitían **saltarse el Sensor**. No era hipotético — VM01 alcanzó el TCP/22
del Servidor por `172.17.25.112` sin cruzarlo. Durante campañas oficiales,
esas NIC deben estar desconectadas en ESXi en VM02–VM05.

---

## F02 · Diseño experimental

**Producto:** `docs/fase01-diseno-experimental/` — 19 documentos.

Nada se ejecuta a mano. El orquestador está en `scripts/campaign/`:

```
start.sh · stop.sh          arranque y cierre de campaña
run-f1.sh                   tráfico benigno desde el Cliente
run-f1-kali.sh              tráfico anómalo desde Kali
sample-sensor.sh            serie temporal del Sensor
archive-failed-attempt.sh   archiva un intento fallido SIN borrarlo
common.sh                   preflight y gates compartidos
```

Cada campaña produce manifiesto, inventario, contadores, serie temporal del
Sensor, segmento EVE y hashes.

### Los techos de carga están en el código, no en un documento

`scripts/f1/run-benign.sh` **rechaza** cualquier valor fuera de su lista
blanca. No es una recomendación escrita: es una condición que aborta:

```
TCP     10M · 25M · 50M · 100M · 200M      máximo 200 Mbit/s
UDP     1M · 10M · 25M · 50M               máximo  50 Mbit/s
HTTP    2M · 5M · 10M · 20M bytes/s        máximo  20 MB/s
tamaño  10MB · 100MB · 500MB · 1GB
```

Y hay un control adicional que un simple techo no daría: un presupuesto
conjunto de `1459200000` bytes, porque una combinación de valores
individualmente válidos —200M durante 600 s— sí sería excesiva.

Existe por una razón medida: una prueba iperf3 **sin** pacing alcanzó
2,58 Gbit/s y produjo **389.932 descartes**. Está excluida del dataset.

### Gates G0–G7

La progresión de comprobaciones antes de dar por buena una campaña. Los que
dejaron documento propio:

- **G0** línea base y auditoría inicial
- **G2** calibración de carga, TCP/UDP y HTTP/HTTPS
- **G3** validación del orquestador — `CAL-F1-DNS-003`: 6 paquetes, cero
  descartes, 7 registros EVE exactos y 7 muestras del Sensor
- **G4** captura PCAP por campaña, con `ppi-pcap-control`. En
  `CAL-G4-HTTP-001`, **7.242 de 8.484 paquetes IPv4 (85,36 %)** midieron entre
  500 y 1500 bytes, cero descartes y SHA remoto y local coincidentes
- **G5** contrato de variables (pasa a F03)
- **G7** aislamiento, persistencia y NTP interno

**Un fallo real y cómo se resolvió:** el preflight de `HTTP-C8/R01` se detuvo
sin crear artefactos porque el Sensor perdió `NTPSynchronized=yes` tras unas
18 horas sin alcanzar sus fuentes públicas por la NIC aislada. Se montó la
jerarquía VM01 → Sensor → VM03–VM05; `prefer require` —sin `trust`— resolvió
la espera. Tres gates consecutivos pasaron con desfases por debajo de 100 ms.

### Nada se borra

`17-archivado-intentos-fallidos.md` fija la regla. El intento rechazado
`F1N-HTTP-C8-R01` se archivó como `attempt-01` **sin eliminarlo**, con los
hashes del manifiesto, el ledger y ambos PCAP verificados de nuevo. El
reintento reutiliza el identificador canónico y vuelve a pasar todos los gates.

Esa misma disciplina explica que en F08 exista
`f6_resultados.pass1-contaminado.jsonl`: un pase descartado que se conserva.

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
