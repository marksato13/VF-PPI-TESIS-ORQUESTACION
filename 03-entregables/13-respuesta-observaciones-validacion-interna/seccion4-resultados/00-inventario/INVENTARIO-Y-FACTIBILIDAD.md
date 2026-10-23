# Sección 4 (Results) — Inventario de evidencia y factibilidad

**Revisión:** 2026-10-23. **Marco:** reglas obligatorias del encargo (versión actual
`if_limpio_2026_10`; separar IF / heurísticos / combinado; separar ventana / episodio /
flujo; no reentrenar ni tocar el sistema; directorio nuevo; **no redactar** el artículo;
entregar faltantes + procedimiento). Trabajo en:
`C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\aqui trabajamos ...claude\analisis-seccion4`

## Estado de los repositorios (registrado)

| Repo | Rol | Rama | Commit | Fecha | Push remoto |
|---|---|---|---|---|---|
| `VF-Sistema-Open-Source-...` (clon `producto-main`) | Implementación | `main` | `fa9e5b0` | 2026-10-19 | 2026-10-19 07:35 UTC, público |
| `VF-PPI-TESIS-ORQUESTACION` (clon `orquestacion-limpio`) | Documentación/evidencias | `main` | `2f72d4d` | 2026-10-19 | 2026-10-19 07:05 UTC, público |

Acceso GitHub: **sí** (`gh`, cuenta `marksato13`, scope `repo`). Lectura/documentación OK;
el *push* lo hace Mark desde su terminal. `producto-main` limpio; `orquestacion-limpio`
tiene cambios sin commitear (diagramas, N1, plan de observaciones).

## Artefactos de la versión actual (identificados y verificados)

- **Modelo:** `if_limpio_2026_10`. Paquete local `…\scratchpad\run\arte\paq_despues.joblib`,
  umbral `decision_function < −0,069397` (= `score_samples < −0,569397`), 28 features.
  **Verificado:** el umbral del paquete local coincide con el desplegado en el sensor
  (`ppi-motor` confirmado corriendo este modelo, 23-oct).
- **Heurísticos:** `producto-main\scripts\engine\heuristicos.py`, `VERSION_UMBRALES = 2026-10-06.2`
  (brute_force→BLOCK, port_scan→BLOCK, http_abuse→LIMIT, dns_entropy→LIMIT). Módulo importable;
  `evaluar(row)` consume los contadores crudos de la ventana.

## Datos disponibles y para qué sirve CADA UNO

| Conjunto | n | Distribución | Contadores heur. | Válido para evaluar el modelo limpio |
|---|---:|---|---|---|
| `normal-reservado.csv` (sensor test-normal) | 65 421 | **Sensor (real)** | sí (8/8) | **SÍ** (benigno) |
| 181 ventanas Kali de `limpio.csv` (`eligible_training=False`) | 181 | **Sensor (real)** | sí | SÍ, pero es la **ráfaga de contaminación** (no batería curada) |
| `multilayer-v2-anomalies.csv` (laboratorio) | 179 | **Laboratorio (simulado)** | sí | **NO** — otra distribución (ver abajo) |
| `multilayer-v2-normal.csv` (laboratorio) | 1 373 | **Laboratorio (simulado)** | sí | **NO** para el modelo del sensor |

### Hallazgo metodológico (importante)
El modelo limpio está **entrenado con tráfico del sensor**. Evaluarlo sobre el **set de
laboratorio simulado** da **FPR ≈ 90–91 %** sobre el "benigno" de laboratorio: es el
artefacto **sim→real** que el proyecto ya documenta (el OCSVM daba 92,4 % en real; la
recalibración sobre el sensor lo bajó a 4,45 %). ⇒ **las tablas 7-modelos / ablación de
grupos de features (`ablacion-multicapa.json`, `compare_frozen_models`) son del dataset de
laboratorio y de modelos de laboratorio; NO deben mezclarse con el modelo desplegado del
sensor.** (El script `4.2-ablacion\ablacion_limpio.py` queda como demostración de ese
artefacto; su salida `Tabla8-ablacion-limpio.*` **no es un resultado válido**.)

## 4.2 — Ablación de componentes

