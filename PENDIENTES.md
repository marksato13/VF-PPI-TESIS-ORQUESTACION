# Pendientes — CyberFlow

**Actualizado:** 30 de septiembre de 2026.
Fuente única de "qué falta". Lo **hecho** está al final para contexto; el detalle
vive en `04-evidencias/cyberflow/` (notas K–N), `01-arquitectura/DISENO-ENFORCEMENT.md`
y `TRASPASO.md`.

---

## 🟥 Prioridad para la validación (sesiones del 7-oct)

### 1. GUI / Dashboard — actualizar al modelo recalibrado
El panel ya **lee el manifiesto nuevo** (detector `if_recalibrado_2026_09`, umbral
`-0,568892`, `calibrado_en_esta_red=true`), **pero `scripts/engine/dashboard.py`
tiene `ocsvm_scaled` cableado**:
- **Bug (importante):** `dashboard.py` ~líneas **2063–2070** cuenta las alertas con
  `detector_name == "ocsvm_scaled"`. Con el detector nuevo, **esos contadores salen
  en 0** → las estadísticas del panel no reflejan el modelo desplegado. Arreglar:
  contar por el **detector activo** (leído del manifiesto/config), no hardcodeado.
- ~línea **644**: mapa de nombre de detector → etiqueta; añadir `if_recalibrado_2026_09`
  (o hacerlo genérico) para que muestre una etiqueta legible.
- ~línea **1203**: la tarjeta de "reproducibilidad" menciona `ocsvm_scaled.joblib` →
  actualizar al modelo recalibrado + su hash (`if_recalibrado_desplegable.joblib`).
- **Verificar** que el banner "sin calibrar" desapareció y que el nodo "Cómo decide"
  muestra el umbral `-0,568892`.
- Requiere: editar `dashboard.py` (+ extraer el `<script>` y `node --check`, tests
  del panel), desplegar al sensor y reiniciar `ppi-dashboard`.

### 2. Validación con usuarios y expertos
- **TAM** (utilidad/aceptación, Likert 1–7) + **Alfa de Cronbach** (≥0,70).
- **Juicio de expertos** del entorno + **V de Aiken** (≥0,80).
- Instrumentos ya preparados (carpeta de informes / entregable de orquestación).

---

## 🟧 Enforcement — activar en producción
Código completo y probado en `main` (dormido); e2e demostrado (un BLOCK corta el
ataque en el host, nota `N`). Falta el despliegue operativo:
- **Publicador en timer:** `publicar_feed.py` como servicio+timer systemd en el sensor.
- **Transporte del feed a los hosts:** el host DMZ **no alcanza al sensor directo**
  (segmentación) → usar el **bastión como distribuidor** (o un canal dedicado) para
  que los agentes traigan el feed.
- **Integración motor→feed en vivo:** que la detección real dispare el feed sola (el
  motor ya emite el campo `heuristico`; falta encadenarlo al publicador en vivo).
- **Agente en los hosts:** `agente_enforce.py` + `feed.py` + clave pública + timer
  systemd en cada host protegido (empezar por el DMZ).
- **DNS-entropy 0 %:** re-probar el ataque contra el **resolver real `10.10.10.20`**
  (no el DMZ) para cerrar ese hueco (notas `M`/`N`).
- **Panel:** mostrar las acciones **LIMIT/BLOCK** (hoy el panel es ALERT/PERMIT).
- **Seguridad:** **revocar mi llave `cyberflow-to-srv`** del host DMZ
  (`~/.ssh/authorized_keys` de `adminsrvdmz@10.10.30.10`) cuando termine el despliegue.

---

## 🟨 Publicación (tesis)
- **Artículo a IJIES** (enviar).
- **DOI Zenodo** (`.zenodo.json` ya está; publicar cuando toque).
- Alinear cifras y limitaciones en todos los documentos.

---

## 🟩 Versionado (decidido)
- **Una sola versión principal: `v1.0.0` sobre `main`.** No se crea `v1.1.0`; las
  mejoras se actualizan sobre `main`. El tag `v1.0.0` es foto inmutable; `main` es la
  versión viva.

---

## ✅ Hecho (contexto)
- **v1.0.0** tag + Release GitHub; CI verde.
- **Replicabilidad**: 2ª VM turnkey offline (nota `K`).
- **Recalibración**: FPR **92,4 % → 4,45 %** (nota `L`).
- **Detección (Kali)**: TPR **100 % HTTP**, 63 % escaneo, 69 % global (nota `M`).
- **Congelado + calibrado** en sensor1 (`if_recalibrado_2026_09`, `calibrado=true`).
- **Enforcement**: diseño cerrado (`DISENO-ENFORCEMENT.md` + `flujo-decision.md`);
  código en `main` (heurísticos, feed firmado ed25519, escalera, publicador,
  integración aditiva en el motor, agente); 47 tests, CI verde; **e2e: un BLOCK
  corta el ataque en el host** (nota `N`).
- **Posicionamiento** "complementa, no reemplaza" en README + diseño.
