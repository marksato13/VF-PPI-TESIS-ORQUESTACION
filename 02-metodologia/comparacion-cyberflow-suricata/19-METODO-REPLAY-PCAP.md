# 19 · Método de comparación por replay de PCAP (offline)

**Fecha:** 2026-10-02
**Estado:** método recomendado para la comparación de **detección** (P0). Validado
contra el código real; ver "Viabilidad" abajo.

## Problema que resuelve

La comparación en vivo por SPAN tropezaba con tres cosas:

1. **Relojes (P0-05):** Sensor1 y el comparador tienen ~180 s de desfase y el NTP
   está cerrado en VLAN 60. Sin reloj común no se puede afirmar "quién detectó
   antes" por hora de pared. La única salida en vivo era abrir UDP/123 en pfSense
   (infra de Franco: riesgo, respaldo, rollback).
2. **Equivalencia de entrada:** aunque ambos reciben el mismo PG-SPAN, hay que
   *probar* que recibieron exactamente lo mismo (drops, duplicados, VLAN).
3. **Reproducibilidad:** el asesor pide un experimento que se pueda re-ejecutar.

## La idea

Capturar cada episodio de ataque **una sola vez** como PCAP etiquetado, y luego
pasar **el mismo PCAP** por los dos detectores **en modo offline**. El tiempo de
referencia es el **timestamp del propio paquete** (está dentro del PCAP), idéntico
para ambos → **no hace falta NTP ni tocar pfSense**.

```text
                 episodio.pcap  (capturado 1 vez, etiquetado: inicio/fin/tipo)
                 /                          \
   suricata -r episodio.pcap        extract_multilayer_v2 (lee el PCAP)
        -> eve.json (alertas,         -> CSV de ventanas con window_end_utc
           ts del PCAP)                  -> scorer: decision_function < umbral
                 \                          /
            comparar primera alerta de cada uno contra t_inicio del PCAP
```

## Por qué es metodológicamente superior (responde al asesor)

- **Input idéntico por construcción.** Es un experimento controlado: la única
  variable es el detector. (La duda del "un solo switch" se disuelve: para
  *detección*, mismo input = correcto, no debilita.)
- **Sin confound de reloj.** El tiempo sale del paquete, no de dos relojes
  desincronizados. "Quién detecta primero" se mide contra la misma línea temporal.
- **Reproducible.** El PCAP es el artefacto; cualquiera re-corre ambos detectores
  y obtiene lo mismo. El run en vivo por SPAN queda como **confirmación
  secundaria** de operación en tiempo real, no como la medición principal.

## Viabilidad (validado contra el código, 2026-10-02)

- **Suricata** lee PCAP offline con `suricata -r` (modo estándar) y emite
  `eve.json` con el `timestamp` de cada paquete.
- **CyberFlow:** `scripts/features/extract_multilayer_v2.py` **ya parsea PCAP**
  (`iter_pcap_frames`, `parse_ethernet_ipv4`) y **emite `window_end_utc` por
  ventana**. El scoring con el modelo congelado existe en
  `scripts/modeling/puntuar_deteccion.py` (`decision_function(x) < umbral`).
- **Falta construir (pequeño):** un scorer **por ventana** — variante de
  `puntuar_deteccion.py` que conserve `window_end_utc` y marque la **primera**
  ventana con `score < umbral` (≈20 líneas). Es lo único nuevo.

## Parámetros verificados del detector desplegado (2026-10-02, por SSH)

Para que el replay reproduzca EXACTAMENTE el detector en vivo (`ppi-motor`):

- **Modelo:** `artifacts/preliminar/if_recalibrado_desplegable.joblib` — es un
  **`Pipeline` de sklearn** (escalador + IsolationForest). Se puntúa con
  `pipeline.score_samples(X)`; **ALERT si `score < umbral`**.
- **Umbral:** NO está en el joblib. Sale del manifest:
  `artifacts/preliminar/manifest-if-recalibrado.json`
  → `detectors["if_recalibrado_2026_09"]["calibration"]["threshold"]`
  (comparación declarada `"score < threshold"`).
- **Features:** **28** (`manifest["feature_names"]`), esquema **v2**
  (`configs/features/multilayer-v2.json`). *(Esto confirma que el "31 variables"
  de una arista del panel estaba mal: son 28.)*
- **Extractor:** `scripts/features/extract_multilayer_v2.py` (NO v3).
- **entity-network:** `10.10.0.0/16`. El motor además excluye
  `10.10.60.11,10.10.10.30` y protocolos `112,240` (diferencia menor al reproducir
  offline con el extractor; no afecta a las entidades de ataque).
- El scorer `20-puntuar-por-ventana.py` ya implementa exactamente esto
  (`score_samples < threshold`, features/umbral del manifest). El runner `22-` usa
  estos valores por defecto.

## Procedimiento por episodio

1. **Capturar** el episodio en un punto (p. ej. el propio espejo) a
   `episodio-<id>.pcap`, con metadatos: `t_inicio`, `t_fin`, familia, origen,
   destino, intensidad. (Un solo PCAP; al correrlo offline ambos ven lo mismo.)
2. **Suricata:** `suricata -r episodio-<id>.pcap -l salida/<id>/` con la versión y
   reglas congeladas (ET Open SHA ya fijado) → `eve.json`.
3. **CyberFlow:** extraer features del mismo PCAP (reutilizando el `eve.json` de
   Suricata para la capa L7, igual que en vivo) → CSV de ventanas → scorer por
   ventana con el modelo/umbral **desplegado en Sensor1** (no otro).
4. **Medir** (ver `03-METRICAS-Y-EVIDENCIAS.md`):
   - `tiempo_deteccion = window_end_utc(primera ventana con alerta) − t_inicio`
     (CyberFlow) y `timestamp(primera alerta) − t_inicio` (Suricata).
   - TPR/FPR/FN por familia; pps/bps/tamaño de paquete del PCAP.

## Qué NO mide (honestidad metodológica)

- **Latencia de red real** ni jitter del enforcement en vivo: eso es del run en
  vivo / fase B.
- **Bloqueo inline comparado:** offline se mide la *decisión* de bloquear y su
  latencia; el corte real (nftables de CyberFlow vs drop de Suricata IPS) es la
  **fase B** (`02-ARQUITECTURA.md`, escenario B), que sí puede requerir rama
  inline. Para P0 basta: detección + decisión.

## Efecto en el plan

- **P0-05 (relojes/NTP): deja de ser bloqueante para P0.** No se aplica la regla
  NTP en pfSense para esto. (Si luego se quiere el run en vivo con hora de pared,
  se retoma; para P0 no hace falta.)
- **P0-07 (eventos comparables):** la regla de "primera alerta" se define sobre la
  línea temporal del PCAP, no sobre dos relojes.
- Habilita avanzar a P0-06/07/08 una vez firmado P0-01.