- **Batería original de 9 episodios** (3 DNS, 3 flood HTTP, 3 escaneo; nota 26, 2026-10-05):
  resultados históricos **6/9 (modelo) · 7/9 (heur) · 9/9 (combinado)** con el modelo
  **contaminado** `if_recalibrado_2026_09`. Los veredictos están en `26-BATERIA-N3-RESULTADOS.md`
  y `producto-main\docs\evaluacion\comparacion-suricata.json` como **latencias por episodio**.
  **NO se conservaron los datos por ventana ni los PCAP** (el anillo PCAP del sensor se poda).
  ⇒ **un re-scoring fiel con el modelo limpio NO es posible offline: hay que RE-CORRER la batería.**
- **Computable offline AHORA (válido, sensor):** ablación IF/heur/combinado sobre
  {181 Kali del sensor + 65 421 benignas}. Script `4.2-ablacion\ablacion_sensor.py`.
  Resultado: FPR IF **4,53 %** (valida model card), heur 0,72 % (472 LIMIT/0 BLOCK), híbrido
  5,23 %; detección por ventana IF 50/181, heur 41/181 (`port_scan` 9, `http_abuse` 32),
  híbrido 54/181. **Salvedad:** las 181 son contaminación ambiental (1 ráfaga), sin DGA →
  valida FPR y muestra complementariedad, **no** reemplaza la batería 3×3.

**Faltante exacto para 4.2 fiel:** per-ventana (features + contadores) de los 9 episodios con
el modelo limpio. **Procedimiento:** re-correr la batería N≥3 por familia (DNS/flood/escaneo)
contra el modelo limpio y guardar, por ventana, score del modelo + veredicto heurístico +
`window_end_utc` (ver `4.4` para la instrumentación común).

## 4.3 — Comparación con Suricata

- **Disponible:** método de replay (`19-METODO-REPLAY-PCAP.md`), batería y Nikto
  (`26`, `27`, `28`), `comparacion-suricata.json` (CyberFlow 9/9 vs Suricata 0/9 sin firma;
  Nikto: Suricata 3,4 s por firma vs modelo 12,0 s), FPR benigno Suricata 14-oct.
- **Problema:** esos números de CyberFlow son del modelo **contaminado** y de PCAP **no
  conservados**. Reutilizar los de Suricata exige el **mismo PCAP/ruleset/config** (regla B).
- **Faltante:** PCAP de los episodios + config/HOME_NET/versión de Suricata + hashes.
  **Procedimiento:** en la misma re-corrida, capturar PCAP por episodio y pasarlo a Suricata
  (ET Open, versión y hash fijados) y al modelo limpio; medir t_detección desde marcas de
  paquete. Nikto como control aparte (N real).

## 4.4 — Respuestas y tiempos del sistema

- **Disponible:** cadena vigente (feed firmado cada 10 s, agente nftables); N1 (tabla
  LIMIT/BLOCK) y N3 (41,4 s extremo a extremo, cadena 10 s) ya redactados; batería en vivo
  de hoy (23-oct) contra el modelo limpio con DGA→`dns_entropy`→LIMIT confirmado en vivo.
- **Faltante:** ensayos **completos post-despliegue limpio** con los 6 sellos t0–t5 por
  ensayo (LIMIT por anomalía del IF, BLOCK por heurístico, caducidad/reversión), reloj
  monótono para la inferencia, y verificación de corte real. La de hoy fue N=1 y sin t0–t5
  instrumentados.
- **Procedimiento:** en la re-corrida, registrar t0 (lanzamiento), t1 (1ª señal), t2 (emisión
  feed), t3 (regla nftables aplicada), t4 (efecto en tráfico), t5 (expiración); sincronizar
  relojes; figura de 3 paneles (decisión / feed firmado / nftables) con id de ensayo.

## Bottom line

El **camino crítico común a 4.2, 4.3 y 4.4** es **UNA campaña de laboratorio bien
instrumentada** contra el modelo limpio: batería N≥3 × 3 familias (+ fuerza bruta N aparte) con
**PCAP por episodio** (para Suricata), **score+heurístico por ventana** (para la ablación) y
**sellos t0–t5 + reloj monótono** (para los tiempos). Eso produce las entradas de las tres
tablas a la vez. Lo offline-válido ya hecho (FPR 4,53 % del IF, comportamiento por componente
en tráfico real del sensor) se conserva como evidencia de apoyo.
</content>
